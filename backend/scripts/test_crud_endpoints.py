import os
import sys
import django
import uuid
import random

# Setup Django environment
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rims_backend.settings")
os.environ["DJANGO_ALLOWED_HOSTS"] = "testserver,localhost,127.0.0.1"
django.setup()

from rest_framework.test import APIClient
from apps.reporting.models import ReportProfile, ReportParameter
from django.contrib.auth import get_user_model

User = get_user_model()

def test_crud():
    client = APIClient()
    user, _ = User.objects.get_or_create(username="testadmin", defaults={"is_superuser": True})
    client.force_authenticate(user=user)

    suffix = str(uuid.uuid4())[:8]

    print("Testing ReportProfile CRUD...")
    # Create
    data = {
        "code": f"TEST_PROFILE_{suffix}",
        "name": f"Test Profile {suffix}",
        "modality": "USG"
    }
    response = client.post('/api/reporting/profiles/', data, format='json')
    if response.status_code == 201:
        print("PASS: Create Profile")
        profile_id = response.data['id']
    else:
        print(f"FAIL: Create Profile {response.status_code} {response.data}")
        return

    print("Testing ReportParameter CRUD with options...")
    # Create Parameter with options
    data = {
        "profile": profile_id,
        "section": "General",
        "name": "Test Dropdown",
        "parameter_type": "dropdown",
        "order": 1,
        "options": [
            {"label": "Opt 1", "value": "1", "order": 0},
            {"label": "Opt 2", "value": "2", "order": 1}
        ]
    }
    response = client.post('/api/reporting/parameters/', data, format='json')
    if response.status_code == 201:
        print("PASS: Create Parameter")
        param_id = response.data['id']
        # Verify options
        param = ReportParameter.objects.get(id=param_id)
        if param.options.count() == 2:
            print("PASS: Options created")
        else:
            print(f"FAIL: Options count {param.options.count()}")

        # Update Parameter
        update_data = {
             "profile": profile_id,
             "section": "General",
             "name": "Updated Name",
             "parameter_type": "dropdown",
             "order": 1,
             "options": [
                 {"label": "Opt 3", "value": "3", "order": 0}
             ]
        }
        response = client.patch(f'/api/reporting/parameters/{param_id}/', update_data, format='json')
        if response.status_code == 200:
             print("PASS: Update Parameter")
             param.refresh_from_db()
             if param.options.count() == 1 and param.options.first().label == "Opt 3":
                 print("PASS: Options updated")
             else:
                 print(f"FAIL: Options update failed. Count {param.options.count()}")
        else:
             print(f"FAIL: Update Parameter {response.data}")

    else:
        print(f"FAIL: Create Parameter {response.data}")

if __name__ == "__main__":
    try:
        test_crud()
    except Exception as e:
        print(f"Error: {e}")
