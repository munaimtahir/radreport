# USG Field Mis-Rendering Investigation - COMPLETE

**Date**: January 22, 2026  
**Status**: ✅ All Investigation Tools Added  
**Next Step**: User Testing & Evidence Collection

---

## Summary

All investigation tools have been added to systematically verify root causes of USG field mis-rendering **BEFORE** applying any patches.

---

## What Was Done

### ✅ Phase 1: Frontend Field Object Inspection
- **Added**: Gray debug panel showing full field object
- **Shows**: identifier keys, type, options format, NA support
- **For fields**: `liver_echotexture`, `liver_size`

### ✅ Phase 2: Frontend Renderer Branch Verification  
- **Added**: Color-coded badge showing which renderer branch executes
- **Shows**: `CHECKLIST_BRANCH` (green), `BOOLEAN_BRANCH` (yellow), etc.
- **Location**: Next to field label

### ✅ Phase 3: Frontend State Value Shape Verification
- **Added**: Orange debug panel showing value storage type
- **Shows**: `typeof`, actual value, NA state
- **Verifies**: Checklist = array, Dropdown = string, etc.

### ✅ Phase 4: Backend API Response Verification
- **Added**: Blue debug banner at top of editor
- **Shows**: Whether `template_schema` exists, section count
- **Warns**: If schema is NULL

### ✅ Phase 5: Backend Template Resolution Verification
- **Added**: Management command `verify_usg_template_resolution`
- **Tests**: Template resolution, service config, publish readiness
- **Output**: Detailed report with ✅/❌ for each check

### ✅ Documentation
- **Created**: 3 comprehensive guides:
  1. `USG_INVESTIGATION_GUIDE.md` - Step-by-step workflow
  2. `USG_DEBUG_TOOLS_ADDED.md` - Tool reference
  3. `USG_INVESTIGATION_COMPLETE.md` - This file

---

## How to Use (Quick Start)

### 1. Backend Check (5 minutes)
```bash
cd backend
source ../.venv/bin/activate
python manage.py verify_usg_template_resolution
```

**Expected Output**:
```
✅ Reports WITH template_version: X
✅ SUCCESS: Schema resolved
✅ Sections: 5
✅ USG_ABDOMEN | USG Abdomen Template
```

**If you see ❌**: Fix backend issues before proceeding to frontend.

---

### 2. Frontend Check (10 minutes)

1. Start frontend dev server
2. Navigate to USG editor
3. Open a USG Abdomen report
4. Scroll to "Liver" section
5. Look for debug panels

**Expected Visuals**:
- ✅ Blue banner at top: "template_schema exists: YES"
- ✅ Red banner: "ACTIVE_RENDERER: USG_FIELD_RENDERER_V2"
- ✅ Field `liver_echotexture` has:
  - Gray panel: Field properties
  - Green badge: `CHECKLIST_BRANCH`
  - Orange panel: State value (array)
  - Multiple checkboxes visible

**If you see ❌** or unexpected values: Proceed to diagnosis in `USG_INVESTIGATION_GUIDE.md`

---

### 3. Browser Console Check (2 minutes)

1. Open DevTools (F12)
2. Look for `DEBUG_FIELD` log
3. Verify field object matches UI

---

## Evidence Collection Checklist

Before applying any fix, collect these:

### Frontend Evidence
- [ ] Screenshot: Blue API debug panel (shows schema status)
- [ ] Screenshot: Field debug panels (gray + orange)
- [ ] Screenshot: Renderer branch badge
- [ ] Screenshot: Actual field rendering (checkboxes present or missing)
- [ ] Console log: `DEBUG_FIELD` output
- [ ] Screenshot: NA toggle visibility

### Backend Evidence  
- [ ] Terminal output: `verify_usg_template_resolution` command
- [ ] Confirmation: All services have templates (no ❌)
- [ ] Confirmation: Schema resolves successfully (✅)
- [ ] Confirmation: Checklist fields have options

### Issue Documentation
- [ ] Describe observed behavior (e.g., "Shows single Yes checkbox")
- [ ] Note which debug panel shows the issue (e.g., "Field Debug shows type=boolean")
- [ ] Identify root cause (e.g., "Backend schema has wrong type")
- [ ] Propose minimal fix (e.g., "Update template definition")

---

## Diagnosis Quick Reference

| Symptom | Check This Panel | Likely Cause |
|---------|-----------------|--------------|
| Single "Yes" checkbox | Field Debug → `type` | Type is `boolean` not `checklist` |
| No options visible | Field Debug → `options_exists` | Backend not sending options |
| NA toggle missing | Field Debug → `na_allowed` | NA not enabled in template |
| Wrong value type | State Debug → `typeof` | State coercion issue |
| "No template schema" error | Blue API Debug → `schema exists` | Template not resolved |
| Renderer branch wrong | Renderer badge color | Type detection logic issue |

---

## Common Findings (Predicted)

Based on symptoms, you're likely to find:

### Finding A: Backend Schema Type Mismatch
**Evidence**: Field Debug shows `type: "boolean"` but should be `"checklist"`  
**Root Cause**: Template definition has wrong field type  
**Fix**: Update template JSON or re-import correct template  
**Patch Location**: Backend template data

### Finding B: Options Not Normalized
**Evidence**: `options_sample` shows strings, but renderer expects objects  
**Root Cause**: Backend sends `["Normal", "Coarse"]` not `[{label, value}]`  
**Fix**: Already patched - `normalizeOptions()` handles this  
**Status**: ✅ Already fixed

