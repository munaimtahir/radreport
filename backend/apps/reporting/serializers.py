from rest_framework import serializers
from .models import (
    ReportTemplateV2,
    ServiceReportTemplateV2,
    ReportBlockLibrary,
    ReportInstanceV2,
)


class ReportBlockLibrarySerializer(serializers.ModelSerializer):
    """
    Serializer for preset blocks.
    """

    class Meta:
        model = ReportBlockLibrary
        fields = [
            "id",
            "name",
            "category",
            "block_type",
            "content",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class ReportTemplateV2Serializer(serializers.ModelSerializer):
    class Meta:
        model = ReportTemplateV2
        fields = [
            "id",
            "code",
            "name",
            "modality",
            "status",
            "is_frozen",
            "json_schema",
            "ui_schema",
            "narrative_rules",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def validate_json_schema(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("json_schema must be a JSON object.")
        return value

    def validate_ui_schema(self, value):
        if value is None:
            return {}
        if not isinstance(value, dict):
            raise serializers.ValidationError("ui_schema must be a JSON object.")
        return value

    def validate_narrative_rules(self, value):
        if value is None:
            return {}
        if not isinstance(value, dict):
            raise serializers.ValidationError("narrative_rules must be a JSON object.")
        return value

    def validate_status(self, value):
        instance = getattr(self, "instance", None)
        if not instance:
            return value
        current = instance.status
        if current == value:
            return value
        allowed = {
            "draft": {"active", "archived"},
            "active": {"archived"},
            "archived": {"active"},
        }

        if value not in allowed.get(current, set()):
            raise serializers.ValidationError(
                f"Invalid status transition from {current} to {value}."
            )

        if current == "archived" and value == "active" and not self.context.get("allow_reactivate"):
            raise serializers.ValidationError("Archived templates cannot be reactivated.")
        return value


class ServiceReportTemplateV2Serializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceReportTemplateV2
        fields = [
            "id",
            "service",
            "template",
            "is_default",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["created_at"]

    def validate(self, attrs):
        is_default = attrs.get("is_default", getattr(self.instance, "is_default", False))
        is_active = attrs.get("is_active", getattr(self.instance, "is_active", True))
        if is_default and not is_active:
            raise serializers.ValidationError("Default templates must be active.")
        return attrs


class ReportInstanceV2Serializer(serializers.ModelSerializer):
    class Meta:
        model = ReportInstanceV2
        fields = ["values_json", "narrative_json", "status", "updated_at"]
