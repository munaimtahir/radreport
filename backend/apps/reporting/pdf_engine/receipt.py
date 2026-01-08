"""
Receipt PDF generation using ReportLab
Supports both Visit (legacy) and ServiceVisit (workflow) models.
"""
from io import BytesIO
from django.core.files.base import ContentFile
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.units import mm
from reportlab.lib.colors import black, white, HexColor
from .base import PDFBase, PDFStyles


def build_receipt_pdf_reportlab(visit) -> ContentFile:
    """
    Generate receipt PDF for Visit model using ReportLab.
    Replaces WeasyPrint-based build_receipt_pdf.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=PDFBase.PAGE_SIZE)
    styles = PDFStyles.get_styles()
    base = PDFBase()
    
    # Get receipt settings
    receipt_settings = base.get_receipt_settings()
    logo_path = None
    if receipt_settings and receipt_settings.logo_image:
        logo_path = receipt_settings.logo_image.path if hasattr(receipt_settings.logo_image, 'path') else None
    
    # Build story (content)
    story = []
    
    # Header
    if receipt_settings and receipt_settings.header_text:
        story.append(Paragraph(receipt_settings.header_text, styles['title']))
    else:
        story.append(Paragraph("RECEIPT", styles['title']))
    story.append(Spacer(1, 10 * mm))
    
    # Receipt metadata
    receipt_date = visit.receipt_generated_at or visit.created_at
    receipt_number = visit.receipt_number or visit.visit_number
    
    metadata_data = [
        ['Receipt No:', receipt_number],
        ['Date:', receipt_date.strftime('%Y-%m-%d %H:%M:%S')],
    ]
    if visit.created_by:
        metadata_data.append(['Cashier:', visit.created_by.get_full_name() or visit.created_by.username])
    
    metadata_table = Table(metadata_data, colWidths=[80 * mm, 100 * mm])
    metadata_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(metadata_table)
    story.append(Spacer(1, 8 * mm))
    
    # Patient Information
    story.append(Paragraph("Patient Information", styles['heading']))
    patient_data = [
        ['MR Number:', visit.patient.mrn],
        ['Name:', visit.patient.name],
    ]
    
    age_gender = []
    if visit.patient.age:
        age_gender.append(f"Age: {visit.patient.age}")
    if visit.patient.gender:
        age_gender.append(f"Gender: {visit.patient.gender}")
    if age_gender:
        patient_data.append(['Age/Gender:', ' | '.join(age_gender)])
    
    if visit.patient.phone:
        patient_data.append(['Mobile:', visit.patient.phone])
    
    patient_table = Table(patient_data, colWidths=[80 * mm, 100 * mm])
    patient_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(patient_table)
    story.append(Spacer(1, 8 * mm))
    
    # Services Table
    story.append(Paragraph("Services", styles['heading']))
    
    # Get items
    items = visit.items.select_related('service', 'service__modality').all()
    
    table_data = [['Service Name', 'Charge']]
    for item in items:
        service_name = f"{item.service.modality.code} - {item.service.name}"
        if item.indication:
            service_name += f"<br/><i>({item.indication[:70]})</i>"
        table_data.append([
            Paragraph(service_name, styles['body']),
            f"Rs. {item.charge:.2f}"
        ])
    
    services_table = Table(table_data, colWidths=[120 * mm, 60 * mm])
    services_table.setStyle(base.create_table_style())
    story.append(services_table)
    story.append(Spacer(1, 8 * mm))
    
    # Billing Summary
    story.append(Paragraph("Billing Summary", styles['heading']))
    
    summary_data = [
        ['Subtotal:', f"Rs. {visit.subtotal:.2f}"],
    ]
    
    if visit.discount_amount > 0:
        discount_label = "Discount"
        if visit.discount_percentage:
            discount_label += f" ({visit.discount_percentage}%)"
        summary_data.append([discount_label + ':', f"-Rs. {visit.discount_amount:.2f}"])
    
    summary_data.append(['<b>Net Total:</b>', f"<b>Rs. {visit.net_total:.2f}</b>"])
    summary_data.append(['Paid:', f"Rs. {visit.paid_amount:.2f}"])
    
    if visit.due_amount > 0:
        summary_data.append(['Due:', f"Rs. {visit.due_amount:.2f}"])
    elif visit.due_amount < 0:
        summary_data.append(['Change:', f"Rs. {abs(visit.due_amount):.2f}"])
    
    if visit.payment_method:
        summary_data.append(['Payment Method:', visit.payment_method.upper()])
    
    summary_table = Table(summary_data, colWidths=[80 * mm, 100 * mm])
    summary_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 10 * mm))
    
    # Footer note
    story.append(Paragraph("Computer generated receipt", styles['footer']))
    
    # Build PDF
    doc.build(story)
    
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    # Sanity check: must start with %PDF
    assert pdf_bytes[:4] == b'%PDF', "Generated PDF does not start with %PDF"
    
    return ContentFile(pdf_bytes, name=f"receipt_{receipt_number}.pdf")


def build_service_visit_receipt_pdf_reportlab(service_visit, invoice) -> ContentFile:
    """
    Generate receipt PDF for ServiceVisit (workflow) using ReportLab.
    Replaces WeasyPrint-based build_service_visit_receipt_pdf.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=PDFBase.PAGE_SIZE)
    styles = PDFStyles.get_styles()  # Use static method
    
    # Use existing receipt number from invoice (idempotent - should already be set)
    receipt_number = invoice.receipt_number or service_visit.visit_id
    
    # Get payment
    payment = service_visit.payments.first()
    
    # Build story
    story = []
    
    # Header
    story.append(Paragraph("RECEIPT", styles['title']))
    story.append(Spacer(1, 10 * mm))
    
    # Receipt metadata
    metadata_data = [
        ['Receipt No:', receipt_number],
        ['Visit ID:', service_visit.visit_id],
        ['Date:', service_visit.registered_at.strftime('%Y-%m-%d %H:%M:%S')],
    ]
    if payment and payment.received_by:
        metadata_data.append(['Cashier:', payment.received_by.username])
    
    metadata_table = Table(metadata_data, colWidths=[80 * mm, 100 * mm])
    metadata_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
    ]))
    story.append(metadata_table)
    story.append(Spacer(1, 8 * mm))
    
    # Patient Information
    story.append(Paragraph("Patient Information", styles['heading']))
    patient_data = [
        ['Patient Reg No:', service_visit.patient.patient_reg_no or service_visit.patient.mrn],
        ['MRN:', service_visit.patient.mrn],
        ['Name:', service_visit.patient.name],
    ]
    
    if service_visit.patient.age:
        patient_data.append(['Age:', str(service_visit.patient.age)])
    if service_visit.patient.gender:
        patient_data.append(['Gender:', service_visit.patient.gender])
    if service_visit.patient.phone:
        patient_data.append(['Phone:', service_visit.patient.phone])
    
    patient_table = Table(patient_data, colWidths=[80 * mm, 100 * mm])
    patient_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
    ]))
    story.append(patient_table)
    story.append(Spacer(1, 8 * mm))
    
    # Service Information - use items (multiple services supported)
    story.append(Paragraph("Service Information", styles['heading']))
    items = service_visit.items.all()
    if items:
        service_rows = []
        for item in items:
            service_rows.append([item.service_name_snapshot, f"Rs. {item.price_snapshot:.2f}"])
        service_table = Table(
            [['Service', 'Amount']] + service_rows,
            colWidths=[120 * mm, 60 * mm]
        )
        service_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#E0E0E0')),
            ('GRID', (0, 0), (-1, -1), 1, black),
        ]))
        story.append(service_table)
    else:
        # Fallback for legacy data
        if service_visit.service:
            service_data = [
                ['Service:', service_visit.service.name],
                ['Code:', service_visit.service.code],
            ]
        else:
            service_data = [['Service:', 'Multiple Services']]
        service_table = Table(service_data, colWidths=[80 * mm, 100 * mm])
        service_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
        ]))
        story.append(service_table)
    story.append(Spacer(1, 8 * mm))
    
    # Amounts
    story.append(Paragraph("Payment Summary", styles['heading']))
    amounts_data = [
        ['Total Amount:', f"Rs. {invoice.total_amount:.2f}"],
    ]
    
    if invoice.discount > 0:
        amounts_data.append(['Discount:', f"Rs. {invoice.discount:.2f}"])
    
    amounts_data.append(['<b>Net Amount:</b>', f"<b>Rs. {invoice.net_amount:.2f}</b>"])
    amounts_data.append(['Paid Amount:', f"Rs. {payment.amount_paid if payment else invoice.net_amount:.2f}"])
    
    if invoice.balance_amount > 0:
        amounts_data.append(['Balance:', f"Rs. {invoice.balance_amount:.2f}"])
    
    amounts_data.append(['Payment Method:', (payment.method if payment else 'cash').upper()])
    
    amounts_table = Table(amounts_data, colWidths=[80 * mm, 100 * mm])
    amounts_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
    ]))
    story.append(amounts_table)
    story.append(Spacer(1, 10 * mm))
    
    # Footer
    story.append(Paragraph("Computer generated receipt", styles['footer']))
    
    # Build PDF
    doc.build(story)
    
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    # Sanity check
    assert pdf_bytes[:4] == b'%PDF', "Generated PDF does not start with %PDF"
    
    return ContentFile(pdf_bytes, name=f"receipt_{receipt_number}.pdf")
