#!/usr/bin/env python
"""
Comprehensive Service Audit Script
Checks all service-level behaviors for production readiness
"""
import os
import sys
import django
from django.db.models import Count, Q, F

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rims_backend.settings")
django.setup()

from apps.catalog.models import Modality, Service
from apps.studies.models import Study, OrderItem
from apps.templates.models import Template

def audit_services():
    """Comprehensive service audit"""
    print("=" * 80)
    print("SERVICE INTEGRITY AUDIT")
    print("=" * 80)
    
    issues = []
    warnings = []
    
    # 1. Service Integrity Audit
    print("\n[1] Service Integrity Audit")
    print("-" * 80)
    
    total_services = Service.objects.count()
    active_services = Service.objects.filter(is_active=True).count()
    inactive_services = Service.objects.filter(is_active=False).count()
    
    print(f"✓ Total services: {total_services}")
    print(f"✓ Active services: {active_services}")
    print(f"✓ Inactive services: {inactive_services}")
    
    # Check for duplicates by code
    duplicate_codes = Service.objects.values('code').annotate(
        count=Count('id')
    ).filter(count__gt=1, code__isnull=False)
    
    if duplicate_codes.exists():
        issues.append("Duplicate service codes found")
        for dup in duplicate_codes:
            print(f"✗ Duplicate code: {dup['code']} ({dup['count']} services)")
    else:
        print("✓ No duplicate service codes")
    
    # Check for duplicates by name+modality (unique_together constraint)
    duplicate_names = Service.objects.values('modality', 'name').annotate(
        count=Count('id')
    ).filter(count__gt=1)
    
    if duplicate_names.exists():
        issues.append("Duplicate service names within same modality")
        for dup in duplicate_names:
            mod = Modality.objects.get(id=dup['modality'])
            print(f"✗ Duplicate: {mod.code} - {dup['name']} ({dup['count']} services)")
    else:
        print("✓ No duplicate service names")
    
    # Check for services without codes
    services_without_code = Service.objects.filter(code__isnull=True).count()
    if services_without_code > 0:
        warnings.append(f"{services_without_code} services without codes")
        print(f"⚠ {services_without_code} services without codes")
    else:
        print("✓ All services have codes")
    
    # 2. Department & Modality Binding
    print("\n[2] Department & Modality Binding")
    print("-" * 80)
    
    usg_modality = Modality.objects.filter(code="USG").first()
    if not usg_modality:
        issues.append("USG modality not found")
        print("✗ USG modality not found")
    else:
        print(f"✓ USG modality exists: {usg_modality.name}")
    
    radiology_services = Service.objects.filter(category="Radiology").count()
    usg_services = Service.objects.filter(modality__code="USG").count()
    
    print(f"✓ Radiology services: {radiology_services}")
    print(f"✓ USG modality services: {usg_services}")
    
    # Check for services with wrong category
    # Procedures should have category="Procedure", routine scans should have "Radiology"
    wrong_category = Service.objects.exclude(
        category__in=["Radiology", "Procedure"]
    ).count()
    if wrong_category > 0:
        issues.append(f"{wrong_category} services with invalid category")
        print(f"✗ {wrong_category} services with invalid category")
        for svc in Service.objects.exclude(category__in=["Radiology", "Procedure"]):
            print(f"  - {svc.code}: {svc.category}")
    else:
        radiology_count = Service.objects.filter(category="Radiology").count()
        procedure_count = Service.objects.filter(category="Procedure").count()
        print(f"✓ Category distribution: {radiology_count} Radiology, {procedure_count} Procedure")
    
    # Check for services with wrong modality
    wrong_modality = Service.objects.exclude(modality__code="USG").count()
    if wrong_modality > 0:
        issues.append(f"{wrong_modality} services with non-USG modality")
        print(f"✗ {wrong_modality} services with non-USG modality")
        for svc in Service.objects.exclude(modality__code="USG"):
            print(f"  - {svc.code}: {svc.modality.code}")
    else:
        print("✓ All services are USG modality")
    
    # 3. Billing Behavior
    print("\n[3] Billing Behavior")
    print("-" * 80)
    
    zero_price = Service.objects.filter(Q(price=0) | Q(charges=0)).count()
    if zero_price > 0:
        issues.append(f"{zero_price} services with zero price")
        print(f"✗ {zero_price} services with zero price")
        for svc in Service.objects.filter(Q(price=0) | Q(charges=0)):
            print(f"  - {svc.code}: price={svc.price}, charges={svc.charges}")
    else:
        print("✓ No services with zero price")
    
    # Check price/charges sync
    price_mismatch = Service.objects.exclude(price=F('charges')).count()
    if price_mismatch > 0:
        warnings.append(f"{price_mismatch} services with price/charges mismatch")
        print(f"⚠ {price_mismatch} services with price/charges mismatch")
    else:
        print("✓ All services have synced price/charges")
    
    # Check for negative prices
    negative_price = Service.objects.filter(Q(price__lt=0) | Q(charges__lt=0)).count()
    if negative_price > 0:
        issues.append(f"{negative_price} services with negative price")
        print(f"✗ {negative_price} services with negative price")
    else:
        print("✓ No services with negative price")
    
    # 4. Procedure vs Routine Scan Separation
    print("\n[4] Procedure vs Routine Scan Separation")
    print("-" * 80)
    
    procedure_services = Service.objects.filter(
        Q(category="Procedure") | Q(name__icontains="guided")
    ).count()
    
    routine_services = Service.objects.filter(
        category="Radiology",
        name__icontains="Ultrasound"
    ).exclude(name__icontains="guided").count()
    
    print(f"✓ Procedure services: {procedure_services}")
    print(f"✓ Routine scan services: {routine_services}")
    
    # Check procedure services are marked correctly
    guided_services = Service.objects.filter(name__icontains="guided")
    wrong_category_procedures = guided_services.exclude(category="Procedure")
    
    if wrong_category_procedures.exists():
        issues.append("Guided procedures not marked as Procedure category")
        print(f"✗ {wrong_category_procedures.count()} guided procedures not marked as Procedure")
        for svc in wrong_category_procedures:
            print(f"  - {svc.code}: {svc.name} (category: {svc.category})")
    else:
        print("✓ All guided procedures marked correctly")
    
    # 5. TAT Enforcement
    print("\n[5] TAT Enforcement")
    print("-" * 80)
    
    services_without_tat = Service.objects.filter(
        Q(tat_minutes=0) | Q(tat_minutes__isnull=True)
    ).count()
    
    if services_without_tat > 0:
        issues.append(f"{services_without_tat} services without TAT")
        print(f"✗ {services_without_tat} services without TAT")
    else:
        print("✓ All services have TAT")
    
    # Check TAT consistency
    tat_issues = []
    for svc in Service.objects.all():
        if svc.tat_unit == "hours":
            expected_minutes = svc.tat_value * 60
        elif svc.tat_unit == "days":
            expected_minutes = svc.tat_value * 24 * 60
        else:
            expected_minutes = svc.tat_minutes
        
        # Allow some tolerance (within 5 minutes)
        if abs(svc.tat_minutes - expected_minutes) > 5:
            tat_issues.append(svc)
    
    if tat_issues:
        warnings.append(f"{len(tat_issues)} services with TAT inconsistencies")
        print(f"⚠ {len(tat_issues)} services with TAT inconsistencies")
        for svc in tat_issues[:5]:  # Show first 5
            print(f"  - {svc.code}: tat_value={svc.tat_value}, tat_unit={svc.tat_unit}, tat_minutes={svc.tat_minutes}")
    else:
        print("✓ TAT values are consistent")
    
    # 6. Report Template Linking
    print("\n[6] Report Template Linking")
    print("-" * 80)
    
    services_without_template = Service.objects.filter(
        default_template__isnull=True
    ).count()
    
    if services_without_template > 0:
        warnings.append(f"{services_without_template} services without default templates")
        print(f"⚠ {services_without_template} services without default templates")
        
        # Check if templates exist for USG
        usg_templates = Template.objects.filter(modality_code="USG", is_active=True).count()
        if usg_templates == 0:
            issues.append("No USG templates found")
            print("✗ No USG templates found")
        else:
            print(f"✓ {usg_templates} USG templates available")
    else:
        print("✓ All services have default templates")
    
    # 7. Searchability Test
    print("\n[7] Searchability Test")
    print("-" * 80)
    
    # Test search by partial name
    test_searches = ["Doppler", "Abdomen", "Obstetric", "Breast", "Guided"]
    for search_term in test_searches:
        results = Service.objects.filter(
            Q(name__icontains=search_term) | Q(code__icontains=search_term)
        ).filter(is_active=True).count()
        print(f"✓ Search '{search_term}': {results} results")
    
    # 8. Summary
    print("\n" + "=" * 80)
    print("AUDIT SUMMARY")
    print("=" * 80)
    
    print(f"\nTotal Services: {total_services}")
    print(f"Active Services: {active_services}")
    print(f"Issues Found: {len(issues)}")
    print(f"Warnings: {len(warnings)}")
    
    if issues:
        print("\n❌ ISSUES:")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")
    
    if warnings:
        print("\n⚠ WARNINGS:")
        for i, warning in enumerate(warnings, 1):
            print(f"  {i}. {warning}")
    
    if not issues and not warnings:
        print("\n✅ All checks passed! Services are production-ready.")
    
    return len(issues) == 0

if __name__ == "__main__":
    success = audit_services()
    sys.exit(0 if success else 1)
