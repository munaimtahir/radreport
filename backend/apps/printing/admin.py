from django.contrib import admin
from .models import ReceiptBrandingConfig


@admin.register(ReceiptBrandingConfig)
class ReceiptBrandingConfigAdmin(admin.ModelAdmin):
    list_display = ("id", "receipt_header_text", "updated_at")
    readonly_fields = ("id", "updated_at")
