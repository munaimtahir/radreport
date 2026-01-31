import csv
import io
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal

from apps.catalog.models import Modality, Service
from apps.reporting.models import ServiceReportProfile, ReportProfile

User = get_user_model()


class ServiceReportProfileCSVTests(TestCase):
    """
    Comprehensive tests for ServiceReportProfile CSV endpoints:
    - template-csv: Generate CSV template
    - export-csv: Export existing data
    - import-csv: Import and create/update data
    """

    def setUp(self):
        """Set up test fixtures"""
        self.client = APIClient()
        
        # Create admin user
        self.admin_user = User.objects.create_superuser(
            username="admin",
            password="admin123",
            email="admin@test.com"
        )
        
        # Create non-admin user
        self.regular_user = User.objects.create_user(
            username="regular",
            password="regular123"
        )
        
        # Create test modality
        self.modality = Modality.objects.create(code="XR", name="X-Ray")
        
        # Create test services
        self.service1 = Service.objects.create(
            modality=self.modality,
            code="XR-CHEST",
            name="Chest X-Ray",
            price=Decimal("500.00")
        )
        self.service2 = Service.objects.create(
            modality=self.modality,
            code="XR-ABDOMEN",
            name="Abdomen X-Ray",
            price=Decimal("600.00")
        )
        
        # Create test report profiles
        self.profile1 = ReportProfile.objects.create(
            code="XR_CHEST",
            name="X-Ray Chest",
            modality="XR"
        )
        self.profile2 = ReportProfile.objects.create(
            code="XR_ABDOMEN",
            name="X-Ray Abdomen",
            modality="XR"
        )

    def test_template_csv_success(self):
        """Test successful CSV template generation"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/reporting/service-profiles/template-csv/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('attachment', response['Content-Disposition'])
        
        # Parse CSV content
        content = response.content.decode('utf-8')
        reader = csv.DictReader(io.StringIO(content))
        rows = list(reader)
        
        # Check header
        self.assertEqual(reader.fieldnames, [
            'service_id', 'service_code', 'service_name',
            'profile_id', 'profile_code', 'profile_name',
            'enforce_single_profile', 'is_default'
        ])
        
        # Check example row exists
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['service_code'], 'XR-CHEST')

    def test_template_csv_requires_auth(self):
        """Test that template-csv requires authentication"""
        response = self.client.get('/reporting/service-profiles/template-csv/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_template_csv_requires_admin(self):
        """Test that template-csv requires admin permissions"""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get('/reporting/service-profiles/template-csv/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_export_csv_no_data(self):
        """Test export with no ServiceReportProfile objects"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/reporting/service-profiles/export-csv/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'text/csv')
        
        # Parse CSV content
        content = response.content.decode('utf-8')
        reader = csv.DictReader(io.StringIO(content))
        rows = list(reader)
        
        # Should have headers but no data rows
        self.assertEqual(len(rows), 0)

    def test_export_csv_with_data(self):
        """Test export with multiple ServiceReportProfile objects"""
        # Create test links
        link1 = ServiceReportProfile.objects.create(
            service=self.service1,
            profile=self.profile1,
            enforce_single_profile=True,
            is_default=True
        )
        link2 = ServiceReportProfile.objects.create(
            service=self.service2,
            profile=self.profile2,
            enforce_single_profile=False,
            is_default=False
        )
        
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/reporting/service-profiles/export-csv/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Parse CSV content
        content = response.content.decode('utf-8')
        reader = csv.DictReader(io.StringIO(content))
        rows = list(reader)
        
        # Check data
        self.assertEqual(len(rows), 2)
        
        # Verify first row
        self.assertEqual(rows[0]['service_id'], str(self.service1.id))
        self.assertEqual(rows[0]['service_code'], 'XR-CHEST')
        self.assertEqual(rows[0]['service_name'], 'Chest X-Ray')
        self.assertEqual(rows[0]['profile_id'], str(self.profile1.id))
        self.assertEqual(rows[0]['profile_code'], 'XR_CHEST')
        self.assertEqual(rows[0]['profile_name'], 'X-Ray Chest')
        self.assertEqual(rows[0]['enforce_single_profile'], 'true')
        self.assertEqual(rows[0]['is_default'], 'true')
        
        # Verify second row
        self.assertEqual(rows[1]['service_id'], str(self.service2.id))
        self.assertEqual(rows[1]['enforce_single_profile'], 'false')
        self.assertEqual(rows[1]['is_default'], 'false')

    def test_import_csv_missing_file(self):
        """Test import without providing a file"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post('/reporting/service-profiles/import-csv/')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)
        self.assertEqual(response.data['detail'], 'CSV file required')

    def test_import_csv_invalid_file_type(self):
        """Test import with non-CSV file"""
        self.client.force_authenticate(user=self.admin_user)
        
        file_content = b"This is not a CSV file"
        file = SimpleUploadedFile("test.txt", file_content, content_type="text/plain")
        
        response = self.client.post('/reporting/service-profiles/import-csv/', {'file': file})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)
        self.assertEqual(response.data['detail'], 'File must be a CSV')

    def test_import_csv_create_new(self):
        """Test importing CSV to create new links"""
        self.client.force_authenticate(user=self.admin_user)
        
        # Create CSV content
        csv_content = f"""service_id,service_code,service_name,profile_id,profile_code,profile_name,enforce_single_profile,is_default
{self.service1.id},,Chest X-Ray,{self.profile1.id},,X-Ray Chest,true,true
,{self.service2.code},Abdomen X-Ray,,{self.profile2.code},X-Ray Abdomen,false,false
"""
        
        file = SimpleUploadedFile("links.csv", csv_content.encode('utf-8'), content_type="text/csv")
        response = self.client.post('/reporting/service-profiles/import-csv/', {'file': file})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['created'], 2)
        self.assertEqual(response.data['updated'], 0)
        
        # Verify links were created
        self.assertEqual(ServiceReportProfile.objects.count(), 2)
        
        link1 = ServiceReportProfile.objects.get(service=self.service1, profile=self.profile1)
        self.assertTrue(link1.enforce_single_profile)
        self.assertTrue(link1.is_default)
        
        link2 = ServiceReportProfile.objects.get(service=self.service2, profile=self.profile2)
        self.assertFalse(link2.enforce_single_profile)
        self.assertFalse(link2.is_default)

    def test_import_csv_update_existing(self):
        """Test importing CSV to update existing links"""
        # Create existing link
        link = ServiceReportProfile.objects.create(
            service=self.service1,
            profile=self.profile1,
            enforce_single_profile=True,
            is_default=True
        )
        
        self.client.force_authenticate(user=self.admin_user)
        
        # Create CSV with updated values
        csv_content = f"""service_id,service_code,service_name,profile_id,profile_code,profile_name,enforce_single_profile,is_default
{self.service1.id},,Chest X-Ray,{self.profile1.id},,X-Ray Chest,false,false
"""
        
        file = SimpleUploadedFile("links.csv", csv_content.encode('utf-8'), content_type="text/csv")
        response = self.client.post('/reporting/service-profiles/import-csv/', {'file': file})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['created'], 0)
        self.assertEqual(response.data['updated'], 1)
        
        # Verify link was updated
        link.refresh_from_db()
        self.assertFalse(link.enforce_single_profile)
        self.assertFalse(link.is_default)

    def test_import_csv_mixed_create_update(self):
        """Test importing CSV with both new and existing links"""
        # Create one existing link
        ServiceReportProfile.objects.create(
            service=self.service1,
            profile=self.profile1,
            enforce_single_profile=True,
            is_default=True
        )
        
        self.client.force_authenticate(user=self.admin_user)
        
        # CSV with one update and one create
        csv_content = f"""service_id,service_code,service_name,profile_id,profile_code,profile_name,enforce_single_profile,is_default
{self.service1.id},,Chest X-Ray,{self.profile1.id},,X-Ray Chest,false,false
{self.service2.id},,Abdomen X-Ray,{self.profile2.id},,X-Ray Abdomen,true,true
"""
        
        file = SimpleUploadedFile("links.csv", csv_content.encode('utf-8'), content_type="text/csv")
        response = self.client.post('/reporting/service-profiles/import-csv/', {'file': file})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['created'], 1)
        self.assertEqual(response.data['updated'], 1)

    def test_import_csv_invalid_service(self):
        """Test importing CSV with invalid service reference"""
        self.client.force_authenticate(user=self.admin_user)
        
        csv_content = f"""service_id,service_code,service_name,profile_id,profile_code,profile_name,enforce_single_profile,is_default
