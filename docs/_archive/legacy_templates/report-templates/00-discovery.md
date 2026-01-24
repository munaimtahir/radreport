# Report Templates Discovery Notes

## Backend apps and current reporting locations
- Core backend apps involved in reporting: `apps/reporting`, `apps/workflow`, `apps/templates`, `apps/catalog`, `apps/studies`.
- Legacy report flow lives in `apps/reporting` with `Report` and `ReportViewSet` for study-based reporting.
- Workflow reporting lives in `apps/workflow` with `USGReport` and worklist endpoints for item-centric reporting.
- Existing template system (section-based) lives in `apps/templates` with `Template`, `TemplateSection`, `TemplateField`, and `TemplateVersion`.

## Existing models
- **Service**: `apps.catalog.models.Service` (includes `default_template` link to `templates.Template`).
- **Worklist/Visit**: `apps.workflow.models.ServiceVisit` and `ServiceVisitItem`.
- **Report models**: `apps.reporting.models.Report` (legacy) and `apps.workflow.models.USGReport` (workflow).

## Current reporting endpoints used by frontend
- Workflow reporting: `/api/workflow/usg/`, `/api/workflow/usg/{id}/save_draft/`, `/api/workflow/usg/{id}/submit_for_verification/`.
- Worklist data: `/api/workflow/visits/` and `/api/workflow/items/`.
- Legacy report editor: `/api/reports/{id}/`, `/api/reports/{id}/save_draft/`, `/api/reports/{id}/finalize/`.

## Frontend framework + UI locations
- Frontend is React (Vite) under `frontend/src`.
- Reporting UI surfaces in `frontend/src/views/USGWorklistPage.tsx` (performance desk) and `frontend/src/views/ReportEditor.tsx` (legacy study report editor).
- Verification review UI is in `frontend/src/views/VerificationWorklistPage.tsx`.

## Auth method + roles/permissions patterns
- Auth uses JWT (`rest_framework_simplejwt`) with `/api/auth/token/` and `/api/auth/me/` endpoints.
- Role checks are group-based (`registration`, `performance`, `verification`) via `apps.workflow.permissions`.
- Admin capabilities typically rely on `is_superuser` or `IsAdminUser` for privileged actions.
