import uuid
from django.conf import settings
from django.db import models


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
    narrative_rules = models.JSONField(default=dict, blank=True, help_text="Narrative generation rules")
    is_frozen = models.BooleanField(default=False, help_text="If true, template cannot be edited")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.code} - {self.name}"

    def can_edit(self):
        if self.is_frozen:
            return False, "Template is frozen"
        return True, None


class ReportActionLogV2(models.Model):
    """
    Audit log for critical reporting V2 actions.
    """
    ACTION_CHOICES = (
        ("save_draft", "Draft Saved"),
        ("submit", "Submit"),
        ("verify", "Verify"),
        ("return", "Return for Correction"),
        ("publish", "Publish"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report_v2 = models.ForeignKey("ReportInstanceV2", on_delete=models.CASCADE, related_name="action_logs")
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    meta = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.action} on {self.report_v2} by {self.actor}"


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
        related_name="report_instance_v2",
    )
    template_v2 = models.ForeignKey(ReportTemplateV2, on_delete=models.PROTECT, related_name="instances")
    values_json = models.JSONField(default=dict)
    narrative_json = models.JSONField(default=dict, blank=True, help_text="Current narrative content (including overrides)")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_reports_v2",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_published(self):
        return self.publish_snapshots_v2.exists()

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
        if not self.pk and ReportingOrganizationConfig.objects.exists():
            pass
        super().save(*args, **kwargs)

    def __str__(self):
        return self.org_name


class ReportPublishSnapshotV2(models.Model):
    """
    Immutable snapshot of a published V2 report version.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report_instance_v2 = models.ForeignKey(
        ReportInstanceV2,
        on_delete=models.CASCADE,
        related_name="publish_snapshots_v2",
    )
    template_v2 = models.ForeignKey(
        ReportTemplateV2,
        on_delete=models.PROTECT,
        related_name="snapshots",
    )
    values_json = models.JSONField(help_text="Immutable values at publish time")
    narrative_json = models.JSONField(help_text="Generated narrative at publish time")
    pdf_file = models.FileField(upload_to="report_snapshots_v2/%Y/%m/%d/")
    content_hash = models.CharField(
        max_length=64,
        help_text="SHA256 hash of template+values+narrative",
        db_index=True,
    )
    published_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    published_at = models.DateTimeField(auto_now_add=True)
    version = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["-version"]
        unique_together = ("report_instance_v2", "version")
        indexes = [
            models.Index(fields=["report_instance_v2", "published_at"]),
            models.Index(fields=["content_hash"]),
        ]

    def __str__(self):
        return f"Snapshot V2 v{self.version} for {self.report_instance_v2_id}"


class ReportBlockLibrary(models.Model):
    """
    Library of reusable reporting blocks (Phase 3C).
    Can be used for UI blocks or Narrative snippets.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150)
    category = models.CharField(max_length=100, blank=True, null=True)
    block_type = models.CharField(
        max_length=50,
        default="ui",
        choices=[
            ("ui", "UI Component"),
            ("narrative", "Narrative Snippet"),
        ],
    )
    content = models.JSONField(help_text="JSON schema/UI schema or narrative rule snippet")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
