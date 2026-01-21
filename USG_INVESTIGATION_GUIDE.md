# USG Field Mis-Rendering Investigation Guide

**Date**: January 22, 2026  
**Objective**: Systematically verify all plausible failure points before applying patches

## Overview

This document provides a complete investigation workflow to identify the root cause(s) of:
1. Checklist fields showing single "Yes" instead of multiple options
2. NA toggle not visible
3. Options not displayed correctly
4. Publish/verify errors: "No template schema available for this report"

## Investigation Phases

### PHASE 1: Confirm Runtime Field Object (Frontend)

**Goal**: Verify what field data the frontend actually receives from the API.

**Debug Panels Added**:
- **Field Debug Panel** (yellow background) - Shows full field object for `liver_echotexture` and `liver_size`
- **State Value Debug** (orange background) - Shows value storage shape and type
- **Renderer Branch Badge** (green/yellow pill) - Shows which renderer branch is executing

**How to Use**:
1. Navigate to any USG report editor (e.g., USG Abdomen)
2. Look for the "Liver" section
3. Find the `liver_echotexture` field
4. Observe the debug panels below the field label

**What to Verify**:

✅ **Field Object Properties** (Field Debug Panel):
```json
{
  "identifier_key": "liver_echotexture",      // Should be present
  "identifier_key_alt": null,                 // Check if 'key' exists instead
  "type": "checklist",                        // Should match expected type
  "na_allowed": true,                         // Should be true if NA supported
  "options_exists": true,                     // Must be true
  "options_length": 4,                        // Should match template
  "options_sample": [...],                    // Check format: string[] or object[]
  "normalized_options": [                     // Should be {label, value}[]
    {"label": "Normal", "value": "Normal"},
    ...
  ]
}
```

✅ **Renderer Branch Badge**:
- **CHECKLIST_BRANCH** (green) = Correct for multi-select fields
- **BOOLEAN_BRANCH** (yellow) = WRONG if field should be checklist
- **DROPDOWN_BRANCH** (yellow) = Check if correct for single-select

✅ **State Value Debug** (orange panel):
```
value typeof: array          // Checklist MUST be array
value: ["Normal", "Coarse"]  // Should be string[] for checklist
is_not_applicable: false     // Should reflect NA state
```

**Common Issues to Look For**:
- ❌ `identifier_key` is null but `identifier_key_alt` has value → **key mismatch bug**
- ❌ `type` is "boolean" but should be "checklist" → **backend schema issue**
- ❌ `options_exists: false` → **backend not sending options**
- ❌ `options_sample` shows strings but expected objects → **normalization needed**
- ❌ `value typeof: string` for checklist → **state shape mismatch**
- ❌ Renderer badge shows wrong branch → **type detection logic error**

---

### PHASE 2: Verify Renderer Branch Selection (Frontend)

**Goal**: Confirm the correct UI component is being rendered for each field type.

**Debug Features**:
- Type badge next to field label: `(type=checklist)`
- Renderer branch badge: `CHECKLIST_BRANCH`

**Expected Mappings**:
| Field Type | Expected Branch | UI Component |
|------------|----------------|--------------|
| `checklist` | CHECKLIST_BRANCH | Multiple checkboxes |
| `multi_choice` | CHECKLIST_BRANCH | Multiple checkboxes |
| `dropdown` | DROPDOWN_BRANCH | Select dropdown |
| `single_choice` (>5 options) | DROPDOWN_BRANCH | Select dropdown |
| `single_choice` (≤5 options) | RADIO_BRANCH | Radio buttons |
| `boolean` | BOOLEAN_BRANCH | Single checkbox |
| `number` | NUMBER_BRANCH | Number input |
| `text` / `short_text` / `long_text` | TEXT_BRANCH | Text input/textarea |

**What to Verify**:
- ✅ Badge matches expected branch for field type
- ✅ UI matches badge (e.g., CHECKLIST_BRANCH → multiple checkboxes visible)
- ❌ If badge is wrong, the issue is in `supportsMultiChoice()` or `usesSelectForSingleChoice()` logic

---

### PHASE 3: Verify State Storage Shape (Frontend)

**Goal**: Confirm values are stored in the correct data type.

**Debug Panel**: Orange "STATE VALUE DEBUG" panel

**Expected Storage**:
| Field Type | Expected value typeof | Example |
|------------|----------------------|---------|
| `checklist` | `array` | `["Normal", "Coarse"]` |
| `dropdown` | `string` | `"Normal"` |
| `single_choice` | `string` | `"Yes"` |
| `boolean` | `boolean` | `true` |
| `number` | `number` | `45` |
| `text` | `string` | `"Sample text"` |

**Common Issues**:
- ❌ Checklist stored as `string` → Will render as single value
- ❌ Checklist stored as `boolean` → Will render incorrectly
- ❌ Dropdown stored as `object` → Will not match options
- ❌ Value is `undefined` when it should be `null` or `[]`

**Fix Strategy**:
If state shape is wrong, fix `handleFieldChange` to coerce values:
```typescript
// For checklist
if (field.type === "checklist" && typeof value === "string") {
  value = [value];
}
```

---

### PHASE 4: Confirm Backend Schema Source (Frontend + Backend)

**Goal**: Verify the editor receives a valid schema from the API.

**Frontend Debug Panel** (blue banner at top):
- Shows if `template_schema` is present or NULL
- Shows section count
- Displays API endpoint

