from django.contrib import admin
from .models import (
    ServiceCatalog, ServiceVisit, Invoice, Payment,
    USGReport, OPDVitals, OPDConsult, StatusAuditLog
)


@admin.register(ServiceCatalog)
class ServiceCatalogAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "default_price", "turnaround_time", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["code", "name"]


@admin.register(ServiceVisit)
class ServiceVisitAdmin(admin.ModelAdmin):
    list_display = ["visit_id", "patient", "service", "status", "registered_at", "created_by"]
    list_filter = ["status", "service", "registered_at"]
    search_fields = ["visit_id", "patient__name", "patient__patient_reg_no", "patient__mrn"]
    readonly_fields = ["visit_id", "registered_at", "updated_at"]


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ["service_visit", "total_amount", "net_amount", "balance_amount"]
    search_fields = ["service_visit__visit_id"]


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
