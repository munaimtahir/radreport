from decimal import Decimal, ROUND_HALF_UP

from django.db.models import Sum

from apps.workflow.models import ServiceVisit

from .models import ConsultantBillingRule, ConsultantSettlementLine

MONEY_QUANT = Decimal("0.01")


def quantize_money(value: Decimal) -> Decimal:
    return value.quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)


def get_consultant_percent(consultant, as_of_date):
    rules = ConsultantBillingRule.objects.filter(consultant=consultant, is_active=True).order_by(
        "-active_from",
        "-created_at",
    )
    for rule in rules:
        if rule.active_from and as_of_date and rule.active_from > as_of_date:
            continue
        return rule.consultant_percent
    return Decimal("0")


def build_settlement_preview(consultant, date_from, date_to):
    # Exclude items already included in ANY finalized settlement for this consultant
    # regardless of the settlement's date range to prevent double settlements
    settled_item_ids = set(
        ConsultantSettlementLine.objects.filter(
            settlement__consultant=consultant,
            settlement__status=ConsultantSettlement.STATUS_FINALIZED,
        ).values_list("service_item_id", flat=True)
    )

    service_visits = ServiceVisit.objects.filter(
        registered_at__date__gte=date_from,
        registered_at__date__lte=date_to,
        items__consultant=consultant,
    ).distinct().prefetch_related("items", "payments", "patient")

    consultant_percent = get_consultant_percent(consultant, date_to)
    lines = []
    gross_collected = Decimal("0")
    consultant_payable = Decimal("0")
    clinic_share = Decimal("0")

    for visit in service_visits:
        total_paid = (
            visit.payments.filter(received_at__date__gte=date_from, received_at__date__lte=date_to)
            .aggregate(total=Sum("amount_paid"))
            .get("total")
            or Decimal("0")
        )
        remaining = total_paid
        items = list(visit.items.all().order_by("created_at", "id"))
        for item in items:
            item_total = item.price_snapshot or Decimal("0")
            item_paid = min(item_total, remaining)
            item_paid = quantize_money(item_paid)
            remaining = max(Decimal("0"), remaining - item_paid)

            if item.consultant_id != consultant.id:
                continue
            if item.id in settled_item_ids:
                continue

            consultant_share = quantize_money(item_paid * consultant_percent / Decimal("100"))
            clinic_share_item = quantize_money(item_paid - consultant_share)

            lines.append(
                {
                    "service_item": item,
                    "service_item_id": str(item.id),
                    "visit_id": item.service_visit.visit_id,
                    "patient_name": item.service_visit.patient.name,
                    "service_name": item.service_name_snapshot,
                    "item_amount_snapshot": quantize_money(item_total),
                    "paid_amount_snapshot": item_paid,
                    "consultant_share_snapshot": consultant_share,
                    "clinic_share_snapshot": clinic_share_item,
                }
            )

            gross_collected += item_paid
            consultant_payable += consultant_share
            clinic_share += clinic_share_item

    return {
        "consultant_percent": consultant_percent,
        "gross_collected": quantize_money(gross_collected),
        "consultant_payable": quantize_money(consultant_payable),
        "clinic_share": quantize_money(clinic_share),
        "lines": lines,
    }
