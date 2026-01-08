# PHASE B: Core Model Enforcement Implementation Log

## Overview
This document tracks the implementation of Phase B: Core Model Enforcement for RIMS (Radiology LIMS-style workflow).

**Goal:** Unify the service catalog, line items, billing, and receipt generation while disabling legacy write paths.

---

## 1. BASELINE REPO MAP

### Current Models (Before Phase B)

#### Workflow App (`backend/apps/workflow/models.py`)
- **ServiceCatalog** - Service catalog (code, name, default_price, turnaround_time, is_active)
  - Used by: ServiceVisit.service (ForeignKey)
  - API: `/api/workflow/service-catalog/`
- **ServiceVisit** - Core workflow model
  - Links to: ServiceCatalog (single service per visit - **NEEDS CHANGE**)
  - Links to: Patient
  - Status: REGISTERED → IN_PROGRESS → PENDING_VERIFICATION → PUBLISHED
- **Invoice** - OneToOne with ServiceVisit
  - Fields: total_amount, discount, net_amount, balance_amount
- **Payment** - ForeignKey to ServiceVisit (supports multiple payments)
  - Fields: amount_paid, method, received_by, received_at
- **USGReport** - OneToOne with ServiceVisit
- **OPDVitals** - OneToOne with ServiceVisit
- **OPDConsult** - OneToOne with ServiceVisit

#### Catalog App (`backend/apps/catalog/models.py`)
- **Service** - Rich service model (canonical)
  - Fields: code, modality, name, category, price, charges, tat_value, tat_unit, tat_minutes, default_template, requires_radiologist_approval, is_active
  - API: `/api/services/`
  - **This is the source of truth per requirements**

#### Legacy Studies App (`backend/apps/studies/models.py`)
- **Visit** - Legacy visit model (to be archived)
  - Has embedded billing fields (subtotal, discount_amount, net_total, paid_amount, due_amount)
  - Has receipt_number, receipt_pdf_path
- **OrderItem** - Links Visit to catalog.Service (supports multiple items)
  - Has charge snapshot
