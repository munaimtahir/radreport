# ReportLab Migration Summary

## Overview
Complete migration from WeasyPrint to ReportLab for all PDF generation in RIMS. This ensures deterministic, print-safe PDF output across all environments.

## Changes Made

### 1. PDF Engine Module (`backend/apps/reporting/pdf_engine/`)
Created new modular PDF engine:
- **base.py**: Common styles, page templates, header/footer utilities
- **receipt.py**: Receipt PDF generation (Visit and ServiceVisit models)
- **clinical_report.py**: USG reports and diagnostic reports
- **prescription.py**: OPD prescriptions

### 2. Code Replacements
- `backend/apps/reporting/pdf.py`:
  - `build_receipt_pdf()` → Uses `build_receipt_pdf_reportlab()`
  - `build_basic_pdf()` → Uses `build_basic_report_pdf()`
  
- `backend/apps/workflow/pdf.py`:
  - `build_service_visit_receipt_pdf()` → Uses `build_service_visit_receipt_pdf_reportlab()`
  - `build_usg_report_pdf()` → Uses `build_clinical_report_pdf()`
  - `build_opd_prescription_pdf()` → Uses `build_prescription_pdf()`

### 3. Dependencies
- **Removed**: `weasyprint>=62.0` from `requirements.txt`
- **Kept**: `reportlab>=4.0` (already present)
- **Dockerfile**: Removed WeasyPrint OS dependencies (cairo, pango, etc.)
  - Now only requires: `postgresql-client`, `libpq5`

### 4. Smoke Tests
- **scripts/smoke_pdf.py**: Tests all PDF generation functions
  - Validates PDF header (`%PDF`)
  - Checks file size
  - Tests: receipts, reports, prescriptions
  
- **scripts/smoke_workflow.py**: End-to-end workflow tests
  - Creates test patients and visits
  - Tests workflow progression
  - Validates PDF generation at each stage

- **Removed**: `scripts/smoke_pdf_selftest.py` (WeasyPrint-specific)

### 5. Documentation
- **DEPLOYMENT.md**: Updated with:
  - ReportLab PDF architecture section
  - Updated smoke test instructions
  - Git pull strategy (rebase)
  - PDF troubleshooting guide

## PDF Output Specifications
- **Page Size**: A4 (595 × 842 points)
- **Format**: Deterministic, print-safe
- **Header**: Institution name/logo (if configured)
- **Footer**: Page numbers, disclaimer
- **Validation**: All PDFs must start with `%PDF` header

## Testing
Run smoke tests:
```bash
# Inside backend container
docker compose exec backend python scripts/smoke_pdf.py
docker compose exec backend python scripts/smoke_workflow.py

# From host
RIMS_HOST=rims.alshifalab.pk bash scripts/smoke_api.sh
```

## Deployment Steps
1. Pull latest code (with rebase strategy)
2. Rebuild backend container:
   ```bash
   docker compose build --no-cache backend
   docker compose up -d
   ```
3. Run smoke tests to verify PDF generation
4. Monitor for any PDF-related errors

## Benefits
- ✅ No external dependencies (cairo, pango, etc.)
- ✅ Deterministic output (no layout drift)
- ✅ Smaller Docker image
- ✅ Faster PDF generation
- ✅ Print-safe formatting
- ✅ Identical output across environments

## Validation
- Domain: `rims.alshifalab.pk`
- IP: `34.124.150.231`
- All PDF endpoints tested and verified
