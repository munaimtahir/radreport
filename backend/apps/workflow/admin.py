from django.contrib import admin
from .models import (
    ServiceCatalog, ServiceVisit, ServiceVisitItem, Invoice, Payment,
    USGReport, OPDVitals, OPDConsult, StatusAuditLog
)


@admin.register(ServiceCatalog)
class ServiceCatalogAdmin(admin.ModelAdmin):
    """
    DEPRECATED: Use catalog.Service instead.
    This model is kept for migration compatibility only.
    """
    list_display = ["code", "name", "default_price", "turnaround_time", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["code", "name"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(ServiceVisitItem)
class ServiceVisitItemAdmin(admin.ModelAdmin):
    list_display = ["service_visit", "service", "service_name_snapshot", "price_snapshot", "status", "created_at"]
    list_filter = ["status", "department_snapshot", "created_at"]
    search_fields = ["service_visit__visit_id", "service__name", "service_name_snapshot"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(ServiceVisit)
class ServiceVisitAdmin(admin.ModelAdmin):
    list_display = ["visit_id", "patient", "status", "registered_at", "created_by"]
    list_filter = ["status", "registered_at"]
    search_fields = ["visit_id", "patient__name", "patient__patient_reg_no", "patient__mrn"]
    readonly_fields = ["visit_id", "registered_at", "updated_at"]
    filter_horizontal = []  # Remove service filter since it's now via items


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ["service_visit", "subtotal", "discount", "total_amount", "net_amount", "balance_amount", "receipt_number"]
    list_filter = ["created_at"]
    search_fields = ["service_visit__visit_id", "receipt_number"]
    readonly_fields = ["receipt_number", "created_at", "updated_at"]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ["service_visit", "amount_paid", "method", "received_by", "received_at"]
    list_filter = ["method", "received_at"]
    search_fields = ["service_visit__visit_id"]


@admin.register(USGReport)
class USGReportAdmin(admin.ModelAdmin):
    list_display = ["service_visit", "created_by", "verifier", "verified_at", "published_pdf_path"]
    search_fields = ["service_visit__visit_id"]


@admin.register(OPDVitals)
class OPDVitalsAdmin(admin.ModelAdmin):
    list_display = ["service_visit", "bp_systolic", "bp_diastolic", "pulse", "entered_by", "entered_at"]
    search_fields = ["service_visit__visit_id"]


@admin.register(OPDConsult)
class OPDConsultAdmin(admin.ModelAdmin):
    list_display = ["service_visit", "consultant", "consult_at", "published_pdf_path"]
    search_fields = ["service_visit__visit_id", "diagnosis"]


@admin.register(StatusAuditLog)
class StatusAuditLogAdmin(admin.ModelAdmin):
    list_display = ["service_visit", "from_status", "to_status", "changed_by", "changed_at"]
    list_filter = ["from_status", "to_status", "changed_at"]
    search_fields = ["service_visit__visit_id"]
    readonly_fields = ["changed_at"]
