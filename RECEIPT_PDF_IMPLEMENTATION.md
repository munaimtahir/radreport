# Receipt PDF Generation Module - Implementation Summary

## Overview
A comprehensive PDF receipt generation system has been implemented with branding support, concurrency-safe receipt numbering, and full integration with the FrontDeskIntake workflow.

## Features Implemented

### 1. Receipt Number Generation
- **Format**: YYMM-### (e.g., 2601-001 for January 2026)
- **Monthly Reset**: Counter resets each month automatically
- **Concurrency-Safe**: Uses database-level locking (`select_for_update`) to prevent collisions
- **Implementation**: `ReceiptSequence` model with atomic transaction handling

### 2. Receipt Branding
- **Header Text**: Configurable header text (default: "Consultants Clinic Place")
- **Logo Image**: Optional logo upload with preview
- **Header Image**: Optional banner-style header image upload
- **Fallback**: If images not uploaded, renders text header only
- **Storage**: Images stored in `/media/branding/`

### 3. PDF Generation
- **Page Size**: A4
- **Template Includes**:
  - Header (image/logo/text)
  - Receipt metadata (receipt number, date/time, cashier)
  - Patient information (MRN, name, age/gender, mobile)
  - Service items table with charges
  - Billing summary (subtotal, discount, net total, paid, due)
  - Footer note
- **Storage**: PDFs saved to `/media/pdfs/receipts/{YYYY}/{MM}/{receipt_number}.pdf`
- **Reprint Support**: Can regenerate or serve existing PDFs

### 4. Database Models

#### ReceiptSequence
- `yymm`: Month identifier (e.g., "2601")
- `last_number`: Last generated sequence number
- `updated_at`: Timestamp

#### ReceiptSettings (Singleton)
- `header_text`: Default header text
- `logo_image`: Logo file (optional)
- `header_image`: Header banner file (optional)
- `updated_by`: User who last updated
- `updated_at`: Timestamp

#### Visit Model Updates
- `receipt_number`: Generated receipt number (YYMM-###)
- `receipt_pdf_path`: Path to stored PDF file
- `receipt_generated_at`: Timestamp when receipt was generated

### 5. API Endpoints

#### Receipt Settings
- `GET /api/receipt-settings/` - Get current settings
- `PATCH /api/receipt-settings/1/` - Update header text
- `POST /api/receipt-settings/logo/` - Upload logo image
- `POST /api/receipt-settings/header-image/` - Upload header image

#### Receipt Generation
- `POST /api/visits/{id}/generate-receipt/` - Generate receipt number and PDF
- `GET /api/visits/{id}/receipt/` - Download/view receipt PDF

### 6. Frontend Components

#### ReceiptSettings Page
- Header text input with save
- Logo upload with preview
- Header image upload with preview
- Located at `/receipt-settings` route

#### FrontDeskIntake Integration
- "Save & Print Receipt" button generates receipt and opens PDF
- Automatically calls `generate-receipt` endpoint before displaying PDF
- PDF opens in new tab for printing/downloading

### 7. Admin Interface
- ReceiptSettings admin with image previews
- ReceiptSequence admin for monitoring
- Visit admin shows receipt number and PDF path

### 8. Testing
Comprehensive test suite in `apps/studies/tests.py`:
- Receipt number format validation
- Sequential numbering
- Concurrency safety tests
- PDF generation tests
- Integration workflow tests

## File Structure

```
backend/
├── apps/
│   ├── studies/
│   │   ├── models.py          # ReceiptSequence, ReceiptSettings, Visit updates
│   │   ├── api.py              # ReceiptSettingsViewSet, receipt endpoints
│   │   ├── serializers.py      # ReceiptSettingsSerializer
│   │   ├── admin.py            # Admin interfaces
│   │   └── tests.py            # Unit tests
│   └── reporting/
│       └── pdf.py              # Enhanced PDF generation with branding
├── rims_backend/
│   └── urls.py                 # ReceiptSettingsViewSet registration, media serving
└── media/
    ├── branding/               # Logo and header images
    └── pdfs/
        └── receipts/
            └── {YYYY}/{MM}/    # Receipt PDFs

frontend/
└── src/
    └── views/
        ├── ReceiptSettings.tsx # Admin UI for branding
        └── FrontDeskIntake.tsx # Updated with receipt generation
```

## Usage

### Setting Up Branding
1. Navigate to `/receipt-settings` in the frontend
2. Update header text if needed
3. Upload logo image (optional)
4. Upload header image (optional)
5. Preview changes

### Generating Receipts
1. Complete Front Desk Intake workflow
2. Click "Save & Print Receipt"
3. Receipt number is generated automatically
4. PDF is created and opened in new tab
5. Print or download as needed

### Reprinting Receipts
- Visit detail screen can call `/api/visits/{id}/receipt/` to reprint
- Same receipt number is used (idempotent)

## Technical Details

### Concurrency Safety
- Uses Django's `select_for_update()` with database transactions
- Prevents race conditions in high-concurrency scenarios
- Tested with multi-threaded test cases

### PDF Generation
- Uses ReportLab for programmatic PDF creation
- Supports image rendering with PIL/Pillow
- Maintains aspect ratios for images
- Print-friendly layout with proper spacing

### File Storage
- Media files served in development via Django static file serving
- Production should use proper media file serving (e.g., nginx, S3)
- PDFs organized by year/month for easy management

## Migration
Run migrations:
```bash
python manage.py migrate
```

## Testing
Run tests:
```bash
python manage.py test apps.studies.tests
```

## Future Enhancements
- QR code generation for receipts
- Email receipt delivery
- Receipt templates customization
- Multi-language support
- Receipt history/audit trail
