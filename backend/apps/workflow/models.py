import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from decimal import Decimal

# ServiceVisit Status Choices
SERVICE_VISIT_STATUS = (
    ("REGISTERED", "Registered"),
    ("IN_PROGRESS", "In Progress"),
    ("PENDING_VERIFICATION", "Pending Verification"),
    ("RETURNED_FOR_CORRECTION", "Returned for Correction"),
    ("FINALIZED", "Finalized"),  # PHASE C: For OPD workflow
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


# ServiceCatalog is DEPRECATED - use catalog.Service instead
# Keeping for migration compatibility only
class ServiceCatalog(models.Model):
    """DEPRECATED: Use catalog.Service instead. This model is kept for migration compatibility only."""
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
        verbose_name = "Service Catalog (Deprecated)"
        verbose_name_plural = "Service Catalogs (Deprecated)"

    def __str__(self):
        return f"{self.code} - {self.name} (DEPRECATED)"


class ServiceVisit(models.Model):
    """Core workflow model - represents a service visit that moves through desks
    
    PHASE C: status is now DERIVED from ServiceVisitItem.status values.
    This field is kept for backward compatibility and is auto-updated when items change.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    visit_id = models.CharField(max_length=30, unique=True, editable=False, db_index=True)
    patient = models.ForeignKey("patients.Patient", on_delete=models.PROTECT, related_name="service_visits")
    # DEPRECATED: service field kept for migration compatibility. Use items relationship instead.
    service = models.ForeignKey(ServiceCatalog, on_delete=models.PROTECT, related_name="service_visits", null=True, blank=True)
    # PHASE C: status is DERIVED from items - do not set manually
    status = models.CharField(max_length=30, choices=SERVICE_VISIT_STATUS, default="REGISTERED", db_index=True, editable=False, help_text="DERIVED: Auto-calculated from ServiceVisitItem.status values")
    
    # Assignment
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="created_service_visits")
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_service_visits")
    booked_consultant = models.ForeignKey(
        "consultants.ConsultantProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="booked_visits",
    )
    
    # Timestamps
    registered_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def derive_status(self):
        """
        PHASE C: Derive visit status from item statuses.
        Rule:
        - If any item is PENDING_VERIFICATION => PENDING_VERIFICATION
        - Else if any item is IN_PROGRESS => IN_PROGRESS
        - Else if any item is RETURNED_FOR_CORRECTION => RETURNED_FOR_CORRECTION
        - Else if any item is FINALIZED => FINALIZED
        - Else if all items are PUBLISHED => PUBLISHED
        - Else if all items are CANCELLED => CANCELLED
        - Else REGISTERED
        """
        items = self.items.all()
        if not items.exists():
            return "REGISTERED"
        
        statuses = [item.status for item in items]
        
        # Priority order (highest first)
        if "PENDING_VERIFICATION" in statuses:
            return "PENDING_VERIFICATION"
        elif "IN_PROGRESS" in statuses:
            return "IN_PROGRESS"
        elif "RETURNED_FOR_CORRECTION" in statuses:
            return "RETURNED_FOR_CORRECTION"
        elif "FINALIZED" in statuses:
            return "FINALIZED"
        elif all(s == "PUBLISHED" for s in statuses):
            return "PUBLISHED"
        elif all(s == "CANCELLED" for s in statuses):
            return "CANCELLED"
        else:
            return "REGISTERED"
    
    def update_derived_status(self):
        """Update the derived status field (called after item status changes)"""
        new_status = self.derive_status()
        if self.status != new_status:
            self.status = new_status
            self.save(update_fields=['status'])

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
        service_name = self.service.name if self.service else "Multiple Services"
        return f"{self.visit_id} - {self.patient.name} - {service_name}"


class ServiceVisitItem(models.Model):
    """Line item for a service visit - supports multiple services per visit
    
    PHASE C: status is the PRIMARY source of truth for workflow state.
    ServiceVisit.status is derived from item statuses.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service_visit = models.ForeignKey(ServiceVisit, on_delete=models.CASCADE, related_name="items")
    service = models.ForeignKey("catalog.Service", on_delete=models.PROTECT, related_name="service_visit_items")
    consultant = models.ForeignKey(
        "consultants.ConsultantProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="service_visit_items",
    )
    
    # Snapshots at time of billing
    service_name_snapshot = models.CharField(max_length=150, help_text="Service name at time of order")
    department_snapshot = models.CharField(max_length=50, help_text="Department/category at time of order (USG/OPD/etc)")
    price_snapshot = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price at time of order")
    
    # PHASE C: Per-item status is PRIMARY - drives worklists, permissions, actions
    status = models.CharField(max_length=30, choices=SERVICE_VISIT_STATUS, default="REGISTERED", db_index=True)
    
    # Timestamps for workflow tracking
    started_at = models.DateTimeField(null=True, blank=True, help_text="When item moved to IN_PROGRESS")
    submitted_at = models.DateTimeField(null=True, blank=True, help_text="When item moved to PENDING_VERIFICATION")
    verified_at = models.DateTimeField(null=True, blank=True, help_text="When item was verified")
    published_at = models.DateTimeField(null=True, blank=True, help_text="When item was published")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["service_visit"]),
            models.Index(fields=["service"]),
            models.Index(fields=["status"]),
        ]

    def save(self, *args, **kwargs):
        """Auto-populate snapshots from service if not set"""
        if not self.service_name_snapshot and self.service:
            self.service_name_snapshot = self.service.name
        if not self.department_snapshot and self.service:
            # Prefer modality code (USG, CT, etc.) for workflow filtering, fallback to category
            if self.service.modality and self.service.modality.code:
                self.department_snapshot = self.service.modality.code
            elif self.service.category:
                self.department_snapshot = self.service.category
        if not self.price_snapshot and self.service:
            self.price_snapshot = self.service.price
        
        # Track if status changed
        status_changed = False
        if self.pk:
            try:
                old_item = ServiceVisitItem.objects.get(pk=self.pk)
                status_changed = old_item.status != self.status
            except ServiceVisitItem.DoesNotExist:
                status_changed = True
        else:
            status_changed = True
        
        super().save(*args, **kwargs)
        
        # PHASE C: Update derived visit status when item status changes
        if status_changed and self.service_visit_id:
            self.service_visit.update_derived_status()

    def __str__(self):
        return f"{self.service_visit.visit_id} - {self.service_name_snapshot}"


