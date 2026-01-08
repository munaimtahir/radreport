# Repository Audit Report
**Phase A: Repository Audit**  
**Date:** 2026-01-07  
**Purpose:** Document current state, identify duplicates, conflicts, and classify modules

---

## Overview

The RIMS (Radiology Information Management System) repository contains **two parallel systems** operating simultaneously:

1. **Legacy System** (`apps/studies`, `apps/reporting`): Study-based workflow with template-driven reporting
2. **New Workflow System** (`apps/workflow`): ServiceVisit-based three-desk workflow (Registration → Performance → Verification)

Both systems share common models (`Patient`, `Service`/`ServiceCatalog`) but implement different workflows, creating significant duplication and confusion.

### Key Statistics
- **Backend Apps:** 7 (patients, catalog, templates, studies, reporting, workflow, audit)
- **Frontend Views:** 14 pages
- **Duplicate Concepts:** 3 major pairs
- **Workflow Systems:** 2 (legacy Study-based, new ServiceVisit-based)
- **Billing Systems:** 2 (Visit-based, Invoice/Payment-based)

---

## Folder-by-Folder Breakdown

### Root Directory
- **Documentation Bloat:** 30+ markdown files (README variants, completion reports, deployment guides)
- **Scripts:** Mix of deployment, testing, and data seeding scripts
- **Docker:** `docker-compose.yml` for local development

### `/backend`
**Purpose:** Django REST API backend

#### `/backend/apps/patients`
- **Models:** `Patient` (UUID primary key, MRN, patient_reg_no)
- **APIs:** CRUD operations, search by MRN/name/phone
- **Status:** ✅ KEEP - Single source of truth for patients
- **Notes:** Used by both legacy and new systems

#### `/backend/apps/catalog`
- **Models:** `Modality`, `Service` (with modality FK, price, TAT, template reference)
- **APIs:** CRUD, CSV import
- **Status:** ⚠️ REFACTOR - Duplicates `ServiceCatalog` in workflow app
- **Notes:** 
  - `Service` has rich metadata (modality, category, TAT, template)
  - `ServiceCatalog` is simpler (code, name, price, TAT)
  - Both are actively used

#### `/backend/apps/templates`
- **Models:** `Template`, `TemplateVersion`, `TemplateSection`, `TemplateField`, `FieldOption`
- **APIs:** CRUD, publish (creates TemplateVersion)
- **Status:** ✅ KEEP - Template builder system
- **Notes:** Used by legacy `Report` model, not by `USGReport`

#### `/backend/apps/studies` (LEGACY)
- **Models:** 
  - `Visit` (visit_number, billing fields, receipt generation)
  - `OrderItem` (links Visit to Service)
  - `Study` (accession, links to Patient/Service/Visit/OrderItem)
  - `ReceiptSequence`, `ReceiptSettings`
- **APIs:** 
  - `StudyViewSet` (CRUD)
  - `VisitViewSet` (CRUD, unified-intake, receipt generation)
  - `ReceiptSettingsViewSet`
- **Status:** ⚠️ REWIRE - Legacy system, partially replaced by workflow
- **Notes:**
  - `Visit` duplicates `ServiceVisit` concept
  - `Study` duplicates `ServiceVisit` concept (both represent exam/visit)
  - Receipt system is more mature than workflow receipt system
  - `FrontDeskIntake` UI uses this system

#### `/backend/apps/reporting` (LEGACY)
- **Models:** `Report` (links to Study, TemplateVersion, has values/narrative/impression)
- **APIs:** CRUD, create_for_study, save_draft, finalize, download_pdf
- **Status:** ⚠️ REWIRE - Legacy reporting, replaced by USGReport/OPDConsult
- **Notes:**
  - Template-driven reporting (uses TemplateVersion schema)
  - `ReportEditor` UI uses this
  - Not connected to new workflow system

