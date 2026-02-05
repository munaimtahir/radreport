import csv
import io
import json
from pathlib import Path

from django.core.management import call_command
from django.test import TestCase

from apps.catalog.models import Modality, Service
from apps.reporting.models import ReportTemplateV2, ServiceReportTemplateV2


class V2TemplateImportTests(TestCase):
    def setUp(self):
        ReportTemplateV2.objects.all().delete()
        ServiceReportTemplateV2.objects.all().delete()
        Service.objects.all().delete()
        Modality.objects.all().delete()
        self.modality = Modality.objects.create(code="USG", name="Ultrasound")
        self.service = Service.objects.create(code="USG-ABD", name="USG Abdomen", modality=self.modality)
        self.seed_dir = Path(__file__).resolve().parents[1] / "seed_data" / "templates_v2"
        self.active_codes = {"USG_ABD_V1", "USG_KUB_V1", "USG_PELVIS_V1"}

    def test_active_seed_templates_are_schema_valid(self):
        files = list(self.seed_dir.glob("*.json"))
        payloads = [json.loads(p.read_text(encoding="utf-8")) for p in files]
        by_code = {p["code"]: p for p in payloads}

        for code in self.active_codes:
            self.assertIn(code, by_code)
            template = by_code[code]
            self.assertTrue(template["json_schema"]["properties"])
            self.assertTrue(template["ui_schema"]["ui:order"])

    def test_import_command_dry_run_makes_no_writes(self):
        call_command("import_templates_v2", "--dry-run")
        self.assertEqual(ReportTemplateV2.objects.count(), 0)
        self.assertEqual(ServiceReportTemplateV2.objects.count(), 0)

    def test_import_command_is_idempotent(self):
        call_command("import_templates_v2")
        template_count = ReportTemplateV2.objects.count()
        mapping_count = ServiceReportTemplateV2.objects.count()

        call_command("import_templates_v2")
        self.assertEqual(ReportTemplateV2.objects.count(), template_count)
        self.assertEqual(ServiceReportTemplateV2.objects.count(), mapping_count)

    def test_mapping_created_when_service_exists(self):
        call_command("import_templates_v2")
        self.assertTrue(ServiceReportTemplateV2.objects.filter(service=self.service).exists())

    def test_unresolved_service_is_reported_without_crashing(self):
        mapping_file = self.seed_dir / "tmp_unresolved_map.csv"
        with mapping_file.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["service_code", "service_name", "template_code", "is_default", "is_active"],
            )
            writer.writeheader()
            writer.writerow(
                {
                    "service_code": "USG-NON-EXISTENT",
                    "service_name": "USG Missing",
                    "template_code": "USG_ABD_V1",
                    "is_default": "true",
                    "is_active": "true",
                }
            )

        stdout = io.StringIO()
        call_command("import_templates_v2", "--mappings", str(mapping_file), stdout=stdout)
        self.assertIn("Unresolved services", stdout.getvalue())
        mapping_file.unlink(missing_ok=True)