class Invoice(models.Model):
    """Invoice for a service visit"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service_visit = models.OneToOneField(ServiceVisit, on_delete=models.CASCADE, related_name="invoice")
    
    # Billing amounts
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Sum of line items before discount")
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Discount amount (fixed)")
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Discount percentage (if applicable)")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Subtotal - discount")
    net_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Alias for total_amount")
    balance_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Amount still due after payments")
    
    # Receipt number (generated when first payment is made)
    receipt_number = models.CharField(max_length=20, unique=True, null=True, blank=True, editable=False, db_index=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def calculate_balance(self):
        """Calculate balance from payments"""
        total_paid = sum(p.amount_paid for p in self.service_visit.payments.all())
        self.balance_amount = max(Decimal('0'), self.net_amount - total_paid)
        return self.balance_amount
    
    def save(self, *args, **kwargs):
        """Auto-calculate net_amount and balance"""
        # Ensure net_amount = total_amount (for consistency)
        if not self.net_amount:
            self.net_amount = self.total_amount
        # Calculate balance if not explicitly set
        if self.balance_amount == 0 and self.service_visit_id:
            self.calculate_balance()
        super().save(*args, **kwargs)

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


class ReceiptSnapshot(models.Model):
    """Immutable snapshot of receipt data at time of issuance."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service_visit = models.OneToOneField(ServiceVisit, on_delete=models.CASCADE, related_name="receipt_snapshot")
    receipt_number = models.CharField(max_length=20, db_index=True)
    issued_at = models.DateTimeField()

    items_json = models.JSONField(default=list, help_text="[{name, qty, unit_price, line_total}]")
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default="cash")

    patient_name = models.CharField(max_length=200, blank=True, default="")
    patient_phone = models.CharField(max_length=30, blank=True, default="")
    patient_reg_no = models.CharField(max_length=30, blank=True, default="")
    patient_mrn = models.CharField(max_length=30, blank=True, default="")
    patient_age = models.CharField(max_length=20, blank=True, default="")
    patient_gender = models.CharField(max_length=20, blank=True, default="")
    cashier_name = models.CharField(max_length=150, blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-issued_at"]
        indexes = [
            models.Index(fields=["receipt_number"]),
            models.Index(fields=["issued_at"]),
        ]

    def __str__(self):
        return f"ReceiptSnapshot {self.receipt_number} ({self.service_visit.visit_id})"


class USGReport(models.Model):
    """USG report data - PHASE D: Canonical ultrasound reporting standard"""
    
    # Report Status Choices
    REPORT_STATUS_CHOICES = (
        ("DRAFT", "Draft"),
        ("FINAL", "Final"),
        ("AMENDED", "Amended"),
    )
    
    # Scan Quality Choices
    SCAN_QUALITY_CHOICES = (
        ("Good", "Good"),
        ("Fair", "Fair"),
        ("Limited", "Limited"),
    )
    
    # Study Type Choices
    STUDY_TYPE_CHOICES = (
        ("Abdomen", "Abdomen"),
        ("Pelvis", "Pelvis"),
        ("KUB", "KUB"),
        ("OB", "OB"),
        ("Doppler", "Doppler"),
        ("Other", "Other"),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Link to ServiceVisitItem for the USG service (preferred) or ServiceVisit (fallback for legacy)
    service_visit_item = models.OneToOneField("ServiceVisitItem", on_delete=models.CASCADE, related_name="usg_report", null=True, blank=True)
    service_visit = models.ForeignKey(ServiceVisit, on_delete=models.CASCADE, related_name="usg_reports", null=True, blank=True, help_text="Legacy field - use service_visit_item instead")
    
    # PHASE D: Canonical Template Fields
    # Header & Status
    report_status = models.CharField(max_length=20, choices=REPORT_STATUS_CHOICES, default="DRAFT", db_index=True, help_text="DRAFT | FINAL | AMENDED")
    study_title = models.CharField(max_length=200, blank=True, default="", help_text="Auto-generated from service/study type")
    
    # Patient & Order Details
    referring_clinician = models.CharField(max_length=200, blank=True, default="", help_text="Referring clinician name")
    clinical_history = models.TextField(blank=True, default="", help_text="Clinical history/indication (required before FINAL)")
    clinical_questions = models.TextField(blank=True, default="", help_text="Explicit clinical questions (multiline text)")
    
    # Exam Metadata
    exam_datetime = models.DateTimeField(null=True, blank=True, help_text="When exam was performed")
    report_datetime = models.DateTimeField(null=True, blank=True, help_text="When report was created/finalized")
    study_type = models.CharField(max_length=50, choices=STUDY_TYPE_CHOICES, blank=True, default="", help_text="Abdomen / Pelvis / KUB / OB / Doppler / Other")
    
    # Technique
    technique_approach = models.CharField(max_length=100, blank=True, default="", help_text="e.g., transabdominal, transvaginal")
    doppler_used = models.BooleanField(default=False, help_text="Doppler used in exam")
    contrast_used = models.BooleanField(default=False, help_text="Contrast used in exam")
    technique_notes = models.TextField(blank=True, default="", help_text="Additional technique notes")
    
    # Performed/Interpreted By
    performed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="performed_usg_reports", help_text="User who performed the exam")
    interpreted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="interpreted_usg_reports", help_text="User who interpreted the exam")
    comparison = models.TextField(blank=True, default="", help_text="Comparison with prior studies")
    
    # Scan Quality & Limitations (MANDATORY before FINAL)
    scan_quality = models.CharField(max_length=20, choices=SCAN_QUALITY_CHOICES, blank=True, default="", help_text="Good/Fair/Limited - REQUIRED before FINAL")
    limitations_text = models.TextField(blank=True, default="", help_text="Scan limitations - REQUIRED before FINAL (can be 'None' but must be explicit)")
    
    # Findings & Measurements
    findings_json = models.JSONField(default=dict, help_text="Structured per-organ modules with standardized keys")
    measurements_json = models.JSONField(default=list, help_text="Optional summary table derived from findings OR stored as structured list")
    
    # Impression (MANDATORY before FINAL)
    impression_text = models.TextField(blank=True, default="", help_text="Impression - REQUIRED before FINAL")
    
    # Suggestions/Follow-up (OPTIONAL)
    suggestions_text = models.TextField(blank=True, default="", help_text="Suggestions or follow-up recommendations")
    
    # Critical Result Communication (CONDITIONAL)
    critical_flag = models.BooleanField(default=False, help_text="Urgent/critical result flag")
    critical_communication_json = models.JSONField(default=dict, help_text="{ recipient, method, communicated_at, notes } - REQUIRED if critical_flag true")
    
    # Sign-off
    signoff_json = models.JSONField(default=dict, help_text="{ clinician_name, credentials, verified_at } set on FINAL/AMENDED")
    
    # Versioning & Amendment
    version = models.PositiveIntegerField(default=1, help_text="Increment on each FINAL/AMENDED publish; DRAFT saves do not increment")
    parent_report_id = models.UUIDField(null=True, blank=True, help_text="Link to parent report if this is an amendment")
    amendment_reason = models.TextField(blank=True, default="", help_text="Reason for amendment")
    amendment_history_json = models.JSONField(default=list, help_text="Immutable history of finalized versions")
    
    # Legacy fields (kept for backward compatibility)
    report_json = models.JSONField(default=dict, help_text="Legacy structured report data - use canonical fields instead")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="created_usg_reports")
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="updated_usg_reports")
    saved_at = models.DateTimeField(auto_now=True)
    published_pdf_path = models.CharField(max_length=500, blank=True, default="")
    verifier = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="verified_usg_reports")
    verified_at = models.DateTimeField(null=True, blank=True)
    return_reason = models.TextField(blank=True, default="")
    
    # PHASE C: Template bridge (preparation for dynamic templates)
    template_version = models.ForeignKey("templates.TemplateVersion", on_delete=models.SET_NULL, null=True, blank=True, help_text="Template version used for this report (bridge to template system)")

    class Meta:
        ordering = ["-saved_at"]
        indexes = [
            models.Index(fields=["report_status"]),
            models.Index(fields=["version"]),
        ]

    def __str__(self):
        visit_id = self.service_visit_item.service_visit.visit_id if self.service_visit_item else (self.service_visit.visit_id if self.service_visit else "Unknown")
        return f"USG Report for {visit_id} ({self.report_status} v{self.version})"
    
    def can_finalize(self):
        """Check if report can be finalized (all required fields present)"""
        errors = []
        if self.template_version and self.template_version.schema:
            schema = self.template_version.schema or {}
            sections = schema.get("sections", [])
            values = self.report_json if isinstance(self.report_json, dict) else {}

            def is_missing(field_type, value):
                if field_type == "checklist":
                    return not value or len(value) == 0
                if field_type == "number":
                    return value is None or value == ""
                if field_type == "boolean":
                    return value is None
                return value is None or (isinstance(value, str) and not value.strip())

            for section in sections:
                for field in section.get("fields", []):
                    if field.get("required"):
                        key = field.get("key")
                        field_type = field.get("type")
                        raw_value = values.get(key)
                        
                        # Handle structured value from frontend { value: ..., is_na: ... }
                        value = raw_value
                        is_na = False
                        if isinstance(raw_value, dict) and "is_na" in raw_value:
                            is_na = raw_value.get("is_na", False)
                            value = raw_value.get("value")
                            
                        # If explicitly marked NA, it passes validation
                        if is_na:
                            continue

                        if is_missing(field_type, value):
                            label = field.get("label") or key
                            errors.append(f"{label} is required")
        else:
            if not self.scan_quality:
                errors.append("scan_quality is required")
            if not self.limitations_text or not self.limitations_text.strip():
                errors.append("limitations_text is required (can be 'None' but must be explicit)")
            if not self.impression_text or not self.impression_text.strip():
                errors.append("impression_text is required")
            if self.critical_flag:
                comm = self.critical_communication_json or {}
                if not comm.get("recipient") or not comm.get("method") or not comm.get("communicated_at"):
                    errors.append("critical_communication_json must have recipient, method, and communicated_at when critical_flag is true")
        return len(errors) == 0, errors


