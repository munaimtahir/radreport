#!/usr/bin/env python
"""
Data seeding script for RIMS (Updated)
Creates superuser, basic modalities, and calls app-specific seeders.
"""
import os
import sys
import django
from django.core.management import call_command

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rims_backend.settings")
django.setup()

from django.contrib.auth import get_user_model
from apps.catalog.models import Modality, Service

User = get_user_model()

def seed_data():
    print("=" * 60)
    print("RIMS Data Seeding")
    print("=" * 60)
    
    # Create or get superuser
    print("\n[1/3] Creating superuser...")
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
    print("\n[2/3] Creating modalities...")
    for code, name in [("USG", "Ultrasound"), ("XRAY", "X-Ray"), ("CT", "CT Scan"), ("MRI", "MRI")]:
        mod, created = Modality.objects.get_or_create(code=code, defaults={"name": name})
        print(f"✓ {'Created' if created else 'Exists'}: {code} - {name}")
    
    # Call app-specific seeders
    print("\n[3/3] Calling app seeders...")
    try:
        print("Running seed_reporting...")
        call_command('seed_reporting')
        print("✓ seed_reporting complete")
    except Exception as e:
        print(f"⚠ Error in seed_reporting: {e}")

    print("\n" + "=" * 60)
    print("✅ Data seeding completed!")
    print("=" * 60)
    print(f"\nLogin: admin / admin123")

if __name__ == "__main__":
    seed_data()
