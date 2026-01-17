import json
import os
from django.core.management.base import BaseCommand
from apps.usg.models import UsgTemplate


class Command(BaseCommand):
    help = "Load USG templates from JSON files into the database"

    def handle(self, *args, **options):
        templates_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "templates"
        )
        
        json_files = [
            f for f in os.listdir(templates_dir)
            if f.endswith('.json')
        ]
        
        if not json_files:
            self.stdout.write(
                self.style.WARNING(f"No JSON files found in {templates_dir}")
            )
            return
        
        for json_file in json_files:
            filepath = os.path.join(templates_dir, json_file)
            self.stdout.write(f"Loading template from {json_file}...")
            
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            code = data.get('code')
            version = data.get('version', 1)
            
            if not code:
                self.stdout.write(
                    self.style.ERROR(f"Template in {json_file} missing 'code' field")
                )
                continue
            
            # Check if template already exists
            existing = UsgTemplate.objects.filter(code=code, version=version).first()
            if existing:
                self.stdout.write(
                    self.style.WARNING(
                        f"Template {code} v{version} already exists. Skipping."
                    )
                )
                continue
            
            # Create new template
            template = UsgTemplate.objects.create(
                code=code,
                name=data.get('name', code),
                category=data.get('category', 'general'),
                version=version,
                is_locked=True,  # Lock by default
                schema_json=data
            )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"✓ Created template: {template.code} v{template.version}"
                )
            )
        
        self.stdout.write(self.style.SUCCESS("\nTemplate loading complete!"))
