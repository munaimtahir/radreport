# Current UI Workflows

## Primary (desk-based) workflow
This appears to be the **intended** flow because it matches the “3-desk workflow” referenced in docs and has dedicated screens in the navigation.

1. **Registration Desk** (`/registration`)
   - Searches or creates a patient, selects a **workflow service** (from `ServiceCatalog`), takes payment, creates a `ServiceVisit` + `Invoice` + `Payment`.

2. **Performance Desk**
   - **USG Worklist** (`/worklists/usg`) edits findings and impression for a USG report and submits for verification.
   - **OPD Vitals** (`/worklists/opd-vitals`) captures vitals and moves the visit to IN_PROGRESS (server-side).
   - **Consultant** (`/worklists/consultant`) captures OPD consult, generates a prescription PDF, and publishes the visit immediately.

3. **Verification Desk** (`/worklists/verification`)
   - Reviews USG reports and either publishes or returns for correction, with PDF output stored in `media/pdfs/reports/usg/...`.

4. **Final Reports** (`/reports`)
   - Lists published USG reports and OPD prescriptions and opens PDF URLs if available.

## Legacy (study/report) workflow
This appears to be an **older flow** that still exists in the UI and backend.

1. **Front Desk Intake** (`/intake`)
   - Creates a `Visit` with `OrderItem` rows and auto-creates `Study` records for radiology services (via unified intake).

2. **Studies** (`/studies`) + **Report Editor** (`/reports/:reportId/edit`)
   - Studies are created against `catalog.Service` and optionally link to a `Report` if one already exists. There is no visible UI action to create a report for a study. **Needs verification** how reports are created in this flow.

3. **Templates** (`/templates`)
   - Manages template builder entities for the legacy reporting flow (Template → TemplateVersion schema).

4. **Receipt Settings** (`/receipt-settings`)
   - Controls receipt branding for the legacy `Visit` receipt PDF, not the workflow receipt PDF. **Needs verification** which receipt layout is used in production.

## Duplicates and mismatches
- **Two registration paths**:
  - `/registration` (workflow ServiceVisit) vs `/intake` (Visit/OrderItem/Study). These create different records and do not converge later.
- **Two service catalogs**: workflow uses `ServiceCatalog`, legacy uses `catalog.Service`. This makes service prices and names diverge if both are used.
- **USG status filtering**: UI requests `status=REGISTERED,RETURNED_FOR_CORRECTION` but backend expects a single status value; this can hide returned items. **Needs verification**.

## Intended flow vs remnants
- **Intended (likely)**: the desk-based workflow (`/registration`, worklists, verification, final reports) because it has matching backend models (`ServiceVisit`, `USGReport`, `OPDVitals`, `OPDConsult`) and explicit permissions for desks.
- **Remnants (legacy)**: the Visit/Study/Report flow (`/intake`, `/studies`, `/reports/:id/edit`) appears to be an older radiology workflow kept for reference or transition. **Needs verification** if still used in production.
