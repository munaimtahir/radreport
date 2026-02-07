# Repository Debloat Log

## Deleted Files/Directories
- `backend/apps/reporting/pdf_engine/report_pdf.py` (V1 PDF Engine)
- `backend/apps/reporting/printing_api.py` (V1 Printing API)
- `baseline_packs/` (Root Legacy V1 Baseline Packs)
- `backend/baseline_packs_v2/` (Redundant V2 baseline packs, canonical is now `seed_data/templates_v2`)
- `backend/smoke_test.py` (Temporary testing script)

## Rationale
- Removing broken imports (V1 remnants) to pass Gate 0.
- Debloating unused code and duplicate seeding data.
- Establishing single source of truth for V2 Templates (`backend/apps/reporting/seed_data/templates_v2`).

## Updated files
- `backend/apps/reporting/management/commands/seed_reporting_v2.py`: Use correct command names and dry-run support.
- `backend/apps/reporting/management/commands/import_block_library.py`: Support for list payloads and code injection for idempotency.
- `backend/apps/reporting/tests/test_block_library_import.py`: Updated to use correct command name.
- `backend/apps/reporting/tests/test_workitem_v2_publish_pdf.py`: Fixed status precondition for publish tests.

## Notes
- `.gitignore` already covered `backend/media/` and `*.pdf`.
- Cleaned up manual testing artifacts.
