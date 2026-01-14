from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.studies.models import Visit, Study
from apps.workflow.models import Invoice, Payment, ServiceVisit, ServiceVisitItem, StatusAuditLog
from apps.workflow.transitions import map_study_status_to_item_status


class Command(BaseCommand):
    help = "Backfill ServiceVisit and related workflow models from legacy Visit/Study data."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing to the database.")
        parser.add_argument("--limit", type=int, default=None, help="Limit number of legacy visits to process.")

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        limit = options["limit"]

        visits = (
            Visit.objects.select_related("patient", "created_by")
            .prefetch_related(
                "items__service__modality",
                "studies__service__modality",
                "studies__order_item",
                "studies__created_by",
            )
            .order_by("created_at")
        )
        if limit:
            visits = visits[:limit]

        created_visits = 0
        created_items = 0
        created_invoices = 0
        created_payments = 0
        skipped_visits = 0

        for visit in visits:
            if ServiceVisit.objects.filter(visit_id=visit.visit_number).exists():
                skipped_visits += 1
                continue

            if dry_run:
                created_visits += 1
                created_items += visit.items.count() + visit.studies.filter(order_item__isnull=True).count()
                if visit.subtotal or visit.net_total or visit.paid_amount:
                    created_invoices += 1
                if visit.paid_amount > 0:
                    created_payments += 1
                continue

            with transaction.atomic():
                service_visit = ServiceVisit.objects.create(
                    visit_id=visit.visit_number,
                    patient=visit.patient,
                    status="REGISTERED",
                    created_by=visit.created_by,
                )
                ServiceVisit.objects.filter(id=service_visit.id).update(registered_at=visit.created_at)

                study_by_order_item = {
                    study.order_item_id: study for study in visit.studies.all() if study.order_item_id
                }

                for order_item in visit.items.all():
                    study = study_by_order_item.get(order_item.id)
                    item_status = map_study_status_to_item_status(study.status if study else None)
                    legacy_timestamp = (study.created_at if study else visit.created_at)
                    item = self._create_item_from_service(
                        service_visit=service_visit,
                        service=order_item.service,
                        price_snapshot=order_item.charge or order_item.service.price,
                        status=item_status,
                        legacy_timestamp=legacy_timestamp,
                    )
                    created_items += 1
                    if study:
                        self._log_legacy_status(item, study.status, study.created_by or visit.created_by)
                    elif item_status != "REGISTERED":
                        self._log_status_transition(item, "REGISTERED", item_status, visit.created_by)

                unmatched_studies = visit.studies.filter(order_item__isnull=True)
                for study in unmatched_studies:
                    item_status = map_study_status_to_item_status(study.status)
                    item = self._create_item_from_service(
                        service_visit=service_visit,
                        service=study.service,
                        price_snapshot=study.service.price,
                        status=item_status,
                        legacy_timestamp=study.created_at,
                    )
                    created_items += 1
                    self._log_legacy_status(item, study.status, study.created_by or visit.created_by)

                if visit.subtotal or visit.net_total or visit.paid_amount:
                    invoice = Invoice.objects.create(
                        service_visit=service_visit,
                        subtotal=visit.subtotal or Decimal("0"),
                        discount=visit.discount_amount or Decimal("0"),
                        discount_percentage=visit.discount_percentage,
                        total_amount=visit.net_total or Decimal("0"),
                        net_amount=visit.net_total or Decimal("0"),
                        balance_amount=visit.due_amount or Decimal("0"),
                    )
                    if visit.receipt_number:
                        invoice.receipt_number = visit.receipt_number
                        invoice.save(update_fields=["receipt_number"])
                    created_invoices += 1

                if visit.paid_amount and visit.paid_amount > 0:
                    Payment.objects.create(
                        service_visit=service_visit,
                        amount_paid=visit.paid_amount,
                        method=visit.payment_method or "cash",
                        received_by=visit.created_by,
                    )
                    created_payments += 1

                service_visit.update_derived_status()
                if service_visit.status != "REGISTERED":
                    StatusAuditLog.objects.create(
                        service_visit=service_visit,
                        from_status="REGISTERED",
                        to_status=service_visit.status,
                        reason="Legacy visit status derived from study statuses.",
                        changed_by=visit.created_by,
                    )

                created_visits += 1

        self._backfill_orphan_studies(dry_run)

        summary = (
            f"ServiceVisit backfill summary: created_visits={created_visits}, "
            f"created_items={created_items}, created_invoices={created_invoices}, "
            f"created_payments={created_payments}, skipped_visits={skipped_visits}, "
            f"dry_run={dry_run}"
        )
        self.stdout.write(self.style.SUCCESS(summary))

    def _create_item_from_service(self, service_visit, service, price_snapshot, status, legacy_timestamp):
        department_snapshot = ""
        if service.modality and service.modality.code:
            department_snapshot = service.modality.code
        elif service.category:
            department_snapshot = service.category

        item = ServiceVisitItem.objects.create(
            service_visit=service_visit,
            service=service,
            service_name_snapshot=service.name,
            department_snapshot=department_snapshot,
            price_snapshot=price_snapshot,
            status=status,
        )

        self._apply_legacy_timestamps(item, status, legacy_timestamp)
        return item

    def _apply_legacy_timestamps(self, item, status, legacy_timestamp):
        update_fields = []
        if status in ["IN_PROGRESS", "PENDING_VERIFICATION", "RETURNED_FOR_CORRECTION", "FINALIZED", "PUBLISHED"]:
            item.started_at = item.started_at or legacy_timestamp
            update_fields.append("started_at")
        if status in ["PENDING_VERIFICATION", "FINALIZED", "PUBLISHED"]:
            item.submitted_at = item.submitted_at or legacy_timestamp
            update_fields.append("submitted_at")
        if status in ["PUBLISHED"]:
            item.published_at = item.published_at or legacy_timestamp
            update_fields.append("published_at")

        if update_fields:
            item.save(update_fields=update_fields)

    def _log_legacy_status(self, item, study_status, user):
        mapped_status = map_study_status_to_item_status(study_status)
        if mapped_status == "REGISTERED":
            return
        StatusAuditLog.objects.create(
            service_visit_item=item,
            service_visit=item.service_visit,
            from_status="REGISTERED",
            to_status=mapped_status,
            reason=f"Legacy study status backfill ({study_status}).",
            changed_by=user,
        )

    def _log_status_transition(self, item, from_status, to_status, user):
        StatusAuditLog.objects.create(
            service_visit_item=item,
            service_visit=item.service_visit,
            from_status=from_status,
            to_status=to_status,
            reason="Legacy status backfill.",
            changed_by=user,
        )

    def _backfill_orphan_studies(self, dry_run):
        orphan_studies = Study.objects.filter(visit__isnull=True).select_related(
            "patient", "service", "created_by", "service__modality"
        )
        if not orphan_studies.exists():
            return

        for study in orphan_studies:
            if ServiceVisit.objects.filter(visit_id=study.accession).exists():
                continue

            if dry_run:
                continue

            with transaction.atomic():
                service_visit = ServiceVisit.objects.create(
                    visit_id=study.accession,
                    patient=study.patient,
                    status="REGISTERED",
                    created_by=study.created_by,
                )
                item_status = map_study_status_to_item_status(study.status)
                item = self._create_item_from_service(
                    service_visit=service_visit,
                    service=study.service,
                    price_snapshot=study.service.price,
                    status=item_status,
                    legacy_timestamp=study.created_at,
                )
                self._log_legacy_status(item, study.status, study.created_by)
                service_visit.update_derived_status()
                if service_visit.status != "REGISTERED":
                    StatusAuditLog.objects.create(
                        service_visit=service_visit,
                        from_status="REGISTERED",
                        to_status=service_visit.status,
                        reason="Legacy study-only visit status backfill.",
                        changed_by=study.created_by,
                    )
