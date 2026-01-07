from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm, inch
from reportlab.lib.utils import ImageReader
from io import BytesIO
from django.core.files.base import ContentFile
from decimal import Decimal
import os
from PIL import Image

def build_receipt_pdf(visit) -> ContentFile:
    """Generate receipt PDF for a visit with branding support"""
    from apps.studies.models import ReceiptSettings
    
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # Get receipt settings
    settings = ReceiptSettings.get_settings()
    
    y = height - 20  # Start from top
    
    # Header Image (full width banner)
    if settings.header_image and os.path.exists(settings.header_image.path):
        try:
            img = Image.open(settings.header_image.path)
            img_width, img_height = img.size
            # Scale to fit page width while maintaining aspect ratio
            scale = (width - 40) / img_width
            display_height = img_height * scale
            
            c.drawImage(
                ImageReader(img),
                20,  # left margin
                y - display_height,
                width=width - 40,
                height=display_height,
                preserveAspectRatio=True
            )
            y -= display_height + 10
        except Exception as e:
            # If image fails to load, fall back to text
            pass
    
    # Logo (if exists, place left/top)
    logo_height = 0
    if settings.logo_image and os.path.exists(settings.logo_image.path):
        try:
            logo = Image.open(settings.logo_image.path)
            logo_width, logo_height_img = logo.size
            # Scale logo to reasonable size (max 60mm height)
            logo_scale = min(60 / (logo_height_img * mm), (width - 100) / (logo_width * mm))
            logo_display_height = logo_height_img * logo_scale * mm
            logo_display_width = logo_width * logo_scale * mm
            
            c.drawImage(
                ImageReader(logo),
                40,  # left margin
                y - logo_display_height,
                width=logo_display_width,
                height=logo_display_height,
                preserveAspectRatio=True
            )
            logo_height = logo_display_height
        except Exception as e:
            # If logo fails to load, continue without it
            pass
    
    # Header Text (if no header image, or as fallback)
    if not (settings.header_image and os.path.exists(settings.header_image.path)):
        header_text = settings.header_text or "Consultants Clinic Place"
        c.setFont("Helvetica-Bold", 20)
        text_width = c.stringWidth(header_text, "Helvetica-Bold", 20)
        c.drawString((width - text_width) / 2, y - 20, header_text)
        y -= 35
    
    # Adjust y if logo was drawn
    if logo_height > 0:
        y = min(y, height - logo_height - 30)
    
    y -= 15
    
    # Receipt Metadata
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y, "RECEIPT")
    y -= 25
    
    c.setFont("Helvetica", 10)
    if visit.receipt_number:
        c.drawString(40, y, f"Receipt No: {visit.receipt_number}")
    else:
        c.drawString(40, y, f"Visit Number: {visit.visit_number}")
    y -= 15
    
    receipt_date = visit.receipt_generated_at or visit.created_at
    c.drawString(40, y, f"Date: {receipt_date.strftime('%Y-%m-%d %H:%M:%S')}")
    y -= 15
    
    if visit.created_by:
        c.drawString(40, y, f"Cashier: {visit.created_by.get_full_name() or visit.created_by.username}")
        y -= 15
    
    y -= 10
    
    # Patient Information Block
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "Patient Information")
    y -= 18
    
    c.setFont("Helvetica", 10)
    c.drawString(40, y, f"MR Number: {visit.patient.mrn}")
    y -= 14
    
    c.drawString(40, y, f"Name: {visit.patient.name}")
    y -= 14
    
    # Age/Gender
    age_gender_parts = []
    if visit.patient.age:
        age_gender_parts.append(f"Age: {visit.patient.age}")
    if visit.patient.gender:
        age_gender_parts.append(f"Gender: {visit.patient.gender}")
    if age_gender_parts:
        c.drawString(40, y, " | ".join(age_gender_parts))
        y -= 14
    
    if visit.patient.phone:
        c.drawString(40, y, f"Mobile: {visit.patient.phone}")
        y -= 14
    
    y -= 10
    
    # Services Table
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "Services")
    y -= 18
    
    # Table header
    c.setFont("Helvetica-Bold", 10)
    c.drawString(40, y, "Service Name")
    c.drawString(width - 120, y, "Charge")
    y -= 15
    
    # Draw line
    c.line(40, y, width - 40, y)
    y -= 10
    
    c.setFont("Helvetica", 10)
    for item in visit.items.all():
        service_name = f"{item.service.modality.code} - {item.service.name}"
        
        # Handle long service names
        if c.stringWidth(service_name, "Helvetica", 10) > (width - 200):
            service_name = service_name[:50] + "..."
        
        c.drawString(40, y, service_name)
        c.drawString(width - 120, y, f"Rs. {item.charge:.2f}")
        y -= 14
        
        if item.indication:
            c.setFont("Helvetica-Oblique", 9)
            indication_text = item.indication[:70]
            c.drawString(50, y, f"({indication_text})")
            y -= 12
            c.setFont("Helvetica", 10)
        
        # Check if we need a new page
        if y < 200:
            c.showPage()
            y = height - 40
    
    y -= 10
    
    # Billing Summary
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "Billing Summary")
    y -= 18
    
    c.setFont("Helvetica", 10)
    c.drawString(40, y, "Subtotal:")
    c.drawString(width - 120, y, f"Rs. {visit.subtotal:.2f}")
    y -= 16
    
    if visit.discount_amount > 0:
        discount_label = "Discount"
        if visit.discount_percentage:
            discount_label += f" ({visit.discount_percentage}%)"
        c.drawString(40, y, discount_label + ":")
        c.drawString(width - 120, y, f"-Rs. {visit.discount_amount:.2f}")
        y -= 16
    
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, y, "Net Total:")
    c.drawString(width - 120, y, f"Rs. {visit.net_total:.2f}")
    y -= 20
    
    c.setFont("Helvetica", 10)
    c.drawString(40, y, "Paid:")
    c.drawString(width - 120, y, f"Rs. {visit.paid_amount:.2f}")
    y -= 16
    
    if visit.due_amount > 0:
        c.drawString(40, y, "Due:")
        c.drawString(width - 120, y, f"Rs. {visit.due_amount:.2f}")
        y -= 16
    elif visit.due_amount < 0:
        c.drawString(40, y, "Change:")
        c.drawString(width - 120, y, f"Rs. {abs(visit.due_amount):.2f}")
        y -= 16
    
    if visit.payment_method:
        c.drawString(40, y, f"Payment Method: {visit.payment_method.upper()}")
        y -= 16
    
    y -= 20
    
    # Footer
    c.setFont("Helvetica-Oblique", 9)
    c.drawString(40, y, "Computer generated receipt")
    
    c.showPage()
    c.save()
    
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return ContentFile(pdf_bytes, name=f"receipt_{visit.receipt_number or visit.visit_number}.pdf")

