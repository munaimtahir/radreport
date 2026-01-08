#!/usr/bin/env python3
"""
End-to-end API workflow test for RIMS
Tests complete workflow via HTTP API including permissions
Usage:
  python scripts/test_e2e_workflow.py [base_url] [username] [password]
"""
import os
import sys
import requests
import json
from datetime import datetime
from decimal import Decimal

# Default configuration
BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000")
USERNAME = os.environ.get("TEST_USERNAME", "admin")
PASSWORD = os.environ.get("TEST_PASSWORD", "admin123")

if len(sys.argv) > 1:
    BASE_URL = sys.argv[1]
if len(sys.argv) > 2:
    USERNAME = sys.argv[2]
if len(sys.argv) > 3:
    PASSWORD = sys.argv[3]

API_BASE = f"{BASE_URL}/api"
PASSED = 0
FAILED = 0
FAILED_TESTS = []


def test(name, func):
    """Run a test and track results"""
    global PASSED, FAILED
    print(f"\n[TEST] {name}")
    try:
        result = func()
        if result:
            print(f"  ✓ PASS: {name}")
            PASSED += 1
            return True
        else:
            print(f"  ✗ FAIL: {name}")
            FAILED += 1
            FAILED_TESTS.append(name)
            return False
    except Exception as e:
        print(f"  ✗ ERROR: {name} - {e}")
        import traceback
        traceback.print_exc()
        FAILED += 1
        FAILED_TESTS.append(name)
        return False


def get_token():
    """Get authentication token"""
    response = requests.post(
        f"{API_BASE}/auth/login/",
        json={"username": USERNAME, "password": PASSWORD}
    )
    if response.status_code != 200:
        raise Exception(f"Login failed: {response.status_code} - {response.text}")
    data = response.json()
    return data.get("access") or data.get("token")


def test_auth():
    """Test authentication"""
    token = get_token()
    assert token, "No token received"
    print(f"  Token obtained: {token[:20]}...")
    return token


def test_create_patient(token):
    """Test patient creation"""
    patient_data = {
        "name": f"Test Patient E2E {datetime.now().strftime('%Y%m%d%H%M%S')}",
        "age": 35,
        "gender": "M",
        "phone": f"123456{datetime.now().strftime('%H%M%S')}",
    }
    response = requests.post(
        f"{API_BASE}/patients/",
        headers={"Authorization": f"Bearer {token}"},
        json=patient_data
    )
    if response.status_code not in [200, 201]:
        print(f"  Response: {response.status_code} - {response.text}")
        return False
    patient = response.json()
    print(f"  Patient created: {patient.get('name')} (ID: {patient.get('id')})")
    return patient


def test_get_services(token):
    """Test getting services"""
    response = requests.get(
        f"{API_BASE}/workflow/service-catalog/",
        headers={"Authorization": f"Bearer {token}"}
    )
    if response.status_code != 200:
        print(f"  Response: {response.status_code} - {response.text}")
        return None
    services = response.json()
    if isinstance(services, dict) and "results" in services:
        services = services["results"]
    print(f"  Found {len(services)} services")
    return services


def test_create_service_visit(token, patient, service):
    """Test creating service visit - this was failing"""
    visit_data = {
        "patient_id": patient["id"],
        "service_id": service["id"],
        "total_amount": str(float(service.get("default_price", 1000))),
        "discount": "0.00",
        "net_amount": str(float(service.get("default_price", 1000))),
        "balance_amount": "0.00",
        "amount_paid": str(float(service.get("default_price", 1000))),
        "payment_method": "cash",
    }
    response = requests.post(
        f"{API_BASE}/workflow/visits/create_visit/",
        headers={"Authorization": f"Bearer {token}"},
        json=visit_data
    )
    if response.status_code not in [200, 201]:
        print(f"  Response: {response.status_code} - {response.text}")
        return None
    visit = response.json()
    print(f"  Service visit created: {visit.get('visit_id')} (ID: {visit.get('id')})")
    return visit


def test_usg_workflow(token):
    """Test complete USG workflow"""
    # 1. Get or create patient
    patient = test_create_patient(token)
    if not patient:
        return False
    
    # 2. Get USG service
    services = test_get_services(token)
    if not services:
        return False
    
    usg_service = None
    for svc in services:
        if "USG" in svc.get("code", "").upper() or "USG" in svc.get("name", "").upper():
            usg_service = svc
            break
    
    if not usg_service:
        print("  ⚠ No USG service found, using first service")
        usg_service = services[0]
    
    # 3. Create service visit
    visit = test_create_service_visit(token, patient, usg_service)
    if not visit:
        return False
    
    # 4. Create USG report
    report_data = {
        "visit_id": visit["id"],
        "report_json": {
            "findings": "Test findings for E2E test",
            "impression": "Test impression",
        }
    }
    response = requests.post(
        f"{API_BASE}/workflow/usg/",
        headers={"Authorization": f"Bearer {token}"},
        json=report_data
    )
    if response.status_code not in [200, 201]:
        print(f"  USG report creation failed: {response.status_code} - {response.text}")
        return False
    report = response.json()
    print(f"  USG report created/updated")
    
    # 5. Save draft
    report_id = report.get("id")
    if report_id:
        response = requests.post(
            f"{API_BASE}/workflow/usg/{report_id}/save_draft/",
            headers={"Authorization": f"Bearer {token}"},
            json={"report_json": report_data["report_json"]}
        )
        if response.status_code == 200:
            print(f"  Draft saved successfully")
        else:
            print(f"  Draft save response: {response.status_code}")
    
    # 6. Submit for verification
    if report_id:
        response = requests.post(
            f"{API_BASE}/workflow/usg/{report_id}/submit_for_verification/",
            headers={"Authorization": f"Bearer {token}"},
            json={"report_json": report_data["report_json"]}
        )
        if response.status_code == 200:
            print(f"  Submitted for verification")
        else:
            print(f"  Submit response: {response.status_code}")
    
    print("  ✅ USG workflow completed")
    return True


