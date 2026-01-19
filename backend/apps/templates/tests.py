from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.templates.models import ReportTemplate, Template, ServiceReportTemplate
from apps.templates.engine import TemplatePackageEngine
from apps.catalog.models import Modality, Service

User = get_user_model()

class TemplateImportTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(username="admin", password="password", email="admin@test.com")
        self.modality = Modality.objects.create(code="USG", name="Ultrasound")
        self.service = Service.objects.create(
            code="USG_ABB", 
            name="USG Abdomen", 
            modality=self.modality,
            price=1000
        )

    def test_import_creates_report_template(self):
        data = {
            "code": "USG_BASIC",
            "name": "USG Basic Template",
            "category": "USG",
            "service_mappings": ["USG_ABB"],
            "sections": [
                {
                    "title": "Findings",
                    "fields": [
                        {
                            "key": "liver",
                            "label": "Liver",
                            "type": "short_text"
                        }
                    ]
                }
            ]
        }
        
        template, version = TemplatePackageEngine.import_package(data, mode="create", user=self.user)
        
        # Check ReportTemplate exists
        rt = ReportTemplate.objects.filter(code="USG_BASIC").first()
        self.assertIsNotNone(rt)
        self.assertEqual(rt.name, "USG Basic Template")
        self.assertEqual(rt.category, "USG")
        self.assertTrue(rt.is_active)
        
        # Check fields (heading + field)
        fields = rt.fields.order_by("order")
        self.assertEqual(fields.count(), 2)
        self.assertEqual(fields[0].field_type, "heading")
        self.assertEqual(fields[0].label, "Findings")
        self.assertEqual(fields[1].field_type, "short_text")
        self.assertEqual(fields[1].label, "Liver")
        
        # Check service mapping
        link = ServiceReportTemplate.objects.filter(service=self.service, template=rt).first()
        self.assertIsNotNone(link)

    def test_update_template(self):
        data = {
            "code": "USG_UPDATE",
            "name": "USG Initial",
            "sections": [{"title": "S1", "fields": []}]
        }
        TemplatePackageEngine.import_package(data, mode="create", user=self.user)
        
        update_data = {
            "code": "USG_UPDATE",
            "name": "USG Updated",
            "sections": [{"title": "S2", "fields": []}]
        }
        TemplatePackageEngine.import_package(update_data, mode="update", user=self.user)
        
        rt = ReportTemplate.objects.get(code="USG_UPDATE")
        self.assertEqual(rt.name, "USG Updated")
        self.assertEqual(rt.fields.filter(field_type="heading").first().label, "S2")
        self.assertEqual(rt.version, 2)
