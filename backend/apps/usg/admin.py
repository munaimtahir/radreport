from django.contrib import admin
from .models import (
    UsgTemplate, UsgServiceProfile, UsgStudy,
    UsgFieldValue, UsgPublishedSnapshot
)


@admin.register(UsgTemplate)
class UsgTemplateAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "category", "version", "is_locked", "created_at")
    search_fields = ("code", "name", "category")
    list_filter = ("category", "is_locked", "version", "created_at")
    readonly_fields = ("id", "created_at", "updated_at")

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of locked templates"""
        if obj and obj.is_locked:
            return False
        return super().has_delete_permission(request, obj)

    def has_change_permission(self, request, obj=None):
        """Prevent modification of locked templates"""
        if obj and obj.is_locked:
            return False
        return super().has_change_permission(request, obj)


@admin.register(UsgServiceProfile)
class UsgServiceProfileAdmin(admin.ModelAdmin):
    list_display = ("service_code", "template", "created_at", "updated_at")
    search_fields = ("service_code", "template__code", "template__name")
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(UsgStudy)
class UsgStudyAdmin(admin.ModelAdmin):
    list_display = (
        "id", "patient", "visit", "service_code", "status",
        "created_at", "published_at"
    )
    search_fields = (
        "patient__name", "patient__mrn", "visit__visit_number",
        "service_code"
    )
    list_filter = ("status", "service_code", "created_at", "published_at")
    readonly_fields = (
        "id", "created_at", "verified_at", "published_at",
        "created_by", "verified_by", "published_by"
    )

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of published studies"""
        if obj and obj.status == "published":
            return False
        return super().has_delete_permission(request, obj)

    def has_change_permission(self, request, obj=None):
        """Prevent modification of published studies"""
        if obj and obj.status == "published":
            return False
        return super().has_change_permission(request, obj)


@admin.register(UsgFieldValue)
class UsgFieldValueAdmin(admin.ModelAdmin):
    list_display = ("study", "field_key", "is_not_applicable", "updated_at")
    search_fields = ("study__patient__name", "field_key")
    list_filter = ("is_not_applicable", "field_key", "updated_at")
    readonly_fields = ("id", "updated_at", "updated_by")

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion if study is published"""
        if obj and obj.study.status == "published":
            return False
        return super().has_delete_permission(request, obj)

    def has_change_permission(self, request, obj=None):
        """Prevent modification if study is published"""
        if obj and obj.study.status == "published":
            return False
        return super().has_change_permission(request, obj)


@admin.register(UsgPublishedSnapshot)
class UsgPublishedSnapshotAdmin(admin.ModelAdmin):
    list_display = (
        "study", "template_code", "template_version", "renderer_version",
        "pdf_drive_file_id", "published_at", "published_by"
    )
    search_fields = (
        "study__patient__name", "study__patient__mrn",
        "template_code", "pdf_drive_file_id"
    )
    list_filter = ("template_code", "template_version", "renderer_version", "published_at")
    readonly_fields = (
        "id", "study", "template_code", "template_version",
        "renderer_version", "published_json_snapshot",
        "published_text_snapshot", "pdf_drive_file_id",
        "pdf_drive_folder_id", "pdf_sha256", "published_at",
        "published_by", "audit_note"
    )

    def has_delete_permission(self, request, obj=None):
        """Never allow deletion of published snapshots"""
        return False

    def has_add_permission(self, request):
        """Snapshots are created via publish endpoint, not admin"""
        return False

    def has_change_permission(self, request, obj=None):
        """Only allow audit_note updates"""
        return False
