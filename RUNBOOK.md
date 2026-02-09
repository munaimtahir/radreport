# RadReport — Runbook

## 0. Purpose
This runbook provides the authoritative operational guide for the RadReport system. It is designed for developers and system administrators to ensure consistent setup, maintenance, and verification of the V2 reporting pipeline and core application workflows.

## 1. Prerequisites
- **OS**: Linux (Ubuntu 22.04+ recommended)
- **Software**:
    - Python 3.10+
    - Node.js 18+ (npm 10+)
    - Docker & Docker Compose
    - PostgreSQL 15+
- **Environment Variables** (Names only):
    - `DATABASE_URL`
    - `SECRET_KEY`
    - `DEBUG`
    - `ALLOWED_HOSTS`
    - `CORS_ALLOWED_ORIGINS`

## 2. Repository Structure (Mental Model)
- `backend/`: Django 5 application containing the REST API, Reporting Engine, and business logic.
- `frontend/`: React 18 / Vite / TypeScript Single Page Application (SPA).
- `seed_data/`: Canonical data for blocks and templates (located in `backend/apps/reporting/seed_data/`).
- `e2e/`: Playwright end-to-end test suite for critical workflow verification.
- `_graveyard/`: Quarantined legacy assets, documentation, and scripts scheduled for removal.

## 3. Backend — Local Development
1. **Create virtualenv**:
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate
   ```
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Run migrations**:
   ```bash
   python manage.py migrate
   ```
4. **Start server**:
   ```bash
   python manage.py runserver 0.0.0.0:8000
   ```

## 4. Frontend — Local Development
1. **Install dependencies**:
   ```bash
   cd frontend
   npm install
   ```
2. **Start dev server**:
   ```bash
   npm run dev
   ```

## 5. Template & Reporting Setup (CRITICAL)
1. **Import V2 Block Library**:
   ```bash
   python manage.py import_block_library
   ```
2. **Import V2 Templates**:
   ```bash
   python manage.py import_templates_v2
   ```
3. **Activate Templates**:
   Ensure the `status` in the template JSON is set to `"active"`. To activate via API:
   ```bash
   POST /api/reporting/templates-v2/{id}/activate/
   ```
4. **Map Services to Templates**:
   This is handled automatically by `import_templates_v2` using the default activation CSV. To map manually via API:
   ```bash
   POST /api/reporting/service-templates-v2/
   # Body: {"service": "id", "template": "id", "is_active": true, "is_default": true}
   ```
5. **Verify Active Template Mapping**:
   Run the import script in dry-run mode to see the current effective mapping:
   ```bash
   python manage.py import_templates_v2 --dry-run
   ```

## 6. End-to-End Report Flow (Happy Path)
1. **Create Work Item**: A patient visit is registered and a `ServiceVisitItem` is generated.
2. **Enter Report Values**: Performer opens the report in the UI. Frontend hits `GET /api/reporting/workitems/{id}/values/`.
3. **Save**: Draft values are saved via `POST /api/reporting/workitems/{id}/save/`.
4. **Submit**: Performer locks the report via `POST /api/reporting/workitems/{id}/submit/`. Status becomes `submitted`.
5. **Verify**: Verifier reviews and calls `POST /api/reporting/workitems/{id}/verify/`. Status becomes `verified`.
6. **Publish**: Verifier finalizes the report via `POST /api/reporting/workitems/{id}/publish/`. Status becomes `PUBLISHED`.
7. **Generate PDF**: The finalized PDF snapshot is available via `GET /api/reporting/workitems/{id}/published-pdf/`.

## 7. Tests & Validation
- **Backend Tests**: Run `python manage.py test` or `pytest`.
- **Frontend Tests**: Run `npm test` inside the `frontend/` directory.
- **E2E Smoke Tests**: Run `npm run e2e:smoke` from the root directory.
- **Pass Definition**: A "pass" means 0 failures across all suites. This guarantees the integrity of the V2 reporting pipeline and core CRUD operations.

## 8. Production Notes (Non-sensitive)
- **Backend Execution**: Run via Gunicorn workers (`gunicorn rims_backend.wsgi:application`).
- **Frontend Serving**: Served as static assets (built via `npm run build`).
- **Reverse Proxy**: Caddy handles TLS termination, proxies `/api/` and `/admin/` to Gunicorn, and serves frontend static files. Use the root `Caddyfile`.

## 9. Known Non-Goals
- **Legacy V1 Reporting**: No support for Jinja2 or legacy Django templates for reports.
- **Third-Party LIMS Integration**: This runbook strictly covers the standalone RadReport deployment.
- **OS Customization**: This guide assumes a standard Debian-based Linux environment.
