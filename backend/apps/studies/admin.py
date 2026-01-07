from django.contrib import admin
from .models import Study, Visit, OrderItem, ReceiptSettings, ReceiptSequence

@admin.register(Visit)
class VisitAdmin(admin.ModelAdmin):
    list_display = ("visit_number", "receipt_number", "patient", "net_total", "paid_amount", "due_amount", "is_finalized", "created_at")
    search_fields = ("visit_number", "receipt_number", "patient__name", "patient__mrn")
    list_filter = ("is_finalized", "payment_method", "created_at")
    readonly_fields = ("visit_number", "receipt_number", "receipt_pdf_path", "receipt_generated_at", "created_at", "finalized_at")

@admin.register(ReceiptSettings)
class ReceiptSettingsAdmin(admin.ModelAdmin):
    list_display = ("header_text", "has_logo", "has_header_image", "updated_at", "updated_by")
    readonly_fields = ("updated_at", "updated_by")
    
    def has_logo(self, obj):
        return bool(obj.logo_image)
    has_logo.boolean = True
    has_logo.short_description = "Has Logo"
    
    def has_header_image(self, obj):
        return bool(obj.header_image)
    has_header_image.boolean = True
    has_header_image.short_description = "Has Header Image"
    
    def save_model(self, request, obj, form, change):
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(ReceiptSequence)
class ReceiptSequenceAdmin(admin.ModelAdmin):
    list_display = ("yymm", "last_number", "updated_at")
    readonly_fields = ("yymm", "last_number", "updated_at")
    list_filter = ("yymm",)

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("visit", "service", "charge", "created_at")
    search_fields = ("visit__visit_number", "service__name")
    list_filter = ("service__modality", "created_at")

@admin.register(Study)
class StudyAdmin(admin.ModelAdmin):
    list_display = ("accession", "patient", "service", "status", "visit", "created_at")
    search_fields = ("accession", "patient__name", "patient__mrn", "service__name")
    list_filter = ("status", "service__modality")
