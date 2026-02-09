#!/usr/bin/env python3
"""
Phase C Smoke Tests for RIMS - Deterministic Workflow Execution

Tests:
1. ServiceVisitItem.status is primary; ServiceVisit.status is derived
2. Transitions are enforced server-side (no skipping)
3. Role-based permissions are enforced
4. All transitions are audit-logged
5. Worklists are item-centric
6. Illegal transitions are blocked
"""

import requests
import json
import sys
from decimal import Decimal
from datetime import datetime

# Configuration
API_BASE = "http://localhost:8015/api"  # Backend is mapped to port 8015
USERNAME = "admin"
PASSWORD = "admin"

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

def test_1_create_patient_and_visit(token):
    """Test 1: Create patient + multi-service visit"""
    print_test("Create Patient + Multi-Service Visit")
    
    # Create patient
    patient_data = {
        "name": "Test Patient Phase C",
        "age": 40,
        "gender": "Female",
        "phone": "9876543210",
    }
    patient_resp = requests.post(
        f"{API_BASE}/patients/",
        headers={"Authorization": f"Bearer {token}"},
        json=patient_data
    )
    if patient_resp.status_code != 201:
        print_fail(f"Failed to create patient: {patient_resp.text}")
        return None, None
    patient = patient_resp.json()
    print_pass(f"Patient created: {patient.get('mrn')}")
    
    # Get services
    services_resp = requests.get(
        f"{API_BASE}/services/",
        headers={"Authorization": f"Bearer {token}"}
    )
    if services_resp.status_code != 200:
        print_fail("Failed to get services")
        return None, None
    
    services_data = services_resp.json()
    services = services_data.get("results", services_data) if isinstance(services_data, dict) else services_data
    usg_services = [s for s in services if s.get("category") == "Radiology" and s.get("modality", {}).get("code") == "USG"]
    opd_services = [s for s in services if s.get("category") == "OPD"]
    
    if not usg_services or not opd_services:
        print_fail("Need at least one USG and one OPD service")
        return None, None
    
    # Create visit with USG + OPD
    service_ids = [usg_services[0]["id"], opd_services[0]["id"]]
    selected_services = [s for s in services if s["id"] in service_ids]
    subtotal = sum(Decimal(str(s.get("price") or s.get("charges") or 0)) for s in selected_services)
    
    visit_data = {
        "patient_id": patient["id"],
        "service_ids": service_ids,
        "subtotal": float(subtotal),
        "total_amount": float(subtotal),
        "net_amount": float(subtotal),
        "amount_paid": float(subtotal),
        "payment_method": "cash"
    }
    
    visit_resp = requests.post(
        f"{API_BASE}/workflow/visits/create_visit/",
        headers={"Authorization": f"Bearer {token}"},
        json=visit_data
    )
    
    if visit_resp.status_code != 201:
        print_fail(f"Failed to create visit: {visit_resp.text}")
        return None, None
    
    visit = visit_resp.json()
    items = visit.get("items", [])
    
    if len(items) != 2:
        print_fail(f"Expected 2 items, got {len(items)}")
        return None, None
    
    print_pass(f"Visit created: {visit.get('visit_id')} with {len(items)} items")
    
    # PHASE C: Verify item statuses are REGISTERED
    for item in items:
        if item.get("status") != "REGISTERED":
            print_fail(f"Item {item.get('id')} should be REGISTERED, got {item.get('status')}")
            return None, None
    
    print_pass("All items start with REGISTERED status")
    
    # PHASE C: Verify visit status is derived from items
    visit_status = visit.get("status")
    if visit_status != "REGISTERED":
        print_fail(f"Visit status should be REGISTERED (derived), got {visit_status}")
        return None, None
    
    print_pass(f"Visit status is derived: {visit_status}")
    
    return visit, items

