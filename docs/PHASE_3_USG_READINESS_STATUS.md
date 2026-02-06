# RADREPORT Phase 3 — USG Core Readiness Status

## Activation scope (active now)
- `USG-ABD` → `USG_ABD_V1`
- `USG-KUB` → `USG_KUB_V1`
- `USG-PELVIS` → `USG_PELVIS_V1`

Activation file: `backend/apps/reporting/seed_data/templates_v2/activation/phase3_usg_core.csv`.

## Service code scheme
- Option A (locked) codes are implemented and seeded idempotently:
  - `USG-ABD` (`USG Abdomen`)
  - `USG-KUB` (`USG KUB`)
  - `USG-PELVIS` (`USG Pelvis`)

## What is active in bootstrap
- `seed_data.py` invokes:
  1. `seed_usg_basic_services`
  2. `seed_reporting_v2`
- `seed_reporting_v2` invokes:
  1. `import_block_library_v1`
  2. `import_templates_v2`

## Idempotent seed/import assets
- Template library (full-preserve location for this phase):
  - `backend/apps/reporting/seed_data/templates_v2/library/phase2_v1.1/`
- Activation set (only USG core active now):
  - `backend/apps/reporting/seed_data/templates_v2/activation/phase3_usg_core.csv`
- Block library seeds:
  - `backend/apps/reporting/seed_data/block_library/phase2_v1.1/block_library.json`

## Repro commands
```bash
# backend tests
cd backend && python manage.py test apps.reporting.tests.test_v2_import apps.reporting.tests.test_workitem_v2_minimal_flow -v 2

# frontend smoke
cd frontend && npm test -- --run src/utils/reporting/__tests__/errors.test.ts

# v2 import dry-run
cd backend && python manage.py import_templates_v2 --dry-run
```

## Deferred (explicitly not active in this phase)
- Doppler (all)
- OB / anomaly workflows (all)
- Procedures / interventions
- Other USG templates beyond core ABD/KUB/PELVIS activation:
  - Abdomen+pelvis variants, breast, scrotal, soft tissue / lump / swelling,
  - chest, cranial, pediatric hips/knee and all additional non-core scans.

## Current gate status in this environment
- Backend/Frontend automated checks for import + minimal V2 flow: **PASS**.
- Docker-based transcript commands cannot complete here because `docker` is unavailable in the runtime shell; command outputs are captured in transcript.
