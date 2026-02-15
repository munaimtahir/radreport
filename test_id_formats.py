#!/usr/bin/env python
"""
Test script to verify the new ID formats using apps.sequences:
- Patient MRN: MRYYYYMMDD####
- Patient Registration Number: CCJ-YY-####
- Visit ID: YYMM-####
- Receipt: YYMM-####
"""
import os
import sys
import django
from django.conf import settings

# Setup Django
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "backend")))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rims_backend.settings")
django.setup()

from apps.sequences.models import get_next_mrn, get_next_patient_reg_no, get_next_visit_id, get_next_receipt_number
from django.utils import timezone

def test_formats():
    print("=" * 60)
    print("Testing ID Formats (apps.sequences)")
    print("=" * 60)
    
    # MRN
    mrn = get_next_mrn()
    period = timezone.now().strftime("%Y%m%d")
    expected_prefix = f"MR{period}"
    print(f"\nMRN: {mrn}")
    if mrn.startswith(expected_prefix) and len(mrn) == len(expected_prefix) + 4:
        print(f"  ✓ Format is CORRECT (MRYYYYMMDD####)")
    else:
        print(f"  ✗ Format is INCORRECT. Expected starts with {expected_prefix}")
        sys.exit(1)

    # Patient Reg No
    reg = get_next_patient_reg_no()
    period_yy = timezone.now().strftime("%y")
    expected_prefix = f"CCJ-{period_yy}-"
    print(f"\nPatient Reg No: {reg}")
    if reg.startswith(expected_prefix) and len(reg) == len(expected_prefix) + 4:
        print(f"  ✓ Format is CORRECT (CCJ-YY-####)")
    else:
        print(f"  ✗ Format is INCORRECT. Expected starts with {expected_prefix}")
        sys.exit(1)

    # Visit ID
    visit = get_next_visit_id()
    period_yymm = timezone.now().strftime("%y%m")
    expected_prefix = f"{period_yymm}-"
    print(f"\nVisit ID: {visit}")
    if visit.startswith(expected_prefix) and len(visit) == len(expected_prefix) + 4:
        print(f"  ✓ Format is CORRECT (YYMM-####)")
    else:
        print(f"  ✗ Format is INCORRECT. Expected starts with {expected_prefix}")
        sys.exit(1)

    # Receipt
    receipt = get_next_receipt_number(increment=True)
    period_yymm_receipt = timezone.now().strftime("%y%m")
    expected_prefix = f"{period_yymm_receipt}-"
    print(f"\nReceipt: {receipt}")
    if receipt.startswith(expected_prefix) and len(receipt) == len(expected_prefix) + 4:
        print(f"  ✓ Format is CORRECT (YYMM-####)")
    else:
        print(f"  ✗ Format is INCORRECT. Expected starts with {expected_prefix}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        test_formats()
        print("\n" + "=" * 60)
        print("✓ All format tests completed!")
        print("=" * 60 + "\n")
    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        sys.exit(1)
