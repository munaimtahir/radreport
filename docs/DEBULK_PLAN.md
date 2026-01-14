# Debulk Plan (No Implementation)

## Step 1 — Confirm the primary workflow
**Goal:** Decide which flow is authoritative (desk-based workflow vs legacy Visit/Study flow).
- Review active endpoints in use (frontend calls in `frontend/src/views/*`).
- Confirm with stakeholders which screens are still used.

**Test after step:**
- Login → Registration → create a ServiceVisit.
- USG worklist → save draft → submit for verification.
- Verification → publish and open PDF.

## Step 2 — Consolidate service masters
**Goal:** Choose one source of truth for services.
- If workflow is primary, map `workflow.ServiceCatalog` to `catalog.Service` or migrate data into one model.
- If legacy is primary, redirect workflow UI to use `catalog.Service` and remove `ServiceCatalog`.

**Test after step:**
- Service list loads in the registration screen.
- New visit creation uses the chosen service model.
- Pricing totals match expected values.

## Step 3 — Consolidate intake
**Goal:** Remove one of the duplicate intake systems.
- Either:
  - Retire `/intake` and unify everything into `ServiceVisit` + workflow desks, **or**
  - Retire `/registration` and use unified intake + studies as primary.

**Test after step:**
- Intake screen creates the correct records (Visit/OrderItem/Study **or** ServiceVisit).
- Downstream workflow pages show the newly created record.

## Step 4 — Consolidate reporting
**Goal:** Use a single report and PDF pipeline.
- If workflow is primary, remove legacy report editor screens and keep workflow PDF templates.
- If legacy is primary, ensure report creation is accessible in UI and deprecate workflow USG/OPD reports.

**Test after step:**
- One report can be created, edited, finalized, and downloaded from the UI.
- No orphaned PDFs or missing report links.

## Step 5 — Clean up routes and permissions
**Goal:** Remove unused routes and ensure desk permissions match reality.
- Remove unused API endpoints and UI routes marked “candidate for removal.”
- Re-enable desk role enforcement if required.

**Test after step:**
- Role-based access works (Registration/Performance/Verification).
- Unused pages/routes are no longer accessible.

## Final verification checklist
- [ ] Only one intake workflow exists in UI and backend.
- [ ] Only one service master is used across UI and APIs.
- [ ] Report creation + PDF generation works end-to-end for one workflow.
- [ ] Final reports list only uses the chosen reporting pipeline.
- [ ] No duplicate receipt generation paths remain.
- [ ] All critical screens load without console or API errors.
