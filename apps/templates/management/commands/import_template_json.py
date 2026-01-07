import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

# NOTE: adjust import paths if your project uses a different app layout.
from apps.templates.models import Template, TemplateSection, TemplateField, FieldOption, TemplateVersion


def _safe_bool(v, default=False):
    if v is None:
        return default
    if isinstance(v, bool):
        return v
    if isinstance(v, str):
        return v.strip().lower() in ("1", "true", "yes", "y", "on")
    return bool(v)


def build_schema(template: Template) -> dict:
    """
    Build a renderable schema snapshot for TemplateVersion.
    Kept local (instead of importing from api layer) to avoid circular imports.
    """
    schema = {
        "template_id": str(template.id),
        "name": template.name,
        "modality_code": template.modality_code,
        "sections": [],
    }

    for sec in template.sections.all().order_by("order", "id"):
        sec_obj = {
            "id": str(sec.id),
            "title": sec.title,
            "order": sec.order,
            "fields": [],
        }

        for f in sec.fields.all().order_by("order", "id"):
            field_obj = {
                "id": str(f.id),
                "label": f.label,
                "key": f.key,
                "type": f.field_type,
                "required": f.required,
                "help_text": f.help_text,
                "placeholder": f.placeholder,
                "unit": f.unit,
                "order": f.order,
                "options": [],
            }

            for o in f.options.all().order_by("order", "id"):
                field_obj["options"].append(
                    {"label": o.label, "value": o.value, "order": o.order}
                )

            sec_obj["fields"].append(field_obj)

        schema["sections"].append(sec_obj)

    return schema


class Command(BaseCommand):
    help = "Import a template preset JSON into Template/Sections/Fields/Options, then publish TemplateVersion."

    def add_arguments(self, parser):
        parser.add_argument("--path", required=True, help="Path to template JSON file")
        parser.add_argument(
            "--replace",
            action="store_true",
            help="If template exists, delete old sections/fields/options before re-import",
        )
        parser.add_argument(
            "--publish",
            action="store_true",
            default=True,
            help="Publish a new TemplateVersion after import",
        )
        parser.add_argument(
            "--link-service",
            default="",
            help='Service name to set default_template to this template (exact match, optional)',
        )

    @transaction.atomic
    def handle(self, *args, **opts):
        path = Path(opts["path"])
        if not path.exists():
            raise CommandError(f"Template JSON not found: {path}")

        data = json.loads(path.read_text(encoding="utf-8"))

        name = (data.get("name") or "").strip()
        modality_code = (data.get("modality_code") or "").strip()
        is_active = _safe_bool(data.get("is_active", True), True)
        sections = data.get("sections") or []

        if not name:
            raise CommandError("JSON must contain non-empty: name")

        template, created = Template.objects.get_or_create(
            name=name,
            modality_code=modality_code,
            defaults={"is_active": is_active},
        )

        if not created:
            template.is_active = is_active
            template.save(update_fields=["is_active"])

            if opts["replace"]:
                template.sections.all().delete()

        # Import sections / fields / options
        for sec in sections:
            sec_title = (sec.get("title") or "").strip()
            if not sec_title:
                raise CommandError("Each section must have: title")

            sec_obj = TemplateSection.objects.create(
                template=template,
                title=sec_title,
                order=int(sec.get("order", 0)),
            )

            for f in sec.get("fields") or []:
                label = (f.get("label") or "").strip()
                key = (f.get("key") or "").strip()
                field_type = (f.get("field_type") or "").strip()

                if not (label and key and field_type):
                    raise CommandError(f"Field missing label/key/field_type in section: {sec_title}")

                field = TemplateField.objects.create(
                    section=sec_obj,
                    label=label,
                    key=key,
                    field_type=field_type,
                    required=_safe_bool(f.get("required", False)),
                    help_text=f.get("help_text", "") or "",
                    placeholder=f.get("placeholder", "") or "",
                    unit=f.get("unit", "") or "",
                    order=int(f.get("order", 0)),
                )

                for o in f.get("options") or []:
                    FieldOption.objects.create(
                        field=field,
                        label=(o.get("label") or "").strip(),
                        value=(o.get("value") or "").strip(),
                        order=int(o.get("order", 0)),
                    )

        # Publish new version
        if opts["publish"]:
            latest = template.versions.order_by("-version").first()
            next_version = 1 if not latest else (latest.version + 1)

            TemplateVersion.objects.create(
                template=template,
                version=next_version,
                schema=build_schema(template),
                is_published=True,
            )
            self.stdout.write(self.style.SUCCESS(f"Published {template.name} v{next_version}"))
        else:
            self.stdout.write(self.style.WARNING("Skipped publishing TemplateVersion"))

        # Link service default template (optional)
        service_name = (opts.get("link_service") or "").strip()
        if service_name:
            try:
                # Import here so projects without catalog app still run command without link-service.
                from apps.catalog.models import Service  # type: ignore

                svc = Service.objects.get(name=service_name)
                svc.default_template = template
                svc.save(update_fields=["default_template"])
                self.stdout.write(self.style.SUCCESS(f'Linked template to service: "{service_name}"'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Could not link service "{service_name}": {e}'))

        self.stdout.write(self.style.SUCCESS(f"Imported template: {template.name} ({template.modality_code})"))
