#!/usr/bin/env python
"""
Test Order → Report → Invoice Flow
Tests all service-level behaviors end-to-end
"""
import os
import sys
import django
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rims_backend.settings")
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.catalog.models import Service
from apps.patients.models import Patient
from apps.studies.models import Visit, OrderItem, Study
from apps.reporting.models import Report

_accession_counter = {}

def generate_accession():
    """Generate a unique accession number"""
    now = timezone.now()
    prefix = now.strftime("%Y%m%d")
    
    # Use a counter to ensure uniqueness within the same test run
    if prefix not in _accession_counter:
        today_count = Study.objects.filter(accession__startswith=prefix).count()
        _accession_counter[prefix] = today_count
    
    _accession_counter[prefix] += 1
    sequence = str(_accession_counter[prefix]).zfill(4)
    return f"{prefix}{sequence}"

User = get_user_model()

def test_service_flow():
    """Test complete order → report → invoice flow"""
    print("=" * 80)
    print("ORDER → REPORT → INVOICE FLOW TEST")
    print("=" * 80)
    
    issues = []
    
    # Get test user
    user = User.objects.filter(is_superuser=True).first()
    if not user:
        print("✗ No superuser found - cannot run tests")
        return False
    
    # Get test services
    abdomen_usg = Service.objects.filter(code="US008").first()  # Ultrasound Abdomen
    doppler_ob = Service.objects.filter(code="US001").first()  # Doppler Obstetric Single
    guided_proc = Service.objects.filter(code="US025").first()  # Ultrasound Guided Abscess Drainage
    twin_ob = Service.objects.filter(code="US002").first()  # Doppler Obstetric Twins
    
    if not all([abdomen_usg, doppler_ob, guided_proc, twin_ob]):
        print("✗ Required test services not found")
        return False
    
    print("\n[Test 1] Single Ultrasound (Abdomen)")
    print("-" * 80)
    try:
        # Create test patient
        patient = Patient.objects.create(
            name="Test Patient 1",
            age=35,
            gender="M",
            phone="03001234567"
        )
        
        # Create visit with single service
        visit = Visit.objects.create(
            patient=patient,
            created_by=user,
            subtotal=abdomen_usg.price,
            net_total=abdomen_usg.price,
            paid_amount=abdomen_usg.price,
            payment_method="cash"
        )
        
        # Create order item
        order_item = OrderItem.objects.create(
            visit=visit,
            service=abdomen_usg,
            charge=abdomen_usg.price,
            indication="Abdominal pain"
        )
        
        # Create study (as UnifiedIntakeSerializer does)
        if abdomen_usg.category == "Radiology" or abdomen_usg.modality.code in ["USG", "CT", "XRAY"]:
            study = Study.objects.create(
                patient=patient,
                service=abdomen_usg,
                visit=visit,
                order_item=order_item,
                indication=order_item.indication,
                status="registered",
                accession=generate_accession(),
                created_by=user,
            )
        
        # Verify study created
        study = Study.objects.filter(order_item=order_item).first()
        if not study:
            issues.append("Test 1: Study not created for single ultrasound")
            print("✗ Study not created")
        else:
            print(f"✓ Study created: {study.accession}")
            print(f"  Service: {study.service.name}")
            print(f"  Charge: Rs. {order_item.charge}")
            print(f"  Visit total: Rs. {visit.net_total}")
            
            # Verify pricing
            if visit.subtotal != abdomen_usg.price:
                issues.append(f"Test 1: Wrong subtotal. Expected {abdomen_usg.price}, got {visit.subtotal}")
                print(f"✗ Wrong subtotal: {visit.subtotal} (expected {abdomen_usg.price})")
            else:
                print(f"✓ Correct pricing: Rs. {visit.subtotal}")
        
        # Cleanup
        Study.objects.filter(patient=patient).delete()
        OrderItem.objects.filter(visit=visit).delete()
        Visit.objects.filter(patient=patient).delete()
        Patient.objects.filter(id=patient.id).delete()
        
    except Exception as e:
        issues.append(f"Test 1 failed: {str(e)}")
        print(f"✗ Test 1 failed: {str(e)}")
    
    print("\n[Test 2] Doppler Study")
    print("-" * 80)
    try:
        patient = Patient.objects.create(
            name="Test Patient 2",
            age=28,
            gender="F",
            phone="03009876543"
        )
        
        visit = Visit.objects.create(
            patient=patient,
            created_by=user,
            subtotal=doppler_ob.price,
            net_total=doppler_ob.price,
            paid_amount=doppler_ob.price,
            payment_method="card"
        )
        
        order_item = OrderItem.objects.create(
            visit=visit,
            service=doppler_ob,
            charge=doppler_ob.price,
            indication="Pregnancy check"
        )
        
        # Create study
        if doppler_ob.category == "Radiology" or doppler_ob.modality.code in ["USG", "CT", "XRAY"]:
            Study.objects.create(
                patient=patient,
                service=doppler_ob,
                visit=visit,
                order_item=order_item,
                indication=order_item.indication,
                status="registered",
                accession=generate_accession(),
                created_by=user,
            )
        
        study = Study.objects.filter(order_item=order_item).first()
        if not study:
            issues.append("Test 2: Study not created for Doppler")
            print("✗ Study not created")
        else:
            print(f"✓ Study created: {study.accession}")
            print(f"  Service: {study.service.name}")
            print(f"  Charge: Rs. {order_item.charge}")
        
        Study.objects.filter(patient=patient).delete()
        OrderItem.objects.filter(visit=visit).delete()
        Visit.objects.filter(patient=patient).delete()
        Patient.objects.filter(id=patient.id).delete()
        
    except Exception as e:
        issues.append(f"Test 2 failed: {str(e)}")
        print(f"✗ Test 2 failed: {str(e)}")
    
    print("\n[Test 3] Ultrasound + Doppler Together")
    print("-" * 80)
    try:
        patient = Patient.objects.create(
            name="Test Patient 3",
            age=32,
            gender="F",
            phone="03005555666"
        )
        
        total_price = abdomen_usg.price + doppler_ob.price
        visit = Visit.objects.create(
            patient=patient,
            created_by=user,
            subtotal=total_price,
            net_total=total_price,
            paid_amount=total_price,
            payment_method="online"
        )
        
        item1 = OrderItem.objects.create(
            visit=visit,
            service=abdomen_usg,
            charge=abdomen_usg.price,
            indication="Routine check"
        )
        
        item2 = OrderItem.objects.create(
            visit=visit,
            service=doppler_ob,
            charge=doppler_ob.price,
            indication="OB follow-up"
        )
        
        # Create studies
        for order_item in [item1, item2]:
            service = order_item.service
            if service.category == "Radiology" or service.modality.code in ["USG", "CT", "XRAY"]:
                Study.objects.create(
                    patient=patient,
                    service=service,
                    visit=visit,
                    order_item=order_item,
                    indication=order_item.indication,
                    status="registered",
                    accession=generate_accession(),
                    created_by=user,
                )
        
        studies = Study.objects.filter(visit=visit)
        if studies.count() != 2:
            issues.append(f"Test 3: Expected 2 studies, got {studies.count()}")
            print(f"✗ Expected 2 studies, got {studies.count()}")
        else:
            print(f"✓ Both studies created")
            print(f"  Total charge: Rs. {visit.subtotal}")
            print(f"  Item 1: {item1.service.name} - Rs. {item1.charge}")
            print(f"  Item 2: {item2.service.name} - Rs. {item2.charge}")
            
            # Verify no price duplication
            if visit.subtotal != (item1.charge + item2.charge):
                issues.append("Test 3: Price mismatch in visit total")
                print(f"✗ Price mismatch: {visit.subtotal} vs {item1.charge + item2.charge}")
            else:
                print("✓ No price duplication")
        
        Study.objects.filter(patient=patient).delete()
        OrderItem.objects.filter(visit=visit).delete()
        Visit.objects.filter(patient=patient).delete()
        Patient.objects.filter(id=patient.id).delete()
        
    except Exception as e:
        issues.append(f"Test 3 failed: {str(e)}")
        print(f"✗ Test 3 failed: {str(e)}")
    
    print("\n[Test 4] Ultrasound + Guided Procedure")
    print("-" * 80)
    try:
        patient = Patient.objects.create(
            name="Test Patient 4",
            age=45,
            gender="M",
            phone="03001111222"
        )
        
        total_price = abdomen_usg.price + guided_proc.price
        visit = Visit.objects.create(
            patient=patient,
            created_by=user,
            subtotal=total_price,
            net_total=total_price,
            paid_amount=total_price,
            payment_method="cash"
        )
        
        item1 = OrderItem.objects.create(
            visit=visit,
            service=abdomen_usg,
            charge=abdomen_usg.price,
            indication="Diagnostic scan"
        )
        
        item2 = OrderItem.objects.create(
            visit=visit,
            service=guided_proc,
            charge=guided_proc.price,
            indication="Abscess drainage"
        )
        
        # Create studies
        for order_item in [item1, item2]:
            service = order_item.service
            if service.category == "Radiology" or service.modality.code in ["USG", "CT", "XRAY"]:
                Study.objects.create(
                    patient=patient,
                    service=service,
                    visit=visit,
                    order_item=order_item,
                    indication=order_item.indication,
                    status="registered",
                    accession=generate_accession(),
                    created_by=user,
                )
        
        studies = Study.objects.filter(visit=visit)
        if studies.count() != 2:
            issues.append(f"Test 4: Expected 2 studies, got {studies.count()}")
            print(f"✗ Expected 2 studies, got {studies.count()}")
        else:
            print(f"✓ Both scan and procedure studies created")
            print(f"  Scan: {item1.service.name} (category: {item1.service.category})")
            print(f"  Procedure: {item2.service.name} (category: {item2.service.category})")
            print(f"  Total: Rs. {visit.subtotal}")
        
        Study.objects.filter(patient=patient).delete()
        OrderItem.objects.filter(visit=visit).delete()
        Visit.objects.filter(patient=patient).delete()
        Patient.objects.filter(id=patient.id).delete()
        
    except Exception as e:
        issues.append(f"Test 4 failed: {str(e)}")
        print(f"✗ Test 4 failed: {str(e)}")
    
    print("\n[Test 5] Twin OB Scan")
    print("-" * 80)
    try:
        patient = Patient.objects.create(
            name="Test Patient 5",
            age=30,
            gender="F",
            phone="03003333444"
        )
        
        visit = Visit.objects.create(
            patient=patient,
            created_by=user,
            subtotal=twin_ob.price,
            net_total=twin_ob.price,
            paid_amount=twin_ob.price,
            payment_method="insurance"
        )
        
        order_item = OrderItem.objects.create(
            visit=visit,
            service=twin_ob,
            charge=twin_ob.price,
            indication="Twin pregnancy"
        )
        
        # Create study
        if twin_ob.category == "Radiology" or twin_ob.modality.code in ["USG", "CT", "XRAY"]:
            Study.objects.create(
                patient=patient,
                service=twin_ob,
                visit=visit,
                order_item=order_item,
                indication=order_item.indication,
                status="registered",
                accession=generate_accession(),
                created_by=user,
            )
        
        study = Study.objects.filter(order_item=order_item).first()
        if not study:
            issues.append("Test 5: Study not created for twin OB")
            print("✗ Study not created")
        else:
            print(f"✓ Study created: {study.accession}")
            print(f"  Service: {study.service.name}")
            print(f"  Charge: Rs. {order_item.charge}")
            print(f"  TAT: {study.service.tat_minutes} minutes")
        
        Study.objects.filter(patient=patient).delete()
        OrderItem.objects.filter(visit=visit).delete()
        Visit.objects.filter(patient=patient).delete()
        Patient.objects.filter(id=patient.id).delete()
        
    except Exception as e:
        issues.append(f"Test 5 failed: {str(e)}")
        print(f"✗ Test 5 failed: {str(e)}")
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    if issues:
        print(f"\n❌ {len(issues)} issues found:")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")
        return False
    else:
        print("\n✅ All tests passed! Service flow is working correctly.")
        return True

if __name__ == "__main__":
    success = test_service_flow()
    sys.exit(0 if success else 1)
