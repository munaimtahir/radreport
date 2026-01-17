"""
Receipt PDF generation using ReportLab
COMPACT SINGLE-PAGE RECEIPT FORMAT (Not Dual-Copy A4)
Supports both Visit (legacy) and ServiceVisit (workflow) models.
"""
import logging
from io import BytesIO
from django.core.files.base import ContentFile
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    Flowable,
)
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm, inch
from reportlab.lib.colors import black, white, HexColor
from .base import PDFBase, PDFStyles

# Configure logging
logger = logging.getLogger(__name__)

# Locked clinic branding footer (fallback constant)
LOCKED_FOOTER_TEXT = "Adjacent Excel Labs, Near Arman Pan Shop Faisalabad Road Jaranwala\nFor information/Appointment: Tel: 041 4313 777 | WhatsApp: 03279640897"

# Clinic brand colors
CLINIC_BLUE = HexColor('#0B5ED7')
ACCENT_ORANGE = HexColor('#F39C12')
LIGHT_GREY = HexColor('#9AA0A6')
BORDER_GREY = HexColor('#E5E7EB')

# Compact receipt page size (80mm thermal receipt width, but on standard page)
# We'll use A5 landscape or Letter size with reduced margins for a compact receipt
COMPACT_PAGE_WIDTH = 210 * mm  # A4 width
COMPACT_PAGE_HEIGHT = 148 * mm  # A5 height (half of A4)
COMPACT_MARGIN = 10 * mm


