# UI-Wireframes.md

## Global Layout
- Top bar: Center name + location, user menu
- Left sidebar: Reception, Worklists (USG/OPD), Reprint Center, Admin
- Main content area: forms + tables
- Theme: minimal, soft background, professional clinic look
- Logo: configurable in Admin

---

## Screen 1: Reception (Single page – split view)
### A) Patient Section (top)
- Search box (MR/phone/name)
- Search results list
- “New Patient” button
- Patient form: name, age/gender, phone, address (optional)

### B) Visit + Services Section (bottom)
- Visit details: SV auto-generated on create
- Services selector (searchable dropdown)
- Selected services table:
  - Service name | Dept | Rate | Remove
- Billing panel:
  - Subtotal
  - Discount (type + value)
  - Total
  - Paid
  - Due (auto)
- Actions:
  - Save & Print Receipt
  - Save Only (optional)
  - Cancel

---

## Screen 2: USG Worklist
- Table: SV | MR | Patient | Services | Status | Time | Action (Open)
- Filters: status, date, template type
- Quick badge: “Pending Verification”

## Screen 3: USG Entry (Operator)
- Patient header (MR, SV, name, age/sex)
- Template picker
- Form fields (template-based)
- Impression (optional)
- Buttons:
  - Save Draft
  - Submit for Verification
- Status banner

## Screen 4: USG Verification (Verifier)
- Read-only view of findings
- Buttons:
  - Return for correction (requires reason)
  - Verify
  - Publish (after verify)
- “Generate PDF Preview” optional

---

## Screen 5: OPD Worklist
- Table: SV | MR | Patient | Status | Action (Open)
- Filters: status, doctor

## Screen 6: OPD Vitals
- Vitals form
- Save → Forward to doctor

## Screen 7: OPD Doctor
- Diagnosis
- Medicines (repeatable list: drug, dose, frequency, duration)
- Advice
- Investigations (optional)
- Finalize + Publish

---

## Screen 8: Reprint Center
- Search by MR / SV / Receipt No
- Tabs: Receipts | USG Reports | Prescriptions
- Print log view (who printed, when, version)
