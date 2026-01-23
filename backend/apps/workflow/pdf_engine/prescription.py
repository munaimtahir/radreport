"""
Prescription PDF generation using ReportLab
For OPD consultations and prescriptions.
"""
from io import BytesIO
from django.core.files.base import ContentFile
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import mm
from reportlab.lib.colors import black
from .base import PDFBase, PDFStyles


def build_prescription_pdf(opd_consult) -> ContentFile:
    """
    Generate OPD prescription PDF using ReportLab.
    Replaces WeasyPrint-based build_opd_prescription_pdf.
    """
    service_visit = opd_consult.service_visit
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=PDFBase.PAGE_SIZE)
    styles = PDFStyles.get_styles()
    base = PDFBase()
    
    # Build story
    story = []
    
    # Header
    story.append(Paragraph("PRESCRIPTION", styles['title']))
    story.append(Spacer(1, 10 * mm))
    
    # Patient Information
    story.append(Paragraph("Patient Information", styles['heading']))
    patient_data = [
        ['Visit ID:', service_visit.visit_id],
        ['Patient Reg No:', service_visit.patient.patient_reg_no or service_visit.patient.mrn],
        ['Name:', service_visit.patient.name],
    ]
    
    if service_visit.patient.age:
        patient_data.append(['Age:', str(service_visit.patient.age)])
    if service_visit.patient.gender:
        patient_data.append(['Gender:', service_visit.patient.gender])
    
    patient_table = Table(patient_data, colWidths=[80 * mm, 100 * mm])
    patient_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
    ]))
    story.append(patient_table)
    story.append(Spacer(1, 10 * mm))
    
    # Diagnosis
    if opd_consult.diagnosis:
        story.append(Paragraph("Diagnosis", styles['heading']))
        for line in str(opd_consult.diagnosis).splitlines():
            if line.strip():
                story.append(Paragraph(line.strip(), styles['body']))
        story.append(Spacer(1, 8 * mm))
    
    # Medicines
    medicines = opd_consult.medicines_json if isinstance(opd_consult.medicines_json, list) else []
    if medicines:
        story.append(Paragraph("Medicines", styles['heading']))
        
        # Build medicines table
        med_table_data = [['Medicine', 'Dosage', 'Frequency', 'Duration']]
        for med in medicines:
            if isinstance(med, dict):
                med_table_data.append([
                    med.get('name', ''),
                    med.get('dosage', ''),
                    med.get('frequency', ''),
                    med.get('duration', ''),
                ])
            else:
                med_table_data.append([str(med), '', '', ''])
        
        med_table = Table(med_table_data, colWidths=[60 * mm, 40 * mm, 40 * mm, 40 * mm])
        med_table.setStyle(base.create_table_style())
        story.append(med_table)
        story.append(Spacer(1, 8 * mm))
    
    # Investigations
    investigations = opd_consult.investigations_json if isinstance(opd_consult.investigations_json, list) else []
    if investigations:
        story.append(Paragraph("Investigations", styles['heading']))
        
        # Build investigations table
        inv_table_data = [['Investigation']]
        for inv in investigations:
            if isinstance(inv, dict):
                inv_table_data.append([inv.get('name', str(inv))])
            else:
                inv_table_data.append([str(inv)])
        
        inv_table = Table(inv_table_data, colWidths=[180 * mm])
        inv_table.setStyle(base.create_table_style())
        story.append(inv_table)
        story.append(Spacer(1, 8 * mm))
    
    # Advice
    if opd_consult.advice:
        story.append(Paragraph("Advice", styles['heading']))
        for line in str(opd_consult.advice).splitlines():
            if line.strip():
                story.append(Paragraph(line.strip(), styles['body']))
        story.append(Spacer(1, 8 * mm))
    
    # Follow-up
    if opd_consult.followup:
        story.append(Paragraph("Follow-up", styles['heading']))
        story.append(Paragraph(opd_consult.followup, styles['body']))
        story.append(Spacer(1, 8 * mm))
    
    # Consultant Information
    story.append(Spacer(1, 10 * mm))
    consultant_data = []
    if opd_consult.consultant:
        consultant_data.append(['Consultant:', opd_consult.consultant.username])
    if opd_consult.consult_at:
        consultant_data.append(['Date:', opd_consult.consult_at.strftime('%Y-%m-%d %H:%M:%S')])
    
    if consultant_data:
        consultant_table = Table(consultant_data, colWidths=[80 * mm, 100 * mm])
        consultant_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
        ]))
        story.append(consultant_table)
    
    # Footer
    story.append(Spacer(1, 10 * mm))
    story.append(Paragraph("Computer generated prescription - RIMS", styles['footer']))
    
    # Build PDF
    doc.build(story)
    
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    # Sanity check
    assert pdf_bytes[:4] == b'%PDF', "Generated PDF does not start with %PDF"
    
    return ContentFile(pdf_bytes, name=f"prescription_{service_visit.visit_id}.pdf")
