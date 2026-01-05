from django.contrib import admin
from .models import Study

@admin.register(Study)
class StudyAdmin(admin.ModelAdmin):
    list_display = ("accession", "patient", "service", "status", "created_at")
    search_fields = ("accession", "patient__name", "patient__mrn", "service__name")
    list_filter = ("status", "service__modality")
