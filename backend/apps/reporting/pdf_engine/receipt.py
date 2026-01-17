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

CLINIC_BLUE = HexColor("#0B5ED7")
ACCENT_ORANGE = HexColor("#F39C12")
LIGHT_GREY = HexColor("#9AA0A6")
BORDER_GREY = HexColor("#E5E7EB")


def _wrap_text(text: str, font_name: str, font_size: float, max_width: float) -> List[str]:
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
            if current:
                lines.append(" ".join(current))
                current = [word]
            else:
                lines.append(word)
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


def _draw_receipt_copy(
    canvas: pdf_canvas.Canvas,
    x: float,
    y: float,
    width: float,
    height: float,
    data: dict,
    copy_label: str,
    receipt_settings,
) -> None:
    padding = 6 * mm
    current_y = y + height - padding
    left_x = x + padding
    right_x = x + width - padding
    content_width = width - padding * 2

    header_image_path = _safe_image_path(getattr(receipt_settings, "header_image", None))
    logo_path = _safe_image_path(getattr(receipt_settings, "logo_image", None))
    header_text = getattr(receipt_settings, "header_text", None) or "Consultant Place Clinic"

    header_height = 18 * mm
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
    elif logo_path:
        logo_height = 15 * mm
        _draw_image_fit(
            canvas,
            logo_path,
            left_x,
            current_y - logo_height,
            25 * mm,
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

    meta_rows = [
        ("Receipt No:", data["receipt_number"]),
        ("Visit ID:", data["visit_id"]),
        ("Date:", data["date"]),
        ("Cashier:", data["cashier"] or "-"),
    ]
    current_y = _draw_label_value_rows(
        canvas,
        meta_rows,
        left_x,
        current_y,
        label_width=28 * mm,
        value_width=content_width - 28 * mm,
        font_size=8,
        line_height=4 * mm,
    )

    canvas.setFont("Helvetica-Bold", 9)
    canvas.setFillColor(CLINIC_BLUE)
    canvas.drawString(left_x, current_y, "Patient Information")
    current_y -= 4.5 * mm

    patient_rows = [
        ("Patient Reg No:", data["patient_reg_no"] or "-"),
        ("MRN:", data["mrn"] or "-"),
        ("Name:", data["patient_name"] or "-"),
        ("Age:", data["age"] or "-"),
        ("Gender:", data["gender"] or "-"),
        ("Phone:", data["phone"] or "-"),
    ]
    current_y = _draw_label_value_rows(
        canvas,
        patient_rows,
        left_x,
        current_y,
        label_width=32 * mm,
        value_width=content_width - 32 * mm,
        font_size=8,
        line_height=4 * mm,
    )

    canvas.setFont("Helvetica-Bold", 9)
    canvas.setFillColor(CLINIC_BLUE)
    canvas.drawString(left_x, current_y, "Services")
    current_y -= 4.5 * mm

    service_column_width = content_width * 0.7
    amount_column_width = content_width * 0.3
    header_height = 5 * mm
    row_padding = 1.5
    line_height = 3.5 * mm

    canvas.setStrokeColor(BORDER_GREY)
    canvas.setFillColor(LIGHT_GREY)
    canvas.setFont("Helvetica-Bold", 8)
    canvas.drawString(left_x, current_y, "Service")
    canvas.drawRightString(left_x + service_column_width + amount_column_width, current_y, "Amount")
    current_y -= header_height
    canvas.line(left_x, current_y + 2, right_x, current_y + 2)

    footer_height = 12 * mm
    summary_height = 28 * mm
    services_bottom_limit = y + footer_height + summary_height + padding

    remaining_items = list(data["services"])
    displayed_items = []
    available_height = current_y - services_bottom_limit
    for item in remaining_items:
        service_lines = _wrap_text(
            item[0],
            "Helvetica",
            8,
            service_column_width,
        )[:2]
        row_height = len(service_lines) * line_height + row_padding
        if available_height - row_height < line_height:
            break
        displayed_items.append((service_lines, item[1]))
        available_height -= row_height

    extra_count = len(remaining_items) - len(displayed_items)
    if extra_count > 0 and available_height >= line_height:
        displayed_items.append(([f"(+ {extra_count} more items)"], ""))

    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(black)
    for service_lines, amount_text in displayed_items:
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


def _build_receipt_canvas(data: dict, receipt_settings) -> ContentFile:
    buffer = BytesIO()
    canvas = pdf_canvas.Canvas(buffer, pagesize=A4)

    page_width, page_height = A4
    margin = 10 * mm
    divider_gap = 6 * mm
    usable_height = page_height - 2 * margin
    half_height = (usable_height - divider_gap) / 2
    receipt_width = page_width - 2 * margin

    bottom_y = margin
    top_y = margin + half_height + divider_gap

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

    return ContentFile(pdf_bytes, name="receipt.pdf")


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

    return _build_receipt_canvas(data, receipt_settings)


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

    return _build_receipt_canvas(data, receipt_settings)
