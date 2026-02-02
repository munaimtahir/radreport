import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone

class ReportProfile(models.Model):
    """
    Defines a reporting template/profile (e.g., USG KUB, CXR PA).
    Supports versioning and governance for safe template evolution.
    """
    STATUS_CHOICES = (
        ("draft", "Draft"),
        ("active", "Active"),
        ("archived", "Archived"),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, help_text="Unique code, e.g., USG_KUB")
    name = models.CharField(max_length=150, help_text="Human readable name")
    modality = models.CharField(max_length=20, help_text="Modality code, e.g., USG")
    enable_narrative = models.BooleanField(default=True)
    narrative_mode = models.CharField(max_length=50, default="rule_based", choices=[("rule_based", "Rule Based")])
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Governance fields
    version = models.PositiveIntegerField(default=1, help_text="Version number of this template")
    revision_of = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='revisions',
        help_text="Points to the original profile when cloned"
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default="active",
        help_text="Template status"
    )
    is_frozen = models.BooleanField(default=False, help_text="If true, template cannot be edited")
    activated_at = models.DateTimeField(null=True, blank=True, help_text="When this version was activated")
    activated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activated_profiles'
    )
    archived_at = models.DateTimeField(null=True, blank=True, help_text="When this version was archived")
    archived_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='archived_profiles'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['code', 'version'], name='unique_code_version')
        ]

    def __str__(self):
        return f"{self.code} v{self.version} - {self.name}"
    
    @property
    def used_by_reports_count(self):
        """Count of report instances using this profile."""
        return self.instances.count()
    
    def can_edit(self):
        """Check if this profile can be edited."""
        if self.is_frozen:
            return False, "Template is frozen"
        if self.status == "active" and self.used_by_reports_count > 0:
            return False, "Active template with existing reports cannot be edited"
        return True, None
    
    def can_delete(self):
        """Check if this profile can be deleted."""
        if self.status == "active":
            return False, "Active templates cannot be deleted"
        if self.used_by_reports_count > 0:
            return False, "Templates with existing reports cannot be deleted"
        return True, None

