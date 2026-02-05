import csv
import os
import json
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify
from apps.reporting.models import (
    ReportProfile, ReportParameter, ReportParameterOption,
    ReportParameterLibraryItem, ReportProfileParameterLink
)

class Command(BaseCommand):
    help = 'Import reporting profiles from CSV.'

    def add_arguments(self, parser):
        parser.add_argument('--file', type=str, required=True, help='Path to import file (CSV)')
        parser.add_argument('--mode', type=str, choices=['dry_run', 'apply'], required=True, help='Execution mode')
        parser.add_argument('--use-library', action='store_true', help='Use Parameter Library + Links strategy')

    def handle(self, *args, **options):
        file_path = options['file']
        mode = options['mode']
        use_library = options['use_library']

        if not os.path.exists(file_path):
            raise CommandError(f"File not found: {file_path}")

        if not file_path.endswith('.csv'):
             raise CommandError("Only CSV supported in this iteration.")

        with open(file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        self.stdout.write(f"Loaded {len(rows)} rows. Mode: {mode}")

        # Validation + Dry Run
        errors = []
        parsed_data = []

        param_slugs_by_profile = {}

        for idx, row in enumerate(rows, start=1):
            try:
                # Basic Validation
                required_cols = ['profile_code', 'profile_name', 'modality', 'field_slug', 'field_type']
                for col in required_cols:
                    if not row.get(col):
                        raise ValueError(f"Missing required column: {col}")

                # Type check
                p_type = row['field_type']
                valid_types = [t[0] for t in ReportParameter.PARAMETER_TYPES]
                if p_type not in valid_types:
                    raise ValueError(f"Invalid field_type: {p_type}. Must be one of {valid_types}")

                # Options check
                if p_type in ['dropdown', 'checklist'] and not row.get('options'):
                    raise ValueError(f"Options required for {p_type}")

                # JSON parsing
                omit_json = row.get('omit_if_values_json')
                if omit_json:
                    try:
                        json.loads(omit_json)
                    except json.JSONDecodeError:
                        raise ValueError("Invalid JSON in omit_if_values_json")
                
                # Unique slug check (in-memory)
                p_code = row['profile_code']
                slug = row['field_slug']
                key = (p_code, slug)
                if key in param_slugs_by_profile:
                     raise ValueError(f"Duplicate slug '{slug}' for profile '{p_code}' in file")
                param_slugs_by_profile[key] = True

                parsed_data.append(row)

            except Exception as e:
                errors.append(f"Row {idx}: {str(e)}")

        if errors:
            self.stdout.write(self.style.ERROR("Validation Errors:"))
            for e in errors:
                self.stdout.write(e)
            raise CommandError("Aborting due to validation errors.")

        if mode == 'dry_run':
            self.stdout.write(self.style.SUCCESS(f"Validation successful. {len(parsed_data)} valid rows ready to import."))
            return

        # APPLY
        self.apply_import(parsed_data, use_library)

    def apply_import(self, rows, use_library):
        profiles_map = {} # code -> profile_obj
        
        with transaction.atomic():
            for row in rows:
                p_code = row['profile_code']
                
                # 1. Upsert Profile
                if p_code not in profiles_map:
                    profile, created = ReportProfile.objects.update_or_create(
                        code=p_code,
                        defaults={
                            'name': row['profile_name'],
                            'modality': row['modality'],
                            'narrative_mode': 'rule_based'
                        }
                    )
                    profiles_map[p_code] = profile
                    if created:
                        self.stdout.write(f"Created profile {p_code}")
                
                profile = profiles_map[p_code]

                # 2. Extract Fields
                field_data = {
                    'section': row['section'],
                    'name': row['field_name'],
                    'parameter_type': row['field_type'],
                    'unit': row.get('unit') or None,
                    'normal_value': row.get('normal_value') or None,
                    'order': int(row['order']) if row['order'] else 0,
                    'is_required': str(row.get('is_required', '')).lower() in ('true', '1', 'yes'),
                    'sentence_template': row.get('sentence_template') or None,
                    'narrative_role': row.get('narrative_role') or 'finding',
                    'omit_if_values': json.loads(row['omit_if_values_json']) if row.get('omit_if_values_json') else None,
                    'join_label': row.get('join_label') or None,
                }
                
                slug = row['field_slug']

                # Options parsing
                options_raw = row.get('options', '')
                options_list = []
                if options_raw:
                    for opt in options_raw.split('|'):
                         # Handle label:value or just value
                         if ':' in opt:
                             lbl, val = opt.split(':', 1)
                             options_list.append({'label': lbl.strip(), 'value': val.strip()})
                         else:
                             options_list.append({'label': opt.strip(), 'value': opt.strip()})

                if use_library:
                    # Library Strategy
                    # 1. Upsert Library Item
                    lib_item, created = ReportParameterLibraryItem.objects.update_or_create(
                        slug=slug,
                        modality=row['modality'], 
                        defaults={
                            'name': field_data['name'],
                            'parameter_type': field_data['parameter_type'],
                            'unit': field_data['unit'],
                            'default_normal_value': field_data['normal_value'],
                            'default_sentence_template': field_data['sentence_template'],
                            'default_omit_if_values': field_data['omit_if_values'],
                            'default_join_label': field_data['join_label'],
                            'default_narrative_role': field_data['narrative_role'],
                            'default_options_json': options_list if options_list else None
                        }
                    )
                    
                    # 2. Upsert Link
                    link, created = ReportProfileParameterLink.objects.update_or_create(
                        profile=profile,
                        library_item=lib_item,
                        defaults={
                            'section': field_data['section'],
                            'order': field_data['order'],
                            'is_required': field_data['is_required'],
                            'overrides_json': {} 
                        }
                    )
                    
                else:
                    # Standard ReportParameter Strategy (Legacy/Hybrid)
                    # We utilize 'slug' now to identify parameters.
                    
                    param, created = ReportParameter.objects.update_or_create(
                        profile=profile,
                        slug=slug, 
                        defaults={
                            'name': field_data['name'],
                            'section': field_data['section'],
                            'parameter_type': field_data['parameter_type'],
                            'unit': field_data['unit'],
                            'normal_value': field_data['normal_value'],
                            'order': field_data['order'],
                            'is_required': field_data['is_required'],
                            'sentence_template': field_data['sentence_template'],
                            'narrative_role': field_data['narrative_role'],
                            'omit_if_values': field_data['omit_if_values'],
                            'join_label': field_data['join_label'],
                        }
                    )
                    
                    # Determine options
                    if options_list:
                        # Rebuild options
                        param.options.all().delete()
                        for i, opt in enumerate(options_list):
                            ReportParameterOption.objects.create(
                                parameter=param,
                                label=opt['label'],
                                value=opt['value'],
                                order=i
                            )
            
            self.stdout.write(self.style.SUCCESS("Import completed successfully."))
