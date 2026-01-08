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
    PHASE D: Generate USG report PDF using canonical template structure.
    Layout matches canonical standard exactly:
    1) Header: facility+logo, auto study title, report status
    2) Patient & Order Details
    3) Exam Metadata
    4) Scan Quality & Limitations (MANDATORY)
    5) Findings: structured organ-wise modules
    6) Impression (MANDATORY)
    7) Suggestions/Follow-up (OPTIONAL)
    8) Critical Result Communication (CONDITIONAL)
    9) Sign-off
    """
    from django.utils import timezone
    
    # Get service visit (prefer from item, fallback to legacy)
    service_visit = usg_report.service_visit_item.service_visit if usg_report.service_visit_item else usg_report.service_visit
    patient = service_visit.patient
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=PDFBase.PAGE_SIZE)
    styles = PDFStyles.get_styles()
    base = PDFBase()
    
    # Build story
    story = []
    
    # 1) HEADER: Facility + Logo + Auto Study Title + Report Status
    story.append(Paragraph("ULTRASOUND REPORT", styles['title']))
    
    # Study title and status
    study_title = usg_report.study_title or "Ultrasound Study"
    status_badge = usg_report.report_status
    if usg_report.report_status == "AMENDED":
        status_badge = f"AMENDED (Version {usg_report.version})"
    
    header_data = [
        ['Study Title:', study_title],
        ['Report Status:', status_badge],
    ]
    if usg_report.version > 1:
        header_data.append(['Version:', str(usg_report.version)])
    
    header_table = Table(header_data, colWidths=[80 * mm, 100 * mm])
    header_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 10 * mm))
    
    # 2) PATIENT & ORDER DETAILS
    story.append(Paragraph("Patient & Order Details", styles['heading']))
    patient_data = [
        ['Patient Reg No:', patient.patient_reg_no or patient.mrn or 'N/A'],
        ['Name:', patient.name],
    ]
    if patient.age:
        patient_data.append(['Age:', str(patient.age)])
    if patient.gender:
        patient_data.append(['Gender:', patient.gender])
    
    # Order details
    if usg_report.service_visit_item:
        service_name = usg_report.service_visit_item.service_name_snapshot or 'N/A'
        patient_data.append(['Service:', service_name])
    
    if usg_report.referring_clinician:
        patient_data.append(['Referring Clinician:', usg_report.referring_clinician])
    
    patient_table = Table(patient_data, colWidths=[80 * mm, 100 * mm])
    patient_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
    ]))
    story.append(patient_table)
    story.append(Spacer(1, 8 * mm))
    
    # Clinical History/Indication
    if usg_report.clinical_history:
        story.append(Paragraph("Clinical History/Indication", styles['subheading']))
        for line in str(usg_report.clinical_history).splitlines():
            if line.strip():
                story.append(Paragraph(line.strip(), styles['body']))
        story.append(Spacer(1, 6 * mm))
    
    # Clinical Questions
    if usg_report.clinical_questions:
        story.append(Paragraph("Clinical Questions", styles['subheading']))
        for line in str(usg_report.clinical_questions).splitlines():
            if line.strip():
                story.append(Paragraph(line.strip(), styles['body']))
        story.append(Spacer(1, 6 * mm))
    
    # 3) EXAM METADATA
    story.append(Paragraph("Exam Metadata", styles['heading']))
    exam_data = []
    
    if usg_report.exam_datetime:
        exam_data.append(['Exam Date/Time:', usg_report.exam_datetime.strftime('%Y-%m-%d %H:%M:%S')])
    if usg_report.report_datetime:
        exam_data.append(['Report Date/Time:', usg_report.report_datetime.strftime('%Y-%m-%d %H:%M:%S')])
    if usg_report.study_type:
        exam_data.append(['Study Type:', usg_report.study_type])
    
    # Technique
    technique_parts = []
    if usg_report.technique_approach:
        technique_parts.append(usg_report.technique_approach)
    if usg_report.doppler_used:
        technique_parts.append("Doppler")
    if usg_report.contrast_used:
        technique_parts.append("Contrast")
    if technique_parts:
        exam_data.append(['Technique:', ', '.join(technique_parts)])
    if usg_report.technique_notes:
        exam_data.append(['Technique Notes:', usg_report.technique_notes])
    
    if usg_report.performed_by:
        exam_data.append(['Performed By:', usg_report.performed_by.get_full_name() or usg_report.performed_by.username])
    if usg_report.interpreted_by:
        exam_data.append(['Interpreted By:', usg_report.interpreted_by.get_full_name() or usg_report.interpreted_by.username])
    
    if exam_data:
        exam_table = Table(exam_data, colWidths=[80 * mm, 100 * mm])
        exam_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
        ]))
        story.append(exam_table)
        story.append(Spacer(1, 8 * mm))
    
    if usg_report.comparison:
        story.append(Paragraph("Comparison", styles['subheading']))
        for line in str(usg_report.comparison).splitlines():
            if line.strip():
                story.append(Paragraph(line.strip(), styles['body']))
        story.append(Spacer(1, 6 * mm))
    
    # 4) SCAN QUALITY & LIMITATIONS (MANDATORY)
    story.append(Paragraph("Scan Quality & Limitations", styles['heading']))
    quality_data = [
        ['Scan Quality:', usg_report.scan_quality or 'Not specified'],
        ['Limitations:', usg_report.limitations_text or 'None specified'],
    ]
    quality_table = Table(quality_data, colWidths=[80 * mm, 100 * mm])
    quality_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
    ]))
    story.append(quality_table)
    story.append(Spacer(1, 10 * mm))
    
    # 5) FINDINGS: Structured organ-wise modules
    story.append(Paragraph("Findings", styles['heading']))
    
    # Render findings_json as structured organ modules
    findings_json = usg_report.findings_json or {}
    if findings_json:
        for organ, organ_data in findings_json.items():
            if organ_data:
                story.append(Paragraph(f"{organ.replace('_', ' ').title()}", styles['subheading']))
                if isinstance(organ_data, dict):
                    for key, value in organ_data.items():
                        if value:
                            label = key.replace('_', ' ').title()
                            story.append(Paragraph(f"{label}: {value}", styles['body']))
                elif isinstance(organ_data, str):
                    for line in organ_data.splitlines():
                        if line.strip():
                            story.append(Paragraph(line.strip(), styles['body']))
                story.append(Spacer(1, 4 * mm))
    else:
        # Fallback to legacy report_json
        legacy_findings = usg_report.report_json.get('findings', '') if isinstance(usg_report.report_json, dict) else ''
        if legacy_findings:
            for line in str(legacy_findings).splitlines():
                if line.strip():
                    story.append(Paragraph(line.strip(), styles['body']))
    
    # Measurements summary table (if available)
    measurements = usg_report.measurements_json
    if measurements and isinstance(measurements, list) and len(measurements) > 0:
        story.append(Spacer(1, 6 * mm))
        story.append(Paragraph("Measurements Summary", styles['subheading']))
        # Create table from measurements
        if isinstance(measurements[0], dict):
            headers = list(measurements[0].keys())
            table_data = [headers]
            for m in measurements:
                table_data.append([str(m.get(h, '')) for h in headers])
            measurements_table = Table(table_data, colWidths=[180 * mm / len(headers)] * len(headers))
            measurements_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), '#E0E0E0'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, '#CCCCCC'),
            ]))
            story.append(measurements_table)
    
    story.append(Spacer(1, 10 * mm))
    
    # 6) IMPRESSION (MANDATORY)
    story.append(Paragraph("Impression", styles['heading']))
    impression_text = usg_report.impression_text or ''
    if not impression_text:
        # Fallback to legacy
        impression_text = usg_report.report_json.get('impression', '') if isinstance(usg_report.report_json, dict) else ''
    
    if impression_text:
        for line in str(impression_text).splitlines():
            if line.strip():
                story.append(Paragraph(line.strip(), styles['body']))
    else:
        story.append(Paragraph("No impression provided", styles['body']))
    story.append(Spacer(1, 10 * mm))
    
    # 7) SUGGESTIONS/FOLLOW-UP (OPTIONAL)
    if usg_report.suggestions_text:
        story.append(Paragraph("Suggestions/Follow-up", styles['heading']))
        for line in str(usg_report.suggestions_text).splitlines():
            if line.strip():
                story.append(Paragraph(line.strip(), styles['body']))
        story.append(Spacer(1, 10 * mm))
    
    # 8) CRITICAL RESULT COMMUNICATION (CONDITIONAL)
    if usg_report.critical_flag:
        story.append(Paragraph("CRITICAL RESULT COMMUNICATION", styles['heading']))
        comm = usg_report.critical_communication_json or {}
        comm_data = []
        if comm.get('recipient'):
            comm_data.append(['Recipient:', comm['recipient']])
        if comm.get('method'):
            comm_data.append(['Method:', comm['method']])
        if comm.get('communicated_at'):
            comm_data.append(['Communicated At:', comm['communicated_at']])
        if comm.get('notes'):
            comm_data.append(['Notes:', comm['notes']])
        
        if comm_data:
            comm_table = Table(comm_data, colWidths=[80 * mm, 100 * mm])
            comm_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BACKGROUND', (0, 0), (-1, -1), '#FFE0E0'),
            ]))
            story.append(comm_table)
        story.append(Spacer(1, 10 * mm))
    
    # 9) SIGN-OFF
    story.append(Paragraph("Sign-off", styles['heading']))
    signoff = usg_report.signoff_json or {}
    signoff_data = []
    
    if signoff.get('clinician_name'):
        signoff_data.append(['Interpreting Clinician:', signoff['clinician_name']])
    elif usg_report.verifier:
        signoff_data.append(['Interpreting Clinician:', usg_report.verifier.get_full_name() or usg_report.verifier.username])
    
    if signoff.get('credentials'):
        signoff_data.append(['Credentials:', signoff['credentials']])
    
    if signoff.get('verified_at'):
        signoff_data.append(['Verified At:', signoff['verified_at']])
    elif usg_report.verified_at:
        signoff_data.append(['Verified At:', usg_report.verified_at.strftime('%Y-%m-%d %H:%M:%S')])
    
    if signoff_data:
        signoff_table = Table(signoff_data, colWidths=[80 * mm, 100 * mm])
        signoff_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
        ]))
        story.append(signoff_table)
    
    # Amendment history (if amended)
    if usg_report.report_status == "AMENDED" and usg_report.amendment_reason:
        story.append(Spacer(1, 6 * mm))
        story.append(Paragraph("Amendment Information", styles['subheading']))
        story.append(Paragraph(f"Amendment Reason: {usg_report.amendment_reason}", styles['body']))
        if usg_report.parent_report_id:
            story.append(Paragraph(f"Parent Report ID: {usg_report.parent_report_id}", styles['body']))
    
    # Footer
    story.append(Spacer(1, 10 * mm))
    story.append(Paragraph("Computer generated report - RIMS", styles['footer']))
    
    # Build PDF
    doc.build(story)
    
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    # Sanity check
    assert pdf_bytes[:4] == b'%PDF', "Generated PDF does not start with %PDF"
    
    return ContentFile(pdf_bytes, name=f"usg_report_{service_visit.visit_id}_v{usg_report.version}.pdf")


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
