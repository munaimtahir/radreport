# API Contracts

## Auth
POST /api/auth/token/
POST /api/auth/refresh/
GET /api/auth/me/

## Health
GET /api/health/ - Public health check (enhanced for dashboard)

## Dashboard (v1)
GET /api/dashboard/summary/ - KPI counts for Layer 1
GET /api/dashboard/worklist/ - Work items for Layer 2 (role-based)
GET /api/dashboard/flow/ - Today's flow counts for Layer 3

See [dashboard.md](./dashboard.md) for detailed API documentation.

## Core
POST /patients/
POST /studies/
POST /templates/{id}/publish/
GET /studies/{id}/report/
POST /reports/{id}/finalize/
