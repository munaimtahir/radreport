"""
Management command to import USG templates from JSON files.

Usage:
    python manage.py import_usg_template /path/to/template.json
    python manage.py import_usg_template /path/to/template.json --mode=update
    python manage.py import_usg_template /path/to/template.json --link-service=USG_ABDOMEN
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from apps.templates.engine import TemplatePackageEngine
from apps.templates.models import Template, TemplateVersion
from apps.catalog.models import Service
import json
import sys


class Command(BaseCommand):
    help = 'Import USG template from JSON file and optionally link to service'

    def add_arguments(self, parser):
        parser.add_argument(
            'json_file',
            type=str,
            help='Path to JSON template file'
        )
        parser.add_argument(
            '--mode',
            type=str,
            default='create',
            choices=['create', 'update'],
            help='Import mode: create (default) or update'
        )
        parser.add_argument(
            '--link-service',
            type=str,
            help='Service code to link template to (e.g., USG_ABDOMEN)'
        )
        parser.add_argument(
            '--verify-only',
            action='store_true',
            help='Only validate JSON, do not import'
        )

    def handle(self, *args, **options):
        json_file = options['json_file']
        mode = options['mode']
        service_code = options.get('link_service')
        verify_only = options.get('verify_only', False)

        # Load JSON file
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
        except FileNotFoundError:
            raise CommandError(f'File not found: {json_file}')
        except json.JSONDecodeError as e:
            raise CommandError(f'Invalid JSON: {str(e)}')

        code = data.get('code')
        name = data.get('name')

        self.stdout.write('')
        self.stdout.write(self.style.WARNING('=' * 70))
        self.stdout.write(self.style.WARNING(f'  USG Template Import'))
        self.stdout.write(self.style.WARNING('=' * 70))
        self.stdout.write(f'  File: {json_file}')
        self.stdout.write(f'  Code: {code}')
        self.stdout.write(f'  Name: {name}')
        self.stdout.write(f'  Mode: {mode}')
        if service_code:
            self.stdout.write(f'  Link Service: {service_code}')
        self.stdout.write(self.style.WARNING('=' * 70))
        self.stdout.write('')

        # Validate template structure
        self.stdout.write('Step 1: Validating template structure...')
        is_valid, errors, validated_data = TemplatePackageEngine.validate(data)
        
        if not is_valid:
            self.stdout.write(self.style.ERROR('✗ Validation failed!'))
            for error in errors:
                self.stdout.write(self.style.ERROR(f'  - {error}'))
            sys.exit(1)
        
        self.stdout.write(self.style.SUCCESS('✓ Template structure valid'))
        
        # Show template summary
        sections = data.get('sections', [])
        total_fields = sum(len(s.get('fields', [])) for s in sections)
        self.stdout.write(f'  - Sections: {len(sections)}')
        self.stdout.write(f'  - Total fields: {total_fields}')
        for section in sections:
            field_count = len(section.get('fields', []))
            self.stdout.write(f'    • {section.get("title")}: {field_count} fields')
        self.stdout.write('')

        if verify_only:
            self.stdout.write(self.style.SUCCESS('✓ Verification complete (no import performed)'))
            return

        # Import template
        self.stdout.write(f'Step 2: Importing template (mode={mode})...')
        try:
            with transaction.atomic():
                result = TemplatePackageEngine.import_package(data, mode=mode)
                self.stdout.write(self.style.SUCCESS('✓ Template imported successfully'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Import failed: {str(e)}'))
            sys.exit(1)

        # Verify import
        self.stdout.write('')
        self.stdout.write('Step 3: Verifying import...')
        
        template = Template.objects.filter(code=code).first()
        if not template:
            self.stdout.write(self.style.ERROR('✗ Template not found after import!'))
            sys.exit(1)
        
        self.stdout.write(self.style.SUCCESS(f'✓ Template created: {template.name}'))
        self.stdout.write(f'  - ID: {template.id}')
        self.stdout.write(f'  - Code: {template.code}')
        self.stdout.write(f'  - Modality: {template.modality_code}')
        
        # Check TemplateVersion
        version = TemplateVersion.objects.filter(
            template=template,
            is_published=True
        ).order_by('-version').first()
        
        if not version:
            self.stdout.write(self.style.ERROR('✗ No published TemplateVersion found!'))
            sys.exit(1)
        
        self.stdout.write(self.style.SUCCESS(f'✓ TemplateVersion created: v{version.version}'))
        schema_sections = version.schema.get('sections', [])
        self.stdout.write(f'  - Schema sections: {len(schema_sections)}')
        
        # Link to service if requested
        if service_code:
            self.stdout.write('')
            self.stdout.write(f'Step 4: Linking to service {service_code}...')
            
            try:
                service = Service.objects.get(code=service_code)
            except Service.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'✗ Service not found: {service_code}'))
                self.stdout.write(self.style.WARNING('  Template imported but not linked to service'))
            else:
                service.default_template = template
                service.save()
                self.stdout.write(self.style.SUCCESS(f'✓ Linked to service: {service.name}'))
                self.stdout.write(f'  - Service ID: {service.id}')
                self.stdout.write(f'  - Service Code: {service.code}')

        # Final summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('  Import Complete!'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS(f'✓ Template: {template.name}'))
        self.stdout.write(self.style.SUCCESS(f'✓ Code: {code}'))
        self.stdout.write(self.style.SUCCESS(f'✓ Version: {version.version}'))
        self.stdout.write(self.style.SUCCESS(f'✓ Sections: {len(schema_sections)}'))
        self.stdout.write(self.style.SUCCESS(f'✓ Fields: {total_fields}'))
        if service_code:
            self.stdout.write(self.style.SUCCESS(f'✓ Linked to: {service_code}'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write('')
        
        self.stdout.write('Next steps:')
        self.stdout.write('  1. Test in admin: https://rims.alshifalab.pk/admin/templates/template/')
        self.stdout.write(f'  2. View template: https://rims.alshifalab.pk/admin/templates/template/{template.id}/change/')
        if not service_code:
            self.stdout.write('  3. Link to service:')
            self.stdout.write(f'     python manage.py import_usg_template {json_file} --link-service=USG_XXX')
        else:
            self.stdout.write(f'  3. Test report entry for service: {service_code}')
        self.stdout.write('')