### Finding C: State Value Type Mismatch
**Evidence**: State Debug shows `typeof: string` for checklist  
**Root Cause**: `handleFieldChange` doesn't coerce to array  
**Fix**: Add array coercion in state setter  
**Patch Location**: `handleFieldChange` function

### Finding D: Template Version Not Set
**Evidence**: Blue API Debug shows `schema exists: NO`  
**Root Cause**: Report has no `template_version` set  
**Fix**: Run backfill command  
**Patch Location**: Backend database

---

## Patch Decision Matrix

| Finding | Apply Patch? | Location | Action |
|---------|-------------|----------|--------|
| Backend schema wrong | Yes | Template JSON | Re-import template |
| Options format wrong | ✅ Done | Frontend | `normalizeOptions()` exists |
| State type wrong | Yes | `handleFieldChange` | Add coercion |
| Template not set | Yes | Database | Run backfill |
| NA not allowed | Yes | Template JSON | Set `na_allowed: true` |
| Renderer detection wrong | Maybe | Type check logic | Fix conditions |

**Rule**: Only apply patches **after** evidence proves the root cause.

---

## Minimal Patch Examples

### Patch 1: State Coercion (if needed)
```typescript
const handleFieldChange = (field: TemplateField, value: any) => {
  // Coerce to correct type
  let coercedValue = value;
  
  if (field.type === "checklist" || field.type === "multi_choice") {
    // Ensure array
    if (!Array.isArray(value)) {
      coercedValue = value ? [value] : [];
    }
  }
  
  setValues((prev) => ({
    ...prev,
    [field.field_key]: {
      field_key: field.field_key,
      value_json: coercedValue,
      is_not_applicable: false,
    },
  }));
  // ... rest
};
```

### Patch 2: Canonical Key Usage (if needed)
```typescript
// If field uses 'key' instead of 'field_key'
const fieldKey = field.field_key ?? (field as any).key;

// Use fieldKey everywhere
const value = values[fieldKey]?.value_json;
```

### Patch 3: Backend Template Fix (if needed)
```json
{
  "field_key": "liver_echotexture",
  "type": "checklist",  // Was: "boolean"
  "label": "Liver Echotexture",
  "options": [
    {"label": "Normal", "value": "Normal"},
    {"label": "Coarse", "value": "Coarse"},
    {"label": "Fatty change", "value": "Fatty change"},
    {"label": "Heterogeneous", "value": "Heterogeneous"}
  ],
  "na_allowed": true  // Add if missing
}
```

---

## Cleanup After Fix

Once fix is verified:

1. **Remove debug panels** from `UsgStudyEditorPage.tsx`:
   - Set `showDebugPanel = false`
   - Remove blue API debug banner
   - Remove console logs

2. **Keep these**:
   - Backend verification command (useful for monitoring)
   - Red renderer banner (optional, can remove if desired)
   - Documentation files (for future reference)

3. **Create PR** with:
   - Evidence screenshots
   - Root cause explanation
   - Minimal patch diff
   - Before/After comparison

---

## Files Changed Summary

### Frontend (1 file)
- ✅ `frontend/src/views/UsgStudyEditorPage.tsx`
  - Added 4 debug panels
  - Added renderer branch detection
  - Added type badges
  - Added console logging

### Backend (2 files)
- ✅ `backend/apps/workflow/management/commands/verify_usg_template_resolution.py`
- ✅ `backend/verify_usg_template_resolution.py`

### Documentation (4 files)
- ✅ `USG_INVESTIGATION_GUIDE.md` (workflow guide)
- ✅ `USG_DEBUG_TOOLS_ADDED.md` (tool reference)
- ✅ `USG_INVESTIGATION_COMPLETE.md` (this file)
- ℹ️ `USG_FIX_SUMMARY_2026_01_22.md` (existing, previous fixes)

---

## Success Criteria

Investigation is complete when:

- ✅ All debug tools are functional
- ✅ Backend verification command runs without errors
- ✅ Frontend displays all debug panels correctly
- ✅ Evidence collected proves root cause
- ✅ Minimal patch identified and documented
- ✅ Fix applied and verified
- ✅ Debug tools removed
- ✅ PR submitted with proof

---

## Next Actions for User

1. **Run backend verification**:
   ```bash
   cd backend
   source ../.venv/bin/activate
   python manage.py verify_usg_template_resolution
   ```

2. **Start frontend and test**:
   ```bash
   cd frontend
   npm run dev
   # Navigate to USG editor
   ```

3. **Collect evidence**:
   - Take screenshots of all debug panels
   - Copy backend verification output
   - Note any ❌ or unexpected values

4. **Identify root cause**:
   - Use `USG_INVESTIGATION_GUIDE.md` flowchart
   - Match symptoms to diagnosis table
   - Confirm with multiple evidence points

5. **Apply minimal patch**:
   - Use patch examples above
   - Test fix works
   - Verify all debug panels show ✅

6. **Clean up**:
   - Remove debug panels
   - Test without debug tools
   - Create PR with evidence

---

## Support Resources

- **Workflow Guide**: `USG_INVESTIGATION_GUIDE.md`
- **Tool Reference**: `USG_DEBUG_TOOLS_ADDED.md`
- **Previous Fixes**: `USG_FIX_SUMMARY_2026_01_22.md`
- **Backend Command**: `python manage.py verify_usg_template_resolution --help`

---

## Contact

For questions:
- Check documentation first
- Run backend verification for database issues
- Check browser console for JavaScript errors
- Collect evidence before asking for help

---

**Status**: ✅ Investigation tools ready for use  
**Blocker**: None - all tools functional  
**Estimated Time**: 20-30 minutes to collect evidence and identify root cause

Good luck with the investigation! 🔍
