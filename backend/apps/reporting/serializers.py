from rest_framework import serializers
from .models import (
    ReportProfile, ReportParameter, ReportParameterOption,
    ReportInstance, ReportValue, ServiceReportProfile, TemplateAuditLog,
    ReportParameterLibraryItem, ReportInstanceV2,
    ReportTemplateV2, ServiceReportTemplateV2,
)
from apps.workflow.models import ServiceVisitItem

class ReportParameterLibraryItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportParameterLibraryItem
        fields = [
            'id', 'modality', 'name', 'slug', 'parameter_type', 'unit',
            'default_normal_value', 'default_sentence_template',
            'default_omit_if_values', 'default_options_json',
            'default_join_label', 'default_narrative_role'
        ]

class ServiceReportProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceReportProfile
        fields = ["id", "service", "profile", "enforce_single_profile", "is_default"]


class ReportTemplateV2Serializer(serializers.ModelSerializer):
    class Meta:
        model = ReportTemplateV2
        fields = [
            "id", "code", "name", "modality", "status",
            "json_schema", "ui_schema", "narrative_rules",
            "created_at", "updated_at",
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
            "archived": {"active"},  # Reactivation is a possible transition
        }

        if value not in allowed.get(current, set()):
            raise serializers.ValidationError(f"Invalid status transition from {current} to {value}.")

        if current == 'archived' and value == 'active' and not self.context.get("allow_reactivate"):
            raise serializers.ValidationError("Archived templates cannot be reactivated.")
        return value


class ServiceReportTemplateV2Serializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceReportTemplateV2
        fields = [
            "id", "service", "template", "is_default", "is_active",
            "created_at",
        ]
        read_only_fields = ["created_at"]

    def validate(self, attrs):
        is_default = attrs.get("is_default", getattr(self.instance, "is_default", False))
        is_active = attrs.get("is_active", getattr(self.instance, "is_active", True))
        if is_default and not is_active:
            raise serializers.ValidationError("Default templates must be active.")
        return attrs

class ReportParameterOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportParameterOption
        fields = ["id", "label", "value", "order"]

class ReportParameterSerializer(serializers.ModelSerializer):
    options = ReportParameterOptionSerializer(many=True, read_only=True)
    parameter_id = serializers.UUIDField(source="id", read_only=True)
    type = serializers.CharField(source="parameter_type", read_only=True)

    class Meta:
        model = ReportParameter
        fields = [
            "parameter_id", "profile", "section", "name", "type", "parameter_type",
            "unit", "normal_value", "order", "is_required", "options",
            "slug", "sentence_template", "narrative_role", "omit_if_values", "join_label"
        ]

class ReportProfileSerializer(serializers.ModelSerializer):
    parameters = serializers.SerializerMethodField()
    used_by_reports = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    can_delete = serializers.SerializerMethodField()
    activated_by_username = serializers.SerializerMethodField()
    archived_by_username = serializers.SerializerMethodField()

    class Meta:
        model = ReportProfile
        fields = [
            "id", "code", "name", "modality", "parameters",
            "version", "status", "is_frozen", "revision_of",
            "activated_at", "activated_by", "activated_by_username",
            "archived_at", "archived_by", "archived_by_username",
            "used_by_reports", "can_edit", "can_delete",
            "is_active", "created_at", "updated_at"
        ]
        read_only_fields = [
            "version", "revision_of", "activated_at", "activated_by",
            "archived_at", "archived_by", "used_by_reports", "can_edit", "can_delete"
        ]

    def get_used_by_reports(self, obj):
        return obj.used_by_reports_count
    
    def get_can_edit(self, obj):
        can, _ = obj.can_edit()
        return can
    
    def get_can_delete(self, obj):
        can, _ = obj.can_delete()
        return can
    
    def get_activated_by_username(self, obj):
        return obj.activated_by.username if obj.activated_by else None
    
    def get_archived_by_username(self, obj):
        return obj.archived_by.username if obj.archived_by else None

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
                "type": p.parameter_type,
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
                "type": item.parameter_type,
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

class ReportInstanceV2Serializer(serializers.ModelSerializer):
    class Meta:
        model = ReportInstanceV2
        fields = ["values_json"]

class ReportSaveItemSerializer(serializers.Serializer):
    parameter_id = serializers.UUIDField()
    value = serializers.JSONField(allow_null=True) # Allow any type as specified

class ReportSaveSerializer(serializers.Serializer):
    """
    Serializer to accept a list of values to save.
    Example: { "values": [ { "parameter_id": "<uuid>", "value": <any> } ] }
    """
    values = ReportSaveItemSerializer(many=True)


class TemplateAuditLogSerializer(serializers.ModelSerializer):
    """Serializer for template governance audit logs."""
    actor_username = serializers.SerializerMethodField()
    actor_email = serializers.SerializerMethodField()

    class Meta:
        model = TemplateAuditLog
        fields = [
            "id", "actor", "actor_username", "actor_email",
            "action", "entity_type", "entity_id",
            "timestamp", "metadata"
        ]
        read_only_fields = fields

    def get_actor_username(self, obj):
        return obj.actor.username if obj.actor else None

    def get_actor_email(self, obj):
        return obj.actor.email if obj.actor else None


class ProfileListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for profiles list without parameters."""
    used_by_reports = serializers.SerializerMethodField()

    class Meta:
        model = ReportProfile
        fields = [
            "id", "code", "name", "modality", 
            "version", "status", "is_frozen",
            "used_by_reports", "is_active",
            "created_at", "updated_at"
        ]

    def get_used_by_reports(self, obj):
        return obj.used_by_reports_count
