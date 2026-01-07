#!/usr/bin/env python
"""
Load production data: Templates and Services
This script loads previously configured templates and services into the deployed application.
"""
import os
import sys
import django
import csv
from pathlib import Path
from django.db import transaction

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rims_backend.settings")
django.setup()

from apps.catalog.models import Modality, Service
from apps.templates.models import Template, TemplateSection, TemplateField, FieldOption, TemplateVersion
from django.core.management import call_command


def _safe_bool(v, default=False):
    if v is None:
        return default
    if isinstance(v, bool):
        return v
    if isinstance(v, str):
        return v.strip().lower() in ("1", "true", "yes", "y", "on")
    return bool(v)


def build_schema(template: Template) -> dict:
    """Build a renderable schema snapshot for TemplateVersion."""
    schema = {
        "template_id": str(template.id),
        "name": template.name,
        "modality_code": template.modality_code,
        "sections": [],
    }

    for sec in template.sections.all().order_by("order", "id"):
        sec_obj = {
            "id": str(sec.id),
            "title": sec.title,
            "order": sec.order,
            "fields": [],
        }

        for f in sec.fields.all().order_by("order", "id"):
            field_obj = {
                "id": str(f.id),
                "label": f.label,
                "key": f.key,
                "type": f.field_type,
                "required": f.required,
                "help_text": f.help_text,
                "placeholder": f.placeholder,
                "unit": f.unit,
                "order": f.order,
                "options": [],
            }

            for o in f.options.all().order_by("order", "id"):
                field_obj["options"].append(
                    {"label": o.label, "value": o.value, "order": o.order}
                )

            sec_obj["fields"].append(field_obj)

        schema["sections"].append(sec_obj)

    return schema


def import_template_from_json(json_path):
    """Import template from JSON file"""
    print("\n" + "=" * 60)
    print("Importing Template from JSON")
    print("=" * 60)
    
    json_path = Path(json_path)
    if not json_path.exists():
        print(f"⚠ Template JSON not found: {json_path}")
        return None
    
    import json
    data = json.loads(json_path.read_text(encoding="utf-8"))
    
    name = (data.get("name") or "").strip()
    modality_code = (data.get("modality_code") or "").strip()
    is_active = _safe_bool(data.get("is_active", True), True)
    sections = data.get("sections") or []
    
    if not name:
        print("⚠ JSON must contain non-empty: name")
        return None
    
    template, created = Template.objects.get_or_create(
        name=name,
        modality_code=modality_code,
        defaults={"is_active": is_active},
    )
    
    if not created:
        template.is_active = is_active
        template.save(update_fields=["is_active"])
        # Delete existing sections for fresh import
        template.sections.all().delete()
        print(f"✓ Updating existing template: {template.name}")
    else:
        print(f"✓ Created new template: {template.name}")
    
    # Import sections / fields / options
    for sec in sections:
        sec_title = (sec.get("title") or "").strip()
        if not sec_title:
            continue
        
        sec_obj = TemplateSection.objects.create(
            template=template,
            title=sec_title,
            order=int(sec.get("order", 0)),
        )
        
        for f in sec.get("fields") or []:
            label = (f.get("label") or "").strip()
            key = (f.get("key") or "").strip()
            field_type = (f.get("field_type") or "").strip()
            
            if not (label and key and field_type):
                continue
            
            field = TemplateField.objects.create(
                section=sec_obj,
                label=label,
                key=key,
                field_type=field_type,
                required=_safe_bool(f.get("required", False)),
                help_text=f.get("help_text", "") or "",
                placeholder=f.get("placeholder", "") or "",
                unit=f.get("unit", "") or "",
                order=int(f.get("order", 0)),
            )
            
            for o in f.get("options") or []:
                FieldOption.objects.create(
                    field=field,
                    label=(o.get("label") or "").strip(),
                    value=(o.get("value") or "").strip(),
                    order=int(o.get("order", 0)),
                )
    
    # Publish new version
    latest = template.versions.order_by("-version").first()
    next_version = 1 if not latest else (latest.version + 1)
    
    TemplateVersion.objects.create(
        template=template,
        version=next_version,
        schema=build_schema(template),
        is_published=True,
    )
    print(f"✓ Published template version {next_version}")
    
    return template


