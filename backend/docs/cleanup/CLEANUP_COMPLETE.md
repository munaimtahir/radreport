# Cleanup Complete

## Deletions
- **Backend Apps**: `apps.templates`, `apps.usg`, `apps.reporting` deleted.
- **Frontend Views**: 
    - `ReportTemplates.tsx`
    - `ServiceTemplates.tsx`
    - `Templates.tsx`
    - `TemplateImportManager.tsx`
    - `USGWorklistPage.tsx`
    - `VerificationWorklistPage.tsx`
    - `FinalReportsPage.tsx`
    - `UsgVisitDetailPage.tsx`
    - `UsgStudyEditorPage.tsx` (and related components)
    - `Studies.tsx` (Legacy)

## Modifications
- **Project Structure**:
    - `apps.workflow.pdf_engine` created to house receipt generation logic (migrated from billing/reporting).
    - `apps.catalog.models.Service`: Removed `default_template`.
    - `apps.workflow.models.USGReport`: Removed `template_version`.
    - `rims_backend.urls`: Removed routes for deleted apps.
    - `apps.workflow.api`: Removed `USGReportViewSet` (template driven reporting API).
    - `App.tsx`: Removed routes and navigation for deleted features.

## Database State
- Migrations for `catalog` and `workflow` (field removals) applied/faked.
- Migrations for `templates`, `usg`, `reporting` deletions faked (tables should be dropped manually if reusing DB, or ignored if starting fresh). Since this was a surgical purge on strict constraints, faking was necessary.

## Remaining Functionality
- **Patient Registration**: Preserved (`apps.patients`, `apps.studies`, `apps.workflow` registration flows).
- **Billing/Receipts**: Preserved (`apps.workflow` invoicing, `apps.workflow.pdf_engine`).
- **Consultants**: Preserved (`apps.consultants`).
- **Dashboard**: Preserved.

This state represents a "Clean Slate" for the USG reporting module, with all legacy and complex template systems removed.
