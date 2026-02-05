from django.contrib import admin
from .models import (
    ReportTemplateV2,
    ServiceReportTemplateV2,
    ReportInstanceV2,
    ReportPublishSnapshotV2,
    ReportActionLogV2,
    ReportingOrganizationConfig,
    ReportBlockLibrary,
)


@admin.register(ReportTemplateV2)
class ReportTemplateV2Admin(admin.ModelAdmin):
    list_display = ("code", "name", "modality", "status", "is_frozen", "updated_at")
    list_filter = ("status", "modality", "is_frozen")
    search_fields = ("code", "name")


@admin.register(ServiceReportTemplateV2)
class ServiceReportTemplateV2Admin(admin.ModelAdmin):
    list_display = ("service", "template", "is_active", "is_default", "created_at")
    list_filter = ("is_active", "is_default")
    search_fields = ("service__name", "service__code", "template__code")


@admin.register(ReportInstanceV2)
class ReportInstanceV2Admin(admin.ModelAdmin):
    list_display = ("work_item", "template_v2", "status", "created_at")
    list_filter = ("status",)


@admin.register(ReportPublishSnapshotV2)
class ReportPublishSnapshotV2Admin(admin.ModelAdmin):
    list_display = ("report_instance_v2", "version", "published_at", "content_hash")
    list_filter = ("published_at",)


@admin.register(ReportActionLogV2)
class ReportActionLogV2Admin(admin.ModelAdmin):
    list_display = ("report_v2", "action", "actor", "created_at")
    list_filter = ("action",)


@admin.register(ReportingOrganizationConfig)
class ReportingOrganizationConfigAdmin(admin.ModelAdmin):
    list_display = ("org_name", "updated_at")


@admin.register(ReportBlockLibrary)
class ReportBlockLibraryAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "block_type", "updated_at")
    list_filter = ("block_type", "category")
