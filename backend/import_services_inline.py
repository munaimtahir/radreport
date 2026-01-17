#!/usr/bin/env python
"""
Import ultrasound services with inline CSV data
This script will delete all existing services and import new ones
"""
import os
import sys
import django
import csv
import io

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rims_backend.settings")
django.setup()

from apps.catalog.models import Modality, Service
from apps.studies.models import OrderItem, Study
from apps.workflow.models import ServiceVisit, ServiceVisitItem
from apps.reporting.models import Report

# Inline CSV data
CSV_DATA = """service_code,name,department,billing_group,sub_category,price,currency,tat_min,unit,is_active
US001,Doppler Obstetric Single,Radiology,Ultrasound,Doppler,3000,PKR,30,service,1
US002,Doppler Obstetric Twins,Radiology,Ultrasound,Doppler,6000,PKR,45,service,1
US003,Doppler Obstetric Triplet,Radiology,Ultrasound,Doppler,9000,PKR,60,service,1
US004,Doppler Peripheral Veins Single Side,Radiology,Ultrasound,Doppler,3500,PKR,30,service,1
US005,Doppler Peripheral Veins Both Sides,Radiology,Ultrasound,Doppler,7500,PKR,45,service,1
US006,Doppler Renal,Radiology,Ultrasound,Doppler,3500,PKR,30,service,1
US007,Doppler Abdomen,Radiology,Ultrasound,Doppler,5000,PKR,30,service,1
US008,Ultrasound Abdomen,Radiology,Ultrasound,Gray Scale,1500,PKR,20,service,1
US009,Ultrasound Abdomen and Pelvis,Radiology,Ultrasound,Gray Scale,3000,PKR,30,service,1
US010,Ultrasound KUB,Radiology,Ultrasound,Gray Scale,1500,PKR,20,service,1
US011,Ultrasound Pelvis,Radiology,Ultrasound,Gray Scale,1500,PKR,20,service,1
US012,Ultrasound Soft Tissue,Radiology,Ultrasound,Gray Scale,2500,PKR,20,service,1
US013,Ultrasound Obstetrics (1st & 2nd Trimester),Radiology,Ultrasound,Gray Scale,2000,PKR,25,service,1
US014,Ultrasound for Swelling,Radiology,Ultrasound,Gray Scale,2500,PKR,20,service,1
US015,Doppler Thyroid,Radiology,Ultrasound,Doppler,3500,PKR,30,service,1
US016,Ultrasound Anomaly / Congenital Scan,Radiology,Ultrasound,Gray Scale,4000,PKR,45,service,1
US017,Ultrasound Breast (Single),Radiology,Ultrasound,Gray Scale,2500,PKR,20,service,1
US018,Ultrasound Chest,Radiology,Ultrasound,Gray Scale,2500,PKR,20,service,1
US019,Doppler Uterine Arteries,Radiology,Ultrasound,Doppler,3500,PKR,30,service,1
US020,Ultrasound Scrotum,Radiology,Ultrasound,Gray Scale,1500,PKR,20,service,1
US021,Doppler Peripheral Arteries Single Side,Radiology,Ultrasound,Doppler,3500,PKR,30,service,1
US022,Ultrasound Cranial,Radiology,Ultrasound,Gray Scale,2500,PKR,20,service,1
US023,Doppler Peripheral Arteries and Veins Both Sides,Radiology,Ultrasound,Doppler,7000,PKR,45,service,1
US024,Doppler Peripheral Arteries Both Sides,Radiology,Ultrasound,Doppler,7000,PKR,45,service,1
US025,Ultrasound Guided Abscess Drainage (Diagnostic),Radiology,Procedure,Ultrasound Guided,3000,PKR,30,service,1
US026,Ultrasound Guided Pleural Effusion Tap (Diagnostic),Radiology,Procedure,Ultrasound Guided,2500,PKR,30,service,1
US027,Ultrasound Guided Ascitic Fluid Tap (Diagnostic),Radiology,Procedure,Ultrasound Guided,3000,PKR,30,service,1
US028,Ultrasound Guided Abscess Drainage (Therapeutic),Radiology,Procedure,Ultrasound Guided,5000,PKR,45,service,1
US029,Ultrasound Guided Ascitic Fluid Tap (Therapeutic),Radiology,Procedure,Ultrasound Guided,5000,PKR,45,service,1
US030,Ultrasound Guided Pleural Effusion Tap (Therapeutic),Radiology,Procedure,Ultrasound Guided,5000,PKR,45,service,1
US031,Ultrasound Knee Joint,Radiology,Ultrasound,Gray Scale,2500,PKR,20,service,1
US032,Ultrasound Both Hip Joints (Child),Radiology,Ultrasound,Gray Scale,3000,PKR,25,service,1
US033,Doppler Scrotum,Radiology,Ultrasound,Doppler,3500,PKR,30,service,1
US034,Doppler Neck,Radiology,Ultrasound,Doppler,3500,PKR,30,service,1
US035,Ultrasound Breast (Bilateral),Radiology,Ultrasound,Gray Scale,5000,PKR,30,service,1
US036,Ultrasound Twin Obstetrics (Non-Doppler),Radiology,Ultrasound,Gray Scale,3000,PKR,30,service,1"""

def import_ultrasound_services():
    """Import services from inline CSV data"""
    print("=" * 60)
    print("Importing Ultrasound Services")
    print("=" * 60)
    
    # Step 1: Delete all existing services and related objects
    print("\n[1/3] Deleting all existing services and related data...")
    
    # Delete Reports first (they reference studies)
    reports_deleted = Report.objects.all().delete()[0]
    print(f"✓ Deleted {reports_deleted} reports")
    
    # Delete OrderItems (they reference services)
    order_items_deleted = OrderItem.objects.all().delete()[0]
    print(f"✓ Deleted {order_items_deleted} order items")
    
    # Delete Studies (they reference services)
    studies_deleted = Study.objects.all().delete()[0]
    print(f"✓ Deleted {studies_deleted} studies")
    
    # Delete ServiceVisitItems (they reference services)
    service_visit_items_deleted = ServiceVisitItem.objects.all().delete()[0]
    print(f"✓ Deleted {service_visit_items_deleted} service visit items")
    
    # Delete ServiceVisits
    service_visits_deleted = ServiceVisit.objects.all().delete()[0]
    print(f"✓ Deleted {service_visits_deleted} service visits")
    
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
    print("\n[3/3] Importing services from inline CSV...")
    created_count = 0
    errors = []
    
    csvfile = io.StringIO(CSV_DATA)
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
            if tat_min < 60:
                tat_value = 1  # Round up to 1 hour
                tat_unit = "hours"
            elif tat_min < 1440:  # Less than 24 hours
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
            print(f"✓ Created: {service_code} - {name} (Price: {price} PKR, TAT: {tat_min} min)")
            
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
    import_ultrasound_services()
