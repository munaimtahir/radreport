# RADREPORT Phase 3 — USG Core (V2-only) Readiness

## Activated now (locked scope)
- `USG-ABD` → `USG_ABD_V1`
- `USG-KUB` → `USG_KUB_V1`
- `USG-PELVIS` → `USG_PELVIS_V1`

Activation source:
- `backend/apps/reporting/seed_data/templates_v2/activation/phase3_usg_core.csv`

## Merge-conflict resolution choices applied
To keep this branch auto-merge friendly with `main`, the following conflict-prone files were normalized to the Phase-3 V2-only path and reduced to one canonical implementation each:
- `seed_usg_basic_services.py`: kept Option-A code upsert implementation only.
- `seed_reporting_v2.py`: kept V2-only bootstrap calls (`import_block_library_v1`, `import_templates_v2`) only.
- `import_templates_v2.py`: kept no-arg defaults to library+activation Phase-3 locations and idempotent dry-run flow.
- `import_block_library_v1.py`: kept idempotent JSON block import logic only.
- USG template JSON files + activation CSV: kept the Phase-3 core mapping set only.
- `narrative_v2.py`: kept deterministic multi-rule impression evaluation path.
- `test_v2_import.py`: aligned to new default seed/activation locations and 3-service mapping assertion.

## Bootstrap path (V2 only)
- `backend/seed_data.py` now runs:
  1) `seed_usg_basic_services`
  2) `seed_reporting_v2`
- `seed_reporting_v2` runs:
  1) `import_block_library_v1`
  2) `import_templates_v2`

## Deferred (not activated in this phase)
- Doppler (all)
- OB/anomaly (all)
- Procedures/interventions (all)
- Other non-core USG templates

## Reproduce checks
```bash
cd backend && python manage.py test apps.reporting.tests.test_v2_import apps.reporting.tests.test_workitem_v2_minimal_flow -v 2
cd frontend && npm test -- --run src/utils/reporting/__tests__/errors.test.ts
cd backend && python manage.py import_templates_v2 --dry-run
```

## Environment note
- Docker CLI is unavailable in this runtime shell, so docker-compose based checks cannot be executed here.
