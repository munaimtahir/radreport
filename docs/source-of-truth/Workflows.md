# Workflows.md

## Entities & IDs (Locked)
### Patient
- **MR Number** (permanent, unique)
- Format suggestion: `MR000001` (configurable)

### Visit
- **SV (Service Visit ID)** (unique per visit)
- Format suggestion: `SVYYYYMMDD-001` (daily sequence) OR `SV20260108-0001`
- A visit can include multiple ordered services.

### VisitService (Line Items)
- Each ordered service becomes a VisitService record with:
  - service name snapshot
  - price snapshot
  - department routing (USG / OPD)
  - its own status (optional but recommended)

---

## Reception Workflow (Registration + Billing + Receipt)
**Actor:** Receptionist

1. Search patient (MR / phone / name)
2. If not found → create patient → generate MR
3. Create new Visit → generate SV
4. Add services from Service Catalog (rates auto-populate)
5. Billing:
   - subtotal (sum of selected services)
   - discount: % or fixed
   - total = subtotal - discount
   - paid amount (>=0)
   - due = total - paid
6. Save transaction
7. Print receipt (A4 duplicate: patient copy + office copy)
8. System routes to worklists:
   - OPD if any OPD service in visit
   - USG if any USG service in visit

### Reception Statuses
Visit status:
- `REGISTERED` (after save/receipt)

Payment status:
- `PAID` (due=0)
- `PARTIALLY_PAID` (due>0 and paid>0)
- `UNPAID` (paid=0)

---

## Ultrasound Workflow (Draft → Verify → Publish)
**Actors:** USG Data Operator, Verifier (Doctor/Radiologist)

VisitService (USG) statuses:
- `USG_DRAFTING`
- `USG_PENDING_VERIFICATION`
- `USG_RETURNED`
- `USG_VERIFIED`
- `USG_PUBLISHED`

Steps:
1. Operator opens USG worklist item
2. Selects template (e.g., Abdomen, KUB, Pelvis; configurable)
3. Enters findings + measurements
4. Save Draft
5. Submit for verification → status `USG_PENDING_VERIFICATION`
6. Verifier actions:
   - Return for correction → `USG_RETURNED` with reason
   - Verify → `USG_VERIFIED` (locks report fields)
7. Publish:
   - generate PDF
   - mark `USG_PUBLISHED`
   - allow printing + reprint with version log

---

## OPD Workflow (Vitals → Doctor → Publish)
**Actors:** OPD Operator, Doctor

VisitService (OPD) statuses:
- `OPD_VITALS_PENDING`
- `OPD_DOCTOR_PENDING`
- `OPD_FINALIZED`
- `OPD_PUBLISHED`

Steps:
1. OPD Operator opens OPD worklist item
2. Enters vitals
3. Saves and forwards to doctor → `OPD_DOCTOR_PENDING`
4. Doctor enters diagnosis + medicines + advice (+ investigations optional)
5. Finalize → `OPD_FINALIZED` (locks prescription)
6. Publish:
   - generate PDF
   - mark `OPD_PUBLISHED`
   - allow printing + reprint with version log

---

## Audit Log (Mandatory)
Log these events:
- patient created/updated
- visit created
- services added/removed (and by whom)
- payment recorded + receipt printed
- report draft saved
- report submitted/returned/verified/published
- prescription saved/finalized/published
- any deletion (prefer soft delete)
