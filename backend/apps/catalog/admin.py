from django.contrib import admin
from .models import Modality, Service

@admin.register(Modality)
class ModalityAdmin(admin.ModelAdmin):
    list_display = ("code", "name")
    search_fields = ("code", "name")

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("name", "modality", "price", "tat_minutes", "is_active")
    search_fields = ("name",)
    list_filter = ("modality", "is_active")
