"""
Receipt PDF generation using ReportLab.
Dual-copy A4 receipt layout with fixed canvas positioning.
Supports both Visit (legacy) and ServiceVisit (workflow) models.
"""
import logging
import os
from io import BytesIO
from typing import Iterable, List, Optional, Tuple

from django.core.files.base import ContentFile
from reportlab.lib.colors import HexColor, black
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen import canvas as pdf_canvas

from .base import PDFBase

logger = logging.getLogger(__name__)

LOCKED_FOOTER_TEXT = (
    "Adjacent Excel Labs, Near Arman Pan Shop Faisalabad Road Jaranwala\n"
    "For information/Appointment: Tel: 041 4313 777 | WhatsApp: 03279640897"
)

# Color constants
CLINIC_BLUE = HexColor("#0B5ED7")
ACCENT_ORANGE = HexColor("#F39C12")
LIGHT_GREY = HexColor("#9AA0A6")
BORDER_GREY = HexColor("#E5E7EB")

# Layout dimension constants (in mm)
HEADER_IMAGE_HEIGHT = 18
LOGO_HEIGHT = 14
LOGO_MAX_WIDTH = 30
PADDING = 6
COLUMN_GAP = 6
HEADER_HEIGHT = 5
ROW_PADDING = 1.5
LINE_HEIGHT = 3.5
FOOTER_HEIGHT = 12
SUMMARY_HEIGHT = 28
MIN_FONT_SIZE = 8  # Minimum font size before splitting to multiple pages


def _wrap_text(text: str, font_name: str, font_size: float, max_width: float) -> List[str]:
    """
    Wrap text to fit within a specified width using the given font.
    
    Handles edge case where a single word is longer than max_width by splitting
    the word at character boundaries.
    
    Args:
        text: The text to wrap
        font_name: The font name for width calculation
        font_size: The font size for width calculation
        max_width: Maximum width in points
        
    Returns:
        List of text lines that fit within max_width
    """
    if not text:
        return [""]
    words = text.split()
    lines: List[str] = []
    current: List[str] = []
    for word in words:
        tentative = " ".join(current + [word])
        if pdfmetrics.stringWidth(tentative, font_name, font_size) <= max_width:
            current.append(word)
        else:
            # Flush current line if it has content
            if current:
                lines.append(" ".join(current))
                current = []
            # Handle words that are themselves longer than max_width by
            # splitting them into segments that each fit within max_width.
            word_width = pdfmetrics.stringWidth(word, font_name, font_size)
            if word_width > max_width:
                remaining = word
                while remaining:
                    low, high = 1, len(remaining)
                    fit_len = 0
                    # Binary search for the longest prefix that fits
                    while low <= high:
                        mid = (low + high) // 2
                        segment = remaining[:mid]
                        if pdfmetrics.stringWidth(segment, font_name, font_size) <= max_width:
                            fit_len = mid
                            low = mid + 1
                        else:
                            high = mid - 1
                    if fit_len == 0:
                        # Fallback: force progress to avoid infinite loop
                        fit_len = 1
                    segment = remaining[:fit_len]
                    lines.append(segment)
                    remaining = remaining[fit_len:]
            else:
                current = [word]
    if current:
        lines.append(" ".join(current))
    return lines


def _safe_image_path(field) -> Optional[str]:
    if not field:
        return None
    path = getattr(field, "path", None)
    if path and os.path.exists(path):
        return path
    return None


def _draw_image_fit(
    canvas: pdf_canvas.Canvas,
    image_path: str,
    x: float,
    y: float,
    max_width: float,
    max_height: float,
    align_center: bool = False,
) -> Tuple[float, float]:
    try:
        image = ImageReader(image_path)
        image_width, image_height = image.getSize()
        if not image_width or not image_height:
            return 0.0, 0.0
        scale = min(max_width / image_width, max_height / image_height)
        draw_width = image_width * scale
        draw_height = image_height * scale
        draw_x = x + (max_width - draw_width) / 2 if align_center else x
        canvas.drawImage(image, draw_x, y, width=draw_width, height=draw_height, mask="auto")
        return draw_width, draw_height
    except Exception:
        logger.exception("Failed to load or draw image at path '%s'", image_path)
        return 0.0, 0.0


