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
    parameters = serializers.SerializerMethodField()

    class Meta:
        model = ReportProfile
        fields = ["id", "code", "name", "modality", "parameters"]

    def get_parameters(self, obj):
        # 1. Get legacy parameters
        legacy_params = obj.parameters.prefetch_related("options").all()
        
        # 2. Get library links (ReportProfileParameterLink)
        links = obj.library_links.select_related('library_item').all()
        
        combined = []
        
        # Helper to format legacy
        for p in legacy_params:
            combined.append({
                "id": p.id,
                "parameter_id": p.id,
                "section": p.section,
                "name": p.name,
                "parameter_type": p.parameter_type,
                "unit": p.unit,
                "normal_value": p.normal_value,
                "order": p.order,
                "is_required": p.is_required,
                "options": ReportParameterOptionSerializer(p.options.all(), many=True).data
            })
            
        # Helper to format links
        for link in links:
            item = link.library_item
            overrides = link.overrides_json or {}
            
            # Format options from default_options_json
            options = []
            if item.parameter_type in ["dropdown", "checklist"]:
                raw_options = item.default_options_json or []
                for i, opt in enumerate(raw_options):
                    options.append({
                        "id": f"opt_{link.id}_{i}",
                        "label": opt.get("label", ""),
                        "value": opt.get("value", ""),
                        "order": i
                    })

            combined.append({
                "id": link.id, # Use link ID as the parameter identifier
                "parameter_id": link.id,
                "section": link.section,
                "name": overrides.get("name", item.name),
                "parameter_type": item.parameter_type,
                "unit": overrides.get("unit", item.unit),
                "normal_value": overrides.get("normal_value", item.default_normal_value),
                "order": link.order,
                "is_required": link.is_required,
                "options": options
            })
            
        # Sort by order
        combined.sort(key=lambda x: x["order"])
        return combined

class ReportValueSerializer(serializers.ModelSerializer):
    parameter_id = serializers.SerializerMethodField()
    
    class Meta:
        model = ReportValue
        fields = ["parameter_id", "value"]

    def get_parameter_id(self, obj):
        if obj.parameter_id:
            return obj.parameter_id
        if obj.profile_link_id:
            return obj.profile_link_id
        return None

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
