#!/usr/bin/env python
"""
Fix Service Issues
Fixes all identified issues from the audit
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rims_backend.settings")
django.setup()

from django.db import transaction
from apps.catalog.models import Service
from apps.templates.models import Template

def fix_services():
    """Fix all service issues"""
    print("=" * 80)
    print("FIXING SERVICE ISSUES")
    print("=" * 80)
    
    # 1. Fix guided procedures category
    print("\n[1] Fixing guided procedures category...")
    guided_services = Service.objects.filter(name__icontains="guided")
    fixed_count = 0
    
    for svc in guided_services:
        if svc.category != "Procedure":
            old_category = svc.category
            svc.category = "Procedure"
            svc.save()
            print(f"✓ Fixed {svc.code}: {old_category} → Procedure")
            fixed_count += 1
    
    print(f"✓ Fixed {fixed_count} guided procedures")
    
    # 2. Fix TAT inconsistencies
    print("\n[2] Fixing TAT inconsistencies...")
    # The TAT inconsistencies are expected because we're storing exact minutes
    # but the model calculates from tat_value/tat_unit. We'll update tat_value/tat_unit
    # to match the actual tat_minutes.
    
    fixed_tat_count = 0
    for svc in Service.objects.all():
        # Calculate proper tat_value and tat_unit from tat_minutes
        if svc.tat_minutes < 60:
            # Less than 1 hour - round to nearest hour (minimum 1)
            svc.tat_value = 1
            svc.tat_unit = "hours"
            # Keep tat_minutes as is (we'll override after save)
            svc.save()
            Service.objects.filter(id=svc.id).update(tat_minutes=svc.tat_minutes)
            fixed_tat_count += 1
        elif svc.tat_minutes < 1440:  # Less than 24 hours
            # Round to nearest hour
            hours = round(svc.tat_minutes / 60)
            if hours == 0:
                hours = 1
            svc.tat_value = hours
            svc.tat_unit = "hours"
            svc.save()
            Service.objects.filter(id=svc.id).update(tat_minutes=svc.tat_minutes)
            fixed_tat_count += 1
        else:
            # Days
            days = round(svc.tat_minutes / 1440)
            if days == 0:
                days = 1
            svc.tat_value = days
            svc.tat_unit = "days"
            svc.save()
            Service.objects.filter(id=svc.id).update(tat_minutes=svc.tat_minutes)
            fixed_tat_count += 1
    
    print(f"✓ Fixed TAT for {fixed_tat_count} services")
    
    # 3. Link default templates
    print("\n[3] Linking default templates...")
    usg_template = Template.objects.filter(modality_code="USG", is_active=True).first()
    
    if usg_template:
        linked_count = Service.objects.filter(
            default_template__isnull=True
        ).update(default_template=usg_template)
        print(f"✓ Linked {linked_count} services to default USG template")
    else:
        print("⚠ No USG template found - skipping template linking")
    
    print("\n" + "=" * 80)
    print("✅ All fixes completed!")
    print("=" * 80)

if __name__ == "__main__":
    with transaction.atomic():
        fix_services()