#### `/backend/apps/workflow` (NEW)
- **Models:**
  - `ServiceCatalog` (simplified service catalog)
  - `ServiceVisit` (core workflow model, visit_id, status transitions)
  - `Invoice`, `Payment` (billing for ServiceVisit)
  - `USGReport` (JSON-based report, links to ServiceVisit)
  - `OPDVitals`, `OPDConsult` (OPD workflow models)
  - `StatusAuditLog` (audit trail for status transitions)
- **APIs:**
  - `ServiceCatalogViewSet`
  - `ServiceVisitViewSet` (create_visit, transition_status)
  - `USGReportViewSet` (save_draft, submit_for_verification, publish, return_for_correction)
  - `OPDVitalsViewSet`, `OPDConsultViewSet`
  - `PDFViewSet` (receipt, report, prescription)
- **Status:** ⚠️ REWIRE - New system but incomplete integration
- **Notes:**
  - Three-desk workflow (Registration → Performance → Verification)
  - Status-based state machine with audit logging
  - USGReport uses JSON, not template-driven
  - Missing connection to legacy Study/Report system

#### `/backend/apps/audit`
- **Models:** `AuditLog` (actor, action, entity_type, entity_id, meta)
- **APIs:** Read-only ViewSet
- **Status:** ✅ KEEP - General audit logging
- **Notes:** Used by legacy Report system, workflow uses StatusAuditLog

### `/frontend`
**Purpose:** React + TypeScript frontend

#### `/frontend/src/views/` (Workflow Pages - NEW)
- `RegistrationPage.tsx` - Uses ServiceVisit workflow
- `USGWorklistPage.tsx` - USG report entry
- `OPDVitalsWorklistPage.tsx` - OPD vitals entry
- `ConsultantWorklistPage.tsx` - OPD consultation
- `VerificationWorklistPage.tsx` - USG verification
- `FinalReportsPage.tsx` - Published reports viewer
- **Status:** ✅ KEEP - New workflow UI

#### `/frontend/src/views/` (Legacy Pages)
- `FrontDeskIntake.tsx` - Uses Visit/Study system
- `Studies.tsx` - Study management (legacy)
- `ReportEditor.tsx` - Template-based report editor (legacy)
- `Patients.tsx` - Patient management (shared)
- `Templates.tsx` - Template builder (shared)
- `ReceiptSettings.tsx` - Receipt branding (shared)
- `Dashboard.tsx` - Dashboard (mixed)
- **Status:** ⚠️ REWIRE - Legacy UI, needs migration or removal

### `/scripts`
- `test_e2e_workflow.py` - Tests new workflow system
- `smoke_api.sh`, `smoke_workflow.py` - Smoke tests
- Various deployment scripts
- **Status:** ✅ KEEP - Testing and deployment utilities

### `/docs`
- **Source of Truth:** `docs/00_overview.md` through `docs/10_merge_strategy.md`
- **Status:** ✅ KEEP - Authoritative design documentation
- **Notes:** Describes Study-based workflow, not ServiceVisit workflow

---

## Workflow Findings

### Legacy Workflow (Study-Based)
**Path:** Patient → Visit → OrderItem → Study → Report → PDF

1. **FrontDeskIntake** (`/intake`)
   - Creates `Visit` with billing
   - Creates `OrderItem` for each service
   - Creates `Study` for each OrderItem
   - Generates receipt via `ReceiptSequence`
   - **Status:** ⚠️ ACTIVE but LEGACY

2. **Studies Page** (`/studies`)
   - Lists `Study` objects
   - Can create/edit studies manually
   - Links to `ReportEditor` if report exists
   - **Status:** ⚠️ ACTIVE but LEGACY

3. **ReportEditor** (`/reports/:reportId/edit`)
   - Creates `Report` linked to `Study`
   - Uses `TemplateVersion` schema for form rendering
   - Saves draft, finalizes (generates PDF)
   - **Status:** ⚠️ ACTIVE but LEGACY

### New Workflow (ServiceVisit-Based)
**Path:** Patient → ServiceVisit → USGReport/OPDVitals/OPDConsult → Status Transitions → PDF

1. **RegistrationPage** (`/registration`)
   - Creates `ServiceVisit` with `ServiceCatalog`
   - Creates `Invoice` and `Payment`
   - Generates receipt (workflow receipt system)
   - **Status:** ✅ ACTIVE