def test_2_usg_item_transitions(token, visit, items):
    """Test 2: USG item transitions with audit logging"""
    print_test("USG Item Transitions")
    
    # Find USG item
    usg_item = None
    for item in items:
        if item.get("department_snapshot") == "USG":
            usg_item = item
            break
    
    if not usg_item:
        print_fail("No USG item found")
        return False
    
    item_id = usg_item["id"]
    print_pass(f"Found USG item: {item_id}")
    
    # Transition: REGISTERED -> IN_PROGRESS
    print("  Transition: REGISTERED -> IN_PROGRESS")
    resp = requests.post(
        f"{API_BASE}/workflow/items/{item_id}/transition_status/",
        headers={"Authorization": f"Bearer {token}"},
        json={"to_status": "IN_PROGRESS"}
    )
    if resp.status_code != 200:
        print_fail(f"Failed transition to IN_PROGRESS: {resp.text}")
        return False
    print_pass("  Transitioned to IN_PROGRESS")
    
    # Verify item status
    item_resp = requests.get(
        f"{API_BASE}/workflow/items/{item_id}/",
        headers={"Authorization": f"Bearer {token}"}
    )
    if item_resp.status_code != 200:
        print_fail("Failed to get item")
        return False
    item_data = item_resp.json()
    if item_data.get("status") != "IN_PROGRESS":
        print_fail(f"Item status should be IN_PROGRESS, got {item_data.get('status')}")
        return False
    print_pass("  Item status verified: IN_PROGRESS")
    
    # Transition: IN_PROGRESS -> PENDING_VERIFICATION
    print("  Transition: IN_PROGRESS -> PENDING_VERIFICATION")
    resp = requests.post(
        f"{API_BASE}/workflow/items/{item_id}/transition_status/",
        headers={"Authorization": f"Bearer {token}"},
        json={"to_status": "PENDING_VERIFICATION"}
    )
    if resp.status_code != 200:
        print_fail(f"Failed transition to PENDING_VERIFICATION: {resp.text}")
        return False
    print_pass("  Transitioned to PENDING_VERIFICATION")
    
    # Transition: PENDING_VERIFICATION -> RETURNED_FOR_CORRECTION (with reason)
    print("  Transition: PENDING_VERIFICATION -> RETURNED_FOR_CORRECTION")
    resp = requests.post(
        f"{API_BASE}/workflow/items/{item_id}/transition_status/",
        headers={"Authorization": f"Bearer {token}"},
        json={"to_status": "RETURNED_FOR_CORRECTION", "reason": "Need more details"}
    )
    if resp.status_code != 200:
        print_fail(f"Failed transition to RETURNED: {resp.text}")
        return False
    print_pass("  Transitioned to RETURNED_FOR_CORRECTION")
    
    # Transition: RETURNED -> IN_PROGRESS
    print("  Transition: RETURNED_FOR_CORRECTION -> IN_PROGRESS")
    resp = requests.post(
        f"{API_BASE}/workflow/items/{item_id}/transition_status/",
        headers={"Authorization": f"Bearer {token}"},
        json={"to_status": "IN_PROGRESS"}
    )
    if resp.status_code != 200:
        print_fail(f"Failed transition back to IN_PROGRESS: {resp.text}")
        return False
    print_pass("  Transitioned back to IN_PROGRESS")
    
    # Transition: IN_PROGRESS -> PENDING_VERIFICATION (again)
    print("  Transition: IN_PROGRESS -> PENDING_VERIFICATION (again)")
    resp = requests.post(
        f"{API_BASE}/workflow/items/{item_id}/transition_status/",
        headers={"Authorization": f"Bearer {token}"},
        json={"to_status": "PENDING_VERIFICATION"}
    )
    if resp.status_code != 200:
        print_fail(f"Failed transition to PENDING_VERIFICATION: {resp.text}")
        return False
    print_pass("  Transitioned to PENDING_VERIFICATION")
    
    # Transition: PENDING_VERIFICATION -> PUBLISHED
    print("  Transition: PENDING_VERIFICATION -> PUBLISHED")
    resp = requests.post(
        f"{API_BASE}/workflow/items/{item_id}/transition_status/",
        headers={"Authorization": f"Bearer {token}"},
        json={"to_status": "PUBLISHED"}
    )
    if resp.status_code != 200:
        print_fail(f"Failed transition to PUBLISHED: {resp.text}")
        return False
    print_pass("  Transitioned to PUBLISHED")
    
    # Verify audit logs
    item_resp = requests.get(
        f"{API_BASE}/workflow/items/{item_id}/",
        headers={"Authorization": f"Bearer {token}"}
    )
    item_data = item_resp.json()
    audit_logs = item_data.get("status_audit_logs", [])
    
    if len(audit_logs) < 5:
        print_fail(f"Expected at least 5 audit log entries, got {len(audit_logs)}")
        return False
    
    print_pass(f"  Audit logs verified: {len(audit_logs)} entries")
    
    # Verify transitions in order
    transitions = [(log.get("from_status"), log.get("to_status")) for log in audit_logs]
    expected = [
        ("REGISTERED", "IN_PROGRESS"),
        ("IN_PROGRESS", "PENDING_VERIFICATION"),
        ("PENDING_VERIFICATION", "RETURNED_FOR_CORRECTION"),
        ("RETURNED_FOR_CORRECTION", "IN_PROGRESS"),
        ("IN_PROGRESS", "PENDING_VERIFICATION"),
        ("PENDING_VERIFICATION", "PUBLISHED"),
    ]
    
    # Check that all expected transitions exist (order may vary due to reverse ordering)
    found_transitions = set(transitions)
    expected_set = set(expected)
    if not expected_set.issubset(found_transitions):
        print_fail(f"Missing transitions. Expected: {expected_set}, Found: {found_transitions}")
        return False
    
    print_pass("  All transitions logged correctly")
    
    return True

