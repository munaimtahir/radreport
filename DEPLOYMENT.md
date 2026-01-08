RIMS Production Deployment (rims.alshifalab.pk)
==============================================

Environment
-----------
- VPS (Linux) at IP 34.124.150.231
- Domain rims.alshifalab.pk
- Reverse proxy: Caddy
- Deployment: docker-compose

Prerequisites
-------------
- Docker and docker compose installed
- Caddy installed on host and running as a service
- DNS A-record rims.alshifalab.pk → 34.124.150.231
- Firewall allows 80/443

Repository Setup
----------------
On the VPS:
1) Clone or update repo safely
   - Configure a consistent pull strategy (LOCKED):
     git config pull.rebase true
   - Safe update steps:
     git fetch --all --prune
     git status
     git log --oneline -n 10
     git pull
   - If pull rejects due to divergence:
     - Last-resort (destructive):
       git fetch origin
       git reset --hard origin/main

2) Environment variables (.env file in repo root)
   Create `.env` with the following (example):
     DJANGO_SECRET_KEY=change-me
     DJANGO_ALLOWED_HOSTS=rims.alshifalab.pk,127.0.0.1,localhost
     CORS_ALLOWED_ORIGINS=https://rims.alshifalab.pk
     DB_NAME=rims
     DB_USER=rims
     DB_PASSWORD=strong-db-password
     GUNICORN_WORKERS=4
     GUNICORN_TIMEOUT=120

Docker Compose
--------------
Services and ports:
- backend (Django + Gunicorn) → 127.0.0.1:8015
- frontend (React, served by nginx) → 127.0.0.1:8081
- db (Postgres) internal only

Static and Media
----------------
- Django uses WhiteNoise to serve static at `/static/`.
- `docker-compose.yml` mounts:
  - `media_data` → `/app/media`
  - `static_data` → `/app/staticfiles`
- Entry point runs `collectstatic` at startup.

Reverse Proxy (Caddy)
---------------------
The provided `Caddyfile` includes the RIMS block:
- rims.alshifalab.pk
  - /api/*, /admin/*, /static/*, /media/*, /docs*, /schema* → 127.0.0.1:8015 (backend)
  - All other paths → 127.0.0.1:8081 (frontend)

Caddy validation and reload:
  sudo caddy validate --config /etc/caddy/Caddyfile
  sudo caddy reload --config /etc/caddy/Caddyfile

Build and Run
-------------
From repo root:
  docker compose build --no-cache backend
  docker compose build frontend
  docker compose up -d

Check containers:
  docker compose ps

Domain Checks
-------------
Run from any machine:
  curl -I https://rims.alshifalab.pk/
  curl -s https://rims.alshifalab.pk/api/health/
  curl -I https://rims.alshifalab.pk/api/schema/
  curl -I https://rims.alshifalab.pk/admin/
  curl -I https://rims.alshifalab.pk/static/
  curl -I https://rims.alshifalab.pk/media/

Smoke Tests
-----------
API smoke:
  RIMS_HOST=rims.alshifalab.pk bash scripts/smoke_api.sh

PDF generation (inside backend container):
  docker compose exec backend python scripts/smoke_pdf.py
  # Tests all PDF types: receipts, reports, prescriptions
  # Validates PDF output starts with %PDF and has reasonable size

Workflow end-to-end (inside backend container):
  docker compose exec backend python scripts/smoke_workflow.py
  # Tests complete workflows: patient → visit → invoice → PDF generation
  # Creates test data and validates USG and OPD workflows

Common Production Failure Modes
-------------------------------
- Divergent branches on VPS:
  - Use the documented safe update flow above.
  - As last resort: reset hard to origin/main.
- PDFs fail to render:
  - Ensure backend image rebuilt after Dockerfile changes:
    docker compose build --no-cache backend && docker compose up -d
  - Run PDF smoke test:
    docker compose exec backend python scripts/smoke_pdf.py
  - Verify ReportLab is installed:
    docker compose exec backend python -c "import reportlab; print(reportlab.Version)"
  - All PDFs use ReportLab (WeasyPrint removed)
- Static 404 or mismatched hashes:
  - Restart backend to force `collectstatic`:
    docker compose restart backend
  - Verify `/app/staticfiles` volume exists and has assets.
- Media 404:
  - Ensure uploads exist under `/app/media` and volume `media_data` is attached.
  - Access via `https://rims.alshifalab.pk/media/<path>`.

PDF Architecture
----------------
All PDF generation uses ReportLab for deterministic, print-safe output:
- Location: `backend/apps/reporting/pdf_engine/`
- Modules:
  - `base.py` - Common styles, page templates, utilities
  - `receipt.py` - Payment receipts (Visit and ServiceVisit models)
  - `clinical_report.py` - USG reports and diagnostic reports
  - `prescription.py` - OPD prescriptions
- Output: A4 format, all PDFs start with `%PDF` header
- WeasyPrint completely removed (no HTML-to-PDF conversion)

VPS-Specific Notes
------------------
- Target IP: 34.124.150.231
- Domain: rims.alshifalab.pk
- Backend port: 127.0.0.1:8015
- Frontend port: 127.0.0.1:8081

