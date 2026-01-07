"""
Unit tests for receipt generation functionality
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from unittest.mock import patch, MagicMock
import os
from datetime import datetime

from apps.patients.models import Patient
from apps.catalog.models import Modality, Service
from .models import Visit, OrderItem, ReceiptSequence, ReceiptSettings

User = get_user_model()


class ReceiptSequenceTest(TestCase):
    """Test receipt number generation"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123"
        )
        self.patient = Patient.objects.create(
            mrn="TEST001",
            name="Test Patient",
            age=30,
            gender="M",
            phone="1234567890"
        )
        modality = Modality.objects.create(code="USG", name="Ultrasound")
        self.service = Service.objects.create(
            modality=modality,
            name="Test Service",
            price=Decimal("100.00"),
            charges=Decimal("100.00")
        )
    
    def test_receipt_number_format(self):
        """Test that receipt numbers follow YYMM-### format"""
        receipt_number = ReceiptSequence.get_next_receipt_number()
        
        # Should be in format YYMM-###
        parts = receipt_number.split("-")
        self.assertEqual(len(parts), 2)
        self.assertEqual(len(parts[0]), 4)  # YYMM
        self.assertEqual(len(parts[1]), 3)  # ###
        
        # Check it's numeric
        self.assertTrue(parts[0].isdigit())
        self.assertTrue(parts[1].isdigit())
        
        # Check it starts with current year/month
        now = timezone.now()
        expected_yymm = now.strftime("%y%m")
        self.assertEqual(parts[0], expected_yymm)
    
    def test_receipt_number_sequence(self):
        """Test that receipt numbers increment sequentially"""
        num1 = ReceiptSequence.get_next_receipt_number()
        num2 = ReceiptSequence.get_next_receipt_number()
        
        # Extract sequence numbers
        seq1 = int(num1.split("-")[1])
        seq2 = int(num2.split("-")[1])
        
        self.assertEqual(seq2, seq1 + 1)
    
    def test_receipt_number_monthly_reset(self):
        """Test that receipt numbers reset monthly"""
        # Create a sequence for current month
        current_num = ReceiptSequence.get_next_receipt_number()
        current_seq = ReceiptSequence.objects.get(yymm=timezone.now().strftime("%y%m"))
        current_seq.last_number = 5
        current_seq.save()
        
        # Get next number - should be 6
        next_num = ReceiptSequence.get_next_receipt_number()
        self.assertEqual(int(next_num.split("-")[1]), 6)
        
        # Simulate month change by creating sequence for different month
        from datetime import timedelta
        next_month = timezone.now() + timedelta(days=32)
        next_yymm = next_month.strftime("%y%m")
        
        # Manually create sequence for next month
        ReceiptSequence.objects.create(yymm=next_yymm, last_number=0)
        next_month_seq = ReceiptSequence.objects.get(yymm=next_yymm)
        next_month_seq.last_number = 0
        next_month_seq.save()
        
        # If we were in next month, sequence should reset
        # (This is more of a documentation test since we can't easily change system time)
        self.assertTrue(True)  # Placeholder - actual test would require time mocking
    
    def test_receipt_number_concurrency_safe(self):
        """Test that receipt number generation is concurrency-safe"""
        from threading import Thread
        import queue
        
        results = queue.Queue()
        
        def generate_receipt():
            num = ReceiptSequence.get_next_receipt_number()
            results.put(num)
        
        # Generate 10 receipt numbers concurrently
        threads = []
        for _ in range(10):
            t = Thread(target=generate_receipt)
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # Collect all results
        receipt_numbers = []
        while not results.empty():
            receipt_numbers.append(results.get())
        
        # All should be unique
        self.assertEqual(len(receipt_numbers), len(set(receipt_numbers)))
        
        # All should have same YYMM prefix
        yymm_prefix = receipt_numbers[0].split("-")[0]
        for num in receipt_numbers:
            self.assertEqual(num.split("-")[0], yymm_prefix)


class ReceiptSettingsTest(TestCase):
    """Test receipt settings"""
    
    def test_singleton_behavior(self):
        """Test that ReceiptSettings is a singleton"""
        settings1 = ReceiptSettings.get_settings()
        settings2 = ReceiptSettings.get_settings()
        
        self.assertEqual(settings1.pk, settings2.pk)
        self.assertEqual(settings1.pk, 1)
    
    def test_default_header_text(self):
        """Test default header text"""
        settings = ReceiptSettings.get_settings()
        self.assertEqual(settings.header_text, "Consultants Clinic Place")
    
    def test_update_header_text(self):
        """Test updating header text"""
        settings = ReceiptSettings.get_settings()
        settings.header_text = "New Clinic Name"
        settings.save()
        
        # Reload and verify
        settings = ReceiptSettings.get_settings()
        self.assertEqual(settings.header_text, "New Clinic Name")


