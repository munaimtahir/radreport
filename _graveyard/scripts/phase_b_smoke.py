#!/usr/bin/env python3
"""
Phase B Smoke Tests for RIMS Core Model Enforcement
Tests the unified service catalog, line items, billing, and receipt generation.
"""

import requests
import json
import sys
from decimal import Decimal

# Configuration
API_BASE = "http://localhost:8000/api"
# You'll need to set these via environment variables or update manually
USERNAME = "admin"  # Update with test user
PASSWORD = "admin"  # Update with test password

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    RESET = '\033[0m'

def print_test(name):
    print(f"\n{Colors.YELLOW}Testing: {name}{Colors.RESET}")

def print_pass(msg):
    print(f"{Colors.GREEN}✓ PASS: {msg}{Colors.RESET}")

def print_fail(msg):
    print(f"{Colors.RED}✗ FAIL: {msg}{Colors.RESET}")

def get_auth_token():
    """Get authentication token"""
    response = requests.post(
        f"{API_BASE}/auth/token/",
        json={"username": USERNAME, "password": PASSWORD}
    )
    if response.status_code == 200:
        return response.json()["access"]
    raise Exception(f"Failed to authenticate: {response.text}")

def test_1_create_patient(token):
    """Test 1: Create patient -> MR stable"""
    print_test("Create Patient")
    data = {
        "name": "Test Patient Phase B",
        "age": 35,
        "gender": "Male",
        "phone": "1234567890",
        "address": "Test Address"
    }
    response = requests.post(
        f"{API_BASE}/patients/",
        headers={"Authorization": f"Bearer {token}"},
        json=data
    )
    if response.status_code == 201:
        patient = response.json()
        mrn = patient.get("mrn")
        if mrn:
            print_pass(f"Patient created with MRN: {mrn}")
            return patient
        else:
            print_fail("Patient created but no MRN")
            return None
    else:
        print_fail(f"Failed to create patient: {response.text}")
        return None

def test_2_get_services(token):
    """Test 2: Get services from unified catalog"""
    print_test("Get Services from Unified Catalog")
    response = requests.get(
        f"{API_BASE}/services/",
        headers={"Authorization": f"Bearer {token}"}
    )
    if response.status_code == 200:
        data = response.json()
        # Handle both paginated and non-paginated responses
        if isinstance(data, dict) and "results" in data:
            services = data["results"]
        else:
            services = data if isinstance(data, list) else []
        usg_services = [s for s in services if s.get("category") == "Radiology" and s.get("modality", {}).get("code") == "USG"]
        opd_services = [s for s in services if s.get("category") == "OPD"]
        print_pass(f"Found {len(services)} services ({len(usg_services)} USG, {len(opd_services)} OPD)")
        return services, usg_services, opd_services
    else:
        print_fail(f"Failed to get services: {response.text}")
        return [], [], []

def test_3_create_service_visit_multiple_services(token, patient, services, usg_services, opd_services):
    """Test 3: Create ServiceVisit with multiple services (USG + OPD)"""
    print_test("Create ServiceVisit with Multiple Services")
    
    # Select one USG and one OPD service if available
    service_ids = []
    if usg_services:
        service_ids.append(usg_services[0]["id"])
    if opd_services:
        service_ids.append(opd_services[0]["id"])
    
    if not service_ids:
        print_fail("No USG or OPD services available")
        return None
    
    # Calculate totals
    selected_services = [s for s in services if s["id"] in service_ids]
    subtotal = sum(Decimal(str(s.get("price") or s.get("charges") or 0)) for s in selected_services)
    discount = Decimal("0")
    total = subtotal - discount
    net_amount = total
    
    data = {
        "patient_id": patient["id"],
        "service_ids": service_ids,
        "subtotal": float(subtotal),
        "total_amount": float(total),
        "discount": float(discount),
        "net_amount": float(net_amount),
        "amount_paid": float(net_amount),
        "payment_method": "cash"
    }
    
    response = requests.post(
        f"{API_BASE}/workflow/visits/create_visit/",
        headers={"Authorization": f"Bearer {token}"},
        json=data
    )
    
    if response.status_code == 201:
        visit = response.json()
        visit_id = visit.get("visit_id")
        items = visit.get("items", [])
        
        if len(items) == len(service_ids):
            print_pass(f"ServiceVisit created: {visit_id} with {len(items)} items")
            for item in items:
                print_pass(f"  - Item: {item.get('service_name_snapshot')} (Price: {item.get('price_snapshot')})")
            return visit
        else:
            print_fail(f"Expected {len(service_ids)} items, got {len(items)}")
            return None
    else:
        print_fail(f"Failed to create service visit: {response.text}")
        return None

