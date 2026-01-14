# Routes Map (Current)

## Backend (API)
Base path: `/api/`

### Core / auth / docs
- `GET /api/health/` – health check.
- `POST /api/auth/token/` – JWT login.
- `POST /api/auth/token/refresh/` – JWT refresh.
- `GET /api/schema/` – OpenAPI schema.
- `GET /api/docs/` – Swagger UI.

### Patients
- `GET/POST /api/patients/` – list/create patients.
- `GET/PUT/PATCH/DELETE /api/patients/{id}/` – patient detail.

### Catalog (legacy services)
- `GET/POST /api/modalities/` and `/api/modalities/{id}/` – modality CRUD.
- `GET/POST /api/services/` and `/api/services/{id}/` – service CRUD.
- `POST /api/services/import-csv/` – import service master from CSV.

### Templates (legacy reporting)
- `GET/POST /api/templates/` and `/api/templates/{id}/` – template CRUD.
- `POST /api/templates/{id}/publish/` – create and publish a new template version.
- `GET /api/template-versions/` and `/api/template-versions/{id}/` – read-only versions.

### Studies + Visits (legacy flow)
- `GET/POST /api/studies/` and `/api/studies/{id}/` – study CRUD.
- `GET/POST /api/visits/` and `/api/visits/{id}/` – visit CRUD.
- `POST /api/visits/unified-intake/` – combined patient + visit + order items.
- `POST /api/visits/{id}/finalize/` – finalize visit.
- `POST /api/visits/{id}/generate-receipt/` – create receipt number + PDF.
- `GET /api/visits/{id}/receipt/` – stream receipt PDF.
- `GET /api/visits/{id}/receipt-preview/` – preview receipt HTML.

### Reports (legacy reporting)
- `GET/POST /api/reports/` and `/api/reports/{id}/` – report CRUD.
- `POST /api/reports/create_for_study/` – create report for a study.
- `POST /api/reports/{id}/save_draft/` – update values/narrative.
- `POST /api/reports/{id}/finalize/` – finalize and generate PDF.
- `GET /api/reports/{id}/download_pdf/` – download report PDF.

### Audit
- `GET /api/audit/` and `/api/audit/{id}/` – audit logs.

### Receipt branding
- `GET/PUT/PATCH /api/receipt-settings/` – singleton receipt settings.
- `POST /api/receipt-settings/logo/` – upload logo image.
- `POST /api/receipt-settings/header-image/` – upload header image.

### Workflow (desk-based)
- `GET/POST /api/workflow/service-catalog/` – workflow service master.
- `GET/POST /api/workflow/visits/` – service visits list/create.
- `POST /api/workflow/visits/create_visit/` – registration desk create visit.
- `POST /api/workflow/visits/{id}/transition_status/` – status transitions.
- `GET/POST /api/workflow/usg/` – USG reports create/update.
- `POST /api/workflow/usg/{id}/save_draft/` – save draft.
- `POST /api/workflow/usg/{id}/submit_for_verification/` – submit for verification.
- `POST /api/workflow/usg/{id}/publish/` – publish and generate PDF.
- `POST /api/workflow/usg/{id}/return_for_correction/` – return with reason.
- `GET/POST /api/workflow/opd/vitals/` – OPD vitals create/update.
- `GET/POST /api/workflow/opd/consult/` – OPD consult create/update.
- `POST /api/workflow/opd/consult/{id}/save_and_print/` – generate prescription PDF.

### Workflow PDF shortcuts
- `GET /api/pdf/receipt/{service_visit_id}/` – workflow receipt.
- `GET /api/pdf/report/{service_visit_id}/` – USG report PDF.
- `GET /api/pdf/prescription/{service_visit_id}/` – OPD prescription PDF.

## Frontend (pages)
- `/login` – authentication.
- `/` – dashboard.

**Workflow (desk-based)**
- `/registration` – registration desk (workflow service visits).
- `/worklists/usg` – USG worklist.
- `/worklists/opd-vitals` – OPD vitals.
- `/worklists/consultant` – OPD consult.
- `/worklists/verification` – USG verification.
- `/reports` – final reports list.

**Legacy (candidate for removal)**
- `/intake` – front desk intake (legacy Visit/Study flow).
- `/patients` – patient list (legacy admin-style screen).
- `/studies` – studies list + report links.
- `/templates` – template builder CRUD.
- `/receipt-settings` – receipt branding settings.
- `/reports/:reportId/edit` – report editor.

> Any page marked “candidate for removal” is still present but overlaps with the desk-based workflow.
