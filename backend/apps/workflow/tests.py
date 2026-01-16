from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.catalog.models import Modality, Service
from apps.patients.models import Patient
from apps.templates.api import build_schema
from apps.templates.models import Template, TemplateField, TemplateSection, TemplateVersion
from apps.workflow.api import ServiceVisitViewSet, USGReportViewSet
from apps.workflow.models import ServiceVisit, USGReport


class Phase3RBACWorkflowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        for group_name in ["registration", "performance", "verification"]:
            Group.objects.get_or_create(name=group_name)

        user_model = get_user_model()
        cls.reg_user = user_model.objects.create_user(username="reg_user_test", password="reg_user_test")
        cls.perf_user = user_model.objects.create_user(username="perf_user_test", password="perf_user_test")
        cls.ver_user = user_model.objects.create_user(username="ver_user_test", password="ver_user_test")
        cls.reg_user.groups.add(Group.objects.get(name="registration"))
        cls.perf_user.groups.add(Group.objects.get(name="performance"))
        cls.ver_user.groups.add(Group.objects.get(name="verification"))

        modality, _ = Modality.objects.get_or_create(code="USG", defaults={"name": "Ultrasound"})
        template, _ = Template.objects.get_or_create(
            name="Phase3 RBAC Template",
            modality_code="USG",
            defaults={"is_active": True},
        )
        section, _ = TemplateSection.objects.get_or_create(template=template, title="Findings", defaults={"order": 1})
        TemplateField.objects.get_or_create(
            section=section,
            key="summary",
            defaults={
                "label": "Summary",
                "field_type": "short_text",
                "required": True,
                "order": 1,
            },
        )
        if not template.versions.filter(is_published=True).exists():
            TemplateVersion.objects.create(
                template=template,
                version=1,
                schema=build_schema(template),
                is_published=True,
            )

        cls.service, _ = Service.objects.get_or_create(
            code="USG-RBAC",
            defaults={
                "modality": modality,
                "name": "USG RBAC",
                "category": "Radiology",
                "price": Decimal("500.00"),
                "charges": Decimal("500.00"),
                "default_price": Decimal("500.00"),
                "is_active": True,
                "default_template": template,
            },
        )
        if cls.service.default_template_id != template.id:
            cls.service.default_template = template
            cls.service.save(update_fields=["default_template"])

        cls.patient = Patient.objects.create(
            name="RBAC Patient",
            gender="Other",
            phone="0000000000",
            address="RBAC Address",
        )

    def _create_visit(self, user):
        factory = APIRequestFactory()
        payload = {
            "patient_id": str(self.patient.id),
            "service_ids": [str(self.service.id)],
            "subtotal": str(self.service.price),
            "discount": "0",
            "total_amount": str(self.service.price),
            "net_amount": str(self.service.price),
            "amount_paid": str(self.service.price),
            "payment_method": "cash",
        }
        request = factory.post("/api/workflow/visits/create_visit/", payload, format="json")
        force_authenticate(request, user=user)
        response = ServiceVisitViewSet.as_view({"post": "create_visit"})(request)
        self.assertEqual(response.status_code, 201, response.data)
        return ServiceVisit.objects.get(id=response.data["id"])

    def _create_report(self, user, item_id):
        factory = APIRequestFactory()
        payload = {
            "service_visit_item_id": str(item_id),
            "values": {"summary": "Normal ultrasound."},
        }
        request = factory.post("/api/workflow/usg/", payload, format="json")
        force_authenticate(request, user=user)
        response = USGReportViewSet.as_view({"post": "create"})(request)
        self.assertIn(response.status_code, [200, 201], response.data)
        return USGReport.objects.get(id=response.data["id"])

    def test_registration_cannot_submit_or_finalize(self):
        visit = self._create_visit(self.reg_user)
        item = visit.items.first()
        report = self._create_report(self.perf_user, item.id)

        factory = APIRequestFactory()
        submit_request = factory.post(
            f"/api/workflow/usg/{report.id}/submit_for_verification/",
            {"values": {"summary": "Normal ultrasound."}},
            format="json",
        )
        force_authenticate(submit_request, user=self.reg_user)
        submit_response = USGReportViewSet.as_view({"post": "submit_for_verification"})(submit_request, pk=str(report.id))
        self.assertEqual(submit_response.status_code, 403)

        finalize_request = factory.post(f"/api/workflow/usg/{report.id}/finalize/", {}, format="json")
        force_authenticate(finalize_request, user=self.reg_user)
        finalize_response = USGReportViewSet.as_view({"post": "finalize"})(finalize_request, pk=str(report.id))
        self.assertEqual(finalize_response.status_code, 403)

    def test_performance_can_submit_but_cannot_finalize(self):
        visit = self._create_visit(self.reg_user)
        item = visit.items.first()
        report = self._create_report(self.perf_user, item.id)

        factory = APIRequestFactory()
        submit_request = factory.post(
            f"/api/workflow/usg/{report.id}/submit_for_verification/",
            {"values": {"summary": "Normal ultrasound."}},
            format="json",
        )
        force_authenticate(submit_request, user=self.perf_user)
        submit_response = USGReportViewSet.as_view({"post": "submit_for_verification"})(submit_request, pk=str(report.id))
        self.assertEqual(submit_response.status_code, 200, submit_response.data)

        finalize_request = factory.post(f"/api/workflow/usg/{report.id}/finalize/", {}, format="json")
        force_authenticate(finalize_request, user=self.perf_user)
        finalize_response = USGReportViewSet.as_view({"post": "finalize"})(finalize_request, pk=str(report.id))
        self.assertEqual(finalize_response.status_code, 403)

    def test_verification_can_finalize_but_cannot_edit(self):
        visit = self._create_visit(self.reg_user)
        item = visit.items.first()
        report = self._create_report(self.perf_user, item.id)

        factory = APIRequestFactory()
        submit_request = factory.post(
            f"/api/workflow/usg/{report.id}/submit_for_verification/",
            {"values": {"summary": "Normal ultrasound."}},
            format="json",
        )
        force_authenticate(submit_request, user=self.perf_user)
        submit_response = USGReportViewSet.as_view({"post": "submit_for_verification"})(submit_request, pk=str(report.id))
        self.assertEqual(submit_response.status_code, 200, submit_response.data)

        save_request = factory.post(
            f"/api/workflow/usg/{report.id}/save_draft/",
            {"values": {"summary": "Edited by verifier."}},
            format="json",
        )
        force_authenticate(save_request, user=self.ver_user)
        save_response = USGReportViewSet.as_view({"post": "save_draft"})(save_request, pk=str(report.id))
        self.assertEqual(save_response.status_code, 403)

        finalize_request = factory.post(f"/api/workflow/usg/{report.id}/finalize/", {}, format="json")
        force_authenticate(finalize_request, user=self.ver_user)
        finalize_response = USGReportViewSet.as_view({"post": "finalize"})(finalize_request, pk=str(report.id))
        self.assertEqual(finalize_response.status_code, 200, finalize_response.data)

    def test_registration_cannot_create_report(self):
        """Registration users cannot create USG reports"""
        visit = self._create_visit(self.reg_user)
        item = visit.items.first()

        factory = APIRequestFactory()
        create_request = factory.post(
            "/api/workflow/usg/",
            {"service_visit_item_id": str(item.id), "values": {"summary": "Attempt by registration."}},
            format="json",
        )
        force_authenticate(create_request, user=self.reg_user)
        create_response = USGReportViewSet.as_view({"post": "create"})(create_request)
        self.assertEqual(create_response.status_code, 403)

    def test_verification_cannot_create_or_update_report(self):
        """Verification users cannot create or update USG reports"""
        visit = self._create_visit(self.reg_user)
        item = visit.items.first()

        factory = APIRequestFactory()
        # Test create
        create_request = factory.post(
            "/api/workflow/usg/",
            {"service_visit_item_id": str(item.id), "values": {"summary": "Attempt by verification."}},
            format="json",
        )
        force_authenticate(create_request, user=self.ver_user)
        create_response = USGReportViewSet.as_view({"post": "create"})(create_request)
        self.assertEqual(create_response.status_code, 403)

        # Create a report with performance user first
        report = self._create_report(self.perf_user, item.id)

        # Test update
        update_request = factory.put(
            f"/api/workflow/usg/{report.id}/",
            {"report_json": {"summary": "Update attempt by verification."}},
            format="json",
        )
        force_authenticate(update_request, user=self.ver_user)
        update_response = USGReportViewSet.as_view({"put": "update"})(update_request, pk=str(report.id))
        self.assertEqual(update_response.status_code, 403)

        # Test partial_update
        patch_request = factory.patch(
            f"/api/workflow/usg/{report.id}/",
            {"report_json": {"summary": "Patch attempt by verification."}},
            format="json",
        )
        force_authenticate(patch_request, user=self.ver_user)
        patch_response = USGReportViewSet.as_view({"patch": "partial_update"})(patch_request, pk=str(report.id))
        self.assertEqual(patch_response.status_code, 403)


