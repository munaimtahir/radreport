from rest_framework import serializers
from .models import Report

class ReportSerializer(serializers.ModelSerializer):
    accession = serializers.CharField(source="study.accession", read_only=True)
    patient_name = serializers.CharField(source="study.patient.name", read_only=True)
    service_name = serializers.CharField(source="study.service.name", read_only=True)

    class Meta:
        model = Report
        fields = "__all__"
        read_only_fields = ["pdf_file","finalized_by","finalized_at","created_at","status"]
