import json
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from apps.catalog.models import Modality, Service
from apps.patients.models import Patient
from apps.reporting.models import ReportInstanceV2, ReportTemplateV2, ServiceReportTemplateV2
from apps.workflow.models import ServiceVisit, ServiceVisitItem


class Command(BaseCommand):
    help = "Seed minimal V2 reporting data for Playwright E2E tests (idempotent)."

    def add_arguments(self, parser):
        parser.add_argument("--json-out", required=True, help="Path to write seed JSON output")
        parser.add_argument("--username", default="e2e_reporter")
        parser.add_argument("--password", default="e2e_password")
        parser.add_argument("--template-code", default="USG_ABD_V1")
        parser.add_argument("--template-file", default="")
        parser.add_argument("--service-code", default="E2E-USG-ABD")
        parser.add_argument("--service-name", default="E2E USG Abdomen")
        parser.add_argument("--patient-name", default="E2E Patient")
        parser.add_argument("--patient-phone", default="0000000000")

    def handle(self, *args, **options):
        username = options["username"]
        password = options["password"]
        template_code = options["template_code"]
        template_file = options["template_file"]
        service_code = options["service_code"]
        service_name = options["service_name"]
        patient_name = options["patient_name"]
        patient_phone = options["patient_phone"]
        json_out = Path(options["json_out"])

        user_model = get_user_model()
        user, _ = user_model.objects.get_or_create(
            username=username,
            defaults={"is_staff": True, "is_superuser": True},
        )
        if not user.is_staff or not user.is_superuser:
            user.is_staff = True
            user.is_superuser = True
            user.save(update_fields=["is_staff", "is_superuser"])
        if not user.check_password(password):
            user.set_password(password)
            user.save(update_fields=["password"])

        template = ReportTemplateV2.objects.filter(code=template_code).first()
        if not template:
            data = self._load_template_data(template_code, template_file)
            template = ReportTemplateV2.objects.create(
                code=data.get("code", template_code),
                name=data.get("name", template_code),
                modality=data.get("modality", "USG"),
                status="active",
                json_schema=data.get("json_schema") or {},
                ui_schema=data.get("ui_schema") or {},
                narrative_rules=data.get("narrative_rules") or {},
                is_frozen=bool(data.get("is_frozen", False)),
            )
        elif template.status != "active":
            template.status = "active"
            template.save(update_fields=["status", "updated_at"])

        modality, _ = Modality.objects.get_or_create(code="USG", defaults={"name": "Ultrasound"})
        service, _ = Service.objects.get_or_create(
            code=service_code,
            defaults={
                "modality": modality,
                "name": service_name,
                "category": "Radiology",
                "price": 0,
                "charges": 0,
                "default_price": 0,
                "is_active": True,
            },
        )

        mapping, created = ServiceReportTemplateV2.objects.get_or_create(
            service=service,
            template=template,
            defaults={"is_active": True, "is_default": True},
        )
        if created or not mapping.is_active or not mapping.is_default:
            ServiceReportTemplateV2.objects.filter(service=service).update(is_default=False)
            mapping.is_active = True
            mapping.is_default = True
            mapping.save(update_fields=["is_active", "is_default"])

        patient, _ = Patient.objects.get_or_create(
            name=patient_name,
            phone=patient_phone,
            defaults={"age": 42, "gender": "Male"},
        )

        item = (
            ServiceVisitItem.objects.filter(service=service, service_visit__patient=patient)
            .select_related("service_visit")
            .order_by("-created_at")
            .first()
        )

        if not item:
            visit = ServiceVisit.objects.create(patient=patient, created_by=user)
            item = ServiceVisitItem.objects.create(service_visit=visit, service=service, status="REGISTERED")
        else:
            if item.service_visit.created_by_id != user.id:
                item.service_visit.created_by = user
                item.service_visit.save(update_fields=["created_by"])
            item.status = "REGISTERED"
            item.started_at = None
            item.submitted_at = None
            item.verified_at = None
            item.published_at = None
            item.save(update_fields=["status", "started_at", "submitted_at", "verified_at", "published_at"])
            item.service_visit.update_derived_status()

        instance, _ = ReportInstanceV2.objects.get_or_create(
            work_item=item,
            defaults={"template_v2": template, "created_by": user, "status": "draft"},
        )
        if instance.template_v2_id != template.id:
            instance.template_v2 = template
        instance.created_by = user
        instance.status = "draft"
        instance.values_json = {}
        instance.narrative_json = {}
        instance.save()
        instance.publish_snapshots_v2.all().delete()

        payload = {
            "username": username,
            "password": password,
            "workitemId": str(item.id),
            "reportTemplateCode": template.code,
            "reportInstanceId": str(instance.id),
            "patientName": patient.name,
            "patientMrn": patient.mrn,
            "serviceCode": service.code,
            "visitId": str(item.service_visit_id),
        }

        json_out.parent.mkdir(parents=True, exist_ok=True)
        json_out.write_text(json.dumps(payload, indent=2))
        self.stdout.write(self.style.SUCCESS(f"E2E seed complete. JSON written to {json_out}"))

    def _load_template_data(self, template_code: str, template_file: str) -> dict:
        if template_file:
            path = Path(template_file)
        else:
            seed_root = Path(__file__).resolve().parents[2] / "seed_data" / "templates_v2" / "library" / "phase2_v1.1"
            path = seed_root / f"{template_code}.json"
        if not path.exists():
            raise CommandError(f"Template seed file not found: {path}")
        return json.loads(path.read_text())
