# USG Reporting - Quick Start Guide

## Prerequisites
- RIMS backend running
- PostgreSQL database
- Python 3.9+ environment

## Step 1: Install Dependencies

```bash
cd /home/munaim/srv/apps/radreport/backend
pip install -r requirements.txt
```

This installs the new Google Drive dependencies:
- google-auth
- google-auth-oauthlib
- google-auth-httplib2
- google-api-python-client

## Step 2: Run Migrations

```bash
python3 manage.py makemigrations usg
python3 manage.py migrate usg
```

Expected output:
```
Migrations for 'usg':
  apps/usg/migrations/0001_initial.py
    - Create model UsgTemplate
    - Create model UsgServiceProfile
    - Create model UsgStudy
    - Create model UsgFieldValue
    - Create model UsgPublishedSnapshot
```

## Step 3: Load Templates

```bash
python3 manage.py load_usg_templates
```

Expected output:
```
Loading template from usg_abdomen_base.v1.json...
✓ Created template: USG_ABDOMEN_BASE v1

Template loading complete!
```

## Step 4: Verify Installation

### Check Admin Panel
1. Start server: `python3 manage.py runserver`
2. Visit: http://localhost:8000/admin/
3. Look for "USG" section with models:
   - Usg templates
   - Usg service profiles
   - Usg studies
   - Usg field values
   - Usg published snapshots

### Check API
Visit: http://localhost:8000/api/docs/

Look for new endpoints under "usg" tag:
- `/api/usg/templates/`
- `/api/usg/studies/`
- `/api/usg/snapshots/`

## Step 5: Configure Google Drive (Optional)

### Create Service Account
1. Go to Google Cloud Console
2. Create project or use existing
3. Enable Google Drive API
4. Create Service Account
5. Download JSON key file

### Set Environment Variables

**Option A: JSON String**
```bash
export GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON='<paste_json_here>'
export GOOGLE_DRIVE_USG_FOLDER_ID='<your_drive_folder_id>'
```

**Option B: File Path**
```bash
export GOOGLE_DRIVE_SERVICE_ACCOUNT_PATH=/path/to/service-account.json
export GOOGLE_DRIVE_USG_FOLDER_ID='<your_drive_folder_id>'
```

### Test Drive Connection
```python
from apps.usg.google_drive import get_drive_service
service = get_drive_service()
print("Drive service available:", service is not None)
```

## Step 6: Test the Workflow

### 1. Create a Test Patient and Visit
```bash
# Via Django shell
python3 manage.py shell

from apps.patients.models import Patient
from apps.studies.models import Visit
from django.contrib.auth import get_user_model

User = get_user_model()
user = User.objects.first()

patient = Patient.objects.create(
    name="Test Patient",
    age=45,
    gender="Male"
)

visit = Visit.objects.create(
    patient=patient,
    created_by=user
)

print(f"Patient MR: {patient.mrn}")
print(f"Visit Number: {visit.visit_number}")
```

### 2. Create a Draft Study via API

```bash
curl -X POST http://localhost:8000/api/usg/studies/ \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "patient": "<patient_id>",
    "visit": "<visit_id>",
    "service_code": "USG_ABDOMEN",
    "template": "<template_id>"
  }'
```

### 3. Fill Field Values

```bash
curl -X PUT http://localhost:8000/api/usg/studies/<study_id>/values/ \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "values": [
      {
        "field_key": "liver_size",
        "value_json": "normal",
        "is_not_applicable": false
      },
      {
        "field_key": "liver_span_cm",
        "value_json": 14.5,
        "is_not_applicable": false
      },
      {
        "field_key": "gb_calculi",
        "value_json": null,
        "is_not_applicable": true
      }
    ]
  }'
```

### 4. Preview Narrative

```bash
curl -X POST http://localhost:8000/api/usg/studies/<study_id>/render/ \
  -H "Authorization: Bearer <your_token>"
```

### 5. Publish Report

```bash
curl -X POST http://localhost:8000/api/usg/studies/<study_id>/publish/ \
  -H "Authorization: Bearer <your_token>"
```

### 6. Get PDF

```bash
curl http://localhost:8000/api/usg/studies/<study_id>/pdf/ \
  -H "Authorization: Bearer <your_token>" \
  > report.pdf

# Open the PDF
open report.pdf  # macOS
xdg-open report.pdf  # Linux
```

### 7. List Reports for Visit

```bash
curl http://localhost:8000/api/visits/<visit_id>/usg-reports/ \
  -H "Authorization: Bearer <your_token>"
```

## Step 7: Run Tests

```bash
python3 manage.py test apps.usg
```

Expected output:
```
Creating test database...
..........
----------------------------------------------------------------------
Ran 10 tests in 0.XXXs

OK
```

## Troubleshooting

### Migration Issues
If migrations fail:
```bash
python3 manage.py migrate --fake-initial usg
```

### Google Drive Connection Issues
Check environment variables:
```bash
echo $GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON
echo $GOOGLE_DRIVE_USG_FOLDER_ID
```

Test connection:
```python
from apps.usg.google_drive import get_drive_service
service = get_drive_service()
if service:
    print("✓ Drive service connected")
else:
    print("✗ Drive service unavailable (will work without Drive)")
```

### Template Not Loading
Check template file exists:
```bash
ls -la apps/usg/templates/*.json
```

Manual load:
```bash
python3 manage.py load_usg_templates
```

### PDF Generation Issues
Check ReportLab installed:
```python
import reportlab
print(reportlab.Version)
```

### Authentication Issues
Get a token first:
```bash
curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your_password"}'
```

## Verification Checklist

- [ ] Migrations applied successfully
- [ ] Template loaded (visible in admin)
- [ ] Can create draft study via API
- [ ] Can fill field values
- [ ] Can preview narrative
- [ ] Can publish report
- [ ] Published report is locked (edit fails)
- [ ] Can retrieve PDF
- [ ] Can list reports from visit
- [ ] Google Drive integration working (optional)
- [ ] Tests pass

## Next Steps

1. **Create more templates** for other USG types (KUB, Pelvis, etc.)
2. **Add role-based permissions** (Reporter/Verifier/Publisher)
3. **Build frontend UI** for report filling
4. **Set up production Google Drive** with proper folder structure
5. **Configure backup strategy** for published snapshots

## Support

- Documentation: `docs/usg_reporting.md`
- Implementation details: `USG_IMPLEMENTATION_COMPLETE.md`
- Code: `backend/apps/usg/`

---

**Status**: ✅ Ready for testing and development
