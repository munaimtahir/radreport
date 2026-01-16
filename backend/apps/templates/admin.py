from django.contrib import admin
from .models import (
    Template, TemplateVersion, TemplateSection, TemplateField, FieldOption,
    ReportTemplate, ReportTemplateField, ReportTemplateFieldOption, ServiceReportTemplate,
)

class FieldOptionInline(admin.TabularInline):
    model = FieldOption
    extra = 0

class TemplateFieldInline(admin.TabularInline):
    model = TemplateField
    extra = 0

class TemplateSectionInline(admin.TabularInline):
    model = TemplateSection
    extra = 0

@admin.register(Template)
class TemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "modality_code", "is_active", "created_at")
    search_fields = ("name", "modality_code")

@admin.register(TemplateSection)
class TemplateSectionAdmin(admin.ModelAdmin):
    list_display = ("template", "title", "order")
    list_filter = ("template",)
    inlines = [TemplateFieldInline]

@admin.register(TemplateField)
class TemplateFieldAdmin(admin.ModelAdmin):
    list_display = ("section", "label", "key", "field_type", "required", "order")
    list_filter = ("field_type", "required")
    search_fields = ("label", "key")
    inlines = [FieldOptionInline]

@admin.register(TemplateVersion)
class TemplateVersionAdmin(admin.ModelAdmin):
    list_display = ("template", "version", "is_published", "created_at")
    list_filter = ("template", "is_published")


class ReportTemplateFieldOptionInline(admin.TabularInline):
    model = ReportTemplateFieldOption
    extra = 0


class ReportTemplateFieldInline(admin.TabularInline):
    model = ReportTemplateField
    extra = 0


@admin.register(ReportTemplate)
class ReportTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "category", "version", "is_active", "created_at")
    search_fields = ("name", "code", "category")
    inlines = [ReportTemplateFieldInline]


@admin.register(ReportTemplateField)
class ReportTemplateFieldAdmin(admin.ModelAdmin):
    list_display = ("template", "label", "key", "field_type", "is_required", "order", "is_active")
    list_filter = ("field_type", "is_required", "is_active")
    search_fields = ("label", "key")
    inlines = [ReportTemplateFieldOptionInline]


@admin.register(ServiceReportTemplate)
class ServiceReportTemplateAdmin(admin.ModelAdmin):
    list_display = ("service", "template", "is_default", "is_active", "created_at")
    list_filter = ("is_default", "is_active")
