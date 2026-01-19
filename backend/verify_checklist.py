import json
import uuid
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from rest_framework.test import APIRequestFactory, force_authenticate
from apps.templates.engine import TemplatePackageEngine
from apps.templates.models import ReportTemplate, ServiceReportTemplate
from apps.templates.api import ReportTemplateViewSet
from apps.catalog.models import Service

# Setup
User = get_user_model()
try:
    user = User.objects.get(username="admin")
except User.DoesNotExist:
    user = User.objects.create_superuser("admin", "admin@example.com", "password")

factory = APIRequestFactory()

# Test Data
TEMPLATE_CODE = "CHECKLIST_VERIFY"
SERVICE_CODE = "USG_CHECK"

# Ensure modality exists
modality, _ = Modality.objects.get_or_create(code="USG", defaults={"name": "Ultrasound"})

# Ensure service exists for mapping test
service, _ = Service.objects.get_or_create(
    code=SERVICE_CODE, 
    defaults={"name": "Checklist Service", "modality": modality, "price": 0} 
)

package_data = {
    "code": TEMPLATE_CODE,
    "name": "Checklist Verification Template",
    "category": "Verification",
    "service_mappings": [SERVICE_CODE],
    "sections": [
        {
            "title": "Section 1",
            "fields": [
                {
                    "key": "f1",
                    "label": "Field 1",
                    "type": "short_text",
                    "required": True
                }
            ]
        }
    ]
}

print("--- STARTING VERIFICATION CHECKLIST ---")

# Step 1: Simulate Import (A)
print(f"\n[A] Simulating Import of '{TEMPLATE_CODE}'...")
try:
    # Cleanup previous if exists
    ReportTemplate.objects.filter(code=TEMPLATE_CODE).delete()
    
    t, v = TemplatePackageEngine.import_package(package_data, mode="create", user=user)
    print("  ✅ Import function executed successfully.")
except Exception as e:
    print(f"  ❌ Import failed: {e}")
    exit(1)

# Step 2: DB Verification (A)
print("\n[A] Checking DB existence...")
rt = ReportTemplate.objects.get(code=TEMPLATE_CODE)
print(f"  ✅ Code: {rt.code}")
print(f"  ✅ Name: {rt.name}")
print(f"  ✅ Category: {rt.category}")
print(f"  ✅ Is Active: {rt.is_active}")
print(f"  ✅ Created By: {rt.created_by.username if rt.created_by else 'None'}")

# Fields check
fields = list(rt.fields.order_by('order'))
print(f"  ✅ Fields count: {len(fields)} (Expected 2: 1 heading + 1 field)")
if len(fields) >= 2:
    print(f"     - Field 0: {fields[0].field_type} '{fields[0].label}'")
    print(f"     - Field 1: {fields[1].field_type} '{fields[1].label}'")

# Step 3: Service Mapping (E/F)
print("\n[E/F] Checking Service mapping...")
link = ServiceReportTemplate.objects.filter(template=rt, service__code=SERVICE_CODE).first()
if link:
    print(f"  ✅ Linked to service: {link.service.name}")
else:
    print(f"  ❌ NOT linked to service {SERVICE_CODE}")

# Step 4: API Verification (B/C)
print("\n[B] Verifying API List Response...")
view = ReportTemplateViewSet.as_view({'get': 'list'})
request = factory.get('/api/report-templates/')
force_authenticate(request, user=user)
response = view(request)

if response.status_code == 200:
    results = response.data['results'] if 'results' in response.data else response.data
    found = next((item for item in results if item['code'] == TEMPLATE_CODE), None)
    if found:
        print("  ✅ Template found in API response")
        print(f"  ✅ API 'is_active': {found['is_active']}")
        print(f"  ✅ API 'category': {found['category']}")
    else:
        print("  ❌ Template NOT found in API response")
        print("     (List returned ids: " + ", ".join([str(i.get('id')) for i in results]) + ")")
else:
    print(f"  ❌ API call failed: {response.status_code}")

print("\n--- VERIFICATION COMPLETE ---")