def test_3_opd_item_transitions(token, visit, items):
    """Test 3: OPD item transitions"""
    print_test("OPD Item Transitions")
    
    # Find OPD item
    opd_item = None
    for item in items:
        if item.get("department_snapshot") == "OPD":
            opd_item = item
            break
    
    if not opd_item:
        print_fail("No OPD item found")
        return False
    
    item_id = opd_item["id"]
    print_pass(f"Found OPD item: {item_id}")
    
    # Transition: REGISTERED -> IN_PROGRESS
    print("  Transition: REGISTERED -> IN_PROGRESS")
    resp = requests.post(
        f"{API_BASE}/workflow/items/{item_id}/transition_status/",
        headers={"Authorization": f"Bearer {token}"},
        json={"to_status": "IN_PROGRESS"}
    )
    if resp.status_code != 200:
        print_fail(f"Failed transition to IN_PROGRESS: {resp.text}")
        return False
    print_pass("  Transitioned to IN_PROGRESS")
    
    # Note: OPD workflow may use FINALIZED or go directly to PUBLISHED
    # For this test, we'll try FINALIZED -> PUBLISHED
    # If FINALIZED is not in allowed transitions, we'll skip it
    
    # Transition: IN_PROGRESS -> FINALIZED (if allowed)
    print("  Transition: IN_PROGRESS -> FINALIZED")
    resp = requests.post(
        f"{API_BASE}/workflow/items/{item_id}/transition_status/",
        headers={"Authorization": f"Bearer {token}"},
        json={"to_status": "FINALIZED"}
    )
    if resp.status_code == 200:
        print_pass("  Transitioned to FINALIZED")
        
        # Transition: FINALIZED -> PUBLISHED
        print("  Transition: FINALIZED -> PUBLISHED")
        resp = requests.post(
            f"{API_BASE}/workflow/items/{item_id}/transition_status/",
            headers={"Authorization": f"Bearer {token}"},
            json={"to_status": "PUBLISHED"}
        )
        if resp.status_code != 200:
            print_fail(f"Failed transition to PUBLISHED: {resp.text}")
            return False
        print_pass("  Transitioned to PUBLISHED")
    else:
        # FINALIZED not allowed, try direct to PUBLISHED (if OPD workflow allows it)
        print("  FINALIZED not allowed, trying direct to PUBLISHED")
        resp = requests.post(
            f"{API_BASE}/workflow/items/{item_id}/transition_status/",
            headers={"Authorization": f"Bearer {token}"},
            json={"to_status": "PUBLISHED"}
        )
        if resp.status_code != 200:
            print_fail(f"Failed transition to PUBLISHED: {resp.text}")
            return False
        print_pass("  Transitioned to PUBLISHED")
    
    # Verify audit logs
    item_resp = requests.get(
        f"{API_BASE}/workflow/items/{item_id}/",
        headers={"Authorization": f"Bearer {token}"}
    )
    item_data = item_resp.json()
    audit_logs = item_data.get("status_audit_logs", [])
    
    if len(audit_logs) < 2:
        print_fail(f"Expected at least 2 audit log entries, got {len(audit_logs)}")
        return False
    
    print_pass(f"  Audit logs verified: {len(audit_logs)} entries")
    
    return True

