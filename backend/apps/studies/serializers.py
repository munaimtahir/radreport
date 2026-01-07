from rest_framework import serializers
from django.utils import timezone
from decimal import Decimal
from .models import Study, Visit, OrderItem

class OrderItemSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source="service.name", read_only=True)
    service_code = serializers.CharField(source="service.code", read_only=True)
    modality = serializers.CharField(source="service.modality.code", read_only=True)
    
    class Meta:
        model = OrderItem
        fields = "__all__"
        read_only_fields = ["created_at"]

class VisitSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    patient_name = serializers.CharField(source="patient.name", read_only=True)
    patient_mrn = serializers.CharField(source="patient.mrn", read_only=True)
    
    class Meta:
        model = Visit
        fields = "__all__"
        read_only_fields = ["visit_number", "created_at", "finalized_at"]

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

class UnifiedIntakeSerializer(serializers.Serializer):
    """Serializer for unified patient + exam intake"""
    # Patient fields
    patient_id = serializers.UUIDField(required=False, allow_null=True)
    name = serializers.CharField(max_length=200, required=False)
    age = serializers.IntegerField(required=False, allow_null=True)
    date_of_birth = serializers.DateField(required=False, allow_null=True)
    gender = serializers.CharField(max_length=20, required=False, allow_blank=True)
    phone = serializers.CharField(max_length=30, required=False, allow_blank=True)
    address = serializers.CharField(max_length=300, required=False, allow_blank=True)
    referrer = serializers.CharField(max_length=200, required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    
    # Services/Items
    items = serializers.ListField(
        child=serializers.DictField(),
        required=True,
        min_length=1
    )
    
    # Billing
    discount_amount = serializers.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_percentage = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, allow_null=True)
    paid_amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    payment_method = serializers.CharField(max_length=20, required=False, allow_blank=True)
    
    def validate_items(self, value):
        """Validate that each item has service_id and optional indication"""
        for item in value:
            if "service_id" not in item:
                raise serializers.ValidationError("Each item must have a service_id")
        return value
    
    def create(self, validated_data):
        from apps.patients.models import Patient
        from apps.catalog.models import Service
        
        request = self.context.get("request")
        items_data = validated_data.pop("items")
        discount_amount = validated_data.pop("discount_amount", Decimal("0"))
        discount_percentage = validated_data.pop("discount_percentage", None)
        paid_amount = validated_data.pop("paid_amount", None)
        payment_method = validated_data.pop("payment_method", "")
        
        # Get or create patient
        patient_id = validated_data.pop("patient_id", None)
        if patient_id:
            patient = Patient.objects.get(id=patient_id)
        else:
            # Create new patient
            patient_data = {
                k: v for k, v in validated_data.items()
                if k in ["name", "age", "date_of_birth", "gender", "phone", "address", "referrer", "notes"]
            }
            patient = Patient.objects.create(**patient_data)
        
        # Create visit
        visit = Visit.objects.create(
            patient=patient,
            created_by=request.user if request else None,
            discount_amount=discount_amount,
            discount_percentage=discount_percentage,
            payment_method=payment_method,
        )
        
        # Calculate subtotal from items
        subtotal = Decimal("0")
        order_items = []
        
        for item_data in items_data:
            service = Service.objects.get(id=item_data["service_id"])
            charge = service.charges or service.price
            subtotal += charge
            
            order_item = OrderItem.objects.create(
                visit=visit,
                service=service,
                charge=charge,
                indication=item_data.get("indication", ""),
            )
            order_items.append(order_item)
        
        # Calculate billing
        visit.subtotal = subtotal
        
        if discount_percentage:
            visit.discount_amount = subtotal * (discount_percentage / Decimal("100"))
        else:
            visit.discount_amount = discount_amount
        
        visit.net_total = subtotal - visit.discount_amount
        
        if paid_amount is None:
            visit.paid_amount = visit.net_total
        else:
            visit.paid_amount = paid_amount
        
        visit.due_amount = visit.net_total - visit.paid_amount
        visit.save()
        
        # Create studies for radiology services (workflow routing)
        from apps.studies.models import STUDY_STATUS
        
        for order_item in order_items:
            service = order_item.service
            # Create study for radiology services
            if service.category == "Radiology" or service.modality.code in ["USG", "CT", "XRAY"]:
                Study.objects.create(
                    patient=patient,
                    service=service,
                    visit=visit,
                    order_item=order_item,
                    indication=order_item.indication,
                    status=STUDY_STATUS[0][0],  # "registered"
                    created_by=request.user if request else None,
                )
        
        return visit
