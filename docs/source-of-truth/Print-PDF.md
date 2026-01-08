# Print-PDF.md

## A4 Duplicate Receipt (Mandatory)
- Page: A4 Portrait
- Layout:
  - **Top 48%:** Patient Copy
  - **Middle 2%:** Divider line + “--- cut here ---”
  - **Bottom 48%:** Office Copy
- Both copies show same receipt data, only label differs.

### Receipt Content
- Header: Center name + logo (left) + contact/address
- Receipt No: `YYMM-001` (configurable)
- Date/Time
- Patient: MR, name, age/sex, phone
- Visit: SV
- Services table:
  - Service | Rate
- Totals:
  - subtotal, discount, total, paid, due
- Footer: Thank-you note + optional terms

## Ultrasound Report PDF
- Clean medical report format
- Header includes center details + logo
- Patient block: MR, SV, name, age/sex, date/time
- Findings section (template-based)
- Impression (optional)
- Verification block:
  - verified by, timestamp, version
- Footer disclaimer (medical interpretation)

## OPD Prescription PDF
- Header includes center details + logo
- Patient block: MR, SV, name, age/sex, date/time
- Vitals summary
- Diagnosis
- Medicines table
- Advice + Investigations
- Doctor name + signature line
