from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.catalog.models import Modality, Service
from apps.catalog.api import ServiceViewSet
from apps.patients.models import Patient
from apps.workflow.models import ServiceVisit, ServiceVisitItem
from apps.templates.api import ReportTemplateViewSet
from apps.reporting.api import ReportingViewSet
from apps.reporting.models import ReportTemplateReport


class ReportTemplateFlowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        user_model = get_user_model()
        cls.admin = user_model.objects.create_superuser(
            username="admin_report_template", password="admin_report_template"
        )

        cls.modality = Modality.objects.create(code="XR", name="X-Ray")
        cls.service = Service.objects.create(
            code="XR-TEST",
            modality=cls.modality,
            name="X-Ray Chest",
            category="Radiology",
            price=Decimal("100.00"),
            charges=Decimal("100.00"),
            default_price=Decimal("100.00"),
            is_active=True,
        )
        cls.patient = Patient.objects.create(
            name="Template Patient",
            gender="Other",
            phone="0000000000",
            address="Test Address",
        )
        cls.visit = ServiceVisit.objects.create(patient=cls.patient, created_by=cls.admin)
        cls.item = ServiceVisitItem.objects.create(
            service_visit=cls.visit,
            service=cls.service,
            service_name_snapshot=cls.service.name,
            department_snapshot=cls.modality.code,
            price_snapshot=cls.service.price,
        )

    def _create_template(self):
        factory = APIRequestFactory()
        payload = {
            "name": "General Report",
            "code": "GEN",
            "description": "General template",
            "category": "Radiology",
            "is_active": True,
            "version": 1,
        }
        request = factory.post("/api/report-templates/", payload, format="json")
        force_authenticate(request, user=self.admin)
        response = ReportTemplateViewSet.as_view({"post": "create"})(request)
        self.assertEqual(response.status_code, 201, response.data)
        template_id = response.data["id"]

        fields_payload = [
            {
                "label": "Finding",
                "key": "finding",
                "field_type": "short_text",
                "is_required": True,
                "order": 0,
                "is_active": True,
                "options": [],
            },
            {
                "label": "Quality",
                "key": "quality",
                "field_type": "dropdown",
                "is_required": False,
                "order": 1,
                "is_active": True,
                "options": [
                    {"label": "Good", "value": "good", "order": 0, "is_active": True},
                    {"label": "Fair", "value": "fair", "order": 1, "is_active": True},
                ],
            },
        ]
        fields_request = factory.put(
            f"/api/report-templates/{template_id}/fields/",
            fields_payload,
            format="json",
        )
        force_authenticate(fields_request, user=self.admin)
        fields_response = ReportTemplateViewSet.as_view({"put": "update_fields"})(
            fields_request, pk=template_id
        )
        self.assertEqual(fields_response.status_code, 200, fields_response.data)
        return template_id

    def test_template_create_duplicate_and_link(self):
        template_id = self._create_template()

        factory = APIRequestFactory()
        duplicate_request = factory.post(f"/api/report-templates/{template_id}/duplicate/", {}, format="json")
        force_authenticate(duplicate_request, user=self.admin)
        duplicate_response = ReportTemplateViewSet.as_view({"post": "duplicate"})(
            duplicate_request, pk=template_id
        )
        self.assertEqual(duplicate_response.status_code, 201, duplicate_response.data)

        attach_request = factory.post(
            f"/api/services/{self.service.id}/templates/",
            {"template_id": template_id, "is_default": True},
            format="json",
        )
        force_authenticate(attach_request, user=self.admin)
        attach_response = ServiceViewSet.as_view({"post": "attach_template"})(
            attach_request, pk=str(self.service.id)
        )
        self.assertEqual(attach_response.status_code, 201, attach_response.data)

    def test_fetch_template_for_workitem_and_save(self):
        template_id = self._create_template()
        factory = APIRequestFactory()
        attach_request = factory.post(
            f"/api/services/{self.service.id}/templates/",
            {"template_id": template_id, "is_default": True},
            format="json",
        )
        force_authenticate(attach_request, user=self.admin)
        ServiceViewSet.as_view({"post": "attach_template"})(attach_request, pk=str(self.service.id))

        fetch_request = factory.get(f"/api/reporting/{self.item.id}/template/")
        force_authenticate(fetch_request, user=self.admin)
        fetch_response = ReportingViewSet.as_view({"get": "template"})(
            fetch_request, pk=str(self.item.id)
        )
        self.assertEqual(fetch_response.status_code, 200, fetch_response.data)
        self.assertEqual(fetch_response.data["template"]["id"], template_id)

        save_request = factory.post(
            f"/api/reporting/{self.item.id}/save-template-report/",
            {
                "template_id": template_id,
                "values": {"finding": "Normal", "quality": "good"},
                "narrative_text": "All good",
                "submit": True,
            },
            format="json",
        )
        force_authenticate(save_request, user=self.admin)
        save_response = ReportingViewSet.as_view({"post": "save_template_report"})(
            save_request, pk=str(self.item.id)
        )
        self.assertEqual(save_response.status_code, 200, save_response.data)
        report = ReportTemplateReport.objects.get(service_visit_item=self.item)
        self.assertEqual(report.values.get("finding"), "Normal")
