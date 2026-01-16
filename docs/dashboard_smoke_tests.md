# Dashboard v1 Smoke Test Checklist

This document provides a comprehensive smoke test checklist for Dashboard v1 implementation.

## Prerequisites

1. Backend server running on port 8000 (or configured port)
2. Frontend dev server running on port 5173 (or configured port)
3. Database with test data:
   - At least one patient
   - At least one service visit with items
   - At least one user with admin role
   - At least one user with non-admin role

## Backend Smoke Tests

### Test 1: Health Endpoint
```bash
curl http://localhost:8000/api/health/
```
**Expected:**
- Status code: 200 (or 503 if DB down)
- Response includes: `status`, `server_time`, `checks`, `latency_ms`
- `checks.db` is "ok" when DB is reachable

### Test 2: Dashboard Summary (Unauthenticated)
```bash
curl http://localhost:8000/api/dashboard/summary/
```
**Expected:**
- Status code: 401 (Unauthorized)

### Test 3: Dashboard Summary (Authenticated)
```bash
# Get token first
TOKEN=$(curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | jq -r '.access')

# Test summary endpoint
curl http://localhost:8000/api/dashboard/summary/ \
  -H "Authorization: Bearer $TOKEN"
```
**Expected:**
- Status code: 200
- Response includes: `total_patients_today`, `total_services_today`, `reports_pending`, `reports_verified`, `critical_delays`
- All counts are non-negative integers

### Test 4: Dashboard Worklist - Admin (Department Scope)
```bash
curl "http://localhost:8000/api/dashboard/worklist/?scope=department" \
  -H "Authorization: Bearer $TOKEN"
```
**Expected:**
- Status code: 200
- Response includes: `scope: "department"`
- Response includes: `grouped_by_department` OR `items`
- If `grouped_by_department` exists, it's an object with department keys

### Test 5: Dashboard Worklist - Non-Admin (My Scope)
```bash
# Get token for non-admin user
TOKEN_REGULAR=$(curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"regular_user","password":"test"}' | jq -r '.access')

curl "http://localhost:8000/api/dashboard/worklist/?scope=my" \
  -H "Authorization: Bearer $TOKEN_REGULAR"
```
**Expected:**
- Status code: 200
- Response includes: `scope: "my"`
- Response includes: `items` array
- Items are filtered to user's assigned/created items only

### Test 6: Dashboard Worklist - Non-Admin (Department Scope - Should Fail)
```bash
curl "http://localhost:8000/api/dashboard/worklist/?scope=department" \
  -H "Authorization: Bearer $TOKEN_REGULAR"
```
**Expected:**
- Status code: 400
- Response includes error message about invalid scope

### Test 7: Dashboard Flow
```bash
curl "http://localhost:8000/api/dashboard/flow/" \
  -H "Authorization: Bearer $TOKEN"
```
**Expected:**
- Status code: 200
- Response includes: `registered_count`, `paid_count`, `performed_count`, `reported_count`, `verified_count`
- All counts are non-negative integers

### Test 8: Backend Unit Tests
```bash
cd backend
python manage.py test apps.workflow.tests.DashboardAPITests
```
**Expected:**
- All tests pass
- No errors or failures

## Frontend Smoke Tests

### Test 9: Dashboard Renders
1. Navigate to `http://localhost:5173/`
2. Login with admin credentials
3. Verify dashboard loads without errors

**Expected:**
- Dashboard page renders
- No console errors
- All 5 layers visible

### Test 10: Layer 1 - KPI Tiles
1. Verify all 5 KPI tiles are visible
2. Check that numbers are displayed (can be 0)
3. Click each tile

**Expected:**
- 5 tiles: Total Patients, Total Services, Reports Pending, Reports Verified, Critical Delays
- Each tile is clickable
- Clicking navigates to appropriate filtered list page
- No 404 errors

### Test 11: Layer 2 - Admin Sees Department Worklists
1. Login as admin user
2. Check Layer 2 section

**Expected:**
- Title shows "Department Worklists"
- Worklists grouped by department (USG, OPD, etc.)
- Each department shows count of items
- Table with columns: Patient, Service, Status, Waiting, Action
- Items are clickable

### Test 12: Layer 2 - Non-Admin Sees My Worklist
1. Login as non-admin user
2. Check Layer 2 section

**Expected:**
- Title shows "My Worklist"
- Single table (not grouped by department)
- Only shows items assigned to or created by current user
- Table with same columns as admin view

### Test 13: Layer 3 - Today's Flow
1. Verify all 5 flow steps are visible
2. Check that counts are displayed

**Expected:**
- 5 steps: Registered, Paid, Performed, Reported, Verified
- Each step shows a count
- Steps are connected with arrows (→)
- All counts are non-negative integers

### Test 14: Layer 4 - Alerts & System Health
1. Check Alerts card
2. Check System Health card

**Expected:**
- Alerts card shows active alerts (if any)
- System Health card shows:
  - Backend API status (ok/degraded/down)
  - Database status (ok/fail)
  - Network status (online/offline)
  - Version (if available)
  - Last checked time
- Health status updates every 60 seconds

### Test 15: Layer 5 - Shortcuts
1. Verify shortcuts are visible
2. Click each shortcut

**Expected:**
- Up to 5 shortcuts displayed
- Common shortcuts: New Registration, Search Patient, USG Worklist, Verification
- Admin sees additional: Templates Manager
- Each shortcut navigates to correct route
- No 404 errors

