from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status as http_status

from apps.catalog.models import Modality, Service
from apps.reporting.models import ReportTemplateV2, ServiceReportTemplateV2

User = get_user_model()


class ReportTemplateV2APITestCase(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username="admin",
            email="admin@test.com",
            password="testpass123",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin_user)

        self.modality = Modality.objects.create(code="USG", name="Ultrasound")
        self.service = Service.objects.create(
            code="USG-TEST",
            modality=self.modality,
            name="USG Test",
        )

    def _create_template(self, code, status="draft", version=1):
        payload = {
            "code": code,
            "name": f"{code} Template",
            "modality": "USG",
            "status": status,
            "version": version,
            "json_schema": {"type": "object"},
            "ui_schema": {},
            "narrative_rules": {},
        }
        response = self.client.post("/api/reporting/templates-v2/", payload, format="json")
        self.assertEqual(response.status_code, http_status.HTTP_201_CREATED)
        return response.data

    def test_set_default_link_clears_other_defaults(self):
        template1 = self._create_template("TPL_ONE")
        template2 = self._create_template("TPL_TWO")

        link1_response = self.client.post(
            "/api/reporting/service-templates-v2/",
            {
                "service": str(self.service.id),
                "template": template1["id"],
                "is_default": True,
                "is_active": True,
            },
            format="json",
        )
        self.assertEqual(link1_response.status_code, http_status.HTTP_201_CREATED)

        link2_response = self.client.post(
            "/api/reporting/service-templates-v2/",
            {
                "service": str(self.service.id),
                "template": template2["id"],
                "is_default": False,
                "is_active": True,
            },
            format="json",
        )
        self.assertEqual(link2_response.status_code, http_status.HTTP_201_CREATED)

        set_default = self.client.post(
            f"/api/reporting/service-templates-v2/{link2_response.data['id']}/set-default/",
        )
        self.assertEqual(set_default.status_code, http_status.HTTP_200_OK)

        link1_instance = ServiceReportTemplateV2.objects.get(id=link1_response.data["id"])
        link2_instance = ServiceReportTemplateV2.objects.get(id=link2_response.data["id"])
        self.assertFalse(link1_instance.is_default)
        self.assertTrue(link2_instance.is_default)

    def test_activate_requires_force_when_conflict_exists(self):
        active_template = ReportTemplateV2.objects.create(
            code="CONFLICT",
            name="Active Template",
            modality="USG",
            status="active",
            version=1,
            json_schema={"type": "object"},
        )
        draft = ReportTemplateV2.objects.create(
            code="CONFLICT",
            name="Draft Template",
            modality="USG",
            status="draft",
            version=2,
            json_schema={"type": "object"},
        )

        response = self.client.post(f"/api/reporting/templates-v2/{draft.id}/activate/")
        self.assertEqual(response.status_code, http_status.HTTP_409_CONFLICT)

        response = self.client.post(f"/api/reporting/templates-v2/{draft.id}/activate/?force=1")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)

        active_template.refresh_from_db()
        draft.refresh_from_db()
        self.assertEqual(active_template.status, "archived")
        self.assertEqual(draft.status, "active")
