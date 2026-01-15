from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.test import Client
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.catalog.models import Modality, Service
from apps.patients.models import Patient
from apps.templates.api import build_schema
from apps.templates.models import Template, TemplateField, TemplateSection, TemplateVersion
from apps.workflow.api import ServiceVisitViewSet, USGReportViewSet
from apps.workflow.models import ServiceVisitItem, USGReport
from apps.workflow.transitions import transition_item_status


class Command(BaseCommand):
    help = "Smoke test for production USG workflow without UI."

    def handle(self, *args, **options):
        details = []
        success = True

        def record_detail(message):
            self.stdout.write(message)
            details.append(message)

        try:
            user_model = get_user_model()
            admin_user, _ = user_model.objects.get_or_create(
                username="smoke_admin",
                defaults={
                    "email": "smoke_admin@example.com",
                    "is_superuser": True,
                    "is_staff": True,
                },
            )
            if not admin_user.is_superuser or not admin_user.is_staff:
                admin_user.is_superuser = True
                admin_user.is_staff = True
                admin_user.save(update_fields=["is_superuser", "is_staff"])

            modality, _ = Modality.objects.get_or_create(
                code="USG",
                defaults={"name": "Ultrasound"},
            )

            template, _ = Template.objects.get_or_create(
                name="SMOKE_USG Template",
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
                code="SMOKE_USG",
                defaults={
                    "modality": modality,
                    "name": "SMOKE USG Abdomen",
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

            patient, _ = Patient.objects.get_or_create(
                name="SMOKE_USG Patient",
                defaults={
                    "gender": "Other",
                    "phone": "0000000000",
                    "address": "SMOKE_USG Address",
                },
            )

            report = USGReport.objects.filter(
                service_visit_item__service=service,
                service_visit_item__service_visit__patient=patient,
            ).order_by("-created_at").first()
            item = report.service_visit_item if report else None

            if not report or not item:
                factory = APIRequestFactory()
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
                item = ServiceVisitItem.objects.filter(
                    service=service,
                    service_visit_id=visit_response.data["id"],
                ).first()
                if not item:
                    raise CommandError("Service visit item not found after creation.")

                report_payload = {
                    "service_visit_item_id": str(item.id),
                    "values": {"summary": "SMOKE USG summary"},
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
                item = report.service_visit_item

            if not isinstance(report.report_json, dict):
                report.report_json = {}
            report.report_json["summary"] = report.report_json.get("summary") or "SMOKE USG summary"
            if not report.template_version_id:
                report.template_version = published_version
            report.save()

            if item.status == "RETURNED_FOR_CORRECTION":
                transition_item_status(item, "IN_PROGRESS", admin_user, reason="Smoke reset")
                item.refresh_from_db()

            factory = APIRequestFactory()
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

            if report.report_status != "FINAL":
                raise CommandError(f"Report not FINAL: {report.report_status}")
            if item.status != "PUBLISHED":
                raise CommandError(f"Item not PUBLISHED: {item.status}")

            if not report.published_pdf_path:
                raise CommandError("Published PDF path missing.")

            media_root = Path(settings.MEDIA_ROOT).resolve()
            pdf_path = (media_root / report.published_pdf_path).resolve()
            if not str(pdf_path).startswith(str(media_root)):
                raise CommandError(f"PDF path escapes media root: {report.published_pdf_path}")
            if not pdf_path.exists():
                raise CommandError(f"PDF not found on disk: {pdf_path}")

            client = Client()
            health_response = client.get("/api/health/")
            if health_response.status_code != 200:
                raise CommandError(f"Health check failed: {health_response.status_code} {health_response.content}")
            health_json = health_response.json()
            if health_json.get("status") != "ok" or health_json.get("db") != "ok":
                raise CommandError(f"Health payload not ok: {health_json}")

            record_detail(f"Health: ok (db={health_json.get('db')})")
            record_detail(f"USG report: FINAL (id={report.id})")
            record_detail(f"PDF: {pdf_path}")
        except Exception as exc:
            success = False
            record_detail(f"Error: {exc}")

        summary = f"SMOKE_PROD_USG: {'PASS' if success else 'FAIL'}"
        self.stdout.write(summary)
        if not success:
            raise CommandError(summary)
