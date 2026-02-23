# RIMS Dashboard Truth Map

## Metric Inventory
Here is the list of metrics displayed on the dashboard, what they meant previously, and their new corrected definitions.

1. **Total Patients Today**
   - **Old Source:** `apiGet("/dashboard/summary/")` (Server Timezone bug)
   - **Why Wrong:** Used `timezone.now()` which defaults to UTC. Local boundaries (like Pakistan's Karachi midnight) were completely ignored.
   - **New Definition:** Count of distinct patients from visits registered today (`Asia/Karachi` timezone).
   - **Backend Query:** `ServiceVisit.objects.filter(registered_at__gte=today_start, registered_at__lt=today_end).values('patient').distinct().count()`

2. **Total Services Today**
   - **Old Source:** `apiGet("/dashboard/summary/")`
   - **Why Wrong:** Server Timezone drift.
   - **New Definition:** Count of service visit items created today (`Asia/Karachi` timezone).
   - **Backend Query:** `ServiceVisitItem.objects.filter(created_at__gte=today_start, created_at__lt=today_end).count()`

3. **Reports Pending**
   - **Old Source:** `apiGet("/dashboard/summary/")`
   - **Why Wrong:** Correct query in previous code but decoupled from main payload.
   - **New Definition:** Count of all items currently in `PENDING_VERIFICATION` status globally.
   - **Backend Query:** `ServiceVisitItem.objects.filter(status="PENDING_VERIFICATION").count()`

4. **Reports Verified**
   - **Old Source:** `apiGet("/dashboard/summary/")`
   - **Why Wrong:** Server Timezone drift.
   - **New Definition:** Count of items published today (`Asia/Karachi` timezone).
   - **Backend Query:** `ServiceVisitItem.objects.filter(status="PUBLISHED", published_at__gte=today_start, published_at__lt=today_end).count()`

5. **Critical Delays**
   - **Old Source:** `apiGet("/dashboard/summary/")`
   - **Why Wrong:** Correct logic for threshold but timezone drift.
   - **New Definition:** Count of items in `IN_PROGRESS` or `PENDING_VERIFICATION` longer than 4 hours.
   - **Backend Query:** Filter for `IN_PROGRESS | PENDING_VERIFICATION` where `started_at < threshold` or `submitted_at < threshold` or `created_at < threshold`.

6. **Today's Flow (Registered, Paid, Performed, Reported, Verified)**
   - **Old Source:** `apiGet("/dashboard/flow/")`
   - **Why Wrong:** Not merged with single payload, and had Timezone drift.
   - **New Definition:** Exact count of distinct items matching step filters within local today.

7. **My / Department Worklists**
   - **Old Source:** `apiGet("/dashboard/worklist/?scope=X")`
   - **Why Wrong:** Redundant API request and client-side scope handling.
   - **New Definition:** Items constrained correctly by Admin RBAC vs My Tasks RBAC inside the canonical endpoint.

## Endpoint Contract (Canonical Payload)
Endpoint: `GET /api/dashboard/summary/`
Sample Response:
```json
{
  "timestamp_generated": "2026-02-23T06:53:48+00:00",
  "timezone_used": "Asia/Karachi",
  "tenant_id": null,
  "user_context": {
    "username": "admin",
    "is_admin": true,
    "scope": "department"
  },
  "metrics": [
    {
      "key": "reports_pending",
      "label": "Reports Pending",
      "value": 15,
      "definition": "Count of all items currently in PENDING_VERIFICATION status globally."
    }
  ],
  "sections": {
    "pending_worklist": {
      "items": [],
      "grouped_by_department": { "USG": [] },
      "total_items": 0,
      "scope": "department"
    },
    "flow": {
      "registered_count": 5,
      ...
    }
  }
}
```

## Setup & Tests
- No DB migrations were needed as the dashboard relies on existing stable fields.
- **Backend tests:** Run `source .venv/bin/activate && pytest apps/workflow/tests/test_dashboard_truth.py -v`
- **Frontend tests:** Run `npm run test -- views/__tests__/Dashboard.test.tsx`
- **Truth command:** Run `cat ARTIFACTS/dashboard_truth_check.txt` after generating it with `python manage.py dashboard_truth_check`.
