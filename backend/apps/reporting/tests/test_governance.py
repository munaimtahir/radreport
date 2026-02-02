"""
Tests for Template Governance v1

Tests cover:
- Clone copies parameters/options
- Activate ensures single active per code
- Freeze blocks edits
- Archive blocked for active version
- Audit logs created for each action
- used_by_reports count correct
"""
import json
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status as http_status

from apps.reporting.models import (
    ReportProfile, ReportParameter, ReportParameterOption,
    ReportInstance, TemplateAuditLog
)
from apps.workflow.models import ServiceVisitItem, ServiceVisit
from apps.patients.models import Patient
from apps.catalog.models import Service, Modality

User = get_user_model()


class TemplateGovernanceTestCase(TestCase):
    """Test template governance actions."""

    def setUp(self):
        """Set up test data."""
        self.admin_user = User.objects.create_superuser(
            username="admin",
            email="admin@test.com",
            password="testpass123"
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin_user)
        
        # Create a test profile with parameters
        self.profile = ReportProfile.objects.create(
            code="TEST_PROFILE",
            name="Test Profile",
            modality="USG",
            version=1,
            status="active",
            is_frozen=False,
        )
        
        # Create parameters with options
        self.param = ReportParameter.objects.create(
            profile=self.profile,
            section="Test Section",
            name="Test Parameter",
            slug="test_param",
            parameter_type="dropdown",
            order=1,
        )
        
        ReportParameterOption.objects.create(
            parameter=self.param,
            label="Option 1",
            value="opt1",
            order=0,
        )
        ReportParameterOption.objects.create(
            parameter=self.param,
            label="Option 2",
            value="opt2",
            order=1,
        )

    def test_clone_copies_parameters_and_options(self):
        """Test that cloning a profile copies all parameters and options."""
        url = f"/api/reporting/governance/{self.profile.id}/clone/"
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, http_status.HTTP_201_CREATED)
        
        # Check new profile was created
        new_profile_id = response.data["profile"]["id"]
        new_profile = ReportProfile.objects.get(id=new_profile_id)
        
        self.assertEqual(new_profile.code, self.profile.code)
        self.assertEqual(new_profile.version, 2)
        self.assertEqual(new_profile.status, "draft")
        self.assertEqual(new_profile.revision_of, self.profile)
        
        # Check parameters were copied
        new_params = new_profile.parameters.all()
        self.assertEqual(new_params.count(), 1)
        
        new_param = new_params.first()
        self.assertEqual(new_param.name, self.param.name)
        self.assertEqual(new_param.slug, self.param.slug)
        
        # Check options were copied
        new_options = new_param.options.all()
        self.assertEqual(new_options.count(), 2)

    def test_activate_deactivates_other_versions(self):
        """Test that activating a version deactivates other active versions."""
        # Create a draft version
        draft_profile = ReportProfile.objects.create(
            code="TEST_PROFILE",
            name="Test Profile v2",
            modality="USG",
            version=2,
            status="draft",
            revision_of=self.profile,
        )
        
        url = f"/api/reporting/governance/{draft_profile.id}/activate/"
        response = self.client.post(url, {"confirmation": "ACTIVATE"}, format="json")
        
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        
        # Check draft is now active
        draft_profile.refresh_from_db()
        self.assertEqual(draft_profile.status, "active")
        
        # Check original is now archived
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.status, "archived")

    def test_activate_requires_confirmation(self):
        """Test that activation requires confirmation phrase."""
        draft_profile = ReportProfile.objects.create(
            code="TEST_PROFILE",
            name="Test Profile v2",
            modality="USG",
            version=2,
            status="draft",
        )
        
        url = f"/api/reporting/governance/{draft_profile.id}/activate/"
        
        # Without confirmation
        response = self.client.post(url)
        self.assertEqual(response.status_code, http_status.HTTP_400_BAD_REQUEST)
        self.assertTrue(response.data.get("requires_confirmation"))
        
        # With wrong confirmation
        response = self.client.post(url, {"confirmation": "WRONG"}, format="json")
        self.assertEqual(response.status_code, http_status.HTTP_400_BAD_REQUEST)

    def test_freeze_blocks_edits(self):
        """Test that frozen profiles cannot be edited."""
        # Freeze the profile
        freeze_url = f"/api/reporting/governance/{self.profile.id}/freeze/"
        response = self.client.post(freeze_url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        
        self.profile.refresh_from_db()
        self.assertTrue(self.profile.is_frozen)
        
        # Try to edit
        edit_url = f"/api/reporting/profiles/{self.profile.id}/"
        response = self.client.patch(edit_url, {"name": "New Name"}, format="json")
        self.assertEqual(response.status_code, http_status.HTTP_403_FORBIDDEN)

    def test_unfreeze_allows_edits(self):
        """Test that unfreezing allows edits again."""
        self.profile.is_frozen = True
        self.profile.status = "draft"  # Non-active profile
        self.profile.save()
        
        # Unfreeze
        url = f"/api/reporting/governance/{self.profile.id}/unfreeze/"
        response = self.client.post(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        
        self.profile.refresh_from_db()
        self.assertFalse(self.profile.is_frozen)

    def test_archive_blocked_for_active(self):
        """Test that active profiles cannot be archived."""
        url = f"/api/reporting/governance/{self.profile.id}/archive/"
        response = self.client.post(url, {"confirmation": "ARCHIVE"}, format="json")
        
        self.assertEqual(response.status_code, http_status.HTTP_400_BAD_REQUEST)
        self.assertIn("active", response.data["detail"].lower())

    def test_archive_requires_confirmation(self):
        """Test that archiving requires confirmation phrase."""
        # Create a draft profile
        draft = ReportProfile.objects.create(
            code="DRAFT_PROFILE",
            name="Draft Profile",
            modality="USG",
            version=1,
            status="draft",
        )
        
        url = f"/api/reporting/governance/{draft.id}/archive/"
        
        # Without confirmation
        response = self.client.post(url)
        self.assertEqual(response.status_code, http_status.HTTP_400_BAD_REQUEST)
        self.assertTrue(response.data.get("requires_confirmation"))

    def test_audit_logs_created(self):
        """Test that audit logs are created for governance actions."""
        # Clear any existing logs
        TemplateAuditLog.objects.all().delete()
        
        # Clone
        url = f"/api/reporting/governance/{self.profile.id}/clone/"
        self.client.post(url)
        
        # Check log was created
        logs = TemplateAuditLog.objects.filter(action="clone")
        self.assertEqual(logs.count(), 1)
        self.assertEqual(logs.first().entity_type, "report_profile")
        
        # Freeze
        freeze_url = f"/api/reporting/governance/{self.profile.id}/freeze/"
        self.client.post(freeze_url)
        
        freeze_logs = TemplateAuditLog.objects.filter(action="freeze")
        self.assertEqual(freeze_logs.count(), 1)

    def test_used_by_reports_count(self):
        """Test that used_by_reports count is correct."""
        # Initially 0
        url = f"/api/reporting/profiles/{self.profile.id}/"
        response = self.client.get(url)
        self.assertEqual(response.data["used_by_reports"], 0)
        
        # Create required related objects
        modality = Modality.objects.create(name="Ultrasound", code="USG")
        service = Service.objects.create(name="Test Service", code="TESTSVC", modality=modality, category="Radiology")
        patient = Patient.objects.create(name="Test Patient", mrn="MR001")
        service_visit = ServiceVisit.objects.create(patient=patient)
        svi = ServiceVisitItem.objects.create(
            service_visit=service_visit, 
            service=service,
            service_name_snapshot=service.name,
            department_snapshot="USG",
            price_snapshot=100,
        )
        
        ReportInstance.objects.create(
            service_visit_item=svi,
            profile=self.profile,
            status="draft",
        )
        
        # Check count is now 1
        response = self.client.get(url)
        self.assertEqual(response.data["used_by_reports"], 1)

    def test_active_with_reports_cannot_be_edited_destructively(self):
        """Test that active profiles with reports block destructive edits."""
        # Create related objects for a report
        modality = Modality.objects.create(name="CT Scan", code="CT")
        service = Service.objects.create(name="Test Svc 2", code="TESTSVC2", modality=modality, category="Radiology")
        patient = Patient.objects.create(name="Test Patient 2", mrn="MR002")
        service_visit = ServiceVisit.objects.create(patient=patient)
        svi = ServiceVisitItem.objects.create(
            service_visit=service_visit, 
            service=service,
            service_name_snapshot=service.name,
            department_snapshot="CT",
            price_snapshot=100,
        )
        
        ReportInstance.objects.create(
            service_visit_item=svi,
            profile=self.profile,
            status="draft",
        )
        
        # Try to edit
        url = f"/api/reporting/profiles/{self.profile.id}/"
        response = self.client.patch(url, {"name": "New Name"}, format="json")
        
        # Should be blocked
        self.assertEqual(response.status_code, http_status.HTTP_403_FORBIDDEN)

    def test_delete_blocked_for_active(self):
        """Test that active profiles cannot be deleted."""
        url = f"/api/reporting/profiles/{self.profile.id}/"
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, http_status.HTTP_403_FORBIDDEN)
        
        # Profile should still exist
        self.assertTrue(ReportProfile.objects.filter(id=self.profile.id).exists())

    def test_versions_endpoint(self):
        """Test the versions endpoint returns all versions of a profile."""
        # Create another version
        ReportProfile.objects.create(
            code="TEST_PROFILE",
            name="Test Profile v2",
            modality="USG",
            version=2,
            status="draft",
        )
        
        url = f"/api/reporting/governance/{self.profile.id}/versions/"
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(response.data["code"], "TEST_PROFILE")
        self.assertEqual(len(response.data["versions"]), 2)


class AuditLogAPITestCase(TestCase):
    """Test the audit log API."""

    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username="admin",
            email="admin@test.com",
            password="testpass123"
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin_user)
        
        # Create some audit logs
        TemplateAuditLog.objects.create(
            actor=self.admin_user,
            action="clone",
            entity_type="report_profile",
            entity_id="test-id-1",
            metadata={"test": "data"},
        )
        TemplateAuditLog.objects.create(
            actor=self.admin_user,
            action="activate",
            entity_type="report_profile",
            entity_id="test-id-2",
        )
        TemplateAuditLog.objects.create(
            actor=self.admin_user,
            action="import",
            entity_type="report_parameter",
            entity_id="test-id-3",
        )

    def test_list_audit_logs(self):
        """Test listing all audit logs."""
        url = "/api/reporting/audit-logs/"
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        # Should return all 3 logs (or paginated)
        results = response.data if isinstance(response.data, list) else response.data.get("results", response.data)
        self.assertGreaterEqual(len(results), 3)

    def test_filter_by_entity_type(self):
        """Test filtering audit logs by entity type."""
        url = "/api/reporting/audit-logs/?entity=report_parameter"
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        results = response.data if isinstance(response.data, list) else response.data.get("results", response.data)
        self.assertEqual(len(results), 1)

    def test_filter_by_action(self):
        """Test filtering audit logs by action."""
        url = "/api/reporting/audit-logs/?action=clone"
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        results = response.data if isinstance(response.data, list) else response.data.get("results", response.data)
        self.assertEqual(len(results), 1)

    def test_export_csv(self):
        """Test exporting audit logs to CSV."""
        url = "/api/reporting/audit-logs/export-csv/"
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "text/csv")
        self.assertIn("attachment", response["Content-Disposition"])