class AuthMeEndpointTests(TestCase):
    """Tests for the /api/auth/me/ endpoint that returns user identity and groups"""

    @classmethod
    def setUpTestData(cls):
        user_model = get_user_model()
        
        # Create groups
        cls.reg_group = Group.objects.create(name="registration")
        cls.perf_group = Group.objects.create(name="performance")
        cls.ver_group = Group.objects.create(name="verification")
        
        # Create users with different group memberships
        cls.user_with_one_group = user_model.objects.create_user(
            username="user_one_group", password="test"
        )
        cls.user_with_one_group.groups.add(cls.reg_group)
        
        cls.user_with_multiple_groups = user_model.objects.create_user(
            username="user_multi_groups", password="test"
        )
        cls.user_with_multiple_groups.groups.add(cls.perf_group, cls.ver_group)
        
        cls.user_no_groups = user_model.objects.create_user(
            username="user_no_groups", password="test"
        )
        
        cls.superuser = user_model.objects.create_superuser(
            username="admin", password="test"
        )

    def test_auth_me_returns_user_info_with_one_group(self):
        """Test that auth_me returns correct user info for user with one group"""
        from rims_backend.urls import auth_me
        import json
        
        factory = APIRequestFactory()
        request = factory.get("/api/auth/me/")
        force_authenticate(request, user=self.user_with_one_group)
        
        response = auth_me(request)
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertEqual(data["username"], "user_one_group")
        self.assertEqual(data["is_superuser"], False)
        self.assertEqual(data["groups"], ["registration"])

    def test_auth_me_returns_user_info_with_multiple_groups(self):
        """Test that auth_me returns correct user info for user with multiple groups"""
        from rims_backend.urls import auth_me
        import json
        
        factory = APIRequestFactory()
        request = factory.get("/api/auth/me/")
        force_authenticate(request, user=self.user_with_multiple_groups)
        
        response = auth_me(request)
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertEqual(data["username"], "user_multi_groups")
        self.assertEqual(data["is_superuser"], False)
        self.assertCountEqual(data["groups"], ["performance", "verification"])

    def test_auth_me_returns_user_info_with_no_groups(self):
        """Test that auth_me returns correct user info for user with no groups"""
        from rims_backend.urls import auth_me
        import json
        
        factory = APIRequestFactory()
        request = factory.get("/api/auth/me/")
        force_authenticate(request, user=self.user_no_groups)
        
        response = auth_me(request)
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertEqual(data["username"], "user_no_groups")
        self.assertEqual(data["is_superuser"], False)
        self.assertEqual(data["groups"], [])

    def test_auth_me_returns_superuser_status(self):
        """Test that auth_me correctly identifies superusers"""
        from rims_backend.urls import auth_me
        import json
        
        factory = APIRequestFactory()
        request = factory.get("/api/auth/me/")
        force_authenticate(request, user=self.superuser)
        
        response = auth_me(request)
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertEqual(data["username"], "admin")
        self.assertEqual(data["is_superuser"], True)
        self.assertEqual(data["groups"], [])

    def test_auth_me_requires_authentication(self):
        """Test that auth_me requires authentication"""
        from rims_backend.urls import auth_me
        
        factory = APIRequestFactory()
        request = factory.get("/api/auth/me/")
        # No authentication
        
        response = auth_me(request)
        self.assertEqual(response.status_code, 401)


