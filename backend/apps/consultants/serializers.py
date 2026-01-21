from rest_framework import serializers

from .models import (
    ConsultantProfile,
    ConsultantBillingRule,
    ConsultantSettlement,
    ConsultantSettlementLine,
)


class ConsultantProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConsultantProfile
        fields = [
            "id",
            "display_name",
            "mobile_number",
            "email",
            "degrees",
            "designation",
            "user",
            "is_active",
            "created_at",
            "updated_at"
        ]
        read_only_fields = ["created_at", "updated_at"]


class ConsultantBillingRuleSerializer(serializers.ModelSerializer):
    consultant_name = serializers.CharField(source="consultant.display_name", read_only=True)
    service_name = serializers.CharField(source="service.name", read_only=True, allow_null=True)

    class Meta:
        model = ConsultantBillingRule
        fields = [
            "id",
            "consultant",
            "consultant_name",
            "service",
            "service_name",
            "rule_type",
            "consultant_percent",
            "consultant_fixed_amount",
            "is_active",
            "active_from",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class ConsultantBillingRuleInputSerializer(serializers.Serializer):
    service_id = serializers.UUIDField(required=False, allow_null=True)
    rule_type = serializers.ChoiceField(
        choices=ConsultantBillingRule.RULE_TYPE_CHOICES,
        default=ConsultantBillingRule.RULE_TYPE_PERCENT_SPLIT,
        required=False,
    )
    consultant_percent = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, allow_null=True)
    consultant_fixed_amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    active_from = serializers.DateField(required=False, allow_null=True)


class ConsultantSettlementLineSerializer(serializers.ModelSerializer):
    service_name_snapshot = serializers.CharField(source="service_item.service_name_snapshot", read_only=True)
    visit_id = serializers.CharField(source="service_item.service_visit.visit_id", read_only=True)
    patient_name = serializers.CharField(source="service_item.service_visit.patient.name", read_only=True)

    class Meta:
        model = ConsultantSettlementLine
        fields = [
            "id",
            "service_item",
            "service_name_snapshot",
            "visit_id",
            "patient_name",
            "item_amount_snapshot",
            "paid_amount_snapshot",
            "consultant_share_snapshot",
            "clinic_share_snapshot",
            "metadata",
            "created_at",
        ]
        read_only_fields = ["created_at"]


class ConsultantSettlementSerializer(serializers.ModelSerializer):
    consultant_name = serializers.CharField(source="consultant.display_name", read_only=True)
    lines = ConsultantSettlementLineSerializer(many=True, read_only=True)

    class Meta:
        model = ConsultantSettlement
        fields = [
            "id",
            "consultant",
            "consultant_name",
            "date_from",
            "date_to",
            "gross_collected",
            "net_payable",
            "clinic_share",
            "status",
            "finalized_at",
            "finalized_by",
            "notes",
            "created_at",
            "updated_at",
            "lines",
        ]
        read_only_fields = ["created_at", "updated_at", "finalized_at", "finalized_by"]


class ConsultantSettlementCreateSerializer(serializers.Serializer):
    consultant_id = serializers.UUIDField()
    date_from = serializers.DateField()
    date_to = serializers.DateField()
    notes = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def validate(self, data):
        if data["date_from"] > data["date_to"]:
            raise serializers.ValidationError("date_from must be before or equal to date_to")
        return data


class ConsultantSettlementPreviewSerializer(serializers.Serializer):
    consultant_id = serializers.UUIDField()
    date_from = serializers.DateField()
    date_to = serializers.DateField()

    def validate(self, data):
        if data["date_from"] > data["date_to"]:
            raise serializers.ValidationError("date_from must be before or equal to date_to")
        return data
