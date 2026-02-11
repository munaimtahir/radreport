from django.contrib import admin

from .models import BackupJob


@admin.register(BackupJob)
class BackupJobAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "operation",
        "trigger",
        "status",
        "created_by",
        "created_at",
        "duration_sec",
        "uploaded",
    )
    list_filter = ("operation", "trigger", "status", "uploaded", "created_at")
    search_fields = ("id", "created_by", "backup_path", "error_message")
    readonly_fields = (
        "id",
        "created_at",
        "started_at",
        "finished_at",
        "duration_sec",
    )
