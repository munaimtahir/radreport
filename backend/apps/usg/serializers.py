from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    UsgTemplate, UsgServiceProfile, UsgStudy,
    UsgFieldValue, UsgPublishedSnapshot
)

User = get_user_model()


class UsgTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UsgTemplate
        fields = [
            'id', 'code', 'name', 'category', 'version',
            'is_locked', 'schema_json', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class UsgServiceProfileSerializer(serializers.ModelSerializer):
    template_detail = UsgTemplateSerializer(source='template', read_only=True)
    
    class Meta:
        model = UsgServiceProfile
        fields = [
            'id', 'service_code', 'template', 'template_detail',
            'hidden_sections', 'forced_na_fields',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class UsgFieldValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = UsgFieldValue
        fields = [
            'id', 'study', 'field_key', 'value_json',
            'is_not_applicable', 'updated_by', 'updated_at'
        ]
        read_only_fields = ['id', 'updated_at']
    
    def validate(self, attrs):
        """Enforce immutability for published studies"""
        if self.instance and self.instance.study.status == 'published':
            raise serializers.ValidationError(
                "Published study is locked"
            )
        return attrs


class UsgFieldValueBulkSerializer(serializers.Serializer):
    """Serializer for bulk field value updates"""
    field_key = serializers.CharField(max_length=200)
    value_json = serializers.JSONField(required=False, allow_null=True)
    is_not_applicable = serializers.BooleanField(default=False)


class UsgStudySerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.name', read_only=True)
    patient_mrn = serializers.CharField(source='patient.mrn', read_only=True)
    visit_number = serializers.CharField(source='visit.visit_number', read_only=True)
    template_detail = UsgTemplateSerializer(source='template', read_only=True)
    field_values = UsgFieldValueSerializer(many=True, read_only=True)
    is_locked = serializers.BooleanField(read_only=True)
    service_profile = serializers.SerializerMethodField()
    hidden_sections = serializers.SerializerMethodField()
    forced_na_fields = serializers.SerializerMethodField()
    
    class Meta:
        model = UsgStudy
        fields = [
            'id', 'patient', 'patient_name', 'patient_mrn',
            'visit', 'visit_number', 'service_code',
            'template', 'template_detail', 'status',
            'created_by', 'verified_by', 'published_by',
            'created_at', 'verified_at', 'published_at',
            'lock_reason', 'field_values', 'is_locked',
            'service_profile', 'hidden_sections', 'forced_na_fields'
        ]
        read_only_fields = [
            'id', 'created_at', 'verified_at', 'published_at',
            'created_by', 'verified_by', 'published_by', 'is_locked'
        ]
    
    def validate(self, attrs):
        """Enforce immutability for published studies"""
        if self.instance and self.instance.status == 'published':
            # Only allow reading published studies, no updates
            if self.instance.status != attrs.get('status', self.instance.status):
                raise serializers.ValidationError(
                    "Published study is locked"
                )
        return attrs

    def _get_service_profile(self, obj):
        if not hasattr(self, '_service_profile_cache'):
            self._service_profile_cache = {}
        cache_key = obj.service_code
        if cache_key not in self._service_profile_cache:
            self._service_profile_cache[cache_key] = UsgServiceProfile.objects.select_related('template').filter(
                service_code=obj.service_code
            ).first()
        return self._service_profile_cache[cache_key]

    def get_service_profile(self, obj):
        profile = self._get_service_profile(obj)
        if not profile:
            return None
        return {
            'id': str(profile.id),
            'service_code': profile.service_code,
            'template': str(profile.template_id),
            'template_code': profile.template.code,
            'hidden_sections': profile.hidden_sections,
            'forced_na_fields': profile.forced_na_fields,
        }

    def get_hidden_sections(self, obj):
        profile = self._get_service_profile(obj)
        return profile.hidden_sections if profile else []

    def get_forced_na_fields(self, obj):
        profile = self._get_service_profile(obj)
        return profile.forced_na_fields if profile else []


class UsgPublishedSnapshotSerializer(serializers.ModelSerializer):
    study_detail = UsgStudySerializer(source='study', read_only=True)
    
    class Meta:
        model = UsgPublishedSnapshot
        fields = [
            'id', 'study', 'study_detail', 'template_code',
            'template_version', 'renderer_version',
            'published_json_snapshot', 'published_text_snapshot',
            'template_snapshot', 'pdf_file_path',
            'pdf_drive_file_id', 'pdf_drive_folder_id',
            'pdf_sha256', 'published_at', 'published_by', 'audit_note'
        ]
        read_only_fields = '__all__'  # All fields are read-only
