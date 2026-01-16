# Dashboard v1 Documentation

## Overview

The Dashboard v1 provides a role-based overview of the Radiology Information Management System (RIMS) with 5 distinct layers of information. All dashboard data is derived from real database statuses with no fake caching.

## Role-Based Behavior

### Admin Users
- **Layer 2**: Sees "Department Worklists" grouped by department/modality (USG, OPD, CT, MRI, etc.)
- **Access**: Can view all departments and all work items across the system
- **Scope**: `scope=department` (default for admin)

### Non-Admin Users
- **Layer 2**: Sees "My Worklist" only
- **Access**: Restricted to items assigned to them or created by them
- **Scope**: `scope=my` (only allowed scope for non-admin)

## Dashboard Layers

### Layer 1: Global Status Strip (KPI Tiles)

Top-level KPIs for today (server timezone). All tiles are clickable and navigate to filtered list views.

**KPIs:**
- **Total Patients Today**: Count of unique patients with visits registered today
- **Total Services Today**: Count of service items created today
- **Reports Pending**: Count of items in `PENDING_VERIFICATION` status
- **Reports Verified**: Count of items `PUBLISHED` today
- **Critical Delays**: Count of items in reporting pipeline (IN_PROGRESS or PENDING_VERIFICATION) that have been waiting longer than the threshold (default: 4 hours)

**Click Actions:**
- Patients → `/registration`
- Services → `/registration`
- Pending → `/worklists/verification?status=PENDING_VERIFICATION`
- Verified → `/reports?status=PUBLISHED`
- Delays → `/worklists/verification?status=PENDING_VERIFICATION`

### Layer 2: Work In Progress

**Non-Admin (My Worklist):**
- Shows items assigned to the current user or created by the current user
- Statuses included: `IN_PROGRESS`, `PENDING_VERIFICATION`, `RETURNED_FOR_CORRECTION`, `FINALIZED`
- Sorted by longest waiting first
- Each row shows: Patient name/MRN, Service name, Status badge, Waiting time, Action link

**Admin (Department Worklists):**
- Shows worklists grouped by department/modality
- Same row design as My Worklist
- Scope is department-based, not user-based
- Only shows departments that have active items

**Worklist Item Fields:**
- `id`: ServiceVisitItem UUID
- `visit_id`: ServiceVisit visit_id
- `patient_name`: Patient full name
- `patient_mrn`: Patient MRN
- `service_name`: Service name snapshot
- `department`: Department/modality code (USG, OPD, etc.)
- `status`: Current status
- `status_display`: Human-readable status
- `created_at`: ISO datetime
- `last_updated`: ISO datetime
- `waiting_minutes`: Calculated waiting time
- `assigned_to`: Username of assigned user (if any)
- `action_url`: Navigation URL to open the item

### Layer 3: Today's Flow

Step counters showing the flow of work through the system today:

1. **Registered**: Visits registered today
2. **Paid**: Visits with payments received today
3. **Performed**: Items moved to `IN_PROGRESS` today
4. **Reported**: Items moved to `PENDING_VERIFICATION` today
5. **Verified**: Items `PUBLISHED` today

Each step is clickable and navigates to a filtered list view.

### Layer 4: Alerts & System Health

**Alerts:**
- Reports pending > threshold hours (configurable, default 4 hours)
- Returned reports (today or active)
- PDF generation failures (if logs exist; otherwise placeholder)
- Missing templates/config (placeholder if template system exists)

**System Health Card:**
- **Backend API**: Status (ok/degraded/down) + latency (ms) + last checked time
- **Database**: Status (ok/fail)
- **Storage**: Status (ok/unknown)
- **Network**: Online/Offline status (browser-based)
- **Version**: Git SHA or commit SHA (if available)

Health status refreshes every 60 seconds and on page load.

### Layer 5: Shortcuts

Up to 5 quick actions based on user role:

**Common Actions:**
- New Registration
- Search Patient
- USG Worklist
- Verification Queue

**Admin Only:**
- Templates Manager

All shortcuts navigate to existing routes/actions.

## API Endpoints

### GET /api/dashboard/summary/

Returns KPI counts for Layer 1.

**Query Parameters:**
- `date`: Optional, defaults to "today" (server timezone)
- `threshold_hours`: Optional, defaults to 4 (for critical delays calculation)

**Response:**
```json
{
  "date": "2024-01-15",
  "server_time": "2024-01-15T10:30:00Z",
  "total_patients_today": 25,
  "total_services_today": 42,
  "reports_pending": 8,
  "reports_verified": 15,
  "critical_delays": 2,
  "threshold_hours": 4
}
```

### GET /api/dashboard/worklist/

Returns work items for Layer 2.

**Query Parameters:**
- `scope`: Required. `"my"` for non-admin, `"department"` for admin
- `department`: Optional. Filter by specific department (USG, OPD, etc.) when scope=department