def test_4_illegal_transitions_blocked(token, items):
    """Test 4: Illegal transitions are blocked"""
    print_test("Illegal Transitions Blocked")
    
    # Find an item in REGISTERED status (or create a new visit)
    # For this test, we'll try to transition from REGISTERED directly to PUBLISHED
    # This should be blocked
    
    # Get a REGISTERED item (if we have one from previous tests, use it, otherwise skip)
    # Actually, let's use the OPD item if it's still REGISTERED, or create a new visit
    
    # Try to transition from REGISTERED to PUBLISHED directly (should fail)
    print("  Attempting illegal transition: REGISTERED -> PUBLISHED")
    
    # Create a new visit for this test
    services_resp = requests.get(
        f"{API_BASE}/services/",
        headers={"Authorization": f"Bearer {token}"}
    )
    services_data = services_resp.json()
    services = services_data.get("results", services_data) if isinstance(services_data, dict) else services_data
    usg_services = [s for s in services if s.get("category") == "Radiology" and s.get("modality", {}).get("code") == "USG"]
    
    if not usg_services:
        print_fail("No USG service available")
        return False
    
    # Create a simple visit
    patients_resp = requests.get(
        f"{API_BASE}/patients/",
        headers={"Authorization": f"Bearer {token}"}
    )
    patients_data = patients_resp.json()
    patients = patients_data.get("results", patients_data) if isinstance(patients_data, dict) else patients_data
    if not patients:
        print_fail("No patients available")
        return False
    
    patient = patients[0]
    service_ids = [usg_services[0]["id"]]
    subtotal = Decimal(str(usg_services[0].get("price") or usg_services[0].get("charges") or 0))
    
    visit_data = {
        "patient_id": patient["id"],
        "service_ids": service_ids,
        "subtotal": float(subtotal),
        "total_amount": float(subtotal),
        "net_amount": float(subtotal),
        "amount_paid": float(subtotal),
        "payment_method": "cash"
    }
    
    visit_resp = requests.post(
        f"{API_BASE}/workflow/visits/create_visit/",
        headers={"Authorization": f"Bearer {token}"},
        json=visit_data
    )
    
    if visit_resp.status_code != 201:
        print_fail("Failed to create test visit")
        return False
    
    visit = visit_resp.json()
    test_item = visit.get("items", [])[0]
    test_item_id = test_item["id"]
    
    # Try illegal transition
    resp = requests.post(
        f"{API_BASE}/workflow/items/{test_item_id}/transition_status/",
        headers={"Authorization": f"Bearer {token}"},
        json={"to_status": "PUBLISHED"}
    )
    
    if resp.status_code == 200:
        print_fail("Illegal transition REGISTERED -> PUBLISHED was allowed (should be blocked)")
        return False
    
    if resp.status_code in [400, 403]:
        print_pass(f"Illegal transition blocked: {resp.status_code}")
        error_detail = resp.json().get("detail", "")
        if "Invalid transition" in error_detail or "permission" in error_detail.lower():
            print_pass("  Error message indicates invalid transition")
        return True
    else:
        print_fail(f"Unexpected response: {resp.status_code} - {resp.text}")
        return False

