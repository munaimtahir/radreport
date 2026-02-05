from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient
from decimal import Decimal

from apps.catalog.models import Modality, Service
from apps.patients.models import Patient
from apps.workflow.models import ServiceVisit, ServiceVisitItem
from apps.reporting.models import ReportProfile, ReportInstance
from apps.consultants.models import ConsultantProfile
from apps.reporting.pdf_engine.report_pdf import generate_report_pdf

User = get_user_model()

class ReportPDFTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="testradiologist", password="password")
        self.client.force_authenticate(user=self.user)
        
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
        self.visit = ServiceVisit.objects.create(
            patient=self.patient,
            created_by=self.user
        )
        
        # Item
        self.item = ServiceVisitItem.objects.create(
            service_visit=self.visit,
            service=self.service,
            status="REGISTERED"
        )
        
        # Report Profile
        self.profile = ReportProfile.objects.create(
            code="USG_ABD",
            name="USG Abdomen",
            modality="USG"
        )
        
        # Report Instance
        self.instance = ReportInstance.objects.create(
            service_visit_item=self.item,
            profile=self.profile,
            created_by=self.user,
            status="draft",
            findings_text="Liver is normal.\nGallbladder is normal.",
            impression_text="Normal Study",
            limitations_text=None
        )

    def test_pdf_generation_basics(self):
        """Test that PDF generation returns bytes and PDF header"""
        pdf_bytes = generate_report_pdf(str(self.instance.id))
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertTrue(len(pdf_bytes) > 0)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))

    def test_pdf_generation_empty_fields(self):
        """Test PDF generation does not crash with empty impression/limitations"""
        self.instance.impression_text = ""
        self.instance.findings_text = ""
        self.instance.save()
        
        pdf_bytes = generate_report_pdf(str(self.instance.id))
        self.assertTrue(len(pdf_bytes) > 0)

    def test_pdf_endpoint_success(self):
        """Test the API endpoint returns PDF"""
        url = f"/api/reporting/workitems/{self.item.id}/report-pdf/"
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('inline', response.get('Content-Disposition', ''))
        self.assertIn('Report_', response['Content-Disposition'])

    def test_pdf_endpoint_auto_narrative(self):
        """Test that PDF endpoint auto-generates narrative if missing"""
        # clear narrative
        self.instance.findings_text = ""
        self.instance.narrative_updated_at = None
        self.instance.save()
        
        # We need to mock generate_report_narrative or let it run (it might produce empty if no params)
        # If we rely on real logic, it returns empty dict if no values?
        # Let's mock it to ensure we test the wiring.
        from unittest.mock import patch
        with patch('apps.reporting.views.generate_report_narrative') as mock_gen:
            mock_gen.return_value = {
                "findings_text": "Auto-generated findings",
                "impression_text": "Auto-generated impression",
                "limitations_text": "",
                "version": "v1"
            }
            
            url = f"/api/reporting/workitems/{self.item.id}/report-pdf/"
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            
            # Verify DB updated
            self.instance.refresh_from_db()
            self.assertEqual(self.instance.findings_text, "Auto-generated findings")

