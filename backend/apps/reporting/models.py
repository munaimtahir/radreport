import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone

class ReportProfile(models.Model):
    """
    Defines a reporting template/profile (e.g., USG KUB, CXR PA).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True, help_text="Unique code, e.g., USG_KUB")
    name = models.CharField(max_length=150, help_text="Human readable name")
    modality = models.CharField(max_length=20, help_text="Modality code, e.g., USG")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.code} - {self.name}"

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
    parameter_type = models.CharField(max_length=20, choices=PARAMETER_TYPES)
    unit = models.CharField(max_length=20, blank=True, null=True, help_text="Unit of measurement, e.g., mm")
    normal_value = models.CharField(max_length=500, blank=True, null=True, help_text="Default/Normal value")
    order = models.PositiveIntegerField(default=0)
    is_required = models.BooleanField(default=False)

    class Meta:
        ordering = ["profile", "order"]

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

    class Meta:
        unique_together = ("service", "profile")

    def __str__(self):
        return f"{self.service.name} -> {self.profile.code}"

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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Report {self.id} for {self.service_visit_item.service_visit.visit_id}"

class ReportValue(models.Model):
    """
    The value entered for a specific parameter in a report.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report = models.ForeignKey(ReportInstance, on_delete=models.CASCADE, related_name="values")
    parameter = models.ForeignKey(ReportParameter, on_delete=models.PROTECT)
    value = models.TextField(blank=True, null=True) # Storing as text, JSON parsing can happen in serializer/frontend
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("report", "parameter")

    def __str__(self):
        return f"{self.parameter.name}: {self.value}"
