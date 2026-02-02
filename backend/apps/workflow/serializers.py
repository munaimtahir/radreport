from rest_framework import serializers
from django.utils import timezone
from decimal import Decimal
from .models import (
    ServiceVisit, ServiceVisitItem, Invoice, Payment,
    OPDVitals, OPDConsult, StatusAuditLog
)
from .receipts import create_receipt_snapshot
from apps.patients.models import Patient
from apps.consultants.models import ConsultantProfile
from apps.patients.serializers import PatientSerializer
from apps.catalog.models import Service as CatalogService



class ServiceVisitItemSerializer(serializers.ModelSerializer):
    """PHASE C: Item-centric serializer - primary source of truth for workflow status"""
    service_name = serializers.CharField(source="service.name", read_only=True)
    service_code = serializers.CharField(source="service.code", read_only=True)
    service_category = serializers.CharField(source="service.category", read_only=True)
    
    # Visit and patient info for worklists
    visit_id = serializers.CharField(source="service_visit.visit_id", read_only=True)
    service_visit_id = serializers.UUIDField(source="service_visit.id", read_only=True)
    patient_name = serializers.CharField(source="service_visit.patient.name", read_only=True)
    patient_mrn = serializers.CharField(source="service_visit.patient.mrn", read_only=True)
    patient_reg_no = serializers.CharField(source="service_visit.patient.patient_reg_no", read_only=True)
    
    # Report info
    report_status = serializers.SerializerMethodField()
    profile_code = serializers.SerializerMethodField()
    
    # Audit logs
    status_audit_logs = serializers.SerializerMethodField()

    class Meta:
        model = ServiceVisitItem
        fields = "__all__"
        read_only_fields = ["created_at", "updated_at", "started_at", "submitted_at", "verified_at", "published_at"]
    
    def get_report_status(self, obj):
        try:
            return obj.report_instance.status
        except:
            return None

    def get_profile_code(self, obj):
        from django.apps import apps
        try:
            ServiceReportProfile = apps.get_model('reporting', 'ServiceReportProfile')
            # Check mapping for service
            srp = ServiceReportProfile.objects.filter(service=obj.service).select_related('profile').first()
            return srp.profile.code if srp else None
        except LookupError:
            return None

    def get_status_audit_logs(self, obj):
        """Get audit logs for this item"""
        logs = obj.status_audit_logs.all()[:10]  # Last 10 logs
        return StatusAuditLogSerializer(logs, many=True, context=self.context).data




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
    # Legacy fields (for backward compatibility)
    service_name = serializers.SerializerMethodField()
    service_code = serializers.SerializerMethodField()
    # New: items relationship
    items = ServiceVisitItemSerializer(many=True, read_only=True)
    invoice = serializers.SerializerMethodField()
    created_by_name = serializers.CharField(source="created_by.username", read_only=True)
    assigned_to_name = serializers.CharField(source="assigned_to.username", read_only=True)
    status_audit_logs = StatusAuditLogSerializer(many=True, read_only=True)
    
    class Meta:
        model = ServiceVisit
        fields = "__all__"
        read_only_fields = ["visit_id", "registered_at", "updated_at"]
    
    def get_service_name(self, obj):
        """Return first item's service name, or legacy service name"""
        if obj.items.exists():
            return obj.items.first().service_name_snapshot
        return obj.service.name if obj.service else None
    
    def get_service_code(self, obj):
        """Return first item's service code, or legacy service code"""
        if obj.items.exists():
            return obj.items.first().service.code if obj.items.first().service else None
        return obj.service.code if obj.service else None
    
    def get_invoice(self, obj):
        """Return invoice if exists"""
        try:
            return InvoiceSerializer(obj.invoice).data
        except:
            return None


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





class OPDVitalsSerializer(serializers.ModelSerializer):
    service_visit_id = serializers.SerializerMethodField()
    visit_id = serializers.SerializerMethodField()
    
    def get_service_visit_id(self, obj):
        sv = obj.service_visit_item.service_visit if obj.service_visit_item else obj.service_visit
        return str(sv.id) if sv else None
    
    def get_visit_id(self, obj):
        sv = obj.service_visit_item.service_visit if obj.service_visit_item else obj.service_visit
        return sv.visit_id if sv else None
    entered_by_name = serializers.CharField(source="entered_by.username", read_only=True)
    
    class Meta:
        model = OPDVitals
        fields = "__all__"
        read_only_fields = ["entered_at"]


