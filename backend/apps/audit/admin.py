from django.contrib import admin
from .models import AuditLog

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "action", "entity_type", "entity_id", "actor")
    search_fields = ("action", "entity_type", "entity_id")
    list_filter = ("entity_type", "action", "created_at")
