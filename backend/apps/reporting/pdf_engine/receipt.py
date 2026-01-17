"""
Receipt PDF generation using ReportLab
Supports both Visit (legacy) and ServiceVisit (workflow) models.
Dual-copy receipts: Patient Copy (top) + Office Copy (bottom) on one A4 page.
"""
from io import BytesIO
from django.core.files.base import ContentFile
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    Image,
    HRFlowable,
    KeepTogether,
    Flowable,
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.colors import black, white, HexColor
from .base import PDFBase, PDFStyles


# Locked clinic branding footer (fallback constant)
LOCKED_FOOTER_TEXT = "Adjacent Excel Labs, Near Arman Pan Shop Faisalabad Road Jaranwala\nFor information/Appointment: Tel: 041 4313 777 | WhatsApp: 03279640897"

# Clinic brand colors
CLINIC_BLUE = HexColor('#0B5ED7')
ACCENT_ORANGE = HexColor('#F39C12')
LIGHT_GREY = HexColor('#9AA0A6')


class DottedSeparator(Flowable):
    """Custom flowable for dotted tear separator line"""
    
    def __init__(self, width='100%', dash_length=3, gap_length=3, color=LIGHT_GREY):
        Flowable.__init__(self)
        self.width = width
        self.dash_length = dash_length
        self.gap_length = gap_length
        self.color = color
        self.height = 3 * mm
    
    def wrap(self, availWidth, availHeight):
        """Calculate the space needed"""
        if isinstance(self.width, str) and self.width.endswith('%'):
            percent = float(self.width[:-1])
            self.actual_width = availWidth * (percent / 100.0)
        else:
            self.actual_width = self.width if isinstance(self.width, (int, float)) else availWidth
        return (self.actual_width, self.height)
    
    def draw(self):
        """Draw the dotted line on the canvas"""
        canvas = self.canv
        canvas.saveState()
        canvas.setStrokeColor(self.color)
        canvas.setLineWidth(0.5)
        canvas.setDash([self.dash_length, self.gap_length])
        canvas.line(0, self.height / 2, self.actual_width, self.height / 2)
        canvas.restoreState()


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
    header_image_path = None
    footer_text = "Computer generated receipt"
    if receipt_settings:
        if receipt_settings.logo_image:
            logo_path = receipt_settings.logo_image.path if hasattr(receipt_settings.logo_image, 'path') else None
        if receipt_settings.header_image:
            header_image_path = receipt_settings.header_image.path if hasattr(receipt_settings.header_image, 'path') else None
        if receipt_settings.footer_text:
            footer_text = receipt_settings.footer_text
    
    # Build story (content)
    story = []
    
    # Header
    if header_image_path:
        header_image = Image(header_image_path)
        max_width = PDFBase.PAGE_WIDTH - PDFBase.MARGIN_LEFT - PDFBase.MARGIN_RIGHT
        if header_image.imageWidth and header_image.imageHeight:
            scale = max_width / header_image.imageWidth
            header_image.drawWidth = max_width
            header_image.drawHeight = header_image.imageHeight * scale
        story.append(header_image)
        story.append(Spacer(1, 4 * mm))
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
    
    # Footer note (footer_text already set from receipt_settings at top of function)
    story.append(Paragraph(footer_text, styles['footer']))
    
    # Build PDF
    doc.build(story)
    
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    # Sanity check: must start with %PDF
    assert pdf_bytes[:4] == b'%PDF', "Generated PDF does not start with %PDF"
    
    return ContentFile(pdf_bytes, name=f"receipt_{receipt_number}.pdf")


