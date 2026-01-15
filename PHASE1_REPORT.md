# Phase 1 Report (RIMS) — Registration → USG → Verify → PDF

## How to run (dev)

### Backend
```bash
cd backend
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

### Frontend
```bash
cd frontend
npm install
# Optional: point to a custom API host
# export VITE_API_BASE=http://localhost:8000/api
npm run dev
```

## Seed/smoke script
```bash
cd backend
python manage.py seed_smoke_phase1
```

Notes:
- The script reuses existing records when possible and is safe to re-run.
- If no superuser exists, it creates `phase1_admin` / `phase1_admin` for the workflow transitions.

## Sample output (seed/smoke)
```
Phase 1 seed complete:
- Patient ID: c64da2ac-5adb-42e6-95b6-e3f8e3c68386
- Service ID: 1e0e4b93-7d9d-426d-b875-f455f1a3ce3a
- Template ID: ba863916-b6e7-4384-8758-fde7cf9e36fe
- Template Version ID: 1aae630e-b166-43fd-9362-4229e0a6833b
- Service Visit ID: c60883ad-9664-486c-840d-2b967acadc94 (visit_id=SV202601150001)
- Service Visit Item ID: 7b406bc8-1ac3-46ff-bdbd-75ef2f05e33b (status=PUBLISHED)
- USG Report ID: 3b5eab36-218c-4680-b8c9-715d006a4c7d (status=FINAL)
- Published PDF Path: pdfs/reports/usg/2026/01/SV202601150001_v1.pdf
```

## Files changed
- `backend/apps/workflow/management/commands/seed_smoke_phase1.py`
- `backend/apps/workflow/serializers.py`
- `frontend/src/views/FinalReportsPage.tsx`
- `frontend/src/views/RegistrationPage.tsx`
- `PHASE1_REPORT.md`

## Remaining known issues (deferred to Phase 2/3)
- No automated curl-based E2E login flow is included yet; current proof relies on the seed/smoke command plus frontend build.
- ReportEditor uses the reporting app PDF endpoint (`/api/reports/{id}/download_pdf/`) which is separate from the workflow PDF endpoints.
