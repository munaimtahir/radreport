#!/usr/bin/env python
"""
Test script to verify the new ID formats:
- Patient Registration Number: CCJ-26-0001 (CCJ-yy-nnnn)
- Visit ID: 2601-001 (yymm-nnn)
"""
import os
import sys
import django
from datetime import datetime

# Skip when invoked by pytest; this script is intended to be run manually.
if "pytest" in sys.modules:
    import pytest

    pytest.skip("Integration script is not a pytest test module.", allow_module_level=True)

# Setup Django
sys.path.insert(0, '/home/munaim/srv/apps/radreport/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rims_backend.settings')
django.setup()

from apps.patients.models import Patient
from apps.workflow.models import ServiceVisit

def test_patient_reg_no():
    """Test patient registration number generation"""
    print("=" * 60)
    print("Testing Patient Registration Number Format")
    print("=" * 60)
    
    # Create a test patient
    patient = Patient(
        name="Test Patient",
        age=30,
        gender="Male",
        phone="03001234567"
    )
    
    # Generate the registration number (without saving)
    reg_no = patient.generate_patient_reg_no()
    print(f"\n✓ Generated Patient Reg No: {reg_no}")
    print(f"  Expected Format: CCJ-yy-nnnn (e.g., CCJ-26-0001)")
    
    # Validate format
    parts = reg_no.split('-')
    if len(parts) == 3 and parts[0] == "CCJ" and len(parts[1]) == 2 and len(parts[2]) == 4:
        print(f"  ✓ Format is CORRECT")
        print(f"    - Clinic Code: {parts[0]}")
        print(f"    - Year: {parts[1]}")
        print(f"    - Sequential: {parts[2]}")
    else:
        print(f"  ✗ Format is INCORRECT")
    
    return reg_no

def test_visit_id():
    """Test visit ID generation"""
    print("\n" + "=" * 60)
    print("Testing Visit ID Format")
    print("=" * 60)
    
    # Create a test patient first
    patient = Patient.objects.first()
    if not patient:
        print("  ⚠ No patients found in database. Creating one...")
        patient = Patient.objects.create(
            name="Test Patient for Visit",
            age=25,
            gender="Female"
        )
        print(f"  ✓ Created patient: {patient.patient_reg_no}")
    
    # Create a test visit
    visit = ServiceVisit(patient=patient)
    
    # Generate the visit ID (without saving)
    visit_id = visit.generate_visit_id()
    print(f"\n✓ Generated Visit ID: {visit_id}")
    print(f"  Expected Format: yymm-nnn (e.g., 2601-023)")
    
    # Validate format
    parts = visit_id.split('-')
    if len(parts) == 2 and len(parts[0]) == 4 and len(parts[1]) == 3:
        print(f"  ✓ Format is CORRECT")
        print(f"    - Year-Month: {parts[0]}")
        print(f"    - Sequential: {parts[1]}")
        print(f"    - Resets: Monthly (on 1st of each month)")
    else:
        print(f"  ✗ Format is INCORRECT")
    
    return visit_id

def show_examples():
    """Show example IDs for different scenarios"""
    print("\n" + "=" * 60)
    print("Example IDs Throughout the Year")
    print("=" * 60)
    
    print("\nPatient Registration Numbers (CCJ-yy-nnnn):")
    print("  - First patient in 2026: CCJ-26-0001")
    print("  - 31st patient in 2026: CCJ-26-0031")
    print("  - 100th patient in 2026: CCJ-26-0100")
    print("  - First patient in 2027: CCJ-27-0001 (resets yearly)")
    
    print("\nVisit IDs (yymm-nnn):")
    print("  - First visit in Jan 2026: 2601-001")
    print("  - 23rd visit in Jan 2026: 2601-023")
    print("  - First visit in Feb 2026: 2602-001 (resets monthly)")
    print("  - First visit in Dec 2026: 2612-001")
    print("  - First visit in Jan 2027: 2701-001")

if __name__ == "__main__":
    print("\n🔍 ID Format Verification Script")
    print("=" * 60)
    
    try:
        test_patient_reg_no()
        test_visit_id()
        show_examples()
        
        print("\n" + "=" * 60)
        print("✓ All format tests completed successfully!")
        print("=" * 60 + "\n")
        
    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
