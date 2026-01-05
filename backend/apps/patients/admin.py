from django.contrib import admin
from .models import Patient

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ("mrn", "name", "phone", "age", "gender", "created_at")
    search_fields = ("mrn", "name", "phone")
