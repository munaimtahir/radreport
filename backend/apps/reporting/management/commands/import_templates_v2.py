import csv
import json
from pathlib import Path
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.catalog.models import Service
from apps.reporting.models import ReportTemplateV2, ServiceReportTemplateV2


class Command(BaseCommand):
    help = "Import V2 reporting templates and service mappings."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Validate without writing to DB")

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        base_dir = Path(__file__).resolve().parents[2] / "seed_data" / "templates_v2"
        templates_dir = base_dir
        mapping_path = base_dir / "service_template_map.csv"

        if not templates_dir.exists():
            self.stdout.write(self.style.ERROR("Templates directory not found."))
            return

        template_files = sorted([p for p in templates_dir.glob("*.json")])
        if not template_files:
            self.stdout.write(self.style.WARNING("No template JSON files found."))

        templates_created = 0
        templates_updated = 0
        mappings_created = 0
        mappings_updated = 0
        unresolved = []
        template_cache = {}

        def normalize_name(value: str) -> str:
            return " ".join(value.strip().lower().split())

        def resolve_service(code, slug, name):
            if code:
                svc = Service.objects.filter(code=code).first()
                if svc:
                    return svc
            if slug:
                svc = Service.objects.filter(slug=slug).first()
                if svc:
                    return svc
            if name:
                normalized = normalize_name(name)
                for svc in Service.objects.all():
                    if normalize_name(svc.name) == normalized:
                        return svc
            return None

        def upsert_template(payload):
            nonlocal templates_created, templates_updated
            code = payload.get("code")
            if not code:
                raise ValueError("Template missing code")
            defaults = {
                "name": payload.get("name", ""),
                "modality": payload.get("modality", ""),
                "status": payload.get("status", "active"),
                "is_frozen": payload.get("is_frozen", False),
                "json_schema": payload.get("json_schema", {}),
                "ui_schema": payload.get("ui_schema", {}),
                "narrative_rules": payload.get("narrative_rules", {}),
            }
            existing = ReportTemplateV2.objects.filter(code=code).first()
            if dry_run:
                if existing:
                    templates_updated += 1
                else:
                    templates_created += 1
                template_cache[code] = defaults
                return existing
            obj, created = ReportTemplateV2.objects.update_or_create(code=code, defaults=defaults)
            if created:
                templates_created += 1
            else:
                templates_updated += 1
            return obj

        def upsert_mapping(service, template, is_default, is_active):
            nonlocal mappings_created, mappings_updated
            existing = ServiceReportTemplateV2.objects.filter(service=service, template=template).first()
            if dry_run:
                if existing:
                    mappings_updated += 1
                else:
                    mappings_created += 1
                return
            obj, created = ServiceReportTemplateV2.objects.update_or_create(
                service=service,
                template=template,
                defaults={
                    "is_default": is_default,
                    "is_active": is_active,
                },
            )
            if created:
                mappings_created += 1
            else:
                mappings_updated += 1
            if is_default:
                ServiceReportTemplateV2.objects.filter(service=service).exclude(id=obj.id).update(is_default=False)

        context = transaction.atomic() if not dry_run else _noop()
        with context:
            for template_file in template_files:
                payload = json.loads(template_file.read_text())
                upsert_template(payload)

            if mapping_path.exists():
                with mapping_path.open(newline="") as csvfile:
                    reader = csv.DictReader(csvfile)
                    for row in reader:
                        template_code = (row.get("template_code") or "").strip()
                        service_code = (row.get("service_code") or "").strip()
                        service_slug = (row.get("service_slug") or "").strip()
                        service_name = (row.get("service_name") or "").strip()
                        is_default = str(row.get("is_default") or "").strip().lower() in {"true", "1", "yes", "y"}
                        is_active = str(row.get("is_active") or "").strip().lower() not in {"false", "0", "no", "n"}

                        template = template_cache.get(template_code) if dry_run else ReportTemplateV2.objects.filter(code=template_code).first()
                        if not template:
                            self.stdout.write(self.style.WARNING(f"Template not found: {template_code}"))
                            continue

                        service = resolve_service(service_code, service_slug, service_name)
                        if not service:
                            unresolved.append(service_code or service_slug or service_name)
                            self.stdout.write(self.style.WARNING(
                                f"Service not resolved for mapping row: {service_code or service_slug or service_name}"
                            ))
                            continue

                        if dry_run:
                            mappings_created += 1
                        else:
                            upsert_mapping(service, template, is_default, is_active)

        self.stdout.write(self.style.SUCCESS("Import summary:"))
        self.stdout.write(f"Templates created: {templates_created}")
        self.stdout.write(f"Templates updated: {templates_updated}")
        self.stdout.write(f"Mappings created: {mappings_created}")
        self.stdout.write(f"Mappings updated: {mappings_updated}")
        if unresolved:
            self.stdout.write("Unresolved services:")
            for name in unresolved:
                self.stdout.write(f"- {name}")


class _noop:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False
