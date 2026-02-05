import io
import zipfile
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from apps.reporting.models import ReportProfile, ServiceReportProfile, ReportParameter
from apps.catalog.models import Service

User = get_user_model()


class BaselinePackTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin_user = User.objects.create_superuser(
            username="admin", password="admin123", email="admin@example.com"
        )
        self.client.force_authenticate(user=self.admin_user)

    def test_list_packs(self):
        resp = self.client.get("/api/admin/baseline-packs/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        slugs = [p["slug"] for p in resp.data]
        self.assertIn("usg_abdomen_v1", slugs)
        self.assertIn("usg_kub_v1", slugs)
        self.assertIn("usg_pelvis_v1", slugs)

    def test_download_pack_zip(self):
        resp = self.client.get("/api/admin/baseline-packs/usg_abdomen_v1/download/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp["Content-Type"], "application/zip")
        with zipfile.ZipFile(io.BytesIO(resp.content), "r") as zf:
            names = zf.namelist()
            self.assertIn("usg_abdomen_v1/profiles.csv", names)
            self.assertIn("usg_abdomen_v1/parameters.csv", names)
            self.assertIn("usg_abdomen_v1/services.csv", names)
            self.assertIn("usg_abdomen_v1/linkage.csv", names)

    def test_seed_dry_run_preview(self):
        resp = self.client.post("/api/admin/baseline-packs/usg_abdomen_v1/seed/?dry_run=true")
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.data)
        steps = resp.data.get("steps", [])
        self.assertEqual(steps[0]["data"].get("created"), 1)  # profiles preview
        self.assertEqual(ReportProfile.objects.filter(code="USG_ABD").count(), 0)

    def test_seed_apply_and_verify(self):
        resp = self.client.post("/api/admin/baseline-packs/usg_kub_v1/seed/?dry_run=false")
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.data)
        self.assertTrue(ReportProfile.objects.filter(code="USG_KUB").exists())
        self.assertTrue(ReportParameter.objects.filter(profile__code="USG_KUB").exists())
        self.assertTrue(Service.objects.filter(code="USG_KUB").exists())
        self.assertTrue(ServiceReportProfile.objects.filter(service__code="USG_KUB", profile__code="USG_KUB").exists())
        verification = resp.data.get("verification", {})
        self.assertEqual(verification.get("status"), "pass")

        # Verify endpoint works separately
        verify_resp = self.client.post("/api/admin/baseline-packs/usg_kub_v1/verify/")
        self.assertEqual(verify_resp.status_code, status.HTTP_200_OK, verify_resp.data)
        self.assertEqual(verify_resp.data.get("status"), "pass")

