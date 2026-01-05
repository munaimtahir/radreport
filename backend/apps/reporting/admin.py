from django.contrib import admin
from .models import Report

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("study", "status", "created_at", "finalized_at")
    search_fields = ("study__accession", "study__patient__name")
    list_filter = ("status",)
