# Repository Audit (Current State)

## Tech stack
- **Backend:** Django 5 + Django REST Framework (DRF).
- **Database:** Postgres (docker-compose services).
- **Auth:** JWT via SimpleJWT (`/api/auth/token/`, `/api/auth/token/refresh/`).
- **API docs:** drf-spectacular OpenAPI + Swagger UI (`/api/schema/`, `/api/docs/`).
- **Frontend:** React + TypeScript + Vite. Navigation is in `frontend/src/ui/App.tsx`.
- **PDF engines:**
  - ReportLab for the basic radiology report PDF (`build_basic_pdf`).
  - WeasyPrint for receipts and workflow PDFs (USG report, OPD prescription).

## How to run locally
**Backend (manual dev flow)**
1. `cd backend`
2. `docker compose up -d db redis` (uses `backend/docker-compose.yml`).
3. `python -m venv .venv && source .venv/bin/activate`
4. `pip install -r requirements.txt`
5. `python manage.py migrate`
6. `python manage.py createsuperuser`
7. `python manage.py runserver 0.0.0.0:8000`

**Frontend (manual dev flow)**
1. `cd frontend`
2. `npm install`
3. `npm run dev`

**Notes / env files**
- The README references copying `.env.example` for backend, but no `.env.example` exists in `backend/` in this repo. **Needs verification**.
- Production-style containers are defined in the root `docker-compose.yml` (backend + frontend + Postgres).

## Key directories
- `backend/apps/`: Django domain apps (patients, catalog, studies, templates, reporting, workflow, audit).
- `backend/rims_backend/`: Django project settings + URL router (`urls.py`).
- `frontend/src/views/`: React screens (workflow and legacy pages).
- `docs/`: existing documentation set (architecture, workflows, etc.).

## Main workflows/screens present
**Workflow (newer, desk-based UI)**
- Registration desk (`/registration`) creates a service visit in the workflow system.
- USG worklist (`/worklists/usg`) for USG reporting and submission to verification.
- OPD vitals (`/worklists/opd-vitals`) for vitals entry.
- Consultant (`/worklists/consultant`) for OPD consultation and prescription PDF generation.
- Verification (`/worklists/verification`) to publish USG reports.
- Final reports (`/reports`) lists published USG reports or OPD prescriptions.

**Legacy (older, study/report flow)**
- Front desk intake (`/intake`) creates a `Visit` + `OrderItem` + `Study` via unified intake.
- Patients list (`/patients`).
- Studies list (`/studies`) for the classic Study workflow and report links.
- Templates (`/templates`) and report editor (`/reports/:reportId/edit`).
- Receipt settings (`/receipt-settings`).

## Roles and access
- Roles are defined as desk roles (Registration, Performance, Verification). Permissions check Django groups or a user profile `desk_role`.
- For MVP, `IsAnyDesk` allows any authenticated user; role enforcement is partly disabled. **Needs verification** for production settings.

## Known red flags / partial features
- **Two parallel service catalogs:** `catalog.Service` (radiology services) vs `workflow.ServiceCatalog` (USG/OPD). This can split pricing and selection logic. **Needs verification** which one is authoritative now.
- **Two intake flows:** `FrontDeskIntake` uses `/visits/unified-intake/` (Visit + OrderItems + Studies). `RegistrationPage` uses `/workflow/visits/create_visit/` (ServiceVisit + Invoice + Payment). This duplicates “registration” in two systems.
- **PDF generation duplication:** receipts are generated both in `apps/reporting/pdf.py` (visit receipts) and `apps/workflow/pdf.py` (service-visit receipts). This may lead to two receipt formats and storage paths.
- **USG worklist filter mismatch:** the UI sends `status=REGISTERED,RETURNED_FOR_CORRECTION`, but the backend expects a single status value, so filtering may fail. **Needs verification** in runtime.
- **Patient update uses POST:** `RegistrationPage` updates patients via `apiPost` (POST), while DRF expects PUT/PATCH for updates. **Needs verification** if the backend accepts POST updates.
- **Report creation gap in UI:** there is no obvious frontend action that calls `/reports/create_for_study/`, so report creation may be manual or missing in the legacy flow. **Needs verification**.
