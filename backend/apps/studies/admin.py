from django.contrib import admin
from apps.admin_utils import HiddenFromAdminIndexModelAdmin
from .models import Study, Visit, OrderItem

@admin.register(Visit)
class VisitAdmin(HiddenFromAdminIndexModelAdmin):
    list_display = ("visit_number", "receipt_number", "patient", "net_total", "paid_amount", "due_amount", "is_finalized", "created_at")
    search_fields = ("visit_number", "receipt_number", "patient__name", "patient__mrn")
    list_filter = ("is_finalized", "payment_method", "created_at")
    readonly_fields = ("visit_number", "receipt_number", "receipt_pdf_path", "receipt_generated_at", "created_at", "finalized_at")

@admin.register(OrderItem)
class OrderItemAdmin(HiddenFromAdminIndexModelAdmin):
    list_display = ("visit", "service", "charge", "created_at")
    search_fields = ("visit__visit_number", "service__name")
    list_filter = ("service__modality", "created_at")

@admin.register(Study)
class StudyAdmin(HiddenFromAdminIndexModelAdmin):
    list_display = ("accession", "patient", "service", "status", "visit", "created_at")
    search_fields = ("accession", "patient__name", "patient__mrn", "service__name")
    list_filter = ("status", "service__modality")
