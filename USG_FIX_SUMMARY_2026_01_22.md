# USG Template Rendering & Verification Fix Summary
**Date**: January 22, 2026  
**Issue**: USG template renderer not interpreting JSON correctly + verification/publish fails with template schema error

---

## PART 1: Frontend Fixes (UsgStudyEditorPage.tsx)

### 1.1 Active Renderer Identified
**File**: `frontend/src/views/UsgStudyEditorPage.tsx`

**Proof Marker Added** (Lines 621-624):
```tsx
<div style={{position:"sticky", top:0, zIndex:9999, background:"#fff", border:"2px solid red", padding:6, marginBottom: 12}}>
  ACTIVE_RENDERER: USG_FIELD_RENDERER_V2
</div>
```
This red banner will be visible at the top of the USG editor form to confirm the correct renderer is active.

### 1.2 Runtime Field Logging
**Debug Log Added** (Lines 647-649):
```tsx
if (field.field_key === "liver_echotexture") {
  console.log("DEBUG_FIELD", field);
}
```
This will log the full field object including options structure to browser console.

### 1.3 normalizeOptions Helper Function
**Added** (Lines 84-94):
```tsx
function normalizeOptions(options?: any[]): { label: string; value: any }[] {
  if (!Array.isArray(options)) return [];
  return options
    .map((opt) => {
      if (!opt) return null;
      if (typeof opt === "string") return { label: opt, value: opt };
      if (typeof opt === "object" && opt.label != null && opt.value != null) return opt;
      if (typeof opt === "object" && opt.value != null) return { label: String(opt.value), value: opt.value };
      return null;
    })
    .filter(Boolean) as { label: string; value: any }[];
}
```
This ensures consistent `{label, value}` format for all field options.

### 1.4 Checklist Rendering Fixed
**Applied normalizeOptions** (Line 750):
- Changed from `(field.options || [])` to `normalizeOptions(field.options)`
- Checklist now correctly renders multiple checkboxes from `field.options[]`
- Layout: `display: flex, flexWrap: wrap, gap: 12` for horizontal wrapping

### 1.5 Dropdown Rendering Fixed
**Applied normalizeOptions** (Line 687):
- Changed from `(field.options || [])` to `normalizeOptions(field.options)`
- Dropdown now correctly renders `<select>` with options from `field.options[]`

### 1.6 N/A Toggle Behavior
**Already Correctly Implemented**:
- N/A checkbox visible for fields with `na_allowed: true` (Lines 656-666)
- Auto-uncheck on user input: `handleFieldChange` sets `is_not_applicable: false` (Line 296)
- Payload omission: Save logic skips fields where `is_not_applicable: true` (Lines 344-346)

### 1.7 Rules.show_if Support
**Already Working**: Dependent field visibility logic remains intact.

---

## PART 2: Backend Fixes (Template Resolution)

### 2.1 Error Source Located
**File**: `backend/apps/usg/services.py` (Line 43)
- This is the OLD USG module at `/api/usg/`
- The frontend uses the NEW workflow module at `/api/workflow/usg/`
- The error is not directly triggered by the frontend workflow

**Workflow Module Files**:
- `backend/apps/workflow/models.py` - USGReport model
- `backend/apps/workflow/api.py` - USGReportViewSet (publish/finalize)
- `backend/apps/workflow/serializers.py` - USGReportSerializer

### 2.2 Template Resolution Function Created
**New File**: `backend/apps/workflow/template_resolution.py`

**Functions**:
1. `resolve_template_schema_for_report(report)`:
   - Returns template schema JSON
   - Auto-resolves from service if missing
   - Backfills `report.template_version` if found
   - Raises ValidationError with clear message if cannot resolve

2. `ensure_template_for_report(report)`:
   - Ensures report has `template_version` set
   - Auto-resolves and saves if missing
   - Raises ValidationError if cannot resolve

### 2.3 Serializer Updated
**File**: `backend/apps/workflow/serializers.py` (Lines 203-218)
- `get_template_schema()` now calls `resolve_template_schema_for_report()`
- Auto-resolves template schema for reports without `template_version`
- Returns None gracefully if resolution fails (logs warning)
- Frontend receives valid schema or null (can handle both)

### 2.4 Publish & Finalize Endpoints Updated
**File**: `backend/apps/workflow/api.py`

**Changes**:
- `publish()` action (Lines 904-911): Calls `ensure_template_for_report()` before validation
- `finalize()` action (Lines 806-813): Calls `ensure_template_for_report()` before validation
- Returns clear 400 error if template cannot be resolved

### 2.5 Template Assignment at Creation
**Already Working** (Lines 577-587 in api.py):
- Report creation requires `service.default_template`
- Returns 400 error BEFORE creating report if template missing
- Template version is set from service profile mapping
- All new reports created through workflow API have `template_version`