def build_receipt_pdf_reportlab(visit) -> ContentFile:
    """
    Generate COMPACT single-page receipt PDF for Visit model using ReportLab.
    Format: Compact single receipt (not dual-copy A4).
    """
    logger.info(f"[RECEIPT PDF] Starting receipt generation for Visit ID: {getattr(visit, 'visit_number', 'N/A')}")
    logger.info(f"[RECEIPT PDF] Patient: {visit.patient.name} (MRN: {visit.patient.mrn})")
    
    buffer = BytesIO()
    
    # Use compact page size
    doc = SimpleDocTemplate(
        buffer,
        pagesize=(COMPACT_PAGE_WIDTH, COMPACT_PAGE_HEIGHT),
        leftMargin=COMPACT_MARGIN,
        rightMargin=COMPACT_MARGIN,
        topMargin=COMPACT_MARGIN,
        bottomMargin=COMPACT_MARGIN,
    )
    
    logger.info(f"[RECEIPT PDF] Page size: {COMPACT_PAGE_WIDTH/mm:.1f}mm x {COMPACT_PAGE_HEIGHT/mm:.1f}mm")
    
    styles = PDFStyles.get_styles()
    base = PDFBase()
    
    # Get receipt settings
    logger.info("[RECEIPT PDF] Loading receipt settings...")
    receipt_settings = base.get_receipt_settings()
    logo_path = None
    header_text = "Consultants Place Clinic"
    footer_text = "Computer generated receipt"
    
    if receipt_settings:
        logger.info("[RECEIPT PDF] Receipt settings found")
        if receipt_settings.logo_image:
            logo_path = receipt_settings.logo_image.path if hasattr(receipt_settings.logo_image, 'path') else None
            logger.info(f"[RECEIPT PDF] Logo path: {logo_path}")
        if receipt_settings.header_text:
            header_text = receipt_settings.header_text
            logger.info(f"[RECEIPT PDF] Header text: {header_text}")
        if receipt_settings.footer_text:
            footer_text = receipt_settings.footer_text
            logger.info(f"[RECEIPT PDF] Footer text (first 50 chars): {footer_text[:50]}...")
    else:
        logger.warning("[RECEIPT PDF] No receipt settings found, using defaults")
    
    # Build story (content)
    story = []
    
    # Header with logo and clinic name
    logger.info("[RECEIPT PDF] Building header...")
    if logo_path:
        try:
            logo = Image(logo_path)
            max_height = 20 * mm
            if logo.imageHeight and logo.imageWidth:
                scale = max_height / logo.imageHeight
                logo.drawHeight = max_height
                logo.drawWidth = logo.imageWidth * scale
            story.append(logo)
            story.append(Spacer(1, 2 * mm))
            logger.info(f"[RECEIPT PDF] Logo added: {logo.drawWidth/mm:.1f}mm x {logo.drawHeight/mm:.1f}mm")
        except Exception as e:
            logger.error(f"[RECEIPT PDF] Failed to load logo: {e}")
    
    # Clinic name header (centered, bold, blue)
    clinic_header_style = ParagraphStyle(
        'ClinicHeader',
        parent=styles['title'],
        fontSize=14,
        fontName='Helvetica-Bold',
        textColor=CLINIC_BLUE,
        alignment=1,  # CENTER
    )
    story.append(Paragraph(header_text, clinic_header_style))
    
    # RECEIPT title
    receipt_title_style = ParagraphStyle(
        'ReceiptTitle',
        parent=styles['title'],
        fontSize=12,
        fontName='Helvetica-Bold',
        textColor=black,
        alignment=1,  # CENTER
    )
    story.append(Paragraph("RECEIPT", receipt_title_style))
    story.append(Spacer(1, 3 * mm))
    
    logger.info("[RECEIPT PDF] Building receipt metadata...")
    # Receipt metadata
    receipt_date = visit.receipt_generated_at or visit.created_at
    receipt_number = visit.receipt_number or visit.visit_number
    
    logger.info(f"[RECEIPT PDF] Receipt Number: {receipt_number}")
    logger.info(f"[RECEIPT PDF] Receipt Date: {receipt_date}")
    
    metadata_data = [
        ['Receipt No:', receipt_number],
        ['Date:', receipt_date.strftime('%Y-%m-%d %H:%M:%S')],
    ]
    if visit.created_by:
        cashier_name = visit.created_by.get_full_name() or visit.created_by.username
        metadata_data.append(['Cashier:', cashier_name])
        logger.info(f"[RECEIPT PDF] Cashier: {cashier_name}")
    
    content_width = COMPACT_PAGE_WIDTH - 2 * COMPACT_MARGIN
    metadata_table = Table(metadata_data, colWidths=[content_width * 0.4, content_width * 0.6])
    metadata_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TEXTCOLOR', (0, 0), (0, -1), LIGHT_GREY),
    ]))
    story.append(metadata_table)
    story.append(Spacer(1, 4 * mm))
    
    # Patient Information
    logger.info("[RECEIPT PDF] Building patient information...")
    patient_heading_style = ParagraphStyle(
        'PatientHeading',
        parent=styles['heading'],
        fontSize=10,
        fontName='Helvetica-Bold',
        textColor=CLINIC_BLUE,
    )
    story.append(Paragraph("Patient Information", patient_heading_style))
    story.append(Spacer(1, 1 * mm))
    
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
    
    logger.info(f"[RECEIPT PDF] Patient: {visit.patient.name}, MRN: {visit.patient.mrn}")
    
    patient_table = Table(patient_data, colWidths=[content_width * 0.4, content_width * 0.6])
    patient_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TEXTCOLOR', (0, 0), (0, -1), LIGHT_GREY),
    ]))
    story.append(patient_table)
    story.append(Spacer(1, 4 * mm))
    
    # Services Table
    logger.info("[RECEIPT PDF] Building services table...")
    story.append(Paragraph("Services", patient_heading_style))
    story.append(Spacer(1, 1 * mm))
    
    # Get items
    items = visit.items.select_related('service', 'service__modality').all()
    logger.info(f"[RECEIPT PDF] Number of service items: {items.count()}")
    
    table_data = [['Service Name', 'Charge']]
    for idx, item in enumerate(items):
        service_name = f"{item.service.modality.code} - {item.service.name}"
        if item.indication:
            indication_text = item.indication[:50] + "..." if len(item.indication) > 50 else item.indication
            service_name += f"<br/><font size='7'><i>({indication_text})</i></font>"
        table_data.append([
            Paragraph(service_name, styles['body']),
            f"Rs. {item.charge:.2f}"
        ])
        logger.info(f"[RECEIPT PDF]   Item {idx+1}: {item.service.name} - Rs. {item.charge:.2f}")
    
    services_table = Table(table_data, colWidths=[content_width * 0.65, content_width * 0.35])
    services_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BACKGROUND', (0, 0), (-1, 0), CLINIC_BLUE),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_GREY),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(services_table)
    story.append(Spacer(1, 4 * mm))
    
    # Billing Summary
    logger.info("[RECEIPT PDF] Building billing summary...")
    story.append(Paragraph("Billing Summary", patient_heading_style))
    story.append(Spacer(1, 1 * mm))
    
    summary_data = [
        ['Subtotal:', f"Rs. {visit.subtotal:.2f}"],
    ]
    
    logger.info(f"[RECEIPT PDF] Subtotal: Rs. {visit.subtotal:.2f}")
    
    if visit.discount_amount > 0:
        discount_label = "Discount"
        if visit.discount_percentage:
            discount_label += f" ({visit.discount_percentage}%)"
        summary_data.append([discount_label + ':', f"-Rs. {visit.discount_amount:.2f}"])
        logger.info(f"[RECEIPT PDF] Discount: Rs. {visit.discount_amount:.2f}")
    
    # Net total with accent color
    net_total_style = ParagraphStyle(
        'NetTotal',
        parent=styles['body'],
        fontSize=10,
        fontName='Helvetica-Bold',
        textColor=ACCENT_ORANGE,
    )
    summary_data.append([
        Paragraph('<b>Net Total:</b>', net_total_style),
        Paragraph(f"<b>Rs. {visit.net_total:.2f}</b>", net_total_style)
    ])
    logger.info(f"[RECEIPT PDF] Net Total: Rs. {visit.net_total:.2f}")
    
    summary_data.append(['Paid:', f"Rs. {visit.paid_amount:.2f}"])
    logger.info(f"[RECEIPT PDF] Paid Amount: Rs. {visit.paid_amount:.2f}")
    
    if visit.due_amount > 0:
        summary_data.append(['Due:', f"Rs. {visit.due_amount:.2f}"])
        logger.info(f"[RECEIPT PDF] Due Amount: Rs. {visit.due_amount:.2f}")
    elif visit.due_amount < 0:
        summary_data.append(['Change:', f"Rs. {abs(visit.due_amount):.2f}"])
        logger.info(f"[RECEIPT PDF] Change: Rs. {abs(visit.due_amount):.2f}")
    
    if visit.payment_method:
        summary_data.append(['Payment Method:', visit.payment_method.upper()])
        logger.info(f"[RECEIPT PDF] Payment Method: {visit.payment_method}")
    
    summary_table = Table(summary_data, colWidths=[content_width * 0.5, content_width * 0.5])
    summary_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('TEXTCOLOR', (0, 0), (0, -1), LIGHT_GREY),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 5 * mm))
    
    # Footer note
    logger.info("[RECEIPT PDF] Adding footer...")
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['body'],
        fontSize=7,
        textColor=LIGHT_GREY,
        alignment=1,  # CENTER
        fontName='Helvetica',
    )
    story.append(Paragraph(footer_text.replace('\n', '<br/>'), footer_style))
    
    # Build PDF
    logger.info("[RECEIPT PDF] Building PDF document...")
    try:
        doc.build(story)
        logger.info("[RECEIPT PDF] PDF document built successfully")
    except Exception as e:
        logger.error(f"[RECEIPT PDF] Failed to build PDF: {e}", exc_info=True)
        raise
    
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    logger.info(f"[RECEIPT PDF] PDF size: {len(pdf_bytes)} bytes")
    
    # Sanity check: must start with %PDF
    if pdf_bytes[:4] != b'%PDF':
        logger.error("[RECEIPT PDF] Generated PDF does not start with %PDF signature!")
        raise ValueError("Generated PDF is invalid")
    
    logger.info(f"[RECEIPT PDF] Receipt PDF generation completed successfully for receipt {receipt_number}")
    
    return ContentFile(pdf_bytes, name=f"receipt_{receipt_number}.pdf")


