#!/usr/bin/env python
"""
Verification script for USG template resolution.
Tests all possible failure points in the backend.

Usage:
    python backend/verify_usg_template_resolution.py
"""
import os
import sys
import django

# Setup Django environment
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rims_backend.settings')
django.setup()

from apps.workflow.models import USGReport
from apps.workflow.template_resolution import resolve_template_schema_for_report, ensure_template_for_report
from apps.catalog.models import Service as CatalogService
from apps.templates.models import Template, TemplateVersion
from rest_framework.exceptions import ValidationError


def test_template_resolution():
    """Test template resolution for existing USG reports"""
    print("=" * 80)
    print("PHASE 5: Backend Template Resolution Verification")
    print("=" * 80)
    print()
    
    # Test 1: Check if any reports exist
    total_reports = USGReport.objects.count()
    print(f"📊 Total USG Reports: {total_reports}")
    
    if total_reports == 0:
        print("⚠️  No USG reports found. Create a test report first.")
        return
    
    # Test 2: Check reports with/without template_version
    reports_with_template = USGReport.objects.filter(template_version__isnull=False).count()
    reports_without_template = USGReport.objects.filter(template_version__isnull=True).count()
    
    print(f"✅ Reports WITH template_version: {reports_with_template}")
    print(f"❌ Reports WITHOUT template_version: {reports_without_template}")
    print()
    
    # Test 3: Pick first report and verify resolution
    print("-" * 80)
    print("Testing template resolution for first report:")
    print("-" * 80)
    
    report = USGReport.objects.first()
    print(f"Report ID: {report.id}")
    print(f"Report Status: {report.report_status}")
    print(f"Template Version: {report.template_version}")
    
    # Get service
    service = None
    if report.service_visit_item and report.service_visit_item.service:
        service = report.service_visit_item.service
    elif report.service_visit and report.service_visit.service:
        service = report.service_visit.service
    
    if service:
        print(f"Service Code: {service.code}")
        print(f"Service Default Template: {service.default_template}")
        
        if service.default_template:
            template = service.default_template
            published_versions = template.versions.filter(is_published=True).order_by("-version")
            print(f"Template Name: {template.name}")
            print(f"Published Versions: {published_versions.count()}")
            
            if published_versions.exists():
                latest = published_versions.first()
                print(f"Latest Version: {latest.version}")
                print(f"Schema exists: {bool(latest.schema)}")
                print(f"Schema sections: {len(latest.schema.get('sections', [])) if latest.schema else 0}")
    else:
        print("❌ No service association found!")
    
    print()
    
    # Test 4: Try to resolve schema
    print("-" * 80)
    print("Attempting to resolve template schema:")
    print("-" * 80)
    
    try:
        schema = resolve_template_schema_for_report(report)
        sections = schema.get('sections', [])
        print(f"✅ SUCCESS: Schema resolved")
        print(f"   Sections count: {len(sections)}")
        if sections:
            print(f"   First section: {sections[0].get('title', 'N/A')}")
            fields = sections[0].get('fields', [])
            print(f"   First section fields: {len(fields)}")
            if fields:
                print(f"   Sample field: {fields[0].get('label', 'N/A')} (type: {fields[0].get('type', 'N/A')})")
    except ValidationError as e:
        print(f"❌ FAILED: {str(e)}")
    except Exception as e:
        print(f"❌ ERROR: {type(e).__name__}: {str(e)}")
    
    print()
    
    # Test 5: Check all USG services have templates configured
    print("-" * 80)
    print("Checking USG services configuration:")
    print("-" * 80)
    
    usg_services = CatalogService.objects.filter(
        category="Radiology",
        modality__code="USG",
        is_active=True
    )
    
    print(f"Active USG Services: {usg_services.count()}")
    
    for svc in usg_services:
        has_template = "✅" if svc.default_template else "❌"
        template_name = svc.default_template.name if svc.default_template else "NONE"
        print(f"{has_template} {svc.code:30s} | Template: {template_name}")
    
    print()
    
    # Test 6: Verify publish/finalize will work
    print("-" * 80)
    print("Testing ensure_template_for_report (used by publish/finalize):")
    print("-" * 80)
    
    # Get a DRAFT report
    draft_report = USGReport.objects.filter(report_status="DRAFT").first()
    
    if draft_report:
        print(f"Testing with draft report: {draft_report.id}")
        print(f"Current template_version: {draft_report.template_version}")
        
        try:
            template_version = ensure_template_for_report(draft_report)
            print(f"✅ SUCCESS: Template ensured")
            print(f"   Template Version: {template_version.version}")
            print(f"   Template Name: {template_version.template.name}")
        except ValidationError as e:
            print(f"❌ FAILED: {str(e)}")
            print("   This report would fail on publish/finalize!")
        except Exception as e:
            print(f"❌ ERROR: {type(e).__name__}: {str(e)}")
    else:
        print("ℹ️  No DRAFT reports found to test")
    
    print()
    print("=" * 80)
    print("Verification Complete")
    print("=" * 80)


def test_specific_report(report_id):
    """Test a specific report by ID"""
    try:
        report = USGReport.objects.get(id=report_id)
        print(f"Testing report: {report_id}")
        print(f"Status: {report.report_status}")
        
        schema = resolve_template_schema_for_report(report)
        print(f"✅ Schema resolved with {len(schema.get('sections', []))} sections")
        
    except USGReport.DoesNotExist:
        print(f"❌ Report {report_id} not found")
    except ValidationError as e:
        print(f"❌ Validation Error: {str(e)}")
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {str(e)}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Test specific report ID
        report_id = sys.argv[1]
        test_specific_report(report_id)
    else:
        # Run full verification
        test_template_resolution()
