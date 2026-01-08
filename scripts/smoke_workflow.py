#!/usr/bin/env python3
"""
End-to-end workflow smoke test for RIMS
Tests complete workflow: patient creation → service visit → workflow progression → PDF generation
Usage:
  python scripts/smoke_workflow.py
"""
import os
import sys
import django
from datetime import datetime

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rims_backend.settings')
django.setup()

from django.utils import timezone
from apps.patients.models import Patient
from apps.workflow.models import ServiceVisit, ServiceCatalog, Invoice, USGReport, OPDConsult
from apps.workflow.pdf import build_service_visit_receipt_pdf, build_usg_report_pdf, build_opd_prescription_pdf


def test_workflow_usg():
    """Test USG workflow end-to-end"""
    print("\n[TEST] USG Workflow End-to-End")
    
    try:
        # 1. Create or get patient
        patient, _ = Patient.objects.get_or_create(
            mrn=f"TEST-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            defaults={
                'name': 'Test Patient USG',
                'age': 35,
                'gender': 'M',
                'phone': '1234567890',
            }
        )
        print(f"  ✓ Patient: {patient.mrn}")
        
        # 2. Get or create USG service
        service = ServiceCatalog.objects.filter(code__icontains='USG').first()
        if not service:
            print("  ⚠ No USG service found, creating test service")
            service = ServiceCatalog.objects.create(
                name='Test USG Service',
                code='USG-TEST',
                modality_code='USG',
                base_price=1000.00,
            )
        print(f"  ✓ Service: {service.name}")
        
        # 3. Create service visit (REGISTERED)
        service_visit = ServiceVisit.objects.create(
            patient=patient,
            service=service,
            status='REGISTERED',
            registered_at=timezone.now(),
        )
        print(f"  ✓ Service Visit created: {service_visit.visit_id} (status: {service_visit.status})")
        
        # 4. Create invoice
        invoice = Invoice.objects.create(
            service_visit=service_visit,
            total_amount=1000.00,
            discount=0.00,
            net_amount=1000.00,
            balance_amount=0.00,
        )
        print(f"  ✓ Invoice created: Rs. {invoice.net_amount}")
        
        # 5. Generate receipt PDF
        try:
            pdf_file = build_service_visit_receipt_pdf(service_visit, invoice)
            pdf_bytes = pdf_file.read()
            assert pdf_bytes[:4] == b'%PDF', "Receipt PDF invalid"
            print(f"  ✓ Receipt PDF generated: {len(pdf_bytes)} bytes")
        except Exception as e:
            print(f"  ✗ Receipt PDF generation failed: {e}")
            return False
        
        # 6. Transition to IN_PROGRESS
        service_visit.status = 'IN_PROGRESS'
        service_visit.save()
        print(f"  ✓ Status transition: REGISTERED → IN_PROGRESS")
        
        # 7. Create USG report
        usg_report = USGReport.objects.create(
            service_visit=service_visit,
            report_json={
                'findings': 'Test findings for smoke test',
                'impression': 'Test impression',
            },
        )
        print(f"  ✓ USG Report created")
        
        # 8. Transition to PENDING_VERIFICATION
        service_visit.status = 'PENDING_VERIFICATION'
        service_visit.save()
        print(f"  ✓ Status transition: IN_PROGRESS → PENDING_VERIFICATION")
        
        # 9. Generate USG report PDF
        try:
            pdf_file = build_usg_report_pdf(usg_report)
            pdf_bytes = pdf_file.read()
            assert pdf_bytes[:4] == b'%PDF', "USG Report PDF invalid"
            print(f"  ✓ USG Report PDF generated: {len(pdf_bytes)} bytes")
        except Exception as e:
            print(f"  ✗ USG Report PDF generation failed: {e}")
            return False
        
        # 10. Transition to PUBLISHED
        service_visit.status = 'PUBLISHED'
        service_visit.save()
        print(f"  ✓ Status transition: PENDING_VERIFICATION → PUBLISHED")
        
        print("  ✅ USG workflow completed successfully")
        return True
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_workflow_opd():
    """Test OPD workflow end-to-end"""
    print("\n[TEST] OPD Workflow End-to-End")
    
    try:
        # 1. Create or get patient
        patient, _ = Patient.objects.get_or_create(
            mrn=f"TEST-OPD-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            defaults={
                'name': 'Test Patient OPD',
                'age': 40,
                'gender': 'F',
                'phone': '0987654321',
            }
        )
        print(f"  ✓ Patient: {patient.mrn}")
        
        # 2. Get or create OPD service
        service = ServiceCatalog.objects.filter(code__icontains='OPD').first()
        if not service:
            print("  ⚠ No OPD service found, creating test service")
            service = ServiceCatalog.objects.create(
                name='Test OPD Service',
                code='OPD-TEST',
                modality_code='OPD',
                base_price=500.00,
            )
        print(f"  ✓ Service: {service.name}")
        
        # 3. Create service visit (REGISTERED)
        service_visit = ServiceVisit.objects.create(
            patient=patient,
            service=service,
            status='REGISTERED',
            registered_at=timezone.now(),
        )
        print(f"  ✓ Service Visit created: {service_visit.visit_id} (status: {service_visit.status})")
        
        # 4. Create invoice
        invoice = Invoice.objects.create(
            service_visit=service_visit,
            total_amount=500.00,
            discount=0.00,
            net_amount=500.00,
            balance_amount=0.00,
        )
        print(f"  ✓ Invoice created: Rs. {invoice.net_amount}")
        
        # 5. Transition to IN_PROGRESS
        service_visit.status = 'IN_PROGRESS'
        service_visit.save()
        print(f"  ✓ Status transition: REGISTERED → IN_PROGRESS")
        
        # 6. Create OPD consultation
        opd_consult = OPDConsult.objects.create(
            service_visit=service_visit,
            diagnosis='Test diagnosis for smoke test',
            medicines_json=[
                {'name': 'Medicine A', 'dosage': '500mg', 'frequency': 'BD', 'duration': '5 days'},
            ],
            investigations_json=[
                {'name': 'CBC'},
                {'name': 'Blood Sugar'},
            ],
            advice='Test advice',
            followup='Follow up in 1 week',
        )
        print(f"  ✓ OPD Consultation created")
        
        # 7. Generate prescription PDF
        try:
            pdf_file = build_opd_prescription_pdf(opd_consult)
            pdf_bytes = pdf_file.read()
            assert pdf_bytes[:4] == b'%PDF', "Prescription PDF invalid"
            print(f"  ✓ Prescription PDF generated: {len(pdf_bytes)} bytes")
        except Exception as e:
            print(f"  ✗ Prescription PDF generation failed: {e}")
            return False
        
        # 8. Transition to PUBLISHED
        service_visit.status = 'PUBLISHED'
        service_visit.save()
        print(f"  ✓ Status transition: IN_PROGRESS → PUBLISHED")
        
        print("  ✅ OPD workflow completed successfully")
        return True
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all workflow smoke tests"""
    print("=" * 60)
    print("Workflow End-to-End Smoke Test")
    print("=" * 60)
    
    results = []
    
    results.append(("USG Workflow", test_workflow_usg()))
    results.append(("OPD Workflow", test_workflow_opd()))
    
    print("\n" + "=" * 60)
    print("Results Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✅ All workflow tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
