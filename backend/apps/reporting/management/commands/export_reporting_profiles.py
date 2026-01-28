import csv
import json
from django.core.management.base import BaseCommand, CommandError
from apps.reporting.models import ReportProfile

class Command(BaseCommand):
    help = 'Export reporting profile to CSV.'

    def add_arguments(self, parser):
        parser.add_argument('--profile', type=str, required=True, help='Profile Code')
        parser.add_argument('--out', type=str, required=True, help='Output CSV path')

    def handle(self, *args, **options):
        profile_code = options['profile']
        out_path = options['out']

        try:
            profile = ReportProfile.objects.get(code=profile_code)
        except ReportProfile.DoesNotExist:
            raise CommandError(f"Profile {profile_code} not found.")

        fieldnames = [
            'profile_code', 'profile_name', 'modality',
            'section', 'field_name', 'field_slug', 'field_type',
            'unit', 'normal_value', 'is_required', 'order',
            'options', 'sentence_template', 'narrative_role', 'omit_if_values_json', 'join_label'
        ]

        rows = []
        p_info = {
            'profile_code': profile.code,
            'profile_name': profile.name,
            'modality': profile.modality
        }

        # Check if using Links
        links = profile.library_links.select_related('library_item').order_by('order')
        
        if links.exists():
            self.stdout.write(f"Exporting from Library Links ({links.count()} items)...")
            for link in links:
                item = link.library_item
                # Options from library item
                options_str = ""
                if item.default_options_json:
                    opts = []
                    for o in item.default_options_json:
                         # label:value or just value if same
                         if o['label'] == o['value']:
                             opts.append(o['value'])
                         else:
                             opts.append(f"{o['label']}:{o['value']}")
                    options_str = "|".join(opts)

                row = p_info.copy()
                row.update({
                    'section': link.section,
                    'field_name': item.name,
                    'field_slug': item.slug,
                    'field_type': item.parameter_type,
                    'unit': item.unit,
                    'normal_value': item.default_normal_value,
                    'is_required': link.is_required,
                    'order': link.order,
                    'options': options_str,
                    'sentence_template': item.default_sentence_template,
                    'narrative_role': item.default_narrative_role,
                    'omit_if_values_json': json.dumps(item.default_omit_if_values) if item.default_omit_if_values else "",
                    'join_label': item.default_join_label
                })
                rows.append(row)
        else:
            # Export from ReportParameter
            params = profile.parameters.prefetch_related('options').order_by('order')
            self.stdout.write(f"Exporting from Parameters ({params.count()} items)...")
            for param in params:
                 # Options
                opts_objs = param.options.all().order_by('order')
                opts_str = ""
                if opts_objs.exists():
                    o_list = []
                    for o in opts_objs:
                        if o.label == o.value:
                            o_list.append(o.value)
                        else:
                            o_list.append(f"{o.label}:{o.value}")
                    opts_str = "|".join(o_list)
                
                row = p_info.copy()
                row.update({
                    'section': param.section,
                    'field_name': param.name,
                    'field_slug': param.slug or slugify(param.name).replace('-', '_'), # Fallback if slug missing
                    'field_type': param.parameter_type,
                    'unit': param.unit,
                    'normal_value': param.normal_value,
                    'is_required': param.is_required,
                    'order': param.order,
                    'options': opts_str,
                    'sentence_template': param.sentence_template,
                    'narrative_role': param.narrative_role,
                    'omit_if_values_json': json.dumps(param.omit_if_values) if param.omit_if_values else "",
                    'join_label': param.join_label
                })
                rows.append(row)

        with open(out_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        self.stdout.write(self.style.SUCCESS(f"Exported {len(rows)} rows to {out_path}"))
