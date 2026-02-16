#!/usr/bin/env python3
"""
Production Validation Script for RIMS
Tests complete end-to-end workflow including V2 reporting
"""
import os
import sys
import requests
import json
from datetime import datetime

API_BASE = os.getenv("API_BASE", "http://localhost:8000/api")
USERNAME = os.getenv("TEST_USERNAME", "admin")
PASSWORD = os.getenv("TEST_PASSWORD", "admin123")

results = {}
errors = []

def log_test(name, passed, message=""):
    status = "✓ PASS" if passed else "✗ FAIL"
    print(f"{status}: {name}")
    if message:
        print(f"  {message}")
    results[name] = passed
    if not passed:
        errors.append(f"{name}: {message}")

def get_token():
    """Get authentication token"""
    try:
        response = requests.post(
            f"{API_BASE}/auth/token/",
            json={"username": USERNAME, "password": PASSWORD},
            timeout=10
        )
        response.raise_for_status()
        token = response.json().get("access")
        if not token:
            raise Exception("No token in response")
        return token
    except Exception as e:
        log_test("Authentication", False, str(e))
        return None

def create_patient(token):
    """Create test patient"""
    try:
        data = {
            "name": f"Validation Test {datetime.now().strftime('%Y%m%d%H%M%S')}",
            "age": 35,
            "gender": "M",
            "phone": "1234567890"
        }
        response = requests.post(
            f"{API_BASE}/patients/",
            headers={"Authorization": f"Bearer {token}"},
            json=data,
            timeout=10
        )
        response.raise_for_status()
        patient = response.json()
        
        # Validate MRN format
        mrn = patient.get("mrn", "")
        if not mrn.startswith("MR"):
            raise Exception(f"Invalid MRN format: {mrn}")
        
        log_test("Create Patient", True, f"MRN: {mrn}")
        return patient
    except Exception as e:
        log_test("Create Patient", False, str(e))
        return None

