from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.catalog.models import Modality, Service
from apps.patients.models import Patient
from apps.reporting.models import ReportTemplateV2, ServiceReportTemplateV2, ReportInstanceV2
from apps.workflow.models import ServiceVisit, ServiceVisitItem


@override_settings(ALLOWED_HOSTS=["testserver", "localhost"], MEDIA_ROOT="/tmp/radreport-test-media")
class WorkItemV2MinimalFlowTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(username="reporter", password="password")
        self.verifier = user_model.objects.create_user(username="verifier", password="password")
        verifier_group = Group.objects.create(name="reporting_verifier")
        self.verifier.groups.add(verifier_group)

        modality = Modality.objects.create(code="USG", name="Ultrasound")
        self.service = Service.objects.create(modality=modality, name="USG Abdomen", code="USG-ABD")
        patient = Patient.objects.create(name="Test", age=40, gender="Male", phone="1234567890")
        visit = ServiceVisit.objects.create(patient=patient, created_by=self.user)
        self.item = ServiceVisitItem.objects.create(service_visit=visit, service=self.service, status="REGISTERED")

        self.template = ReportTemplateV2.objects.create(
            code="USG_ABD_V1",
            name="USG Abdomen",
            modality="USG",
            status="active",
            json_schema={"type": "object", "properties": {"note": {"type": "string"}}},
            ui_schema={"ui:order": ["note"]},
            narrative_rules={"sections": [{"title": "Main", "content": ["Note: {{note}}"]}]},
        )
        ServiceReportTemplateV2.objects.create(service=self.service, template=self.template, is_active=True, is_default=True)
        self.client = APIClient()

    def test_v2_flow(self):
        self.client.force_authenticate(self.user)
        base = f"/api/reporting/workitems/{self.item.id}/"

        schema_resp = self.client.get(base + "schema/")
        self.assertEqual(schema_resp.status_code, 200)
        self.assertEqual(schema_resp.data["template"]["code"], "USG_ABD_V1")
        self.assertTrue(schema_resp.data["json_schema"]["properties"])

        save_resp = self.client.post(base + "save/", {"values_json": {"note": "ok"}}, format="json")
        self.assertEqual(save_resp.status_code, 200)
        self.assertEqual(ReportInstanceV2.objects.get(work_item=self.item).values_json["note"], "ok")

        narrative_resp = self.client.post(base + "generate-narrative/")
        self.assertEqual(narrative_resp.status_code, 200)
        self.assertIn("sections", narrative_resp.data["narrative_json"])

        submit_resp = self.client.post(base + "submit/")
        self.assertEqual(submit_resp.status_code, 200)

        self.client.force_authenticate(self.verifier)
        verify_resp = self.client.post(base + "verify/")
        self.assertEqual(verify_resp.status_code, 200)

        pdf_resp = self.client.get(base + "report-pdf/")
        self.assertEqual(pdf_resp.status_code, 200)
        self.assertEqual(pdf_resp["Content-Type"], "application/pdf")

        publish_resp = self.client.post(base + "publish/", {"confirm": "PUBLISH"}, format="json")
        self.assertEqual(publish_resp.status_code, 200)

        integrity_resp = self.client.get(base + "published-integrity/?version=1")
        self.assertEqual(integrity_resp.status_code, 200)
        self.assertIn("content_hash", integrity_resp.data)
