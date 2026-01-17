# Receipt PDF Verification Guide

## Overview
This guide describes how to verify the finalized dual-copy receipt PDF design for service visits in the RIMS system.

## Locked Requirements
The receipt PDF must meet these specifications:
1. **A4 Portrait format** - single page
2. **Two copies per page**:
   - Top copy labeled: "Patient copy"
   - Bottom copy labeled: "Office copy"
3. **Dotted tear separator** between copies (light grey)
4. **Self-contained halves** - each copy has complete information
5. **Clinic branding**:
   - Logo from ReceiptSettings (logo_image or header_image)
   - Clinic name: "Consultant Place Clinic" (customizable via settings)
6. **Footer text** (locked, centered, light grey, small):
   ```
   Adjacent Excel Labs, Near Arman Pan Shop Faisalabad Road Jaranwala
   For information/Appointment: Tel: 041 4313 777 | WhatsApp: 03279640897
   ```

## Styling Requirements
- **Service table header**: Blue background (#0B5ED7) with white text
- **Net Amount row**: Orange accent (#F39C12) 
- **Borders**: Subtle grey borders, no heavy grids
- **Separator**: Dotted line (light grey #9AA0A6)

## Test Endpoint
```
GET /api/pdf/{service_visit_id}/receipt/
```

## Verification Steps

### Prerequisites
1. Backend server running
2. At least one ServiceVisit with invoice and payment created
3. Admin access to upload logo (optional but recommended)

### Step 1: Create Test Data

#### Minimal Test Case (1 service item)
```bash
# Register a patient and create a service visit with 1 item
# Use the workflow UI at /workflow or API directly
# Note the service_visit ID
```

#### Heavy Load Test Case (10+ service items)
```bash
# Create a service visit with 10-15 service items
# This tests the overflow handling (should show first 10 + "(+ N more items)")
```

### Step 2: Upload Branding (Optional)
1. Navigate to: `/settings/receipt`
2. Upload logo image (recommended: square, max 200x200px)
3. OR upload header image (recommended: banner 1200x200px)
4. Verify header_text is "Consultant Place Clinic"
5. Verify footer_text shows the locked clinic details

### Step 3: Generate Receipt PDFs

#### Test Case 1: Minimal Receipt
```bash
# Access the receipt endpoint
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/pdf/{service_visit_id}/receipt/ \
  --output test_receipt_minimal.pdf
```

Or in browser:
```
http://localhost:8000/api/pdf/{service_visit_id}/receipt/
```

#### Test Case 2: Heavy Load Receipt
```bash
# Generate receipt with many items
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/pdf/{service_visit_id_with_many_items}/receipt/ \
  --output test_receipt_heavy.pdf
```

### Step 4: Visual Verification Checklist

Open each generated PDF and verify:

#### ✓ Page Format
- [ ] Single A4 page (portrait)
- [ ] No page breaks or overflow to page 2

#### ✓ Top Copy (Patient copy)
- [ ] Label reads exactly: "Patient copy" (lowercase 'copy')
- [ ] Logo or header image present (if uploaded)
- [ ] Clinic name: "Consultant Place Clinic"
- [ ] "RECEIPT" title centered
- [ ] Receipt metadata: Receipt No, Visit ID, Date, Cashier
- [ ] Patient Information section complete
- [ ] Service Information table with blue header (#0B5ED7)
- [ ] Payment Summary with orange Net Amount (#F39C12)
- [ ] Footer text exact and present (clinic address + contact)

#### ✓ Separator
- [ ] Dotted line between copies (light grey)
- [ ] No "Cut/Tear Here" text (removed)
- [ ] Separator is subtle and print-friendly

#### ✓ Bottom Copy (Office copy)
- [ ] Label reads exactly: "Office copy" (lowercase 'copy')
- [ ] All content identical to Patient copy except label
- [ ] Same logo, same data, same footer

#### ✓ Styling
- [ ] Service table header: blue background with white text
- [ ] Net Amount: orange accent but readable when printed
- [ ] Borders are subtle (not heavy black grid)
- [ ] Footer: centered, light grey, font size 8

#### ✓ Overflow Handling (Heavy Load Test)
- [ ] If > 10 items, shows first 10 items
- [ ] Last row shows "(+ N more items)" where N is remaining count
- [ ] Both copies still fit on one A4 page

### Step 5: Print Test
1. Print the PDF to physical paper or PDF printer
2. Verify:
   - [ ] All text is legible
   - [ ] Colors are print-friendly (blue and orange not too dark)
   - [ ] Footer text is readable
   - [ ] Dotted separator is visible for tearing

### Step 6: Data Migration Verification
```bash
# Check that existing ReceiptSettings was updated
cd /home/munaim/srv/apps/radreport/backend
python manage.py shell

# In Django shell:
from apps.studies.models import ReceiptSettings
settings = ReceiptSettings.get_settings()
print(settings.header_text)  # Should be "Consultant Place Clinic"
print(settings.footer_text)  # Should contain locked footer text
```

Expected:
- header_text: "Consultant Place Clinic"
- footer_text: "Adjacent Excel Labs, Near Arman Pan Shop Faisalabad Road Jaranwala\nFor information/Appointment: Tel: 041 4313 777 | WhatsApp: 03279640897"

## Expected Visual Outcome

### Layout
```
┌─────────────────────────────────────┐
│  [LOGO/HEADER IMAGE]                │
│  Consultant Place Clinic            │
│         RECEIPT                     │
│      Patient copy                   │
│                                     │
│  Receipt No: ...                    │
│  Visit ID: ...                      │
│  Date: ...                          │
│                                     │
│  Patient Information                │
│  [patient details table]            │
│                                     │
│  Service Information                │
│  ┌──────────────┬─────────┐        │
│  │ Service (BLUE)│ Amount  │        │
│  ├──────────────┼─────────┤        │
│  │ Item 1       │ Rs. ... │        │
│  └──────────────┴─────────┘        │
│                                     │
│  Payment Summary                    │
│  Total: Rs. ...                     │
│  Net Amount: Rs. ... (ORANGE)       │
│  Paid: Rs. ...                      │
│                                     │
│  Adjacent Excel Labs, Near Arman... │
│  For information/Appointment: ...   │
│                                     │
├ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┤  (dotted separator)
│                                     │
│  [LOGO/HEADER IMAGE]                │
│  Consultant Place Clinic            │
│         RECEIPT                     │
│       Office copy                   │
│                                     │
│  [... identical content ...]        │
│                                     │
└─────────────────────────────────────┘
```

## Troubleshooting

### Issue: Old header text still showing
**Solution**: Run migration
```bash
cd backend
python manage.py migrate studies
```

### Issue: Footer text is blank
**Solution**: 
1. Check migration ran: `python manage.py showmigrations studies`
2. Manually update via admin or shell
3. Re-generate receipt

### Issue: Both copies don't fit on one page
**Solution**: This should auto-handle via MAX_ITEMS_DISPLAY=10. If still overflowing:
- Check logo/header image size (should be scaled)
- Verify spacing values in receipt.py
- Report as bug for further spacing reduction

### Issue: Logo not displaying
**Solution**:
1. Verify logo uploaded via `/settings/receipt`
2. Check file exists at uploaded path
3. Verify image format (jpg, png supported)

## Smoke Test Summary

Minimum passing criteria:
1. ✓ PDF generates without error
2. ✓ Single A4 page
3. ✓ Two copies present with correct labels ("Patient copy", "Office copy")
4. ✓ Dotted separator visible
5. ✓ Footer text correct and present in both copies
6. ✓ Heavy load (10+ items) still fits on one page

## Files Changed
- `backend/apps/studies/models.py` - Updated ReceiptSettings defaults
- `backend/apps/studies/migrations/0005_backfill_receipt_settings.py` - Data migration
- `backend/apps/reporting/pdf_engine/receipt.py` - Complete receipt layout rewrite
- `frontend/src/views/ReceiptSettings.tsx` - Updated default placeholders

## Related Documentation
- Workflow API: `/api/pdf/{pk}/receipt/` (PDFViewSet.receipt)
- Receipt builder: `backend/apps/workflow/pdf.py`
- ReportLab engine: `backend/apps/reporting/pdf_engine/receipt.py`
- Settings model: `backend/apps/studies/models.py` (ReceiptSettings)