class OPDConsultSerializer(serializers.ModelSerializer):
    service_visit_id = serializers.SerializerMethodField()
    visit_id = serializers.SerializerMethodField()
    
    def get_service_visit_id(self, obj):
        sv = obj.service_visit_item.service_visit if obj.service_visit_item else obj.service_visit
        return str(sv.id) if sv else None
    
    def get_visit_id(self, obj):
        sv = obj.service_visit_item.service_visit if obj.service_visit_item else obj.service_visit
        return sv.visit_id if sv else None
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
                sv = obj.service_visit_item.service_visit if obj.service_visit_item else obj.service_visit
                if sv:
                    return request.build_absolute_uri(f"/api/pdf/{sv.id}/prescription/")
        return None


class ServiceVisitItemInputSerializer(serializers.Serializer):
    service_id = serializers.UUIDField()
    consultant_id = serializers.UUIDField(required=False, allow_null=True)


class ServiceVisitCreateSerializer(serializers.Serializer):
    """Serializer for creating service visit at registration with multiple services"""
    patient_id = serializers.UUIDField(required=False, allow_null=True)
    # Patient fields (if creating new)
    name = serializers.CharField(max_length=200, required=False)
    age = serializers.IntegerField(required=False, allow_null=True)
    date_of_birth = serializers.DateField(required=False, allow_null=True)
    gender = serializers.CharField(max_length=20, required=False, allow_blank=True)
    phone = serializers.CharField(max_length=30, required=False, allow_blank=True)
    address = serializers.CharField(max_length=300, required=False, allow_blank=True)
    
    # Service fields - NEW: supports multiple services
    service_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        min_length=1,
        help_text="List of catalog.Service IDs to order"
    )
    service_items = serializers.ListField(
        child=ServiceVisitItemInputSerializer(),
        required=False,
        help_text="Optional list of {service_id, consultant_id} entries",
    )
    # Legacy single service_id (for backward compatibility)
    service_id = serializers.UUIDField(required=False, allow_null=True)

    booked_consultant_id = serializers.UUIDField(required=False, allow_null=True)
    referring_consultant = serializers.CharField(max_length=150, required=False, allow_blank=True)
    
    # Billing fields
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, required=True)
    discount = serializers.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_percentage = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, allow_null=True)
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=True)
    net_amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    
    # Payment fields
    amount_paid = serializers.DecimalField(max_digits=10, decimal_places=2, required=True)
    payment_method = serializers.ChoiceField(choices=Payment._meta.get_field('method').choices, default="cash")
    
    def validate(self, data):
        """Validate that either patient_id or patient fields are provided"""
        patient_id = data.get("patient_id")
        patient_fields = ["name"]
        
        if not patient_id and not any(data.get(field) for field in patient_fields):
            raise serializers.ValidationError("Either patient_id or patient name must be provided")
        
        # Ensure service_ids/service_items or service_id is provided
        service_items = data.get("service_items") or []
        service_ids = data.get("service_ids", [])
        service_id = data.get("service_id")
        if not service_ids and not service_id and not service_items:
            raise serializers.ValidationError("Either service_ids or service_id must be provided")
        
        return data
    
    def create(self, validated_data):
        from django.db import transaction
        request = self.context.get("request")
        
        with transaction.atomic():
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
            
            # Get services - support both new (service_ids) and legacy (service_id) formats
            referring_consultant = validated_data.get("referring_consultant", "")
            service_items = validated_data.get("service_items") or []
            service_ids = validated_data.get("service_ids", [])
            legacy_service_id = validated_data.get("service_id")

            if not service_ids and legacy_service_id:
                service_ids = [legacy_service_id]
            if service_items:
                service_ids = [item.get("service_id") for item in service_items if item.get("service_id")]

            services = CatalogService.objects.filter(id__in=service_ids, is_active=True)
            if services.count() != len(service_ids):
                raise serializers.ValidationError("One or more services not found or inactive")

            booked_consultant = None
            booked_consultant_id = validated_data.get("booked_consultant_id")
            if booked_consultant_id:
                try:
                    booked_consultant = ConsultantProfile.objects.get(id=booked_consultant_id)
                except ConsultantProfile.DoesNotExist:
                    raise serializers.ValidationError("Booked consultant not found")
            
            # Create service visit (without legacy service FK)
            service_visit = ServiceVisit.objects.create(
                patient=patient,
                status="REGISTERED",
                created_by=request.user if request else None,
                booked_consultant=booked_consultant,
                referring_consultant=referring_consultant,
            )
            
            # Create ServiceVisitItems with snapshots
            items = []
            subtotal = Decimal("0")
            service_lookup = {str(service.id): service for service in services}
            if service_items:
                items_payload = service_items
            else:
                items_payload = [{"service_id": str(service.id)} for service in services]

            for payload in items_payload:
                service = service_lookup.get(str(payload.get("service_id")))
                if not service:
                    raise serializers.ValidationError("One or more services not found or inactive")
                # Set department_snapshot: prefer modality code (USG, CT, etc.) for workflow filtering
                # Fallback to category (Radiology, OPD, etc.) if no modality
                dept_snapshot = ""
                if service.modality and service.modality.code:
                    dept_snapshot = service.modality.code  # USG, CT, XRAY, etc.
                elif service.category:
                    dept_snapshot = service.category  # Radiology, OPD, etc.
                item_consultant = booked_consultant
                consultant_id = payload.get("consultant_id")
                if consultant_id:
                    try:
                        item_consultant = ConsultantProfile.objects.get(id=consultant_id)
                    except ConsultantProfile.DoesNotExist:
                        raise serializers.ValidationError("Item consultant not found")

                item = ServiceVisitItem.objects.create(
                    service_visit=service_visit,
                    service=service,
                    consultant=item_consultant,
                    service_name_snapshot=service.name,
                    department_snapshot=dept_snapshot,
                    price_snapshot=service.price,
                    status="REGISTERED",
                )
                items.append(item)
                subtotal += service.price
            
            # Calculate amounts
            subtotal_calc = validated_data.get("subtotal", subtotal)
            discount = validated_data.get("discount", Decimal("0"))
            discount_percentage = validated_data.get("discount_percentage")
            
            # Apply discount percentage if provided
            if discount_percentage:
                discount = subtotal_calc * (discount_percentage / Decimal("100"))
            
            total_amount = validated_data.get("total_amount", subtotal_calc - discount)
            net_amount = validated_data.get("net_amount", total_amount)
            amount_paid = validated_data.get("amount_paid", Decimal("0"))
            balance_amount = net_amount - amount_paid
            
            # Create invoice
            invoice = Invoice.objects.create(
                service_visit=service_visit,
                subtotal=subtotal_calc,
                discount=discount,
                discount_percentage=discount_percentage,
                total_amount=total_amount,
                net_amount=net_amount,
                balance_amount=max(Decimal("0"), balance_amount),
            )
            
            # Generate receipt number on invoice creation (idempotent - can be regenerated on print)
            # Receipt number is generated when invoice is created OR when receipt is printed
            # This ensures receipt number exists even if paid=0
            if not invoice.receipt_number:
                from apps.studies.models import ReceiptSequence
                invoice.receipt_number = ReceiptSequence.get_next_receipt_number()
                invoice.save()
            
            # Create payment if amount_paid > 0
            if amount_paid > 0:
                payment = Payment.objects.create(
                    service_visit=service_visit,
                    amount_paid=amount_paid,
                    method=validated_data.get("payment_method", "cash"),
                    received_by=request.user if request else None,
                )
                # Recalculate balance after payment
                invoice.calculate_balance()
                invoice.save()

            # Snapshot receipt data once issued (immutable, read-only reprints)
            create_receipt_snapshot(service_visit, invoice)
            
            # PHASE C: Update derived status after creating items
            service_visit.update_derived_status()
            
            # Log status transition
            StatusAuditLog.objects.create(
                service_visit=service_visit,
                from_status="REGISTERED",
                to_status=service_visit.status,
                changed_by=request.user if request else None,
            )
            
            return service_visit


class StatusTransitionSerializer(serializers.Serializer):
    """Serializer for status transitions"""
    to_status = serializers.ChoiceField(choices=ServiceVisit._meta.get_field('status').choices)
    reason = serializers.CharField(required=False, allow_blank=True, allow_null=True)
