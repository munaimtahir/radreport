# Phase 3: V2 Reporting Cutover

## What was deleted (legacy reporting summary)
- Removed the legacy V1 reporting models, serializers, views, and management commands (profiles, parameters, service-profile mapping, narrative v1, and v1 PDF generation).
- Removed legacy reporting routes and frontend screens tied to V1 template governance, parameter editing, baseline packs, and service-profile CSV tooling.
- Dropped legacy reporting tables via a dedicated migration.

## What replaced it (V2 system overview)
- V2 JSON-schema templates (`ReportTemplateV2`) are the sole source of truth.
- Service-to-template mappings use `ServiceReportTemplateV2` with default/active flags.
- Report instances are stored as `ReportInstanceV2` with schema-driven `values_json` and `narrative_json`.
- Narrative generation uses the V2 rules engine and V2 PDF generation pipeline.

## How to import templates
```bash
python manage.py import_templates_v2 --dry-run
python manage.py import_templates_v2
```

## Quick verification (minimal smoke checks)
1. List templates:
   ```bash
   curl -H "Authorization: Bearer <token>" http://localhost:8000/api/reporting/templates-v2/
   ```
2. Fetch V2 schema for a work item:
   ```bash
   curl -H "Authorization: Bearer <token>" http://localhost:8000/api/reporting/workitems/<service_visit_item_id>/schema/
   ```

## Updating service-template mappings
- Update `backend/apps/reporting/seed_data/templates_v2/service_template_map.csv`.
- Use `service_code` (preferred), or add optional `service_slug`/`service_name` columns if needed for matching.
- Re-run `python manage.py import_templates_v2` to apply changes.