def _draw_label_value_rows(
    canvas: pdf_canvas.Canvas,
    rows: Iterable[Tuple[str, str]],
    x: float,
    y: float,
    label_width: float,
    value_width: float,
    font_size: float,
    line_height: float,
) -> float:
    current_y = y
    for label, value in rows:
        label_lines = _wrap_text(label, "Helvetica-Bold", font_size, label_width)
        value_lines = _wrap_text(value, "Helvetica", font_size, value_width)
        max_lines = max(len(label_lines), len(value_lines))
        for line_idx in range(max_lines):
            label_text = label_lines[line_idx] if line_idx < len(label_lines) else ""
            value_text = value_lines[line_idx] if line_idx < len(value_lines) else ""
            canvas.setFont("Helvetica-Bold", font_size)
            canvas.setFillColor(LIGHT_GREY)
            canvas.drawString(x, current_y, label_text)
            canvas.setFont("Helvetica", font_size)
            canvas.setFillColor(black)
            canvas.drawString(x + label_width, current_y, value_text)
            current_y -= line_height
        current_y -= 1.5
    return current_y


def _calculate_service_layout(
    services: List[Tuple[str, str]],
    service_column_width: float,
    available_height: float,
    initial_font_size: float = 8,
    initial_line_height: float = 3.5,
) -> Tuple[float, float, int, bool]:
    """
    Calculate optimal font size and line height to fit all service items.
    
    Tries to fit all items by reducing font size and line spacing. If font size
    would drop below MIN_FONT_SIZE (8pt), returns parameters indicating a split
    is needed.
    
    Args:
        services: List of (service_name, amount) tuples
        service_column_width: Width available for service name column (in points)
        available_height: Height available for all service items (in points)
        initial_font_size: Starting font size to try
        initial_line_height: Starting line height (in mm)
        
    Returns:
        Tuple of (font_size, line_height_mm, items_count, needs_split)
        - font_size: Optimal font size to use
        - line_height_mm: Optimal line height in mm
        - items_count: Number of items that fit (all if needs_split=False)
        - needs_split: True if items need to be split across pages
    """
    font_size = initial_font_size
    line_height_mm = initial_line_height
    row_padding = ROW_PADDING
    
    # Try progressively smaller font sizes
    while font_size >= MIN_FONT_SIZE:
        total_height = 0
        items_fitted = 0
        
        for service_name, _ in services:
            service_lines = _wrap_text(
                service_name,
                "Helvetica",
                font_size,
                service_column_width,
            )[:2]  # Limit to 2 lines per item
            row_height = len(service_lines) * line_height_mm * mm + row_padding
            
            if total_height + row_height > available_height:
                break
            
            total_height += row_height
            items_fitted += 1
        
        if items_fitted == len(services):
            # All items fit!
            return font_size, line_height_mm, len(services), False
        
        # Reduce font size and line height
        font_size -= 0.5
        line_height_mm -= 0.2
        
        # Ensure line height doesn't become too small
        if line_height_mm < 2.5:
            line_height_mm = 2.5
    
    # If we reach here, we need to split across pages
    # Calculate how many items fit with MIN_FONT_SIZE
    font_size = MIN_FONT_SIZE
    line_height_mm = 2.8  # Minimum reasonable line height
    total_height = 0
    items_fitted = 0
    
    for service_name, _ in services:
        service_lines = _wrap_text(
            service_name,
            "Helvetica",
            font_size,
            service_column_width,
        )[:2]
        row_height = len(service_lines) * line_height_mm * mm + row_padding
        
        if total_height + row_height > available_height:
            break
        
        total_height += row_height
        items_fitted += 1
    
    return font_size, line_height_mm, items_fitted, True


