from rest_framework import serializers
from django.utils import timezone
from .models import Study

class StudySerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.name", read_only=True)
    service_name = serializers.CharField(source="service.name", read_only=True)
    modality = serializers.CharField(source="service.modality.code", read_only=True)
    accession = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Study
        fields = "__all__"
        read_only_fields = ["created_at"]

    def generate_accession(self):
        """Generate a unique accession number based on date and time"""
        now = timezone.now()
        prefix = now.strftime("%Y%m%d")
        # Get count of studies today to append sequence number
        today_count = Study.objects.filter(accession__startswith=prefix).count()
        sequence = str(today_count + 1).zfill(4)
        return f"{prefix}{sequence}"

    def create(self, validated_data):
        if not validated_data.get("accession"):
            validated_data["accession"] = self.generate_accession()
        if not validated_data.get("created_by") and "request" in self.context:
            validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)
