from dataclasses import dataclass
from decimal import Decimal
from typing import List, Optional

from django.utils import timezone

from .models import ReceiptSnapshot, ServiceVisit, Invoice


@dataclass(frozen=True)
class ReceiptLineItem:
    name: str
    qty: int
    unit_price: Decimal
    line_total: Decimal


def build_receipt_items(service_visit: ServiceVisit) -> List[ReceiptLineItem]:
    items = []
    for item in service_visit.items.all():
        items.append(
            ReceiptLineItem(
                name=item.service_name_snapshot,
                qty=1,
                unit_price=item.price_snapshot,
                line_total=item.price_snapshot,
            )
        )
    if not items and service_visit.service:
        items.append(
            ReceiptLineItem(
                name=service_visit.service.name,
                qty=1,
                unit_price=Decimal("0"),
                line_total=Decimal("0"),
            )
        )
    return items


def _resolve_cashier_name(service_visit: ServiceVisit) -> str:
    payment = service_visit.payments.first()
    if payment and payment.received_by:
        return payment.received_by.get_full_name() or payment.received_by.username
    return service_visit.created_by.get_full_name() if service_visit.created_by else ""


def create_receipt_snapshot(service_visit: ServiceVisit, invoice: Invoice) -> Optional[ReceiptSnapshot]:
    if not invoice.receipt_number:
        return None
    try:
        return service_visit.receipt_snapshot
    except ReceiptSnapshot.DoesNotExist:
        pass

    items = build_receipt_items(service_visit)
    total_paid = sum((payment.amount_paid for payment in service_visit.payments.all()), Decimal("0"))
    payment = service_visit.payments.first()
    payment_method = payment.method if payment else "cash"

    snapshot = ReceiptSnapshot.objects.create(
        service_visit=service_visit,
        receipt_number=invoice.receipt_number,
        issued_at=payment.received_at if payment else service_visit.registered_at,
        items_json=[
            {
                "name": item.name,
                "qty": item.qty,
                "unit_price": str(item.unit_price),
                "line_total": str(item.line_total),
            }
            for item in items
        ],
        subtotal=invoice.subtotal,
        discount=invoice.discount,
        total_paid=total_paid,
        payment_method=payment_method,
        patient_name=service_visit.patient.name,
        patient_phone=service_visit.patient.phone or "",
        patient_reg_no=service_visit.patient.patient_reg_no or "",
        patient_mrn=service_visit.patient.mrn or "",
        patient_age=str(service_visit.patient.age) if service_visit.patient.age else "",
        patient_gender=service_visit.patient.gender or "",
        cashier_name=_resolve_cashier_name(service_visit),
        referring_consultant=service_visit.referring_consultant or "",
    )
    return snapshot


def get_receipt_snapshot_data(service_visit: ServiceVisit, invoice: Invoice):
    try:
        return service_visit.receipt_snapshot
    except ReceiptSnapshot.DoesNotExist:
        pass

    items = build_receipt_items(service_visit)
    total_paid = sum((payment.amount_paid for payment in service_visit.payments.all()), Decimal("0"))
    payment = service_visit.payments.first()
    payment_method = payment.method if payment else "cash"

    return ReceiptSnapshot(
        service_visit=service_visit,
        receipt_number=invoice.receipt_number or service_visit.visit_id,
        issued_at=payment.received_at if payment else service_visit.registered_at or timezone.now(),
        items_json=[
            {
                "name": item.name,
                "qty": item.qty,
                "unit_price": str(item.unit_price),
                "line_total": str(item.line_total),
            }
            for item in items
        ],
        subtotal=invoice.subtotal,
        discount=invoice.discount,
        total_paid=total_paid,
        payment_method=payment_method,
        patient_name=service_visit.patient.name,
        patient_phone=service_visit.patient.phone or "",
        patient_reg_no=service_visit.patient.patient_reg_no or "",
        patient_mrn=service_visit.patient.mrn or "",
        patient_age=str(service_visit.patient.age) if service_visit.patient.age else "",
        patient_gender=service_visit.patient.gender or "",
        cashier_name=_resolve_cashier_name(service_visit),
        referring_consultant=service_visit.referring_consultant or "",
    )