### Test 16: Health Polling
1. Open browser DevTools → Network tab
2. Wait 60+ seconds
3. Check for periodic `/api/health/` requests

**Expected:**
- Health endpoint called every 60 seconds
- Health card updates with new status
- Last checked time updates

### Test 17: Network Status Monitoring
1. Open browser DevTools → Network tab
2. Toggle "Offline" mode
3. Check System Health card

**Expected:**
- Network status changes to "OFFLINE"
- Status color changes to red
- When back online, status updates to "ONLINE"

### Test 18: Worklist Item Navigation
1. Click on a worklist item
2. Verify navigation

**Expected:**
- Item is clickable
- Navigates to correct worklist page (USG/OPD/Verification)
- URL includes `item_id` parameter
- Page loads without errors

### Test 19: Error Handling
1. Stop backend server
2. Refresh dashboard
3. Check error display

**Expected:**
- Error alert/message displayed
- Health card shows "down" status
- Dashboard gracefully handles errors
- No unhandled exceptions in console

### Test 20: Role-Based Access
1. Login as admin → verify department worklists
2. Logout
3. Login as non-admin → verify my worklist only
4. Try to access department scope via API (should fail)

**Expected:**
- Admin sees department worklists
- Non-admin sees only my worklist
- Non-admin cannot access department scope via API (400 error)

## Integration Tests

### Test 21: End-to-End Dashboard Flow
1. Create a new patient via Registration page
2. Create a service visit with USG service
3. Navigate to Dashboard
4. Verify:
   - Total Patients Today increased
   - Total Services Today increased
   - New item appears in worklist (if assigned to current user)

**Expected:**
- Dashboard reflects new data
- Counts update correctly
- Worklist shows new items

### Test 22: Status Transitions
1. Create a service visit item in IN_PROGRESS
2. Submit for verification (moves to PENDING_VERIFICATION)
3. Check dashboard:
   - Reports Pending count increases
   - Item appears in worklist with correct status
4. Verify and publish (moves to PUBLISHED)
5. Check dashboard:
   - Reports Verified count increases
   - Item no longer in worklist (published items excluded)

**Expected:**
- Dashboard reflects status changes
- Counts update correctly
- Worklist filters correctly

### Test 23: Critical Delays
1. Create a service visit item
2. Manually set `started_at` to 5 hours ago (via admin or direct DB)
3. Check dashboard Critical Delays count

**Expected:**
- Critical Delays count includes the item
- Item appears in worklist
- Waiting time shows correctly

## Regression Tests

### Test 24: Existing Routes Not Broken
1. Test existing routes:
   - `/registration`
   - `/worklists/usg`
   - `/worklists/verification`
   - `/reports`
   - `/templates`

**Expected:**
- All existing routes work
- No 404 errors
- No broken functionality

### Test 25: Existing API Endpoints Not Broken
1. Test existing endpoints:
   - `GET /api/patients/`
   - `GET /api/workflow/visits/`
   - `GET /api/workflow/items/`
   - `POST /api/workflow/usg/`

**Expected:**
- All existing endpoints work
- No 500 errors
- Response formats unchanged

## Performance Tests

### Test 26: Dashboard Load Time
1. Open browser DevTools → Network tab
2. Navigate to dashboard
3. Check load time

**Expected:**
- Dashboard loads in < 2 seconds
- All API calls complete successfully
- No timeout errors

### Test 27: Health Polling Performance
1. Monitor health polling for 5 minutes
2. Check for performance issues

**Expected:**
- Health polling doesn't cause performance degradation
- No memory leaks
- Polling interval consistent (60s)

## Checklist Summary

- [ ] Test 1: Health Endpoint
- [ ] Test 2: Dashboard Summary (Unauthenticated)
- [ ] Test 3: Dashboard Summary (Authenticated)
- [ ] Test 4: Dashboard Worklist - Admin (Department Scope)
- [ ] Test 5: Dashboard Worklist - Non-Admin (My Scope)
- [ ] Test 6: Dashboard Worklist - Non-Admin (Department Scope - Should Fail)
- [ ] Test 7: Dashboard Flow
- [ ] Test 8: Backend Unit Tests
- [ ] Test 9: Dashboard Renders
- [ ] Test 10: Layer 1 - KPI Tiles
- [ ] Test 11: Layer 2 - Admin Sees Department Worklists
- [ ] Test 12: Layer 2 - Non-Admin Sees My Worklist
- [ ] Test 13: Layer 3 - Today's Flow
- [ ] Test 14: Layer 4 - Alerts & System Health
- [ ] Test 15: Layer 5 - Shortcuts
- [ ] Test 16: Health Polling
- [ ] Test 17: Network Status Monitoring
- [ ] Test 18: Worklist Item Navigation
- [ ] Test 19: Error Handling
- [ ] Test 20: Role-Based Access
- [ ] Test 21: End-to-End Dashboard Flow
- [ ] Test 22: Status Transitions
- [ ] Test 23: Critical Delays
- [ ] Test 24: Existing Routes Not Broken
- [ ] Test 25: Existing API Endpoints Not Broken
- [ ] Test 26: Dashboard Load Time
- [ ] Test 27: Health Polling Performance

## Notes

- All tests should pass before considering Dashboard v1 complete
- If any test fails, document the issue and fix before deployment
- Performance tests are optional but recommended for production readiness
