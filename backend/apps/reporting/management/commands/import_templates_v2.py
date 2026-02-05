import csv
import json
import os
import re
from difflib import get_close_matches
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError


class _DryRunRollback(Exception):
    pass
from django.db import transaction

from apps.catalog.models import Service
from apps.reporting.models import ReportTemplateV2, ServiceReportTemplateV2


class Command(BaseCommand):
    help = "Import V2 Reporting Templates and Service Mappings"

    def add_arguments(self, parser):
        parser.add_argument("--templates", type=str, help="Path to templates JSON file or directory")
        parser.add_argument("--mappings", type=str, help="Path to service mappings CSV file")
        parser.add_argument("--dry-run", action="store_true", help="Validate without saving")
        parser.add_argument("--strict", action="store_true", help="Fail on missing services")

    def handle(self, *args, **options):
        base_dir = Path(__file__).resolve().parents[2] / "seed_data" / "templates_v2"
        templates_path = Path(options.get("templates") or base_dir)
        mappings_path = Path(options.get("mappings") or (base_dir / "service_template_map.csv"))
        dry_run = options["dry_run"]
        strict = options["strict"]

        self.stdout.write(self.style.MIGRATE_HEADING("Starting V2 template import"))
        self.stdout.write(f"Templates source: {templates_path}")
        self.stdout.write(f"Mappings source:  {mappings_path}")
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE: no changes will be persisted."))

        stats = {
            "templates_created": 0,
            "templates_updated": 0,
            "mappings_created": 0,
            "mappings_updated": 0,
            "errors": [],
            "unresolved_services": [],
        }

        try:
            with transaction.atomic():
                self._import_templates(templates_path, stats)
                self._import_mappings(mappings_path, stats, strict)
                if dry_run:
                    raise _DryRunRollback()
        except _DryRunRollback:
            pass

        self._print_summary(stats)

    def _template_files(self, templates_path: Path):
        if not templates_path.exists():
            raise CommandError(f"Templates path not found: {templates_path}")
        if templates_path.is_dir():
            files = sorted(templates_path.glob("*.json"))
            if not files:
                raise CommandError(f"No template JSON files found under: {templates_path}")
            return files
        return [templates_path]

    def _import_templates(self, templates_path: Path, stats: dict):
        for filepath in self._template_files(templates_path):
            payload = json.loads(filepath.read_text(encoding="utf-8"))
            items = payload if isinstance(payload, list) else [payload]

            for item in items:
                code = item.get("code")
                modality = item.get("modality")
                if not code or not modality:
                    stats["errors"].append(f"{filepath.name}: missing code/modality")
                    continue

                defaults = {
                    "name": item.get("name", code),
                    "modality": modality,
                    "status": item.get("status", "draft"),
                    "json_schema": item.get("json_schema", {}),
                    "ui_schema": item.get("ui_schema", {}),
                    "narrative_rules": item.get("narrative_rules", {}),
                    "is_frozen": bool(item.get("is_frozen", False)),
                }
                _, created = ReportTemplateV2.objects.update_or_create(code=code, defaults=defaults)
                key = "templates_created" if created else "templates_updated"
                stats[key] += 1

    @staticmethod
    def _norm(value: str):
        return re.sub(r"[^a-z0-9]+", "", (value or "").strip().lower())

    def _find_service(self, row, norm_index):
        service_code = (row.get("service_code") or "").strip()
        service_slug = (row.get("service_slug") or "").strip()
        service_name = (row.get("service_name") or "").strip()

        if service_code:
            service = Service.objects.filter(code=service_code).first()
            if service:
                return service, f"service_code:{service_code}"

        if service_slug:
            service = norm_index.get(self._norm(service_slug))
            if service:
                return service, f"service_slug:{service_slug}"

        if service_name:
            service = norm_index.get(self._norm(service_name))
            if service:
                return service, f"service_name:{service_name}"

        identifier = service_code or service_slug or service_name
        return None, identifier

    def _closest_names(self, identifier, service_names):
        if not identifier:
            return []
        return get_close_matches(identifier, service_names, n=5, cutoff=0.3)

    def _import_mappings(self, filepath: Path, stats: dict, strict: bool):
        if not filepath.exists():
            raise CommandError(f"Mappings file not found: {filepath}")

        services = list(Service.objects.all())
        norm_index = {self._norm(s.name): s for s in services}
        service_names = [s.name for s in services]

        with filepath.open("r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                template_code = (row.get("template_code") or "").strip()
                if not template_code:
                    continue
                template = ReportTemplateV2.objects.filter(code=template_code).first()
                if not template:
                    msg = f"Template not found: {template_code}"
                    if strict:
                        raise CommandError(msg)
                    stats["errors"].append(msg)
                    continue

                service, identifier = self._find_service(row, norm_index)
                if not service:
                    suggestions = self._closest_names(identifier, service_names)
                    msg = f"Service not found: '{identifier}'"
                    if suggestions:
                        msg = f"{msg}. closest={', '.join(suggestions)}"
                    stats["unresolved_services"].append(msg)
                    if strict:
                        raise CommandError(msg)
                    continue

                is_active = str(row.get("is_active", "true")).strip().lower() in {"1", "true", "yes"}
                is_default = str(row.get("is_default", "false")).strip().lower() in {"1", "true", "yes"}

                if is_default:
                    ServiceReportTemplateV2.objects.filter(service=service, is_default=True).exclude(template=template).update(is_default=False)

                _, created = ServiceReportTemplateV2.objects.update_or_create(
                    service=service,
                    template=template,
                    defaults={"is_active": is_active, "is_default": is_default},
                )
                key = "mappings_created" if created else "mappings_updated"
                stats[key] += 1

    def _print_summary(self, stats: dict):
        self.stdout.write("\n--------- SUMMARY ---------")
        self.stdout.write(f"Templates Created: {stats['templates_created']}")
        self.stdout.write(f"Templates Updated: {stats['templates_updated']}")
        self.stdout.write(f"Mappings Created:  {stats['mappings_created']}")
        self.stdout.write(f"Mappings Updated:  {stats['mappings_updated']}")
        if stats["errors"]:
            self.stdout.write(self.style.ERROR(f"Errors ({len(stats['errors'])}):"))
            for err in stats["errors"]:
                self.stdout.write(f" - {err}")
        if stats["unresolved_services"]:
            self.stdout.write(self.style.WARNING(f"Unresolved services ({len(stats['unresolved_services'])}):"))
            for err in stats["unresolved_services"]:
                self.stdout.write(f" - {err}")
        self.stdout.write("---------------------------")