### 2.6 Management Command for Legacy Reports
**New File**: `backend/apps/workflow/management/commands/backfill_usg_template_versions.py`

**Usage**:
```bash
# Dry run
python manage.py backfill_usg_template_versions --dry-run

# Actual backfill
python manage.py backfill_usg_template_versions
```

**What it does**:
- Finds USG reports without `template_version`
- Resolves template from `service.default_template`
- Backfills `report.template_version` field
- Reports on success/failure for each report

---

## VERIFICATION CHECKLIST

### Frontend Smoke Tests
✅ On USG Abdomen editor:
- [ ] Red banner "ACTIVE_RENDERER: USG_FIELD_RENDERER_V2" visible at top
- [ ] Liver echotexture shows multiple options (Normal, Coarse, Fatty change, Heterogeneous)
- [ ] Options displayed horizontally with wrap
- [ ] N/A checkbox appears before liver echotexture and liver size fields
- [ ] Typing in liver size field auto-unchecks N/A
- [ ] Console logs "DEBUG_FIELD" for liver_echotexture field

### Backend Smoke Tests
✅ Template Resolution:
```python
from apps.workflow.models import USGReport
from apps.workflow.template_resolution import resolve_template_schema_for_report

# Get any USG report
report = USGReport.objects.first()

# Should return schema dict or raise ValidationError with clear message
schema = resolve_template_schema_for_report(report)
print("Schema sections:", len(schema.get("sections", [])))
```

✅ Publish/Finalize:
1. Create new USG abdomen report/study
2. Save draft with some fields
3. Submit for verification
4. Publish/Finalize:
   - Must NOT throw "No template schema..." error
   - Should succeed or return clear 400 error
5. Verify PDF generated successfully

---

## FILES CHANGED

### Frontend
1. `frontend/src/views/UsgStudyEditorPage.tsx`
   - Added `normalizeOptions()` helper function
   - Added red banner proof marker
   - Added debug logging for liver_echotexture
   - Updated dropdown rendering to use `normalizeOptions()`
   - Updated radio button rendering to use `normalizeOptions()`
   - Updated checklist rendering to use `normalizeOptions()`

### Backend
2. `backend/apps/workflow/template_resolution.py` (NEW)
   - `resolve_template_schema_for_report()` function
   - `ensure_template_for_report()` function

3. `backend/apps/workflow/serializers.py`
   - Updated `get_template_schema()` to auto-resolve

4. `backend/apps/workflow/api.py`
   - Updated `publish()` action to call `ensure_template_for_report()`
   - Updated `finalize()` action to call `ensure_template_for_report()`

5. `backend/apps/workflow/management/commands/backfill_usg_template_versions.py` (NEW)
   - Management command to fix legacy reports

---

## KNOWN ISSUES / NOTES

1. **Old USG Module**: The `/api/usg/` module still exists and has its own error messages. It's not used by the frontend but is registered in URLs. Consider deprecating or documenting.

2. **Template Assignment**: Reports created through workflow API always have `template_version` set (enforced at creation). Only legacy reports or reports from migrations might be missing it.

3. **Service Configuration**: If a service doesn't have `default_template` configured, report creation will fail with 400 error. This is intentional to prevent orphaned reports.

4. **Console Logs**: Remember to remove debug console.log statements after verification.

---

## DEPLOYMENT STEPS

1. **Deploy Frontend**:
   ```bash
   cd frontend
   npm run build
   # Deploy built assets
   ```

2. **Deploy Backend**:
   ```bash
   cd backend
   python manage.py migrate  # If any migrations
   python manage.py collectstatic --noinput
   # Restart backend service
   ```

3. **Run Backfill** (if needed):
   ```bash
   python manage.py backfill_usg_template_versions --dry-run
   python manage.py backfill_usg_template_versions
   ```

4. **Verify**:
   - Test USG editor with Abdomen template
   - Test publish/finalize workflow
   - Check browser console for any errors

---

## SUCCESS CRITERIA

✅ **Frontend**:
- Checklist fields render as multiple checkboxes (not single "Yes")
- Dropdown fields render as select with all options
- N/A toggle visible for `na_allowed` fields
- N/A auto-unchecks when user types/selects
- Checklist options display horizontally with wrap
- Red banner proof marker visible

✅ **Backend**:
- Publish/finalize succeeds without "No template schema..." error
- Template schema always resolves or fails with clear message
- Legacy reports can be backfilled with template_version
- PDF generation succeeds for published reports

---

## CONTACT

For issues or questions:
- Frontend: Check browser console for DEBUG_FIELD logs
- Backend: Check Django logs for template resolution warnings
- Run backfill command for legacy report issues
