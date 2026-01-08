# API-Interfaces.md

## Auth
- POST `/api/auth/login`
- POST `/api/auth/logout`
- GET  `/api/auth/me`

## Patients
- GET  `/api/patients?query=` (MR/phone/name)
- POST `/api/patients` (create new patient → generates MR)
- GET  `/api/patients/{id}`
- PATCH `/api/patients/{id}`

## Visits
- POST `/api/visits` (create visit for patient → generates SV)
- GET  `/api/visits/{id}`
- GET  `/api/visits/{id}/services`
- POST `/api/visits/{id}/services` (add service line items)
- DELETE `/api/visit-services/{id}` (soft delete recommended)

## Service Catalog
- GET  `/api/services`
- POST `/api/services`
- PATCH `/api/services/{id}`
- POST `/api/services/import` (CSV import optional)

## Billing / Receipt
- POST `/api/visits/{id}/payment` (create/update payment)
- GET  `/api/visits/{id}/payment`
- GET  `/api/payments/{id}/receipt.pdf`
- POST `/api/payments/{id}/print-log` (log print)

## Worklists
- GET `/api/worklists/usg?status=`
- GET `/api/worklists/opd?status=`

## USG
- GET  `/api/usg/{visit_service_id}`
- POST `/api/usg/{visit_service_id}/draft` (save draft)
- POST `/api/usg/{visit_service_id}/submit`
- POST `/api/usg/{visit_service_id}/return` (with reason)
- POST `/api/usg/{visit_service_id}/verify`
- POST `/api/usg/{visit_service_id}/publish`
- GET  `/api/usg/{visit_service_id}/report.pdf`

## OPD
- GET  `/api/opd/{visit_service_id}`
- POST `/api/opd/{visit_service_id}/vitals`
- POST `/api/opd/{visit_service_id}/finalize`
- POST `/api/opd/{visit_service_id}/publish`
- GET  `/api/opd/{visit_service_id}/prescription.pdf`

## Admin / Audit
- GET `/api/audit?entity_type=&entity_id=`
