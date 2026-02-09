#!/usr/bin/env python3
"""
PDF generation smoke test for RIMS
Tests all PDF generation functions using ReportLab.
Usage:
  python scripts/smoke_pdf.py
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rims_backend.settings')
django.setup()

from io import BytesIO
from django.core.files.base import ContentFile
from apps.reporting.pdf_engine.receipt import build_receipt_pdf_reportlab, build_service_visit_receipt_pdf_reportlab
from apps.reporting.pdf_engine.clinical_report import build_clinical_report_pdf, build_basic_report_pdf
from apps.reporting.pdf_engine.prescription import build_prescription_pdf


def test_pdf_basic(pdf_bytes: bytes, pdf_name: str) -> bool:
    """Basic PDF validation"""
    assert len(pdf_bytes) > 100, f"{pdf_name}: PDF too small ({len(pdf_bytes)} bytes)"
    assert pdf_bytes[:4] == b'%PDF', f"{pdf_name}: PDF does not start with %PDF"
    print(f"✓ {pdf_name}: {len(pdf_bytes)} bytes, valid PDF header")
    return True


def test_receipt_pdf():
    """Test receipt PDF generation (Visit model)"""
    print("\n[TEST] Receipt PDF (Visit model)")
    try:
        from apps.studies.models import Visit, Patient
        
        # Try to get a visit or create minimal test data
        visit = Visit.objects.first()
        if not visit:
            print("  ⚠ No visits found, skipping receipt test")
            return True
        
        pdf_file = build_receipt_pdf_reportlab(visit)
        pdf_bytes = pdf_file.read()
        return test_pdf_basic(pdf_bytes, "Receipt PDF")
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def test_service_visit_receipt_pdf():
    """Test service visit receipt PDF generation"""
    print("\n[TEST] Service Visit Receipt PDF")
    try:
        from apps.workflow.models import ServiceVisit, Invoice
        
        # Try to get a service visit with invoice
        service_visit = ServiceVisit.objects.filter(invoice__isnull=False).first()
        if not service_visit:
            print("  ⚠ No service visits with invoices found, skipping test")
            return True
        
        invoice = service_visit.invoice
        pdf_file = build_service_visit_receipt_pdf_reportlab(service_visit, invoice)
        pdf_bytes = pdf_file.read()
        return test_pdf_basic(pdf_bytes, "Service Visit Receipt PDF")
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def test_usg_report_pdf():
    """Test USG report PDF generation"""
    print("\n[TEST] USG Report PDF")
    try:
        from apps.workflow.models import USGReport
        
        usg_report = USGReport.objects.first()
        if not usg_report:
            print("  ⚠ No USG reports found, skipping test")
            return True
        
        pdf_file = build_clinical_report_pdf(usg_report)
        pdf_bytes = pdf_file.read()
        return test_pdf_basic(pdf_bytes, "USG Report PDF")
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def test_prescription_pdf():
    """Test prescription PDF generation"""
    print("\n[TEST] Prescription PDF")
    try:
        from apps.workflow.models import OPDConsult
        
        opd_consult = OPDConsult.objects.first()
        if not opd_consult:
            print("  ⚠ No OPD consultations found, skipping test")
            return True
        
        pdf_file = build_prescription_pdf(opd_consult)
        pdf_bytes = pdf_file.read()
        return test_pdf_basic(pdf_bytes, "Prescription PDF")
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def test_basic_report_pdf():
    """Test basic report PDF generation"""
    print("\n[TEST] Basic Report PDF")
    try:
        from apps.reporting.models import Report
        
        report = Report.objects.first()
        if not report:
            print("  ⚠ No reports found, skipping test")
            return True
        
        pdf_file = build_basic_report_pdf(report)
        pdf_bytes = pdf_file.read()
        return test_pdf_basic(pdf_bytes, "Basic Report PDF")
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def main():
    """Run all PDF smoke tests"""
    print("=" * 60)
    print("PDF Generation Smoke Test")
    print("=" * 60)
    
    results = []
    
    results.append(("Receipt PDF", test_receipt_pdf()))
    results.append(("Service Visit Receipt PDF", test_service_visit_receipt_pdf()))
    results.append(("USG Report PDF", test_usg_report_pdf()))
    results.append(("Prescription PDF", test_prescription_pdf()))
    results.append(("Basic Report PDF", test_basic_report_pdf()))
    
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
        print("\n✅ All PDF generation tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed or skipped")
        return 1


if __name__ == "__main__":
    sys.exit(main())