def _draw_receipt_copy(
    canvas: pdf_canvas.Canvas,
    x: float,
    y: float,
    width: float,
    height: float,
    data: dict,
    copy_label: str,
    receipt_settings,
    services_subset: Optional[List[Tuple[str, str]]] = None,
) -> None:
    """
    Render a single receipt copy into a rectangular region of the PDF canvas.

    This function draws one complete receipt "copy" (e.g. patient or clinic copy)
    inside the area defined by ``(x, y, width, height)`` on the given ReportLab
    canvas. It is responsible for laying out header imagery/text, logos, receipt
    metadata, line items, totals, payment information and footer content according
    to a fixed A4 dual-copy layout.

    Coordinate system
    ------------------
    The underlying ReportLab coordinate system has its origin at the bottom-left
    of the page. The ``x`` and ``y`` values passed here represent the bottom-left
    corner of the rectangular region reserved for this receipt copy, expressed in
    points (usually converted from millimetres using ``reportlab.lib.units.mm``).

    - ``width`` is the total width of the receipt copy region, extending to the
      right from ``x``.
    - ``height`` is the total height of the receipt copy region, extending
      upwards from ``y``.
    - Internal vertical positioning starts from the top edge of this region
      (``y + height``) and moves downward as elements are drawn. A small inner
      padding is applied on all sides before content is rendered.

    Parameters
    ----------
    canvas:
        The ReportLab :class:`~reportlab.pdfgen.canvas.Canvas` on which all
        drawing operations are performed. It is modified in-place.
    x:
        Left X coordinate (in points) of the receipt copy region.
    y:
        Bottom Y coordinate (in points) of the receipt copy region.
    width:
        Width (in points) of the receipt copy region.
    height:
        Height (in points) of the receipt copy region.
    data:
        Dictionary containing all precomputed data required to render the receipt,
        such as patient details, visit information, line items and totals. The
        expected structure matches what the caller of this function provides and
        is not validated here.
    copy_label:
        Short textual label identifying the copy being rendered (for example,
        "Patient Copy" or "Clinic Copy"). Typically displayed in the header
        area to differentiate multiple copies on the same page.
    receipt_settings:
        An object providing configuration and assets used for rendering, such as
        header images, logos and optional header text attributes (e.g.
        ``header_image``, ``logo_image``, ``header_text``). Attribute presence is
        checked dynamically.
    services_subset:
        Optional subset of services to display. If None, uses all services from
        data["services"]. Used when splitting services across multiple pages.

    Returns
    -------
    None
        All output is drawn directly onto the provided canvas.
    """
    padding = PADDING * mm
    current_y = y + height - padding
    left_x = x + padding
    right_x = x + width - padding
    content_width = width - padding * 2

    header_image_path = _safe_image_path(getattr(receipt_settings, "header_image", None))
    logo_path = _safe_image_path(getattr(receipt_settings, "logo_image", None))
    header_text = getattr(receipt_settings, "header_text", None) or "Consultant Place Clinic"

    header_height = HEADER_IMAGE_HEIGHT * mm
    if header_image_path:
        _draw_image_fit(
            canvas,
            header_image_path,
            left_x,
            current_y - header_height,
            content_width,
            header_height,
            align_center=True,
        )
        current_y -= header_height + 2 * mm

    if logo_path:
        logo_height = LOGO_HEIGHT * mm
        _draw_image_fit(
            canvas,
            logo_path,
            left_x,
            current_y - logo_height,
            LOGO_MAX_WIDTH * mm,
            logo_height,
            align_center=False,
        )
        current_y -= logo_height + 2 * mm

    canvas.setFont("Helvetica-Bold", 12)
    canvas.setFillColor(CLINIC_BLUE)
    canvas.drawCentredString(x + width / 2, current_y, header_text)
    current_y -= 5 * mm

    canvas.setFont("Helvetica-Bold", 10)
    canvas.setFillColor(black)
    canvas.drawCentredString(x + width / 2, current_y, "RECEIPT")
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(LIGHT_GREY)
    canvas.drawRightString(right_x, current_y, copy_label)
    current_y -= 6 * mm

    canvas.setStrokeColor(BORDER_GREY)
    canvas.line(left_x, current_y, right_x, current_y)
    current_y -= 4 * mm

    column_gap = COLUMN_GAP * mm
    column_width = (content_width - column_gap) / 2
    left_column_x = left_x
    right_column_x = left_x + column_width + column_gap
    section_top_y = current_y

    canvas.setFont("Helvetica-Bold", 9)
    canvas.setFillColor(CLINIC_BLUE)
    canvas.drawString(left_column_x, section_top_y, "Patient Information")
    left_column_y = section_top_y - 4.5 * mm
    patient_rows = [
        ("Patient Reg No:", data["patient_reg_no"] or "-"),
        ("MRN:", data["mrn"] or "-"),
        ("Name:", data["patient_name"] or "-"),
        ("Age:", data["age"] or "-"),
        ("Gender:", data["gender"] or "-"),
        ("Phone:", data["phone"] or "-"),
    ]
    left_column_y = _draw_label_value_rows(
        canvas,
        patient_rows,
        left_column_x,
        left_column_y,
        label_width=30 * mm,
        value_width=column_width - 30 * mm,
        font_size=8,
        line_height=4 * mm,
    )

    canvas.setFont("Helvetica-Bold", 9)
    canvas.setFillColor(CLINIC_BLUE)
    canvas.drawString(right_column_x, section_top_y, "Receipt Details")
    right_column_y = section_top_y - 4.5 * mm
    meta_rows = [
        ("Receipt No:", data["receipt_number"]),
        ("Visit ID:", data["visit_id"]),
        ("Date:", data["date"]),
        ("Cashier:", data["cashier"] or "-"),
    ]
    right_column_y = _draw_label_value_rows(
        canvas,
        meta_rows,
        right_column_x,
        right_column_y,
        label_width=24 * mm,
        value_width=column_width - 24 * mm,
        font_size=8,
        line_height=4 * mm,
    )

    current_y = min(left_column_y, right_column_y) - 2 * mm

    canvas.setFont("Helvetica-Bold", 9)
    canvas.setFillColor(CLINIC_BLUE)
    canvas.drawString(left_x, current_y, "Services")
    current_y -= 4.5 * mm

    service_column_width = content_width * 0.7
    amount_column_width = content_width * 0.3
    header_height_var = HEADER_HEIGHT * mm
    row_padding = ROW_PADDING

    canvas.setStrokeColor(BORDER_GREY)
    canvas.setFillColor(LIGHT_GREY)
    canvas.setFont("Helvetica-Bold", 8)
    canvas.drawString(left_x, current_y, "Service")
    canvas.drawRightString(left_x + service_column_width + amount_column_width, current_y, "Amount")
    current_y -= header_height_var
    canvas.line(left_x, current_y + 2, right_x, current_y + 2)

    footer_height = FOOTER_HEIGHT * mm
    summary_height = SUMMARY_HEIGHT * mm
    services_bottom_limit = y + footer_height + summary_height + padding

    # Use provided services subset or all services
    services_to_display = services_subset if services_subset is not None else data["services"]
    
    # Calculate optimal layout for services
    available_height = current_y - services_bottom_limit
    font_size, line_height_mm, items_count, needs_split = _calculate_service_layout(
        services_to_display,
        service_column_width,
        available_height,
    )
    
    line_height = line_height_mm * mm
    
    # Draw service items with calculated font size and line height
    canvas.setFont("Helvetica", font_size)
    canvas.setFillColor(black)
    
    for idx in range(items_count):
        service_name, amount_text = services_to_display[idx]
        service_lines = _wrap_text(
            service_name,
            "Helvetica",
            font_size,
            service_column_width,
        )[:2]
        
        start_y = current_y
        for line in service_lines:
            canvas.drawString(left_x, start_y, line)
            start_y -= line_height
        
        canvas.drawRightString(
            left_x + service_column_width + amount_column_width,
            current_y,
            amount_text,
        )
        current_y -= len(service_lines) * line_height + row_padding
    
    current_y -= 2 * mm

    canvas.setFont("Helvetica-Bold", 9)
    canvas.setFillColor(CLINIC_BLUE)
    canvas.drawString(left_x, current_y, "Payment Summary")
    current_y -= 4.5 * mm

    summary_rows = [
        ("Total Amount:", data["total_amount"], False),
        ("Net Amount:", data["net_amount"], True),
        ("Paid Amount:", data["paid_amount"], False),
        ("Payment Method:", data["payment_method"], False),
    ]
    for label, value, highlight in summary_rows:
        canvas.setFont("Helvetica-Bold", 8)
        canvas.setFillColor(LIGHT_GREY)
        canvas.drawString(left_x + content_width * 0.35, current_y, label)
        canvas.setFont("Helvetica-Bold" if highlight else "Helvetica", 8)
        canvas.setFillColor(ACCENT_ORANGE if highlight else black)
        canvas.drawRightString(right_x, current_y, value)
        current_y -= 4 * mm

    footer_lines = LOCKED_FOOTER_TEXT.split("\n")
    canvas.setFont("Helvetica", 6.5)
    canvas.setFillColor(LIGHT_GREY)
    footer_y = y + 8 * mm
    for idx, line in enumerate(footer_lines):
        canvas.drawCentredString(x + width / 2, footer_y + (len(footer_lines) - idx - 1) * 3.2, line)


