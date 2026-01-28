from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.test import APIClient
from decimal import Decimal
from unittest.mock import patch
import json
import hashlib
from django.utils import timezone
from django.core.cache import cache

from apps.catalog.models import Modality, Service
from apps.patients.models import Patient
from apps.workflow.models import ServiceVisit, ServiceVisitItem, WorkflowStatus
from apps.reporting.models import ReportProfile, ReportInstance, ReportPublishSnapshot, ReportActionLog, ReportParameter, ReportValue

User = get_user_model()

class Stage5ReportingTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.reporter = User.objects.create_user(username="reporter", password="password")
        self.verifier = User.objects.create_user(username="verifier", password="password", is_staff=True) # Staff for admin tests
        
        verifier_group = Group.objects.create(name="reporting_verifier")
        self.verifier.groups.add(verifier_group)
        
        self.modality = Modality.objects.create(code="USG", name="Ultrasound")
        self.service = Service.objects.create(
            modality=self.modality,
            name="Abdomen",
            price=Decimal("1500.00"),
            code="USG-ABD-001"
        )
        self.patient = Patient.objects.create(name="John Doe", age=30, gender="Male", phone="1234567890")
        self.visit = ServiceVisit.objects.create(patient=self.patient, created_by=self.reporter)
        self.item = ServiceVisitItem.objects.create(
            service_visit=self.visit,
            service=self.service,
            status="REGISTERED"
        )
        self.profile = ReportProfile.objects.create(code="USG_ABD", name="USG Abdomen", modality="USG")
        self.param1 = ReportParameter.objects.create(
            profile=self.profile, section="S1", name="Para1", parameter_type="short_text", order=1
        )
        
        self.instance = ReportInstance.objects.create(
            service_visit_item=self.item,
            profile=self.profile,
            created_by=self.reporter,
            status="submitted",
            findings_text="Normal study",
            impression_text="Normal",
        )

    def test_police_mode_return_length(self):
        """Return requires reason >= 10 chars"""
        self.client.force_authenticate(user=self.verifier)
        url = f"/api/reporting/workitems/{self.item.id}/return-for-correction/"
        
        # Too short
        response = self.client.post(url, {"reason": "Short"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("at least 10 characters", response.data["error"])
        
        # Long enough
        response = self.client.post(url, {"reason": "This is a long enough reason."})
        self.assertEqual(response.status_code, 200)

    def test_police_mode_publish_confirm(self):
        """Publish requires confirm string 'PUBLISH'"""
        self.instance.status = "verified"
        self.instance.save()
        
        self.client.force_authenticate(user=self.verifier)
        url = f"/api/reporting/workitems/{self.item.id}/publish/"
        
        # Missing confirm
        response = self.client.post(url, {"notes": "ok"})
        self.assertEqual(response.status_code, 400)
        
        # Wrong confirm
        response = self.client.post(url, {"notes": "ok", "confirm": "YES"})
        self.assertEqual(response.status_code, 400)
        
        # Success (mocking PDF)
        with patch('apps.reporting.views.generate_report_pdf') as mock_pdf:
            mock_pdf.return_value = b"PDF"
            response = self.client.post(url, {"notes": "ok", "confirm": "PUBLISH"})
            self.assertEqual(response.status_code, 200)

    def test_integrity_verification(self):
        """Integrity endpoint recomputes hash and compares"""
        # Create snapshot
        vmap = {str(self.param1.id): "Val1"}
        canon = json.dumps(vmap, sort_keys=True)
        txt = "FindingsImpressionLimitations"
        h = hashlib.sha256((canon + txt).encode()).hexdigest()
        
        snap = ReportPublishSnapshot.objects.create(
            report=self.instance,
            version=1,
            findings_text="Findings",
            impression_text="Impression",
            limitations_text="Limitations",
            values_json=vmap,
            sha256=h,
            published_by=self.verifier
        )
        
        self.client.force_authenticate(user=self.reporter)
        url = f"/api/reporting/workitems/{self.item.id}/published-integrity/?version=1"
        
        # Match
        response = self.client.get(url)
        self.assertEqual(response.data["match"], True)
        
        # Tamper snap in DB (simulating data corruption or bypass)
        snap.findings_text = "Corrupted findings"
        snap.save()
        
        response = self.client.get(url)
        self.assertEqual(response.data["match"], False)

    def test_pdf_caching(self):
        """PDF endpoint caches bytes and invalidates on update"""
        self.client.force_authenticate(user=self.reporter)
        url = f"/api/reporting/workitems/{self.item.id}/report-pdf/"
        
        with patch('apps.reporting.views.generate_report_pdf') as mock_pdf:
            mock_pdf.return_value = b"PDF_BYTES_1"
            
            # First call - generated
            res1 = self.client.get(url)
            self.assertEqual(res1.content, b"PDF_BYTES_1")
            self.assertEqual(mock_pdf.call_count, 1)
            
            # Second call - cached
            res2 = self.client.get(url)
            self.assertEqual(res2.content, b"PDF_BYTES_1")
            self.assertEqual(mock_pdf.call_count, 1) # Still 1
            
            # Update instance -> updated_at changes
            self.instance.findings_text = "Updated findings"
            self.instance.save()
            
            mock_pdf.return_value = b"PDF_BYTES_2"
            res3 = self.client.get(url)
            self.assertEqual(res3.content, b"PDF_BYTES_2")
            self.assertEqual(mock_pdf.call_count, 2)

    def test_query_count_optimizations(self):
        """Assert max queries for common endpoints"""
        self.client.force_authenticate(user=self.reporter)
        
        # Schema endpoint
        url_schema = f"/api/reporting/workitems/{self.item.id}/schema/"
        with self.assertNumQueries(4): # 1 auth, 1 item/service, 1 profile, 1 params+options prefetch
            # Adjusted count might vary based on middleware but should be low and constant
            self.client.get(url_schema)
            
        # Values endpoint
        url_values = f"/api/reporting/workitems/{self.item.id}/values/"
        with self.assertNumQueries(4):
            self.client.get(url_values)

    def test_admin_rebuild_tools(self):
        """Admin only rebuild endpoints work and log"""
        self.client.force_authenticate(user=self.verifier) # is_staff=True
        
        # Rebuild Narrative
        url_narrative = "/api/reporting/admin/rebuild-narrative/"
        with patch('apps.reporting.views.generate_report_narrative') as mock_narrative:
            mock_narrative.return_value = {
                "findings_text": "Rebuilt", "impression_text": "", "limitations_text": "", "version": "v2"
            }
            response = self.client.post(url_narrative, {"report_instance_id": str(self.instance.id)})
            self.assertEqual(response.status_code, 200)
            self.instance.refresh_from_db()
            self.assertEqual(self.instance.findings_text, "Rebuilt")

        # Rebuild PDF
        url_pdf = "/api/reporting/admin/rebuild-pdf/"
        with patch('apps.reporting.views.generate_report_pdf') as mock_pdf:
            mock_pdf.return_value = b"REBUILT_PDF"
            response = self.client.post(url_pdf, {"report_instance_id": str(self.instance.id)})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content, b"REBUILT_PDF")
