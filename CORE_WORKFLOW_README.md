# Core Workflow (3 Desks) - RIMS

## Overview

The RIMS core workflow implements a three-desk system for managing patient visits through registration, performance, and verification stages. Each service visit moves through status-based transitions with full audit logging.

## Architecture

### Three Desk Roles

1. **Registration Desk**
   - Patient search and registration
   - Service visit creation
   - Receipt generation

2. **Performance Desk**
   - USG reporting (findings entry)
   - OPD vitals entry
   - OPD consultation (diagnosis, medicines, investigations)

3. **Verification Desk**
   - USG report verification
   - Publish or return for correction

### ID Model

- **PatientRegNo**: Permanent unique patient registration number (format: PRN000001)
- **ServiceVisitID**: Unique visit/service ID per visit (format: SV20260101001)
- A patient can have many visits; visits move through worklists

### Status Engine

ServiceVisit statuses:
- `REGISTERED` - Initial status after registration
- `IN_PROGRESS` - Performance desk is working on it
- `PENDING_VERIFICATION` - Awaiting verification
- `RETURNED_FOR_CORRECTION` - Returned by verification desk
- `PUBLISHED` - Final published status (locked)
- `CANCELLED` - Cancelled visit

All status transitions are logged in `StatusAuditLog` with:
- Who changed it
- When it changed
- From status → To status
- Reason (optional)

## Workflows

### USG Workflow

1. **Registration**: Create service visit with service=USG → status=REGISTERED
2. **USG Worklist (Performance)**: 
   - Opens USG reporting template form
   - Enters findings
   - Saves → status=PENDING_VERIFICATION
3. **Verification Worklist**:
   - Can return for correction (status=RETURNED_FOR_CORRECTION + reason) → goes back to USG Worklist
   - Can publish → status=PUBLISHED, generates final report PDF, locks editing

### OPD Workflow

1. **Registration**: Create service visit with service=OPD → status=REGISTERED
2. **OPD Vitals Worklist (Performance)**:
   - Enters vitals (BP, pulse, temp, etc.)
   - Saves → status=IN_PROGRESS
3. **Consultant Worklist (Performance)**:
   - Enters diagnosis, medicines, investigations, advice, follow-up
   - Clicks Save & Print → status=PUBLISHED, generates prescription PDF

## Data Models

### ServiceVisit
- Core workflow model
- Links patient + service
- Tracks status and assignments
- Auto-generates visit_id

### Invoice
- One-to-one with ServiceVisit
- Tracks total_amount, discount, net_amount, balance_amount

### Payment
- Links to ServiceVisit
- Records amount_paid, method, received_by, received_at

### USGReport
- One-to-one with ServiceVisit
- Stores report_json (structured findings)
- Tracks created_by, updated_by, verifier
- Stores published_pdf_path

### OPDVitals
- One-to-one with ServiceVisit
- Stores BP, pulse, temperature, SpO2, weight, height, BMI

### OPDConsult
- One-to-one with ServiceVisit
- Stores diagnosis, medicines_json, investigations_json, advice, followup
- Stores published_pdf_path

### StatusAuditLog
- Logs all status transitions
- Records who, when, from→to, reason

## API Endpoints

### Patients
- `GET /api/patients/?search=` - Search patients
- `POST /api/patients/` - Create patient
- `PUT /api/patients/:id/` - Update patient

### Services
- `GET /api/workflow/service-catalog/` - List services

### Visits
- `POST /api/workflow/visits/create_visit/` - Create service visit (Registration)
- `GET /api/workflow/visits/?workflow=USG|OPD&status=` - List visits by workflow/status
- `GET /api/workflow/visits/:id/` - Get visit details
- `POST /api/workflow/visits/:id/transition_status/` - Transition status

### USG
- `GET /api/workflow/usg/?visit_id=` - Get USG report
- `POST /api/workflow/usg/` - Create/update USG report
- `POST /api/workflow/usg/:id/save_draft/` - Save draft
- `POST /api/workflow/usg/:id/submit_for_verification/` - Submit for verification
- `POST /api/workflow/usg/:id/publish/` - Publish (Verification)
- `POST /api/workflow/usg/:id/return_for_correction/` - Return for correction

### OPD
- `POST /api/workflow/opd/vitals/` - Create/update vitals
- `POST /api/workflow/opd/consult/` - Create/update consultation
- `POST /api/workflow/opd/consult/:id/save_and_print/` - Save & print prescription

### PDFs
- `GET /api/pdf/receipt/:visit_id/` - Get receipt PDF
- `GET /api/pdf/report/:visit_id/` - Get USG report PDF
- `GET /api/pdf/prescription/:visit_id/` - Get OPD prescription PDF

## Frontend Pages

1. **RegistrationPage** (`/registration`)
   - Top: Patient search + patient form (create/update)
   - Bottom: Service registration form (select service, charges, payment, save/save+print receipt)

2. **USGWorklistPage** (`/worklists/usg`)
   - Shows visits with status=REGISTERED or RETURNED_FOR_CORRECTION
   - Opens USG reporting form
   - Saves and submits for verification

3. **OPDVitalsWorklistPage** (`/worklists/opd-vitals`)
   - Shows visits with status=REGISTERED
   - Opens vitals form
   - Saves → moves to consultant worklist

4. **ConsultantWorklistPage** (`/worklists/consultant`)
   - Shows visits with status=IN_PROGRESS
   - Opens consultation form
   - Saves & prints prescription

5. **VerificationWorklistPage** (`/worklists/verification`)
   - Shows visits with status=PENDING_VERIFICATION
   - Can publish or return for correction

6. **FinalReportsPage** (`/reports`)
   - Shows published visits (status=PUBLISHED)
   - Download/view PDFs

## Receipt Printing

Receipt number format: `yymm-001` (increments monthly)
- Generated via `ReceiptSequence.get_next_receipt_number()`
- Includes patient identifiers, visit ID, service name, charges, paid, balance, payment method, date/time, cashier name
- PDF stored and downloadable

## RBAC

Role-based access control enforced at route + API level:
- Registration desk: Can create visits, search patients
- Performance desk: Can work on USG reports, OPD vitals, consultations
- Verification desk: Can verify and publish USG reports

For MVP, all authenticated users have access. In production, use Django groups:
- Group: "Registration"
- Group: "Performance"  
- Group: "Verification"

## Setup

1. **Run migrations**:
```bash
cd backend
python manage.py migrate
```

2. **Seed services**:
```bash
python manage.py seed_services
```

3. **Create user groups** (optional, for production RBAC):
```bash
python manage.py shell
>>> from django.contrib.auth.models import Group
>>> Group.objects.get_or_create(name="Registration")
>>> Group.objects.get_or_create(name="Performance")
>>> Group.objects.get_or_create(name="Verification")
```

## Testing Checklist

- [ ] Create new patient → patient_reg_no generated → searchable
- [ ] Existing patient → new visit → visit_id generated
- [ ] USG visit shows in USG Worklist → entry saved → moves to Verification → publish → appears in Final Reports with PDF
- [ ] USG verifier return → goes back to USG Worklist with reason visible
- [ ] OPD visit → vitals saved → moves to consultant → save&print → appears in Final Reports with prescription PDF
- [ ] Receipt save&print works and receipt number increments monthly
- [ ] RBAC prevents wrong desk from performing actions
- [ ] StatusAuditLog exists for every transition
