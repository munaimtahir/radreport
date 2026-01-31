# Radiology Template Standardization Report

Date: 2026-01-31
Repo: /home/munaim/Documents/github/radreport
Scope: Template-only narrative standardization + verification harness + legacy template tracing removal/neutralization

## Admin Catalog & Templates Module

A new Admin UI module has been implemented to manage Report Profiles, Report Parameters, Services, and Service-Template Linkages. This module includes CRUD operations and robust CSV import/export functionalities with dry-run validation.

### Endpoints:

*   **Report Profiles (`reporting-profiles`)**:
    *   `GET /api/reporting/profiles/template-csv/`: Download CSV template for report profiles.
    *   `GET /api/reporting/profiles/export-csv/`: Export report profiles to CSV.
    *   `POST /api/reporting/profiles/import-csv/`: Import report profiles from CSV (supports `?dry_run=true/false`).
    *   `POST /api/reporting/profiles/{pk}/import-parameters/`: Import parameters for a specific report profile (supports `?dry_run=true/false`).
*   **Report Parameters (`reporting-parameters`)**:
    *   `GET /api/reporting/parameters/template-csv/`: Download CSV template for report parameters.
    *   `GET /api/reporting/parameters/export-csv/`: Export report parameters to CSV.
    *   `POST /api/reporting/parameters/import-csv/`: Import report parameters from CSV (supports `?dry_run=true/false`).
*   **Services (`services`)**:
    *   `GET /api/services/template-csv/`: Download CSV template for services.
    *   `GET /api/services/export-csv/`: Export services to CSV.
    *   `POST /api/services/import-csv/`: Import services from CSV (supports `?dry_run=true/false`).
*   **Service-Template Linkages (`reporting-service-profiles`)**:
    *   `GET /api/reporting/service-profiles/template-csv/`: Download CSV template for service-template linkages.
    *   `GET /api/reporting/service-profiles/export-csv/`: Export service-template linkages to CSV.
    *   `POST /api/reporting/service-profiles/import-csv/`: Import service-template linkages from CSV (supports `?dry_run=true/false`).

### Import Rules:

*   **Profiles**: Upsert by `code`.
*   **Parameters**: Upsert by (`profile_code`, `slug`).
*   **Services**: Upsert by `code`.
*   **Linkage**: Upsert by (`service_code`, `profile_code`).
*   **Validation**: Rejects unknown `profile_code`/`service_code` during apply. Provides row-level error list and counts (created/updated/skipped/errors).
*   **Safety**: Uses `transaction.atomic()` for apply operations and includes a `dry_run` option for validation without database writes.

## Narrative Engine Ground Truth
- Engine implementation: `backend/apps/reporting/services/narrative_v1.py` (`generate_report_narrative`).
- Primary call sites:
  - `backend/apps/reporting/views.py`:
    - `ReportWorkItemViewSet.generate_narrative` (`POST /api/reporting/workitems/{id}/generate-narrative/`) generates + persists narrative.
    - `ReportWorkItemViewSet.narrative` (`GET /api/reporting/workitems/{id}/narrative/`) returns persisted narrative.
    - `ReportWorkItemViewSet.report_pdf` (`GET /api/reporting/workitems/{id}/report-pdf/`) auto-generates narrative if missing prior to PDF.
- Persistence path:
  - `backend/apps/reporting/models.py` → `ReportInstance` fields: `findings_text`, `impression_text`, `limitations_text`, `narrative_version`, `narrative_updated_at`.

## Phase A: Narrative Trace + Legacy Trace
### A1: Narrative Trace Evidence
- Trace log: `/tmp/rad_audit/logs/narrative_trace.txt`.
- Engine file: `backend/apps/reporting/services/narrative_v1.py`.
- Service call chain and API endpoints captured above.

### A2: Legacy Trace Map (Templates / presets / old loaders)
Source log: `/tmp/rad_audit/logs/legacy_trace.txt`

| Path | Purpose (best-effort) | Runtime referenced? | Action |
|---|---|---|---|
| `backend/load_production_data.py` | Legacy template loader (apps.templates) + preset JSON import | No call sites found | REMOVE (deleted) |
| `backend/audit_services.py` | Legacy audit using apps.templates | No call sites found | REMOVE (deleted) |
| `backend/fix_services.py` | Legacy fix script using apps.templates | No call sites found | REMOVE (deleted) |
| `backend/test_workflow.py` | Legacy workflow test referencing apps.templates | No call sites found | REMOVE (deleted) |
| `backend/apps/workflow/management/commands/seed_smoke_phase1.py` | Legacy smoke seed using apps.templates | No runtime call sites | REMOVE (deleted) |
| `backend/test_service_flow.py` | Legacy script test importing removed Report model | Picked up by test runner | REMOVE (deleted) |
| `docs/presets/templates/*` + `backend/docs/presets/templates/*` | Documentation preset JSONs | Docs only | KEEP (doc-only, no runtime refs) |
| `docs/_archive/legacy_templates/**` | Archived legacy template system docs | Docs only | KEEP (archive) |

## Phase B: Template Import/Export Evidence (USG Abdomen)
- Commands run (Docker dev container):
  - Export before: `manage.py export_reporting_profiles --profile USG_ABD --out /tmp/rad_audit/exports/usg_abd_before.csv`
  - Import dry-run: `manage.py import_reporting_profiles --file PHASE1_USG_ABD_template.csv --mode dry_run`
  - Import apply: `manage.py import_reporting_profiles --file PHASE1_USG_ABD_template.csv --mode apply`
  - Export after: `manage.py export_reporting_profiles --profile USG_ABD --out /tmp/rad_audit/exports/usg_abd_after.csv`
