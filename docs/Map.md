# Codebase Truth Map - Registration v2 Hardening Sprint

## Frontend Architecture
- **Framework**: React 18.3.1 + TypeScript
- **Build Tool**: Vite 5.4.2
- **Routing**: React Router DOM 6.26.2
- **Entry**: `frontend/src/main.tsx`
- **App Shell**: `frontend/src/ui/App.tsx`

## Authentication
- **Method**: JWT Bearer token
- **Storage**: `localStorage.getItem("token")`
- **Login Endpoint**: `/api/auth/token/` (POST, returns `{access: "token"}`)
- **Auth Context**: `frontend/src/ui/auth.tsx` (provides `token`, `user`, `logout`)
- **API Base**: `frontend/src/ui/api.ts` (uses `VITE_API_BASE` env or defaults to `/api` in prod, `http://localhost:8000/api` in dev)

## Registration Page
- **Route**: `/registration` (defined in `frontend/src/ui/App.tsx`)
- **Component**: `frontend/src/views/RegistrationPage.tsx`
- **Status**: Current version does NOT have v2 features (keyboard-first, most-used services, etc.)
- **Needs**: Full v2 rewrite with keyboard navigation, service search dropdown, most-used buttons

## Backend Architecture
- **Framework**: Django 5.2.9 + Django REST Framework
- **Entry**: `backend/manage.py`
- **Settings**: `backend/rims_backend/settings.py`
- **URLs**: `backend/rims_backend/urls.py`

## API Endpoints

### Authentication
- `POST /api/auth/token/` - Login (returns JWT access token)

### Patients
- `GET /api/patients/?search={query}` - Search patients by name/mobile/reg_no
- `POST /api/patients/` - Create patient
- `PATCH /api/patients/{id}/` - Update patient
- **ViewSet**: `backend/apps/patients/api.py::PatientViewSet`

### Services
- `GET /api/services/` - List/search services (supports `?search=`, `?category=`, `?modality=`)
- `GET /api/services/most-used/` - **MISSING** - Needs to be implemented
- **ViewSet**: `backend/apps/catalog/api.py::ServiceViewSet`
- **Serializer**: `backend/apps/catalog/serializers.py::ServiceSerializer`
- **Model**: `backend/apps/catalog/models.py::Service`
- **Note**: Service model does NOT have `usage_count` field - needs to be calculated from ServiceVisitItem

### Visits (Workflow)
- `POST /api/workflow/visits/create_visit/` - Create service visit with multiple services
- **Payload** (from `backend/apps/workflow/serializers.py::ServiceVisitCreateSerializer`):
  ```json
  {
    "patient_id": "uuid",
    "service_ids": ["uuid1", "uuid2"],
    "subtotal": "decimal",
    "discount": "decimal",
    "discount_percentage": "decimal|null",
    "total_amount": "decimal",
    "net_amount": "decimal",
    "amount_paid": "decimal",
    "payment_method": "cash|card|online|insurance|other"
  }
  ```
- **ViewSet**: `backend/apps/workflow/api.py::ServiceVisitViewSet`
- **Model**: `backend/apps/workflow/models.py::ServiceVisit` + `ServiceVisitItem`

### Receipt PDF
- `GET /api/pdf/{visit_id}/receipt/` - Generate receipt PDF (returns PDF blob)
- **ViewSet**: `backend/apps/workflow/api.py::PDFViewSet`
- **Engine**: `backend/apps/reporting/pdf_engine/receipt.py`
- **Functions**:
  - `build_receipt_pdf_reportlab(visit)` - Legacy Visit model
  - `build_service_visit_receipt_pdf_reportlab(service_visit, invoice)` - Workflow ServiceVisit model
- **Status**: Does NOT have dual-copy (Patient Copy + Office Copy) - needs implementation

### Receipt Settings
- `GET /api/receipt-settings/` - Get settings (authenticated)
- `GET /api/receipt-settings/public/` - Get public settings (logo only, no auth)
- `PATCH /api/receipt-settings/` - Update settings
- **ViewSet**: `backend/apps/studies/api.py::ReceiptSettingsViewSet`
- **Model**: `backend/apps/studies/models.py::ReceiptSettings`
- **Fields**:
  - `header_text` (CharField, max 200)
  - `logo_image` (ImageField)
  - `header_image` (ImageField)
  - `footer_text` - **MISSING** - Needs migration `0004_receiptsettings_footer_text.py`
- **Serializer**: `backend/apps/studies/serializers.py::ReceiptSettingsSerializer`

## Migrations Status
- **Existing**: `backend/apps/studies/migrations/0003_receiptsequence_receiptsettings_and_more.py`
- **Missing**: `0004_receiptsettings_footer_text.py` - Needs to be created and applied

## Key Files

### Frontend
- `frontend/src/views/RegistrationPage.tsx` - Main registration component (needs v2 rewrite)
- `frontend/src/ui/api.ts` - API client utilities
- `frontend/src/ui/auth.tsx` - Auth context provider
- `frontend/src/ui/App.tsx` - App shell with routing

### Backend
- `backend/apps/catalog/api.py` - Service endpoints (needs `/most-used/` action)
- `backend/apps/catalog/serializers.py` - Service serializer (needs `usage_count` field)
- `backend/apps/workflow/api.py` - Visit creation endpoint
- `backend/apps/workflow/serializers.py` - Visit creation serializer
- `backend/apps/studies/models.py` - ReceiptSettings model (needs `footer_text` field)
- `backend/apps/studies/api.py` - ReceiptSettings endpoints
- `backend/apps/reporting/pdf_engine/receipt.py` - PDF generation (needs dual-copy)

## Missing Features (To Implement)
1. ✅ `/api/services/most-used/` endpoint
2. ✅ `ReceiptSettings.footer_text` field + migration
3. ✅ Dual-copy receipt PDF (Patient Copy + Office Copy on one A4)
4. ✅ RegistrationPage v2 with keyboard-first navigation
5. ✅ Service search dropdown with arrow keys + Enter
6. ✅ Most-used services quick buttons
7. ✅ Discount % field (0-100 clamp)
8. ✅ DOB ↔ age linkage
9. ✅ Enter behaves like Tab across patient → services → billing
