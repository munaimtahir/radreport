from io import StringIO
import json
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.catalog.models import Service, Modality
from apps.reporting.models import ReportProfile, ReportParameter, ServiceReportProfile

User = get_user_model()

class AdminImportExportTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin_user = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="adminpassword"
        )
        self.client.force_authenticate(user=self.admin_user)

        self.modality_usg, _ = Modality.objects.get_or_create(code="USG", name="Ultrasound")
        self.modality_xr, _ = Modality.objects.get_or_create(code="XR", name="X-Ray")

        self.service1, _ = Service.objects.get_or_create(
            code="USG-KUB", name="USG KUB", modality=self.modality_usg, defaults={"category": "Radiology", "price": 100}
        )
        self.service2, _ = Service.objects.get_or_create(
            code="XR-CHEST", name="X-Ray Chest", modality=self.modality_xr, defaults={"category": "Radiology", "price": 150}
        )

        self.profile1, _ = ReportProfile.objects.get_or_create(
            code="USG_KUB_PROFILE", name="USG KUB Report", modality="USG"
        )
        self.profile2, _ = ReportProfile.objects.get_or_create(
            code="XR_CHEST_PROFILE", name="X-Ray Chest Report", modality="XR"
        )

        self.param1, _ = ReportParameter.objects.get_or_create(
            profile=self.profile1, slug="kidney_size", defaults={"name": "Kidney Size", "parameter_type": "number", "section": "Kidney"}
        )
        self.param2, _ = ReportParameter.objects.get_or_create(
            profile=self.profile1, slug="liver_texture", defaults={"name": "Liver Texture", "parameter_type": "short_text", "section": "Liver"}
        )
        self.param3, _ = ReportParameter.objects.get_or_create(
            profile=self.profile2, slug="lung_fields", defaults={"name": "Lung Fields", "parameter_type": "short_text", "section": "Chest"}
        )

        self.srp1, _ = ServiceReportProfile.objects.get_or_create(
            service=self.service1, profile=self.profile1
        )

    def tearDown(self):
        # Clean up created objects to avoid interference between tests
        ServiceReportProfile.objects.all().delete()
        ReportParameter.objects.all().delete()
        ReportProfile.objects.all().delete()
        Service.objects.all().delete()
        Modality.objects.all().delete()
        User.objects.all().delete()
    
    def _create_csv_file(self, content):
        csv_file = StringIO(content)
        csv_file.name = "test.csv"
        return csv_file

    def test_report_profile_template_csv(self):
        url = reverse("reporting-profiles-template-csv")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "text/csv")
        content = response.content.decode("utf-8")
        self.assertIn("code,name,modality,is_active", content)
        self.assertIn("USG_KUB", content)

    def test_report_profile_export_csv(self):
        url = reverse("reporting-profiles-export-csv")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "text/csv")
        content = response.content.decode("utf-8")
        self.assertIn(self.profile1.code, content)
        self.assertIn(self.profile2.code, content)
        self.assertNotIn("field_slug", content) # Ensure no parameter fields

    def test_report_profile_import_csv_dry_run_success(self):
        url = reverse("reporting-profiles-import-csv") + "?dry_run=true"
        csv_content = """code,name,modality,is_active,enable_narrative,narrative_mode
NEW_PROFILE,New Profile,CT,true,true,rule_based
USG_KUB_PROFILE,Updated KUB Profile,USG,false,true,rule_based
"""
        csv_file = self._create_csv_file(csv_content)
        response = self.client.post(url, {"file": csv_file}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data["created"], 1)
        self.assertEqual(response.data["updated"], 1)
        self.assertEqual(ReportProfile.objects.count(), 2) # No changes yet

    def test_report_profile_import_csv_apply_success(self):
        url = reverse("reporting-profiles-import-csv") + "?dry_run=false"
        csv_content = """code,name,modality,is_active,enable_narrative,narrative_mode
NEW_PROFILE_ACTUAL,New Profile Actual,CT,true,true,rule_based
USG_KUB_PROFILE,Updated KUB Profile,USG,false,true,rule_based
"""
        csv_file = self._create_csv_file(csv_content)
        response = self.client.post(url, {"file": csv_file}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data["profiles_created"], 1)
        self.assertEqual(response.data["profiles_updated"], 1)
        self.assertEqual(ReportProfile.objects.count(), 3)
        self.assertTrue(ReportProfile.objects.filter(code="NEW_PROFILE_ACTUAL").exists())
        self.assertFalse(ReportProfile.objects.get(code="USG_KUB_PROFILE").is_active)

    def test_report_profile_import_csv_dry_run_error(self):
        url = reverse("reporting-profiles-import-csv") + "?dry_run=true"
        csv_content = """code,name,modality
,Invalid Profile,CT
"""
        csv_file = self._create_csv_file(csv_content)
        response = self.client.post(url, {"file": csv_file}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
        self.assertIn("code is required", json.dumps(response.data))
        self.assertEqual(ReportProfile.objects.count(), 2) # No changes

    def test_report_parameter_template_csv(self):
        url = reverse("reporting-parameters-template-csv")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "text/csv")
        content = response.content.decode("utf-8")
        self.assertIn("profile_code,section,name,slug,parameter_type", content)
        self.assertIn("USG_KUB", content)

    def test_report_parameter_export_csv(self):
        url = reverse("reporting-parameters-export-csv")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "text/csv")
        content = response.content.decode("utf-8")
        self.assertIn(self.profile1.code, content)
        self.assertIn(self.param1.slug, content)
        self.assertIn(self.param2.slug, content)
        self.assertIn(self.param3.slug, content)

    def test_report_parameter_import_csv_dry_run_success(self):
        url = reverse("reporting-parameters-import-csv") + "?dry_run=true"
        csv_content = f"""profile_code,section,name,slug,parameter_type,unit,normal_value,is_required,order,options,sentence_template,narrative_role,omit_if_values_json,join_label
{self.profile1.code},New Section,New Param,new_param,number,cm,10,true,0,,,
{self.profile1.code},Kidney,Kidney Size Updated,kidney_size,number,cm,12,false,1,,,
"""
        csv_file = self._create_csv_file(csv_content)
        response = self.client.post(url, {"file": csv_file}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data["created"], 1)
        self.assertEqual(response.data["updated"], 1)
        self.assertEqual(ReportParameter.objects.count(), 3) # No changes yet

    def test_report_parameter_import_csv_apply_success(self):
        url = reverse("reporting-parameters-import-csv") + "?dry_run=false"
        csv_content = f"""profile_code,section,name,slug,parameter_type,unit,normal_value,is_required,order,options,sentence_template,narrative_role,omit_if_values_json,join_label
{self.profile1.code},New Section Actual,New Param Actual,new_param_actual,number,cm,10,true,0,,,
{self.profile1.code},Kidney,Kidney Size Updated Actual,kidney_size,number,cm,12,false,1,,,
"""
        csv_file = self._create_csv_file(csv_content)
        response = self.client.post(url, {"file": csv_file}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data["fields_created"], 1)
        self.assertEqual(response.data["fields_updated"], 1)
        self.assertEqual(ReportParameter.objects.count(), 4) # 3 + 1 new
        self.assertTrue(ReportParameter.objects.filter(slug="new_param_actual").exists())
        self.assertEqual(ReportParameter.objects.get(slug="kidney_size").name, "Kidney Size Updated Actual")

    def test_report_parameter_import_csv_dry_run_error(self):
        url = reverse("reporting-parameters-import-csv") + "?dry_run=true"
        csv_content = f"""profile_code,section,name,slug,parameter_type
{self.profile1.code},Invalid Section,Missing Type,,
"""
        csv_file = self._create_csv_file(csv_content)
        response = self.client.post(url, {"file": csv_file}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
        self.assertIn("profile_code and slug are required", json.dumps(response.data))
        self.assertEqual(ReportParameter.objects.count(), 3) # No changes

    def test_service_template_link_template_csv(self):
        url = reverse("reporting-service-profiles-template-csv")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "text/csv")
        content = response.content.decode("utf-8")
        self.assertIn("service_id,service_code,service_name,profile_id,profile_code,profile_name,enforce_single_profile,is_default", content)
        self.assertIn("XR-CHEST", content)

    def test_service_template_link_export_csv(self):
        url = reverse("reporting-service-profiles-export-csv")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "text/csv")
        content = response.content.decode("utf-8")
        self.assertIn(self.service1.code, content)
        self.assertIn(self.profile1.code, content)

    def test_service_template_link_import_csv_dry_run_success(self):
        url = reverse("reporting-service-profiles-import-csv") + "?dry_run=true"
        csv_content = f"""service_code,profile_code,enforce_single_profile,is_default
{self.service1.code},{self.profile2.code},true,false
NEW_SERVICE,NEW_PROFILE,true,true
"""
        csv_file = self._create_csv_file(csv_content)
        response = self.client.post(url, {"file": csv_file}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data) # Expect error because NEW_SERVICE/NEW_PROFILE don't exist
        self.assertIn("Service or profile not found", json.dumps(response.data))
        self.assertEqual(ServiceReportProfile.objects.count(), 1) # No changes

    def test_service_template_link_import_csv_apply_success(self):
        # Create the new service and profile first for a clean test
        Service.objects.create(code="TEMP_SVC", name="Temp Service", modality=self.modality_usg, category="Radiology", price=50)
        ReportProfile.objects.create(code="TEMP_PROF", name="Temp Profile", modality="USG")

        url = reverse("reporting-service-profiles-import-csv") + "?dry_run=false"
        csv_content = f"""service_code,profile_code,enforce_single_profile,is_default
TEMP_SVC,TEMP_PROF,true,true
{self.service1.code},{self.profile1.code},false,false
"""
        csv_file = self._create_csv_file(csv_content)
        response = self.client.post(url, {"file": csv_file}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data["created"], 1)
        self.assertEqual(response.data["updated"], 1)
        self.assertEqual(ServiceReportProfile.objects.count(), 2) # 1 existing + 1 new
        self.assertTrue(ServiceReportProfile.objects.filter(service__code="TEMP_SVC", profile__code="TEMP_PROF").exists())
        self.assertFalse(ServiceReportProfile.objects.get(service=self.service1, profile=self.profile1).is_default)
    
    def test_service_template_link_import_csv_dry_run_invalid_profile(self):
        url = reverse("reporting-service-profiles-import-csv") + "?dry_run=true"
        csv_content = f"""service_code,profile_code,enforce_single_profile,is_default
{self.service1.code},NON_EXISTENT_PROFILE,true,true
"""
        csv_file = self._create_csv_file(csv_content)
        response = self.client.post(url, {"file": csv_file}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
        self.assertIn("Service or profile not found", json.dumps(response.data))

    # --- Service Tests ---
    def test_service_template_csv(self):
        url = reverse("services-template-csv")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "text/csv")
        content = response.content.decode("utf-8")
        self.assertIn("code,name,category,modality,charges,tat_value,tat_unit,active", content)
        self.assertIn("SRV-001,Example Service,Radiology,USG,0,1,hours,true", content)

    def test_service_export_csv(self):
        url = reverse("services-export-csv")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "text/csv")
        content = response.content.decode("utf-8")
        self.assertIn(self.service1.code, content)
        self.assertIn(self.service2.code, content)

    def test_service_import_csv_dry_run_success(self):
        url = reverse("services-import-csv") + "?dry_run=true"
        csv_content = """code,name,category,modality,charges,tat_value,tat_unit,active
NEW-SERVICE,New Service Name,Radiology,USG,200,2,days,true
USG-KUB,USG KUB Updated,Radiology,USG,120,1,hours,false
"""
        csv_file = self._create_csv_file(csv_content)
        response = self.client.post(url, {"file": csv_file}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data["created"], 1)
        self.assertEqual(response.data["updated"], 1)
        self.assertEqual(Service.objects.count(), 2) # No changes yet

    def test_service_import_csv_apply_success(self):
        url = reverse("services-import-csv") + "?dry_run=false"
        csv_content = """code,name,category,modality,charges,tat_value,tat_unit,active
NEW-SERVICE-ACTUAL,New Service Name Actual,Radiology,USG,200,2,days,true
USG-KUB,USG KUB Updated Actual,Radiology,USG,120,1,hours,false
"""
        csv_file = self._create_csv_file(csv_content)
        response = self.client.post(url, {"file": csv_file}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data["created"], 1)
        self.assertEqual(response.data["updated"], 1)
        self.assertEqual(Service.objects.count(), 3) # 2 existing + 1 new
        self.assertTrue(Service.objects.filter(code="NEW-SERVICE-ACTUAL").exists())
        self.assertFalse(Service.objects.get(code="USG-KUB").is_active)

    def test_service_import_csv_dry_run_error(self):
        url = reverse("services-import-csv") + "?dry_run=true"
        csv_content = """code,name,category,modality,charges,tat_value,tat_unit,active
INVALID_CAT,Invalid Service,InvalidCategory,USG,100,1,hours,true
"""
        csv_file = self._create_csv_file(csv_content)
        response = self.client.post(url, {"file": csv_file}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
        self.assertIn("Invalid category 'InvalidCategory'", json.dumps(response.data))
        self.assertEqual(Service.objects.count(), 2) # No changes