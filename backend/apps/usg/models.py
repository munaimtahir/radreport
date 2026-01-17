import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError

USG_STUDY_STATUS = (
    ("draft", "Draft"),
    ("verified", "Verified"),
    ("published", "Published"),
)


class UsgTemplate(models.Model):
    """Ultrasound report template with stable schema"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=100, unique=True, db_index=True)  # e.g., USG_ABDOMEN_BASE
    name = models.CharField(max_length=200)  # e.g., "USG Abdomen – Base"
    category = models.CharField(max_length=100, db_index=True)  # e.g., "abdomen"
    version = models.PositiveIntegerField(default=1)
    is_locked = models.BooleanField(default=True, help_text="Locked templates cannot be modified")
    schema_json = models.JSONField(help_text="Full template schema including sections/fields/options")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["category", "code", "version"]
        indexes = [
            models.Index(fields=["code", "version"]),
            models.Index(fields=["category"]),
        ]
        unique_together = [["code", "version"]]

    def __str__(self):
        return f"{self.code} v{self.version}"

    def clean(self):
        if self.is_locked and self.pk:
            # If trying to update a locked template, check what's being changed
            old = UsgTemplate.objects.get(pk=self.pk)
            if old.schema_json != self.schema_json:
                raise ValidationError("Cannot modify schema_json of a locked template")


class UsgServiceProfile(models.Model):
    """Maps a service to a base template with visibility rules"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service_code = models.CharField(max_length=50, unique=True, db_index=True)  # e.g., USG_ABDOMEN, USG_KUB
    template = models.ForeignKey(
        UsgTemplate, on_delete=models.PROTECT, related_name="service_profiles"
    )
    hidden_sections = models.JSONField(
        default=list, blank=True,
        help_text="Array of section keys to hide for this service"
    )
    forced_na_fields = models.JSONField(
        default=list, blank=True,
        help_text="Array of field keys that should be marked as NA by default"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["service_code"]
        indexes = [
            models.Index(fields=["service_code"]),
        ]

    def __str__(self):
        return f"{self.service_code} -> {self.template.code}"


class UsgStudy(models.Model):
    """One USG study instance per patient visit exam"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(
        "patients.Patient", on_delete=models.PROTECT, related_name="usg_studies"
    )
    visit = models.ForeignKey(
        "studies.Visit", on_delete=models.PROTECT, related_name="usg_studies",
        help_text="MUST link to patient registration/visit in RIMS"
    )
    service_code = models.CharField(max_length=50, db_index=True)  # e.g., USG_ABDOMEN
    template = models.ForeignKey(
        UsgTemplate, on_delete=models.PROTECT, related_name="studies"
    )
    status = models.CharField(
        max_length=20, choices=USG_STUDY_STATUS, default="draft", db_index=True
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="created_usg_studies"
    )
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="verified_usg_studies"
    )
    published_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="published_usg_studies"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    lock_reason = models.TextField(blank=True, null=True, help_text="Reason why study is locked")

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["patient"]),
            models.Index(fields=["visit"]),
            models.Index(fields=["status"]),
            models.Index(fields=["service_code"]),
        ]

    def __str__(self):
        return f"USG Study {self.service_code} - {self.patient.name} ({self.status})"

    def clean(self):
        """Enforce immutability for published studies"""
        if self.status == "published" and self.pk:
            old = UsgStudy.objects.get(pk=self.pk)
            # Block changes to core fields after publish
            if old.status != "published":
                return  # First time publishing is OK
            # If already published, check critical fields
            if (
                old.patient_id != self.patient_id or
                old.visit_id != self.visit_id or
                old.template_id != self.template_id or
                old.service_code != self.service_code
            ):
                raise ValidationError("Cannot modify core fields of a published study")

    def save(self, *args, **kwargs):
        self.clean()
        # Auto-set timestamps on status changes
        if self.status == "verified" and not self.verified_at:
            self.verified_at = timezone.now()
        if self.status == "published" and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    @property
    def is_locked(self):
        """Check if study is locked (published)"""
        return self.status == "published"


class UsgFieldValue(models.Model):
    """Stores structured field values for USG studies"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    study = models.ForeignKey(
        UsgStudy, on_delete=models.CASCADE, related_name="field_values"
    )
    field_key = models.CharField(max_length=200, db_index=True)
    value_json = models.JSONField(null=True, blank=True)  # Supports multi-select, numeric, text, etc.
    is_not_applicable = models.BooleanField(default=False, db_index=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["field_key"]
        indexes = [
            models.Index(fields=["study", "field_key"]),
            models.Index(fields=["is_not_applicable"]),
        ]
        unique_together = [["study", "field_key"]]

    def __str__(self):
        na_marker = " (NA)" if self.is_not_applicable else ""
        return f"{self.study_id}:{self.field_key}{na_marker}"

    def clean(self):
        """Enforce immutability for published studies"""
        if self.study.status == "published":
            raise ValidationError("Cannot modify field values of a published study")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class UsgPublishedSnapshot(models.Model):
    """Immutable snapshot of a published USG study"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    study = models.OneToOneField(
        UsgStudy, on_delete=models.PROTECT, related_name="published_snapshot"
    )
    template_code = models.CharField(max_length=100, db_index=True)
    template_version = models.PositiveIntegerField()
    renderer_version = models.CharField(
        max_length=50, default="usg_renderer_v1",
        help_text="Version of renderer used to generate narrative"
    )
    published_json_snapshot = models.JSONField(
        help_text="Frozen copy of all field_key → {value, is_na}"
    )
    published_text_snapshot = models.TextField(
        help_text="Final narrative text as issued"
    )
    pdf_drive_file_id = models.CharField(
        max_length=255, blank=True, null=True,
        help_text="Google Drive file ID for the PDF"
    )
    pdf_drive_folder_id = models.CharField(
        max_length=255, blank=True, null=True,
        help_text="Google Drive folder ID where PDF is stored"
    )
    pdf_sha256 = models.CharField(
        max_length=64, blank=True, null=True,
        help_text="SHA256 hash of PDF bytes for integrity"
    )
    published_at = models.DateTimeField(auto_now_add=True)
    published_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    audit_note = models.TextField(
        blank=True, null=True,
        help_text="Audit trail notes (e.g., PDF regeneration)"
    )

    class Meta:
        ordering = ["-published_at"]
        indexes = [
            models.Index(fields=["study"]),
            models.Index(fields=["template_code"]),
            models.Index(fields=["pdf_drive_file_id"]),
        ]

    def __str__(self):
        return f"Published Snapshot: {self.study_id} ({self.template_code} v{self.template_version})"
