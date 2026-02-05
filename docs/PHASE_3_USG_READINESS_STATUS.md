# Phase 3 USG V2 Readiness Status

## Truth Map (Audit)

### V2 data model (present)
- `ReportTemplateV2`
- `ServiceReportTemplateV2`
- `ReportInstanceV2`
- `ReportPublishSnapshotV2`
- `ReportActionLogV2`
- `ReportBlockLibrary`

### V2 workitem/reporting endpoints (present)
- `schema`
- `values`
- `save`
- `submit`
- `generate-narrative`
- `report-pdf`
- `verify`
- `publish`
- `publish-history`
- `published-pdf`
- `published-integrity`

### Legacy remnants found and fixed
- Legacy seeding in `backend/seed_data.py` called `seed_reporting` (V1) → replaced with `seed_reporting_v2`.
- Legacy management commands referencing removed V1 models existed and were removed:
  - `seed_reporting`
  - `seed_usg_abd_profile`
  - `import_reporting_profiles`
  - `export_reporting_profiles`
  - `export_published_reports`
- Frontend now resolves missing-template backend errors to a clear user message: `No active template configured for this service`.

### Seed files audit
- `seed_data/templates_v2/*.json` contained many placeholder files.
- Added production-ready active USG templates for this phase:
  - `USG_ABD_V1`
  - `USG_KUB_V1`
  - `USG_PELVIS_V1`
- `service_template_map.csv` was minimal and now includes explicit active mappings for Abdomen/KUB/Pelvis only.

## What changed for Phase 3 completion
- `import_templates_v2` now works with **no args** and uses default seed paths.
- Import supports template directory ingestion and idempotent updates by `code`.
- Mapping supports service lookup by `service_code`, then `service_slug` (normalized), then `service_name` (normalized).
- `--dry-run` is transactional and non-writing.
- Unresolved services are reported with close name suggestions.

## Activated USG services now
- USG Abdomen
- USG KUB
- USG Pelvis

## Deferred services
- Doppler USG services (all)
- Procedures/interventions (pleural/ascitic tap, drainage, etc.)
- OB / anomaly templates
- Non-core non-doppler USG (to be phased later): Abdomen+Pelvis, Soft Tissue, Swelling, Breast/B/L Breast, Chest, Scrotal, Cranial, Knee Joint, Both Hip Joints Child

## Seed + verify commands
```bash
python manage.py import_templates_v2 --dry-run
python manage.py import_templates_v2
pytest backend/apps/reporting/tests/test_v2_import.py backend/apps/reporting/tests/test_workitem_v2_minimal_flow.py
cd frontend && npm test -- --run src/utils/reporting/__tests__/errors.test.ts
```
