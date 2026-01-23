#!/usr/bin/env python
"""
Data seeding script for RIMS
Creates modalities, services, patients, studies, and one finalized report
"""
import os
import sys
import django
from datetime import datetime, timedelta
from django.utils import timezone

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rims_backend.settings")
django.setup()

from django.contrib.auth import get_user_model
from apps.catalog.models import Modality, Service
from apps.patients.models import Patient
from apps.studies.models import Study
# from apps.templates.models import Template, TemplateSection, TemplateField, FieldOption, TemplateVersion
# from apps.reporting.models import Report
# from apps.reporting.pdf import build_basic_pdf

User = get_user_model()

def seed_data():
    print("=" * 60)
    print("RIMS Data Seeding")
    print("=" * 60)
    
    # Create or get superuser
    print("\n[1/7] Creating superuser...")
    user, created = User.objects.get_or_create(
        username="admin",
        defaults={
            "email": "admin@rims.local",
            "is_staff": True,
            "is_superuser": True,
        }
    )
    if created:
        user.set_password("admin123")
        user.save()
        print(f"✓ Created superuser: {user.username} / admin123")
    else:
        print(f"✓ Superuser exists: {user.username}")
    
    # Create Modalities
    print("\n[2/7] Creating modalities...")
    modalities = {}
    for code, name in [("USG", "Ultrasound"), ("XRAY", "X-Ray"), ("CT", "CT Scan"), ("MRI", "MRI")]:
        mod, created = Modality.objects.get_or_create(code=code, defaults={"name": name})
        modalities[code] = mod
        print(f"✓ {'Created' if created else 'Exists'}: {code} - {name}")
    
    # Create Services (SKIPPED - use import_services_inline.py or management command)
    print("\n[3/7] Services...")
    print("✓ Skipping service creation - use import tools to manage services")
    services = {}
    
    # Template creation logic removed (apps.templates deleted)
    print("✓ Skipping template creation (apps.templates deleted)")
    
    # latest_version = template.versions.filter(is_published=True).order_by("-version").first()
    
    # Link template to service
    # Skipped - no demo services created
    
    # Create Patients (SKIPPED - for demo only)
    print("\n[5/7] Patients...")
    print("✓ Skipping patient creation - demo data only")
    patients = []
    
    # Create Studies (SKIPPED - for demo only)
    print("\n[6/7] Studies...")
    print("✓ Skipping study creation - demo data only")
    studies = []
    
    # Create one finalized report (SKIPPED - for demo only)
    print("\n[7/7] Reports...")
    print("✓ Skipping report creation - demo data only")
    
    print("\n" + "=" * 60)
    print("✅ Data seeding completed!")
    print("=" * 60)
    print(f"\nSummary:")
    print(f"  - Modalities: {Modality.objects.count()}")
    print(f"  - Services: {Service.objects.count()}")
    print(f"  - Patients: {Patient.objects.count()}")
    print(f"  - Studies: {Study.objects.count()}")
    # print(f"  - Templates: {Template.objects.count()}")
    # print(f"  - Reports: {Report.objects.count()}")
    # print(f"  - Finalized Reports: {Report.objects.filter(status='final').count()}")
    print(f"\nLogin: admin / admin123")

if __name__ == "__main__":
    seed_data()

