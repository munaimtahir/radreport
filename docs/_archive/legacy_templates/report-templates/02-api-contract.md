# Report Templates API Contract

## Templates
- `GET /api/report-templates/`
  - Query params: `include_inactive=true|false`
- `POST /api/report-templates/`
  - Body: `{ name, code?, description?, category?, is_active, version }`
- `GET /api/report-templates/{id}/`
- `PATCH /api/report-templates/{id}/`
- `DELETE /api/report-templates/{id}/` (soft delete -> `is_active=false`)
- `POST /api/report-templates/{id}/duplicate/`
  - Clones template + fields + options.
- `PUT /api/report-templates/{id}/fields/`
  - Body: `[ { id?, label, key, field_type, is_required, help_text?, default_value?, placeholder?, order, validation?, is_active, options? } ]`

## Service linking
- `GET /api/services/{id}/templates/`
- `POST /api/services/{id}/templates/`
  - Body: `{ template_id, is_default?, is_active? }`
- `PATCH /api/services/{id}/templates/{link_id}/`
  - Body: `{ is_default?, is_active? }`
- `DELETE /api/services/{id}/templates/{link_id}/`

## Reporting integration
- `GET /api/reporting/{workitem_id}/template/`
  - Returns `{ template, report }` where `template` includes fields and `report` includes stored values.
- `POST /api/reporting/{workitem_id}/save-template-report/`
  - Body:
    ```json
    {
      "template_id": "<uuid>",
      "values": { "field_key": "value" },
      "narrative_text": "optional",
      "submit": false
    }
    ```
  - On `submit=true`, required field validation is enforced and the work item transitions to `PENDING_VERIFICATION`.
