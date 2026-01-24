# Decontamination Log
**Date:** January 25, 2026
**Performer:** Antigravity (Senior Repository Decontamination Engineer)

## Executive Summary
The repository has been surgically purged of all artifacts related to the legacy "ReportTemplate", "TemplateSchema", and "USG Template" systems. The system is now lean, containing only the implemented modules (Patients, Consultants, Catalog, Studies, Workflow, Audit).

## 1. Purged Artifacts (DELETED)
The following files and directories were confirmed stale/orphaned and permanently deleted:

### Directories
- `apps/` (Root level orphan containing legacy templates app)

### Backend Code
- `backend/apps/workflow/management/commands/verify_usg_template_resolution.py` (Legacy verification)
- `backend/apps/workflow/management/commands/smoke_prod_usg.py` (Legacy smoke test)
- `backend/apps/workflow/management/commands/backfill_usg_template_versions.py` (Legacy backfill)
- `backend/apps/workflow/test_publish_metadata.py` (Test relying on deleted models)
- `backend/verify_usg_template_resolution.py` (Duplicate root script)
- `backend/import_ultrasound_services.py` (Legacy importer)
- `backend/import_services_inline.py` (Legacy importer)
- `backend/verify_checklist.py` (Orphan script)

### Frontend Code
- `frontend/src/utils/normalizeTemplateSchema.ts` (Template utility)

### Scripts
- `import_templates.sh` (Root script)

## 2. Archived Artifacts
Ambiguous or potentially useful reference material was moved to `docs/_archive/legacy_templates/`:

- `docs/report-templates/`
- `template_guide/`
- `docs/04_template_builder.md`
- `docs/05_reporting_engine.md`
- `docs/usg_reporting.md`
- `USG_TEMPLATE_FIX.md`
- `FRONTEND_TEMPLATE_GUIDE.md`

## 3. Code Modifications (Surgical Edits)
- **`backend/apps/catalog/models.py`**: Removed commented-out reference to `default_template`.
- **`frontend/src/ui/App.tsx`**: Removed dead "Final Reports" navigation link pointing to non-existent route.

## 4. Verification Check
- **Backend**: `python manage.py check` PASSED. `python manage.py showmigrations` CLEAN.
- **Frontend**: `npm run build` SUCCEEDED (dist/ created).

The repository is now actively aligned with the `docs/TRUTH_MAP.md` specification.
