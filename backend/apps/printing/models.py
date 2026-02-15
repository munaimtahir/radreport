"""
Printing configuration: receipt branding (singleton).
Report org config (logo, disclaimer, signatories) lives in apps.reporting.ReportingOrganizationConfig.
"""
import uuid
from django.db import models


class ReceiptBrandingConfig(models.Model):
    """Singleton receipt branding settings."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    receipt_header_text = models.TextField(default="Consultant Place Clinic")
    receipt_footer_text = models.TextField(blank=True, default="")
    receipt_logo = models.ImageField(upload_to="printing/receipt/", blank=True, null=True)
    receipt_banner = models.ImageField(upload_to="printing/receipt/", blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Receipt Branding"
        verbose_name_plural = "Receipt Branding"

    @classmethod
    def get_singleton(cls):
        """Get or create the singleton instance."""
        obj = cls.objects.first()
        if obj is None:
            obj = cls.objects.create()
        return obj

    def __str__(self):
        return "Receipt Branding Settings"
