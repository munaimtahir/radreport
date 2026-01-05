import uuid
from django.db import models
from django.conf import settings

REPORT_STATUS = (
    ("draft", "Draft"),
    ("final", "Final"),
)

class Report(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    study = models.OneToOneField("studies.Study", on_delete=models.CASCADE, related_name="report")
    template_version = models.ForeignKey("templates.TemplateVersion", on_delete=models.PROTECT)
    status = models.CharField(max_length=20, choices=REPORT_STATUS, default="draft")
    values = models.JSONField(default=dict)  # keyed by TemplateField.key
    narrative = models.TextField(blank=True, default="")
    impression = models.TextField(blank=True, default="")
    finalized_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="finalized_reports")
    finalized_at = models.DateTimeField(null=True, blank=True)
    pdf_file = models.FileField(upload_to="reports/", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Report {self.study.accession} ({self.status})"
