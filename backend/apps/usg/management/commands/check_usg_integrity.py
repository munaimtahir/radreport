from django.core.management.base import BaseCommand
from django.db.models import Count, Q
from apps.catalog.models import Service
from apps.workflow.models import USGReport
from apps.templates.models import Template, TemplateVersion

class Command(BaseCommand):
    help = "Diagnostic checks for USG system integrity"

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Automatically fix identified issues where safe to do so',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting USG System Integrity Check..."))
        fix_mode = options['fix']
        
        if fix_mode:
            self.stdout.write(self.style.WARNING("Running in FIX mode - changes will be applied!"))

        # 1. USG Services without templates
        self.stdout.write("\n--- 1. USG Services without Default Template ---")
        usg_services_no_template = Service.objects.filter(
            modality__code="USG",
            default_template__isnull=True,
            is_active=True
        )
        if usg_services_no_template.exists():
            for service in usg_services_no_template:
                self.stdout.write(self.style.WARNING(f"  [MISSING] Service: {service.name} ({service.code})"))
                if fix_mode:
                    self.stdout.write("    - No automatic fix available. Please assign a template in Admin or using import tools.")
        else:
            self.stdout.write(self.style.SUCCESS("  [OK] All active USG services have default templates."))

        # 2. USG Services linked to ReportTemplate (Deprecated)
        self.stdout.write("\n--- 2. USG Services linked to DEPRECATED ReportTemplate (Flat) ---")
        from apps.templates.models import ServiceReportTemplate
        deprecated_links = ServiceReportTemplate.objects.filter(
            service__modality__code="USG"
        ).select_related("service", "template")
        
        if deprecated_links.exists():
            for link in deprecated_links:
                self.stdout.write(self.style.ERROR(f"  [FORBIDDEN] Service {link.service.name} linked to Flat Template '{link.template.name}'"))
                if fix_mode:
                    link.delete()
                    self.stdout.write(self.style.SUCCESS(f"    - FIXED: Deleted forbidden link for {link.service.name}"))
        else:
            self.stdout.write(self.style.SUCCESS("  [OK] No USG services linked to deprecated flat templates."))

        # 3. USG Reports without template_version
        self.stdout.write("\n--- 3. USG Reports without Template Version ---")
        reports_no_version = USGReport.objects.filter(
            template_version__isnull=True
        ).select_related('service_visit_item__service__default_template')
        
        if reports_no_version.exists():
             for report in reports_no_version:
                 svc_name = report.service_visit_item.service.name if report.service_visit_item and report.service_visit_item.service else "Unknown"
                 self.stdout.write(self.style.WARNING(f"  [LEGACY/ERROR] Report {report.id} (Service: {svc_name}) has no template_version"))
                 
                 if fix_mode:
                     item = report.service_visit_item
                     if item and item.service and item.service.default_template:
                         # Find latest published version
                         latest_v = item.service.default_template.versions.filter(is_published=True).order_by('-version').first()
                         if latest_v:
                             report.template_version = latest_v
                             report.save(update_fields=['template_version'])
                             self.stdout.write(self.style.SUCCESS(f"    - FIXED: Assigned {latest_v} to report."))
                         else:
                             self.stdout.write(self.style.ERROR("    - FAILED: No published version found for service template."))
                     else:
                         self.stdout.write(self.style.ERROR("    - FAILED: Service has no default template."))
        else:
            self.stdout.write(self.style.SUCCESS("  [OK] All USG reports have template versions."))

        # 4. Templates without published versions
        self.stdout.write("\n--- 4. Active USG Templates without Published Versions ---")
        usg_templates = Template.objects.filter(modality_code="USG", is_active=True)
        
        ok_count = 0
        warn_count = 0
        for template in usg_templates:
            has_published = template.versions.filter(is_published=True).exists()
            if not has_published:
                self.stdout.write(self.style.WARNING(f"  [UNPUBLISHED] Template '{template.name}' has no published versions."))
                warn_count += 1
                if fix_mode:
                    # Try to find a version to publish
                    latest_draft = template.versions.all().order_by('-version').first()
                    if latest_draft:
                        latest_draft.is_published = True
                        latest_draft.save(update_fields=['is_published'])
                        self.stdout.write(self.style.SUCCESS(f"    - FIXED: Published latest draft v{latest_draft.version}"))
                    else:
                         self.stdout.write(self.style.ERROR("    - FAILED: No versions exist to publish."))
            else:
                ok_count += 1
        
        if warn_count == 0:
            self.stdout.write(self.style.SUCCESS(f"  [OK] All {ok_count} active USG templates have published versions."))

        self.stdout.write(self.style.SUCCESS("\nDiagnostic check complete."))