def _build_receipt_canvas(data: dict, receipt_settings, filename: str) -> ContentFile:
    """
    Build the core receipt PDF canvas in a dual-copy A4 layout.

    This function renders two receipt copies ("Patient copy" and "Office copy")
    on a single A4 page using ReportLab. The copies are stacked vertically
    within the page margins, separated by a horizontal dashed divider line.

    If service items cannot fit on a single page even with font size reduction
    to the minimum (8pt), the function automatically generates a multi-page
    receipt with services split across pages. Each page maintains the full
    dual-copy layout with all receipt metadata, with only the service items
    being split.

    The actual drawing of each receipt section is delegated to
    ``_draw_receipt_copy``, which uses the supplied ``data`` and
    ``receipt_settings`` to populate the content.

    Args:
        data: A dictionary containing all structured data required to render
            a single receipt copy (patient details, line items, totals, etc.).
            Expected keys include 'services' (list of service tuples), patient
            information, and payment details.
        receipt_settings: Receipt configuration/settings object used by
            the drawing helpers to control branding and layout options.
            This is typically obtained from PDFBase.get_receipt_settings().
        filename: The desired filename to associate with the generated PDF.
            This value is used as the ``name`` of the returned ``ContentFile``.

    Returns:
        ContentFile: An in-memory Django ``ContentFile`` instance containing
        the generated PDF bytes for the dual-copy receipt, suitable for
        saving to a model field or sending as a response.
        
    Note:
        This is an internal function (indicated by the underscore prefix) and
        should not be called directly from outside this module. Use
        ``build_receipt_pdf_reportlab`` or
        ``build_service_visit_receipt_pdf_reportlab`` instead.
        
        **API Change (v2.0)**: The ``filename`` parameter was added to allow
        callers to specify the output filename. Previously, the filename was
        determined externally after the ContentFile was created. No external
        code depends on this function as it is only called from within this
        module by the public receipt generation functions.
    """
    buffer = BytesIO()
    canvas = pdf_canvas.Canvas(buffer, pagesize=A4)

    page_width, page_height = A4
    margin = 10 * mm
    divider_gap = COLUMN_GAP * mm
    usable_height = page_height - 2 * margin
    half_height = (usable_height - divider_gap) / 2
    receipt_width = page_width - 2 * margin

    bottom_y = margin
    top_y = margin + half_height + divider_gap

    # Check if services need to be split across pages
    services = data["services"]
    
    # Calculate available height for services in one receipt copy
    # This is an approximation; actual calculation is done in _calculate_service_layout
    padding = PADDING * mm
    service_column_width = (receipt_width - padding * 2) * 0.7
    
    # Approximate available height for services (accounting for header, patient info, etc.)
    # Header + logo + patient info + receipt details ≈ 80mm, payment summary + footer ≈ 40mm
    approx_available_height = half_height - 120 * mm
    
    font_size, line_height_mm, items_count, needs_split = _calculate_service_layout(
        services,
        service_column_width,
        approx_available_height,
    )
    
    if needs_split:
        logger.info(
            "[RECEIPT PDF] Services require multiple pages. Splitting %d items across pages.",
            len(services)
        )
        # Split services across multiple pages
        page_num = 0
        remaining_services = list(services)
        
        while remaining_services:
            page_num += 1
            # Recalculate for remaining services
            font_size, line_height_mm, items_count, _ = _calculate_service_layout(
                remaining_services,
                service_column_width,
                approx_available_height,
            )
            
            # Ensure we make progress
            if items_count == 0:
                items_count = 1
            
            current_page_services = remaining_services[:items_count]
            remaining_services = remaining_services[items_count:]
            
            # Draw patient and office copies with this subset of services
            _draw_receipt_copy(
                canvas,
                margin,
                top_y,
                receipt_width,
                half_height,
                data,
                f"Patient copy (Page {page_num})",
                receipt_settings,
                services_subset=current_page_services,
            )
            _draw_receipt_copy(
                canvas,
                margin,
                bottom_y,
                receipt_width,
                half_height,
                data,
                f"Office copy (Page {page_num})",
                receipt_settings,
                services_subset=current_page_services,
            )
            
            # Draw divider line
            divider_y = margin + half_height + divider_gap / 2
            canvas.setStrokeColor(LIGHT_GREY)
            canvas.setDash(1, 2)
            canvas.line(margin, divider_y, page_width - margin, divider_y)
            canvas.setDash([])
            
            canvas.showPage()
    else:
        # Single page receipt
        _draw_receipt_copy(
            canvas,
            margin,
            top_y,
            receipt_width,
            half_height,
            data,
            "Patient copy",
            receipt_settings,
        )
        _draw_receipt_copy(
            canvas,
            margin,
            bottom_y,
            receipt_width,
            half_height,
            data,
            "Office copy",
            receipt_settings,
        )

        divider_y = margin + half_height + divider_gap / 2
        canvas.setStrokeColor(LIGHT_GREY)
        canvas.setDash(1, 2)
        canvas.line(margin, divider_y, page_width - margin, divider_y)
        canvas.setDash([])

        canvas.showPage()
    
    canvas.save()

    pdf_bytes = buffer.getvalue()
    buffer.close()

    if pdf_bytes[:4] != b"%PDF":
        logger.error("[RECEIPT PDF] Generated PDF does not start with %PDF signature!")
        raise ValueError("Generated PDF is invalid")

    return ContentFile(pdf_bytes, name=filename)


