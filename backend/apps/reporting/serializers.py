from rest_framework import serializers
from .models import Report, ReportTemplateReport

class ReportSerializer(serializers.ModelSerializer):
    accession = serializers.CharField(source="study.accession", read_only=True)
    patient_name = serializers.CharField(source="study.patient.name", read_only=True)
    service_name = serializers.CharField(source="study.service.name", read_only=True)
    study_id = serializers.UUIDField(source="study.id", read_only=True)

    class Meta:
        model = Report
        fields = "__all__"
        read_only_fields = ["pdf_file","finalized_by","finalized_at","created_at","status"]


class ReportTemplateReportSerializer(serializers.ModelSerializer):
    template_id = serializers.UUIDField(source="template.id", read_only=True)

    class Meta:
        model = ReportTemplateReport
        fields = ["id", "service_visit_item", "template_id", "status", "values", "narrative_text", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]
