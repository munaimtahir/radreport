# CURRENT_APPLICATION_STATE.md
## Repo Identity
d3b2432ea051f9ce6680570bdcef4e660ecebd12
## docker-compose services
services:
  backend:
    build:
      context: /home/munaim/srv/apps/radreport/backend
      dockerfile: Dockerfile
    container_name: rims_backend_prod
    depends_on:
      db:
        condition: service_healthy
        required: true
    environment:
      CORS_ALLOWED_ORIGINS: https://rims.alshifalab.pk
      CSRF_TRUSTED_ORIGINS: https://rims.alshifalab.pk,https://api.rims.alshifalab.pk
      DB_ENGINE: postgresql
      DB_HOST: db
      DB_NAME: rims
## Build/Boot Status
NAME                         IMAGE                      COMMAND                  SERVICE    CREATED          STATUS                    PORTS
smoke_radreport-backend-1    smoke_radreport-backend    "/app/scripts/entryp…"   backend    14 minutes ago   Up 14 minutes (healthy)   127.0.0.1:8015->8000/tcp
smoke_radreport-db-1         postgres:16-alpine         "docker-entrypoint.s…"   db         20 minutes ago   Up 20 minutes (healthy)   5432/tcp
smoke_radreport-frontend-1   smoke_radreport-frontend   "/docker-entrypoint.…"   frontend   18 minutes ago   Up 18 minutes (healthy)   127.0.0.1:8081->80/tcp
## Backend Status
Migrations: Applied
Tests: FAILED (Runner TypeError, see logs)
## Frontend Status
Build: SUCCESS
Routes: CONFIRMED (/, /reporting/worklist)
## End-to-End Reporting Workflow Evidence
Item UUID: b70cb88e-8d3b-483e-bf53-52948ce0fa83
Profile: USG_SMOKE
PDF Status: CREATED (%PDF match)
-rw-rw-r--+ 1 munaim munaim 320577 Jan 29 13:41 artifacts/20260129_030115/tmp/published_v1.pdf
## Known Issues / Risks
- Django Test Runner failing with TypeError (namespace/import issue)
- 'published-integrity' endpoint MISSING from views.py (exists in tests but not in ViewSet)
## Verdict: PASS (with caveats)
Stack is functional, workflow completes, PDF renders. Tests need fixing.