2. **USG Workflow**
   - `USGWorklistPage` → Creates/updates `USGReport` (JSON-based)
   - `VerificationWorklistPage` → Publishes or returns for correction
   - Status transitions: REGISTERED → IN_PROGRESS → PENDING_VERIFICATION → PUBLISHED
   - **Status:** ✅ ACTIVE

3. **OPD Workflow**
   - `OPDVitalsWorklistPage` → Creates `OPDVitals`
   - `ConsultantWorklistPage` → Creates `OPDConsult`, saves & prints prescription
   - Status transitions: REGISTERED → IN_PROGRESS → PUBLISHED
   - **Status:** ✅ ACTIVE

### Broken/Incomplete Flows

1. **No Connection Between Systems**
   - Legacy `Study` and new `ServiceVisit` are completely separate
   - Legacy `Report` and new `USGReport` are completely separate
   - No migration path or data sync

2. **Receipt System Duplication**
   - Legacy: `ReceiptSequence` + `Visit.receipt_number` + `Visit.receipt_pdf_path`
   - New: `PDFViewSet.receipt` + `Invoice` + `Payment`
   - Both generate receipts but differently

3. **Service Catalog Duplication**
   - Legacy: `Service` (catalog app) - rich metadata
   - New: `ServiceCatalog` (workflow app) - simplified
   - Frontend uses both depending on page

4. **ReportEditor Not Connected**
   - `ReportEditor` uses legacy `Report` model
   - No way to create `Report` from `ServiceVisit`
   - `ReportEditor` route exists but workflow doesn't use it

---

## Duplication & Conflicts

### 1. Visit Models
**Legacy:** `apps/studies/models.Visit`
- Fields: visit_number, patient, billing fields, receipt fields
- Purpose: Billing-focused visit with receipt generation
- Used by: FrontDeskIntake, unified-intake API

**New:** `apps/workflow/models.ServiceVisit`
- Fields: visit_id, patient, service, status, assignments
- Purpose: Workflow-focused visit with status transitions
- Used by: RegistrationPage, all worklist pages

**Conflict:** Both represent "a patient visit for services" but serve different purposes. Legacy is billing-focused, new is workflow-focused.

**Recommendation:** REWIRE - Merge concepts or create clear separation

### 2. Service Models
**Legacy:** `apps/catalog/models.Service`
- Rich: modality FK, category, price/charges, TAT, default_template, requires_radiologist_approval
- Used by: Studies, FrontDeskIntake, Service import

**New:** `apps/workflow/models.ServiceCatalog`
- Simple: code, name, default_price, turnaround_time
- Used by: RegistrationPage, workflow APIs

**Conflict:** Two service catalogs. `Service` is more complete but `ServiceCatalog` is what workflow uses.

**Recommendation:** REFACTOR - Consolidate into single Service model

### 3. Report Models
**Legacy:** `apps/reporting/models.Report`
- Links to: `Study`, `TemplateVersion`
- Structure: Template-driven (values JSON keyed by TemplateField.key, narrative, impression)
- Used by: ReportEditor, Studies page

**New:** `apps/workflow/models.USGReport`
- Links to: `ServiceVisit`
- Structure: Free-form JSON (report_json)
- Used by: USGWorklistPage, VerificationWorklistPage

**Conflict:** Two report systems. Legacy is template-driven, new is free-form JSON.

**Recommendation:** REWIRE - Decide on single reporting approach

### 4. Billing Systems
**Legacy:** `Visit` model with embedded billing fields
- Fields: subtotal, discount_amount, discount_percentage, net_total, paid_amount, due_amount, payment_method
- Receipt: ReceiptSequence + receipt_number + receipt_pdf_path

**New:** `Invoice` + `Payment` models
- Invoice: total_amount, discount, net_amount, balance_amount
- Payment: amount_paid, method, received_by, received_at
- Receipt: PDFViewSet.receipt endpoint

