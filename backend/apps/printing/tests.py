"""
RBAC sanity tests for printing config endpoints.
Tests that admin can access/modify printing config,
while non-admin users cannot.
"""
import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()


@pytest.fixture
def admin_user(db):
    """Create an admin user for testing."""
    return User.objects.create_user(
        username="admin_test",
        password="testpass123",
        is_staff=True,
        is_superuser=True,
    )


@pytest.fixture
def regular_user(db):
    """Create a regular (non-admin) user for testing."""
    return User.objects.create_user(
        username="regular_test",
        password="testpass123",
        is_staff=False,
        is_superuser=False,
    )


@pytest.fixture
def staff_user_with_role(db):
    """User with registration_desk role (can access worklist)."""
    group, _ = Group.objects.get_or_create(name="registration_desk")
    user = User.objects.create_user(
        username="desk_test",
        password="testpass123",
        is_staff=False,
        is_superuser=False,
    )
    user.groups.add(group)
    return user


@pytest.fixture
def api_client():
    """Create an API client for testing."""
    return APIClient()


@pytest.mark.django_db
class TestPrintingConfigRBAC:
    """Test RBAC for printing config endpoints."""

    def test_admin_can_get_printing_config(self, api_client, admin_user):
        """Admin can GET /api/printing/config/"""
        api_client.force_authenticate(user=admin_user)
        response = api_client.get("/api/printing/config/")
        assert response.status_code == status.HTTP_200_OK
        assert "org_name" in response.data
        assert "receipt_header_text" in response.data

    def test_admin_can_patch_printing_config(self, api_client, admin_user):
        """Admin can PATCH /api/printing/config/"""
        api_client.force_authenticate(user=admin_user)
        payload = {
            "org_name": "Test Organization",
            "receipt_header_text": "Test Header",
        }
        response = api_client.patch(
            "/api/printing/config/", data=payload, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["org_name"] == "Test Organization"
        assert response.data["receipt_header_text"] == "Test Header"

    def test_non_admin_cannot_patch_printing_config(
        self, api_client, regular_user
    ):
        """Non-admin cannot PATCH /api/printing/config/ (403)"""
        api_client.force_authenticate(user=regular_user)
        payload = {
            "org_name": "Unauthorized Change",
        }
        response = api_client.patch(
            "/api/printing/config/", data=payload, format="json"
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Admin required" in str(response.data.get("detail", ""))

    def test_non_admin_can_get_printing_config(
        self, api_client, regular_user
    ):
        """Non-admin can GET /api/printing/config/ (read-only)"""
        api_client.force_authenticate(user=regular_user)
        response = api_client.get("/api/printing/config/")
        assert response.status_code == status.HTTP_200_OK
        assert "org_name" in response.data

    def test_regular_user_can_access_worklist_endpoints(
        self, api_client, staff_user_with_role
    ):
        """User with role can access worklist endpoints relevant to their role."""
        api_client.force_authenticate(user=staff_user_with_role)
        response = api_client.get("/api/workflow/visits/")
        assert response.status_code != status.HTTP_403_FORBIDDEN
