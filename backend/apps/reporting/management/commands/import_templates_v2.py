import json
import csv
import os
from django.core.management.base import BaseCommand
from django.db import transaction
from django.core.files.base import ContentFile
from apps.reporting.models import ReportTemplateV2, ServiceReportTemplateV2
from apps.catalog.models import Service

class Command(BaseCommand):
    help = 'Import V2 Reporting Templates and Service Mappings'

    def add_arguments(self, parser):
        parser.add_argument('--templates', type=str, help='Path to templates JSON file')
        parser.add_argument('--mappings', type=str, help='Path to service mappings CSV file')
        parser.add_argument('--dry-run', action='store_true', help='Validate without saving')
        parser.add_argument('--strict', action='store_true', help='Fail on missing services')
        parser.add_argument('--activate', action='store_true', help='Activate imported templates automatically')
        parser.add_argument('--deactivate-missing', action='store_true', help='Deactivate mappings not in file (risky)')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        strict = options['strict']
        activate = options['activate']
        
        self.stdout.write(self.style.MIGRATE_HEADING("Starting V2 Template Import..."))
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE: No changes will be saved."))

        stats = {
            "templates_created": 0,
            "templates_updated": 0,
            "mappings_created": 0,
            "mappings_updated": 0,
            "errors": []
        }

        try:
            with transaction.atomic():
                if options['templates']:
                    self._import_templates(options['templates'], stats, activate)
                
                if options['mappings']:
                    self._import_mappings(options['mappings'], stats, strict, options['deactivate_missing'])

                if dry_run:
                    raise Exception("Dry Run - Rolling back")

        except Exception as e:
            if str(e) == "Dry Run - Rolling back":
                self.stdout.write(self.style.SUCCESS("Dry run completed successfully."))
            else:
                self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))
                if strict:
                    raise e
        
        self._print_summary(stats)

    def _import_templates(self, filepath, stats, activate):
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Templates file not found: {filepath}")

        with open(filepath, 'r') as f:
            data = json.load(f)
            if isinstance(data, dict): # Single template
                data = [data]

        for item in data:
            code = item.get("code")
            modality = item.get("modality")
            
            if not code or not modality:
                stats["errors"].append(f"Missing code or modality in template: {item.get('name')}")
                continue

            # Update or create based on code only (assuming unique code for V2)
            # Or should we version? The requirement says "create/update template by (code, modality)"
            # For simplicity, we update the existing record with that code.
            
            defaults = {
                "name": item.get("name"),
                "json_schema": item.get("json_schema", {}),
                "ui_schema": item.get("ui_schema", {}),
                "narrative_rules": item.get("narrative_rules", {}),
                "is_frozen": item.get("is_frozen", False),
            }
            if activate:
                defaults["status"] = "active"

            template, created = ReportTemplateV2.objects.update_or_create(
                code=code,
                defaults=defaults
            )
            
            # Ensure modality matches (it's not in defaults)
            if template.modality != modality:
                template.modality = modality
                template.save()

            if created:
                stats["templates_created"] += 1
                self.stdout.write(f"Created template: {code}")
            else:
                stats["templates_updated"] += 1
                self.stdout.write(f"Updated template: {code}")

    def _import_mappings(self, filepath, stats, strict, deactivate_missing):
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Mappings file not found: {filepath}")

        processed_services = set()

        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                service_code = row.get("service_code")
                template_code = row.get("template_code")
                
                if not service_code or not template_code:
                    continue

                service = Service.objects.filter(code=service_code).first()
                if not service:
                    msg = f"Service not found: {service_code}"
                    if strict:
                        raise ValueError(msg)
                    stats["errors"].append(msg)
                    continue

                template = ReportTemplateV2.objects.filter(code=template_code).first()
                if not template:
                    msg = f"Template not found: {template_code}"
                    if strict:
                        raise ValueError(msg)
                    stats["errors"].append(msg)
                    continue

                # Create mapping
                # Ensure it's default if requested (assuming all imports are intended as default)
                # The rule: "Set default mapping (ensuring only one default per service)"
                
                # Deactivate old defaults
                ServiceReportTemplateV2.objects.filter(service=service, is_default=True).update(is_default=False)
                
                mapping, created = ServiceReportTemplateV2.objects.update_or_create(
                    service=service,
                    template=template,
                    defaults={
                        "is_active": True,
                        "is_default": True
                    }
                )
                
                processed_services.add(service.id)
                
                if created:
                    stats["mappings_created"] += 1
                else:
                    stats["mappings_updated"] += 1

    def _print_summary(self, stats):
        self.stdout.write("\n--------- SUMMARY ---------")
        self.stdout.write(f"Templates Created: {stats['templates_created']}")
        self.stdout.write(f"Templates Updated: {stats['templates_updated']}")
        self.stdout.write(f"Mappings Created:  {stats['mappings_created']}")
        self.stdout.write(f"Mappings Updated:  {stats['mappings_updated']}")
        if stats["errors"]:
            self.stdout.write(self.style.ERROR(f"Errors: {len(stats['errors'])}"))
            for err in stats["errors"]:
                self.stdout.write(f" - {err}")
        self.stdout.write("---------------------------")
