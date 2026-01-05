from rest_framework import serializers
from .models import Modality, Service

class ModalitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Modality
        fields = "__all__"

class ServiceSerializer(serializers.ModelSerializer):
    modality_display = serializers.CharField(source="modality.code", read_only=True)
    class Meta:
        model = Service
        fields = "__all__"
