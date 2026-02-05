from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from django.utils import timezone
import tempfile
import shutil
from apps.catalog.models import Modality, Service
from apps.patients.models import Patient
from apps.workflow.models import ServiceVisit, ServiceVisitItem
from apps.reporting.models import (
    ReportProfile,
    ServiceReportProfile,
    ReportTemplateV2,
    ServiceReportTemplateV2,
    ReportInstanceV2,
    ReportActionLogV2
)

User = get_user_model()

# Create a valid temp dir
TEMP_MEDIA_ROOT = tempfile.mkdtemp()

@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class WorkItemV2WorkflowTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.client = APIClient()
        self.reporter = User.objects.create_user(username="reporter", password="password")
        self.verifier = User.objects.create_user(username="verifier", password="password")
        
        # Setup verifier group
        verifier_group = Group.objects.create(name="reporting_verifier")
        self.verifier.groups.add(verifier_group)

        self.modality = Modality.objects.create(code="XR", name="X-Ray")
        self.service = Service.objects.create(
            modality=self.modality,
            name="Chest X-Ray",
            code="XR-CXR-001",
            price=500,
        )
        self.patient = Patient.objects.create(
            name="V2 Patient", age=42, gender="Male", phone="1234567890"
        )
        self.visit = ServiceVisit.objects.create(patient=self.patient, created_by=self.reporter)
        self.item = ServiceVisitItem.objects.create(
            service_visit=self.visit,
            service=self.service,
            status="REGISTERED",
        )
        
        # Setup V2 Template
        self.template = ReportTemplateV2.objects.create(
            code="CXR_V2",
            name="CXR V2",
            modality="XR",
            status="active",
            json_schema={"type": "object", "properties": {"note": {"type": "string"}}},
            ui_schema={},
            narrative_rules={},
            is_frozen=False
        )
        ServiceReportTemplateV2.objects.create(
            service=self.service,
            template=self.template,
            is_active=True,
            is_default=True,
        )

    def test_workflow_happy_path(self):
        """Submit -> Verify -> Publish happy path"""
        self.client.force_authenticate(user=self.reporter)
        url_base = f"/api/reporting/workitems/{self.item.id}/"
        
        # 1. Save Draft
        self.client.post(url_base + "save/", {
            "schema_version": "v2", 
            "values_json": {"note": "Draft"}
        }, format="json")
        
        instance = ReportInstanceV2.objects.get(work_item=self.item)
        self.assertEqual(instance.status, "draft")
        
        # 2. Submit
        resp = self.client.post(url_base + "submit/")
        self.assertEqual(resp.status_code, 200)
        instance.refresh_from_db()
        self.assertEqual(instance.status, "submitted")
        self.assertTrue(ReportActionLogV2.objects.filter(action="submit").exists())
        
        # 3. Verify (as verifier)
        self.client.force_authenticate(user=self.verifier)
        resp = self.client.post(url_base + "verify/", {"notes": "All good"})
        self.assertEqual(resp.status_code, 200)
        instance.refresh_from_db()
        self.assertEqual(instance.status, "verified")
        self.assertTrue(ReportActionLogV2.objects.filter(action="verify").exists())
        
        # 4. Publish
        resp = self.client.post(url_base + "publish/")
        self.assertEqual(resp.status_code, 200)
        instance.refresh_from_db()
        self.assertTrue(instance.is_published)
        self.assertTrue(ReportActionLogV2.objects.filter(action="publish").exists())

    def test_return_workflow(self):
        """Submit -> Return -> Edit -> Resubmit"""
        self.client.force_authenticate(user=self.reporter)
        url_base = f"/api/reporting/workitems/{self.item.id}/"
        
        # Save & Submit
        self.client.post(url_base + "save/", {"schema_version": "v2", "values_json": {}}, format="json")
        self.client.post(url_base + "submit/")
        
        # Return (as verifier)
        self.client.force_authenticate(user=self.verifier)
        resp = self.client.post(url_base + "return-for-correction/", {"reason": "Fix it"})
        self.assertEqual(resp.status_code, 200)
        
        instance = ReportInstanceV2.objects.get(work_item=self.item)
        self.assertEqual(instance.status, "draft")
        self.assertTrue(ReportActionLogV2.objects.filter(action="return").exists())
        
        self.item.refresh_from_db()
        self.assertEqual(self.item.status, "RETURNED_FOR_CORRECTION")
        
        # Edit (as reporter)
        self.client.force_authenticate(user=self.reporter)
        resp = self.client.post(url_base + "save/", {
            "schema_version": "v2", 
            "values_json": {"note": "Fixed value"}
        }, format="json")
        self.assertEqual(resp.status_code, 200)
        
        # Resubmit
        resp = self.client.post(url_base + "submit/")
        self.assertEqual(resp.status_code, 200)
        instance.refresh_from_db()
        self.assertEqual(instance.status, "submitted")

    def test_publish_without_verify(self):
        """Publish should fail if not verified"""
        self.client.force_authenticate(user=self.reporter)
        url_base = f"/api/reporting/workitems/{self.item.id}/"
        
        # Save & Submit
        self.client.post(url_base + "save/", {"schema_version": "v2", "values_json": {}}, format="json")
        self.client.post(url_base + "submit/")
        
        # Try Publish (as verifier)
        self.client.force_authenticate(user=self.verifier)
        resp = self.client.post(url_base + "publish/")
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(resp.data["error"], "Only verified reports can be published.")

    def test_edit_after_publish_conflict(self):
        """Editing after publish normally blocked or creates new version (check expectations)"""
        # Note: Implementation of 'edit after publish' in 'save' usually resets to draft if allowed,
        # or might be blocked. Requirement says: "New draft required for changes".
        # Let's see behavior. If I call save() on a verified report, logically it should reset to draft?
        # But 'edit after publish' (verified + published) -> 409 usually?
        # The prompt says: "edit after publish -> 409" for Phase 3A-3 Tests requirement. -> Actually "publish without verify -> 403", "edit after publish -> 409".
        
        # So I need to ensure edit after publish returns 409.
        # But wait, "New draft required for changes" implies we can edit?
        # Maybe "edit after publish -> 409" means modification of the *published instance* is 409.
        # But `save` creates/updates the draft.
        # If I am published, `ReportInstanceV2` is effectively the live version?
        # Actually, V2 usually keeps `ReportInstanceV2` as the current mutable head.
        # If "Editing blocked after publish" (3A-2 Enforce), then 409 is correct.
        # The user has to explicitly start a NEW draft? 
        # My `save` implementation logic: `instance.status = "draft"`.
        # This effectively RESETS it to draft.
        # But requirements "Tests (required)" says: "edit after publish -> 409".
        # So I should BLOCK editing if status is published?
        # Does `ReportInstanceV2` status switch to `published`?
        # No, status options are `draft`, `submitted`, `verified`. `returned`.
        # `is_published` checks for snapshots.
        # The workflow seems: Draft -> Submitted -> Verified -> (Publish just creates snapshot).
        # It doesn't say `ReportInstanceV2` status becomes `published`.
        # BUT, `item.status` becomes `PUBLISHED`.
        # If I save on a verified report that has been published...
        # If 409 is expected, I must implement that check in `save`.
        
        pass

    def test_edit_after_publish_should_fail(self):
        self.client.force_authenticate(user=self.verifier)
        url_base = f"/api/reporting/workitems/{self.item.id}/"
        
        # Setup verified state
        self.client.post(url_base + "save/", {"schema_version": "v2", "values_json": {}}, format="json")
        self.client.post(url_base + "submit/")
        self.client.post(url_base + "verify/")
        self.client.post(url_base + "publish/")
        
        # Now try to edit (as reporter)
        self.client.force_authenticate(user=self.reporter)
        resp = self.client.post(url_base + "save/", {
            "schema_version": "v2", 
            "values_json": {"note": "New"}
        }, format="json")
        
        # Requirement says 409.
        # My current implementation in `save` resets to "draft" (line 1129 in changes).
        # I need to update `save` to return 409 if published/verified?
        # Wait, if I cannot edit, how do I "New draft required for changes"?
        # Perhaps "New draft required" means I have to "unpublish" or "create new version"?
        # "New draft required for changes (new ReportInstanceV2 version or reset)"
        # If I just `save`, it's an edit.
        # If the requirement demands 409, then `save` must block it.
        # Let's adjust the test to expect 409, and then I will fix `save` to return 409 if is_published.
        
        self.assertEqual(resp.status_code, 409)

