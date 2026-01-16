from rest_framework import serializers
from .models import Modality, Service

class ModalitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Modality
        fields = "__all__"

class ServiceSerializer(serializers.ModelSerializer):
    modality_display = serializers.CharField(source="modality.code", read_only=True)
    modality = ModalitySerializer(read_only=True)
    usage_count = serializers.SerializerMethodField()

    def get_usage_count(self, obj):
        return getattr(obj, "usage_count", 0)
    class Meta:
        model = Service
        fields = "__all__"
