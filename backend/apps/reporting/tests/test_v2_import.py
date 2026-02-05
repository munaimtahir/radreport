import json
import os
from pathlib import Path
import django
from django.core.management import call_command
from django.test import TestCase

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rims_backend.settings")
django.setup()
call_command("migrate", run_syncdb=True, verbosity=0)

from apps.catalog.models import Modality, Service
from apps.reporting.models import ReportTemplateV2, ServiceReportTemplateV2


class V2TemplateImportTests(TestCase):
    def setUp(self):
        self.modality = Modality.objects.create(code="USG", name="Ultrasound")
        self.service = Service.objects.create(
            code="USG-ABD",
            name="USG Abdomen",
            modality=self.modality,
        )

    def test_template_json_structure(self):
        templates_dir = Path(__file__).resolve().parents[1] / "seed_data" / "templates_v2"
        template_files = list(templates_dir.glob("*.json"))
        self.assertTrue(template_files)

        for template_file in template_files:
            payload = json.loads(template_file.read_text())
            self.assertIn("code", payload)
            self.assertIn("name", payload)
            self.assertIn("modality", payload)
            self.assertIn("status", payload)
            self.assertIn("is_frozen", payload)
            self.assertIn("json_schema", payload)
            self.assertIn("ui_schema", payload)
            self.assertIn("narrative_rules", payload)
            self.assertIn("properties", payload["json_schema"])
            self.assertIn("ui:order", payload["ui_schema"])

    def test_import_command_creates_templates_and_mappings(self):
        call_command("import_templates_v2")
        self.assertGreater(ReportTemplateV2.objects.count(), 0)
        self.assertTrue(ServiceReportTemplateV2.objects.filter(service=self.service).exists())

        template_count = ReportTemplateV2.objects.count()
        mapping_count = ServiceReportTemplateV2.objects.count()
        call_command("import_templates_v2")
        self.assertEqual(ReportTemplateV2.objects.count(), template_count)
        self.assertEqual(ServiceReportTemplateV2.objects.count(), mapping_count)

    def test_import_command_dry_run(self):
        call_command("import_templates_v2", "--dry-run")
        self.assertEqual(ReportTemplateV2.objects.count(), 0)
        self.assertEqual(ServiceReportTemplateV2.objects.count(), 0)
