from django.contrib import admin
from .models import (
    ReportProfile, ReportParameter, ReportParameterOption, 
    ServiceReportProfile, ReportInstance, ReportValue
)

class ReportParameterOptionInline(admin.TabularInline):
    model = ReportParameterOption
    extra = 1

@admin.register(ReportParameter)
class ReportParameterAdmin(admin.ModelAdmin):
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

@admin.register(ReportProfile)
class ReportProfileAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "modality", "is_active")
    search_fields = ("code", "name")
    inlines = [ReportParameterInline]

@admin.register(ServiceReportProfile)
class ServiceReportProfileAdmin(admin.ModelAdmin):
    list_display = ("service", "profile", "enforce_single_profile")
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
