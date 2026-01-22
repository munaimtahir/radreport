# USG Field Mis-Rendering Debug Tools - Implementation Summary

**Date**: January 22, 2026  
**Status**: Investigation Tools Added (No Patches Applied Yet)

---

## What Was Added

This document summarizes all debug tools added to systematically investigate USG field mis-rendering issues **before** applying any fixes.

---

## Frontend Debug Tools

### File: `frontend/src/views/UsgStudyEditorPage.tsx`

#### 1. Backend API Response Debug Panel (Lines ~520-560)

**Location**: Top of editor page, below error/success banners

**Appearance**: Blue banner with "🔧 BACKEND API DEBUG (PHASE 4)"

**What It Shows**:
- Whether `template_schema` exists or is NULL
- Number of sections in schema
- Whether `template_detail` exists
- Report status and service code
- API endpoint being used
- Warning if schema is NULL

**Purpose**: Verify the editor receives valid schema from backend API.

**Screenshot Checklist**:
- [ ] Blue debug panel visible
- [ ] Shows "template_schema exists: ✅ YES" or "❌ NULL"
- [ ] Shows section count > 0
- [ ] No red warning about NULL schema

---

#### 2. Field Debug Panel (Lines ~685-720)

**Location**: Below field label for `liver_echotexture` and `liver_size`

**Appearance**: Gray box with "🔍 FIELD DEBUG PANEL"

**What It Shows** (as JSON):
```json
{
  "identifier_key": "liver_echotexture",
  "identifier_key_alt": null,
  "type": "checklist",
  "na_allowed": true,
  "supports_not_applicable": true,
  "options_exists": true,
  "options_length": 4,
  "options_sample": ["Normal", "Coarse", "Fatty change"],
  "normalized_options": [
    {"label": "Normal", "value": "Normal"},
    ...
  ]
}
```

**Purpose**: 
- Verify which identifier is used (`key` vs `field_key`)
- Confirm field type matches template
- Verify options exist and are in correct format
- Check NA support flags

**Verification Points**:
- [ ] `identifier_key` has a value (not null)
- [ ] `type` matches expected (e.g., "checklist" for multi-select)
- [ ] `options_exists: true`
- [ ] `options_length` > 0
- [ ] `normalized_options` has `{label, value}` format

---

#### 3. Renderer Branch Badge (Line ~686)

**Location**: Next to field label in parentheses

**Appearance**: 
- Green pill: `CHECKLIST_BRANCH` (for multi-select)
- Yellow pill: Other branches (`DROPDOWN_BRANCH`, `BOOLEAN_BRANCH`, etc.)

**What It Shows**: Which renderer code path is executing

**Purpose**: Verify correct UI component is selected for field type

**Verification Points**:
- [ ] Checklist fields show `CHECKLIST_BRANCH` (green)
- [ ] Dropdown fields show `DROPDOWN_BRANCH`
- [ ] Boolean fields show `BOOLEAN_BRANCH`
- [ ] Badge matches actual UI rendered below

---

#### 4. State Value Debug Panel (Lines ~725-735)

**Location**: Below field debug panel, for `liver_echotexture` and `liver_size`

**Appearance**: Orange box with "📦 STATE VALUE DEBUG"

**What It Shows**:
```
value typeof: array
value: ["Normal", "Coarse"]
is_not_applicable: false
```

**Purpose**: Verify value is stored in correct data type

**Verification Points**:
- [ ] Checklist: `typeof: array`
- [ ] Dropdown: `typeof: string`
- [ ] Boolean: `typeof: boolean`
- [ ] Number: `typeof: number`
- [ ] Value matches expected format

---

#### 5. Type Badge (Line ~686)

**Location**: Next to field label

**Appearance**: Gray text `(type=checklist)`

**What It Shows**: Field type from backend

**Purpose**: Quick visual confirmation of field type

---

#### 6. Console Debug Log (Line ~663)

**Location**: Browser console

**What It Logs**:
```javascript
DEBUG_FIELD {
  field_key: "liver_echotexture",
  type: "checklist",
  label: "Liver Echotexture",
  options: [...],
  na_allowed: true,
  ...
}
```

**Purpose**: Full field object in console for detailed inspection

---

## Backend Debug Tools

### File: `backend/apps/workflow/management/commands/verify_usg_template_resolution.py`

**Usage**:
```bash
# Test all reports
source .venv/bin/activate  # or your virtualenv
python manage.py verify_usg_template_resolution

# Test specific report
python manage.py verify_usg_template_resolution --report-id <uuid>
```

