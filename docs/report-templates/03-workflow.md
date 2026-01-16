# Report Templates Workflow

## Admin workflow
1. Create a report template in **Admin → Report Templates**.
2. Add fields and options, then save.
3. Link templates to services in **Admin → Service Templates**.
4. Mark one template as default per service.

## Reporting workflow
1. Open a worklist item in the report entry screen.
2. If a default report template exists for the service, the dynamic form renders.
3. Save draft → values are stored via `/api/reporting/{workitem_id}/save-template-report/`.
4. Submit for verification → required fields are validated and the item transitions to `PENDING_VERIFICATION`.

## Legacy compatibility
- If no report template exists, the existing reporting flow continues to render the legacy template schema or free-text fields.
