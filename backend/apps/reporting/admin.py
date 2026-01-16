from django.contrib import admin
from .models import Report, ReportTemplateReport

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("study", "status", "created_at", "finalized_at")
    search_fields = ("study__accession", "study__patient__name")
    list_filter = ("status",)


@admin.register(ReportTemplateReport)
class ReportTemplateReportAdmin(admin.ModelAdmin):
    list_display = ("service_visit_item", "template", "status", "updated_at")
    list_filter = ("status",)
