from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from io import BytesIO
from django.core.files.base import ContentFile
from decimal import Decimal

def build_receipt_pdf(visit) -> ContentFile:
    """Generate receipt PDF for a visit"""
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    y = height - 40
    
    # Header
    c.setFont("Helvetica-Bold", 18)
    c.drawString(40, y, "RECEIPT")
    y -= 30
    
    c.setFont("Helvetica", 10)
    c.drawString(40, y, f"Visit Number: {visit.visit_number}")
    y -= 15
    c.drawString(40, y, f"Date: {visit.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
    y -= 25
    
    # Patient Info
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "Patient Information")
    y -= 18
    c.setFont("Helvetica", 10)
    c.drawString(40, y, f"Name: {visit.patient.name}")
    y -= 14
    c.drawString(40, y, f"MRN: {visit.patient.mrn}")
    y -= 14
    if visit.patient.phone:
        c.drawString(40, y, f"Phone: {visit.patient.phone}")
        y -= 14
    y -= 10
    
    # Services
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "Services")
    y -= 18
    c.setFont("Helvetica", 10)
    
    for item in visit.items.all():
        service_name = f"{item.service.modality.code} - {item.service.name}"
        c.drawString(40, y, service_name)
        c.drawString(width - 150, y, f"Rs. {item.charge:.2f}")
        y -= 14
        if item.indication:
            c.setFont("Helvetica-Oblique", 9)
            c.drawString(50, y, f"  ({item.indication[:60]})")
            y -= 12
            c.setFont("Helvetica", 10)
        if y < 150:
            c.showPage()
            y = height - 40
    
    y -= 10
    
    # Billing Summary
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "Billing Summary")
    y -= 18
    c.setFont("Helvetica", 10)
    
    c.drawString(40, y, "Subtotal:")
    c.drawString(width - 150, y, f"Rs. {visit.subtotal:.2f}")
    y -= 14
    
    if visit.discount_amount > 0:
        discount_label = f"Discount"
        if visit.discount_percentage:
            discount_label += f" ({visit.discount_percentage}%)"
        c.drawString(40, y, discount_label + ":")
        c.drawString(width - 150, y, f"-Rs. {visit.discount_amount:.2f}")
        y -= 14
    
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, y, "Net Total:")
    c.drawString(width - 150, y, f"Rs. {visit.net_total:.2f}")
    y -= 18
    
    c.setFont("Helvetica", 10)
    c.drawString(40, y, "Paid Amount:")
    c.drawString(width - 150, y, f"Rs. {visit.paid_amount:.2f}")
    y -= 14
    
    if visit.due_amount > 0:
        c.drawString(40, y, "Due Amount:")
        c.drawString(width - 150, y, f"Rs. {visit.due_amount:.2f}")
        y -= 14
    
    if visit.payment_method:
        c.drawString(40, y, f"Payment Method: {visit.payment_method.upper()}")
        y -= 14
    
    y -= 20
    c.setFont("Helvetica-Oblique", 9)
    c.drawString(40, y, "Thank you for your visit!")
    
    c.showPage()
    c.save()
    
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return ContentFile(pdf_bytes, name=f"receipt_{visit.visit_number}.pdf")

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
