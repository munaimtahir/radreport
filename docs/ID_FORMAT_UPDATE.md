# ID Format Update Summary

## Overview
Successfully updated the patient registration number and visit ID formats for the RIMS application.

## Changes Made

### 1. Patient Registration Number Format
**Previous Format:** `PRN000001`
**New Format:** `CCJ-26-0001`

**Format Breakdown:**
- **CCJ** = Consultant Clinic Jaranwala (clinic identifier)
- **yy** = Year (2-digit, e.g., "26" for 2026)
- **nnnn** = Sequential number (4 digits, resets yearly)

**Examples:**
- First patient in 2026: `CCJ-26-0001`
- 31st patient in 2026: `CCJ-26-0031`
- 100th patient in 2026: `CCJ-26-0100`
- First patient in 2027: `CCJ-27-0001` (resets yearly)

**File Modified:** `/home/munaim/srv/apps/radreport/backend/apps/patients/models.py`
- Updated `generate_patient_reg_no()` method
- Now filters by year prefix to ensure yearly reset
- Maintains uniqueness and race condition handling

### 2. Visit ID Format
**Previous Format:** `SV20260120-0001` (daily reset)
**New Format:** `2601-001` (monthly reset)

**Format Breakdown:**
- **yy** = Year (2-digit, e.g., "26" for 2026)
- **mm** = Month (2-digit, e.g., "01" for January)
- **nnn** = Sequential number (3 digits, resets monthly on 1st)

**Examples:**
- First visit in Jan 2026: `2601-001`
- 23rd visit in Jan 2026: `2601-023`
- First visit in Feb 2026: `2602-001` (resets monthly)
- First visit in Dec 2026: `2612-001`
- First visit in Jan 2027: `2701-001`

**File Modified:** `/home/munaim/srv/apps/radreport/backend/apps/workflow/models.py`
- Updated `generate_visit_id()` method in `ServiceVisit` model
- Changed from daily to monthly reset
- Shortened format from 14 characters to 8 characters

## Deployment

### Backend Rebuilt
- Stopped and removed old backend container
- Rebuilt backend image with `--no-cache` flag
- Started new backend container
- All migrations applied successfully
- Superuser credentials preserved: `admin / admin123`

### Verification Results
✅ Patient Registration Number: `CCJ-26-0001` - Format CORRECT
✅ Visit ID: `2601-001` - Format CORRECT

## Database Impact

### Existing Records
- Existing patient registration numbers and visit IDs remain unchanged
- New format only applies to newly created records
- No data migration required

### Field Constraints
Both fields maintain their existing constraints:
- `patient_reg_no`: CharField(max_length=30, unique=True, editable=False)
- `visit_id`: CharField(max_length=30, unique=True, editable=False)

The new formats are well within the 30-character limit:
- Patient Reg No: 12 characters (e.g., "CCJ-26-0001")
- Visit ID: 8 characters (e.g., "2601-001")

## Frontend Impact

### No Frontend Changes Required
The frontend already handles these fields as strings and displays them as-is. The format change is transparent to the frontend:
- Registration forms will show the new format
- Search functionality continues to work
- Display components require no updates

### Areas That Display These IDs
- Patient registration page
- Visit/service registration
- Receipts and invoices
- Reports (USG, OPD)
- Search results
- Admin interface

All these areas will automatically show the new format for new records.

## Testing Recommendations

1. **Create a New Patient**
   - Navigate to patient registration
   - Create a new patient
   - Verify the patient_reg_no shows format: `CCJ-26-XXXX`

2. **Create a New Visit**
   - Register a service for any patient
   - Verify the visit_id shows format: `YYMM-XXX`

3. **Monthly Reset Verification**
   - On the 1st of next month, create a new visit
   - Verify the sequential number resets to 001

4. **Yearly Reset Verification**
   - On January 1st, 2027, create a new patient
   - Verify the registration number shows: `CCJ-27-0001`

## Rollback Plan (If Needed)

If you need to revert to the old format:

1. Restore the original methods in:
   - `/home/munaim/srv/apps/radreport/backend/apps/patients/models.py`
   - `/home/munaim/srv/apps/radreport/backend/apps/workflow/models.py`

2. Rebuild the backend:
   ```bash
   cd /home/munaim/srv/apps/radreport
   ./backend.sh
   ```

## Notes

- The change is backward compatible (old records remain valid)
- No database migration required
- Format is more compact and human-readable
- Monthly reset for visits reduces number length
- Yearly reset for patients keeps numbers manageable
- Both formats include date context (year/month)
