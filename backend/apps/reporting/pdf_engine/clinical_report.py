"""
Clinical/Diagnostic Report PDF generation using ReportLab
Supports USG reports and other diagnostic reports.
"""
from io import BytesIO
from django.core.files.base import ContentFile
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.units import mm
from reportlab.lib.colors import black
from .base import PDFBase, PDFStyles


def build_clinical_report_pdf(usg_report) -> ContentFile:
    """
    Generate USG/clinical report PDF using ReportLab.
    Replaces WeasyPrint-based build_usg_report_pdf.
    """
    service_visit = usg_report.service_visit
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=PDFBase.PAGE_SIZE)
    styles = PDFStyles.get_styles()
    base = PDFBase()
    
    # Build story
    story = []
    
    # Header
    story.append(Paragraph("ULTRASOUND REPORT", styles['title']))
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
    story.append(Spacer(1, 8 * mm))
    
    # Service Information
    story.append(Paragraph("Service Information", styles['heading']))
    service_data = [
        ['Service:', service_visit.service.name],
        ['Code:', service_visit.service.code],
    ]
    service_table = Table(service_data, colWidths=[80 * mm, 100 * mm])
    service_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
    ]))
    story.append(service_table)
    story.append(Spacer(1, 10 * mm))
    
    # Report Data (from JSON)
    report_data = usg_report.report_json if isinstance(usg_report.report_json, dict) else {}
    
    # Findings
    if report_data.get('findings') or hasattr(usg_report, 'findings'):
        story.append(Paragraph("Findings", styles['heading']))
        findings_text = report_data.get('findings', '') or getattr(usg_report, 'findings', '')
        if findings_text:
            # Split into paragraphs
            for line in str(findings_text).splitlines():
                if line.strip():
                    story.append(Paragraph(line.strip(), styles['body']))
        story.append(Spacer(1, 8 * mm))
    
    # Impression
    if report_data.get('impression') or hasattr(usg_report, 'impression'):
        story.append(Paragraph("Impression", styles['heading']))
        impression_text = report_data.get('impression', '') or getattr(usg_report, 'impression', '')
        if impression_text:
            for line in str(impression_text).splitlines():
                if line.strip():
                    story.append(Paragraph(line.strip(), styles['body']))
        story.append(Spacer(1, 8 * mm))
    
    # Additional report fields from JSON
    for key, value in report_data.items():
        if key not in ['findings', 'impression'] and value:
            story.append(Paragraph(key.replace('_', ' ').title(), styles['subheading']))
            if isinstance(value, (list, dict)):
                value = str(value)
            for line in str(value).splitlines():
                if line.strip():
                    story.append(Paragraph(line.strip(), styles['body']))
            story.append(Spacer(1, 6 * mm))
    
    story.append(Spacer(1, 10 * mm))
    
    # Signatures
    signature_data = []
    if usg_report.created_by:
        signature_data.append(['Reported by:', usg_report.created_by.username])
    if usg_report.verifier:
        signature_data.append(['Verified by:', usg_report.verifier.username])
        if usg_report.verified_at:
            signature_data.append(['Verified at:', usg_report.verified_at.strftime('%Y-%m-%d %H:%M:%S')])
    
    if signature_data:
        signature_table = Table(signature_data, colWidths=[80 * mm, 100 * mm])
        signature_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
        ]))
        story.append(signature_table)
    
    # Footer
    story.append(Spacer(1, 10 * mm))
    story.append(Paragraph("Computer generated report - RIMS", styles['footer']))
    
    # Build PDF
    doc.build(story)
    
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    # Sanity check
    assert pdf_bytes[:4] == b'%PDF', "Generated PDF does not start with %PDF"
    
    return ContentFile(pdf_bytes, name=f"usg_report_{service_visit.visit_id}.pdf")


def build_basic_report_pdf(report) -> ContentFile:
    """
    Generate basic clinical report PDF for Report model.
    Enhanced version of build_basic_pdf using ReportLab.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=PDFBase.PAGE_SIZE)
    styles = PDFStyles.get_styles()
    base = PDFBase()
    
    # Build story
    story = []
    
    # Header
    story.append(Paragraph("Radiology Report", styles['title']))
    story.append(Spacer(1, 10 * mm))
    
    # Study Information
    study = report.study
    story.append(Paragraph("Study Information", styles['heading']))
    study_data = [
        ['Accession:', study.accession],
        ['Patient:', f"{study.patient.name} | MRN: {study.patient.mrn}"],
        ['Service:', f"{study.service.name} ({study.service.modality.code})"],
    ]
    study_table = Table(study_data, colWidths=[80 * mm, 100 * mm])
    study_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
    ]))
    story.append(study_table)
    story.append(Spacer(1, 10 * mm))
    
    # Findings
    if report.narrative:
        story.append(Paragraph("Findings", styles['heading']))
        for line in str(report.narrative).splitlines()[:40]:
            if line.strip():
                story.append(Paragraph(line.strip()[:110], styles['body']))
        story.append(Spacer(1, 8 * mm))
    
    # Impression
    if report.impression:
        story.append(Paragraph("Impression", styles['heading']))
        for line in str(report.impression).splitlines()[:20]:
            if line.strip():
                story.append(Paragraph(line.strip()[:110], styles['body']))
        story.append(Spacer(1, 8 * mm))
    
    # Footer
    story.append(Spacer(1, 10 * mm))
    story.append(Paragraph("Computer generated report - RIMS", styles['footer']))
    
    # Build PDF
    doc.build(story)
    
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    # Sanity check
    assert pdf_bytes[:4] == b'%PDF', "Generated PDF does not start with %PDF"
    
    return ContentFile(pdf_bytes, name=f"{study.accession}.pdf")
