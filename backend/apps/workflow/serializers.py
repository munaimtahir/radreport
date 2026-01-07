from rest_framework import serializers
from django.utils import timezone
from decimal import Decimal
from .models import (
    ServiceCatalog, ServiceVisit, Invoice, Payment,
    USGReport, OPDVitals, OPDConsult, StatusAuditLog
)
from apps.patients.models import Patient
from apps.patients.serializers import PatientSerializer


class ServiceCatalogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceCatalog
        fields = "__all__"
        read_only_fields = ["created_at", "updated_at"]


class StatusAuditLogSerializer(serializers.ModelSerializer):
    changed_by_name = serializers.CharField(source="changed_by.username", read_only=True)
    
    class Meta:
        model = StatusAuditLog
        fields = "__all__"
        read_only_fields = ["changed_at"]


class ServiceVisitSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.name", read_only=True)
    patient_reg_no = serializers.CharField(source="patient.patient_reg_no", read_only=True)
    patient_mrn = serializers.CharField(source="patient.mrn", read_only=True)
    service_name = serializers.CharField(source="service.name", read_only=True)
    service_code = serializers.CharField(source="service.code", read_only=True)
    created_by_name = serializers.CharField(source="created_by.username", read_only=True)
    assigned_to_name = serializers.CharField(source="assigned_to.username", read_only=True)
    status_audit_logs = StatusAuditLogSerializer(many=True, read_only=True)
    
    class Meta:
        model = ServiceVisit
        fields = "__all__"
        read_only_fields = ["visit_id", "registered_at", "updated_at"]


class InvoiceSerializer(serializers.ModelSerializer):
    service_visit_id = serializers.UUIDField(source="service_visit.id", read_only=True)
    visit_id = serializers.CharField(source="service_visit.visit_id", read_only=True)
    
    class Meta:
        model = Invoice
        fields = "__all__"
        read_only_fields = ["created_at", "updated_at"]


class PaymentSerializer(serializers.ModelSerializer):
    service_visit_id = serializers.UUIDField(source="service_visit.id", read_only=True)
    visit_id = serializers.CharField(source="service_visit.visit_id", read_only=True)
    received_by_name = serializers.CharField(source="received_by.username", read_only=True)
    
    class Meta:
        model = Payment
        fields = "__all__"
        read_only_fields = ["received_at"]


class USGReportSerializer(serializers.ModelSerializer):
    service_visit_id = serializers.UUIDField(source="service_visit.id", read_only=True)
    visit_id = serializers.CharField(source="service_visit.visit_id", read_only=True)
    created_by_name = serializers.CharField(source="created_by.username", read_only=True)
    updated_by_name = serializers.CharField(source="updated_by.username", read_only=True)
    verifier_name = serializers.CharField(source="verifier.username", read_only=True)
    published_pdf_url = serializers.SerializerMethodField()
    
    class Meta:
        model = USGReport
        fields = "__all__"
        read_only_fields = ["saved_at", "published_pdf_path", "verified_at"]
    
    def get_published_pdf_url(self, obj):
        if obj.published_pdf_path:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(f"/api/pdf/report/{obj.service_visit.id}/")
        return None


class OPDVitalsSerializer(serializers.ModelSerializer):
    service_visit_id = serializers.UUIDField(source="service_visit.id", read_only=True)
    visit_id = serializers.CharField(source="service_visit.visit_id", read_only=True)
    entered_by_name = serializers.CharField(source="entered_by.username", read_only=True)
    
    class Meta:
        model = OPDVitals
        fields = "__all__"
        read_only_fields = ["entered_at"]


class OPDConsultSerializer(serializers.ModelSerializer):
    service_visit_id = serializers.UUIDField(source="service_visit.id", read_only=True)
    visit_id = serializers.CharField(source="service_visit.visit_id", read_only=True)
    consultant_name = serializers.CharField(source="consultant.username", read_only=True)
    published_pdf_url = serializers.SerializerMethodField()
    
    class Meta:
        model = OPDConsult
        fields = "__all__"
        read_only_fields = ["consult_at", "published_pdf_path"]
    
    def get_published_pdf_url(self, obj):
        if obj.published_pdf_path:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(f"/api/pdf/prescription/{obj.service_visit.id}/")
        return None


class ServiceVisitCreateSerializer(serializers.Serializer):
    """Serializer for creating service visit at registration"""
    patient_id = serializers.UUIDField(required=False, allow_null=True)
    # Patient fields (if creating new)
    name = serializers.CharField(max_length=200, required=False)
    age = serializers.IntegerField(required=False, allow_null=True)
    date_of_birth = serializers.DateField(required=False, allow_null=True)
    gender = serializers.CharField(max_length=20, required=False, allow_blank=True)
    phone = serializers.CharField(max_length=30, required=False, allow_blank=True)
    address = serializers.CharField(max_length=300, required=False, allow_blank=True)
    
    # Service visit fields
    service_id = serializers.UUIDField(required=True)
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=True)
    discount = serializers.DecimalField(max_digits=10, decimal_places=2, default=0)
    net_amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=True)
    balance_amount = serializers.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Payment fields
    amount_paid = serializers.DecimalField(max_digits=10, decimal_places=2, required=True)
    payment_method = serializers.ChoiceField(choices=Payment._meta.get_field('method').choices, default="cash")
    
    def validate(self, data):
        """Validate that either patient_id or patient fields are provided"""
        patient_id = data.get("patient_id")
        patient_fields = ["name"]
        
        if not patient_id and not any(data.get(field) for field in patient_fields):
            raise serializers.ValidationError("Either patient_id or patient name must be provided")
        
        return data
    
    def create(self, validated_data):
        request = self.context.get("request")
        
        # Get or create patient
        patient_id = validated_data.pop("patient_id", None)
        if patient_id:
            patient = Patient.objects.get(id=patient_id)
        else:
            patient_data = {
                k: v for k, v in validated_data.items()
                if k in ["name", "age", "date_of_birth", "gender", "phone", "address"]
            }
            patient = Patient.objects.create(**patient_data)
        
        # Get service
        service = ServiceCatalog.objects.get(id=validated_data["service_id"])
        
        # Create service visit
        service_visit = ServiceVisit.objects.create(
            patient=patient,
            service=service,
            status="REGISTERED",
            created_by=request.user if request else None,
        )
        
        # Create invoice
        invoice = Invoice.objects.create(
            service_visit=service_visit,
            total_amount=validated_data["total_amount"],
            discount=validated_data.get("discount", Decimal("0")),
            net_amount=validated_data["net_amount"],
            balance_amount=validated_data.get("balance_amount", Decimal("0")),
        )
        
        # Create payment
        payment = Payment.objects.create(
            service_visit=service_visit,
            amount_paid=validated_data["amount_paid"],
            method=validated_data.get("payment_method", "cash"),
            received_by=request.user if request else None,
        )
        
        # Log status transition
        StatusAuditLog.objects.create(
            service_visit=service_visit,
            from_status="REGISTERED",
            to_status="REGISTERED",
            changed_by=request.user if request else None,
        )
        
        return service_visit


class StatusTransitionSerializer(serializers.Serializer):
    """Serializer for status transitions"""
    to_status = serializers.ChoiceField(choices=ServiceVisit._meta.get_field('status').choices)
    reason = serializers.CharField(required=False, allow_blank=True, allow_null=True)