class OPDVitals(models.Model):
    """OPD vitals data"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Link to ServiceVisitItem for the OPD service (preferred) or ServiceVisit (fallback for legacy)
    service_visit_item = models.OneToOneField("ServiceVisitItem", on_delete=models.CASCADE, related_name="opd_vitals", null=True, blank=True)
    service_visit = models.ForeignKey(ServiceVisit, on_delete=models.CASCADE, related_name="opd_vitals_list", null=True, blank=True, help_text="Legacy field - use service_visit_item instead")
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
        visit_id = self.service_visit_item.service_visit.visit_id if self.service_visit_item else (self.service_visit.visit_id if self.service_visit else "Unknown")
        return f"OPD Vitals for {visit_id}"


class OPDConsult(models.Model):
    """OPD consultation data"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Link to ServiceVisitItem for the OPD service (preferred) or ServiceVisit (fallback for legacy)
    service_visit_item = models.OneToOneField("ServiceVisitItem", on_delete=models.CASCADE, related_name="opd_consult", null=True, blank=True)
    service_visit = models.ForeignKey(ServiceVisit, on_delete=models.CASCADE, related_name="opd_consults", null=True, blank=True, help_text="Legacy field - use service_visit_item instead")
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
        visit_id = self.service_visit_item.service_visit.visit_id if self.service_visit_item else (self.service_visit.visit_id if self.service_visit else "Unknown")
        return f"OPD Consult for {visit_id}"


class StatusAuditLog(models.Model):
    """Audit log for status transitions
    
    PHASE C: Now tracks item-level transitions (service_visit_item is primary).
    service_visit is kept for backward compatibility and visit-level queries.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # PHASE C: Item-level tracking (primary)
    service_visit_item = models.ForeignKey("ServiceVisitItem", on_delete=models.CASCADE, related_name="status_audit_logs", null=True, blank=True, help_text="Item that transitioned (PHASE C: primary)")
    # Backward compatibility - kept for visit-level queries
    service_visit = models.ForeignKey(ServiceVisit, on_delete=models.CASCADE, related_name="status_audit_logs", null=True, blank=True, help_text="Visit containing the item (for backward compatibility)")
    from_status = models.CharField(max_length=30, choices=SERVICE_VISIT_STATUS)
    to_status = models.CharField(max_length=30, choices=SERVICE_VISIT_STATUS)
    reason = models.TextField(blank=True, default="", null=True, help_text="Required when RETURNED")
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
