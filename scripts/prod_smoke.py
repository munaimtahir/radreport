#!/usr/bin/env python
"""
Production Smoke Test Script for RIMS Workflow

Tests:
1. Login (or uses token)
2. Create patient
3. Create service visit with USG+OPD items
4. Create invoice/payment
5. Request receipt PDF endpoint and confirm 200
6. Request USG worklist with correct statuses and confirm 200
7. Request OPD worklist and confirm 200
"""

import os
import sys
import django
import requests
import json
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rims_backend.settings")
django.setup()

from django.contrib.auth import get_user_model
from apps.patients.models import Patient
from apps.workflow.models import ServiceVisit, ServiceVisitItem, Invoice, Payment
from apps.catalog.models import Service, Modality
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

# Configuration
API_BASE = os.getenv("API_BASE", "https://rims.alshifalab.pk/api")
USERNAME = os.getenv("TEST_USERNAME", "admin")
PASSWORD = os.getenv("TEST_PASSWORD", "admin")

def print_test(name):
    print(f"\n{'='*60}")
    print(f"TEST: {name}")
    print(f"{'='*60}")

def get_auth_token():
    """Get JWT token for API authentication"""
    print_test("Get Auth Token")
    url = f"{API_BASE}/auth/token/"
    data = {"username": USERNAME, "password": PASSWORD}
    
    try:
        response = requests.post(url, json=data, timeout=10)
        response.raise_for_status()
        token_data = response.json()
        token = token_data.get("access")
        print(f"✓ Token obtained: {token[:20]}...")
        return token
    except Exception as e:
        print(f"✗ Failed to get token: {e}")
        sys.exit(1)

def create_patient(token):
    """Create a test patient"""
    print_test("Create Patient")
    url = f"{API_BASE}/patients/"
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "name": "Test Patient Smoke",
        "age": 30,
        "gender": "M",
        "phone": "1234567890",
    }
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=10)
        response.raise_for_status()
        patient = response.json()
        print(f"✓ Patient created: {patient.get('name')} (ID: {patient.get('id')})")
        return patient
    except Exception as e:
        print(f"✗ Failed to create patient: {e}")
        if response.status_code == 400:
            print(f"  Response: {response.text}")
        sys.exit(1)

def get_services(token):
    """Get USG and OPD services"""
    print_test("Get Services")
    url = f"{API_BASE}/services/"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        services = response.json()
        
        # Find USG and OPD services
        usg_service = None
        opd_service = None
        
        if isinstance(services, dict) and "results" in services:
            services_list = services["results"]
        else:
            services_list = services if isinstance(services, list) else []
        
        for svc in services_list:
            if not usg_service and svc.get("modality", {}).get("code") == "USG":
                usg_service = svc
            if not opd_service and svc.get("category") == "OPD":
                opd_service = svc
        
        if not usg_service:
            print("⚠ No USG service found, will skip USG tests")
        else:
            print(f"✓ USG service found: {usg_service.get('name')} (ID: {usg_service.get('id')})")
        
        if not opd_service:
            print("⚠ No OPD service found, will skip OPD tests")
        else:
            print(f"✓ OPD service found: {opd_service.get('name')} (ID: {opd_service.get('id')})")
        
        return usg_service, opd_service
    except Exception as e:
        print(f"✗ Failed to get services: {e}")
        sys.exit(1)

