# Phase 6 report — Production delivery & observability (Caddy routing, USG only)

## Topology detection (evidence-based)

Commands executed in this environment:

- `docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Ports}}"` → `docker: command not found` (Docker CLI not available here).
- `ss -lntp | head` → `ss: command not found` (socket utilities not available here).
- `systemctl status caddy --no-pager` → systemd not available ("System has not been booted with systemd").
- `systemctl status nginx --no-pager` → systemd not available ("System has not been booted with systemd").

Result: No nginx process detected in this environment; none appears in `docker-compose.yml`. If nginx is present in production, it is external to this repo and should be documented in the runbook.

## Deployment diagram (intended)

```
Internet
  → Caddy (host)
    → / (frontend static or reverse proxy)
    → /api/* (Django/Gunicorn in Docker)
    → /media/* (file_server from MEDIA_ROOT)
  → DB (PostgreSQL container)
```

## Django media serving (prod hardening)

- Django now serves `/media/` **only when `DEBUG=True`**. In production, `/media/` must be handled by Caddy.

## Caddy snippet for `/media/`

```
handle_path /media/* {
  root * /ABS/PATH/TO/MEDIA_ROOT
  file_server
}
```

### MEDIA_ROOT path

- Django `MEDIA_ROOT` = `<repo>/backend/media` (container path: `/app/media`).
- `docker-compose.yml` mounts a named volume `media_data` to `/app/media`.
- **If Caddy runs on the host**: mount the same media directory on the host and point Caddy to that host path.
  - Example: map a host directory to `/app/media` in the backend container, and reuse the same host directory in Caddy.

## Health checks

- External unauthenticated: `GET https://<domain>/api/health/`
- JWT authenticated: `GET https://<domain>/api/health/auth/` with `Authorization: Bearer <token>`

## Logging visibility

- Django logging is configured to stdout/stderr with a console handler.
- Workflow transitions emit `workflow_transition` log entries with IDs and actions.

## Production smoke checklist

See `docs/production/SMOKE_CHECKLIST.md` for the full step-by-step flow.

## Files changed

- `backend/rims_backend/urls.py`
- `backend/rims_backend/settings.py`
- `docs/production/LOGGING.md`
- `docs/production/SMOKE_CHECKLIST.md`
- `scripts/prod_verify.sh`
- `PHASE6_REPORT.md`
