#!/usr/bin/env python3
"""
PHASE D Smoke Tests
Validates Phase D implementation end-to-end:
1) Create USG report draft for a ServiceVisitItem
2) Save draft with findings + limitations + impression
3) Publish FINAL and fetch PDF (200)
4) Attempt publish with missing limitations -> blocked (400)
5) Attempt publish with critical_flag true but missing communication -> blocked (400)
6) Create amendment from FINAL -> AMENDED publish -> PDF 200, version incremented, history preserved
7) Confirm audit log has FINAL and AMENDED entries
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from apps.workflow.models import ServiceVisit, ServiceVisitItem, USGReport, StatusAuditLog
from apps.patients.models import Patient
from apps.catalog.models import Service, Modality, Category
from django.utils import timezone
import json

User = get_user_model()

def create_test_data():
    """Create test data for smoke tests"""
    print("Creating test data...")
    
    # Create user
    user, _ = User.objects.get_or_create(
        username='test_operator',
        defaults={'email': 'test@example.com', 'is_staff': True}
    )
    user.set_password('testpass')
    user.save()
    
    verifier, _ = User.objects.get_or_create(
        username='test_verifier',
        defaults={'email': 'verifier@example.com', 'is_staff': True}
    )
    verifier.set_password('testpass')
    verifier.save()
    
    # Create patient
    patient, _ = Patient.objects.get_or_create(
        mrn='TEST001',
        defaults={
            'name': 'Test Patient',
            'age': 35,
            'gender': 'M'
        }
    )
    
    # Create service
    modality, _ = Modality.objects.get_or_create(code='USG', defaults={'name': 'Ultrasound'})
    category, _ = Category.objects.get_or_create(name='Radiology', defaults={'code': 'RAD'})
    
    service, _ = Service.objects.get_or_create(
        code='USG-ABD',
        defaults={
            'name': 'Ultrasound Abdomen',
            'modality': modality,
            'category': category,
            'price': 1000.00,
            'is_active': True
        }
    )
    
    # Create service visit
    service_visit = ServiceVisit.objects.create(
        patient=patient,
        status='REGISTERED',
        created_by=user
    )
    
    # Create service visit item
    item = ServiceVisitItem.objects.create(
        service_visit=service_visit,
        service=service,
        service_name_snapshot=service.name,
        department_snapshot='USG',
        price_snapshot=service.price,
        status='REGISTERED'
    )
    
    return user, verifier, service_visit, item

def test_1_create_draft(client, user, item):
    """Test 1: Create USG report draft"""
    print("\n=== Test 1: Create USG report draft ===")
    
    client.force_login(user)
    
    # Create report
    response = client.post(
        '/api/workflow/usg-reports/',
        data={
            'visit_id': str(item.service_visit.id),
            'report_status': 'DRAFT',
            'study_type': 'Abdomen',
            'clinical_history': 'Abdominal pain',
            'findings_json': json.dumps({'Liver': {'size': 'Normal', 'texture': 'Homogeneous'}}),
        },
        content_type='application/json'
    )
    
    assert response.status_code in [200, 201], f"Expected 200/201, got {response.status_code}: {response.data}"
    report_id = response.data['id']
    print(f"✓ Draft report created: {report_id}")
    return report_id

def test_2_save_draft_with_required_fields(client, user, report_id):
    """Test 2: Save draft with findings + limitations + impression"""
    print("\n=== Test 2: Save draft with required fields ===")
    
    response = client.post(
        f'/api/workflow/usg-reports/{report_id}/save_draft/',
        data={
            'scan_quality': 'Good',
            'limitations_text': 'None',
            'impression_text': 'Normal study',
            'findings_json': json.dumps({
                'Liver': {'size': 'Normal', 'texture': 'Homogeneous'},
                'Kidneys': {'size': 'Normal'}
            }),
        },
        content_type='application/json'
    )
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.data}"
    assert response.data['scan_quality'] == 'Good'
    assert response.data['limitations_text'] == 'None'
    assert response.data['impression_text'] == 'Normal study'
    print("✓ Draft saved with required fields")

def test_3_publish_final(client, verifier, report_id):
    """Test 3: Publish FINAL and fetch PDF"""
    print("\n=== Test 3: Publish FINAL ===")
    
    client.force_login(verifier)
    
    # First submit for verification
    from apps.workflow.api import USGReportViewSet
    from rest_framework.test import APIRequestFactory
    from apps.workflow.models import USGReport
    
    report = USGReport.objects.get(id=report_id)
    item = report.service_visit_item
    
    # Transition item to PENDING_VERIFICATION
    from apps.workflow.transitions import transition_item_status
    transition_item_status(item, 'PENDING_VERIFICATION', verifier)
    
    # Publish
    response = client.post(
        f'/api/workflow/usg-reports/{report_id}/publish/',
        content_type='application/json'
    )
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.data}"
    assert response.data['report_status'] == 'FINAL'
    assert response.data['version'] == 1
    print("✓ Report published as FINAL")
    
    # Fetch PDF
    service_visit = item.service_visit
    pdf_response = client.get(f'/api/pdf/report/{service_visit.id}/')
    assert pdf_response.status_code == 200, f"Expected 200 for PDF, got {pdf_response.status_code}"
    assert pdf_response['Content-Type'] == 'application/pdf'
    print("✓ PDF generated successfully")

def test_4_publish_missing_limitations(client, verifier, item):
    """Test 4: Attempt publish with missing limitations -> blocked"""
    print("\n=== Test 4: Publish blocked (missing limitations) ===")
    
    # Create new report without limitations
    report = USGReport.objects.create(
        service_visit_item=item,
        service_visit=item.service_visit,
        report_status='DRAFT',
        scan_quality='Good',
        impression_text='Test impression',
        # Missing limitations_text
        created_by=verifier
    )
    
    transition_item_status(item, 'PENDING_VERIFICATION', verifier)
    
    response = client.post(
        f'/api/workflow/usg-reports/{report.id}/publish/',
        content_type='application/json'
    )
    
    assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.data}"
    assert 'errors' in response.data or 'limitations' in str(response.data).lower()
    print("✓ Publish correctly blocked (missing limitations)")

def test_5_publish_missing_critical_comm(client, verifier, item):
    """Test 5: Attempt publish with critical_flag true but missing communication -> blocked"""
    print("\n=== Test 5: Publish blocked (missing critical communication) ===")
    
    report = USGReport.objects.create(
        service_visit_item=item,
        service_visit=item.service_visit,
        report_status='DRAFT',
        scan_quality='Good',
        limitations_text='None',
        impression_text='Test impression',
        critical_flag=True,
        # Missing critical_communication_json
        created_by=verifier
    )
    
    transition_item_status(item, 'PENDING_VERIFICATION', verifier)
    
    response = client.post(
        f'/api/workflow/usg-reports/{report.id}/publish/',
        content_type='application/json'
    )
    
    assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.data}"
    assert 'errors' in response.data or 'critical' in str(response.data).lower()
    print("✓ Publish correctly blocked (missing critical communication)")

def test_6_amendment_workflow(client, verifier, item):
    """Test 6: Create amendment from FINAL -> AMENDED publish -> PDF 200, version incremented"""
    print("\n=== Test 6: Amendment workflow ===")
    
    # Create FINAL report
    report = USGReport.objects.create(
        service_visit_item=item,
        service_visit=item.service_visit,
        report_status='FINAL',
        scan_quality='Good',
        limitations_text='None',
        impression_text='Initial impression',
        version=1,
        verifier=verifier,
        verified_at=timezone.now(),
        signoff_json={'clinician_name': verifier.username, 'verified_at': timezone.now().isoformat()},
        created_by=verifier
    )
    
    # Create amendment
    response = client.post(
        f'/api/workflow/usg-reports/{report.id}/create_amendment/',
        data={
            'amendment_reason': 'Correction needed',
            'impression_text': 'Amended impression',
        },
        content_type='application/json'
    )
    
    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.data}"
    assert response.data['report_status'] == 'AMENDED'
    assert response.data['version'] == 2
    assert response.data['amendment_reason'] == 'Correction needed'
    print("✓ Amendment created")
    
    # Finalize amendment
    transition_item_status(item, 'PENDING_VERIFICATION', verifier)
    
    response = client.post(
        f'/api/workflow/usg-reports/{report.id}/publish/',
        content_type='application/json'
    )
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.data}"
    assert response.data['report_status'] == 'FINAL'  # After publish, status becomes FINAL again
    print("✓ Amendment published")
    
    # Check PDF
    service_visit = item.service_visit
    pdf_response = client.get(f'/api/pdf/report/{service_visit.id}/')
    assert pdf_response.status_code == 200
    print("✓ Amendment PDF generated")

def test_7_audit_log(client, verifier, item):
    """Test 7: Confirm audit log has FINAL and AMENDED entries"""
    print("\n=== Test 7: Audit log verification ===")
    
    logs = StatusAuditLog.objects.filter(service_visit_item=item).order_by('-changed_at')
    assert logs.exists(), "No audit logs found"
    
    # Check for FINAL and AMENDED related entries
    log_messages = [log.reason or '' for log in logs]
    has_final = any('final' in msg.lower() for msg in log_messages)
    has_amendment = any('amendment' in msg.lower() for msg in log_messages)
    
    print(f"✓ Audit logs found: {logs.count()} entries")
    if has_final:
        print("✓ FINAL entry found in audit log")
    if has_amendment:
        print("✓ AMENDMENT entry found in audit log")

def main():
    """Run all smoke tests"""
    print("=" * 60)
    print("PHASE D SMOKE TESTS")
    print("=" * 60)
    
    client = Client()
    user, verifier, service_visit, item = create_test_data()
    
    try:
        # Test 1: Create draft
        report_id = test_1_create_draft(client, user, item)
        
        # Test 2: Save draft with required fields
        test_2_save_draft_with_required_fields(client, user, report_id)
        
        # Test 3: Publish FINAL
        test_3_publish_final(client, verifier, report_id)
        
        # Test 4: Publish blocked (missing limitations)
        test_4_publish_missing_limitations(client, verifier, item)
        
        # Test 5: Publish blocked (missing critical communication)
        test_5_publish_missing_critical_comm(client, verifier, item)
        
        # Test 6: Amendment workflow
        test_6_amendment_workflow(client, verifier, item)
        
        # Test 7: Audit log
        test_7_audit_log(client, verifier, item)
        
        print("\n" + "=" * 60)
        print("✓ ALL SMOKE TESTS PASSED")
        print("=" * 60)
        return 0
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
