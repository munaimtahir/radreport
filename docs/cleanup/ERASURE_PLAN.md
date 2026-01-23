# Erasure Plan

## Backend Erasure

### Apps to Delete (Complete Removal)
1. `apps.usg`
   - Models: `UsgTemplate`, `UsgServiceProfile`, `UsgStudy`, `UsgFieldValue`, `UsgPublishedSnapshot`
   - Views: `UsgTemplateViewSet`, `UsgServiceProfileViewSet`, `UsgStudyViewSet`, `UsgPublishedSnapshotViewSet`
   - Reason: "USG template models/features" target.

2. `apps.templates`
   - Models: `Template`, `TemplateVersion`, `TemplateSection`, `TemplateField`, `FieldOption`, `ReportTemplate`, `ReportTemplateField`, `ReportTemplateFieldOption`, `ServiceReportTemplate`
   - Views: `TemplateViewSet`, `TemplateVersionViewSet`, `ReportTemplateViewSet`, `TemplatePackageViewSet`
   - Reason: "Report template models/features" target.

3. `apps.reporting`
   - Models: `Report`, `ReportTemplateReport`
   - Views: `ReportViewSet`, `ReportingViewSet`
   - Reason: Strictly tied to template based reporting.

### Apps to Clean
1. `apps.workflow`
   - DELETE Class: `USGReport` (The "current" USG implementation).
   - PRESERVE: `ServiceVisit`, `ServiceVisitItem`, `Invoice`, `Payment`, `ReceiptSnapshot` (Core business logic/Billing provided by patient registration?). Note: User said "Do NOT break patient registration". `ServiceVisit` interacts with registration.
   - PRESERVE: `OPDVitals`, `OPDConsult` (Unless user wants them gone, but instructions specify USG/Reports).
   - CHECK: `ServiceVisit` derives status from `ServiceVisitItem`. `ServiceVisitItem` has status. If `USGReport` is deleted, `ServiceVisitItem` remains but won't have a report linked. This is acceptable (item exists, no report).

2. `apps.catalog`
   - MODEL: `Service`
   - REMOVE FIELD: `default_template` (ForeignKey to `templates.Template`).

3. `rims_backend/urls.py`
   - Remove routers for all deleted viewsets.

4. `rims_backend/settings.py`
   - Remove `apps.usg`, `apps.templates`, `apps.reporting` from `INSTALLED_APPS`.

## Frontend Erasure

### Pages/Views to Delete
1. `USGWorklistPage.tsx`
2. `UsgVisitDetailPage.tsx`
3. `UsgStudyEditorPage.tsx`
4. `VerificationWorklistPage.tsx`
5. `FinalReportsPage.tsx`
6. `ReportTemplates.tsx`
7. `ServiceTemplates.tsx`
8. `TemplateImportManager.tsx`
9. `Templates.tsx`
10. `ReportEditor.tsx`
11. `UsgVisitReportsTab.tsx`
12. `UsgPatientLookupPage.tsx`
13. `UsgPatientProfilePage.tsx`

### Routes to Remove in `App.tsx`
- `/worklists/usg`
- `/usg/visits/:visitId`
- `/usg/studies/:studyId`
- `/worklists/verification`
- `/reports`
- `/admin/report-templates`
- `/admin/service-templates`
- `/admin/templates/import`
- `/templates`
- `/reports/:reportId/edit`

### UI Components/Hooks
- Scan `src/api` for clients calling removed endpoints.
- Remove navigation links in `Shell` component (`App.tsx`).

## Migration Strategy
1. **Catalog/Workflow**: Generate migrations to remove ForeignKeys/Models (`default_template`, `USGReport`).
2. **Deleted Apps**: Remove apps from `INSTALLED_APPS`. Tables will become orphaned in production (acceptable per surgical cleanup norms, "fresh DB" will simply not create them).
3. **Verify**: `makemigrations` and `migrate` on fresh DB.