def build_basic_pdf(report) -> ContentFile:
    """Basic PDF generator stub.
    Replace with your branded layout later (header, footer, signatory, QR, etc.)
    """
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    y = height - 50
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y, "Radiology Report")
    y -= 25

    c.setFont("Helvetica", 10)
    c.drawString(40, y, f"Accession: {report.study.accession}")
    y -= 14
    c.drawString(40, y, f"Patient: {report.study.patient.name} | MRN: {report.study.patient.mrn}")
    y -= 14
    c.drawString(40, y, f"Service: {report.study.service.name} ({report.study.service.modality.code})")
    y -= 20

    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, y, "Findings")
    y -= 14
    c.setFont("Helvetica", 10)
    for line in (report.narrative or "").splitlines()[:40]:
        c.drawString(40, y, line[:110])
        y -= 12
        if y < 80:
            c.showPage()
            y = height - 50

    y -= 10
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, y, "Impression")
    y -= 14
    c.setFont("Helvetica", 10)
    for line in (report.impression or "").splitlines()[:20]:
        c.drawString(40, y, line[:110])
        y -= 12
        if y < 80:
            c.showPage()
            y = height - 50

    c.showPage()
    c.save()

    pdf_bytes = buffer.getvalue()
    buffer.close()
    return ContentFile(pdf_bytes, name=f"{report.study.accession}.pdf")
