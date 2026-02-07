"""
Tests for V2 PDF generation and publish snapshot functionality.
"""
import json
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from apps.catalog.models import Service, Modality
from apps.patients.models import Patient
from apps.workflow.models import ServiceVisit, ServiceVisitItem
from apps.reporting.models import (
    ReportTemplateV2,
    ServiceReportTemplateV2,
    ReportInstanceV2,
    ReportPublishSnapshotV2,
)

User = get_user_model()


class WorkItemV2PublishPDFTestCase(TestCase):
    """Test V2 PDF generation and publish snapshot endpoints"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create user
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",
            email="test@example.com"
        )
        self.client.force_authenticate(user=self.user)
        
        # Create modality
        self.modality = Modality.objects.create(
            code="USG",
            name="Ultrasound"
        )
        
        # Create service
        self.service = Service.objects.create(
            code="USG_ABD",
            name="USG Abdomen",
            modality=self.modality,
            price=1000.00
        )
        
        # Create V2 template
        self.template_v2 = ReportTemplateV2.objects.create(
            code="USG_ABD_V2",
            name="USG Abdomen V2",
            modality="USG",
            status="active",
            json_schema={
                "type": "object",
                "required": ["liver_size_cm"],
                "properties": {
                    "liver_size_cm": {
                        "type": "number",
                        "title": "Liver size (cm)"
                    },
                    "liver_echo": {
                        "type": "string",
                        "title": "Liver echotexture",
                        "enum": ["Normal", "Coarse", "Fatty"]
                    },
                    "gb_stones": {
                        "type": "boolean",
                        "title": "Gall bladder stones"
                    },
                    "comments": {
                        "type": "string",
                        "title": "Comments"
                    }
                }
            },
            ui_schema={
                "groups": [
                    {
                        "title": "Liver",
                        "fields": ["liver_size_cm", "liver_echo"]
                    },
                    {
                        "title": "Gall Bladder",
                        "fields": ["gb_stones"]
                    }
                ]
            },
            narrative_rules={
                "sections": [
                    {
                        "title": "Liver",
                        "lines": [
                            "Liver size: {{liver_size_cm}} cm",
                            "Echotexture: {{liver_echo}}"
                        ]
                    },
                    {
                        "title": "Gall Bladder",
                        "lines": ["Stones: {{gb_stones}}"]
                    }
                ],
                "impression": ["{{comments}}"]
            }
        )
        
        # Create service mapping (active + default)
        ServiceReportTemplateV2.objects.create(
            service=self.service,
            template=self.template_v2,
            is_active=True,
            is_default=True
        )
        
        # Create patient
        self.patient = Patient.objects.create(
            name="Test Patient",
            mrn="MRN001",
            age=30,
            gender="M"
        )
        
        # Create service visit
        self.visit = ServiceVisit.objects.create(
            patient=self.patient,
            visit_id="VISIT001"
        )
        
        # Create work item
        self.work_item = ServiceVisitItem.objects.create(
            service_visit=self.visit,
            service=self.service,
            status="PENDING"
        )
    
    def test_schema_returns_v2(self):
        """Test that schema endpoint returns v2 for mapped service"""
        response = self.client.get(
            f"/api/reporting/workitems/{self.work_item.id}/schema/"
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["schema_version"], "v2")
        self.assertEqual(data["template"]["code"], "USG_ABD_V2")
    
    def test_save_v2_draft(self):
        """Test saving V2 draft values"""
        payload = {
            "schema_version": "v2",
            "values_json": {
                "liver_size_cm": 12.5,
                "liver_echo": "Normal",
                "gb_stones": False,
                "comments": "Normal study"
            }
        }
        
        response = self.client.post(
            f"/api/reporting/workitems/{self.work_item.id}/save/",
            data=json.dumps(payload),
            content_type="application/json"
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["schema_version"], "v2")
        self.assertTrue(data["saved"])
        
        # Verify instance was created
        instance = ReportInstanceV2.objects.get(work_item=self.work_item)
        self.assertEqual(instance.values_json["liver_size_cm"], 12.5)
    
    def test_report_pdf_generation(self):
        """Test V2 PDF generation endpoint"""
        # First save some values
        ReportInstanceV2.objects.create(
            work_item=self.work_item,
            template_v2=self.template_v2,
            values_json={
                "liver_size_cm": 12.5,
                "liver_echo": "Normal",
                "gb_stones": False,
                "comments": "Normal study"
            },
            created_by=self.user
        )
        
        response = self.client.get(
            f"/api/reporting/workitems/{self.work_item.id}/report-pdf/"
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertGreater(len(response.content), 0)
    
    def test_publish_creates_snapshot(self):
        """Test that publish creates a snapshot with PDF"""
        # Create report instance
        # Create report instance (VERIFIED)
        instance = ReportInstanceV2.objects.create(
            work_item=self.work_item,
            template_v2=self.template_v2,
            values_json={
                "liver_size_cm": 12.5,
                "liver_echo": "Normal",
                "gb_stones": False,
                "comments": "Normal study"
            },
            created_by=self.user,
            status="verified"
        )
        
        # Make user a verifier (or admin)
        self.user.is_superuser = True
        self.user.save()
        
        response = self.client.post(
            f"/api/reporting/workitems/{self.work_item.id}/publish/"
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "published")
        self.assertEqual(data["schema_version"], "v2")
        self.assertEqual(data["version"], 1)
        self.assertIn("content_hash", data)
        self.assertIn("snapshot_id", data)
        
        # Verify snapshot was created
        snapshot = ReportPublishSnapshotV2.objects.get(report_instance_v2=instance)
        self.assertEqual(snapshot.version, 1)
        self.assertEqual(snapshot.values_json, instance.values_json)
        self.assertIsNotNone(snapshot.narrative_json)
        self.assertTrue(snapshot.pdf_file)
        self.assertEqual(len(snapshot.content_hash), 64)  # SHA256
    
    def test_republish_with_same_values(self):
        """Test republishing with unchanged values produces consistent hash"""
        # Create report instance (VERIFIED)
        instance = ReportInstanceV2.objects.create(
            work_item=self.work_item,
            template_v2=self.template_v2,
            values_json={
                "liver_size_cm": 12.5,
                "liver_echo": "Normal",
                "gb_stones": False,
                "comments": "Normal study"
            },
            created_by=self.user,
            status="verified"
        )
        
        self.user.is_superuser = True
        self.user.save()
        
        # First publish
        response1 = self.client.post(
            f"/api/reporting/workitems/{self.work_item.id}/publish/"
        )
        self.assertEqual(response1.status_code, 200)
        hash1 = response1.json()["content_hash"]
        
        # Second publish (should create new version with same hash)
        response2 = self.client.post(
            f"/api/reporting/workitems/{self.work_item.id}/publish/"
        )
        self.assertEqual(response2.status_code, 200)
        data2 = response2.json()
        hash2 = data2["content_hash"]
        
        self.assertEqual(data2["version"], 2)
        self.assertEqual(hash1, hash2)  # Same content = same hash
    
    def test_published_pdf_retrieval(self):
        """Test retrieving published PDF snapshot"""
        # Create and publish
        # Create and publish (VERIFIED)
        instance = ReportInstanceV2.objects.create(
            work_item=self.work_item,
            template_v2=self.template_v2,
            values_json={
                "liver_size_cm": 12.5,
                "liver_echo": "Normal",
                "gb_stones": False,
                "comments": "Normal study"
            },
            created_by=self.user,
            status="verified"
        )
        
        self.user.is_superuser = True
        self.user.save()
        
        # Publish
        self.client.post(f"/api/reporting/workitems/{self.work_item.id}/publish/")
        
        # Get published PDF (latest version, no version param)
        response = self.client.get(
            f"/api/reporting/workitems/{self.work_item.id}/published-pdf/"
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertGreater(len(response.content), 0)
        
        # Get specific version
        response2 = self.client.get(
            f"/api/reporting/workitems/{self.work_item.id}/published-pdf/?version=1"
        )
        
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(response2["Content-Type"], "application/pdf")
