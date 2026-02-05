from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.test import APIClient
from decimal import Decimal
from unittest.mock import patch
import json

from apps.catalog.models import Modality, Service
from apps.patients.models import Patient
from apps.workflow.models import ServiceVisit, ServiceVisitItem
from apps.reporting.models import ReportProfile, ReportInstance, ReportPublishSnapshot, ReportActionLog

User = get_user_model()

class Stage4ReportingTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.reporter = User.objects.create_user(username="reporter", password="password")
        self.verifier = User.objects.create_user(username="verifier", password="password")
        
        # Groups
        verifier_group = Group.objects.create(name="reporting_verifier")
        self.verifier.groups.add(verifier_group)
        
        # Setup Dependency Models
        self.modality = Modality.objects.create(code="USG", name="Ultrasound")
        self.service = Service.objects.create(
            modality=self.modality,
            name="Abdomen",
            price=Decimal("1500.00"),
            code="USG-ABD-001"
        )
        self.patient = Patient.objects.create(name="John Doe", age=30, gender="Male", phone="1234567890")
        
        # Visit
        self.visit = ServiceVisit.objects.create(patient=self.patient, created_by=self.reporter)
        
        # Item
        self.item = ServiceVisitItem.objects.create(
            service_visit=self.visit,
            service=self.service,
            status="REGISTERED"
        )
        
        # Report Profile
        self.profile = ReportProfile.objects.create(code="USG_ABD", name="USG Abdomen", modality="USG")
        
        # Report Instance (submitted)
        self.instance = ReportInstance.objects.create(
            service_visit_item=self.item,
            profile=self.profile,
            created_by=self.reporter,
            status="submitted",
            findings_text="Normal study",
            impression_text="Normal",
        )

    def test_verify_permission(self):
        """Only verifiers can verify"""
        self.client.force_authenticate(user=self.reporter)
        url = f"/api/reporting/workitems/{self.item.id}/verify/"
        response = self.client.post(url, {"notes": "ok"})
        self.assertEqual(response.status_code, 403)

        self.client.force_authenticate(user=self.verifier)
        response = self.client.post(url, {"notes": "ok"})
        self.assertEqual(response.status_code, 200)
        self.instance.refresh_from_db()
        self.assertEqual(self.instance.status, "verified")

    def test_return_logic(self):
        """Return moves back to draft and logs reason"""
        self.client.force_authenticate(user=self.verifier)
        url = f"/api/reporting/workitems/{self.item.id}/return-for-correction/"
        
        # Missing reason
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, 400)
        
        # Success
        response = self.client.post(url, {"reason": "Typo fix"})
        self.assertEqual(response.status_code, 200)
        
        self.instance.refresh_from_db()
        self.assertEqual(self.instance.status, "draft")
        self.item.refresh_from_db()
        self.assertEqual(self.item.status, "RETURNED_FOR_CORRECTION")
        
        # Check logs
        log = ReportActionLog.objects.filter(action="return").first()
        self.assertIsNotNone(log)
        self.assertEqual(log.meta["reason"], "Typo fix")

    def test_publish_flow(self):
        """Publish creates snapshot and immutable PDF"""
        # First verify
        self.instance.status = "verified"
        self.instance.save()
        
        self.client.force_authenticate(user=self.verifier)
        url = f"/api/reporting/workitems/{self.item.id}/publish/"
        
        # Mock PDF generation to avoid wkhtmltopdf dependency in test env if needed
        # But we want to test flow. Assuming 'generate_report_pdf' works or is mocked.
        # test_pdf.py seemed to invoke it directly. If it fails due to missing binary, we should mock.
        
        with patch('apps.reporting.views.generate_report_pdf') as mock_pdf:
            mock_pdf.return_value = b"%PDF-MOCK"
            
            response = self.client.post(url, {"notes": "Final release"})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data["status"], "published")
            self.assertEqual(response.data["version"], 1)
            
            # Check Instance properties
            self.instance.refresh_from_db()
            self.assertTrue(self.instance.is_published)
            self.assertEqual(self.instance.status, "verified") # Remains verified on Model
            
            # Check Item status
            self.item.refresh_from_db()
            self.assertEqual(self.item.status, "PUBLISHED")
            
            # Check Snapshot
            snap = ReportPublishSnapshot.objects.first()
            self.assertIsNotNone(snap)
            self.assertEqual(snap.version, 1)
            self.assertEqual(snap.sha256, "6f4558ba09186c3d054ccd3d0251c780692e3ba2bb4bc36ce1398f3d2df7d0bc") # Deterministic? depends on values map empty
            # values_map is empty dict -> "{}" + "Normal studyNormal" -> hash.
            
            self.assertTrue(snap.pdf_file.name.endswith(".pdf"))

    def test_publish_history_and_retrieval(self):
        # Create a snapshot manually
        snap = ReportPublishSnapshot.objects.create(
            report=self.instance,
            version=1,
            findings_text="F",
            values_json={},
            sha256="abc",
            published_by=self.verifier
        )
        from django.core.files.base import ContentFile
        snap.pdf_file.save("test.pdf", ContentFile(b"PDFDATA"))
        snap.save()
        
        self.client.force_authenticate(user=self.reporter) # Reporter can view?
        # Actually WorkItemViewSet is Authenticated. Reporter can see history.
        
        url_hist = f"/api/reporting/workitems/{self.item.id}/publish-history/"
        response = self.client.get(url_hist)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["version"], 1)
        
        url_pdf = f"/api/reporting/workitems/{self.item.id}/published-pdf/?version=1"
        response = self.client.get(url_pdf)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"PDFDATA")
