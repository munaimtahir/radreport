from rest_framework import serializers
from .models import (
    ReportProfile, ReportParameter, ReportParameterOption, 
    ReportInstance, ReportValue
)
from apps.workflow.models import ServiceVisitItem

class ReportParameterOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportParameterOption
        fields = ["id", "label", "value", "order"]

class ReportParameterSerializer(serializers.ModelSerializer):
    options = ReportParameterOptionSerializer(many=True, read_only=True)
    parameter_id = serializers.UUIDField(source="id", read_only=True)

    class Meta:
        model = ReportParameter
        fields = [
            "id", "parameter_id", "section", "name", "parameter_type", 
            "unit", "normal_value", "order", "is_required", "options"
        ]

class ReportProfileSerializer(serializers.ModelSerializer):
    parameters = ReportParameterSerializer(many=True, read_only=True)

    class Meta:
        model = ReportProfile
        fields = ["id", "code", "name", "modality", "parameters"]

class ReportValueSerializer(serializers.ModelSerializer):
    parameter_id = serializers.UUIDField(source="parameter.id", read_only=True)
    
    class Meta:
        model = ReportValue
        fields = ["parameter_id", "value"]

class ReportInstanceSerializer(serializers.ModelSerializer):
    values = ReportValueSerializer(many=True, read_only=True)
    last_saved_at = serializers.DateTimeField(source="updated_at", read_only=True)
    last_published_at = serializers.SerializerMethodField()

    class Meta:
        model = ReportInstance
        fields = [
            "id", "service_visit_item", "profile", "status", "values", 
            "created_at", "updated_at", "narrative_updated_at",
            "last_saved_at", "last_published_at"
        ]

    def get_last_published_at(self, obj):
        last_snap = obj.publish_snapshots.order_by("-published_at").first()
        return last_snap.published_at if last_snap else None

class ReportSaveItemSerializer(serializers.Serializer):
    parameter_id = serializers.UUIDField()
    value = serializers.JSONField(allow_null=True) # Allow any type as specified

class ReportSaveSerializer(serializers.Serializer):
    """
    Serializer to accept a list of values to save.
    Example: { "values": [ { "parameter_id": "<uuid>", "value": <any> } ] }
    """
    values = ReportSaveItemSerializer(many=True)