**Conflict:** Two billing implementations. Legacy is simpler (single model), new is normalized (separate models).

**Recommendation:** REWIRE - Standardize billing approach

### 5. Patient Registration Numbers
**Single Model:** `Patient` has both `mrn` and `patient_reg_no`
- `mrn`: Date-based (MR20260101001)
- `patient_reg_no`: Sequential (PRN000001)
- **Status:** ✅ No conflict, both used appropriately

---

## Classification Table

| Feature/Module | Classification | Rationale |
|---------------|----------------|-----------|
| **Core Models** |
| `Patient` | ✅ KEEP | Single source of truth, used by both systems |
| `Modality` | ✅ KEEP | Shared concept |
| `Service` (catalog) | ⚠️ REFACTOR | Rich model but duplicated by ServiceCatalog |
| `ServiceCatalog` (workflow) | ⚠️ REFACTOR | Simplified duplicate of Service |
| `Template` system | ✅ KEEP | Template builder, used by legacy Report |
| **Legacy System** |
| `Visit` (studies) | ⚠️ REWIRE | Billing-focused, duplicates ServiceVisit concept |
| `Study` | ⚠️ REWIRE | Exam concept, duplicates ServiceVisit |
| `OrderItem` | ⚠️ REWIRE | Links Visit to Service, workflow doesn't use |
| `Report` (reporting) | ⚠️ REWIRE | Template-driven, replaced by USGReport |
| `ReceiptSequence` | ✅ KEEP | Mature receipt numbering, used by legacy |
| `ReceiptSettings` | ✅ KEEP | Shared branding settings |
| **New Workflow System** |
| `ServiceVisit` | ⚠️ REWIRE | Core workflow model but needs integration |
| `Invoice` | ⚠️ REWIRE | Billing model, duplicates Visit billing |
| `Payment` | ⚠️ REWIRE | Payment tracking, duplicates Visit payment fields |
| `USGReport` | ⚠️ REWIRE | JSON-based report, replaces Report |
| `OPDVitals` | ✅ KEEP | OPD-specific, no duplicate |
| `OPDConsult` | ✅ KEEP | OPD-specific, no duplicate |
| `StatusAuditLog` | ✅ KEEP | Workflow audit trail |
| **Frontend Pages** |
| `RegistrationPage` | ✅ KEEP | New workflow UI |
| `USGWorklistPage` | ✅ KEEP | New workflow UI |
| `OPDVitalsWorklistPage` | ✅ KEEP | New workflow UI |
| `ConsultantWorklistPage` | ✅ KEEP | New workflow UI |
| `VerificationWorklistPage` | ✅ KEEP | New workflow UI |
| `FinalReportsPage` | ✅ KEEP | New workflow UI |
| `FrontDeskIntake` | ⚠️ REWIRE | Legacy UI, uses Visit/Study system |
| `Studies` | ⚠️ REWIRE | Legacy UI, uses Study model |
| `ReportEditor` | ⚠️ REWIRE | Legacy UI, uses Report model, not connected to workflow |
| `Patients` | ✅ KEEP | Shared UI |
| `Templates` | ✅ KEEP | Shared UI |
| `ReceiptSettings` | ✅ KEEP | Shared UI |
| `Dashboard` | ⚠️ REWIRE | Mixed data sources |
| **APIs** |
| `/api/patients/` | ✅ KEEP | Shared |
| `/api/services/` | ⚠️ REFACTOR | Uses Service model, conflicts with ServiceCatalog |
| `/api/workflow/service-catalog/` | ⚠️ REFACTOR | Uses ServiceCatalog, conflicts with Service |
| `/api/studies/` | ⚠️ REWIRE | Legacy Study API |
| `/api/visits/` | ⚠️ REWIRE | Legacy Visit API |
| `/api/reports/` | ⚠️ REWIRE | Legacy Report API |
| `/api/workflow/visits/` | ⚠️ REWIRE | New ServiceVisit API |
| `/api/workflow/usg/` | ⚠️ REWIRE | New USGReport API |
| `/api/workflow/opd/` | ✅ KEEP | New OPD APIs |
| `/api/receipt-settings/` | ✅ KEEP | Shared |
| **Utilities** |
| `AuditLog` | ✅ KEEP | General audit logging |
| Scripts | ✅ KEEP | Testing and deployment |
| Documentation | ⚠️ DELETE | 30+ markdown files, many duplicates |