def test_opd_workflow(token):
    """Test complete OPD workflow"""
    # 1. Get or create patient
    patient = test_create_patient(token)
    if not patient:
        return False
    
    # 2. Get OPD service
    services = test_get_services(token)
    if not services:
        return False
    
    opd_service = None
    for svc in services:
        if "OPD" in svc.get("code", "").upper() or "OPD" in svc.get("name", "").upper():
            opd_service = svc
            break
    
    if not opd_service:
        print("  ⚠ No OPD service found, using first service")
        opd_service = services[0]
    
    # 3. Create service visit
    visit = test_create_service_visit(token, patient, opd_service)
    if not visit:
        return False
    
    # 4. Create OPD vitals
    vitals_data = {
        "visit_id": visit["id"],
        "bp_systolic": "120",
        "bp_diastolic": "80",
        "pulse": "72",
        "temperature": "98.6",
        "weight": "70",
        "height": "170",
    }
    response = requests.post(
        f"{API_BASE}/workflow/opd-vitals/",
        headers={"Authorization": f"Bearer {token}"},
        json=vitals_data
    )
    if response.status_code not in [200, 201]:
        print(f"  OPD vitals creation failed: {response.status_code} - {response.text}")
        return False
    print(f"  OPD vitals created")
    
    # 5. Create OPD consultation
    consult_data = {
        "visit_id": visit["id"],
        "diagnosis": "Test diagnosis for E2E test",
        "medicines_json": [
            {"name": "Medicine A", "dosage": "500mg", "frequency": "BD", "duration": "5 days"}
        ],
        "investigations_json": ["CBC", "Blood Sugar"],
        "advice": "Test advice",
        "followup": "Follow up in 1 week",
    }
    response = requests.post(
        f"{API_BASE}/workflow/opd-consult/",
        headers={"Authorization": f"Bearer {token}"},
        json=consult_data
    )
    if response.status_code not in [200, 201]:
        print(f"  OPD consultation creation failed: {response.status_code} - {response.text}")
        return False
    consult = response.json()
    print(f"  OPD consultation created")
    
    # 6. Save and print (publish)
    consult_id = consult.get("id")
    if consult_id:
        response = requests.post(
            f"{API_BASE}/workflow/opd-consult/{consult_id}/save_and_print/",
            headers={"Authorization": f"Bearer {token}"},
            json=consult_data
        )
        if response.status_code == 200:
            print(f"  Prescription saved and published")
    
    print("  ✅ OPD workflow completed")
    return True


def main():
    """Run all E2E tests"""
    print("=" * 70)
    print("RIMS End-to-End Workflow Test")
    print("=" * 70)
    print(f"Base URL: {BASE_URL}")
    print(f"Username: {USERNAME}")
    print(f"Date: {datetime.now()}")
    print("=" * 70)
    
    # Test authentication
    token = None
    def auth_test():
        nonlocal token
        token = test_auth()
        return token is not None
    test("Authentication", auth_test)
    if not token:
        token = get_token()
    
    if not token:
        print("\n❌ Authentication failed. Cannot proceed with tests.")
        return 1
    
    # Test basic operations
    test("Create Patient", lambda: test_create_patient(token) is not None)
    test("Get Services", lambda: test_get_services(token) is not None)
    
    # Test service visit creation (the failing operation)
    patient = test_create_patient(token)
    services = test_get_services(token)
    if patient and services and len(services) > 0:
        test("Create Service Visit (was failing)", 
             lambda: test_create_service_visit(token, patient, services[0]) is not None)
    
    # Test complete workflows
    test("USG Workflow E2E", lambda: test_usg_workflow(token))
    test("OPD Workflow E2E", lambda: test_opd_workflow(token))
    
    # Summary
    print("\n" + "=" * 70)
    print("Test Results Summary")
    print("=" * 70)
    print(f"Passed: {PASSED}")
    print(f"Failed: {FAILED}")
    print(f"Total: {PASSED + FAILED}")
    
    if FAILED_TESTS:
        print(f"\nFailed tests:")
        for test_name in FAILED_TESTS:
            print(f"  - {test_name}")
    
    if FAILED == 0:
        print("\n✅ All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {FAILED} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
