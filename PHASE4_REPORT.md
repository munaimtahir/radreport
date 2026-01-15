# Phase 4 OPD Containment Report

## OPD Inventory

### Frontend surfaces
| File | OPD route/UI | OPD API endpoint(s) | Status |
| --- | --- | --- | --- |
| `frontend/src/ui/App.tsx` | `/worklists/opd/*`, `/opd/*` | N/A | **Disabled** (renders module-disabled message). |
| `frontend/src/views/OPDVitalsWorklistPage.tsx` | OPD vitals worklist UI (not routed) | `/workflow/visits/?workflow=OPD&status=REGISTERED`, `/workflow/opd/vitals/` | **Inactive** (no navigation or routes; direct URLs now hit disabled route). |
| `frontend/src/views/ConsultantWorklistPage.tsx` | OPD consultation worklist UI (not routed) | `/workflow/visits/?workflow=OPD&status=IN_PROGRESS`, `/workflow/opd/consult/` | **Inactive** (no navigation or routes; direct URLs now hit disabled route). |
| `frontend/src/views/FinalReportsPage.tsx` | OPD filter for prescriptions | `/workflow/visits/?workflow=OPD` | **Disabled** (OPD filter removed; OPD results filtered out). |

### Backend surfaces
| File | OPD route/API | Status |
| --- | --- | --- |
| `backend/rims_backend/urls.py` | `/api/workflow/opd/vitals/`, `/api/workflow/opd/consult/` | **Disabled** via feature flag gating. |
| `backend/apps/workflow/api.py` | `OPDVitalsViewSet`, `OPDConsultViewSet`, `/api/pdf/{id}/prescription/` | **Disabled** via feature flag gating (404 when OPD disabled). |
| `backend/apps/workflow/api.py` | `/api/workflow/visits/?workflow=OPD` | **Disabled** via feature flag gating (404 when OPD disabled). |
| `backend/apps/workflow/api.py` | `/api/workflow/items/worklist/?department=OPD` | **Disabled** via feature flag gating (404 when OPD disabled). |

## Containment Actions

### Frontend
- Added explicit OPD routes that render a safe module-disabled message with the required copy.
- Removed OPD filter option in Final Reports and filtered OPD results from the listing so OPD prescriptions no longer appear.
- Left OPD worklist components in place but unreachable (no navigation or active routes).

### Backend
- Added feature flag `OPD_ENABLED` (default `False`).
- When `OPD_ENABLED` is false:
  - OPD viewsets return `404` (`"OPD disabled"`).
  - OPD workflow filters (`workflow=OPD` and `department=OPD`) return `404`.
  - Prescription PDF endpoint returns `404`.

## Containment Approach
**Feature flag gating** (Option 1). OPD endpoints are now explicitly disabled in production by default and return a safe `404` response.

## Phase 4B Re-enable Checklist
1. Set `OPD_ENABLED=True` in environment/config.
2. Re-introduce OPD routes/navigation links in `frontend/src/ui/App.tsx`.
3. Restore OPD filter in `frontend/src/views/FinalReportsPage.tsx`.
4. Confirm OPD worklist pages are wired to routes and role access matches RBAC.
5. Re-run workflow tests and add OPD-specific tests.

## Files Changed
- `backend/apps/workflow/api.py`
- `backend/rims_backend/settings.py`
- `frontend/src/ui/App.tsx`
- `frontend/src/views/FinalReportsPage.tsx`
- `frontend/src/views/ModuleDisabled.tsx`
- `PHASE4_REPORT.md`