def build_service_visit_receipt_pdf_reportlab(service_visit, invoice) -> ContentFile:
    """
    Generate dual-copy receipt PDF for ServiceVisit (workflow) using ReportLab.
    Creates Patient copy (top) and Office copy (bottom) on one A4 page with dotted tear line.
    Locked specifications enforced: A4 portrait, two identical copies except labels, clinic branding.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=PDFBase.PAGE_SIZE)
    styles = PDFStyles.get_styles()
    base = PDFBase()
    receipt_settings = base.get_receipt_settings()
    logo_path = None
    header_image_path = None
    header_text = "Consultant Place Clinic"
    footer_text = LOCKED_FOOTER_TEXT  # Use locked footer as default
    
    if receipt_settings:
        if receipt_settings.logo_image:
            logo_path = receipt_settings.logo_image.path if hasattr(receipt_settings.logo_image, 'path') else None
        if receipt_settings.header_image:
            header_image_path = receipt_settings.header_image.path if hasattr(receipt_settings.header_image, 'path') else None
        if receipt_settings.header_text:
            header_text = receipt_settings.header_text
        # Use footer_text from settings if present; otherwise use locked constant
        if receipt_settings.footer_text and receipt_settings.footer_text.strip():
            footer_text = receipt_settings.footer_text
    
    receipt_number = invoice.receipt_number or service_visit.visit_id
    payment = service_visit.payments.first()
    
    # Create custom footer style (centered, light grey, no italics)
    footer_style = ParagraphStyle(
        'ReceiptFooter',
        parent=styles['body'],
        fontSize=8,
        textColor=LIGHT_GREY,
        alignment=1,  # CENTER
        fontName='Helvetica',
        spaceAfter=0,
        spaceBefore=0,
    )
    
    def build_receipt_section(copy_label: str):
        """
        Build a single receipt section ("Patient copy" or "Office copy").
        Each section is self-contained and bounded to fit on half A4 page.
        
        This inner helper captures variables from the enclosing scope:
        - receipt_settings, header_image_path, logo_path, footer_text, header_text
        - styles, service_visit, invoice, payment, receipt_number, footer_style
        
        If needed for testing or reuse, extract to module scope with explicit params.
        """
        section = []
        
        # Logo / Header Image
        if header_image_path:
            header_image = Image(header_image_path)
            max_width = PDFBase.PAGE_WIDTH - PDFBase.MARGIN_LEFT - PDFBase.MARGIN_RIGHT
            if header_image.imageWidth and header_image.imageHeight:
                scale = max_width / header_image.imageWidth
                header_image.drawWidth = max_width
                header_image.drawHeight = header_image.imageHeight * scale
            section.append(header_image)
            section.append(Spacer(1, 2 * mm))
        elif logo_path:
            logo = Image(logo_path)
            max_height = 15 * mm
            if logo.imageHeight and logo.imageWidth:
                scale = max_height / logo.imageHeight
                logo.drawHeight = max_height
                logo.drawWidth = logo.imageWidth * scale
            section.append(logo)
            section.append(Spacer(1, 2 * mm))
        
        # Clinic name header
        if header_text:
            clinic_header_style = ParagraphStyle(
                'ClinicHeader',
                parent=styles['title'],
                fontSize=14,
                fontName='Helvetica-Bold',
                textColor=black,
                alignment=1,  # CENTER
            )
            section.append(Paragraph(header_text, clinic_header_style))
        
        # RECEIPT title
        receipt_title_style = ParagraphStyle(
            'ReceiptTitle',
            parent=styles['title'],
            fontSize=16,
            fontName='Helvetica-Bold',
            textColor=black,
            alignment=1,  # CENTER
        )
        section.append(Paragraph("RECEIPT", receipt_title_style))
        
        # Copy label (Patient copy / Office copy) - exact casing enforced
        copy_label_style = ParagraphStyle(
            'CopyLabel',
            parent=styles['subheading'],
            fontSize=10,
            fontName='Helvetica-Bold',
            textColor=LIGHT_GREY,
            alignment=1,  # CENTER
        )
        section.append(Paragraph(copy_label, copy_label_style))
        section.append(Spacer(1, 4 * mm))
        
        # Receipt metadata
        metadata_data = [
            ['Receipt No:', receipt_number],
            ['Visit ID:', service_visit.visit_id],
            ['Date:', service_visit.registered_at.strftime('%Y-%m-%d %H:%M:%S')],
        ]
        if payment and payment.received_by:
            metadata_data.append(['Cashier:', payment.received_by.username])
        
        metadata_table = Table(metadata_data, colWidths=[70 * mm, 95 * mm])
        metadata_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        section.append(metadata_table)
        section.append(Spacer(1, 3 * mm))
        
        # Patient Information
        patient_heading_style = ParagraphStyle(
            'PatientHeading',
            parent=styles['heading'],
            fontSize=11,
            fontName='Helvetica-Bold',
            textColor=black,
        )
        section.append(Paragraph("Patient Information", patient_heading_style))
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
        
        patient_table = Table(patient_data, colWidths=[70 * mm, 95 * mm])
        patient_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        section.append(patient_table)
        section.append(Spacer(1, 3 * mm))
        
        # Service Information
        section.append(Paragraph("Service Information", patient_heading_style))
        items = service_visit.items.all()
        
        MAX_ITEMS_DISPLAY = 10  # Clamp displayed items to ensure fit on half page
        if items:
            service_rows = []
            item_list = list(items)
            display_items = item_list[:MAX_ITEMS_DISPLAY]
            
            for item in display_items:
                service_rows.append([item.service_name_snapshot, f"Rs. {item.price_snapshot:.2f}"])
            
            # If more items exist, add a summary row
            if len(item_list) > MAX_ITEMS_DISPLAY:
                remaining = len(item_list) - MAX_ITEMS_DISPLAY
                service_rows.append([f"(+ {remaining} more items)", ""])
            
            service_table = Table(
                [['Service', 'Amount']] + service_rows,
                colWidths=[115 * mm, 50 * mm]
            )
            # Clean clinic styling: blue header, subtle borders
            service_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('BACKGROUND', (0, 0), (-1, 0), CLINIC_BLUE),
                ('TEXTCOLOR', (0, 0), (-1, 0), white),
                ('GRID', (0, 0), (-1, -1), 0.5, LIGHT_GREY),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, HexColor('#F9F9F9')]),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            section.append(service_table)
        else:
            # Fallback for single service
            if service_visit.service:
                service_data = [
                    ['Service:', service_visit.service.name],
                    ['Code:', service_visit.service.code],
                ]
            else:
                service_data = [['Service:', 'Multiple Services']]
            service_table = Table(service_data, colWidths=[70 * mm, 95 * mm])
            service_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
            ]))
            section.append(service_table)
        section.append(Spacer(1, 3 * mm))
        
        # Payment Summary
        section.append(Paragraph("Payment Summary", patient_heading_style))
        amounts_data = [
            ['Total Amount:', f"Rs. {invoice.total_amount:.2f}"],
        ]
        
        if invoice.discount > 0:
            discount_label = "Discount"
            if invoice.discount_percentage:
                discount_label += f" ({invoice.discount_percentage:.2f}%)"
            amounts_data.append([f"{discount_label}:", f"Rs. {invoice.discount:.2f}"])
        
        # Net Amount row with orange accent (emphasized but print-friendly)
        net_amount_style = ParagraphStyle(
            'NetAmount',
            parent=styles['body'],
            fontSize=10,
            fontName='Helvetica-Bold',
            textColor=ACCENT_ORANGE,
        )
        amounts_data.append([
            Paragraph('<b>Net Amount:</b>', net_amount_style),
            Paragraph(f"<b>Rs. {invoice.net_amount:.2f}</b>", net_amount_style)
        ])
        amounts_data.append(['Paid Amount:', f"Rs. {payment.amount_paid if payment else invoice.net_amount:.2f}"])
        
        if invoice.balance_amount > 0:
            amounts_data.append(['Balance:', f"Rs. {invoice.balance_amount:.2f}"])
        
        amounts_data.append(['Payment Method:', (payment.method if payment else 'cash').upper()])
        
        amounts_table = Table(amounts_data, colWidths=[70 * mm, 95 * mm])
        amounts_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))
        section.append(amounts_table)
        section.append(Spacer(1, 4 * mm))
        
        # Footer (locked clinic details)
        section.append(Paragraph(footer_text.replace('\n', '<br/>'), footer_style))
        
        return KeepTogether(section)
    
    # Build story with dual copies and dotted separator
    story = []
    story.append(build_receipt_section("Patient copy"))
    story.append(Spacer(1, 3 * mm))
    story.append(DottedSeparator(width="100%", dash_length=3, gap_length=3, color=LIGHT_GREY))
    story.append(Spacer(1, 3 * mm))
    story.append(build_receipt_section("Office copy"))
    
    # Build PDF
    doc.build(story)
    
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    # Sanity check
    assert pdf_bytes[:4] == b'%PDF', "Generated PDF does not start with %PDF"
    
    return ContentFile(pdf_bytes, name=f"receipt_{receipt_number}.pdf")
