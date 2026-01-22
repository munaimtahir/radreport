"""
Management command to link all USG services to their templates.

Usage:
    python manage.py link_usg_services
    python manage.py link_usg_services --dry-run
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from apps.catalog.models import Service
from apps.templates.models import Template
from collections import defaultdict


class Command(BaseCommand):
    help = 'Link all USG services to their corresponding templates'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes'
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)

        self.stdout.write('')
        self.stdout.write(self.style.WARNING('=' * 70))
        if dry_run:
            self.stdout.write(self.style.WARNING('  USG Service Linking (DRY RUN)'))
        else:
            self.stdout.write(self.style.WARNING('  USG Service Linking'))
        self.stdout.write(self.style.WARNING('=' * 70))
        self.stdout.write('')

        # Get all USG services
        try:
            usg_services = Service.objects.filter(modality__code='USG')
        except Exception:
            # Fallback if modality doesn't exist
            usg_services = Service.objects.filter(code__startswith='USG_')

        if not usg_services.exists():
            self.stdout.write(self.style.ERROR('✗ No USG services found!'))
            self.stdout.write('')
            self.stdout.write('Searching for services containing "ultrasound"...')
            usg_services = Service.objects.filter(name__icontains='ultrasound')
            if not usg_services.exists():
                self.stdout.write(self.style.ERROR('✗ No ultrasound services found either!'))
                return

        self.stdout.write(f'Found {usg_services.count()} USG services:')
        for s in usg_services:
            self.stdout.write(f'  - {s.code}: {s.name}')
        self.stdout.write('')

        # Get all available templates
        templates = Template.objects.filter(modality_code='USG')
        if not templates.exists():
            self.stdout.write(self.style.ERROR('✗ No USG templates found!'))
            self.stdout.write('')
            self.stdout.write('You need to import templates first:')
            self.stdout.write('  python manage.py import_usg_template /path/to/template.json')
            return

        self.stdout.write(f'Found {templates.count()} USG templates:')
        for t in templates:
            self.stdout.write(f'  - {t.code}: {t.name}')
        self.stdout.write('')

        # Common mappings (service code → template code)
        # Adjust these based on your actual service and template codes
        common_mappings = {
            'USG_ABDOMEN': 'USG_ABDOMEN_BASIC',
            'USG_PELVIS': 'USG_PELVIS_BASIC',
            'USG_KUB': 'USG_KUB_BASIC',
            'USG_BREAST': 'USG_BREAST_BASIC',
            'USG_THYROID': 'USG_THYROID_BASIC',
            'USG_OB': 'USG_OB_BASIC',
            'USG_CAROTID': 'USG_CAROTID_BASIC',
            'USG_DOPPLER': 'USG_DOPPLER_BASIC',
            'USG_RENAL': 'USG_RENAL_BASIC',
            'USG_PORTAL': 'USG_PORTAL_BASIC',
        }

        # Try to auto-map by matching names
        auto_mappings = {}
        for service in usg_services:
            # Check common mappings first
            if service.code in common_mappings:
                template_code = common_mappings[service.code]
                template = templates.filter(code=template_code).first()
                if template:
                    auto_mappings[service.code] = template.code
                    continue

            # Try to find template by matching service name
            # e.g., "Ultrasound Abdomen" → "USG_ABDOMEN_BASIC"
            service_name_lower = service.name.lower()
            for template in templates:
                template_name_lower = template.name.lower()
                # Extract key words (abdomen, pelvis, kub, etc.)
                if any(keyword in service_name_lower and keyword in template_name_lower 
                       for keyword in ['abdomen', 'pelvis', 'kub', 'breast', 'thyroid', 
                                       'obstetric', 'carotid', 'doppler', 'renal', 'portal']):
                    auto_mappings[service.code] = template.code
                    break

        # Show mappings
        self.stdout.write('Proposed mappings:')
        self.stdout.write('')

        stats = {'success': 0, 'skipped': 0, 'error': 0}

        for service in usg_services:
            if service.code in auto_mappings:
                template_code = auto_mappings[service.code]
                template = templates.get(code=template_code)
                
                if service.default_template == template:
                    self.stdout.write(
                        f'  ⊙ {service.code:20} → {template_code:25} (already linked)'
                    )
                    stats['skipped'] += 1
                else:
                    self.stdout.write(
                        f'  ✓ {service.code:20} → {template_code:25}'
                    )
                    stats['success'] += 1
                    
                    if not dry_run:
                        service.default_template = template
                        service.save()
            else:
                self.stdout.write(
                    self.style.WARNING(f'  ✗ {service.code:20} → (no template match)')
                )
                stats['error'] += 1

        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.WARNING('=' * 70))
        self.stdout.write(self.style.WARNING('  Summary'))
        self.stdout.write(self.style.WARNING('=' * 70))
        self.stdout.write(f'  Services processed: {usg_services.count()}')
        self.stdout.write(self.style.SUCCESS(f'  ✓ Linked: {stats["success"]}'))
        self.stdout.write(f'  ⊙ Already linked: {stats["skipped"]}')
        if stats['error'] > 0:
            self.stdout.write(self.style.ERROR(f'  ✗ No match: {stats["error"]}'))
        self.stdout.write(self.style.WARNING('=' * 70))
        self.stdout.write('')

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - No changes made'))
            self.stdout.write('Run without --dry-run to apply changes')
        else:
            self.stdout.write(self.style.SUCCESS('✓ Linking complete!'))

        # Show unmatched services
        if stats['error'] > 0:
            self.stdout.write('')
            self.stdout.write('Unmatched services need manual linking or template import:')
            for service in usg_services:
                if service.code not in auto_mappings:
                    self.stdout.write(f'  - {service.code}: {service.name}')
                    self.stdout.write(f'    Action: Import template for this exam type')
            self.stdout.write('')

        # Verification
        if not dry_run:
            self.stdout.write('')
            self.stdout.write('Verification:')
            linked_count = Service.objects.filter(
                default_template__isnull=False,
                modality__code='USG'
            ).count()
            self.stdout.write(f'  USG services with templates: {linked_count}/{usg_services.count()}')
