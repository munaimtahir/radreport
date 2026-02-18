#!/usr/bin/env python
"""
Debug script to verify report publish flow.

This script helps verify:
1. User has verification group
2. Report can be verified
3. Report can be published
4. Publish snapshot is created correctly

Usage:
    python manage.py shell < debug_publish_flow.py
    OR
    python debug_publish_flow.py (if Django is in PYTHONPATH)
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rims_backend.settings')
django.setup()

from django.contrib.auth.models import User, Group
from apps.workflow.models import ServiceVisitItem
from apps.reporting.models import ReportInstanceV2, ReportPublishSnapshotV2

def check_user_groups(username):
    """Check if user has verification group"""
    try:
        user = User.objects.get(username=username)
        groups = [g.name for g in user.groups.all()]
        print(f"\n{'='*60}")
        print(f"User: {username}")
        print(f"Groups: {groups}")
        print(f"Is Superuser: {user.is_superuser}")
        
        # Check for verification group variations
        group_lower = [g.lower() for g in groups]
        has_verification = any(name in group_lower for name in ["verification", "verification_desk", "reporting_verifier"])
        print(f"Has Verification Permission: {has_verification or user.is_superuser}")
        print(f"{'='*60}\n")
        
        return user, has_verification or user.is_superuser
    except User.DoesNotExist:
        print(f"ERROR: User '{username}' not found")
        return None, False

def check_report_status(item_id):
    """Check report instance status"""
    try:
        item = ServiceVisitItem.objects.get(id=item_id)
        print(f"\n{'='*60}")
        print(f"ServiceVisitItem ID: {item_id}")
        print(f"Status: {item.status}")
        print(f"Department: {item.department_snapshot}")
        
        # Check for report instance
        if hasattr(item, 'report_instance_v2'):
            instance = item.report_instance_v2
            print(f"\nReportInstanceV2 ID: {instance.id}")
            print(f"Status: {instance.status}")
            print(f"Template: {instance.template_v2.code} - {instance.template_v2.name}")
            
            # Check for publish snapshots
            snapshots = instance.publish_snapshots_v2.all()
            print(f"\nPublish Snapshots: {snapshots.count()}")
            for snap in snapshots:
                print(f"  - Version {snap.version}: {snap.published_at} by {snap.published_by}")
                print(f"    PDF: {snap.pdf_file.name if snap.pdf_file else 'MISSING'}")
                print(f"    Hash: {snap.content_hash[:16]}...")
        else:
            print("\nWARNING: No ReportInstanceV2 found for this item")
        
        print(f"{'='*60}\n")
        return item
    except ServiceVisitItem.DoesNotExist:
        print(f"ERROR: ServiceVisitItem '{item_id}' not found")
        return None

def list_verified_reports():
    """List all verified reports that can be published"""
    instances = ReportInstanceV2.objects.filter(status="verified")
    print(f"\n{'='*60}")
    print(f"Verified Reports (can be published): {instances.count()}")
    for instance in instances:
        item = instance.work_item
        print(f"\n  Item: {item.id} - {item.service_name_snapshot}")
        print(f"  Status: {item.status}")
        print(f"  Report Status: {instance.status}")
        print(f"  Snapshots: {instance.publish_snapshots_v2.count()}")
    print(f"{'='*60}\n")

def list_published_snapshots():
    """List all publish snapshots"""
    snapshots = ReportPublishSnapshotV2.objects.all().order_by("-published_at")
    print(f"\n{'='*60}")
    print(f"Total Publish Snapshots: {snapshots.count()}")
    for snap in snapshots[:10]:  # Show last 10
        print(f"\n  Snapshot ID: {snap.id}")
        print(f"  Version: {snap.version}")
        print(f"  Published: {snap.published_at} by {snap.published_by}")
        print(f"  Instance: {snap.report_instance_v2.id}")
        print(f"  PDF: {snap.pdf_file.name if snap.pdf_file else 'MISSING'}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("REPORT PUBLISH FLOW DEBUG")
    print("="*60)
    
    # Check user groups
    username = input("\nEnter username to check (or press Enter to skip): ").strip()
    if username:
        check_user_groups(username)
    
    # List verified reports
    list_verified_reports()
    
    # List publish snapshots
    list_published_snapshots()
    
    # Check specific item
    item_id = input("\nEnter ServiceVisitItem ID to check (or press Enter to skip): ").strip()
    if item_id:
        check_report_status(item_id)
    
    print("\nDone!")
