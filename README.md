# RIMS (Radiology Information Management System) — AI Dev Pack (Scaffold)

This repo is a **merge-friendly, independent RIMS** designed to later merge into your LIMS with minimal pain.
It matches the same architectural philosophy: Django + DRF + Postgres + JWT + (optional) Celery/Redis + React/Vite.

## 🚀 Deployment Status

✅ **Production Ready** - Assessment completed January 6, 2026

- All critical security issues resolved
- Comprehensive deployment documentation
- Production configuration ready
- See [DEPLOYMENT_READINESS_ASSESSMENT.md](DEPLOYMENT_READINESS_ASSESSMENT.md) for details

## 📚 Documentation

- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Complete deployment guide
- **[SECURITY.md](SECURITY.md)** - Security best practices
- **[SETUP.md](SETUP.md)** - Development setup
- **[TESTING.md](TESTING.md)** - Testing guide
- **[STATUS.md](STATUS.md)** - Implementation status

## What is included
- Backend: Django 5 + DRF + JWT + drf-spectacular + django-filter + CORS
- Core domain apps: `patients`, `catalog`, `studies`, `templates`, `reporting`, `audit`, `accounts`
- Template Builder (schema-driven report forms): Template → Sections → Fields → Options
- Study workflow: Registered → In Progress → Draft → Final → Delivered
- Report storage: JSON values + generated PDF placeholder endpoint
- Frontend: React + TypeScript + Vite (starter pages + routing + auth placeholder)
- Docker Compose: Postgres (+ Redis optional)
- Caddy sample (optional) for reverse proxy
- GitHub issue templates + agent docs

## Quick start (local)
### 1) Backend
```bash
cd backend
cp .env.example .env
docker compose up -d db redis
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 0.0.0.0:8000
```

API docs:
- OpenAPI: http://localhost:8000/api/schema/
- Swagger UI: http://localhost:8000/api/docs/

### 2) Frontend
```bash
cd frontend
npm install
npm run dev
```

Frontend dev server:
- http://localhost:5173

## Default module map
- `patients`: Patient registration + search
- `catalog`: Modalities + Services (USG/XRAY/CT etc.)
- `studies`: Study/Order workflow + worklist
- `templates`: Template Builder (fields + sections + types)
- `reporting`: Report instance (values JSON + finalize + PDF generation)
- `audit`: audit log (who did what, when)
- `accounts`: users/roles/permissions placeholder

## Notes
- This is a scaffold intended for **Cursor (structure lock) → Codex (docker/migrations/smoke tests)** workflow.
- Template versioning is built-in so old reports never break when templates evolve.
