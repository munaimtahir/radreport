# Patient Workflow Viewer

## Overview
The Patient Workflow Viewer provides a unified list of patients with their most recent visit, computed workflow status, and reprint actions. The workflow status is derived from existing visit, payment, and report data (no stored redundant state).

## Workflow Status Mapping
Statuses are computed from current workflow data:

- `registered`: No service items added yet.
- `services_added`: Services exist but no payment recorded.
- `paid`: Payment recorded; no workflow progress started.
- `sample_collected`: Any service item is `IN_PROGRESS`.
- `report_pending`: Any item is `PENDING_VERIFICATION`, `RETURNED_FOR_CORRECTION`, or `FINALIZED` (not yet published).
- `report_ready`: Report finalized (`FINAL`/`AMENDED`) but PDF not published.
- `report_published`: Published report PDF available.

## API Endpoints

### List patients with workflow status
`GET /api/workflow/patients/`

Query params:
- `search=` (matches name, phone, MRN, patient_reg_no, visit_id, receipt_number; case-insensitive)
- `date_from=YYYY-MM-DD` (inclusive, filters by ServiceVisit.registered_at)
- `date_to=YYYY-MM-DD` (inclusive, filters by ServiceVisit.registered_at)
- `status=` one of `registered`, `services_added`, `paid`, `sample_collected`, `report_pending`, `report_ready`, `report_published`
- `page=`
- `page_size=`

Response shape:
```json
{
  "count": 0,
  "next": null,
  "previous": null,
  "results": [
    {
      "patient_id": "...",
      "mrn": "...",
      "reg_no": "...",
      "name": "...",
      "age": 0,
      "sex": "...",
      "phone": "...",
      "last_visit_at": "...",
      "latest_visit_id": "...",
      "workflow_status": "paid",
      "receipt": { "available": true, "receipt_id": "...", "pdf_url": "/api/workflow/visits/<id>/receipt/pdf/" },
      "reports": {
        "available": true,
        "items": [
          { "service_name": "USG Abdomen", "status": "published", "pdf_url": "/api/pdf/<visit_id>/report/" }
        ]
      }
    }
  ]
}
```

### Patient timeline
`GET /api/workflow/patients/{patient_id}/timeline/`

Optional query params:
- `date_from=YYYY-MM-DD`
- `date_to=YYYY-MM-DD`

Returns patient summary plus a newest-first list of visits with workflow status, receipt availability, and report availability.

## Receipt Reprinting Rules
- Receipts are immutable. Reprints never generate new receipt numbers or recalculate totals.
- Receipt PDFs use immutable snapshot data.
- Reprint endpoints:
  - `GET /api/workflow/visits/{visit_id}/receipt/`
  - `GET /api/workflow/visits/{visit_id}/receipt/pdf/`
  - `GET /api/visits/{visit_id}/receipt/` (alias)
  - `GET /api/visits/{visit_id}/receipt/pdf/` (alias)

## Example Calls
```bash
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8000/api/workflow/patients/?search=MR2024&date_from=2024-04-01&date_to=2024-04-30"

curl -H "Authorization: Bearer <token>" \
  "http://localhost:8000/api/workflow/patients/<patient_id>/timeline/"
```
