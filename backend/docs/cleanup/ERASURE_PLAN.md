# Erasure Plan

## Phase 0: Inventory

### Backend Apps Analysis
- **`apps.templates`**: Contains the core "Template" system (`Template`, `TemplateVersion`, etc.) and the "Report Template" system (`ReportTemplate`, etc.). **ACTION: DELETE ENTIRE APP.**
- **`apps.usg`**: Contains the "USG" specific template system (`UsgTemplate`, `UsgStudy`, etc.). **ACTION: DELETE ENTIRE APP.**
- **`apps.reporting`**: Contains `Report` (linked to `TemplateVersion`) and `ReportTemplateReport` (linked to `ReportTemplate`). **ACTION: DELETE ENTIRE APP.**
- **`apps.catalog`**: `Service` model has `default_template` FK to `apps.templates.Template`. **ACTION: MODIFY MODEL (Remove FK).**
- **`apps.workflow`**: `USGReport` model has `template_version` FK to `apps.templates.TemplateVersion`. **ACTION: MODIFY MODEL (Remove FK).**

### Frontend Analysis
- **Views to Delete**:
  - `src/views/ReportTemplates.tsx`
  - `src/views/ServiceTemplates.tsx`
  - `src/views/USGWorklistPage.tsx` (Likely deeply tied to `UsgStudy` or `apps.usg`, review before delete. If it uses `UsgStudy` (from `apps.usg`), it must go or be refactored.)
- **Routes**:
  - Delete routes pointing to above views in `src/ui/App.tsx`.

## Phase A: Backend Purge

1.  **`settings.py`**: Remove `apps.templates`, `apps.usg`, `apps.reporting` from `INSTALLED_APPS`.
2.  **`apps.catalog.models.Service`**: Remove `default_template` field.
3.  **`apps.workflow.models.USGReport`**: Remove `template_version` field.
4.  **Delete Directories**:
    - `backend/apps/templates/`
    - `backend/apps/usg/`
    - `backend/apps/reporting/`
5.  **Migrations**:
    - Create `makemigrations catalog` (to remove FK).
    - Create `makemigrations workflow` (to remove FK).
    - Delete migration files for `templates`, `usg`, `reporting`? No, standard django practice for app deletion implies removing the app and its tables. Since we are doing a "Surgical Cleanup", we can just let Django manage the state or manually cleanup.
    - *Strategy*: Since we are removing the apps, `makemigrations` won't detect deletions of those apps' models if the app is removed from settings.
    - *Correct Strategy for App Deletion*:
        1. Keep app in settings.
        2. Delete models code (or comment out).
        3. `makemigrations` (generates `DeleteModel` operations).
        4. Apply migrate.
        5. Remove app from settings.
        6. Delete app folder.
    - I will follow the "Correct Strategy" for clean DB state.

## Phase B: Frontend Purge

1.  Delete identified `.tsx` files.
2.  Update `App.tsx`.
3.  Fix dead imports (search `from ...` or `import ...`).

## Phase C: Verification

1.  `python manage.py check`
2.  `python manage.py makemigrations --check`
3.  `npm run build`
4.  Smoke test registration.
