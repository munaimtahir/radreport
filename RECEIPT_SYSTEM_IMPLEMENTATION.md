# Receipt System Implementation - Locked A4 Dual Copy Layout

## Overview
Implemented a locked receipt system for Consultants Place Clinic with A4 portrait layout, featuring two identical receipt copies per page (Patient copy top, Office copy bottom).

## Files Created/Modified

### Backend Files

#### 1. **Templates** (`backend/apps/studies/templates/receipts/`)
- `receipt_single.html` - Single receipt copy template (reusable component)
- `receipt_a4_dual.html` - A4 wrapper template with two copies and divider

#### 2. **Static Files** (`backend/static/css/`)
- `receipt_print.css` - Print/PDF CSS with A4 layout rules, dual copy styling

#### 3. **Backend Code**
- `backend/apps/reporting/pdf.py` - Updated `build_receipt_pdf()` function to use WeasyPrint with HTML templates
- `backend/apps/studies/api.py` - Added `receipt_preview` endpoint for HTML preview
- `backend/rims_backend/settings.py` - Added `STATIC_ROOT` and `STATICFILES_DIRS` configuration
- `backend/requirements.txt` - Added `weasyprint>=62.0` dependency

## Features Implemented

### ✅ A4 Portrait Layout
- Fixed A4 portrait page size (210mm × 297mm)
- 10mm margins on all sides
- Each receipt copy uses exactly 138mm height (half page after margins)

### ✅ Dual Copy System
- **Top Half**: Patient copy (labeled "Patient copy")
- **Bottom Half**: Office copy (labeled "Office copy")
- Dotted divider line with scissors icon between copies
- Both copies are identical except for the copy label

### ✅ Receipt Components
- **Header**: Logo (if configured) + "Consultants Place Clinic" name
- **Meta Information**: Receipt No (YYMM-### format), Date/Time, MR No
- **Patient Info**: Name, Age/Gender, Mobile, Consultant (if available)
- **Services Table**: Service/Test, Qty, Rate, Amount columns
- **Payment Summary**: Subtotal, Discount, Total Payable (orange highlight), Paid, Balance/Change
- **Footer**: Locked footer text with contact information

### ✅ Design System Compliance
- Colors: Primary Blue (#0B5ED7), Accent Orange (#F39C12), Text Dark (#2E2E2E), Muted Grey (#9AA0A6)
- Typography: Inter/Roboto/Arial sans-serif
- Layout: Clean whitespace, strict alignment, no overflow

### ✅ PDF Generation
- Uses WeasyPrint for HTML-to-PDF conversion
- Supports logo images from ReceiptSettings
- Handles missing fields gracefully (hides rows instead of breaking layout)
- Generates PDFs with proper A4 sizing

### ✅ Preview System
- HTML preview endpoint: `/api/visits/{id}/receipt-preview/`
- Print button for browser printing
- Same template used for both PDF and preview

## How to Use

### 1. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Collect Static Files
```bash
python manage.py collectstatic --noinput
```

### 3. Generate Receipt PDF

#### Via API Endpoint:
```bash
# Generate receipt number and PDF
POST /api/visits/{visit_id}/generate-receipt/

# Get existing PDF
GET /api/visits/{visit_id}/receipt/

# Preview HTML version
GET /api/visits/{visit_id}/receipt-preview/
```

#### Programmatically:
```python
from apps.reporting.pdf import build_receipt_pdf
from apps.studies.models import Visit

visit = Visit.objects.get(id=visit_id)
pdf_file = build_receipt_pdf(visit)

# Save or serve PDF
with open('receipt.pdf', 'wb') as f:
    f.write(pdf_file.read())
```

### 4. Configure Logo
- Upload logo via: `POST /api/receipt-settings/logo/`
- Logo will appear in receipt header if configured
- Recommended size: max 60mm height, maintain aspect ratio

### 5. Print/Save PDF
- **From Preview**: Click "Print Receipt" button, then use browser's print dialog
- **From API**: Download PDF from `/api/visits/{id}/receipt/` endpoint
- **Browser Print**: Use `window.print()` on preview page

## Receipt Number Format
- Format: `YYMM-###` (e.g., `2601-001` for January 2026)
- Automatically generated via `ReceiptSequence.get_next_receipt_number()`
- Monthly reset (sequence resets each month)
- Concurrency-safe (uses database-level locking)

## Template Structure

### receipt_single.html
- Reusable single receipt copy component
- Accepts `copy_label` variable ("Patient copy" or "Office copy")
- Contains all receipt sections: header, meta, patient info, table, totals, footer

### receipt_a4_dual.html
- A4 page wrapper
- Includes `receipt_single.html` twice with different copy labels
- Adds divider between copies
- Includes print button for preview

## CSS Layout Details

### Key CSS Rules:
- `@page`: A4 portrait, 10mm margins
- `.receipt-copy`: Fixed 138mm height per copy
- `.page-divider`: 8mm height with dotted line
- Print media queries: Hides print button, ensures proper page breaks

### Responsive Behavior:
- **Screen**: Shows print button, adds shadow for preview
- **Print**: Hides controls, ensures clean A4 output

## Testing Checklist

### ✅ Rendering Tests
- [x] Receipt with 1 item renders correctly
- [x] Receipt with 10 items fits without overflow
- [x] Receipt with 25 items fits without overflow
- [x] Missing fields (mobile, consultant) handled gracefully

### ✅ Print Tests
- [x] A4 output shows two copies on one page
- [x] Bottom copy label reads "Office copy"
- [x] Divider line appears between copies
- [x] No content overlaps footer or divider

### ✅ Visual Tests
- [x] Logo displays correctly (if configured)
- [x] Footer text matches exactly: "Adjust Excel Labs, Near Arman Pan Shop Faisalabad Road Jaranwala..."
- [x] Colors match design system (Blue headers, Orange totals)
- [x] Typography is clean and readable

## Environment Variables
No new environment variables required. Uses existing Django settings.

## Dependencies Added
- `weasyprint>=62.0` - HTML to PDF conversion

## Notes
- Logo images should be placed in `/media/branding/` (handled by ReceiptSettings model)
- Static CSS file should be collected via `collectstatic` command
- Receipt numbering is handled automatically - no manual configuration needed
- The system gracefully handles missing optional fields (mobile, consultant, etc.)

## API Endpoints

### Receipt Generation
- `POST /api/visits/{id}/generate-receipt/` - Generate receipt number and PDF
- `GET /api/visits/{id}/receipt/` - Download receipt PDF
- `GET /api/visits/{id}/receipt-preview/` - Preview receipt HTML

### Receipt Settings
- `GET /api/receipt-settings/` - Get receipt branding settings
- `PUT /api/receipt-settings/` - Update settings
- `POST /api/receipt-settings/logo/` - Upload logo image

## Troubleshooting

### PDF Generation Fails
- Check if WeasyPrint is installed: `pip install weasyprint`
- Verify logo file exists and is readable
- Check static files are collected: `python manage.py collectstatic`

### Logo Not Showing
- Ensure logo is uploaded via `/api/receipt-settings/logo/`
- Check file permissions on logo file
- For PDF: Logo path must be absolute file:// URL
- For Preview: Logo URL must be accessible via MEDIA_URL

### Layout Issues
- Verify CSS file is in `backend/static/css/receipt_print.css`
- Run `collectstatic` to ensure CSS is available
- Check browser console for CSS loading errors

### Print Layout Wrong
- Ensure using A4 paper size in print dialog
- Check browser print settings (margins, scale)
- Verify @page CSS rules are applied
