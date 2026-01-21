from decimal import Decimal
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate
from apps.catalog.models import Modality, Service
from apps.patients.models import Patient
from apps.workflow.api import ServiceVisitViewSet, USGReportViewSet
from apps.workflow.models import ServiceVisit, USGReport, ServiceVisitItem
from apps.templates.api import build_schema
from apps.templates.models import Template, TemplateField, TemplateSection, TemplateVersion

class USGPublishMetadataTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create groups
        for group_name in ["registration", "performance", "verification"]:
            Group.objects.get_or_create(name=group_name)

        user_model = get_user_model()
        cls.reg_user = user_model.objects.create_user(username="reg_user", password="test_password")
        cls.perf_user = user_model.objects.create_user(username="perf_user", password="test_password")
        cls.ver_user = user_model.objects.create_user(username="ver_user", password="test_password")
        
        cls.reg_user.groups.add(Group.objects.get(name="registration"))
        cls.perf_user.groups.add(Group.objects.get(name="performance"))
        cls.ver_user.groups.add(Group.objects.get(name="verification"))

        # Setup Modality and Template
        modality, _ = Modality.objects.get_or_create(code="USG", defaults={"name": "Ultrasound"})
        template, _ = Template.objects.get_or_create(
            name="Test USG Template",
            modality_code="USG",
            defaults={"is_active": True},
        )
        section, _ = TemplateSection.objects.get_or_create(template=template, title="Findings", defaults={"order": 1})
        TemplateField.objects.get_or_create(
            section=section,
            key="findings",
            defaults={
                "label": "Findings",
                "field_type": "long_text",
                "required": False,
                "order": 1,
            },
        )
        
        if not template.versions.filter(is_published=True).exists():
            TemplateVersion.objects.create(
                template=template,
                version=1,
                schema=build_schema(template),
                is_published=True,
            )

        # Setup Service
        cls.service, _ = Service.objects.get_or_create(
            code="USG-TEST",
            defaults={
                "modality": modality,
                "name": "USG Test",
                "category": "Radiology",
                "price": Decimal("1000.00"),
                "is_active": True,
                "default_template": template,
            },
        )

        # Setup Patient
        cls.patient = Patient.objects.create(
            name="Test Patient",
            gender="M",
            phone="1234567890",
        )

    def _create_visit(self):
        factory = APIRequestFactory()
        payload = {
            "patient_id": str(self.patient.id),
            "service_ids": [str(self.service.id)],
            "subtotal": "1000.00",
            "discount": "0",
            "total_amount": "1000.00",
            "net_amount": "1000.00",
            "amount_paid": "1000.00",
            "payment_method": "cash",
        }
        request = factory.post("/api/workflow/visits/create_visit/", payload, format="json")
        force_authenticate(request, user=self.reg_user)
        response = ServiceVisitViewSet.as_view({"post": "create_visit"})(request)
        self.assertEqual(response.status_code, 201)
        return ServiceVisit.objects.get(id=response.data["id"])

    def test_publish_without_metadata_succeeds(self):
        """
        Test that publishing a USG report succeeds even if scan_quality,
        limitations_text, and impression_text are missing.
        """
        # 1. Create Visit
        visit = self._create_visit()
        item = visit.items.first()
        
        # 2. Create Report (Performance User)
        factory = APIRequestFactory()
        create_payload = {
            "service_visit_item_id": str(item.id),
            "values": {"findings": "Normal scan content."}
        }
        request = factory.post("/api/workflow/usg/", create_payload, format="json")
        force_authenticate(request, user=self.perf_user)
        response = USGReportViewSet.as_view({"post": "create"})(request)
        self.assertEqual(response.status_code, 201)
        report = USGReport.objects.get(id=response.data["id"])
        
        # Ensure metadata fields are empty
        report.scan_quality = ""
        report.limitations_text = ""
        report.impression_text = ""
        report.save()

        # 3. Submit for verification
        submit_request = factory.post(f"/api/workflow/usg/{report.id}/submit_for_verification/", {}, format="json")
        force_authenticate(submit_request, user=self.perf_user)
        submit_response = USGReportViewSet.as_view({"post": "submit_for_verification"})(submit_request, pk=str(report.id))
        self.assertEqual(submit_response.status_code, 200)
        
        item.refresh_from_db()
        self.assertEqual(item.status, "PENDING_VERIFICATION")

        # 4. Attempt to publish (Verification User)
        publish_request = factory.post(f"/api/workflow/usg/{report.id}/publish/", {}, format="json")
        force_authenticate(publish_request, user=self.ver_user)
        publish_response = USGReportViewSet.as_view({"post": "publish"})(publish_request, pk=str(report.id))
        
        # Assertions
        self.assertEqual(publish_response.status_code, 200, publish_response.data)
        
        report.refresh_from_db()
        self.assertEqual(report.report_status, "FINAL")
        self.assertEqual(report.scan_quality, "Not recorded")
        self.assertEqual(report.limitations_text, "None")
        self.assertEqual(report.impression_text, "")
        
        item.refresh_from_db()
        self.assertEqual(item.status, "PUBLISHED")

    def test_publish_still_fails_for_real_blockers(self):
        """
        Test that publishing still fails for real blockers,
        like invalid workflow transition or critical flag without communication info.
        """
        visit = self._create_visit()
        item = visit.items.first()
        
        # Create report
        factory = APIRequestFactory()
        create_payload = {
            "service_visit_item_id": str(item.id),
            "values": {"findings": "Normal."}
        }
        request = factory.post("/api/workflow/usg/", create_payload, format="json")
        force_authenticate(request, user=self.perf_user)
        response = USGReportViewSet.as_view({"post": "create"})(request)
        report = USGReport.objects.get(id=response.data["id"])
        
        # Set critical flag but no communication info
        report.critical_flag = True
        report.critical_communication_json = {}
        report.save()

        # Submit for verification
        submit_request = factory.post(f"/api/workflow/usg/{report.id}/submit_for_verification/", {}, format="json")
        force_authenticate(submit_request, user=self.perf_user)
        USGReportViewSet.as_view({"post": "submit_for_verification"})(submit_request, pk=str(report.id))

        # Attempt to publish
        publish_request = factory.post(f"/api/workflow/usg/{report.id}/publish/", {}, format="json")
        force_authenticate(publish_request, user=self.ver_user)
        publish_response = USGReportViewSet.as_view({"post": "publish"})(publish_request, pk=str(report.id))
        
        # Should fail because of critical flag validation
        self.assertEqual(publish_response.status_code, 400)
        self.assertIn("critical_communication_json", str(publish_response.data))
