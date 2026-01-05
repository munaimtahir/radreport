# AGENT.md — Goals & Constraints

## Mission
Build an independent **RIMS** that can later merge into LIMS easily by:
- Keeping **app boundaries** aligned (patients/orders/reports/audit/billing concept)
- Using **UUIDs** for core entities
- Using **template versioning** and report schema snapshots
- Avoiding modality-specific assumptions inside patient/order primitives

## Non-negotiables
- Report templates are defined via a **Template Builder**:
  - Field types: short text, number, dropdown, checklist, paragraph, boolean
  - Sections are ordered; template versions are immutable once used in final reports
- Study workflow statuses:
  - Registered → In Progress → Draft → Final → Delivered
- Finalization locks the report and generates a PDF artifact

## Tech
- Django 5 + DRF + Postgres
- JWT auth (SimpleJWT)
- drf-spectacular for OpenAPI docs
- React TS Vite frontend

## Deliverables (definition of done for MVP)
1) Patient registration + search
2) Services catalog (USG/XRAY/CT + named services)
3) Study creation + worklist + status transitions
4) Template Builder CRUD + publish version
5) Reporting UI that renders a form from template schema + saves values JSON
6) Finalize generates PDF and stores it (even if basic first)
7) Audit trail for create/update/finalize actions
