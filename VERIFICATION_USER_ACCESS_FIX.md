# Verification User Access Fix

## Problem
Verification users were unable to access workflow pages even though permissions were configured.

## Changes Made

### 1. Frontend Route Protection
- Added explicit permission checks to workflow routes:
  - `/reporting/worklist` - Now requires `canWorkflow` permission
  - `/reporting/worklist/:id/report` - Now requires `canWorkflow` permission  
  - `/reports` - Now requires `canWorkflow` permission
- Dashboard remains accessible to all authenticated users

### 2. Debug Logging
- Added console logging to help troubleshoot group assignment issues
- Logs user groups, superuser status, and full user object when user loads

### 3. Group Name Normalization
- `/auth/me/` endpoint normalizes group names to lowercase
- Backend permissions check group names case-insensitively
- Handles variations: "Verification", "verification", "verification_desk"

## Verification Steps

### 1. Check User Groups in Django Admin
1. Go to Django Admin: `/admin/auth/user/`
2. Find your verification user
3. Check the "Groups" section
4. Ensure the user has one of these groups assigned:
   - `Verification` (capitalized)
   - `verification` (lowercase)
   - `verification_desk` (with suffix)

### 2. Check Browser Console
1. Open browser Developer Tools (F12)
2. Go to Console tab
3. Look for debug logs showing:
   ```
   [DEBUG] User groups: ["verification"]
   [DEBUG] User is superuser: false
   [DEBUG] User object: {...}
   ```
4. Verify that "verification" appears in the groups array

### 3. Test Access
After logging in as a verification user, you should be able to access:
- ✅ Dashboard (`/`)
- ✅ Registration (`/registration`)
- ✅ Patient Workflow (`/patients/workflow`)
- ✅ Reporting Worklist (`/reporting/worklist`)
- ✅ Print Reports (`/reports`)

### 4. Check Navigation Menu
The sidebar should show these links under "WORKFLOW":
- Registration
- Patient workflow
- Reporting worklist
- Print reports

## Troubleshooting

### If user still can't access pages:

1. **Check Group Assignment**
   ```python
   # In Django shell: python manage.py shell
   from django.contrib.auth.models import User, Group
   user = User.objects.get(username='your_username')
   print("Groups:", [g.name for g in user.groups.all()])
   ```

2. **Verify /auth/me/ Returns Groups**
   - Open browser Network tab
   - Look for `/api/auth/me/` request
   - Check response JSON - should have `groups: ["verification"]`

3. **Check Backend Logs**
   - Look for any permission denied errors
   - Verify backend is recognizing the verification group

4. **Clear Browser Cache**
   - Clear localStorage: `localStorage.clear()`
   - Log out and log back in
   - Check if groups are now recognized

## Expected Behavior

A verification user should:
- ✅ See all workflow navigation links
- ✅ Access all workflow pages
- ✅ Perform all workflow transitions
- ✅ Verify, publish, and return reports
- ✅ Create service visits (registration)

## Group Name Compatibility

The system now recognizes these group name variations (case-insensitive):
- `Verification` / `verification` / `VERIFICATION`
- `verification_desk` / `Verification_Desk`

All variations map to the same permissions.
