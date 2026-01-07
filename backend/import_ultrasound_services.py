#!/usr/bin/env python
"""
Import ultrasound services from CSV file
This script will delete all existing services and import new ones from the CSV
"""
import os
import sys
import django
import csv

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rims_backend.settings")
django.setup()

from apps.catalog.models import Modality, Service
from apps.studies.models import OrderItem, Study

def import_ultrasound_services(csv_path):
    """Import services from the ultrasound CSV file"""
    print("=" * 60)
    print("Importing Ultrasound Services")
    print("=" * 60)
    
    # Step 1: Delete all existing services and related objects
    print("\n[1/3] Deleting all existing services and related data...")
    
    # Delete OrderItems first (they reference services)
    order_items_deleted = OrderItem.objects.all().delete()[0]
    print(f"✓ Deleted {order_items_deleted} order items")
    
    # Delete Studies next (they also reference services)
    studies_deleted = Study.objects.all().delete()[0]
    print(f"✓ Deleted {studies_deleted} studies")
    
    # Now delete services
    deleted_count = Service.objects.all().delete()[0]
    print(f"✓ Deleted {deleted_count} existing services")
    
    # Step 2: Ensure USG modality exists
    print("\n[2/3] Ensuring USG modality exists...")
    modality, created = Modality.objects.get_or_create(
        code="USG",
        defaults={"name": "Ultrasound"}
    )
    print(f"✓ {'Created' if created else 'Exists'}: {modality.code} - {modality.name}")
    
    # Step 3: Import services from CSV
    print("\n[3/3] Importing services from CSV...")
    created_count = 0
    errors = []
    
    with open(csv_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        
        for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
            try:
                # Skip empty rows
                if not row.get('service_code', '').strip():
                    continue
                
                service_code = row['service_code'].strip()
                name = row['name'].strip()
                department = row['department'].strip()
                billing_group = row.get('billing_group', '').strip()
                sub_category = row.get('sub_category', '').strip()
                price = float(row['price'].strip())
                currency = row.get('currency', 'PKR').strip()
                tat_min = int(row['tat_min'].strip())
                unit = row.get('unit', 'service').strip()
                is_active = int(row.get('is_active', '1').strip()) == 1
                
                # Calculate tat_value and tat_unit from tat_minutes
                # Round to nearest hour for tat_value (since it's an integer)
                if tat_min < 60:
                    tat_value = 1  # Round up to 1 hour
                    tat_unit = "hours"
                elif tat_min < 1440:  # Less than 24 hours
                    # Round to nearest hour
                    tat_value = round(tat_min / 60) if tat_min % 60 >= 30 else tat_min // 60
                    if tat_value == 0:
                        tat_value = 1
                    tat_unit = "hours"
                else:
                    tat_value = round(tat_min / 1440) if tat_min % 1440 >= 720 else tat_min // 1440
                    if tat_value == 0:
                        tat_value = 1
                    tat_unit = "days"
                
                # Create service with approximate tat_value/tat_unit
                # The save() method will recalculate tat_minutes, so we'll override it after
                service = Service.objects.create(
                    code=service_code,
                    modality=modality,
                    name=name,
                    category=department,
                    price=price,
                    charges=price,
                    tat_value=tat_value,
                    tat_unit=tat_unit,
                    is_active=is_active,
                )
                
                # Override tat_minutes with exact value from CSV (bypassing save() recalculation)
                Service.objects.filter(id=service.id).update(tat_minutes=tat_min)
                
                created_count += 1
                print(f"✓ Created: {service_code} - {name} (TAT: {tat_min} min)")
                
            except Exception as e:
                error_msg = f"Row {row_num}: {str(e)}"
                errors.append(error_msg)
                print(f"✗ {error_msg}")
    
    print("\n" + "=" * 60)
    print("✅ Import completed!")
    print("=" * 60)
    print(f"\nSummary:")
    print(f"  - Deleted: {deleted_count} services")
    print(f"  - Created: {created_count} services")
    if errors:
        print(f"  - Errors: {len(errors)}")
        for error in errors:
            print(f"    - {error}")
    print(f"\nTotal services in database: {Service.objects.count()}")

if __name__ == "__main__":
    csv_path = "/home/munaim/Downloads/rims_services_ultrasound_import.csv"
    
    if not os.path.exists(csv_path):
        print(f"Error: CSV file not found at {csv_path}")
        sys.exit(1)
    
    import_ultrasound_services(csv_path)