- **Study** - Legacy study model (to be archived)
- **ReceiptSequence** - Receipt number generator (YYMM-### format)
- **ReceiptSettings** - Receipt branding settings (singleton)

#### Legacy Reporting App (`backend/apps/reporting/models.py`)
- **Report** - Legacy report model (to be archived)
  - Links to Study

### Key Issues Identified
1. **ServiceCatalog duplicates catalog.Service** - Two service catalogs exist
2. **ServiceVisit only supports one service** - Needs ServiceVisitItem for multiple services
3. **Receipt numbering** - Legacy ReceiptSequence exists, needs integration
4. **Legacy write paths** - Visit/Study/Report can still be created via API

---

## 2. CONSOLIDATE SERVICE CATALOG

### Changes Made
- [x] Replace ServiceCatalog references with catalog.Service
- [x] Update ServiceCatalogViewSet to proxy to catalog.Service (read-only)
- [x] Mark ServiceCatalog model as deprecated but keep for migration compatibility
- [x] Update API endpoints to use catalog.Service
- [x] Update frontend to use `/api/services/` instead of `/api/workflow/service-catalog/`

### Files Touched
- `backend/apps/workflow/models.py` - Marked ServiceCatalog as deprecated
- `backend/apps/workflow/api.py` - ServiceCatalogViewSet now proxies to catalog.Service
- `backend/apps/workflow/serializers.py` - Added ServiceVisitItemSerializer
- `backend/apps/workflow/admin.py` - Added ServiceVisitItemAdmin, updated ServiceCatalogAdmin
- `frontend/src/views/RegistrationPage.tsx` - Updated to use `/services/` API and support multiple services

---

## 3. UNIFY VISIT LINE ITEMS

### Changes Made
- [x] Create ServiceVisitItem model with snapshots
- [x] Update ServiceVisit to support multiple items via items relationship
- [x] Make ServiceVisit.service nullable for backward compatibility
- [x] Update serializers to include items
- [x] Update ServiceVisitCreateSerializer to accept service_ids array
- [x] Update frontend registration flow to support multiple service selection

### ServiceVisitItem Model Structure
```python
class ServiceVisitItem(models.Model):
    service_visit = ForeignKey(ServiceVisit)
    service = ForeignKey(catalog.Service)
    service_name_snapshot = CharField(max_length=150)
    department_snapshot = CharField(max_length=50)  # USG/OPD
    price_snapshot = DecimalField(max_digits=10, decimal_places=2)
    status = CharField(choices=SERVICE_VISIT_STATUS, default="REGISTERED")
    created_at/updated_at
```

---

## 4. BILLING: LOCK INVOICE + PAYMENT

### Changes Made
- [x] Added subtotal field to Invoice
- [x] Added discount_percentage field to Invoice
- [x] Added receipt_number field to Invoice (idempotent generation)
- [x] Updated Invoice.save() to auto-calculate balance from payments
- [x] Payment model already supports multiple payments (partial payments)
- [x] Receipt number generated on first payment only

---

## 5. RECEIPT PDF GENERATION

### Changes Made
- [x] Integrated ReceiptSequence.get_next_receipt_number() into Invoice creation
- [x] Receipt number format is YYMM-### (e.g., 2501-001)
- [x] Updated PDFViewSet.receipt to use invoice.receipt_number (idempotent)
- [x] Receipt number generated only once when first payment is made
- [x] Receipt PDF generation uses canonical receipt number from invoice

---

## 6. DISABLE LEGACY WRITE PATHS

### Changes Made
- [x] Added get_permissions() to VisitViewSet - blocks create/update/delete for non-admin
- [x] Added get_permissions() to StudyViewSet - blocks create/update/delete for non-admin
- [x] Added get_permissions() to ReportViewSet - blocks create/update/delete for non-admin
- [x] Legacy endpoints are now read-only for regular users (admin-only writes)

---

## 7. REWIRE WORKFLOW PAGES

### Changes Made
- [x] Updated RegistrationPage to use `/services/` API
- [x] Updated RegistrationPage to support multiple service selection
- [x] Updated ServiceVisitCreateSerializer to create ServiceVisitItems
- [x] Updated USGReportViewSet to link reports to ServiceVisitItem
- [x] Updated OPDVitalsViewSet to link vitals to ServiceVisitItem
- [x] Updated OPDConsultViewSet to link consults to ServiceVisitItem
- [x] Updated ServiceVisitViewSet workflow filtering to use items relationship

---

## 8. MIGRATIONS + DATA SAFETY

### Migrations Created
- [x] Created migration `0002_phase_b_consolidation.py`:
  - Adds ServiceVisitItem model
  - Makes ServiceVisit.service nullable (backward compatibility)
  - Adds subtotal, discount_percentage, receipt_number to Invoice
  - Adds service_visit_item fields to USGReport, OPDVitals, OPDConsult
  - Keeps legacy fields for backward compatibility
- [ ] **Data migration not performed** - ServiceCatalog data migration can be done in Phase C if needed

---

## 9. PHASE B SMOKE TESTS

### Test Checklist
- [ ] Create patient → MR stable
- [ ] Create ServiceVisit with multiple services (USG + OPD) → items created with snapshots
- [ ] Create Invoice/Payment → due computed correctly for partial payment
- [ ] Generate receipt → receipt_no format OK and PDF endpoint returns 200
- [ ] USG worklist shows USG items for that SV
- [ ] OPD worklist shows OPD items for that SV
- [ ] Confirm no legacy Visit/Study/Report created by new UI flow

---

## Key Decisions

1. **ServiceCatalog Deprecation**: Kept model but marked as deprecated; ServiceCatalogViewSet now proxies to catalog.Service API
2. **ServiceVisitItem**: Created new model to support multiple services per visit with price snapshots
3. **Receipt Numbering**: Reused legacy ReceiptSequence logic (YYMM-### format), integrated into Invoice model
4. **Legacy Write Blocking**: Used permission gating (IsAdminUser) for create/update/delete operations
5. **Backward Compatibility**: Kept legacy fields (service_visit.service, service_visit_item) nullable for migration period
6. **USG/OPD Report Linking**: Updated to prefer ServiceVisitItem but fallback to ServiceVisit for legacy data

---

## Manual Steps to Run

1. **Run migrations:**
   ```bash
   cd backend
   python3 manage.py migrate workflow
   ```

2. **Restart backend server:**
   ```bash
   # Restart your Django server
   ```

3. **Restart frontend (if needed):**
   ```bash
   cd frontend
   npm install  # If dependencies changed
   npm run dev  # Or your build command
   ```

4. **Run smoke tests:**
   ```bash
   python3 scripts/phase_b_smoke.py
   ```

5. **Verify legacy write paths are blocked:**
   - Try creating a Visit via `/api/visits/` - should return 403 Forbidden for non-admin
   - Try creating a Study via `/api/studies/` - should return 403 Forbidden for non-admin
   - Try creating a Report via `/api/reports/` - should return 403 Forbidden for non-admin

---

## Files Modified

### Backend Models
- `backend/apps/workflow/models.py` - Added ServiceVisitItem, updated ServiceVisit, Invoice, USGReport, OPDVitals, OPDConsult

### Backend APIs
- `backend/apps/workflow/api.py` - Updated all viewsets to use ServiceVisitItem, blocked legacy writes
- `backend/apps/studies/api.py` - Added permission checks to block writes
- `backend/apps/reporting/api.py` - Added permission checks to block writes

### Backend Serializers
- `backend/apps/workflow/serializers.py` - Added ServiceVisitItemSerializer, updated all serializers

### Backend Admin
- `backend/apps/workflow/admin.py` - Added ServiceVisitItemAdmin

### Frontend
- `frontend/src/views/RegistrationPage.tsx` - Updated to use unified catalog and support multiple services

### Migrations
- `backend/apps/workflow/migrations/0002_phase_b_consolidation.py` - Phase B migration

### Scripts
- `scripts/phase_b_smoke.py` - Smoke test suite

### Documentation
- `PHASE_B_IMPLEMENTATION_LOG.md` - This file

---

## Notes

- Do not delete legacy tables yet (migration in Phase C/D)
- Preserve existing Patient model and search functionality
- Ensure backward compatibility where possible
