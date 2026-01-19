import json
import logging
import jsonschema
from django.conf import settings
from django.db import transaction
from django.core.exceptions import ValidationError
from apps.templates.models import (
    Template, TemplateVersion, TemplateSection, TemplateField, FieldOption,
    ReportTemplate, ReportTemplateField, ReportTemplateFieldOption, ServiceReportTemplate
)
from apps.catalog.models import Service
from pathlib import Path

logger = logging.getLogger(__name__)

SCHEMA_PATH = Path(settings.BASE_DIR) / "apps" / "templates" / "schema" / "template_package_v1.json"

TYPE_MAPPING = {
    "short_text": "short_text",
    "long_text": "long_text",
    "number": "number",
    "boolean": "radio",
    "dropdown": "dropdown",
    "checklist": "checkbox",
    "heading": "heading",
    "separator": "separator",
}

class TemplatePackageEngine:
    """
    Handles import, export, and validation of TemplatePackage v1.
    """

    @staticmethod
    def get_schema():
        if not SCHEMA_PATH.exists():
            raise FileNotFoundError(f"Schema not found at {SCHEMA_PATH}")
        with open(SCHEMA_PATH, "r") as f:
            return json.load(f)

    @classmethod
    def validate(cls, data):
        """
        Validates the JSON data against the TemplatePackage v1 schema.
        Returns: (is_valid, errors, report)
        """
        schema = cls.get_schema()
        validator = jsonschema.Draft7Validator(schema)
        errors = sorted(validator.iter_errors(data), key=lambda e: e.path)
        
        error_messages = []
        for error in errors:
            path = " -> ".join([str(p) for p in error.path])
            error_messages.append(f"{path}: {error.message}")

        return len(errors) == 0, error_messages, data

    @classmethod
    @transaction.atomic
    def import_package(cls, data, mode="create", user=None):
        """
        Imports a template package.
        mode: 'create' | 'update'
        """
        is_valid, errors, _ = cls.validate(data)
        if not is_valid:
            raise ValidationError(f"Invalid template package: {errors}")

        code = data.get("code")
        
        # 1. Handle legacy Template model
        existing_template = Template.objects.filter(code=code).first()
        if mode == "create" and existing_template:
            raise ValidationError(f"Template with code '{code}' already exists in legacy system.")
        
        if mode == "create":
            template = Template.objects.create(
                code=code,
                name=data["name"],
                modality_code=data.get("category", ""),
                is_active=True
            )
        else: # update
            if not existing_template:
                raise ValidationError(f"Template with code '{code}' does not exist in legacy system.")
            template = existing_template
            template.name = data["name"]
            template.modality_code = data.get("category", template.modality_code)
            template.save()

        # 2. Handle modern ReportTemplate model (UI visibility)
        existing_report_template = ReportTemplate.objects.filter(code=code).first()
        if mode == "create" and existing_report_template:
            # Code might match but name might differ? We enforce code uniqueness.
            raise ValidationError(f"Report Template with code '{code}' already exists.")
            
        if mode == "create":
            report_template = ReportTemplate.objects.create(
                code=code,
                name=data["name"],
                category=data.get("category", ""),
                is_active=True,
                created_by=user,
                updated_by=user
            )
        else: # update
            if not existing_report_template:
                 # If it exists in legacy but not in new, we create it
                 report_template = ReportTemplate.objects.create(
                    code=code,
                    name=data["name"],
                    category=data.get("category", ""),
                    is_active=True,
                    created_by=user,
                    updated_by=user
                )
            else:
                report_template = existing_report_template
                report_template.name = data["name"]
                report_template.category = data.get("category", report_template.category)
                report_template.updated_by = user
                report_template.version += 1
                report_template.save()

        # Create new version (legacy tracking)
        new_version_num = 1
        last_version = template.versions.order_by("-version").first()
        if last_version:
            new_version_num = last_version.version + 1

        version = TemplateVersion.objects.create(
            template=template,
            version=new_version_num,
            schema=data, 
            is_published=True
        )

        # Sync relational models for legacy Template
        cls._sync_relational_models_legacy(template, data)
        
        # Sync relational models for modern ReportTemplate
        cls._sync_relational_models_report(report_template, data)

        # 3. Handle service mappings
        service_codes = data.get("service_mappings", [])
        if service_codes:
            for s_code in service_codes:
                service = Service.objects.filter(code=s_code).first()
                if service:
                    ServiceReportTemplate.objects.update_or_create(
                        service=service,
                        template=report_template,
                        defaults={"is_active": True}
                    )

        return report_template, version

    @classmethod
    def _sync_relational_models_legacy(cls, template, data):
        # Clear existing structure
        template.sections.all().delete()

        for s_idx, section_data in enumerate(data.get("sections", [])):
            section = TemplateSection.objects.create(
                template=template,
                title=section_data["title"],
                order=s_idx
            )
            
            for f_idx, field_data in enumerate(section_data.get("fields", [])):
                field = TemplateField.objects.create(
                    section=section,
                    label=field_data["label"],
                    key=field_data["key"],
                    field_type=field_data["type"],
                    required=field_data.get("required", False),
                    help_text=field_data.get("help_text", ""),
                    placeholder=field_data.get("placeholder", ""),
                    unit=field_data.get("unit", ""),
                    order=f_idx
                )
                
                # Options
                if "options" in field_data:
                    for o_idx, opt in enumerate(field_data["options"]):
                        FieldOption.objects.create(
                            field=field,
                            label=opt["label"],
                            value=opt["value"],
                            order=o_idx
                        )

    @classmethod
    def _sync_relational_models_report(cls, template, data):
        # Clear existing fields
        template.fields.all().delete()
        
        current_order = 0
        for s_idx, section_data in enumerate(data.get("sections", [])):
            # Add heading for section
            ReportTemplateField.objects.create(
                template=template,
                label=section_data["title"],
                key=f"section_h_{s_idx}",
                field_type="heading",
                order=current_order,
                is_active=True
            )
            current_order += 1
            
            for f_idx, field_data in enumerate(section_data.get("fields", [])):
                field_type = TYPE_MAPPING.get(field_data["type"], "short_text")
                field = ReportTemplateField.objects.create(
                    template=template,
                    label=field_data["label"],
                    key=field_data["key"],
                    field_type=field_type,
                    is_required=field_data.get("required", False),
                    help_text=field_data.get("help_text", ""),
                    placeholder=field_data.get("placeholder", ""),
                    order=current_order,
                    is_active=True
                )
                current_order += 1
                
                # Options
                if "options" in field_data:
                    for o_idx, opt in enumerate(field_data["options"]):
                        ReportTemplateFieldOption.objects.create(
                            field=field,
                            label=opt["label"],
                            value=opt["value"],
                            order=o_idx,
                            is_active=True
                        )
                elif field_data["type"] == "boolean":
                    # Add standard Yes/No options for boolean type mapped to radio
                    ReportTemplateFieldOption.objects.create(field=field, label="Yes", value="true", order=0)
                    ReportTemplateFieldOption.objects.create(field=field, label="No", value="false", order=1)

    @classmethod
    def export_package(cls, code, version_num=None):
        # Prefer ReportTemplate if exists, otherwise fall back to Template
        report_template = ReportTemplate.objects.filter(code=code).first()
        if report_template:
            # Construct JSON from ReportTemplate or return stored schema if we had one
            # For now, we still rely on TemplateVersion for the full schema snapshot
            pass

        template = Template.objects.filter(code=code).first()
        if not template:
            # Maybe check ReportTemplate?
            if report_template:
                # We should probably have a way to export ReportTemplate as Package
                # For now, let's assume we maintain Template for export compatibility
                pass
            raise ValidationError(f"Template '{code}' not found")

        if version_num:
            version = template.versions.filter(version=version_num).first()
            if not version:
                raise ValidationError(f"Version {version_num} not found for '{code}'")
            return version.schema
        else:
            latest = template.versions.order_by("-version").first()
            if latest:
                return latest.schema
            return {}