class DashboardAPITests(TestCase):
    """Tests for dashboard API endpoints"""
    
    @classmethod
    def setUpTestData(cls):
        user_model = get_user_model()
        
        # Create groups
        cls.admin_group = Group.objects.create(name="admin")
        cls.reg_group = Group.objects.create(name="registration")
        
        # Create admin user
        cls.admin_user = user_model.objects.create_superuser(
            username="admin", password="test", email="admin@test.com"
        )
        
        # Create regular user
        cls.regular_user = user_model.objects.create_user(
            username="regular", password="test"
        )
        cls.regular_user.groups.add(cls.reg_group)
        
        # Create patient
        cls.patient = Patient.objects.create(
            name="Test Patient",
            gender="M",
            phone="1234567890"
        )
        
        # Create modality and service
        modality = Modality.objects.get_or_create(code="USG", defaults={"name": "Ultrasound"})[0]
        cls.service = Service.objects.get_or_create(
            modality=modality,
            name="Test USG Service",
            defaults={
                "price": Decimal("500.00"),
                "is_active": True
            }
        )[0]
        
        # Create a service visit with items
        from apps.workflow.models import ServiceVisit, ServiceVisitItem
        cls.visit = ServiceVisit.objects.create(
            patient=cls.patient,
            created_by=cls.admin_user
        )
        cls.item = ServiceVisitItem.objects.create(
            service_visit=cls.visit,
            service=cls.service,
            service_name_snapshot="Test USG Service",
            department_snapshot="USG",
            price_snapshot=Decimal("500.00"),
            status="IN_PROGRESS"
        )
    
    def test_dashboard_summary_requires_auth(self):
        """Test that dashboard summary requires authentication"""
        from apps.workflow.dashboard_api import dashboard_summary
        
        factory = APIRequestFactory()
        request = factory.get("/api/dashboard/summary/")
        # No authentication
        
        response = dashboard_summary(request)
        self.assertEqual(response.status_code, 401)
    
    def test_dashboard_summary_returns_kpis(self):
        """Test that dashboard summary returns KPI counts"""
        from apps.workflow.dashboard_api import dashboard_summary
        
        factory = APIRequestFactory()
        request = factory.get("/api/dashboard/summary/")
        force_authenticate(request, user=self.admin_user)
        
        response = dashboard_summary(request)
        self.assertEqual(response.status_code, 200)
        
        data = response.data
        self.assertIn("total_patients_today", data)
        self.assertIn("total_services_today", data)
        self.assertIn("reports_pending", data)
        self.assertIn("reports_verified", data)
        self.assertIn("critical_delays", data)
        self.assertIn("server_time", data)
    
    def test_dashboard_worklist_admin_sees_department(self):
        """Test that admin users see department worklists"""
        from apps.workflow.dashboard_api import dashboard_worklist
        
        factory = APIRequestFactory()
        request = factory.get("/api/dashboard/worklist/?scope=department")
        force_authenticate(request, user=self.admin_user)
        
        response = dashboard_worklist(request)
        self.assertEqual(response.status_code, 200)
        
        data = response.data
        self.assertEqual(data["scope"], "department")
        # Admin can see grouped_by_department or items
        self.assertTrue("grouped_by_department" in data or "items" in data)
    
    def test_dashboard_worklist_non_admin_sees_my_only(self):
        """Test that non-admin users only see their own worklist"""
        from apps.workflow.dashboard_api import dashboard_worklist
        
        factory = APIRequestFactory()
        request = factory.get("/api/dashboard/worklist/?scope=my")
        force_authenticate(request, user=self.regular_user)
        
        response = dashboard_worklist(request)
        self.assertEqual(response.status_code, 200)
        
        data = response.data
        self.assertEqual(data["scope"], "my")
        self.assertIn("items", data)
    
    def test_dashboard_worklist_non_admin_cannot_access_department(self):
        """Test that non-admin users cannot access department scope"""
        from apps.workflow.dashboard_api import dashboard_worklist
        
        factory = APIRequestFactory()
        request = factory.get("/api/dashboard/worklist/?scope=department")
        force_authenticate(request, user=self.regular_user)
        
        response = dashboard_worklist(request)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid scope", str(response.data))
    
    def test_dashboard_flow_returns_counts(self):
        """Test that dashboard flow returns step counts"""
        from apps.workflow.dashboard_api import dashboard_flow
        
        factory = APIRequestFactory()
        request = factory.get("/api/dashboard/flow/")
        force_authenticate(request, user=self.admin_user)
        
        response = dashboard_flow(request)
        self.assertEqual(response.status_code, 200)
        
        data = response.data
        self.assertIn("registered_count", data)
        self.assertIn("paid_count", data)
        self.assertIn("performed_count", data)
        self.assertIn("reported_count", data)
        self.assertIn("verified_count", data)
        self.assertIn("server_time", data)
    
    def test_health_endpoint_returns_status(self):
        """Test that health endpoint returns status and checks"""
        from rims_backend.urls import health
        import json
        
        factory = APIRequestFactory()
        request = factory.get("/api/health/")
        # Health endpoint is public (AllowAny)
        
        response = health(request)
        self.assertIn(response.status_code, [200, 503])  # 503 if DB fails
        
        data = json.loads(response.content)
        self.assertIn("status", data)
        self.assertIn("server_time", data)
        self.assertIn("checks", data)
        self.assertIn("db", data["checks"])
        self.assertIn("latency_ms", data)
