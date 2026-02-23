import pytest
from datetime import timedelta
from django.utils import timezone
from django.urls import reverse
from rest_framework.test import APIClient
from apps.workflow.models import ServiceVisit, ServiceVisitItem
from apps.patients.models import Patient
from apps.catalog.models import Modality, Service
from django.contrib.auth.models import User

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def admin_user():
    user = User.objects.create_superuser('admin', 'admin@example.com', 'pass')
    return user

@pytest.fixture
def normal_user():
    return User.objects.create_user('doc', 'doc@example.com', 'pass')

@pytest.fixture
def basic_service():
    modality = Modality.objects.create(code="US", name="Ultrasound")
    return Service.objects.create(name="Standard US", modality=modality, code="US1")

@pytest.mark.django_db
def test_dashboard_truth_timezone_and_metrics(api_client, admin_user, basic_service):
    """Test timezone correctness and status bucket counts."""
    api_client.force_authenticate(user=admin_user)
    
    now = timezone.now()
    local_now = timezone.localtime(now)
    today_start = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday = today_start - timedelta(minutes=5)
    
    patient = Patient.objects.create(name="Test Time", mrn="MRN-TIME", date_of_birth="1990-01-01", gender="M")
    
    visit1 = ServiceVisit.objects.create(patient=patient)
    ServiceVisit.objects.filter(id=visit1.id).update(registered_at=yesterday)
    
    visit2 = ServiceVisit.objects.create(patient=patient)
    
    item1 = ServiceVisitItem.objects.create(service=basic_service, service_visit=visit1, service_name_snapshot="X", status="PUBLISHED")
    ServiceVisitItem.objects.filter(id=item1.id).update(published_at=yesterday, created_at=yesterday)

    item2 = ServiceVisitItem.objects.create(service=basic_service, service_visit=visit2, service_name_snapshot="Y", status="PENDING_VERIFICATION")
    # item2 is pending, created today.

    response = api_client.get(reverse('dashboard-summary'))
    assert response.status_code == 200
    data = response.json()
    metrics = {m['key']: m['value'] for m in data['metrics']}
    
    assert metrics['total_patients_today'] == 1 
    assert metrics['total_services_today'] == 1 
    assert metrics['reports_pending'] == 1 
    assert metrics['reports_verified'] == 0 
    
@pytest.mark.django_db
def test_dashboard_rbac_isolation(api_client, admin_user, normal_user, basic_service):
    """Test standard tenant/RBAC isolation on worklist"""
    patient = Patient.objects.create(name="Doc P", mrn="M2", date_of_birth="1990-01-01", gender="M")
    
    v1 = ServiceVisit.objects.create(patient=patient, assigned_to=admin_user)
    item_admin = ServiceVisitItem.objects.create(service=basic_service, service_visit=v1, status="IN_PROGRESS")
    
    v2 = ServiceVisit.objects.create(patient=patient, assigned_to=normal_user)
    item_doc = ServiceVisitItem.objects.create(service=basic_service, service_visit=v2, status="IN_PROGRESS")

    api_client.force_authenticate(user=admin_user)
    resp_admin = api_client.get(reverse('dashboard-summary'))
    worklist_admin = resp_admin.json()['sections']['pending_worklist']['items']
    assert len(worklist_admin) == 2

    api_client.force_authenticate(user=normal_user)
    resp_doc = api_client.get(reverse('dashboard-summary'))
    worklist_doc = resp_doc.json()['sections']['pending_worklist']['items']
    assert len(worklist_doc) == 1
    assert worklist_doc[0]['id'] == str(item_doc.id)