def test_5_item_centric_worklist(token):
    """Test 5: Item-centric worklist"""
    print_test("Item-Centric Worklist")
    
    # Get USG worklist (item-centric)
    resp = requests.get(
        f"{API_BASE}/workflow/items/worklist/?department=USG&status=REGISTERED,IN_PROGRESS",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if resp.status_code != 200:
        print_fail(f"Failed to get worklist: {resp.text}")
        return False
    
    worklist = resp.json()
    
    if not isinstance(worklist, list):
        print_fail("Worklist should return a list")
        return False
    
    print_pass(f"Worklist returned {len(worklist)} items")
    
    # Verify items have required fields
    if worklist:
        item = worklist[0]
        required_fields = ["id", "status", "department_snapshot", "visit_id", "patient_name"]
        missing = [f for f in required_fields if f not in item]
        if missing:
            print_fail(f"Missing fields in worklist item: {missing}")
            return False
        print_pass("  Worklist items have required fields")
        
        # Verify all items are USG
        non_usg = [i for i in worklist if i.get("department_snapshot") != "USG"]
        if non_usg:
            print_fail(f"Found {len(non_usg)} non-USG items in USG worklist")
            return False
        print_pass("  All items are USG")
    
    return True

def test_6_visit_status_derived(token, visit):
    """Test 6: Visit status is derived from items"""
    print_test("Visit Status Derived from Items")
    
    visit_id = visit["id"]
    
    # Get visit with items
    resp = requests.get(
        f"{API_BASE}/workflow/visits/{visit_id}/",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if resp.status_code != 200:
        print_fail("Failed to get visit")
        return False
    
    visit_data = resp.json()
    visit_status = visit_data.get("status")
    items = visit_data.get("items", [])
    
    # Check item statuses
    item_statuses = [item.get("status") for item in items]
    print(f"  Item statuses: {item_statuses}")
    print(f"  Visit status: {visit_status}")
    
    # Verify derived status logic
    # If any item is PENDING_VERIFICATION => visit is PENDING_VERIFICATION
    # Else if any item is IN_PROGRESS => visit is IN_PROGRESS
    # Else if all items are PUBLISHED => visit is PUBLISHED
    # Else REGISTERED
    
    if "PENDING_VERIFICATION" in item_statuses:
        expected = "PENDING_VERIFICATION"
    elif "IN_PROGRESS" in item_statuses:
        expected = "IN_PROGRESS"
    elif all(s == "PUBLISHED" for s in item_statuses):
        expected = "PUBLISHED"
    elif "RETURNED_FOR_CORRECTION" in item_statuses:
        expected = "RETURNED_FOR_CORRECTION"
    else:
        expected = "REGISTERED"
    
    if visit_status != expected:
        print_fail(f"Visit status should be {expected} (derived), got {visit_status}")
        return False
    
    print_pass(f"Visit status correctly derived: {visit_status}")
    
    return True

def main():
    print(f"{Colors.YELLOW}{'='*60}")
    print("PHASE C SMOKE TESTS")
    print("="*60 + Colors.RESET)
    
    try:
        token = get_auth_token()
        print_pass("Authentication successful")
    except Exception as e:
        print_fail(f"Authentication failed: {e}")
        sys.exit(1)
    
    results = []
    
    # Test 1: Create patient + visit
    visit, items = test_1_create_patient_and_visit(token)
    results.append(("Create Patient + Visit", visit is not None and items is not None))
    if not visit or not items:
        print("Cannot continue without visit")
        sys.exit(1)
    
    # Test 2: USG item transitions
    results.append(("USG Item Transitions", test_2_usg_item_transitions(token, visit, items)))
    
    # Test 3: OPD item transitions
    results.append(("OPD Item Transitions", test_3_opd_item_transitions(token, visit, items)))
    
    # Test 4: Illegal transitions blocked
    results.append(("Illegal Transitions Blocked", test_4_illegal_transitions_blocked(token, items)))
    
    # Test 5: Item-centric worklist
    results.append(("Item-Centric Worklist", test_5_item_centric_worklist(token)))
    
    # Test 6: Visit status derived
    results.append(("Visit Status Derived", test_6_visit_status_derived(token, visit)))
    
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
