# Consultant Settlement Notes (MVP)

## Billing model references
- Visit/Invoice header: `ServiceVisit` in `backend/apps/workflow/models.py` (plus `Invoice` for totals).
- Billed service items: `ServiceVisitItem` in `backend/apps/workflow/models.py`.
- Payments: `Payment` in `backend/apps/workflow/models.py`.

## Consultant extensions
- `ConsultantProfile`, `ConsultantBillingRule`, `ConsultantSettlement`, `ConsultantSettlementLine` in `backend/apps/consultants/models.py`.
- `ServiceVisit.booked_consultant` and `ServiceVisitItem.consultant` added in `backend/apps/workflow/models.py`.

## Paid/partial-paid allocation assumptions
- Settlement preview/draft uses payments recorded on the visit within the selected date range (`Payment.received_at`).
- Paid allocation is sequential across visit items ordered by `ServiceVisitItem.created_at` then `id`.
- Items without an assigned consultant are excluded from consultant settlement calculations in the MVP.
- Items already included in a **FINALIZED** settlement are excluded from new settlement previews/drafts.
