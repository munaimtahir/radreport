from django.contrib import admin
from .models import Modality, Service

@admin.register(Modality)
class ModalityAdmin(admin.ModelAdmin):
    list_display = ("code", "name")
    search_fields = ("code", "name")

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "modality", "category", "charges", "tat_value", "tat_unit", "is_active")
    search_fields = ("name", "code")
    list_filter = ("modality", "category", "is_active")
