import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.db import transaction

# ServiceVisit Status Choices
SERVICE_VISIT_STATUS = (
    ("REGISTERED", "Registered"),
    ("IN_PROGRESS", "In Progress"),
    ("PENDING_VERIFICATION", "Pending Verification"),
    ("RETURNED_FOR_CORRECTION", "Returned for Correction"),
    ("PUBLISHED", "Published"),
    ("CANCELLED", "Cancelled"),
)

PAYMENT_METHOD_CHOICES = [
    ("cash", "Cash"),
    ("card", "Card"),
    ("online", "Online"),
    ("insurance", "Insurance"),
    ("other", "Other"),
]


class ServiceCatalog(models.Model):
    """Service catalog for USG, OPD, etc."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=150)
    default_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    turnaround_time = models.PositiveIntegerField(default=60, help_text="Turnaround time in minutes")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["code"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"


class ServiceVisit(models.Model):
    """Core workflow model - represents a service visit that moves through desks"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    visit_id = models.CharField(max_length=30, unique=True, editable=False, db_index=True)
    patient = models.ForeignKey("patients.Patient", on_delete=models.PROTECT, related_name="service_visits")
    service = models.ForeignKey(ServiceCatalog, on_delete=models.PROTECT, related_name="service_visits")
    status = models.CharField(max_length=30, choices=SERVICE_VISIT_STATUS, default="REGISTERED", db_index=True)
    
    # Assignment
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="created_service_visits")
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_service_visits")
    
    # Timestamps
    registered_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-registered_at"]
        indexes = [
            models.Index(fields=["visit_id"]),
            models.Index(fields=["status"]),
            models.Index(fields=["patient"]),
            models.Index(fields=["service"]),
            models.Index(fields=["registered_at"]),
        ]

    def generate_visit_id(self):
        """Generate unique ServiceVisitID"""
        now = timezone.now()
        prefix = now.strftime("%Y%m%d")
        today_count = ServiceVisit.objects.filter(visit_id__startswith=f"SV{prefix}").count()
        sequence = str(today_count + 1).zfill(4)
        visit_id = f"SV{prefix}{sequence}"
        
        max_attempts = 100
        attempt = 0
        while ServiceVisit.objects.filter(visit_id=visit_id).exists() and attempt < max_attempts:
            today_count += 1
            sequence = str(today_count + 1).zfill(4)
            visit_id = f"SV{prefix}{sequence}"
            attempt += 1
        
        return visit_id

    def save(self, *args, **kwargs):
        if not self.visit_id:
            self.visit_id = self.generate_visit_id()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.visit_id} - {self.patient.name} - {self.service.name}"


class Invoice(models.Model):
    """Invoice for a service visit"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service_visit = models.OneToOneField(ServiceVisit, on_delete=models.CASCADE, related_name="invoice")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    net_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    balance_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Invoice for {self.service_visit.visit_id}"


class Payment(models.Model):
    """Payment record for a service visit"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service_visit = models.ForeignKey(ServiceVisit, on_delete=models.CASCADE, related_name="payments")
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default="cash")
    received_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-received_at"]

    def __str__(self):
        return f"Payment {self.amount_paid} for {self.service_visit.visit_id}"


class USGReport(models.Model):
    """USG report data"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service_visit = models.OneToOneField(ServiceVisit, on_delete=models.CASCADE, related_name="usg_report")
    report_json = models.JSONField(default=dict, help_text="Structured report data")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="created_usg_reports")
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="updated_usg_reports")
    saved_at = models.DateTimeField(auto_now=True)
    published_pdf_path = models.CharField(max_length=500, blank=True, default="")
    verifier = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="verified_usg_reports")
    verified_at = models.DateTimeField(null=True, blank=True)
    return_reason = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["-saved_at"]

    def __str__(self):
        return f"USG Report for {self.service_visit.visit_id}"


class OPDVitals(models.Model):
    """OPD vitals data"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service_visit = models.OneToOneField(ServiceVisit, on_delete=models.CASCADE, related_name="opd_vitals")
    bp_systolic = models.PositiveIntegerField(null=True, blank=True)
    bp_diastolic = models.PositiveIntegerField(null=True, blank=True)
    pulse = models.PositiveIntegerField(null=True, blank=True)
    temperature = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    respiratory_rate = models.PositiveIntegerField(null=True, blank=True)
    spo2 = models.PositiveIntegerField(null=True, blank=True, help_text="SpO2 percentage")
    weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    height = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    bmi = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    entered_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    entered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-entered_at"]

    def __str__(self):
        return f"OPD Vitals for {self.service_visit.visit_id}"


class OPDConsult(models.Model):
    """OPD consultation data"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service_visit = models.OneToOneField(ServiceVisit, on_delete=models.CASCADE, related_name="opd_consult")
    diagnosis = models.TextField(blank=True, default="")
    notes = models.TextField(blank=True, default="")
    medicines_json = models.JSONField(default=list, help_text="List of medicines prescribed")
    investigations_json = models.JSONField(default=list, help_text="List of investigations ordered")
    advice = models.TextField(blank=True, default="")
    followup = models.CharField(max_length=200, blank=True, default="")
    consultant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="opd_consults")
    consult_at = models.DateTimeField(auto_now_add=True)
    published_pdf_path = models.CharField(max_length=500, blank=True, default="")

    class Meta:
        ordering = ["-consult_at"]

    def __str__(self):
        return f"OPD Consult for {self.service_visit.visit_id}"


class StatusAuditLog(models.Model):
    """Audit log for status transitions"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service_visit = models.ForeignKey(ServiceVisit, on_delete=models.CASCADE, related_name="status_audit_logs")
    from_status = models.CharField(max_length=30, choices=SERVICE_VISIT_STATUS)
    to_status = models.CharField(max_length=30, choices=SERVICE_VISIT_STATUS)
    reason = models.TextField(blank=True, default="", null=True)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-changed_at"]
        indexes = [
            models.Index(fields=["service_visit"]),
            models.Index(fields=["changed_at"]),
        ]

    def __str__(self):
        return f"{self.service_visit.visit_id}: {self.from_status} -> {self.to_status}"
