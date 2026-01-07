# Unified Patient + Exam Intake Workflow Refactor

## Overview

This document describes the refactoring of the system to merge Patient Registration and Study/Exam Registration into a single unified workflow suitable for real-world front-desk operations in a diagnostic clinic/radiology/OPD setup.

## Changes Summary

### Backend Changes

#### 1. Patient Model (`apps/patients/models.py`)
- **MRN Auto-generation**: MRN is now auto-generated on patient creation using format `MR{YYYYMMDD}{####}`
- **Date of Birth Support**: Added `date_of_birth` field for better patient identification
- **Read-only MRN**: MRN field is now read-only and auto-generated

#### 2. Service Model (`apps/catalog/models.py`)
- **CSV Support Fields**: Added fields to support CSV import:
  - `code`: Unique service code (CSV-driven)
  - `category`: Service category (Radiology/Lab/OPD/Procedure)
  - `charges`: Alias for price, CSV-driven
  - `tat_value`: TAT numeric value
  - `tat_unit`: TAT unit (hours/days)
- **Auto-calculation**: `tat_minutes` is automatically calculated from `tat_value` and `tat_unit`
- **Price Sync**: `charges` and `price` fields are synchronized

#### 3. New Models (`apps/studies/models.py`)
- **Visit Model**: Represents a patient visit/transaction
  - Auto-generates `visit_number` (format: `VN{YYYYMMDD}{####}`)
  - Stores billing snapshot (subtotal, discount, net_total, paid_amount, due_amount)
  - Tracks payment method and finalization status
- **OrderItem Model**: Represents individual services in a visit
  - Links to Visit and Service
  - Stores charge snapshot at order time
  - Supports indication per item

#### 4. Study Model Updates
- Added `visit` and `order_item` foreign keys to link studies to visits
- Studies are automatically created for radiology services during visit finalization

#### 5. API Endpoints

**New Endpoints:**
- `POST /api/visits/unified-intake/`: Unified intake endpoint (patient + services + billing)
- `POST /api/visits/{id}/finalize/`: Finalize a visit
- `GET /api/visits/{id}/receipt/`: Generate receipt PDF
- `POST /api/services/import-csv/`: Import services from CSV

**Updated Endpoints:**
- `GET /api/services/`: Now filters by `is_active=true` by default (can include inactive with `?include_inactive=true`)
- `GET /api/visits/`: List and retrieve visits

#### 6. Serializers
- **UnifiedIntakeSerializer**: Handles unified patient + exam intake
- **VisitSerializer**: Serializes visit with nested items
- **OrderItemSerializer**: Serializes order items with service details

#### 7. Workflow Routing
- Radiology services automatically create Study records
- Studies are routed to the radiology queue (status: "registered")
- Lab and OPD services can be extended for routing to respective queues

### Frontend Changes

#### 1. New Component: `FrontDeskIntake.tsx`
- **Single Page Interface**: Combines patient registration and service selection
- **Patient Search**: Search existing patients by MRN, name, or phone
- **New Patient Form**: Inline form for creating new patients
- **Service Cart**: Add multiple services with indication
- **Live Billing**: Real-time calculation of subtotal, discount, net total, paid, and due
- **Actions**: "Save" and "Save & Print Receipt" buttons

#### 2. Navigation Updates
- Added "Front Desk Intake" link to main navigation
- Route: `/intake`

## CSV Import Format

### Required Columns
- `code`: Unique service code (string)
- `name`: Service name (string)
- `category`: Category (Radiology/Lab/OPD/Procedure)
- `modality`: Modality code (USG/CT/XRAY/LAB/CONSULT)
- `charges`: Service charge (decimal)
- `tat_value`: TAT numeric value (integer)
- `tat_unit`: TAT unit (hours/days)
- `active`: Active status (true/false)

### Example CSV
```csv
code,name,category,modality,charges,tat_value,tat_unit,active
USG001,Abdominal USG,Radiology,USG,1500.00,2,hours,true
CT001,Chest CT,Radiology,CT,5000.00,24,hours,true
LAB001,CBC,Lab,LAB,500.00,4,hours,true
```

## Data Flow

1. **Patient Selection/Creation**
   - User searches for existing patient OR creates new patient
   - MRN is auto-generated for new patients
   - Patient must exist before services can be added

2. **Service Selection**
   - User searches and adds services from catalog
   - Services are added to cart
   - Charges are auto-populated from catalog

3. **Billing Calculation**
   - Subtotal = sum of service charges
   - Discount (amount or percentage)
   - Net Total = Subtotal - Discount
   - Paid Amount defaults to Net Total
   - Due Amount = Net Total - Paid

4. **Finalization**
   - Visit number is auto-generated
   - Visit is finalized (billing locked)
   - Studies are created for radiology services
   - Receipt can be printed

## Migration Notes

### Database Migrations
Run migrations to apply changes:
```bash
python manage.py migrate
```

### Existing Data
- Existing patients retain their MRNs
- Existing studies remain valid
- New workflow applies to new entries only
- Service catalog can be updated via CSV import

### Breaking Changes
- MRN field is now read-only (auto-generated)
- Patient creation no longer requires MRN input
- Study creation now supports visit linkage

## Testing Checklist

- [x] Single screen handles patient + exam
- [x] MR auto-generated once per patient
- [x] Visit number generated per transaction
- [x] Services loaded from catalog
- [x] Charges auto-populate
- [x] Paid defaults to total
- [x] Discount & due work correctly
- [x] Receipt prints
- [x] Record reaches next workflow stage (studies created)

## API Usage Examples

### Unified Intake
```json
POST /api/visits/unified-intake/
{
  "patient_id": "uuid-or-null",
  "name": "John Doe",
  "age": 35,
  "gender": "M",
  "phone": "1234567890",
  "items": [
    {
      "service_id": "service-uuid",
      "indication": "Routine checkup"
    }
  ],
  "discount_amount": 0,
  "discount_percentage": null,
  "paid_amount": 1500.00,
  "payment_method": "cash"
}
```

### CSV Import
```bash
POST /api/services/import-csv/
Content-Type: multipart/form-data
file: services.csv
```

## Future Enhancements

1. Lab queue routing for lab services
2. OPD queue routing for consultation services
3. Receipt customization/templates
4. Payment method validation
5. Discount approval workflow
6. Visit editing before finalization
