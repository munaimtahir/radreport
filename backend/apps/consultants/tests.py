from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.catalog.models import Modality, Service
from apps.patients.models import Patient
from apps.workflow.api import ServiceVisitViewSet
from apps.workflow.models import ServiceVisit

from .api import ConsultantSettlementViewSet
from .models import ConsultantProfile, ConsultantBillingRule, ConsultantSettlement


class ConsultantSettlementTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        user_model = get_user_model()
        cls.admin = user_model.objects.create_superuser(
            username="admin_consultant",
            password="admin_consultant",
            email="admin@example.com",
        )

        cls.consultant = ConsultantProfile.objects.create(display_name="Dr. Consultant")
        ConsultantBillingRule.objects.create(
            consultant=cls.consultant,
            consultant_percent=Decimal("50.00"),
            rule_type=ConsultantBillingRule.RULE_TYPE_PERCENT_SPLIT,
            is_active=True,
        )

        modality, _ = Modality.objects.get_or_create(code="XRAY", defaults={"name": "XRay"})
        cls.service_one = Service.objects.create(
            code="CONS-1",
            name="Service One",
            category="Radiology",
            price=Decimal("100.00"),
            charges=Decimal("100.00"),
            default_price=Decimal("100.00"),
            is_active=True,
            modality=modality,
        )
        cls.service_two = Service.objects.create(
            code="CONS-2",
            name="Service Two",
            category="Radiology",
            price=Decimal("200.00"),
            charges=Decimal("200.00"),
            default_price=Decimal("200.00"),
            is_active=True,
            modality=modality,
        )

        cls.patient = Patient.objects.create(
            name="Consultant Patient",
            gender="Other",
            phone="03000000000",
            address="Test Address",
        )

    def _create_visit(self):
        factory = APIRequestFactory()
        payload = {
            "patient_id": str(self.patient.id),
            "service_ids": [str(self.service_one.id), str(self.service_two.id)],
            "booked_consultant_id": str(self.consultant.id),
            "subtotal": "300.00",
            "discount": "0.00",
            "total_amount": "300.00",
            "net_amount": "300.00",
            "amount_paid": "150.00",
            "payment_method": "cash",
        }
        request = factory.post("/api/workflow/visits/create_visit/", payload, format="json")
        force_authenticate(request, user=self.admin)
        response = ServiceVisitViewSet.as_view({"post": "create_visit"})(request)
        self.assertEqual(response.status_code, 201, response.data)
        return ServiceVisit.objects.get(id=response.data["id"])

    def test_booked_consultant_inheritance_and_preview(self):
        visit = self._create_visit()
        self.assertTrue(visit.booked_consultant)
        for item in visit.items.all():
            self.assertEqual(item.consultant, self.consultant)

        factory = APIRequestFactory()
        date_value = timezone.localdate().isoformat()
        params = {
            "consultant_id": str(self.consultant.id),
            "date_from": date_value,
            "date_to": date_value,
        }
        request = factory.get("/api/consultant-settlements/preview/", params)
        force_authenticate(request, user=self.admin)
        response = ConsultantSettlementViewSet.as_view({"get": "preview"})(request)
        self.assertEqual(response.status_code, 200, response.data)

        data = response.data
        self.assertEqual(Decimal(data["gross_collected"]), Decimal("150.00"))
        self.assertEqual(Decimal(data["consultant_payable"]), Decimal("75.00"))
        self.assertEqual(Decimal(data["clinic_share"]), Decimal("75.00"))
        paid_amounts = sorted(Decimal(line["paid_amount_snapshot"]) for line in data["lines"])
        self.assertEqual(paid_amounts, [Decimal("50.00"), Decimal("100.00")])

    def test_settlement_finalization_is_immutable(self):
        visit = self._create_visit()
        date_value = timezone.localdate().isoformat()

        factory = APIRequestFactory()
        payload = {
            "consultant_id": str(self.consultant.id),
            "date_from": date_value,
            "date_to": date_value,
        }
        request = factory.post("/api/consultant-settlements/", payload, format="json")
        force_authenticate(request, user=self.admin)
        response = ConsultantSettlementViewSet.as_view({"post": "create"})(request)
        self.assertEqual(response.status_code, 201, response.data)

        settlement_id = response.data["id"]
        finalize_request = factory.post(f"/api/consultant-settlements/{settlement_id}/finalize/", {}, format="json")
        force_authenticate(finalize_request, user=self.admin)
        finalize_response = ConsultantSettlementViewSet.as_view({"post": "finalize"})(finalize_request, pk=settlement_id)
        self.assertEqual(finalize_response.status_code, 200, finalize_response.data)

        ConsultantBillingRule.objects.filter(consultant=self.consultant).update(is_active=False)
        ConsultantBillingRule.objects.create(
            consultant=self.consultant,
            consultant_percent=Decimal("80.00"),
            rule_type=ConsultantBillingRule.RULE_TYPE_PERCENT_SPLIT,
            is_active=True,
        )

        settlement = ConsultantSettlement.objects.get(id=settlement_id)
        self.assertTrue(settlement.lines.filter(consultant_share_snapshot=Decimal("50.00")).exists())

        with self.assertRaises(ValidationError):
            settlement.gross_collected = Decimal("999.00")
            settlement.save()