**What It Tests**:
1. Count of total USG reports
2. Reports with/without `template_version`
3. Template resolution for sample report
4. Service configuration (all services have templates)
5. `ensure_template_for_report()` for draft reports (publish test)

**Output Example**:
```
================================================================================
PHASE 5: Backend Template Resolution Verification
================================================================================

📊 Total USG Reports: 15
✅ Reports WITH template_version: 12
❌ Reports WITHOUT template_version: 3

--------------------------------------------------------------------------------
Testing first report:
--------------------------------------------------------------------------------
Report ID: 123e4567-e89b-12d3-a456-426614174000
Status: DRAFT
Template Version: 1
Service: USG_ABDOMEN
Default Template: USG Abdomen Template
Published Versions: 1
Latest Version: 1
Schema exists: True
Schema sections: 5

--------------------------------------------------------------------------------
Attempting to resolve template schema:
--------------------------------------------------------------------------------
✅ SUCCESS: Schema resolved
   Sections: 5
   First section: Liver
   Fields: 8
   Sample field: Liver Size (type: text)
   Checklist fields: 2
   Dropdown fields: 1

   Sample checklist field:
     Label: Liver Echotexture
     Key: liver_echotexture
     Options: 4 items
     First option type: str
     First option: Normal

--------------------------------------------------------------------------------
Checking USG services configuration:
--------------------------------------------------------------------------------
Active USG Services: 10
✅ USG_ABDOMEN                      | USG Abdomen Template
✅ USG_PELVIS                       | USG Pelvis Template
❌ USG_DOPPLER                      | NONE
...

--------------------------------------------------------------------------------
Testing ensure_template_for_report (publish/finalize):
--------------------------------------------------------------------------------
Draft Report: 123e4567-e89b-12d3-a456-426614174000
Current template_version: 1
✅ SUCCESS: Template ensured
   Version: 1
   Template: USG Abdomen Template

================================================================================
Verification Complete
================================================================================
```

---

### Alternative Script: `backend/verify_usg_template_resolution.py`

**Usage**:
```bash
cd backend
source .venv/bin/activate
python verify_usg_template_resolution.py

# Test specific report
python verify_usg_template_resolution.py <report-uuid>
```

Same functionality as management command, but standalone script.

---

## How to Use These Tools

### Step-by-Step Investigation Workflow

#### Step 1: Backend Verification First
```bash
cd backend
source ../.venv/bin/activate  # Adjust path if needed
python manage.py verify_usg_template_resolution
```

**Look for**:
- ✅ All USG services have templates
- ✅ Schema resolves successfully
- ✅ Sections count > 0
- ✅ Checklist fields have options

**If any ❌ appears**: Fix backend issues first before checking frontend.

---

#### Step 2: Frontend Visual Inspection

1. Start frontend dev server
2. Navigate to USG editor page
3. Select a USG Abdomen report (or create new)
4. Scroll to "Liver" section

**Check**:
- [ ] Blue "BACKEND API DEBUG" panel at top shows schema exists
- [ ] Red "ACTIVE_RENDERER" banner visible
- [ ] Find `liver_echotexture` field
- [ ] Gray "FIELD DEBUG PANEL" shows field properties
- [ ] Renderer branch badge shows `CHECKLIST_BRANCH` (green)
- [ ] Orange "STATE VALUE DEBUG" panel shows value type
- [ ] Actual checkboxes visible below panels

---

#### Step 3: Browser Console Check

1. Open browser DevTools (F12)
2. Go to Console tab
3. Look for `DEBUG_FIELD` log entry

**Verify**:
- Field object matches debug panel
- No JavaScript errors
- Options array present

---

#### Step 4: Interact with Field

1. Click checkboxes (should work)
2. Click NA toggle (should hide/show field)
3. Type in text field (should auto-uncheck NA)

**Check State Debug Panel Updates**:
- Value changes when selecting options
- `is_not_applicable` toggles correctly
- Value type remains correct (array for checklist)

---

## Evidence Collection Checklist

Before applying any patches, collect:

### ✅ Frontend Evidence
- [ ] Screenshot of blue API debug panel (schema exists)
- [ ] Screenshot of field debug panels (gray + orange)
- [ ] Screenshot showing renderer branch badge
- [ ] Screenshot of actual field rendering (checkboxes visible or not)
- [ ] Browser console log of `DEBUG_FIELD` object
- [ ] Screenshot of NA toggle visible/hidden

### ✅ Backend Evidence
- [ ] Output of `verify_usg_template_resolution` command
- [ ] Confirmation all USG services have templates
- [ ] Confirmation schema resolves with sections > 0
- [ ] Confirmation checklist fields have options in schema
- [ ] No "❌ FAILED" errors in verification