def build_receipt_pdf_reportlab(visit) -> ContentFile:
    logger.info(
        "[RECEIPT PDF] Starting receipt generation for Visit ID: %s",
        getattr(visit, "visit_number", "N/A"),
    )
    base = PDFBase()
    receipt_settings = base.get_receipt_settings()

    receipt_date = visit.receipt_generated_at or visit.created_at
    receipt_number = visit.receipt_number or visit.visit_number

    items = visit.items.select_related("service", "service__modality").all()
    services = []
    for item in items:
        service_name = f"{item.service.modality.code} - {item.service.name}"
        if item.indication:
            indication_text = (
                item.indication[:50] + "..." if len(item.indication) > 50 else item.indication
            )
            service_name += f" ({indication_text})"
        services.append((service_name, f"Rs. {item.charge:.2f}"))

    data = {
        "receipt_number": str(receipt_number),
        "visit_id": str(getattr(visit, "visit_number", "-")),
        "date": receipt_date.strftime("%Y-%m-%d %H:%M:%S"),
        "cashier": (
            visit.created_by.get_full_name() or visit.created_by.username
            if visit.created_by
            else ""
        ),
        "patient_reg_no": getattr(visit.patient, "patient_reg_no", "") or "",
        "mrn": visit.patient.mrn,
        "patient_name": visit.patient.name,
        "age": str(visit.patient.age) if visit.patient.age else "",
        "gender": visit.patient.gender or "",
        "phone": visit.patient.phone or "",
        "services": services,
        "total_amount": f"Rs. {visit.subtotal:.2f}",
        "net_amount": f"Rs. {visit.net_total:.2f}",
        "paid_amount": f"Rs. {visit.paid_amount:.2f}",
        "payment_method": (visit.payment_method or "cash").upper(),
    }

    filename = f"receipt_{data['visit_id']}.pdf"
    return _build_receipt_canvas(data, receipt_settings, filename)


