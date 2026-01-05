# TESTS.md — Smoke tests (MVP)

## Backend smoke tests
- `GET /api/health/` returns 200
- Auth:
  - Obtain token, refresh token
- Patients:
  - Create patient
  - Search patient by name/phone
- Catalog:
  - Create modality + service
- Templates:
  - Create template v1 with 2 sections, 5 fields (dropdown + checklist included)
  - Publish template version
- Studies:
  - Create study with service
  - List worklist by status
- Reporting:
  - Create report instance for study using template version
  - Save values JSON
  - Finalize report (locks) and generates PDF
  - Download PDF endpoint works

## Frontend smoke tests
- Login flow sets token
- Patients list + create
- Services list + create
- Templates list + create basic schema
- Study create + open report form + save draft + finalize
