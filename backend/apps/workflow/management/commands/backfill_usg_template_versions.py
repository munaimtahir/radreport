"""
Management command to backfill missing template_version for USG reports.
Usage: python manage.py backfill_usg_template_versions
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.workflow.models import USGReport
from apps.templates.models import Template, TemplateVersion


class Command(BaseCommand):
    help = "Backfill missing template_version for USG reports"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Run in dry-run mode without making changes",
        )

    def handle(self, *args, **options):
        dry_run = options.get("dry_run", False)
        
        # Find reports without template_version
        reports_without_template = USGReport.objects.filter(template_version__isnull=True)
        count = reports_without_template.count()
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS("All USG reports have template_version. Nothing to do."))
            return
        
        self.stdout.write(f"Found {count} USG reports without template_version")
        
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No changes will be made"))
        
        fixed_count = 0
        error_count = 0
        
        for report in reports_without_template.select_related('service_visit_item__service'):
            service = report.service_visit_item.service if report.service_visit_item else None
            
            if not service:
                self.stdout.write(self.style.ERROR(
                    f"Report {report.id}: No service found, cannot resolve template"
                ))
                error_count += 1
                continue
            
            # Try to get default template from service
            template = service.default_template
            if not template:
                self.stdout.write(self.style.ERROR(
                    f"Report {report.id}: Service {service.code} has no default_template"
                ))
                error_count += 1
                continue
            
            # Get latest published version
            template_version = template.versions.filter(is_published=True).order_by("-version").first()
            if not template_version:
                self.stdout.write(self.style.ERROR(
                    f"Report {report.id}: Template {template.name} has no published version"
                ))
                error_count += 1
                continue
            
            # Backfill
            if not dry_run:
                report.template_version = template_version
                report.save(update_fields=["template_version"])
            
            self.stdout.write(self.style.SUCCESS(
                f"Report {report.id}: Set template_version to {template_version.template.name} v{template_version.version}"
            ))
            fixed_count += 1
        
        if dry_run:
            self.stdout.write(self.style.WARNING(
                f"DRY RUN: Would fix {fixed_count} reports, {error_count} errors"
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f"Fixed {fixed_count} reports, {error_count} errors"
            ))
