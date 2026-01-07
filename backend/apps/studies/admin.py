from django.contrib import admin
from .models import Study, Visit, OrderItem

@admin.register(Visit)
class VisitAdmin(admin.ModelAdmin):
    list_display = ("visit_number", "patient", "net_total", "paid_amount", "due_amount", "is_finalized", "created_at")
    search_fields = ("visit_number", "patient__name", "patient__mrn")
    list_filter = ("is_finalized", "payment_method", "created_at")
    readonly_fields = ("visit_number", "created_at", "finalized_at")

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