- Results:
  - `USG_ABD` profile not found pre/post: `/tmp/rad_audit/logs/export_usg_before.log`, `/tmp/rad_audit/logs/export_usg_after.log`.
  - CSV file not found: `/tmp/rad_audit/logs/import_dryrun.log`, `/tmp/rad_audit/logs/import_apply.log`.
  - Diff artifacts not generated because exports are missing: `/tmp/rad_audit/diffs/usg_abd_diff.patch` contains errors.

## Phase C: Golden Cases + Snapshot Harness
- Snapshot tests added:
  - `backend/apps/reporting/tests/test_narrative_snapshots.py`
  - Snapshots: `backend/apps/reporting/tests/snapshots/case_01.txt` … `case_10.txt`.
- Golden payloads (JSON) stored at:
  - `/tmp/rad_audit/snapshots/usg_abd_case_01_payload.json` … `usg_abd_case_10_payload.json`.
- Summary:
  - 10 narrative golden cases covering omission rules, boolean behavior, dropdown label mapping, checklist joins, impression/limitations roles.

## Phase D: API End-to-End Verification (3 cases)
- Integration test: `backend/apps/reporting/tests/test_api_narrative.py`.
- Verified flow for 3 cases:
  1) Save values → Generate narrative → Fetch narrative
  2) Exact snapshot match
- Logs:
  - `/tmp/rad_audit/logs/api_case_01.log`
  - `/tmp/rad_audit/logs/api_case_02.log`
  - `/tmp/rad_audit/logs/api_case_03.log`

## Phase E: Legacy Template Tracing Removal
- Removed unused legacy scripts referencing `apps.templates`:
  - `backend/load_production_data.py`
  - `backend/audit_services.py`
  - `backend/fix_services.py`
  - `backend/test_workflow.py`
  - `backend/apps/workflow/management/commands/seed_smoke_phase1.py`
  - `backend/test_service_flow.py` (legacy test script breaking test discovery)
- No deterministic narrative engine logic changed.

## Tests + Logs
- `manage.py test apps.reporting.tests.test_narrative_snapshots`: PASS. Log: `/tmp/rad_audit/logs/django_tests.log`.
- `manage.py test apps.reporting.tests.test_api_narrative` (with `/tmp` bind): PASS. Log: `/tmp/rad_audit/logs/django_tests.log`.
- `pytest -q`: FAILED (pytest not installed). Log: `/tmp/rad_audit/logs/pytest.log`.

## What Changed vs. Not Changed
- Changed:
  - Added deterministic snapshot verification harness (tests + snapshots).
  - Added API verification test for narrative endpoints.
  - Removed unused legacy template loaders/scripts referencing `apps.templates`.
- Not Changed:
  - Deterministic narrative engine logic (`backend/apps/reporting/services/narrative_v1.py`) unchanged.
  - No AI narrative generation added.

## Remaining Risks / Deferred Items
- `PHASE1_USG_ABD_template.csv` not present in repo → template import/export and diff cannot be completed.
- `USG_ABD` profile not present in DB seed → export before/after unavailable.
- `pytest` not installed in container.

## Artifact Listing
```
/tmp/rad_audit/diffs/code_changes.patch
/tmp/rad_audit/logs/api_case_01.log
/tmp/rad_audit/logs/api_case_02.log
/tmp/rad_audit/logs/api_case_03.log
/tmp/rad_audit/logs/artifacts.txt
/tmp/rad_audit/logs/django_check.txt
/tmp/rad_audit/logs/django_tests.log
/tmp/rad_audit/logs/docker_pull.log
/tmp/rad_audit/logs/env_candidates.txt
/tmp/rad_audit/logs/export_after.log
/tmp/rad_audit/logs/export_before.log
/tmp/rad_audit/logs/export_usg_after.log
/tmp/rad_audit/logs/export_usg_before.log
/tmp/rad_audit/logs/git_head_before.txt
/tmp/rad_audit/logs/git_status_before.txt
/tmp/rad_audit/logs/import_apply.log
/tmp/rad_audit/logs/import_dryrun.log
/tmp/rad_audit/logs/legacy_trace.txt
/tmp/rad_audit/logs/narrative_trace.txt
/tmp/rad_audit/logs/pytest.log
/tmp/rad_audit/logs/sample_data_files.txt
/tmp/rad_audit/logs/template_dirs.txt
/tmp/rad_audit/snapshots/usg_abd_case_01_payload.json
/tmp/rad_audit/snapshots/usg_abd_case_02_payload.json
/tmp/rad_audit/snapshots/usg_abd_case_03_payload.json
/tmp/rad_audit/snapshots/usg_abd_case_04_payload.json
/tmp/rad_audit/snapshots/usg_abd_case_05_payload.json
/tmp/rad_audit/snapshots/usg_abd_case_06_payload.json
/tmp/rad_audit/snapshots/usg_abd_case_07_payload.json
/tmp/rad_audit/snapshots/usg_abd_case_08_payload.json
/tmp/rad_audit/snapshots/usg_abd_case_09_payload.json
/tmp/rad_audit/snapshots/usg_abd_case_10_payload.json
```