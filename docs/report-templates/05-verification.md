# Verification

## Backend
- Migration run: `python backend/manage.py migrate`
- Server boot: `python backend/manage.py runserver 0.0.0.0:8000` (validated with `/api/health/`)
- API smoke: `curl http://localhost:8000/api/health/`

## Frontend
- Build: `npm run build` (from `frontend/`)
- Dev boot: `npm run dev -- --host 0.0.0.0 --port 5173` (timed out after a short startup window)

## UI paths tested
- Admin → Report Templates
- Admin → Service Templates
- USG Worklist dynamic template rendering (manual smoke by code inspection)

## Compatibility notes
- Legacy report editor and USG report flows remain unchanged when no report template is linked to the service.
