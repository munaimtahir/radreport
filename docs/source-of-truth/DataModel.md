# DataModel.md

## Patient
- id (uuid/int)
- mr_no (string, unique)
- full_name
- gender
- age_years (or dob)
- phone
- address (optional)
- created_at, updated_at
- is_active

## Visit
- id
- sv_no (string, unique)
- patient_id (FK)
- registered_at
- created_by (FK user)
- overall_status (enum; minimum: REGISTERED)
- notes (optional)

## ServiceCatalog
- id
- code (optional)
- name
- department (enum: USG, OPD)
- base_price
- tat_minutes (optional)
- is_active

## VisitService (line items)
- id
- visit_id (FK)
- service_catalog_id (FK)
- service_name_snapshot
- department_snapshot
- price_snapshot
- status (department-specific enum)
- assigned_to (optional)
- created_at, updated_at

## Payment
- id
- visit_id (FK, one-to-one preferred)
- subtotal
- discount_type (NONE, FIXED, PERCENT)
- discount_value
- total
- paid
- due
- payment_mode (CASH/CARD/ONLINE; optional)
- receipt_no (unique)
- created_at

## ReceiptPrintLog
- id
- payment_id (FK)
- printed_by (FK user)
- printed_at
- copy_type (PATIENT, OFFICE, BOTH)
- version (int)

## UsgReport
- id
- visit_service_id (FK to VisitService where department=USG)
- template_key (ABD, KUB, PELVIS, etc.)
- data_json (structured fields)
- impression_text (optional)
- status (enum aligned with Workflows.md)
- submitted_at, verified_at, published_at
- verified_by (FK user)
- version (int)

## OpdEncounter
- id
- visit_service_id (FK to VisitService where department=OPD)
- vitals_json (BP, pulse, temp, weight, etc.)
- diagnosis_text
- medicines_json (list)
- advice_text
- investigations_text (optional)
- status (enum aligned)
- finalized_by (FK user)
- version (int)

## DocumentStore (optional but recommended)
- id
- doc_type (RECEIPT/USG_REPORT/OPD_RX)
- related_id (payment/usg/opd)
- file_path or blob ref
- version
- created_at

## AuditEvent
- id
- actor_user_id
- action (string)
- entity_type (string)
- entity_id
- before_json (optional)
- after_json (optional)
- created_at