**Response (Non-Admin):**
```json
{
  "scope": "my",
  "items": [
    {
      "id": "uuid",
      "visit_id": "SV202401150001",
      "patient_name": "John Doe",
      "patient_mrn": "MR202401150001",
      "service_name": "Abdominal Ultrasound",
      "department": "USG",
      "status": "IN_PROGRESS",
      "status_display": "In Progress",
      "created_at": "2024-01-15T08:00:00Z",
      "last_updated": "2024-01-15T09:30:00Z",
      "waiting_minutes": 90,
      "assigned_to": "operator1",
      "action_url": "/worklists/usg?item_id=uuid"
    }
  ],
  "total_items": 5
}
```

**Response (Admin - Department Grouped):**
```json
{
  "scope": "department",
  "grouped_by_department": {
    "USG": [
      {
        "id": "uuid",
        "visit_id": "SV202401150001",
        ...
      }
    ],
    "OPD": [...]
  },
  "total_items": 12
}
```

### GET /api/dashboard/flow/

Returns step counts for Layer 3.

**Query Parameters:**
- `date`: Optional, defaults to "today" (server timezone)

**Response:**
```json
{
  "date": "2024-01-15",
  "server_time": "2024-01-15T10:30:00Z",
  "registered_count": 25,
  "paid_count": 23,
  "performed_count": 20,
  "reported_count": 18,
  "verified_count": 15
}
```

### GET /api/health/

Enhanced health check endpoint for dashboard health card.

**Response:**
```json
{
  "status": "ok",
  "server_time": "2024-01-15T10:30:00Z",
  "version": "abc123def",
  "checks": {
    "db": "ok",
    "storage": "ok"
  },
  "latency_ms": 5
}
```

**Status Values:**
- `ok`: All checks passing
- `degraded`: Some checks failing but service operational
- `down`: Critical failure (DB unreachable)

## Status Mappings

Dashboard uses the following status mappings from `ServiceVisitItem.status`:

- `REGISTERED` → "Registered" (initial state)
- `IN_PROGRESS` → "In Progress" / "Draft saved"
- `PENDING_VERIFICATION` → "Pending Verification" / "Submitted for verification"
- `RETURNED_FOR_CORRECTION` → "Returned for Correction"
- `FINALIZED` → "Finalized" (OPD workflow)
- `PUBLISHED` → "Published" / "Verified"
- `CANCELLED` → "Cancelled"

## Configuration

### Critical Delay Threshold

Default threshold is 4 hours. To change:

1. **Via API**: Pass `threshold_hours` query parameter to `/api/dashboard/summary/`
2. **Via Settings**: Update `DEFAULT_CRITICAL_DELAY_HOURS` in `backend/apps/workflow/dashboard_api.py`
3. **Via Environment**: (Future enhancement) Set `DASHBOARD_CRITICAL_DELAY_HOURS` environment variable

### Health Check Interval

Frontend polls `/api/health/` every 60 seconds. To change:

Update the interval in `frontend/src/views/Dashboard.tsx`:
```typescript
const interval = setInterval(loadHealth, 60000); // Change 60000 to desired milliseconds
```

## Navigation

All dashboard tiles and worklist items are clickable and navigate to:

1. **Existing list pages** with query parameters applied as filters
2. **Worklist pages** with item_id parameter to highlight specific items
3. **Registration page** for patient/service creation

## Permissions

All dashboard endpoints require authentication (`IsAuthenticated`).

- **Summary**: Available to all authenticated users
- **Worklist**: Role-based filtering enforced (admin vs non-admin)
- **Flow**: Available to all authenticated users
- **Health**: Public endpoint (no auth required) but enhanced for dashboard use

## Performance

- Dashboard data is computed on-demand from database queries
- No caching is implemented (all data is real-time)
- Queries are optimized with `select_related` and `prefetch_related`
- Worklist is limited to 100 items per request
- Health check has minimal latency overhead

## Troubleshooting

### Dashboard shows no data
- Check that visits and items exist in the database
- Verify user has appropriate permissions
- Check server logs for query errors

### Health card shows "down"
- Check database connectivity
- Verify `/api/health/` endpoint is accessible
- Check server logs for errors

### Worklist empty for non-admin
- Verify items are assigned to the user or created by the user
- Check that items are in work statuses (not PUBLISHED or CANCELLED)

### Critical delays not showing
- Verify threshold_hours setting
- Check that items have `started_at`, `submitted_at`, or `created_at` timestamps
- Verify items are in IN_PROGRESS or PENDING_VERIFICATION status

## Future Enhancements

- [ ] Configurable threshold via environment variable
- [ ] Dashboard caching with TTL
- [ ] Export dashboard data
- [ ] Customizable KPI tiles
- [ ] Historical trend charts
- [ ] Real-time updates via WebSocket