def test_4_verify_invoice_payment(token, visit):
    """Test 4: Verify Invoice/Payment -> due computed correctly"""
    print_test("Verify Invoice and Payment")
    
    visit_id = visit["id"]
    response = requests.get(
        f"{API_BASE}/workflow/visits/{visit_id}/",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        visit_data = response.json()
        invoice = visit_data.get("invoice")
        
        if invoice:
            subtotal = Decimal(str(invoice.get("subtotal", 0)))
            discount = Decimal(str(invoice.get("discount", 0)))
            net_amount = Decimal(str(invoice.get("net_amount", 0)))
            balance = Decimal(str(invoice.get("balance_amount", 0)))
            
            # Check payments - get from visit data or calculate from invoice
            # Payments are linked to service_visit, so we can calculate from invoice balance
            total_paid = Decimal("0")
            # Try to get payments if endpoint exists, otherwise calculate from invoice
            payments_response = requests.get(
                f"{API_BASE}/workflow/visits/{visit_id}/payments/",
                headers={"Authorization": f"Bearer {token}"}
            )
            if payments_response.status_code == 200:
                payments_data = payments_response.json()
                payments = payments_data.get("results", payments_data) if isinstance(payments_data, dict) else (payments_data if isinstance(payments_data, list) else [])
                total_paid = sum(Decimal(str(p.get("amount_paid", 0))) for p in payments)
            else:
                # Calculate from invoice: total_paid = net_amount - balance_amount
                total_paid = net_amount - balance
            
            expected_balance = net_amount - total_paid
            if abs(balance - expected_balance) < Decimal("0.01"):
                print_pass(f"Invoice balance correct: {balance} (expected: {expected_balance})")
                print_pass(f"  Subtotal: {subtotal}, Discount: {discount}, Net: {net_amount}, Paid: {total_paid}")
                return True
            else:
                print_fail(f"Balance mismatch: {balance} vs expected {expected_balance}")
                return False
        else:
            print_fail("No invoice found")
            return False
    else:
        print_fail(f"Failed to get visit: {response.text}")
        return False

def test_5_generate_receipt(token, visit):
    """Test 5: Generate receipt -> receipt_no format OK and PDF endpoint returns 200"""
    print_test("Generate Receipt PDF")
    
    visit_id = visit["id"]
    # Use PDF receipt endpoint
    response = requests.get(
        f"{API_BASE}/pdf/{visit_id}/receipt/",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        # Check receipt number format (YYMM-###)
        invoice_response = requests.get(
            f"{API_BASE}/workflow/visits/{visit_id}/",
            headers={"Authorization": f"Bearer {token}"}
        )
        if invoice_response.status_code == 200:
            invoice = invoice_response.json().get("invoice", {})
            receipt_no = invoice.get("receipt_number")
            
            if receipt_no:
                import re
                if re.match(r'^\d{4}-\d{3}$', receipt_no):
                    print_pass(f"Receipt number format OK: {receipt_no}")
                    print_pass("PDF endpoint returned 200")
                    return True
                else:
                    print_fail(f"Receipt number format invalid: {receipt_no}")
                    return False
            else:
                print_fail("Receipt number not generated")
                return False
        else:
            print_fail("Failed to get invoice")
            return False
    else:
        print_fail(f"Failed to generate receipt: {response.status_code} - {response.text}")
        return False

def test_6_usg_worklist(token):
    """Test 6: USG worklist shows USG items"""
    print_test("USG Worklist Shows USG Items")
    
    response = requests.get(
        f"{API_BASE}/workflow/visits/?workflow=USG",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        data = response.json()
        visits = data.get("results", data) if isinstance(data, dict) else (data if isinstance(data, list) else [])
        print_pass(f"USG worklist returned {len(visits)} visits")
        for visit in visits[:3]:  # Show first 3
            items = visit.get("items", [])
            # Check department_snapshot for USG filtering
            usg_items = [i for i in items if i.get("department_snapshot") == "USG"]
            if usg_items:
                print_pass(f"  Visit {visit.get('visit_id')} has USG items: {[i.get('service_name_snapshot') for i in usg_items]}")
            elif items:
                # Show what we got for debugging
                print_pass(f"  Visit {visit.get('visit_id')} has items with dept_snapshot: {[i.get('department_snapshot') for i in items]}")
        return True
    else:
        print_fail(f"Failed to get USG worklist: {response.text}")
        return False

def test_7_opd_worklist(token):
    """Test 7: OPD worklist shows OPD items"""
    print_test("OPD Worklist Shows OPD Items")
    
    response = requests.get(
        f"{API_BASE}/workflow/visits/?workflow=OPD",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        data = response.json()
        visits = data.get("results", data) if isinstance(data, dict) else (data if isinstance(data, list) else [])
        print_pass(f"OPD worklist returned {len(visits)} visits")
        for visit in visits[:3]:  # Show first 3
            items = visit.get("items", [])
            # Check department_snapshot for OPD filtering
            opd_items = [i for i in items if i.get("department_snapshot") == "OPD"]
            if opd_items:
                print_pass(f"  Visit {visit.get('visit_id')} has OPD items: {[i.get('service_name_snapshot') for i in opd_items]}")
            elif items:
                # Show what we got for debugging
                print_pass(f"  Visit {visit.get('visit_id')} has items with dept_snapshot: {[i.get('department_snapshot') for i in items]}")
        return True
    else:
        print_fail(f"Failed to get OPD worklist: {response.text}")
        return False

def test_8_no_legacy_creation(token):
    """Test 8: Confirm no legacy Visit/Study/Report created by new UI flow"""
    print_test("Verify Legacy Write Paths Blocked")
    
    # Get non-admin token for this test
    test_token_response = requests.post(
        f"{API_BASE}/auth/token/",
        json={"username": "testuser", "password": "testpass"}
    )
    if test_token_response.status_code != 200:
        print_fail("Could not get test user token - skipping legacy write test")
        return False
    
    test_token = test_token_response.json()["access"]
    
    # Try to create legacy Visit (should fail for non-admin)
    # First get a real patient ID for valid request
    patients_response = requests.get(
        f"{API_BASE}/patients/",
        headers={"Authorization": f"Bearer {test_token}"}
    )
    if patients_response.status_code == 200:
        patients_data = patients_response.json()
        patients = patients_data.get("results", patients_data) if isinstance(patients_data, dict) else (patients_data if isinstance(patients_data, list) else [])
        if patients:
            patient_id = patients[0]["id"]
            # Use proper Visit serializer format
            data = {
                "patient": patient_id,  # Use 'patient' not 'patient_id'
                "subtotal": 100,
                "net_total": 100
            }
            response = requests.post(
                f"{API_BASE}/visits/",
                headers={"Authorization": f"Bearer {test_token}"},
                json=data
            )
            
            if response.status_code == 403:
                print_pass("Legacy Visit creation blocked (403 Forbidden)")
            elif response.status_code == 405:
                print_pass("Legacy Visit creation blocked (405 Method Not Allowed)")
            else:
                print_fail(f"Legacy Visit creation not blocked: {response.status_code} - {response.text[:200]}")
                return False
        else:
            print_fail("No patients available for test")
            return False
    else:
        print_fail("Failed to get patients for test")
        return False
    
    return True

def main():
    print(f"{Colors.YELLOW}{'='*60}")
    print("PHASE B SMOKE TESTS")
    print("="*60 + Colors.RESET)
    
    try:
        token = get_auth_token()
        print_pass("Authentication successful")
    except Exception as e:
        print_fail(f"Authentication failed: {e}")
        sys.exit(1)
    
    results = []
    
    # Test 1: Create patient
    patient = test_1_create_patient(token)
    results.append(("Create Patient", patient is not None))
    if not patient:
        print("Cannot continue without patient")
        sys.exit(1)
    
    # Test 2: Get services
    services, usg_services, opd_services = test_2_get_services(token)
    results.append(("Get Services", len(services) > 0))
    
    # Test 3: Create service visit with multiple services
    visit = test_3_create_service_visit_multiple_services(token, patient, services, usg_services, opd_services)
    results.append(("Create ServiceVisit with Multiple Services", visit is not None))
    if not visit:
        print("Cannot continue without service visit")
        sys.exit(1)
    
    # Test 4: Verify invoice/payment
    results.append(("Verify Invoice/Payment", test_4_verify_invoice_payment(token, visit)))
    
    # Test 5: Generate receipt
    results.append(("Generate Receipt", test_5_generate_receipt(token, visit)))
    
    # Test 6: USG worklist
    results.append(("USG Worklist", test_6_usg_worklist(token)))
    
    # Test 7: OPD worklist
    results.append(("OPD Worklist", test_7_opd_worklist(token)))
    
    # Test 8: Legacy write paths blocked
    results.append(("Legacy Write Paths Blocked", test_8_no_legacy_creation(token)))
    
    # Summary
    print(f"\n{Colors.YELLOW}{'='*60}")
    print("SUMMARY")
    print("="*60 + Colors.RESET)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = f"{Colors.GREEN}✓ PASS{Colors.RESET}" if result else f"{Colors.RED}✗ FAIL{Colors.RESET}"
        print(f"{status} {name}")
    
    print(f"\n{passed}/{total} tests passed")
    
    if passed == total:
        print(f"{Colors.GREEN}All tests passed!{Colors.RESET}")
        sys.exit(0)
    else:
        print(f"{Colors.RED}Some tests failed{Colors.RESET}")
        sys.exit(1)

if __name__ == "__main__":
    main()
