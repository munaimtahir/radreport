
import os
import sys
import django
from django.conf import settings
# Setup Django environment
sys.path.append('/home/munaim/srv/apps/radreport/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rims_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from apps.workflow.models import ServiceVisit, ServiceVisitItem, USGReport
from apps.workflow.transitions import transition_item_status
from apps.workflow.api import USGReportViewSet
from apps.catalog.models import Service, Modality
from apps.patients.models import Patient
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status as status_code

def verify_fix():
    print("Verifying fix for workflow status transition...")
    
    # Setup Data
    User = get_user_model()
    admin_user, _ = User.objects.get_or_create(username='admin_fix_test')
    if not admin_user.is_superuser:
        admin_user.is_superuser = True
        admin_user.save()
        
    # Ensure Modality and Service
    modality, _ = Modality.objects.get_or_create(code="USG", defaults={"name": "Ultrasound"})
    service, _ = Service.objects.get_or_create(
        code="USG-TEST",
        defaults={
            "name": "USG Test Service",
            "modality": modality,
            "category": "Radiology",
            "price": 100
        }
    )
    
    patient, _ = Patient.objects.get_or_create(name="Test Patient", defaults={"gender": "M"})
    
    # Create Visit and Item
    visit = ServiceVisit.objects.create(patient=patient)
    item = ServiceVisitItem.objects.create(
        service_visit=visit,
        service=service,
        department_snapshot="USG",
        status="IN_PROGRESS"
    )
    visit.status = "IN_PROGRESS"
    visit.save()
    
    # Verify initial state
    print(f"Initial Visit Status: {visit.status}")
    print(f"Initial Item Status: {item.status}")
    
    # Step 1: Simulate submit_for_verification which calls transition_item_status
    # We will simulate the transition call exactly as the API does
    
    print("\nExecuting transition_item_status to PENDING_VERIFICATION...")
    
    try:
        # Pass the item object. Note: logic in transition_item_status uses item.service_visit
        # Our fix ensures that even if item refers to a stale visit, it refreshes it.
        
        # To simulate stale object, let's artificially ensure 'item' has a 'service_visit' loaded
        # that doesn't know about updates if we were to modify DB directly (though here we don't)
        # Actually, let's just run the transition and check the DB result for visit status
        
        transition_item_status(item, "PENDING_VERIFICATION", admin_user)
        
        # Reload visit from DB to check persistence
        visit.refresh_from_db()
        item.refresh_from_db()
        
        print(f"Final Item Status: {item.status}")
        print(f"Final Visit Status: {visit.status}")
        
        if visit.status == "PENDING_VERIFICATION":
            print("SUCCESS: Visit status correctly updated to PENDING_VERIFICATION.")
        else:
            print(f"FAILURE: Visit status is {visit.status}, expected PENDING_VERIFICATION.")
            exit(1)
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

    print("\nSimulating full API flow for submit_for_verification...")
    
    # Create report linked to item
    report = USGReport.objects.create(
        service_visit_item=item,
        service_visit=visit,
        report_status="DRAFT"
    )
    
    # Reset status
    item.status = "IN_PROGRESS"
    item.save()
    visit.status = "IN_PROGRESS"
    visit.save()
    
    # API Request
    factory = APIRequestFactory()
    request = factory.post(f'/workflow/usg/{report.id}/submit_for_verification/', {}, format='json')
    force_authenticate(request, user=admin_user)
    
    view = USGReportViewSet.as_view({'post': 'submit_for_verification'})
    response = view(request, pk=str(report.id))
    
    print(f"API Response Code: {response.status_code}")
    if response.status_code not in [200, 201]:
        print(f"API Error: {response.data}")
    
    visit.refresh_from_db()
    print(f"API Flow Visit Status: {visit.status}")
    
    if visit.status == "PENDING_VERIFICATION":
        print("SUCCESS: API flow correctly updated Visit Status.")
    else:
        print(f"FAILURE: API flow Visit Status is {visit.status}")
        exit(1)

if __name__ == "__main__":
    verify_fix()
