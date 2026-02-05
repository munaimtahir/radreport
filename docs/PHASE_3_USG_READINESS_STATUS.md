# Phase 3 USG V2 Readiness Status

## Activated (Option A codes)
- USG-ABD (USG Abdomen)
- USG-KUB (USG KUB)
- USG-PELVIS (USG Pelvis)

## Deferred (explicitly out of scope now)
- All Doppler (carotid, DVT, etc.)
- All OB/anomaly/prenatal templates
- Procedures/interventions (paracentesis, taps, drains)
- Remaining USG variants (abdomen+pelvis combined, soft tissue, breast, chest, scrotum, thyroid, etc.)

## Default commands (no-arg)
```
source backend/.venv/bin/activate
cd backend && python manage.py seed_reporting_v2
cd backend && python manage.py import_templates_v2 --dry-run
cd backend && python manage.py import_templates_v2
```
- `import_templates_v2` defaults:
  - templates: `backend/apps/reporting/seed_data/templates_v2/library/phase2_v1.1/`
  - mapping:   `backend/apps/reporting/seed_data/templates_v2/activation/phase3_usg_core.csv`
  - dry-run is fully transactional (no writes)
- `seed_reporting_v2` order: seeds USG services → block library → templates/mappings

## Library policy
- All template JSON live under `templates_v2/library/phase2_v1.1/`
- Activation mappings live under `templates_v2/activation/`
- Block library seeds live under `block_library/phase2_v1.1/` (one JSON per block)

## Narrative & UI notes
- V2-only enforcement: unmapped service returns `NO_ACTIVE_V2_TEMPLATE`; frontend shows friendly "No active template configured for this service".
- Narrative engine is deterministic, skips empty placeholders, and allows multiple rule hits.

## Verification (latest run)
- Backend: migrate, seed_reporting_v2, import_templates_v2 (dry + live), tests: `apps.reporting.tests.test_v2_import`, `apps.reporting.tests.test_workitem_v2_minimal_flow`, `apps.reporting.tests.test_block_library_import`
- Frontend: `npm test -- --run src/utils/reporting/__tests__/errors.test.ts`

## Notes
- Database for local dev: recreate if migration history conflicts with prior state (fresh sqlite used in verification run).
- Media root for tests: `/tmp/radreport-test-media` to allow PDF snapshot writes.
