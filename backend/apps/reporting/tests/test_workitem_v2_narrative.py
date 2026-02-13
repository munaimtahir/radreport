from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
import tempfile
import shutil

from apps.catalog.models import Modality, Service
from apps.patients.models import Patient
from apps.workflow.models import ServiceVisit, ServiceVisitItem
from apps.reporting.models import (
    ReportTemplateV2,
    ServiceReportTemplateV2,
    ReportInstanceV2
)

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp()

@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class WorkItemV2NarrativeAPITests(TestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="reporter", password="password")
        self.client.force_authenticate(user=self.user)

        self.modality = Modality.objects.create(code="XR", name="X-Ray")
        self.service = Service.objects.create(
            modality=self.modality,
            name="Chest X-Ray",
            code="XR-CXR-001",
            price=500,
        )
        self.patient = Patient.objects.create(
            name="Narrative Patient", age=50, gender="Male"
        )
        self.visit = ServiceVisit.objects.create(patient=self.patient, created_by=self.user)
        self.item = ServiceVisitItem.objects.create(
            service_visit=self.visit,
            service=self.service,
            status="REGISTERED",
        )
        
        self.template = ReportTemplateV2.objects.create(
            code="CXR_NARRATIVE",
            name="CXR Narrative",
            modality="XR",
            status="active",
            json_schema={
                "type": "object",
                "properties": {
                    "lung_fields": {"type": "string"},
                    "impr": {"type": "string"}
                }
            },
            narrative_rules={
                "sections": [
                    {
                        "title": "Findings",
                        "content": ["Lungs: {{lung_fields}}"]
                    }
                ],
                "impression_rules": [
                    {
                        "when": {"field": "impr", "is_not_empty": True},
                        "text": "{{impr}}"
                    }
                ]
            }
        )
        ServiceReportTemplateV2.objects.create(
            service=self.service,
            template=self.template,
            is_active=True,
            is_default=True,
        )

    def test_generate_narrative_v2(self):
        url_base = f"/api/reporting/workitems/{self.item.id}/"
        
        # 1. Save values
        self.client.post(url_base + "save/", {
            "schema_version": "v2", 
            "values_json": {"lung_fields": "Clear", "impr": "Normal study."}
        }, format="json")
        
        # 2. Generate
        resp = self.client.post(url_base + "generate-narrative/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["schema_version"], "v2")
        
        narrative = resp.data["narrative_json"]
        self.assertIn("sections", narrative)
        self.assertIn("impression", narrative)
        self.assertEqual(narrative["sections"][0]["lines"][0], "Lungs: Clear")
        self.assertEqual(narrative["impression"][0], "Normal study.")
        self.assertIn("narrative_by_organ", narrative)
        self.assertIn("narrative_text", narrative)
        self.assertIn("narrative_by_organ", resp.data)
        self.assertIn("narrative_text", resp.data)
        
        # Check DB persistence
        instance = ReportInstanceV2.objects.get(work_item=self.item)
        self.assertEqual(instance.narrative_json, narrative)

    def test_manual_narrative_save(self):
        url_base = f"/api/reporting/workitems/{self.item.id}/"
        
        # 1. Save with narrative override
        custom_narrative = {"custom": True}
        self.client.post(url_base + "save/", {
            "schema_version": "v2", 
            "values_json": {},
            "narrative_json": custom_narrative
        }, format="json")
        
        instance = ReportInstanceV2.objects.get(work_item=self.item)
        self.assertEqual(instance.narrative_json, custom_narrative)
