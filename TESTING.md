# Testing Guide

This document describes how to test the RIMS application end-to-end.

## Prerequisites

1. **Backend Setup:**
   ```bash
   cd backend
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Database Setup:**
   ```bash
   # Start database
   docker compose up -d db redis
   
   # Create migrations and apply
   python manage.py makemigrations
   python manage.py migrate
   
   # Create superuser
   python manage.py createsuperuser
   ```

3. **Frontend Setup:**
   ```bash
   cd frontend
   npm install
   ```

## Running the Application

1. **Start Backend:**
   ```bash
   cd backend
   source .venv/bin/activate
   python manage.py runserver 0.0.0.0:8000
   ```

2. **Start Frontend:**
   ```bash
   cd frontend
   npm run dev
   ```

## Testing Methods

### Method 1: Python Workflow Test (Recommended)

Tests the complete workflow programmatically:

```bash
cd backend
source .venv/bin/activate
python test_workflow.py
```

This script will:
1. Create a test user (or use existing)
2. Create a patient
3. Create modality and service
4. Create template with sections and fields
5. Publish template version
6. Create study (with auto-generated accession)
7. Create report
8. Finalize report and generate PDF

### Method 2: API Test Script

Tests the REST API endpoints using curl:

```bash
cd backend
./test_api.sh [base_url] [username] [password]
# Example:
./test_api.sh http://localhost:8000 admin admin123
```

### Method 3: Manual Testing via Frontend

1. **Login:**
   - Navigate to http://localhost:5173
   - Login with superuser credentials

2. **Create Patient:**
   - Go to Patients page
   - Click "Add Patient"
   - Fill in details (MRN, Name, Age, etc.)
   - Click "Create Patient"

3. **Create Modality and Service:**
   - Go to Studies page (or use API/Swagger)
   - Create a modality (e.g., USG, XRAY, CT)
   - Create a service linked to that modality

4. **Create Template:**
   - Go to Templates page
   - Click "Create Template"
   - Enter template name and modality code
   - Add sections and fields
   - For dropdown/checklist fields, add options
   - Click "Create Template"
   - Click "Publish Version" to create a versioned template

5. **Create Study:**
   - Go to Studies page
   - Click "Add Study"
   - Select patient and service
   - Fill in indication
   - Click "Create Study" (accession auto-generated)

6. **Create and Finalize Report:**
   - View the study (or use API)
   - Create report for the study using template version
   - Save draft with values
   - Finalize report (generates PDF)

### Method 4: API Documentation (Swagger)

1. Navigate to http://localhost:8000/api/docs/
2. Use the interactive Swagger UI to test endpoints
3. Authenticate using "Authorize" button with JWT token
4. Test each endpoint individually

## Expected Test Results

All tests should complete successfully with:

- ✅ Health endpoint returns 200
- ✅ Login returns JWT token
- ✅ Patient creation returns 201 with patient data
- ✅ Modality/Service creation successful
- ✅ Template creation with nested sections/fields
- ✅ Template version published successfully
- ✅ Study created with auto-generated accession
- ✅ Report created for study
- ✅ Report finalized and PDF generated
- ✅ Study status updated to "final"

## Smoke Tests Checklist

Based on TESTS.md:

### Backend Smoke Tests
- [x] `GET /api/health/` returns 200
- [x] Auth: Obtain token, refresh token
- [x] Patients: Create patient, Search patient by name/phone
- [x] Catalog: Create modality + service
- [x] Templates: Create template v1 with 2 sections, 5 fields (dropdown + checklist included)
- [x] Templates: Publish template version
- [x] Studies: Create study with service
- [x] Studies: List worklist by status
- [x] Reporting: Create report instance for study using template version
- [x] Reporting: Save values JSON
- [x] Reporting: Finalize report (locks) and generates PDF
- [x] Reporting: Download PDF endpoint works

### Frontend Smoke Tests
- [x] Login flow sets token
- [x] Patients list + create
- [x] Services list + create
- [x] Templates list + create basic schema
- [x] Study create + open report form + save draft + finalize

## Troubleshooting

### Database Connection Issues
- Ensure Docker containers are running: `docker compose ps`
- Check database credentials in `.env` or `settings.py`
- Verify database exists: `docker compose exec db psql -U rims -d rims`

### Migration Issues
- Delete migration files and recreate: `python manage.py makemigrations`
- Apply migrations: `python manage.py migrate`

### Authentication Issues
- Verify JWT endpoints are accessible
- Check CORS settings in `settings.py`
- Ensure frontend URL is in `CORS_ALLOWED_ORIGINS`

### PDF Generation Issues
- Check `MEDIA_ROOT` is writable
- Verify `reportlab` is installed
- Check file permissions on media directory

