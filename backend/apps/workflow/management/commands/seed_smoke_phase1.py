from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.catalog.models import Modality, Service
from apps.patients.models import Patient
from apps.templates.api import build_schema
from apps.templates.models import Template, TemplateField, TemplateSection, TemplateVersion
from apps.workflow.api import ServiceVisitViewSet, USGReportViewSet
from apps.workflow.models import ServiceVisit, USGReport
from apps.workflow.transitions import transition_item_status


class Command(BaseCommand):
    help = "Seed and smoke-test Phase 1 USG workflow (registration → USG → verify → PDF)."

    def handle(self, *args, **options):
        user_model = get_user_model()
        admin_user = user_model.objects.filter(is_superuser=True).first()
        if not admin_user:
            admin_user = user_model.objects.create_superuser(
                username="phase1_admin",
                email="phase1_admin@example.com",
                password="phase1_admin",
            )

        modality, _ = Modality.objects.get_or_create(
            code="USG",
            defaults={"name": "Ultrasound"},
        )

        template, _ = Template.objects.get_or_create(
            name="Phase 1 USG Template",
            modality_code="USG",
            defaults={"is_active": True},
        )
        section, _ = TemplateSection.objects.get_or_create(
            template=template,
            title="Findings",
            defaults={"order": 1},
        )
        field, _ = TemplateField.objects.get_or_create(
            section=section,
            key="summary",
            defaults={
                "label": "Summary",
                "field_type": "short_text",
                "required": True,
                "order": 1,
            },
        )
        if not field.required or field.field_type != "short_text":
            field.required = True
            field.field_type = "short_text"
            field.save(update_fields=["required", "field_type"])

        published_version = template.versions.filter(is_published=True).order_by("-version").first()
        if not published_version:
            latest_version = template.versions.order_by("-version").first()
            next_version = 1 if not latest_version else latest_version.version + 1
            published_version = TemplateVersion.objects.create(
                template=template,
                version=next_version,
                schema=build_schema(template),
                is_published=True,
            )

        service, _ = Service.objects.get_or_create(
            code="USG-PHASE1",
            defaults={
                "modality": modality,
                "name": "USG Abdomen",
                "category": "Radiology",
                "price": Decimal("500.00"),
                "charges": Decimal("500.00"),
                "default_price": Decimal("500.00"),
                "is_active": True,
            },
        )
        service_updates = []
        if service.default_template_id != template.id:
            service.default_template = template
            service_updates.append("default_template")
        if not service.is_active:
            service.is_active = True
            service_updates.append("is_active")
        if service_updates:
            service.save(update_fields=service_updates)

        patient = Patient.objects.filter(name="Phase1 Seed Patient").first()
        if not patient:
            patient = Patient.objects.create(
                name="Phase1 Seed Patient",
                gender="Other",
                phone="0000000000",
                address="Phase1 Seed Address",
            )

        # NOTE: This JSON key lookup (`report_json__seed_marker`) relies on PostgreSQL's
        # JSON/JSONB field support for nested key lookups and is intended to run against
        # a PostgreSQL database. Behavior may differ on other database backends.
        report = USGReport.objects.filter(report_json__seed_marker="phase1").first()
        service_visit = None
        item = None
        factory = APIRequestFactory()

        if report:
            service_visit = report.service_visit_item.service_visit if report.service_visit_item else report.service_visit
            if report.service_visit_item:
                item = report.service_visit_item
            elif service_visit:
                item = service_visit.items.filter(service=service).first()
                if item:
                    report.service_visit_item = item
                    report.save(update_fields=["service_visit_item"])

        if not report or not item or not service_visit:
            visit_payload = {
                "patient_id": str(patient.id),
                "service_ids": [str(service.id)],
                "subtotal": str(service.price),
                "discount": "0",
                "total_amount": str(service.price),
                "net_amount": str(service.price),
                "amount_paid": str(service.price),
                "payment_method": "cash",
            }
            visit_request = factory.post(
                "/api/workflow/visits/create_visit/",
                visit_payload,
                format="json",
                HTTP_HOST="localhost",
            )
            force_authenticate(visit_request, user=admin_user)
            visit_response = ServiceVisitViewSet.as_view({"post": "create_visit"})(visit_request)
            if visit_response.status_code != 201:
                raise CommandError(f"Service visit creation failed: {visit_response.data}")
            service_visit = ServiceVisit.objects.get(id=visit_response.data["id"])
            item = service_visit.items.filter(service=service).first()
            if not item:
                raise CommandError("Service visit item not found after creation.")

            report_payload = {
                "service_visit_item_id": str(item.id),
                "values": {"summary": "Normal abdominal ultrasound.", "seed_marker": "phase1"},
            }
            report_request = factory.post(
                "/api/workflow/usg/",
                report_payload,
                format="json",
                HTTP_HOST="localhost",
            )
            force_authenticate(report_request, user=admin_user)
            report_response = USGReportViewSet.as_view({"post": "create"})(report_request)
            if report_response.status_code not in [200, 201]:
                raise CommandError(f"USG report creation failed: {report_response.data}")
            report = USGReport.objects.get(id=report_response.data["id"])

        if not isinstance(report.report_json, dict):
            report.report_json = {}
        report.report_json.setdefault("summary", "Normal abdominal ultrasound.")
        report.report_json["seed_marker"] = "phase1"
        if not report.template_version_id:
            report.template_version = published_version
        report.save()

        item = report.service_visit_item
        if not item:
            raise CommandError("USG report is missing a service visit item.")

        if item.status == "RETURNED_FOR_CORRECTION":
            transition_item_status(item, "IN_PROGRESS", admin_user, reason="Phase1 seed reset")
            item.refresh_from_db()

        if item.status in ["REGISTERED", "IN_PROGRESS"]:
            submit_request = factory.post(
                f"/api/workflow/usg/{report.id}/submit_for_verification/",
                {"values": report.report_json},
                format="json",
                HTTP_HOST="localhost",
            )
            force_authenticate(submit_request, user=admin_user)
            submit_response = USGReportViewSet.as_view({"post": "submit_for_verification"})(submit_request, pk=str(report.id))
            if submit_response.status_code != 200:
                raise CommandError(f"Submit for verification failed: {submit_response.data}")
            item.refresh_from_db()

        if item.status == "PENDING_VERIFICATION":
            publish_request = factory.post(
                f"/api/workflow/usg/{report.id}/publish/",
                {},
                format="json",
                HTTP_HOST="localhost",
            )
            force_authenticate(publish_request, user=admin_user)
            publish_response = USGReportViewSet.as_view({"post": "publish"})(publish_request, pk=str(report.id))
            if publish_response.status_code != 200:
                raise CommandError(f"Publish failed: {publish_response.data}")

        report.refresh_from_db()
        item.refresh_from_db()
        service_visit = item.service_visit

        self.stdout.write("Phase 1 seed complete:")
        self.stdout.write(f"- Patient ID: {patient.id}")
        self.stdout.write(f"- Service ID: {service.id}")
        self.stdout.write(f"- Template ID: {template.id}")
        self.stdout.write(f"- Template Version ID: {published_version.id}")
        self.stdout.write(f"- Service Visit ID: {service_visit.id} (visit_id={service_visit.visit_id})")
        self.stdout.write(f"- Service Visit Item ID: {item.id} (status={item.status})")
        self.stdout.write(f"- USG Report ID: {report.id} (status={report.report_status})")
        self.stdout.write(f"- Published PDF Path: {report.published_pdf_path or 'N/A'}")
