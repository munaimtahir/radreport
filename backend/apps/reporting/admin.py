from django.contrib import admin
from apps.admin_utils import HiddenFromAdminIndexModelAdmin
from .models import (
    ReportProfile, ReportParameter, ReportParameterOption, 
    ServiceReportProfile, ReportInstance, ReportValue,
    ReportActionLog, ReportPublishSnapshot,
    ReportingOrganizationConfig, ReportParameterLibraryItem, ReportProfileParameterLink
)

class ReportParameterOptionInline(admin.TabularInline):
    model = ReportParameterOption
    extra = 1

@admin.register(ReportParameter)
class ReportParameterAdmin(HiddenFromAdminIndexModelAdmin):
    list_display = ("profile", "section", "name", "parameter_type", "order")
    list_filter = ("profile", "parameter_type")
    inlines = [ReportParameterOptionInline]
    ordering = ("profile", "order")

class ReportParameterInline(admin.TabularInline):
    model = ReportParameter
    extra = 0
    fields = ("section", "name", "parameter_type", "order")
    readonly_fields = ("section", "name", "parameter_type", "order")
    show_change_link = True

class ReportProfileParameterLinkInline(admin.TabularInline):
    model = ReportProfileParameterLink
    extra = 1
    autocomplete_fields = ["library_item"]

@admin.register(ReportProfile)
class ReportProfileAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "modality", "is_active")
    search_fields = ("code", "name")
    inlines = [ReportParameterInline, ReportProfileParameterLinkInline]

@admin.register(ServiceReportProfile)
class ServiceReportProfileAdmin(admin.ModelAdmin):
    list_display = ("service", "profile", "is_default", "enforce_single_profile")
    list_editable = ("is_default",)
    search_fields = ("service__name", "profile__code")

class ReportValueInline(admin.TabularInline):
    model = ReportValue
    extra = 0
    readonly_fields = ("parameter", "value")
    # making it read-only mostly unless we want admin to edit raw values
    
@admin.register(ReportInstance)
class ReportInstanceAdmin(admin.ModelAdmin):
    list_display = ("id", "service_visit_item", "profile", "status", "created_at")
    list_filter = ("status", "profile")
    inlines = [ReportValueInline]

@admin.register(ReportActionLog)
class ReportActionLogAdmin(HiddenFromAdminIndexModelAdmin):
    list_display = ("report", "action", "actor", "created_at")
    list_filter = ("action", "actor", "created_at")
    search_fields = ("report__id", "actor__username")

@admin.register(ReportPublishSnapshot)
class ReportPublishSnapshotAdmin(HiddenFromAdminIndexModelAdmin):
    list_display = ("report", "version", "published_at", "published_by", "sha256")
    list_filter = ("published_at", "published_by", "version")
    search_fields = ("report__id", "sha256", "published_by__username")
    readonly_fields = ("sha256", "values_json", "findings_text", "impression_text", "limitations_text")

@admin.register(ReportingOrganizationConfig)
class ReportingOrganizationConfigAdmin(admin.ModelAdmin):
    list_display = ("org_name", "updated_at")
    
    def has_add_permission(self, request):
        # Enforce singleton in admin UI
        if self.model.objects.exists():
            return False
        return True

@admin.register(ReportParameterLibraryItem)
class ReportParameterLibraryItemAdmin(HiddenFromAdminIndexModelAdmin):
    list_display = ("slug", "name", "modality", "parameter_type")
    search_fields = ("slug", "name")
    list_filter = ("modality", "parameter_type")

