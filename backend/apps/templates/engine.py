import json
import logging
import jsonschema
from django.conf import settings
from django.db import transaction
from django.core.exceptions import ValidationError
from apps.templates.models import Template, TemplateVersion, TemplateSection, TemplateField, FieldOption
from pathlib import Path

logger = logging.getLogger(__name__)

SCHEMA_PATH = Path(settings.BASE_DIR) / "apps" / "templates" / "schema" / "template_package_v1.json"

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
        existing = Template.objects.filter(code=code).first()

        if mode == "create":
            if existing:
                raise ValidationError(f"Template with code '{code}' already exists.")
            template = Template.objects.create(
                code=code,
                name=data["name"],
                modality_code=data.get("category", ""),
                is_active=True
            )
        elif mode == "update":
            if not existing:
                raise ValidationError(f"Template with code '{code}' does not exist.")
            template = existing
            # Update mutable fields
            template.name = data["name"]
            template.modality_code = data.get("category", template.modality_code)
            template.save()
        else:
            raise ValueError(f"Invalid import mode: {mode}")

        # Create new version
        new_version_num = 1
        last_version = template.versions.order_by("-version").first()
        if last_version:
            new_version_num = last_version.version + 1

        version = TemplateVersion.objects.create(
            template=template,
            version=new_version_num,
            schema=data,  # Store the full package as the schema snapshot
            is_published=True # Auto-publish for now
        )

        # Sync relational models (optional, but good for querying)
        # We wipe old sections/fields for the *template* relational view?
        # Ideally, we should keep the relational models in sync with the LATEST version.
        # OR we treat relational models as just a "current state" cache.
        # Given the requirements: "Templates are authored externally... persisted... safely"
        # And "Importing update creates version+1"
        
        # We will Replace relational data for the 'Head' template to match this new version
        # This allows query-based operations on the "current" template.
        cls._sync_relational_models(template, data)

        return template, version

    @classmethod
    def _sync_relational_models(cls, template, data):
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
    def export_package(cls, code, version_num=None):
        template = Template.objects.filter(code=code).first()
        if not template:
            raise ValidationError(f"Template '{code}' not found")

        if version_num:
            version = template.versions.filter(version=version_num).first()
            if not version:
                raise ValidationError(f"Version {version_num} not found for '{code}'")
            return version.schema
        else:
            # Export latest HEAD via relational models OR latest version?
            # Requirement: "Export v1 -> matches imported JSON"
            # So safer to return the stored JSON in the version.
            latest = template.versions.order_by("-version").first()
            if latest:
                return latest.schema
            
            # If no version exists (legacy?), construct from relational
            # (Not implemented for legacy, assuming we start fresh or migrate)
            return {}