### ✅ Django Shell Test (Optional)
```python
from apps.workflow.models import USGReport
from apps.workflow.template_resolution import resolve_template_schema_for_report

report = USGReport.objects.first()
schema = resolve_template_schema_for_report(report)
sections = schema['sections']

# Find liver section
liver_section = next(s for s in sections if 'liver' in s['title'].lower())
fields = liver_section['fields']

# Find echotexture field
echotexture = next(f for f in fields if 'echotexture' in f['label'].lower())

print(f"Type: {echotexture['type']}")
print(f"Options: {echotexture.get('options', [])}")
print(f"NA allowed: {echotexture.get('na_allowed', False)}")
```

---

## Common Issues and Diagnosis

### Issue 1: Checklist Shows Single "Yes"

**Possible Causes**:
1. ❌ Field type is `boolean` instead of `checklist` → Check FIELD DEBUG PANEL `type`
2. ❌ Renderer branch is `BOOLEAN_BRANCH` → Check renderer badge
3. ❌ Options missing from backend → Check `options_exists: false`
4. ❌ State value is `boolean` instead of `array` → Check STATE VALUE DEBUG

**Fix Strategy**:
- If backend schema wrong: Fix template definition
- If frontend rendering wrong: Fix type detection logic
- If state shape wrong: Fix `handleFieldChange` coercion

---

### Issue 2: NA Toggle Not Visible

**Possible Causes**:
1. ❌ `na_allowed: false` in field object → Check FIELD DEBUG PANEL
2. ❌ CSS hiding the checkbox → Inspect element
3. ❌ Field forced NA by system → Check `forcedNaFields` state

**Fix Strategy**:
- If `na_allowed` is false: Update template to set `na_allowed: true`
- If CSS issue: Fix styles
- If system forced: Check service profile configuration

---

### Issue 3: Options Not Displayed

**Possible Causes**:
1. ❌ `options_exists: false` → Backend not sending options
2. ❌ Options in wrong format → Check `options_sample` vs `normalized_options`
3. ❌ Renderer fallback to text input → Check renderer branch badge
4. ❌ State value is not array → Check STATE VALUE DEBUG

**Fix Strategy**:
- If options missing: Fix template definition or serializer
- If format wrong: `normalizeOptions()` should handle (already added)
- If renderer wrong: Fix type detection
- If state wrong: Fix state initialization

---

### Issue 4: Publish Fails with "No template schema"

**Possible Causes**:
1. ❌ Report has no `template_version` set
2. ❌ Service has no `default_template`
3. ❌ Template has no published version
4. ❌ Template version has empty schema

**Diagnosis**:
Run backend verification command (Step 1 above)

**Fix Strategy**:
- Run backfill command: `python manage.py backfill_usg_template_versions`
- Assign templates to services
- Publish template versions
- Re-import corrupted templates

---

## Cleanup After Investigation

Once root cause is identified and fix is verified:

1. **Remove debug panels**:
```typescript
// Comment out or remove:
const showDebugPanel = false; // Was: field.field_key === "liver_echotexture"
```

2. **Remove backend API debug**:
```typescript
// Remove the blue banner section
```

3. **Remove console logs**:
```typescript
// Remove: console.log("DEBUG_FIELD", field);
```

4. **Optional: Keep renderer banner**:
```typescript
// Red "ACTIVE_RENDERER" banner can stay or be removed
```

5. **Keep backend verification command**:
- Useful for production troubleshooting
- Can be part of health checks

---

## Files Modified

### Frontend
- `frontend/src/views/UsgStudyEditorPage.tsx` (debug panels added)

### Backend
- `backend/apps/workflow/management/commands/verify_usg_template_resolution.py` (new)
- `backend/verify_usg_template_resolution.py` (new)

### Documentation
- `USG_INVESTIGATION_GUIDE.md` (new)
- `USG_DEBUG_TOOLS_ADDED.md` (this file, new)

---

## Next Steps

1. **Run backend verification** to ensure database has valid data
2. **Start frontend** and navigate to USG editor
3. **Collect evidence** using debug panels
4. **Identify root cause** based on evidence
5. **Apply minimal patch** (only after evidence collected)
6. **Re-verify** fix works
7. **Remove debug tools** after confirmation

---

## Support

For questions or issues:
- Check `USG_INVESTIGATION_GUIDE.md` for detailed flowcharts
- Check `USG_FIX_SUMMARY_2026_01_22.md` for previous fixes
- Run backend verification command for database issues
- Check browser console for JavaScript errors

---

**Remember**: These are investigation tools, not fixes. They help you **see** what's happening at runtime so you can **prove** the root cause before applying patches.