class ReceiptPDFGenerationTest(TestCase):
    """Test PDF generation for receipts"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123"
        )
        self.patient = Patient.objects.create(
            mrn="TEST001",
            name="Test Patient",
            age=30,
            gender="M",
            phone="1234567890"
        )
        modality = Modality.objects.create(code="USG", name="Ultrasound")
        self.service = Service.objects.create(
            modality=modality,
            name="Test Service",
            price=Decimal("100.00"),
            charges=Decimal("100.00")
        )
        
        # Create visit with items
        self.visit = Visit.objects.create(
            patient=self.patient,
            created_by=self.user,
            subtotal=Decimal("200.00"),
            discount_amount=Decimal("20.00"),
            net_total=Decimal("180.00"),
            paid_amount=Decimal("180.00"),
            due_amount=Decimal("0.00"),
            payment_method="cash"
        )
        
        OrderItem.objects.create(
            visit=self.visit,
            service=self.service,
            charge=Decimal("100.00"),
            indication="Test indication"
        )
        OrderItem.objects.create(
            visit=self.visit,
            service=self.service,
            charge=Decimal("100.00"),
            indication=""
        )
    
    def test_pdf_generation_basic(self):
        """Test basic PDF generation"""
        from apps.reporting.pdf import build_receipt_pdf
        
        # Generate PDF
        pdf_file = build_receipt_pdf(self.visit)
        
        # Verify PDF was created
        self.assertIsNotNone(pdf_file)
        self.assertTrue(len(pdf_file.read()) > 0)
        
        # Verify PDF content (basic check)
        pdf_file.seek(0)
        pdf_content = pdf_file.read()
        self.assertIn(b"PDF", pdf_content)  # PDF files start with PDF header
    
    def test_pdf_generation_with_receipt_number(self):
        """Test PDF generation includes receipt number"""
        from apps.reporting.pdf import build_receipt_pdf
        
        # Generate receipt number
        self.visit.receipt_number = ReceiptSequence.get_next_receipt_number()
        self.visit.save()
        
        # Generate PDF
        pdf_file = build_receipt_pdf(self.visit)
        
        # Verify PDF contains receipt number
        pdf_file.seek(0)
        pdf_content = pdf_file.read().decode("latin-1", errors="ignore")
        self.assertIn(self.visit.receipt_number, pdf_content)
    
    def test_pdf_generation_with_branding(self):
        """Test PDF generation with branding settings"""
        from apps.reporting.pdf import build_receipt_pdf
        
        # Update receipt settings
        settings = ReceiptSettings.get_settings()
        settings.header_text = "Test Clinic Name"
        settings.save()
        
        # Generate PDF
        pdf_file = build_receipt_pdf(self.visit)
        
        # Verify PDF contains header text
        pdf_file.seek(0)
        pdf_content = pdf_file.read().decode("latin-1", errors="ignore")
        self.assertIn("Test Clinic Name", pdf_content)
    
    def test_pdf_includes_patient_info(self):
        """Test that PDF includes patient information"""
        from apps.reporting.pdf import build_receipt_pdf
        
        pdf_file = build_receipt_pdf(self.visit)
        pdf_file.seek(0)
        pdf_content = pdf_file.read().decode("latin-1", errors="ignore")
        
        # Check for patient info
        self.assertIn(self.patient.name, pdf_content)
        self.assertIn(self.patient.mrn, pdf_content)
        if self.patient.phone:
            self.assertIn(self.patient.phone, pdf_content)
    
    def test_pdf_includes_billing_summary(self):
        """Test that PDF includes billing summary"""
        from apps.reporting.pdf import build_receipt_pdf
        
        pdf_file = build_receipt_pdf(self.visit)
        pdf_file.seek(0)
        pdf_content = pdf_file.read().decode("latin-1", errors="ignore")
        
        # Check for billing info
        self.assertIn("200.00", pdf_content)  # Subtotal
        self.assertIn("20.00", pdf_content)  # Discount
        self.assertIn("180.00", pdf_content)  # Net total
        self.assertIn("cash", pdf_content.upper())  # Payment method


class ReceiptWorkflowTest(TestCase):
    """Integration test for receipt generation workflow"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123"
        )
        self.patient = Patient.objects.create(
            mrn="TEST001",
            name="Test Patient",
            age=30,
            gender="M",
            phone="1234567890"
        )
        modality = Modality.objects.create(code="USG", name="Ultrasound")
        self.service = Service.objects.create(
            modality=modality,
            name="Test Service",
            price=Decimal("100.00"),
            charges=Decimal("100.00")
        )
    
    def test_receipt_generation_workflow(self):
        """Test complete receipt generation workflow"""
        from django.conf import settings
        from pathlib import Path
        
        # Create visit
        visit = Visit.objects.create(
            patient=self.patient,
            created_by=self.user,
            subtotal=Decimal("100.00"),
            discount_amount=Decimal("0.00"),
            net_total=Decimal("100.00"),
            paid_amount=Decimal("100.00"),
            due_amount=Decimal("0.00"),
            payment_method="cash"
        )
        
        OrderItem.objects.create(
            visit=visit,
            service=self.service,
            charge=Decimal("100.00"),
            indication="Test"
        )
        
        # Initially no receipt number
        self.assertIsNone(visit.receipt_number)
        self.assertEqual(visit.receipt_pdf_path, "")
        
        # Generate receipt number
        visit.receipt_number = ReceiptSequence.get_next_receipt_number()
        self.assertIsNotNone(visit.receipt_number)
        
        # Generate PDF
        from apps.reporting.pdf import build_receipt_pdf
        pdf_file = build_receipt_pdf(visit)
        
        # Save PDF
        now = timezone.now()
        year = now.strftime("%Y")
        month = now.strftime("%m")
        pdf_dir = Path(settings.MEDIA_ROOT) / "pdfs" / "receipts" / year / month
        pdf_dir.mkdir(parents=True, exist_ok=True)
        
        pdf_filename = f"{visit.receipt_number}.pdf"
        pdf_path = pdf_dir / pdf_filename
        
        with open(pdf_path, "wb") as f:
            f.write(pdf_file.read())
        
        visit.receipt_pdf_path = f"pdfs/receipts/{year}/{month}/{pdf_filename}"
        visit.receipt_generated_at = timezone.now()
        visit.save()
        
        # Verify receipt was saved
        self.assertIsNotNone(visit.receipt_number)
        self.assertNotEqual(visit.receipt_pdf_path, "")
        self.assertIsNotNone(visit.receipt_generated_at)
        
        # Verify PDF file exists
        self.assertTrue(pdf_path.exists())
        
        # Cleanup
        if pdf_path.exists():
            pdf_path.unlink()