---

## High-Risk Areas

### 1. **Dual Workflow Systems**
**Risk:** HIGH  
**Issue:** Two complete workflow systems operating in parallel
- Legacy: Study → Report (template-driven)
- New: ServiceVisit → USGReport (JSON-driven)

**Impact:**
- Data inconsistency (same patient can have both Study and ServiceVisit)
- UI confusion (users don't know which system to use)
- Maintenance burden (two codebases to maintain)

**Recommendation:** Choose one system and migrate the other

### 2. **Service Catalog Duplication**
**Risk:** MEDIUM  
**Issue:** `Service` and `ServiceCatalog` both represent services
- `Service` has rich metadata (modality, category, TAT, template)
- `ServiceCatalog` is simpler (code, name, price)

**Impact:**
- Data sync issues (services added to one don't appear in other)
- Frontend confusion (which API to call?)
- Import complexity (CSV import updates Service, not ServiceCatalog)

**Recommendation:** Consolidate into single Service model

### 3. **Billing System Duplication**
**Risk:** MEDIUM  
**Issue:** Two billing implementations
- Legacy: `Visit` with embedded billing fields
- New: `Invoice` + `Payment` models

**Impact:**
- Receipt generation differs between systems
- Payment tracking inconsistent
- Financial reporting complexity

**Recommendation:** Standardize on one billing approach

### 4. **ReportEditor Orphaned**
**Risk:** LOW  
**Issue:** `ReportEditor` uses legacy `Report` model but workflow doesn't create Reports
- Route exists: `/reports/:reportId/edit`
- No way to create Report from ServiceVisit
- Studies page links to ReportEditor but workflow doesn't

**Impact:**
- Dead code (ReportEditor exists but unused in workflow)
- User confusion (link exists but doesn't work)

**Recommendation:** Either connect ReportEditor to workflow or remove it

### 5. **Template System Unused in Workflow**
**Risk:** LOW  
**Issue:** Template builder exists but USGReport uses free-form JSON
- Templates are created and published
- Legacy Report uses templates
- USGReport ignores templates

**Impact:**
- Template system investment wasted for workflow
- Inconsistent reporting (structured vs free-form)

**Recommendation:** Either use templates in workflow or remove template requirement

### 6. **Documentation Bloat**
**Risk:** LOW  
**Issue:** 30+ markdown files in root directory
- Multiple README variants
- Completion reports, status reports
- Deployment guides, verification reports

**Impact:**
- Confusion about which docs are authoritative
- Maintenance burden
- Cluttered repository

**Recommendation:** Consolidate or archive old documentation

---

## Summary

### System State
- **Two parallel workflows:** Legacy Study-based and new ServiceVisit-based
- **Three duplicate concepts:** Visit/ServiceVisit, Service/ServiceCatalog, Report/USGReport
- **Two billing systems:** Visit billing vs Invoice/Payment
- **Mixed UI:** Some pages use legacy, some use new workflow

### Alignment with Source of Truth
The `docs/` directory describes a **Study-based workflow** with template-driven reporting. However, the **new workflow system** (ServiceVisit-based) has been implemented and is actively used in production. This creates a mismatch between documentation and implementation.

### Recommendations Priority
1. **URGENT:** Decide on single workflow system (Study vs ServiceVisit)
2. **HIGH:** Consolidate Service and ServiceCatalog
3. **MEDIUM:** Standardize billing system
4. **LOW:** Clean up orphaned code (ReportEditor, unused templates)
5. **LOW:** Consolidate documentation

### Next Steps
1. Review source-of-truth documentation vs actual implementation
2. Decide on migration strategy (legacy → new or new → legacy)
3. Create integration plan for chosen system
4. Plan data migration if consolidating models

---

**End of Audit Report**
