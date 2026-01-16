from rest_framework import serializers
from .models import Modality, Service

class ModalitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Modality
        fields = "__all__"

class ServiceSerializer(serializers.ModelSerializer):
    modality_display = serializers.CharField(source="modality.code", read_only=True)
    modality = ModalitySerializer(read_only=True)
    usage_count = serializers.IntegerField(read_only=True, required=False, help_text="Usage count (only included in most-used endpoint)")
    class Meta:
        model = Service
        fields = "__all__"
