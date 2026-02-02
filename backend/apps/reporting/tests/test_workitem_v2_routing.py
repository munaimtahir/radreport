from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.catalog.models import Modality, Service
from apps.patients.models import Patient
from apps.workflow.models import ServiceVisit, ServiceVisitItem
from apps.reporting.models import (
    ReportProfile,
    ServiceReportProfile,
    ReportTemplateV2,
    ServiceReportTemplateV2,
)


User = get_user_model()


class WorkItemV2RoutingTests(TestCase):
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
            name="V2 Patient", age=42, gender="Male", phone="1234567890"
        )
        self.visit = ServiceVisit.objects.create(patient=self.patient, created_by=self.user)
        self.item = ServiceVisitItem.objects.create(
            service_visit=self.visit,
            service=self.service,
            status="REGISTERED",
        )
        self.profile = ReportProfile.objects.create(
            code="CXR_V1",
            name="CXR V1",
            modality="XR",
        )
        ServiceReportProfile.objects.create(service=self.service, profile=self.profile)

    def test_schema_defaults_to_v1_without_v2_mapping(self):
        url = f"/api/reporting/workitems/{self.item.id}/schema/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["schema_version"], "v1")
        self.assertIn("parameters", response.data)

    def test_schema_returns_v2_when_mapping_exists(self):
        template = ReportTemplateV2.objects.create(
            code="CXR_V2",
            name="CXR V2",
            modality="XR",
            status="active",
            json_schema={"type": "object", "properties": {"note": {"type": "string"}}},
            ui_schema={"note": {"ui:widget": "textarea"}},
        )
        ServiceReportTemplateV2.objects.create(
            service=self.service,
            template=template,
            is_active=True,
            is_default=True,
        )

        url = f"/api/reporting/workitems/{self.item.id}/schema/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["schema_version"], "v2")
        self.assertEqual(response.data["json_schema"], template.json_schema)
        self.assertEqual(response.data["ui_schema"], template.ui_schema)
        self.assertEqual(response.data["template"]["code"], template.code)

    def test_v2_values_roundtrip(self):
        template = ReportTemplateV2.objects.create(
            code="CXR_V2_SAVE",
            name="CXR V2 Save",
            modality="XR",
            status="active",
            json_schema={"type": "object"},
            ui_schema={},
        )
        ServiceReportTemplateV2.objects.create(
            service=self.service,
            template=template,
            is_active=True,
            is_default=True,
        )

        save_url = f"/api/reporting/workitems/{self.item.id}/save/"
        payload = {"schema_version": "v2", "values_json": {"note": "hello"}}
        save_response = self.client.post(save_url, payload, format="json")
        self.assertEqual(save_response.status_code, 200)
        self.assertTrue(save_response.data["saved"])

        values_url = f"/api/reporting/workitems/{self.item.id}/values/"
        values_response = self.client.get(values_url)
        self.assertEqual(values_response.status_code, 200)
        self.assertEqual(values_response.data["schema_version"], "v2")
        self.assertEqual(values_response.data["values_json"], payload["values_json"])