**What to Verify**:

✅ **API Response** (`/api/workflow/usg/{studyId}/`):
```json
{
  "template_schema": {
    "sections": [...]  // Must exist and have length > 0
  }
}
```

❌ **Common Issues**:
- `template_schema: null` → Report has no `template_version` set
- `template_schema.sections: []` → Template exists but is empty/malformed
- `template_schema` missing entirely → Serializer error

**Backend Verification**:
Use the management command to test:
```bash
python manage.py verify_usg_template_resolution
```

Or test specific report:
```bash
python manage.py verify_usg_template_resolution --report-id <uuid>
```

---

### PHASE 5: Investigate Publish/Verify Error (Backend)

**Goal**: Confirm "No template schema available" error cause.

**Error Location**: `/api/workflow/usg/{id}/publish/` or `/api/workflow/usg/{id}/finalize/`

**Verification Steps**:

1. **Run Backend Verification**:
```bash
cd backend
python manage.py verify_usg_template_resolution
```

2. **Check Output**:
```
✅ Schema resolved with 5 sections
❌ FAILED: No template schema available for this report...
```

3. **Common Root Causes**:

| Symptom | Root Cause | Fix |
|---------|-----------|-----|
| "report has no service association" | Report not linked to service/item | Backfill service links |
| "service has no default_template" | Service config missing | Assign template to service |
| "template has no published version" | Template not published | Publish template version |
| "template_version has no schema" | Template corrupt | Re-import template |

4. **Django Shell Test**:
```python
from apps.workflow.models import USGReport
from apps.workflow.template_resolution import resolve_template_schema_for_report

report = USGReport.objects.get(id="<report-uuid>")
schema = resolve_template_schema_for_report(report)
print(f"Sections: {len(schema['sections'])}")
```

---

## Quick Diagnosis Flowchart

```
START: Field not rendering correctly
  ↓
  Check PHASE 1 Debug Panel
  ↓
  ├─ options_exists: false?
  │   ↓
  │   YES → Backend schema issue (PHASE 4/5)
  │   NO → Continue
  ↓
  ├─ type: correct?
  │   ↓
  │   NO → Backend schema wrong type
  │   YES → Continue
  ↓
  Check PHASE 2 Renderer Branch
  ↓
  ├─ Badge matches type?
  │   ↓
  │   NO → Frontend type detection logic error
  │   YES → Continue
  ↓
  Check PHASE 3 State Value Debug
  ↓
  ├─ value typeof: correct?
  │   ↓
  │   NO → Fix handleFieldChange coercion
  │   YES → Continue
  ↓
  Check PHASE 4 Backend API Debug
  ↓
  ├─ template_schema: null?
  │   ↓
  │   YES → Run PHASE 5 backend verification
  │   NO → Check sections.length > 0
  ↓
  All checks pass? → Issue may be in:
    - CSS/styling hiding elements
    - NA state preventing interaction
    - Browser dev tools for more clues
```

---

## Proof Output Requirements

Before applying any patches, provide:

### 1. Frontend Screenshot
Must show:
- ✅ Red "ACTIVE_RENDERER" banner at top
- ✅ Blue "BACKEND API DEBUG" panel showing schema exists
- ✅ Field with debug panels (yellow + orange)
- ✅ Renderer branch badge (green or yellow)
- ✅ Multiple options visible (or clear error state)

### 2. Backend Shell Output
```bash
python manage.py verify_usg_template_resolution
```

Must confirm:
- ✅ Total reports count
- ✅ Reports with/without template_version
- ✅ Schema resolved successfully
- ✅ Sections count > 0
- ✅ Sample fields show correct types and options
- ✅ USG services all have templates configured
- ✅ Draft report can resolve template (for publish test)

### 3. Browser Console Log
Must include:
```javascript
DEBUG_FIELD {
  field_key: "liver_echotexture",
  type: "checklist",
  options: [...],
  na_allowed: true
}
```

---

## Cleanup After Investigation

Once root cause is identified and fix is applied:

1. **Remove Debug Panels**:
```typescript
// Remove or comment out:
const showDebugPanel = field.field_key === "liver_echotexture" || field.field_key === "liver_size";
```

2. **Remove Debug Banner**:
```typescript
// Remove blue "BACKEND API DEBUG" panel
```

3. **Remove Console Logs**:
```typescript
// Remove: console.log("DEBUG_FIELD", field);
```

4. **Keep Renderer Banner** (optional):
- The red "ACTIVE_RENDERER" banner can be kept or removed based on preference

---

## Contact / Support

If investigation reveals issues:

1. **Frontend Issues**:
   - Check `frontend/src/views/UsgStudyEditorPage.tsx`
   - Verify `normalizeOptions()` function
   - Check field type conditions in renderer

2. **Backend Issues**:
   - Check `backend/apps/workflow/template_resolution.py`
   - Verify service has `default_template` configured
   - Run backfill command if needed

3. **Template Issues**:
   - Check template versions are published
   - Verify schema JSON structure matches expected format
   - Re-import templates if needed

---

## Summary

This investigation framework provides **evidence-based debugging** before applying patches:

- **PHASE 1-3**: Frontend runtime verification (field data, renderer, state)
- **PHASE 4**: API response verification
- **PHASE 5**: Backend template resolution verification

Each phase has clear success/failure criteria and specific fix strategies. Only after evidence is collected should minimal patches be applied.