class ReportParameter(models.Model):
    """
    A single data point to capture in a report.
    """
    PARAMETER_TYPES = (
        ("number", "Number"),
        ("dropdown", "Dropdown"),
        ("checklist", "Checklist"),
        ("boolean", "Boolean"),
        ("short_text", "Short Text"),
        ("long_text", "Long Text"),
        ("heading", "Heading"),
        ("separator", "Separator"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(ReportProfile, on_delete=models.CASCADE, related_name="parameters")
    section = models.CharField(max_length=100, help_text="Section name, e.g., Kidneys")
    name = models.CharField(max_length=200, help_text="Parameter label, e.g., Right Kidney Size")
    slug = models.SlugField(max_length=200, help_text="Unique identifier within profile", null=True, blank=True)
    parameter_type = models.CharField(max_length=20, choices=PARAMETER_TYPES)
    unit = models.CharField(max_length=20, blank=True, null=True, help_text="Unit of measurement, e.g., mm")
    normal_value = models.CharField(max_length=500, blank=True, null=True, help_text="Default/Normal value")
    order = models.PositiveIntegerField(default=0)
    is_required = models.BooleanField(default=False)
    
    # Stage 2: Narrative Generation
    sentence_template = models.TextField(blank=True, null=True, help_text="Template like: {name}: {value}{unit}.")
    narrative_role = models.CharField(
        max_length=50,
        default="finding",
        choices=[
            ("finding", "Finding"),
            ("impression_hint", "Impression Hint"),
            ("limitation_hint", "Limitation Hint"),
            ("ignore", "Ignore"),
        ]
    )
    omit_if_values = models.JSONField(blank=True, null=True, help_text="List of values to omit sentence for, e.g. ['na', false]")
    join_label = models.CharField(max_length=50, blank=True, null=True, help_text="Join label for checklists, e.g. 'and'")

    class Meta:
        ordering = ["profile", "order"]
        unique_together = ("profile", "slug")

    def __str__(self):
        return f"{self.profile.code} - {self.name}"

class ReportParameterOption(models.Model):
    """
    Predefined options for dropdown/checklist parameters.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    parameter = models.ForeignKey(ReportParameter, on_delete=models.CASCADE, related_name="options")
    label = models.CharField(max_length=200)
    value = models.CharField(max_length=200)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["parameter", "order"]

    def __str__(self):
        return f"{self.label} ({self.parameter.name})"

class ServiceReportProfile(models.Model):
    """
    Mapping between Catalog Services and Report Profiles.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service = models.ForeignKey("catalog.Service", on_delete=models.CASCADE, related_name="report_profiles")
    profile = models.ForeignKey(ReportProfile, on_delete=models.CASCADE, related_name="service_links")
    enforce_single_profile = models.BooleanField(default=True, help_text="If user must use this profile")
    is_default = models.BooleanField(default=True, help_text="Auto-select this profile")

    class Meta:
        unique_together = ("service", "profile")

    def __str__(self):
        return f"{self.service.name} -> {self.profile.code}"

class ReportTemplateV2(models.Model):
    """
    JSON schema-based reporting template (V2).
    """
    STATUS_CHOICES = (
        ("draft", "Draft"),
        ("active", "Active"),
        ("archived", "Archived"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, help_text="Unique code, e.g., USG_KUB_V2")
    name = models.CharField(max_length=150, help_text="Human readable name")
    modality = models.CharField(max_length=20, help_text="Modality code, e.g., USG")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    json_schema = models.JSONField(default=dict)
    ui_schema = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.code} - {self.name}"

class ServiceReportTemplateV2(models.Model):
    """
    Mapping between Catalog Services and V2 report templates.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service = models.ForeignKey("catalog.Service", on_delete=models.CASCADE, related_name="report_templates_v2")
    template = models.ForeignKey(ReportTemplateV2, on_delete=models.CASCADE, related_name="service_links")
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("service", "template")

    def __str__(self):
        return f"{self.service.name} -> {self.template.code}"

class ReportInstance(models.Model):
    """
    An actual report entered for a specific visit item.
    """
    STATUS_CHOICES = (
        ("draft", "Draft"),
        ("submitted", "Submitted"),
        ("verified", "Verified"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service_visit_item = models.OneToOneField("workflow.ServiceVisitItem", on_delete=models.CASCADE, related_name="report_instance")
    profile = models.ForeignKey(ReportProfile, on_delete=models.PROTECT, related_name="instances")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="created_reports")
    
    # Stage 2: Narrative Output
    findings_text = models.TextField(blank=True, null=True)
    impression_text = models.TextField(blank=True, null=True)
    limitations_text = models.TextField(blank=True, null=True)
    narrative_version = models.CharField(max_length=20, default="v1")
    narrative_updated_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_published(self):
        return self.publish_snapshots.exists()

    def __str__(self):
        return f"Report {self.id} for {self.service_visit_item.service_visit.visit_id}"

class ReportInstanceV2(models.Model):
    """
    JSON schema-based report instance for a work item.
    """
    STATUS_CHOICES = (
        ("draft", "Draft"),
        ("submitted", "Submitted"),
        ("verified", "Verified"),
        ("returned", "Returned"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    work_item = models.OneToOneField(
        "workflow.ServiceVisitItem",
        on_delete=models.CASCADE,
        related_name="report_instance_v2"
    )
    template_v2 = models.ForeignKey(ReportTemplateV2, on_delete=models.PROTECT, related_name="instances")
    values_json = models.JSONField(default=dict)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_reports_v2"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Report V2 {self.id} for {self.work_item_id}"

class ReportingOrganizationConfig(models.Model):
    """
    Singleton configuration for branding and header/footer details.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    org_name = models.CharField(max_length=200, help_text="Organization Name")
    address = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    logo = models.ImageField(upload_to="org_config/", blank=True, null=True)
    disclaimer_text = models.TextField(blank=True, default="This report is electronically verified.")
    signatories_json = models.JSONField(default=list, blank=True, help_text="List of {name, designation}")
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Enforce singleton pattern: if another exists, prevent creation or delete others?
        # Typically for simple cases, we just rely on Admin to enforce single instance,
        # but here we can check on save.
        if not self.pk and ReportingOrganizationConfig.objects.exists():
            # If creating a new one but one already exists, we could either error or return existing.
            # Let's just allow it but business logic should enforce one.
            pass
        super().save(*args, **kwargs)

    def __str__(self):
        return self.org_name

class ReportParameterLibraryItem(models.Model):
    """
    Reusable parameter definition library.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    modality = models.CharField(max_length=20, help_text="e.g. USG, XR, CT")
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, help_text="Unique identifier, e.g. liver_size")
    parameter_type = models.CharField(max_length=20, choices=ReportParameter.PARAMETER_TYPES)
    unit = models.CharField(max_length=20, blank=True, null=True)
    default_normal_value = models.CharField(max_length=500, blank=True, null=True)
    default_sentence_template = models.TextField(blank=True, null=True)
    default_omit_if_values = models.JSONField(blank=True, null=True)
    default_options_json = models.JSONField(blank=True, null=True, help_text="List of {label, value} for dropdowns")
    default_join_label = models.CharField(max_length=50, blank=True, null=True)
    default_narrative_role = models.CharField(max_length=50, default="finding")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.slug} ({self.modality})"

class ReportProfileParameterLink(models.Model):
    """
    Link between a Profile and a Library Item, effectively instantiating it for that profile.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(ReportProfile, on_delete=models.CASCADE, related_name="library_links")
    library_item = models.ForeignKey(ReportParameterLibraryItem, on_delete=models.PROTECT)
    section = models.CharField(max_length=100)
    order = models.PositiveIntegerField(default=0)
    is_required = models.BooleanField(default=False)
    overrides_json = models.JSONField(blank=True, null=True, help_text="Override defaults like normal_value, template, etc.")

    class Meta:
        ordering = ["profile", "order"]
        unique_together = ("profile", "library_item")

    def __str__(self):
        return f"{self.profile.code} -> {self.library_item.slug}"

class ReportValue(models.Model):
    """
    The value entered for a specific parameter in a report.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report = models.ForeignKey(ReportInstance, on_delete=models.CASCADE, related_name="values")
    parameter = models.ForeignKey(ReportParameter, on_delete=models.PROTECT, null=True, blank=True)
    profile_link = models.ForeignKey(ReportProfileParameterLink, on_delete=models.PROTECT, null=True, blank=True)
    value = models.TextField(blank=True, null=True) # Storing as text, JSON parsing can happen in serializer/frontend
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # unique_together cannot be conditional easily, but application logic should enforce unique param per report
        # We drop the strict DB constraint or use a CheckConstraint in postgres (too complex for now?)
        # Let's keep the existing one but we can't if parameter is null.
        # So we remove unique_together and rely on app logic for now, or add partial indexes.
        # For safety/speed, let's remove unique_together.
        pass

    def __str__(self):
        name = self.parameter.name if self.parameter else (self.profile_link.library_item.name if self.profile_link else "Unknown")
        return f"{name}: {self.value}"

class ReportPublishSnapshot(models.Model):
    """
    Immutable snapshot of a published report version.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report = models.ForeignKey(ReportInstance, on_delete=models.CASCADE, related_name="publish_snapshots")
    version = models.PositiveIntegerField()
    published_at = models.DateTimeField(auto_now_add=True)
    published_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    
    # Snapshot content
    findings_text = models.TextField()
    impression_text = models.TextField(blank=True, default="")
    limitations_text = models.TextField(blank=True, default="")
    values_json = models.JSONField() # Store full parameter_id -> value map
    sha256 = models.CharField(max_length=64, help_text="SHA256 hash of canonical content")
    notes = models.TextField(blank=True, default="")
    
    # PDF Artifact
    pdf_file = models.FileField(upload_to="report_snapshots/%Y/%m/%d/")

    class Meta:
        ordering = ["-version"]
        unique_together = ("report", "version")

    def __str__(self):
        return f"Snapshot v{self.version} for {self.report}"

class ReportActionLog(models.Model):
    """
    Audit log for critical reporting actions.
    """
    ACTION_CHOICES = (
        ("submit", "Submit"),
        ("verify", "Verify"),
        ("return", "Return for Correction"),
        ("publish", "Publish"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report = models.ForeignKey(ReportInstance, on_delete=models.CASCADE, related_name="action_logs")
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    meta = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.action} on {self.report} by {self.actor}"


class TemplateAuditLog(models.Model):
    """
    Audit log for template governance actions.
    Tracks clone, activate, freeze, archive, import, and other governance operations.
    """
    ACTION_CHOICES = (
        ("clone", "Clone"),
        ("activate", "Activate"),
        ("freeze", "Freeze"),
        ("unfreeze", "Unfreeze"),
        ("archive", "Archive"),
        ("import", "Import"),
        ("apply_baseline", "Apply Baseline"),
        ("delete_blocked", "Delete Blocked"),
        ("edit", "Edit"),
        ("create", "Create"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='template_audit_logs'
    )
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    entity_type = models.CharField(max_length=50, help_text="e.g., report_profile, report_parameter, service_profile")
    entity_id = models.CharField(max_length=100, help_text="ID of the affected entity")
    timestamp = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict, blank=True, help_text="Additional context about the action")

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.action} on {self.entity_type}:{self.entity_id} by {self.actor}"
