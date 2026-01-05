from rest_framework import serializers
from .models import Study

class StudySerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.name", read_only=True)
    service_name = serializers.CharField(source="service.name", read_only=True)
    modality = serializers.CharField(source="service.modality.code", read_only=True)

    class Meta:
        model = Study
        fields = "__all__"