def get_services(token):
    """Get available services"""
    try:
        response = requests.get(
            f"{API_BASE}/workflow/service-catalog/",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        response.raise_for_status()
        services = response.json()
        if isinstance(services, dict) and "results" in services:
            services = services["results"]
        
        # Find USG service
        usg_service = next(
            (s for s in services if "USG" in s.get("code", "").upper() or "USG" in s.get("name", "").upper()),
            None
        )
        if not usg_service and services:
            usg_service = services[0]
        
        log_test("Get Services", True, f"Found {len(services)} services")
        return usg_service
    except Exception as e:
        log_test("Get Services", False, str(e))
        return None

def create_service_visit(token, patient, service):
    """Create service visit"""
    try:
        data = {
            "patient_id": patient["id"],
            "service_ids": [service["id"]],
            "subtotal": 1000,
            "discount": 0,
            "total_amount": 1000,
            "net_amount": 1000,
            "amount_paid": 1000,
            "payment_method": "cash"
        }
        response = requests.post(
            f"{API_BASE}/workflow/visits/create_visit/",
            headers={"Authorization": f"Bearer {token}"},
            json=data,
            timeout=10
        )
        response.raise_for_status()
        visit = response.json()
        
        # Validate visit_id format (should be like YYMM-####)
        visit_id = visit.get("visit_id", "")
        if not visit_id or len(visit_id) < 7:
            raise Exception(f"Invalid visit_id format: {visit_id}")
        
        log_test("Create ServiceVisit", True, f"Visit ID: {visit_id}")
        return visit
    except Exception as e:
        log_test("Create ServiceVisit", False, str(e))
        return None

def get_visit_items(token, visit_id):
    """Get service visit items"""
    try:
        response = requests.get(
            f"{API_BASE}/workflow/visits/{visit_id}/",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        response.raise_for_status()
        visit = response.json()
        items = visit.get("items", [])
        if not items:
            raise Exception("No items found in visit")
        return items[0]  # Return first item
    except Exception as e:
        log_test("Get Visit Items", False, str(e))
        return None

def create_report_instance(token, item_id):
    """Create/get ReportInstanceV2"""
    try:
        # Get values endpoint creates instance if needed
        response = requests.get(
            f"{API_BASE}/reporting/workitems/{item_id}/values/",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        
        log_test("Create ReportInstanceV2", True, f"Status: {data.get('status')}")
        return data
    except Exception as e:
        log_test("Create ReportInstanceV2", False, str(e))
        return None

def save_draft(token, item_id):
    """Save draft report"""
    try:
        values_json = {
            "note": "Test findings for validation",
            "impression": "Test impression"
        }
        response = requests.post(
            f"{API_BASE}/reporting/workitems/{item_id}/save/",
            headers={"Authorization": f"Bearer {token}"},
            json={"values_json": values_json},
            timeout=10
        )
        response.raise_for_status()
        log_test("Save Draft", True)
        return True
    except Exception as e:
        log_test("Save Draft", False, str(e))
        return False

def submit_report(token, item_id):
    """Submit report for verification"""
    try:
        response = requests.post(
            f"{API_BASE}/reporting/workitems/{item_id}/submit/",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        response.raise_for_status()
        log_test("Submit Report", True)
        return True
    except Exception as e:
        log_test("Submit Report", False, str(e))
        return False

def verify_report(token, item_id):
    """Verify report"""
    try:
        response = requests.post(
            f"{API_BASE}/reporting/workitems/{item_id}/verify/",
            headers={"Authorization": f"Bearer {token}"},
            json={"notes": "Verified for validation"},
            timeout=10
        )
        response.raise_for_status()
        log_test("Verify Report", True)
        return True
    except Exception as e:
        log_test("Verify Report", False, str(e))
        return False

def publish_report(token, item_id):
    """Publish report"""
    try:
        response = requests.post(
            f"{API_BASE}/reporting/workitems/{item_id}/publish/",
            headers={"Authorization": f"Bearer {token}"},
            timeout=30  # PDF generation may take time
        )
        response.raise_for_status()
        data = response.json()
        
        # Validate publish response
        if data.get("status") != "published":
            raise Exception(f"Unexpected status: {data.get('status')}")
        
        version = data.get("version")
        snapshot_id = data.get("snapshot_id")
        
        log_test("Publish Report", True, f"Version: {version}, Snapshot: {snapshot_id}")
        return data
    except Exception as e:
        log_test("Publish Report", False, str(e))
        return None

def get_published_pdf(token, item_id):
    """Get published PDF"""
    try:
        response = requests.get(
            f"{API_BASE}/reporting/workitems/{item_id}/published-pdf/",
            headers={"Authorization": f"Bearer {token}"},
            timeout=30
        )
        response.raise_for_status()
        
        # Validate PDF content
        content_type = response.headers.get("Content-Type", "")
        if "application/pdf" not in content_type:
            raise Exception(f"Expected PDF, got {content_type}")
        
        pdf_size = len(response.content)
        if pdf_size < 1000:  # PDF should be at least 1KB
            raise Exception(f"PDF too small: {pdf_size} bytes")
        
        log_test("Get Published PDF", True, f"Size: {pdf_size} bytes")
        return True
    except Exception as e:
        log_test("Get Published PDF", False, str(e))
        return False

def main():
    print("=" * 70)
    print("RIMS PRODUCTION VALIDATION - END-TO-END WORKFLOW")
    print("=" * 70)
    print(f"API Base: {API_BASE}")
    print(f"Username: {USERNAME}")
    print(f"Date: {datetime.now()}")
    print("=" * 70)
    
    # Step 1: Authentication
    token = get_token()
    if not token:
        print("\n❌ Authentication failed. Cannot proceed.")
        return 1
    
    # Step 2: Create Patient
    patient = create_patient(token)
    if not patient:
        return 1
    
    # Step 3: Get Services
    service = get_services(token)
    if not service:
        return 1
    
    # Step 4: Create ServiceVisit
    visit = create_service_visit(token, patient, service)
    if not visit:
        return 1
    
    # Step 5: Get Visit Items
    item = get_visit_items(token, visit["id"])
    if not item:
        return 1
    
    item_id = item["id"]
    
    # Step 6: Create ReportInstanceV2
    report_data = create_report_instance(token, item_id)
    if not report_data:
        return 1
    
    # Step 7: Save Draft
    if not save_draft(token, item_id):
        return 1
    
    # Step 8: Submit
    if not submit_report(token, item_id):
        return 1
    
    # Step 9: Verify
    if not verify_report(token, item_id):
        return 1
    
    # Step 10: Publish
    publish_data = publish_report(token, item_id)
    if not publish_data:
        return 1
    
    # Step 11: Get Published PDF
    if not get_published_pdf(token, item_id):
        return 1
    
    # Summary
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "✓ PASS" if passed_test else "✗ FAIL"
        print(f"  {status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if errors:
        print("\nErrors:")
        for error in errors:
            print(f"  - {error}")
    
    if passed == total:
        print("\n✅ ALL VALIDATION TESTS PASSED")
        return 0
    else:
        print(f"\n❌ {total - passed} TEST(S) FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())