def import_services_from_csv(csv_path, template=None):
    """Import services from CSV file (export format)"""
    print("\n" + "=" * 60)
    print("Importing Services from CSV")
    print("=" * 60)
    
    csv_path = Path(csv_path)
    if not csv_path.exists():
        print(f"⚠ CSV file not found: {csv_path}")
        return
    
    created_count = 0
    updated_count = 0
    errors = []
    modalities_cache = {}
    
    with open(csv_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        
        for row_num, row in enumerate(reader, start=2):
            try:
                # Skip empty rows
                if not row.get('service_code', '').strip():
                    continue
                
                service_code = row['service_code'].strip()
                name = row['name'].strip()
                modality_code = row.get('modality_code', 'USG').strip().upper()
                category = row.get('category', 'Radiology').strip()
                price = float(row['price'].strip())
                charges = float(row.get('charges', price))
                tat_minutes = int(row.get('tat_minutes', row.get('tat_min', 60)))
                tat_value = int(row.get('tat_value', 1))
                tat_unit = row.get('tat_unit', 'hours').strip().lower()
                is_active = _safe_bool(row.get('is_active', '1'), True)
                template_id = row.get('template_id', '').strip()
                
                # Get or create modality
                if modality_code not in modalities_cache:
                    mod, _ = Modality.objects.get_or_create(
                        code=modality_code,
                        defaults={"name": modality_code}
                    )
                    modalities_cache[modality_code] = mod
                modality = modalities_cache[modality_code]
                
                # Get or create service
                service, created = Service.objects.get_or_create(
                    code=service_code,
                    defaults={
                        "modality": modality,
                        "name": name,
                        "category": category,
                        "price": price,
                        "charges": charges,
                        "tat_value": tat_value,
                        "tat_unit": tat_unit,
                        "tat_minutes": tat_minutes,
                        "is_active": is_active,
                    }
                )
                
                if not created:
                    # Update existing service
                    service.modality = modality
                    service.name = name
                    service.category = category
                    service.price = price
                    service.charges = charges
                    service.tat_value = tat_value
                    service.tat_unit = tat_unit
                    service.tat_minutes = tat_minutes
                    service.is_active = is_active
                    service.save()
                    updated_count += 1
                    print(f"✓ Updated: {service_code} - {name}")
                else:
                    created_count += 1
                    print(f"✓ Created: {service_code} - {name}")
                
                # Link template if provided
                if template_id:
                    try:
                        template_obj = Template.objects.get(id=template_id)
                        service.default_template = template_obj
                        service.save(update_fields=["default_template"])
                        print(f"  → Linked template: {template_obj.name}")
                    except Template.DoesNotExist:
                        # If template_id doesn't exist, try linking to provided template
                        if template:
                            service.default_template = template
                            service.save(update_fields=["default_template"])
                            print(f"  → Linked provided template: {template.name}")
                elif template:
                    # Link to provided template if no template_id in CSV
                    service.default_template = template
                    service.save(update_fields=["default_template"])
                    print(f"  → Linked provided template: {template.name}")
                
            except Exception as e:
                error_msg = f"Row {row_num}: {str(e)}"
                errors.append(error_msg)
                print(f"✗ {error_msg}")
    
    print("\n" + "=" * 60)
    print("✅ Services import completed!")
    print("=" * 60)
    print(f"\nSummary:")
    print(f"  - Created: {created_count} services")
    print(f"  - Updated: {updated_count} services")
    if errors:
        print(f"  - Errors: {len(errors)}")
        for error in errors[:10]:  # Show first 10 errors
            print(f"    - {error}")
    print(f"\nTotal services in database: {Service.objects.count()}")


@transaction.atomic
def load_production_data():
    """Main function to load all production data"""
    print("=" * 60)
    print("RIMS Production Data Loader")
    print("=" * 60)
    
    backend_dir = Path(__file__).parent
    
    # Step 1: Import template from JSON
    template_json_path = backend_dir / "docs" / "presets" / "templates" / "abdomen_usg_v1.json"
    template = import_template_from_json(template_json_path)
    
    # Step 2: Import services from CSV
    csv_path = backend_dir / "service_master_export_20260107_143330.csv"
    import_services_from_csv(csv_path, template=template)
    
    # Step 3: Summary
    print("\n" + "=" * 60)
    print("✅ Production Data Loading Complete!")
    print("=" * 60)
    print(f"\nFinal Summary:")
    print(f"  - Modalities: {Modality.objects.count()}")
    print(f"  - Services: {Service.objects.count()}")
    print(f"  - Templates: {Template.objects.count()}")
    print(f"  - Template Versions: {TemplateVersion.objects.filter(is_published=True).count()}")
    print(f"  - Services with Templates: {Service.objects.exclude(default_template__isnull=True).count()}")


if __name__ == "__main__":
    load_production_data()
