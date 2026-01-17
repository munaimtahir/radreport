# Workflow Viewer + Receipt Reprint Verification Checklist

## Backend Checks
- [ ] Reprint endpoints return the same receipt number and totals as originally issued.
- [ ] Reprint endpoints never create a new receipt number.
- [ ] Reprint endpoints never recalculate totals or mutate data.
- [ ] Pricing changes after payment do not affect reprint output.
- [ ] Search matches name, MRN, patient_reg_no, phone, visit_id, and receipt_number.
- [ ] Date range filtering is inclusive (`date_from` >= 00:00:00, `date_to` <= 23:59:59).
- [ ] Status filter returns correct workflow states.
- [ ] Unauthorized users are blocked from workflow endpoints.

## Frontend Checks
- [ ] Search input debounces and updates results.
- [ ] Date range filters update results immediately.
- [ ] URL query params reflect filters and persist across pagination.
- [ ] Pagination retains current filters.
- [ ] Receipt reprint button disabled when receipt is unavailable.
- [ ] Report print button disabled when no published report exists.
- [ ] Timeline view loads visit history and actions correctly.
- [ ] Receipt/report PDFs open successfully.

## Regression Checks
- [ ] Registration flow unchanged.
- [ ] Payment and receipt issuance flow unchanged.
- [ ] Reporting/verification workflow unchanged.
