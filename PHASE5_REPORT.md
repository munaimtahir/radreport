# Phase 5 Production Hardening Report

## Overview
This phase focuses on production hardening for the USG workflow only (no new features, no UI changes). The work adds explicit production-safe settings, health checks, PDF robustness, structured workflow logging, and a smoke-test command for USG that avoids damaging real data.

## What changed and why
### Settings hardening
- **Environment-driven security defaults**: `DEBUG`, `SECRET_KEY`, and `ALLOWED_HOSTS` remain driven by env vars with safe defaults (no wildcards by default). This prevents accidental production exposure.
- **Security flags**: Added configurable `SECURE_PROXY_SSL_HEADER`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, and HSTS settings to allow safe production defaults without breaking local dev.
- **Media path consistency**: Ensured `MEDIA_URL` is `/media/` to align with Django’s static helper and PDF serving paths.

### Health endpoints
- **`GET /api/health/`** (no auth): Returns minimal diagnostics (status, db, time, version) to support uptime monitoring and load balancer checks.
- **`GET /api/health/auth/`** (auth required): Returns the authenticated user and groups to validate RBAC wiring.

### PDF robustness
- **Safe PDF path resolution**: PDF paths are resolved under `MEDIA_ROOT` to prevent directory traversal.
- **Actionable 404s**: Missing PDF responses now include the report/consult ID and expected path.
- **PDF publish logging**: Publishing logs now capture the report ID and file path for debugging and auditability.

### Workflow logging
- **Structured transition logs**: Transition service logs now record user, visit/item IDs, and status transitions.
- **Explicit action logs**: Submit-for-verification, finalize, publish, and return-for-correction now log key details.

### Production smoke command
- **New `smoke_prod_usg` command**: Validates the USG pipeline end-to-end without UI. It reuses or creates deterministic `SMOKE_` data and verifies:
  1. a USG report reaches FINAL
  2. a PDF is generated and exists on disk
  3. `/api/health/` returns OK

## How to run health checks
```bash
curl -s http://localhost:8000/api/health/
```
```bash
curl -s -H "Authorization: Bearer <token>" http://localhost:8000/api/health/auth/
```

## How to run the USG production smoke command
```bash
python manage.py smoke_prod_usg
```

## Known remaining risks (top 5)
1. **Static/media hosting**: Media is still served via Django; production should front PDFs with a web server or object storage.
2. **Security headers**: HSTS and secure cookies are configurable but depend on proper env configuration in production.
3. **Logging aggregation**: Structured logs rely on deployment logging configuration to be collected and searched.
4. **Test coverage**: E2E coverage is via smoke commands; broader integration coverage may still be limited.
5. **Secrets management**: `SECRET_KEY` must be set in production; defaults are safe for dev but not production.

## Files changed
- `backend/rims_backend/settings.py`
- `backend/rims_backend/urls.py`
- `backend/apps/workflow/api.py`
- `backend/apps/workflow/transitions.py`
- `backend/apps/workflow/management/commands/smoke_prod_usg.py`
- `PHASE5_REPORT.md`