def create_service_visit(token, patient_id, service_ids):
    """Create service visit with multiple services"""
    print_test("Create Service Visit")
    url = f"{API_BASE}/workflow/visits/create_visit/"
    headers = {"Authorization": f"Bearer {token}"}
    
    # Calculate totals
    total_price = sum(1000 for _ in service_ids)  # Assume 1000 per service
    
    data = {
        "patient_id": patient_id,
        "service_ids": service_ids,
        "subtotal": total_price,
        "discount": 0,
        "total_amount": total_price,
        "net_amount": total_price,
        "amount_paid": total_price,
        "payment_method": "cash",
    }
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=10)
        response.raise_for_status()
        visit = response.json()
        print(f"✓ Service visit created: {visit.get('visit_id')} (ID: {visit.get('id')})")
        return visit
    except Exception as e:
        print(f"✗ Failed to create service visit: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"  Response: {e.response.text}")
        sys.exit(1)

def test_receipt_pdf(token, visit_id):
    """Test receipt PDF endpoint"""
    print_test("Test Receipt PDF Endpoint")
    
    # Try both route patterns
    routes = [
        f"{API_BASE}/pdf/{visit_id}/receipt/",
        f"{API_BASE}/pdf/receipt/{visit_id}/",
    ]
    
    headers = {"Authorization": f"Bearer {token}"}
    
    for route in routes:
        try:
            print(f"  Trying: {route}")
            response = requests.get(route, headers=headers, timeout=10, allow_redirects=False)
            
            if response.status_code == 200:
                content_type = response.headers.get("Content-Type", "")
                if "application/pdf" in content_type:
                    pdf_size = len(response.content)
                    print(f"✓ Receipt PDF returned 200 (size: {pdf_size} bytes)")
                    print(f"  Route: {route}")
                    return True
                else:
                    print(f"⚠ Route returned 200 but not PDF: {content_type}")
            elif response.status_code == 404:
                print(f"  Route not found: {route}")
            else:
                print(f"  Route returned {response.status_code}: {response.text[:200]}")
        except Exception as e:
            print(f"  Error with route {route}: {e}")
    
    print("✗ Receipt PDF endpoint failed on all routes")
    return False

def test_usg_worklist(token):
    """Test USG worklist with status filter"""
    print_test("Test USG Worklist")
    url = f"{API_BASE}/workflow/visits/"
    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "workflow": "USG",
        "status": "REGISTERED,RETURNED_FOR_CORRECTION",
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if isinstance(data, dict) and "results" in data:
            count = len(data["results"])
        else:
            count = len(data) if isinstance(data, list) else 0
        
        print(f"✓ USG worklist returned 200 (count: {count})")
        print(f"  Status filter: {params['status']}")
        return True
    except Exception as e:
        print(f"✗ USG worklist failed: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"  Response: {e.response.text[:500]}")
        return False

def test_opd_worklist(token):
    """Test OPD worklist"""
    print_test("Test OPD Worklist")
    url = f"{API_BASE}/workflow/visits/"
    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "workflow": "OPD",
        "status": "REGISTERED",
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if isinstance(data, dict) and "results" in data:
            count = len(data["results"])
        else:
            count = len(data) if isinstance(data, list) else 0
        
        print(f"✓ OPD worklist returned 200 (count: {count})")
        return True
    except Exception as e:
        print(f"✗ OPD worklist failed: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"  Response: {e.response.text[:500]}")
        return False

def main():
    print("\n" + "="*60)
    print("RIMS PRODUCTION SMOKE TEST")
    print("="*60)
    print(f"API Base: {API_BASE}")
    print(f"Username: {USERNAME}")
    
    results = {}
    
    # 1. Get token
    token = get_auth_token()
    results["auth"] = True
    
    # 2. Create patient
    patient = create_patient(token)
    results["patient"] = True
    
    # 3. Get services
    usg_service, opd_service = get_services(token)
    results["services"] = True
    
    # 4. Create service visit
    service_ids = []
    if usg_service:
        service_ids.append(usg_service["id"])
    if opd_service:
        service_ids.append(opd_service["id"])
    
    if not service_ids:
        print("\n⚠ No services available, skipping visit creation")
        results["visit"] = False
    else:
        visit = create_service_visit(token, patient["id"], service_ids)
        results["visit"] = True
        
        # 5. Test receipt PDF
        results["receipt_pdf"] = test_receipt_pdf(token, visit["id"])
    
    # 6. Test USG worklist
    results["usg_worklist"] = test_usg_worklist(token)
    
    # 7. Test OPD worklist
    results["opd_worklist"] = test_opd_worklist(token)
    
    # Summary
    print_test("Test Summary")
    all_passed = all(results.values())
    
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}: {test_name}")
    
    print(f"\n{'='*60}")
    if all_passed:
        print("✓ ALL TESTS PASSED")
        return 0
    else:
        print("✗ SOME TESTS FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())
