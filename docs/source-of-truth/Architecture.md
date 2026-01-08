# Architecture.md

## Recommended v1 Architecture
- **Backend:** Django + Django REST Framework (or existing backend if already chosen)
- **DB:** PostgreSQL
- **Frontend:** React (or existing frontend), minimal pages aligned to workflows
- **Reverse Proxy:** Caddy (production)
- **PDF/Print:** ReportLab (server-side PDF generation) OR HTML-to-PDF only if proven stable

## Key Design Principles
1. **Worklist-driven UI**
   - Reception creates Visit + services
   - Each service appears in its department worklist
2. **Immutable financial snapshots**
   - service name/rate snapshot stored at time of billing
3. **State machine + audit log**
   - no “magic” status changes
4. **Document versions**
   - receipt/report/prescription versioned for reprint accountability

## Deployment Notes
- Bind backend services to **127.0.0.1**
- Only Caddy is public-facing
- Static frontend can be served directly by Caddy (preferred)
- Docker compose parity between local and VPS

## Suggested Modules (Backend)
- accounts (users, roles)
- patients (Patient model, search)
- visits (Visit, VisitService, statuses)
- catalog (ServiceCatalog)
- billing (Payment, Receipt)
- usg (templates, draft, verification, publish)
- opd (vitals, prescription, publish)
- documents (PDF generation, version logs)
- audit (immutable logs)
