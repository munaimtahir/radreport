import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone

STUDY_STATUS = (
    ("registered", "Registered"),
    ("in_progress", "In Progress"),
    ("draft", "Draft"),
    ("final", "Final"),
    ("delivered", "Delivered"),
)

PAYMENT_METHOD_CHOICES = [
    ("cash", "Cash"),
    ("card", "Card"),
    ("online", "Online"),
    ("insurance", "Insurance"),
    ("other", "Other"),
]

class Visit(models.Model):
    """Represents a patient visit/transaction with billing information"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    visit_number = models.CharField(max_length=30, unique=True, editable=False)
    patient = models.ForeignKey("patients.Patient", on_delete=models.PROTECT, related_name="visits")
    
    # Billing fields (snapshot at time of creation)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    net_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    due_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, blank=True, default="")
    
    # Metadata
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    finalized_at = models.DateTimeField(null=True, blank=True)
    is_finalized = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["visit_number"]),
            models.Index(fields=["patient"]),
            models.Index(fields=["is_finalized"]),
        ]

    def generate_visit_number(self):
        """Generate a unique visit/examination number"""
        now = timezone.now()
        prefix = now.strftime("%Y%m%d")
        today_count = Visit.objects.filter(visit_number__startswith=f"VN{prefix}").count()
        sequence = str(today_count + 1).zfill(4)
        visit_number = f"VN{prefix}{sequence}"
        
        # Handle race condition: if visit_number exists, try next sequence
        max_attempts = 100
        attempt = 0
        while Visit.objects.filter(visit_number=visit_number).exists() and attempt < max_attempts:
            today_count += 1
            sequence = str(today_count + 1).zfill(4)
            visit_number = f"VN{prefix}{sequence}"
            attempt += 1
        
        return visit_number

    def save(self, *args, **kwargs):
        if not self.visit_number:
            self.visit_number = self.generate_visit_number()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.visit_number} - {self.patient.name}"

class OrderItem(models.Model):
    """Represents a service/item ordered in a visit"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    visit = models.ForeignKey(Visit, on_delete=models.CASCADE, related_name="items")
    service = models.ForeignKey("catalog.Service", on_delete=models.PROTECT, related_name="order_items")
    charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Snapshot of price at order time
    indication = models.CharField(max_length=300, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["visit"]),
            models.Index(fields=["service"]),
        ]

    def __str__(self):
        return f"{self.visit.visit_number} - {self.service.name}"

class Study(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    accession = models.CharField(max_length=30, unique=True)
    patient = models.ForeignKey("patients.Patient", on_delete=models.PROTECT, related_name="studies")
    service = models.ForeignKey("catalog.Service", on_delete=models.PROTECT, related_name="studies")
    visit = models.ForeignKey(Visit, on_delete=models.SET_NULL, null=True, blank=True, related_name="studies")
    order_item = models.ForeignKey(OrderItem, on_delete=models.SET_NULL, null=True, blank=True, related_name="studies")
    indication = models.CharField(max_length=300, blank=True, default="")
    status = models.CharField(max_length=20, choices=STUDY_STATUS, default="registered")
    performed_by = models.CharField(max_length=120, blank=True, default="")
    reported_by = models.CharField(max_length=120, blank=True, default="")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["accession"]),
            models.Index(fields=["status"]),
            models.Index(fields=["visit"]),
        ]

    def __str__(self):
        return f"{self.accession} - {self.patient.name} - {self.service.name}"
