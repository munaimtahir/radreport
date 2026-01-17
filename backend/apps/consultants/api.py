from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import ConsultantProfile, ConsultantBillingRule, ConsultantSettlement
from .serializers import (
    ConsultantProfileSerializer,
    ConsultantBillingRuleSerializer,
    ConsultantBillingRuleInputSerializer,
    ConsultantSettlementSerializer,
    ConsultantSettlementCreateSerializer,
    ConsultantSettlementPreviewSerializer,
)
from .services import build_settlement_preview


class ConsultantProfileViewSet(viewsets.ModelViewSet):
    queryset = ConsultantProfile.objects.all()
    serializer_class = ConsultantProfileSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action == "list":
            return queryset.filter(is_active=True)
        return queryset

    def get_permissions(self):
        if self.action in {"create", "update", "partial_update", "destroy"}:
            return [permissions.IsAdminUser()]
        if self.action == "rule" and self.request.method in {"PUT", "PATCH"}:
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]

    @action(detail=True, methods=["get", "put", "patch"], url_path="rule")
    def rule(self, request, pk=None):
        consultant = self.get_object()

        if request.method == "GET":
            rule = (
                ConsultantBillingRule.objects.filter(consultant=consultant, is_active=True)
                .order_by("-active_from", "-created_at")
                .first()
            )
            if not rule:
                return Response(
                    {
                        "consultant": str(consultant.id),
                        "rule_type": ConsultantBillingRule.RULE_TYPE_PERCENT_SPLIT,
                        "consultant_percent": "0.00",
                        "is_active": False,
                    }
                )
            return Response(ConsultantBillingRuleSerializer(rule).data)

        serializer = ConsultantBillingRuleInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ConsultantBillingRule.objects.filter(consultant=consultant, is_active=True).update(is_active=False)
        rule = ConsultantBillingRule.objects.create(
            consultant=consultant,
            is_active=True,
            **serializer.validated_data,
        )
        return Response(ConsultantBillingRuleSerializer(rule).data, status=status.HTTP_201_CREATED)


class ConsultantSettlementViewSet(viewsets.ModelViewSet):
    queryset = ConsultantSettlement.objects.select_related("consultant", "finalized_by").prefetch_related(
        "lines",
        "lines__service_item",
        "lines__service_item__service_visit",
        "lines__service_item__service_visit__patient",
    )
    serializer_class = ConsultantSettlementSerializer
    permission_classes = [permissions.IsAdminUser]
    http_method_names = ["get", "post", "head", "options"]

    @action(detail=False, methods=["get"], url_path="preview")
    def preview(self, request):
        serializer = ConsultantSettlementPreviewSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        consultant = get_object_or_404(ConsultantProfile, id=data["consultant_id"])
        preview = build_settlement_preview(consultant, data["date_from"], data["date_to"])

        return Response(
            {
                "consultant": {
                    "id": str(consultant.id),
                    "display_name": consultant.display_name,
                },
                "date_from": data["date_from"],
                "date_to": data["date_to"],
                "consultant_percent": str(preview["consultant_percent"]),
                "gross_collected": str(preview["gross_collected"]),
                "consultant_payable": str(preview["consultant_payable"]),
                "clinic_share": str(preview["clinic_share"]),
                "lines": [
                    {
                        "service_item_id": line["service_item_id"],
                        "visit_id": line["visit_id"],
                        "patient_name": line["patient_name"],
                        "service_name": line["service_name"],
                        "item_amount_snapshot": str(line["item_amount_snapshot"]),
                        "paid_amount_snapshot": str(line["paid_amount_snapshot"]),
                        "consultant_share_snapshot": str(line["consultant_share_snapshot"]),
                        "clinic_share_snapshot": str(line["clinic_share_snapshot"]),
                    }
                    for line in preview["lines"]
                ],
            }
        )

    def create(self, request, *args, **kwargs):
        serializer = ConsultantSettlementCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        consultant = get_object_or_404(ConsultantProfile, id=data["consultant_id"])
        preview = build_settlement_preview(consultant, data["date_from"], data["date_to"])

        settlement = ConsultantSettlement.objects.create(
            consultant=consultant,
            date_from=data["date_from"],
            date_to=data["date_to"],
            gross_collected=preview["gross_collected"],
            net_payable=preview["consultant_payable"],
            clinic_share=preview["clinic_share"],
            notes=data.get("notes"),
            status=ConsultantSettlement.STATUS_DRAFT,
        )

        settlement.lines.bulk_create(
            [
                settlement.lines.model(
                    settlement=settlement,
                    service_item=line["service_item"],
                    item_amount_snapshot=line["item_amount_snapshot"],
                    paid_amount_snapshot=line["paid_amount_snapshot"],
                    consultant_share_snapshot=line["consultant_share_snapshot"],
                    clinic_share_snapshot=line["clinic_share_snapshot"],
                    metadata={
                        "visit_id": line["visit_id"],
                        "patient_name": line["patient_name"],
                        "service_name": line["service_name"],
                    },
                )
                for line in preview["lines"]
            ]
        )

        response_serializer = self.get_serializer(settlement)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="finalize")
    def finalize(self, request, pk=None):
        settlement = self.get_object()
        if settlement.status == ConsultantSettlement.STATUS_FINALIZED:
            return Response(self.get_serializer(settlement).data)
        if settlement.status == ConsultantSettlement.STATUS_CANCELLED:
            return Response(
                {"detail": "Cancelled settlements cannot be finalized."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        settlement.status = ConsultantSettlement.STATUS_FINALIZED
        settlement.finalized_at = timezone.now()
        settlement.finalized_by = request.user
        settlement.save()
        return Response(self.get_serializer(settlement).data)
