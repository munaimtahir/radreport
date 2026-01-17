"""
PDF generation for USG reports using ReportLab.
Version: usg_pdf_layout_v1
"""
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, Frame
from io import BytesIO
from django.core.files.base import ContentFile
import os


def generate_usg_pdf(published_text_snapshot, patient, visit, study, published_by=None):
    """
    Generate PDF from published text snapshot.
    
    Args:
        published_text_snapshot: str - The finalized narrative text
        patient: Patient - Patient instance
        visit: Visit - Visit instance
        study: UsgStudy - Study instance
        published_by: User - User who published (optional)
    
    Returns:
        ContentFile - PDF file content
    """
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # Styles
    styles = getSampleStyleSheet()
    
    y = height - 40  # Start from top with margin
    
    # Header
    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, y, "ULTRASOUND REPORT")
    y -= 30
    
    # Horizontal line
    c.setLineWidth(1)
    c.line(40, y, width - 40, y)
    y -= 25
    
    # Patient Information
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, y, "Patient Information")
    y -= 18
    
    c.setFont("Helvetica", 10)
    c.drawString(40, y, f"MR Number: {patient.mrn}")
    y -= 14
    
    c.drawString(40, y, f"Patient Name: {patient.name}")
    y -= 14
    
    # Age and Gender
    age_gender = []
    if patient.age:
        age_gender.append(f"Age: {patient.age}")
    if patient.gender:
        age_gender.append(f"Gender: {patient.gender}")
    if age_gender:
        c.drawString(40, y, " | ".join(age_gender))
        y -= 14
    
    if patient.phone:
        c.drawString(40, y, f"Contact: {patient.phone}")
        y -= 14
    
    y -= 10
    
    # Visit Information
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, y, "Study Information")
    y -= 18
    
    c.setFont("Helvetica", 10)
    c.drawString(40, y, f"Visit Number: {visit.visit_number}")
    y -= 14
    
    c.drawString(40, y, f"Service Code: {study.service_code}")
    y -= 14
    
    c.drawString(40, y, f"Study Date: {study.created_at.strftime('%Y-%m-%d %H:%M')}")
    y -= 14
    
    if study.published_at:
        c.drawString(40, y, f"Published Date: {study.published_at.strftime('%Y-%m-%d %H:%M')}")
        y -= 14
    
    y -= 20
    
    # Horizontal line before report body
    c.line(40, y, width - 40, y)
    y -= 20
    
    # Report Body (narrative text)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "REPORT")
    y -= 20
    
    # Use Paragraph for text wrapping
    c.setFont("Helvetica", 10)
    
    # Split narrative into lines and render with wrapping
    text_lines = published_text_snapshot.split('\n')
    
    for line in text_lines:
        if not line.strip():
            y -= 8  # Empty line spacing
            continue
        
        # Check if heading (ends with colon and is short)
        if line.strip().endswith(':') and len(line.strip()) < 50:
            # It's a heading
            c.setFont("Helvetica-Bold", 10)
            c.drawString(40, y, line.strip())
            c.setFont("Helvetica", 10)
            y -= 14
        else:
            # Regular text - wrap if needed
            max_width = width - 100
            if c.stringWidth(line, "Helvetica", 10) > max_width:
                # Need to wrap
                words = line.split()
                current_line = []
                for word in words:
                    test_line = ' '.join(current_line + [word])
                    if c.stringWidth(test_line, "Helvetica", 10) <= max_width:
                        current_line.append(word)
                    else:
                        # Draw current line and start new one
                        if current_line:
                            c.drawString(50, y, ' '.join(current_line))
                            y -= 14
                            if y < 100:  # Check for page break
                                c.showPage()
                                y = height - 40
                                c.setFont("Helvetica", 10)
                        current_line = [word]
                # Draw remaining words
                if current_line:
                    c.drawString(50, y, ' '.join(current_line))
                    y -= 14
            else:
                c.drawString(50, y, line)
                y -= 14
        
        # Check if we need a new page
        if y < 100:
            c.showPage()
            y = height - 40
            c.setFont("Helvetica", 10)
    
    y -= 20
    
    # Signature section
    if y < 150:
        c.showPage()
        y = height - 40
    
    y -= 30
    c.setFont("Helvetica", 10)
    c.drawString(40, y, "_" * 40)
    y -= 14
    
    if published_by:
        signature_name = published_by.get_full_name() or published_by.username
        c.drawString(40, y, f"Verified by: {signature_name}")
    else:
        c.drawString(40, y, "Radiologist Signature")
    y -= 14
    
    if study.published_at:
        c.drawString(40, y, f"Date: {study.published_at.strftime('%Y-%m-%d')}")
    
    # Footer
    c.setFont("Helvetica-Oblique", 8)
    c.drawString(40, 30, f"Report ID: {study.id}")
    c.drawString(width - 200, 30, "Computer generated report")
    
    c.showPage()
    c.save()
    
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    filename = f"usg_report_{study.id}.pdf"
    return ContentFile(pdf_bytes, name=filename)