def build_service_visit_receipt_pdf_reportlab(service_visit, invoice) -> ContentFile:
    logger.info(
        "[RECEIPT PDF] Starting ServiceVisit receipt generation for Visit ID: %s",
        service_visit.visit_id,
    )
    base = PDFBase()
    receipt_settings = base.get_receipt_settings()

    receipt_number = invoice.receipt_number or service_visit.visit_id
    payment = service_visit.payments.first()
    cashier_name = payment.received_by.username if payment and payment.received_by else ""

    services = []
    items = service_visit.items.all()
    for item in items:
        services.append((item.service_name_snapshot, f"Rs. {item.price_snapshot:.2f}"))

    if not services and service_visit.service:
        services.append((service_visit.service.name, ""))

    paid_amount = payment.amount_paid if payment else invoice.net_amount
    payment_method = (payment.method if payment else "cash").upper()

    data = {
        "receipt_number": str(receipt_number),
        "visit_id": str(service_visit.visit_id),
        "date": service_visit.registered_at.strftime("%Y-%m-%d %H:%M:%S"),
        "cashier": cashier_name,
        "patient_reg_no": service_visit.patient.patient_reg_no or service_visit.patient.mrn,
        "mrn": service_visit.patient.mrn,
        "patient_name": service_visit.patient.name,
        "age": str(service_visit.patient.age) if service_visit.patient.age else "",
        "gender": service_visit.patient.gender or "",
        "phone": service_visit.patient.phone or "",
        "services": services,
        "total_amount": f"Rs. {invoice.total_amount:.2f}",
        "net_amount": f"Rs. {invoice.net_amount:.2f}",
        "paid_amount": f"Rs. {paid_amount:.2f}",
        "payment_method": payment_method,
    }

    filename = f"receipt_{data['visit_id']}.pdf"
    return _build_receipt_canvas(data, receipt_settings, filename)
