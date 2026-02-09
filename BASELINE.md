# RadReport — Operational Baseline

## 1. Active System (In Scope)
- **Backend**: Django 5+ (Python) with Django REST Framework. Serves API only.
- **Frontend**: React 18 with Vite and TypeScript. Single Page Application (SPA).
- **Reporting Model**: **V2** (JSON Schema + UI Schema). Defined in `apps.reporting.models.ReportTemplateV2`.
- **Template System**: JSON-based templates storing structure (`json_schema`) and layout (`ui_schema`).
- **Import / Activation**: Templates are seeded from `backend/apps/reporting/seed_data/templates_v2/` via management commands.
- **PDF Generation**: Active. Handled by `apps.reporting.pdf_engine.report_pdf_v2` using ReportLab.

## 2. Explicitly Out of Scope
- **Legacy Reporting**: V1 Reporting (Jinja2/Django Template based) is deprecated/removed.
- **Deprecated Workflows**: Any workflow not using the "Three Desk" (Registration -> Performance -> Verification) model.
- **Old Template Engines**: Pure HTML/Django templates for reports.
- **Graveyard**: Items listed in `_graveyard/INVENTORY.md` are candidates for deletion and not part of the active system.

## 3. Runtime Entry Points
- **Backend Startup**: `gunicorn rims_backend.wsgi:application` (Production) or `manage.py runserver` (Dev).
- **Frontend Startup**: `npm run dev` (Vite) or Caddy serving static build (Production).
- **Canonical API Namespace**: `/api/` (Core), `/api/reporting/` (Reporting V2), `/api/dashboard/`.
- **Reporting Invocation**: Via `/api/reporting/workitems/` endpoints in `ReportWorkItemViewSet`.

## 4. Data & Templates
- **Template Source**: JSON files in `backend/apps/reporting/seed_data/templates_v2/`.
- **Import Mechanism**: Loaded into `ReportTemplateV2` table via seeding scripts.
- **Service Mapping**: `ServiceReportTemplateV2` maps Catalog Services to V2 Templates.
- **Missing Template Behavior**: System requires an active mapping; absence usually results in a configuration error or fallback to default if configured.

## 5. Tests & Validation (Current Reality)
- **E2E Tests**: Playwright harness in `e2e/` covers critical flows (Smoke Test). Trusted.
- **Backend Tests**: `pytest` suite for API and Models. Trusted.
- **Frontend Tests**: `vitest` for components. Trusted.
- **Manual Verification**: "Three Desk" workflow manually verified.

## 6. Legacy / Historical Artifacts
- **Inventory**: `_graveyard/INVENTORY.md` lists files identified for potential cleanup.
- **Status**: No deletions have occurred yet; files are moved to `_graveyard` or listed there for audit.
- **Runtime**: Items in `_graveyard` do not participate in runtime behavior.

## 7. What This Baseline Means
This document represents the known, working state of the system called "RadReport V2". Future contributors should trust the V2 reporting pipeline and the React/Django stack. Any reference to V1, Jinja reporting, or legacy scripts outside the documented set should be ignored or treated as technical debt.
