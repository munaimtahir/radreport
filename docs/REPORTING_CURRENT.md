# Reporting — Current State

## Report template locations
- **Database-driven templates** (legacy reporting flow):
  - Models: `Template`, `TemplateSection`, `TemplateField`, `FieldOption`, `TemplateVersion` in `backend/apps/templates/models.py`.
  - Versions store a frozen JSON schema snapshot in `TemplateVersion.schema`.
- **Workflow PDFs (HTML templates):**
  - USG report: `backend/apps/workflow/templates/workflow/usg_report.html`.
  - OPD prescription: `backend/apps/workflow/templates/workflow/opd_prescription.html`.
  - Workflow receipt: `backend/apps/workflow/templates/workflow/receipt.html`.
- **Visit receipt templates (legacy):**
  - `backend/apps/studies/templates/receipts/receipt_a4_dual.html` and `receipt_single.html`.

## Data mapping and rendering pipeline
### Legacy report pipeline (Study → Report)
1. A `Study` is created against a `catalog.Service`.
2. A `Report` is created with a `TemplateVersion` (schema snapshot).
3. The report editor renders fields from `TemplateVersion.schema.sections` and saves values in `Report.values`.
4. Finalization (`/reports/:id/finalize/`) generates a PDF using `build_basic_pdf` (ReportLab) and stores it in `Report.pdf_file`.

### Workflow pipeline (ServiceVisit → USG/OPD)
1. A `ServiceVisit` is created for a workflow service (`ServiceCatalog`).
2. USG worklist writes `USGReport.report_json` and submits for verification.
3. Verification desk publishes, generating a PDF with WeasyPrint and storing the path in `USGReport.published_pdf_path`.
4. OPD consult writes `OPDConsult` data and uses `save_and_print` to generate a prescription PDF (WeasyPrint), stored in `OPDConsult.published_pdf_path`.

## PDF generation engines
- **ReportLab:** `apps.reporting.pdf.build_basic_pdf` (basic radiology report PDF).
- **WeasyPrint:**
  - `apps.reporting.pdf.build_receipt_pdf` (visit receipt).
  - `apps.workflow.pdf.build_service_visit_receipt_pdf` (workflow receipt).
  - `apps.workflow.pdf.build_usg_report_pdf` (USG report).
  - `apps.workflow.pdf.build_opd_prescription_pdf` (OPD prescription).

## What is required for “one report works end-to-end”
**Legacy flow (Study → Report PDF)**
1. A `Template` and published `TemplateVersion` must exist.
2. A `Study` record must exist and be linked to a report (manual or via API).
3. The report is edited and saved (values/narrative/impression).
4. Finalize the report to generate and store a PDF.

**Workflow flow (USG/OPD → PDF)**
1. A `ServiceCatalog` entry exists (USG/OPD).
2. A `ServiceVisit` is created in Registration.
3. Performance desk completes USG report or OPD consult data.
4. Verification (USG) or save-and-print (OPD) generates and stores the PDF.

## Known gaps / risks
- The legacy UI does not appear to create a Report for a Study, only edit if it already exists. **Needs verification**.
- There are multiple receipt systems (Visit receipt vs workflow receipt), with different templates and storage paths. **Needs verification** which one is used in production.