99999,,Invalid Service,{self.profile1.id},,X-Ray Chest,true,true
"""
        
        file = SimpleUploadedFile("links.csv", csv_content.encode('utf-8'), content_type="text/csv")
        response = self.client.post('/reporting/service-profiles/import-csv/', {'file': file})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('errors', response.data)
        self.assertEqual(len(response.data['errors']), 1)
        self.assertIn('Service or profile not found', response.data['errors'][0]['error'])

    def test_import_csv_invalid_profile(self):
        """Test importing CSV with invalid profile reference"""
        self.client.force_authenticate(user=self.admin_user)
        
        csv_content = f"""service_id,service_code,service_name,profile_id,profile_code,profile_name,enforce_single_profile,is_default
{self.service1.id},,Chest X-Ray,99999,,Invalid Profile,true,true
"""
        
        file = SimpleUploadedFile("links.csv", csv_content.encode('utf-8'), content_type="text/csv")
        response = self.client.post('/reporting/service-profiles/import-csv/', {'file': file})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('errors', response.data)

    def test_import_csv_boolean_parsing(self):
        """Test various boolean string representations"""
        self.client.force_authenticate(user=self.admin_user)
        
        # Test different boolean representations
        csv_content = f"""service_id,service_code,service_name,profile_id,profile_code,profile_name,enforce_single_profile,is_default
{self.service1.id},,Chest X-Ray,{self.profile1.id},,X-Ray Chest,yes,1
{self.service2.id},,Abdomen X-Ray,{self.profile2.id},,X-Ray Abdomen,no,0
"""
        
        file = SimpleUploadedFile("links.csv", csv_content.encode('utf-8'), content_type="text/csv")
        response = self.client.post('/reporting/service-profiles/import-csv/', {'file': file})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['created'], 2)
        
        # Verify boolean parsing
        link1 = ServiceReportProfile.objects.get(service=self.service1)
        self.assertTrue(link1.enforce_single_profile)
        self.assertTrue(link1.is_default)
        
        link2 = ServiceReportProfile.objects.get(service=self.service2)
        self.assertFalse(link2.enforce_single_profile)
        self.assertFalse(link2.is_default)

    def test_import_csv_utf8_bom(self):
        """Test importing CSV with UTF-8 BOM encoding"""
        self.client.force_authenticate(user=self.admin_user)
        
        # Create CSV with UTF-8 BOM
        csv_content = f"""service_id,service_code,service_name,profile_id,profile_code,profile_name,enforce_single_profile,is_default
{self.service1.id},,Chest X-Ray,{self.profile1.id},,X-Ray Chest,true,true
"""
        # Add UTF-8 BOM
        bom_content = '\ufeff' + csv_content
        
        file = SimpleUploadedFile("links.csv", bom_content.encode('utf-8'), content_type="text/csv")
        response = self.client.post('/reporting/service-profiles/import-csv/', {'file': file})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['created'], 1)
        self.assertEqual(ServiceReportProfile.objects.count(), 1)

    def test_import_csv_partial_failure(self):
        """Test importing CSV with some valid and some invalid rows"""
        self.client.force_authenticate(user=self.admin_user)
        
        # Mix of valid and invalid rows
        csv_content = f"""service_id,service_code,service_name,profile_id,profile_code,profile_name,enforce_single_profile,is_default
{self.service1.id},,Chest X-Ray,{self.profile1.id},,X-Ray Chest,true,true
99999,,Invalid Service,{self.profile2.id},,X-Ray Abdomen,true,true
{self.service2.id},,Abdomen X-Ray,{self.profile2.id},,X-Ray Abdomen,false,false
"""
        
        file = SimpleUploadedFile("links.csv", csv_content.encode('utf-8'), content_type="text/csv")
        response = self.client.post('/reporting/service-profiles/import-csv/', {'file': file})
        
        # Should return 400 with partial success info
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['created'], 2)
        self.assertEqual(response.data['updated'], 0)
        self.assertEqual(len(response.data['errors']), 1)
        
        # Verify successful rows were created
        self.assertEqual(ServiceReportProfile.objects.count(), 2)

    def test_import_csv_empty_boolean_defaults(self):
        """Test that empty boolean fields use defaults"""
        self.client.force_authenticate(user=self.admin_user)
        
        csv_content = f"""service_id,service_code,service_name,profile_id,profile_code,profile_name,enforce_single_profile,is_default
{self.service1.id},,Chest X-Ray,{self.profile1.id},,X-Ray Chest,,
"""
        
        file = SimpleUploadedFile("links.csv", csv_content.encode('utf-8'), content_type="text/csv")
        response = self.client.post('/reporting/service-profiles/import-csv/', {'file': file})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check defaults (should be True according to the code)
        link = ServiceReportProfile.objects.get(service=self.service1, profile=self.profile1)
        self.assertTrue(link.enforce_single_profile)
        self.assertTrue(link.is_default)

    def test_import_csv_requires_auth(self):
        """Test that import requires authentication"""
        csv_content = "service_id,service_code,service_name,profile_id,profile_code,profile_name,enforce_single_profile,is_default\n"
        file = SimpleUploadedFile("links.csv", csv_content.encode('utf-8'), content_type="text/csv")
        
        response = self.client.post('/reporting/service-profiles/import-csv/', {'file': file})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_import_csv_requires_admin(self):
        """Test that import requires admin permissions"""
        self.client.force_authenticate(user=self.regular_user)
        
        csv_content = "service_id,service_code,service_name,profile_id,profile_code,profile_name,enforce_single_profile,is_default\n"
        file = SimpleUploadedFile("links.csv", csv_content.encode('utf-8'), content_type="text/csv")
        
        response = self.client.post('/reporting/service-profiles/import-csv/', {'file': file})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_import_csv_service_by_code(self):
        """Test resolving service by code instead of ID"""
        self.client.force_authenticate(user=self.admin_user)
        
        csv_content = f"""service_id,service_code,service_name,profile_id,profile_code,profile_name,enforce_single_profile,is_default
,{self.service1.code},Chest X-Ray,{self.profile1.id},,X-Ray Chest,true,true
"""
        
        file = SimpleUploadedFile("links.csv", csv_content.encode('utf-8'), content_type="text/csv")
        response = self.client.post('/reporting/service-profiles/import-csv/', {'file': file})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['created'], 1)
        
        # Verify link was created with correct service
        link = ServiceReportProfile.objects.get(profile=self.profile1)
        self.assertEqual(link.service, self.service1)

    def test_import_csv_profile_by_code(self):
        """Test resolving profile by code instead of ID"""
        self.client.force_authenticate(user=self.admin_user)
        
        csv_content = f"""service_id,service_code,service_name,profile_id,profile_code,profile_name,enforce_single_profile,is_default
{self.service1.id},,Chest X-Ray,,{self.profile1.code},X-Ray Chest,true,true
"""
        
        file = SimpleUploadedFile("links.csv", csv_content.encode('utf-8'), content_type="text/csv")
        response = self.client.post('/reporting/service-profiles/import-csv/', {'file': file})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['created'], 1)
        
        # Verify link was created with correct profile
        link = ServiceReportProfile.objects.get(service=self.service1)
        self.assertEqual(link.profile, self.profile1)
