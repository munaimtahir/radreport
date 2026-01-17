from rest_framework import serializers
from .models import Modality, Service

class ModalitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Modality
        fields = "__all__"

class ServiceSerializer(serializers.ModelSerializer):
    modality_display = serializers.CharField(source="modality.code", read_only=True)
    modality = serializers.PrimaryKeyRelatedField(queryset=Modality.objects.all(), required=True)
    usage_count = serializers.SerializerMethodField()

    def get_usage_count(self, obj):
        return getattr(obj, "usage_count", 0)

    class Meta:
        model = Service
        fields = [
            'id', 'code', 'modality', 'name', 'category', 'price', 'charges',
            'default_price', 'tat_value', 'tat_unit', 'tat_minutes', 'turnaround_time',
            'default_template', 'requires_radiologist_approval', 'is_active',
            'modality_display', 'usage_count'
        ]
