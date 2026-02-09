# Phase 2 Frontend Legacy API Containment (RIMS)

## Legacy endpoint inventory

| File | Legacy endpoint | UI feature / usage | Action |
| --- | --- | --- | --- |
| `frontend/src/views/Dashboard.tsx` | `/api/studies` (`/studies/?status=...`) | Dashboard stats for registered/draft/final studies | Removed legacy stats and replaced final count with workflow published visits. |
| `frontend/src/views/ReportEditor.tsx` | `/api/reports` (`/reports/:id`, `/reports/:id/save_draft`, `/reports/:id/finalize`, `/api/reports/:id/download_pdf`) | Legacy report editor for study reports | Route disabled and navigation removed; editor now inaccessible in Phase 2. |
| `frontend/src/ui/App.tsx` | `/api/studies` (route `/studies`), `/api/reports` (route `/reports/:reportId/edit`) | Legacy studies list and legacy report editor routes | Routes now redirect to safe workflow pages. |

No frontend usage of `/api/visits` (legacy) was found in the current UI.

## Actions taken per endpoint

- **`/api/studies`**
  - Removed Dashboard stats and links that depended on `/studies`.
  - Disabled `/studies` route to prevent direct access.
- **`/api/reports` (non-workflow)**
  - Disabled `/reports/:reportId/edit` route to prevent the legacy ReportEditor from loading.
  - Removed Final Reports PDF fallback to `/api/pdf/...` so the page relies only on workflow-provided PDF URLs.

## Files changed

- `frontend/src/ui/App.tsx`
- `frontend/src/views/Dashboard.tsx`
- `frontend/src/views/FinalReportsPage.tsx`
- `PHASE2_REPORT.md`

## Deferred to Phase 3+

- Full removal or replacement of the legacy `ReportEditor` component once workflow-first editing is ready.
- Review legacy patients/templates areas if they should be migrated or disabled alongside other legacy UI paths.