def build_service_visit_receipt_pdf_reportlab(service_visit, invoice) -> ContentFile:
    """
    Generate COMPACT single-page receipt PDF for ServiceVisit (workflow) using ReportLab.
    Format: Compact single receipt (not dual-copy A4).
    """
    logger.info(f"[RECEIPT PDF] Starting ServiceVisit receipt generation for Visit ID: {service_visit.visit_id}")
    logger.info(f"[RECEIPT PDF] Patient: {service_visit.patient.name} (MRN: {service_visit.patient.mrn})")
    
    buffer = BytesIO()
    
    # Use compact page size
    doc = SimpleDocTemplate(
        buffer,
        pagesize=(COMPACT_PAGE_WIDTH, COMPACT_PAGE_HEIGHT),
        leftMargin=COMPACT_MARGIN,
        rightMargin=COMPACT_MARGIN,
        topMargin=COMPACT_MARGIN,
        bottomMargin=COMPACT_MARGIN,
    )
    
    logger.info(f"[RECEIPT PDF] Page size: {COMPACT_PAGE_WIDTH/mm:.1f}mm x {COMPACT_PAGE_HEIGHT/mm:.1f}mm")
    
    styles = PDFStyles.get_styles()
    base = PDFBase()
    
    # Get receipt settings
    logger.info("[RECEIPT PDF] Loading receipt settings...")
    receipt_settings = base.get_receipt_settings()
    logo_path = None
    header_text = "Consultants Place Clinic"
    footer_text = LOCKED_FOOTER_TEXT
    
    if receipt_settings:
        logger.info("[RECEIPT PDF] Receipt settings found")
        if receipt_settings.logo_image:
            logo_path = receipt_settings.logo_image.path if hasattr(receipt_settings.logo_image, 'path') else None
            logger.info(f"[RECEIPT PDF] Logo path: {logo_path}")
        if receipt_settings.header_text:
            header_text = receipt_settings.header_text
            logger.info(f"[RECEIPT PDF] Header text: {header_text}")
        if receipt_settings.footer_text and receipt_settings.footer_text.strip():
            footer_text = receipt_settings.footer_text
            logger.info(f"[RECEIPT PDF] Footer text (first 50 chars): {footer_text[:50]}...")
    else:
        logger.warning("[RECEIPT PDF] No receipt settings found, using defaults")
    
    receipt_number = invoice.receipt_number or service_visit.visit_id
    payment = service_visit.payments.first()
    
    logger.info(f"[RECEIPT PDF] Receipt Number: {receipt_number}")
    logger.info(f"[RECEIPT PDF] Payment found: {payment is not None}")
    
    # Build story
    story = []
    
    # Header with logo and clinic name
    logger.info("[RECEIPT PDF] Building header...")
    if logo_path:
        try:
            logo = Image(logo_path)
            max_height = 20 * mm
            if logo.imageHeight and logo.imageWidth:
                scale = max_height / logo.imageHeight
                logo.drawHeight = max_height
                logo.drawWidth = logo.imageWidth * scale
            story.append(logo)
            story.append(Spacer(1, 2 * mm))
            logger.info(f"[RECEIPT PDF] Logo added: {logo.drawWidth/mm:.1f}mm x {logo.drawHeight/mm:.1f}mm")
        except Exception as e:
            logger.error(f"[RECEIPT PDF] Failed to load logo: {e}")
    
    # Clinic name header
    clinic_header_style = ParagraphStyle(
        'ClinicHeader',
        parent=styles['title'],
        fontSize=14,
        fontName='Helvetica-Bold',
        textColor=CLINIC_BLUE,
        alignment=1,  # CENTER
    )
    story.append(Paragraph(header_text, clinic_header_style))
    
    # RECEIPT title
    receipt_title_style = ParagraphStyle(
        'ReceiptTitle',
        parent=styles['title'],
        fontSize=12,
        fontName='Helvetica-Bold',
        textColor=black,
        alignment=1,  # CENTER
    )
    story.append(Paragraph("RECEIPT", receipt_title_style))
    story.append(Spacer(1, 3 * mm))
    
    # Receipt metadata
    logger.info("[RECEIPT PDF] Building receipt metadata...")
    metadata_data = [
        ['Receipt No:', receipt_number],
        ['Visit ID:', service_visit.visit_id],
        ['Date:', service_visit.registered_at.strftime('%Y-%m-%d %H:%M:%S')],
    ]
    if payment and payment.received_by:
        cashier_name = payment.received_by.username
        metadata_data.append(['Cashier:', cashier_name])
        logger.info(f"[RECEIPT PDF] Cashier: {cashier_name}")
    
    content_width = COMPACT_PAGE_WIDTH - 2 * COMPACT_MARGIN
    metadata_table = Table(metadata_data, colWidths=[content_width * 0.4, content_width * 0.6])
    metadata_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TEXTCOLOR', (0, 0), (0, -1), LIGHT_GREY),
    ]))
    story.append(metadata_table)
    story.append(Spacer(1, 4 * mm))
    
    # Patient Information
    logger.info("[RECEIPT PDF] Building patient information...")
    patient_heading_style = ParagraphStyle(
        'PatientHeading',
        parent=styles['heading'],
        fontSize=10,
        fontName='Helvetica-Bold',
        textColor=CLINIC_BLUE,
    )
    story.append(Paragraph("Patient Information", patient_heading_style))
    story.append(Spacer(1, 1 * mm))
    
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
    
    logger.info(f"[RECEIPT PDF] Patient: {service_visit.patient.name}, MRN: {service_visit.patient.mrn}")
    
    patient_table = Table(patient_data, colWidths=[content_width * 0.4, content_width * 0.6])
    patient_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TEXTCOLOR', (0, 0), (0, -1), LIGHT_GREY),
    ]))
    story.append(patient_table)
    story.append(Spacer(1, 4 * mm))
    
    # Service Information
    logger.info("[RECEIPT PDF] Building services table...")
    story.append(Paragraph("Services", patient_heading_style))
    story.append(Spacer(1, 1 * mm))
    
    items = service_visit.items.all()
    logger.info(f"[RECEIPT PDF] Number of service items: {items.count()}")
    
    if items:
        service_rows = []
        for idx, item in enumerate(items):
            service_rows.append([item.service_name_snapshot, f"Rs. {item.price_snapshot:.2f}"])
            logger.info(f"[RECEIPT PDF]   Item {idx+1}: {item.service_name_snapshot} - Rs. {item.price_snapshot:.2f}")
        
        service_table = Table(
            [['Service', 'Amount']] + service_rows,
            colWidths=[content_width * 0.65, content_width * 0.35]
        )
        service_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BACKGROUND', (0, 0), (-1, 0), CLINIC_BLUE),
            ('TEXTCOLOR', (0, 0), (-1, 0), white),
            ('GRID', (0, 0), (-1, -1), 0.5, BORDER_GREY),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        story.append(service_table)
    else:
        logger.warning("[RECEIPT PDF] No service items found!")
        # Fallback for single service
        if service_visit.service:
            service_data = [
                ['Service:', service_visit.service.name],
                ['Code:', service_visit.service.code],
            ]
            logger.info(f"[RECEIPT PDF] Single service: {service_visit.service.name}")
        else:
            service_data = [['Service:', 'Multiple Services']]
            logger.warning("[RECEIPT PDF] No service information available")
        
        service_table = Table(service_data, colWidths=[content_width * 0.4, content_width * 0.6])
        service_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('TEXTCOLOR', (0, 0), (0, -1), LIGHT_GREY),
        ]))
        story.append(service_table)
    
    story.append(Spacer(1, 4 * mm))
    
    # Payment Summary
    logger.info("[RECEIPT PDF] Building payment summary...")
    story.append(Paragraph("Payment Summary", patient_heading_style))
    story.append(Spacer(1, 1 * mm))
    
    amounts_data = [
        ['Total Amount:', f"Rs. {invoice.total_amount:.2f}"],
    ]
    
    logger.info(f"[RECEIPT PDF] Total Amount: Rs. {invoice.total_amount:.2f}")
    
    if invoice.discount > 0:
        discount_label = "Discount"
        if invoice.discount_percentage:
            discount_label += f" ({invoice.discount_percentage:.2f}%)"
        amounts_data.append([f"{discount_label}:", f"Rs. {invoice.discount:.2f}"])
        logger.info(f"[RECEIPT PDF] Discount: Rs. {invoice.discount:.2f}")
    
    # Net Amount with accent color
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
    logger.info(f"[RECEIPT PDF] Net Amount: Rs. {invoice.net_amount:.2f}")
    
    paid_amount = payment.amount_paid if payment else invoice.net_amount
    amounts_data.append(['Paid Amount:', f"Rs. {paid_amount:.2f}"])
    logger.info(f"[RECEIPT PDF] Paid Amount: Rs. {paid_amount:.2f}")
    
    if invoice.balance_amount > 0:
        amounts_data.append(['Balance:', f"Rs. {invoice.balance_amount:.2f}"])
        logger.info(f"[RECEIPT PDF] Balance: Rs. {invoice.balance_amount:.2f}")
    
    payment_method = (payment.method if payment else 'cash').upper()
    amounts_data.append(['Payment Method:', payment_method])
    logger.info(f"[RECEIPT PDF] Payment Method: {payment_method}")
    
    amounts_table = Table(amounts_data, colWidths=[content_width * 0.5, content_width * 0.5])
    amounts_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('TEXTCOLOR', (0, 0), (0, -1), LIGHT_GREY),
    ]))
    story.append(amounts_table)
    story.append(Spacer(1, 5 * mm))
    
    # Footer
    logger.info("[RECEIPT PDF] Adding footer...")
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['body'],
        fontSize=7,
        textColor=LIGHT_GREY,
        alignment=1,  # CENTER
        fontName='Helvetica',
    )
    story.append(Paragraph(footer_text.replace('\n', '<br/>'), footer_style))
    
    # Build PDF
    logger.info("[RECEIPT PDF] Building PDF document...")
    try:
        doc.build(story)
        logger.info("[RECEIPT PDF] PDF document built successfully")
    except Exception as e:
        logger.error(f"[RECEIPT PDF] Failed to build PDF: {e}", exc_info=True)
        raise
    
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    logger.info(f"[RECEIPT PDF] PDF size: {len(pdf_bytes)} bytes")
    
    # Sanity check
    if pdf_bytes[:4] != b'%PDF':
        logger.error("[RECEIPT PDF] Generated PDF does not start with %PDF signature!")
        raise ValueError("Generated PDF is invalid")
    
    filename = f"receipt_{service_visit.visit_id}_{receipt_number}.pdf"
    logger.info(f"[RECEIPT PDF] Receipt PDF generation completed successfully: {filename}")
    
    return ContentFile(pdf_bytes, name=filename)
