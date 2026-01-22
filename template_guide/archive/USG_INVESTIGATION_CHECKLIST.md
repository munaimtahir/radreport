# USG Investigation Checklist - Step-by-Step

**Purpose**: Systematic evidence collection before applying any patches  
**Time Required**: ~30 minutes  
**Outcome**: Root cause identification with proof

---

## Pre-Flight Check

- [ ] Backend server is running (or can connect to database)
- [ ] Frontend dev server can be started
- [ ] You have access to browser DevTools (F12)
- [ ] You can create or access a USG Abdomen report
- [ ] You have read `USG_INVESTIGATION_GUIDE.md` (optional but recommended)

---

## PHASE 1: Backend Verification (Required First)

**Estimated Time**: 5 minutes

### Step 1.1: Run Verification Command
```bash
cd backend
source ../.venv/bin/activate  # Adjust path if different
python manage.py verify_usg_template_resolution
```

### Step 1.2: Record Results

**Total Reports**: ______

**Reports WITH template_version**: ______  
**Reports WITHOUT template_version**: ______

**Schema Resolution Test**:
- [ ] ✅ SUCCESS: Schema resolved
- [ ] ❌ FAILED with error: ___________________________

**Schema Details** (if successful):
- Sections count: ______
- First section name: ___________________________
- Checklist fields found: ______
- Sample checklist field: ___________________________
- Sample field has options: [ ] Yes [ ] No
- Options count: ______
- First option format: [ ] String [ ] Object

**USG Services Configuration**:
- Total active USG services: ______
- Services WITHOUT template: ______ (should be 0)
- List any services missing templates:
  1. ___________________________
  2. ___________________________

**Publish Test** (ensure_template_for_report):
- [ ] ✅ SUCCESS: Template ensured
- [ ] ❌ FAILED with error: ___________________________
- [ ] ℹ️ No DRAFT reports to test

### Step 1.3: Decision Point

**If ALL checks show ✅**: Proceed to Phase 2 (Frontend)

**If ANY check shows ❌**: STOP. Fix backend issues first:
- Missing templates → Assign templates to services
- No published versions → Publish template versions
- Schema resolution fails → Check service configuration
- Reports without template_version → Run backfill command

---

## PHASE 2: Frontend Visual Inspection (Required)

**Estimated Time**: 10 minutes

### Step 2.1: Start Frontend
```bash
cd frontend
npm run dev
# Open browser to localhost:5173 (or your port)
```

### Step 2.2: Navigate to USG Editor
- [ ] Create new USG Abdomen report OR open existing draft
- [ ] Editor page loads successfully
- [ ] No JavaScript errors in console (F12 → Console)

### Step 2.3: Check Top-Level Debug Banners

**Red Banner** (Active Renderer):
- [ ] Visible at top of form
- [ ] Text: "ACTIVE_RENDERER: USG_FIELD_RENDERER_V2"
- [ ] Screenshot saved: `screenshot_1_renderer_banner.png`

**Blue Banner** (Backend API Debug):
- [ ] Visible below header
- [ ] Shows "template_schema exists": [ ] ✅ YES [ ] ❌ NULL
- [ ] Shows "template_schema.sections": ______ (should be > 0)
- [ ] Shows "report_status": ___________________________
- [ ] Shows "service_code": ___________________________
- [ ] No red warning about NULL schema: [ ] Correct [ ] Warning visible
- [ ] Screenshot saved: `screenshot_2_api_debug.png`

**Decision Point**:
- If schema is NULL: STOP. Backend issue. Check Phase 1 results.
- If schema exists with 0 sections: STOP. Template is empty/corrupt.
- If all ✅: Continue

---

### Step 2.4: Navigate to Liver Section

- [ ] "Liver" section visible in left sidebar
- [ ] Click "Liver" section
- [ ] Section content loads

### Step 2.5: Inspect `liver_echotexture` Field

**Field Label**:
- [ ] "Liver Echotexture" label visible
- [ ] Type badge shows: `(type=________)`
- [ ] Renderer branch badge shows: __________________ (color: ______)

**Field Debug Panel** (Gray box with 🔍):
- [ ] Panel is visible below label
- [ ] Shows JSON with field properties
- [ ] Record values:
  ```
  identifier_key: ___________________________
  identifier_key_alt: ___________________________
  type: ___________________________
  na_allowed: [ ] true [ ] false
  supports_not_applicable: [ ] true [ ] false
  options_exists: [ ] true [ ] false
  options_length: ______
  ```
- [ ] Screenshot saved: `screenshot_3_field_debug.png`

**State Value Debug Panel** (Orange box with 📦):
- [ ] Panel is visible below field debug
- [ ] Shows:
  ```
  value typeof: ___________________________
  value: ___________________________
  is_not_applicable: [ ] true [ ] false
  ```
- [ ] Screenshot saved: `screenshot_4_state_debug.png`

**Actual Field Rendering**:
- [ ] NA checkbox is: [ ] Visible [ ] Hidden
- [ ] Field input is: [ ] Multiple checkboxes [ ] Single checkbox [ ] Dropdown [ ] Text input
- [ ] Options visible: [ ] Yes, count: ______ [ ] No
- [ ] List visible options:
  1. ___________________________
  2. ___________________________
  3. ___________________________
  4. ___________________________
- [ ] Screenshot saved: `screenshot_5_field_render.png`

---

### Step 2.6: Inspect `liver_size` Field (Optional)

Repeat Step 2.5 for `liver_size` field if needed for comparison.

---

## PHASE 3: Browser Console Verification

**Estimated Time**: 2 minutes

### Step 3.1: Open DevTools Console
- [ ] Press F12
- [ ] Go to Console tab
- [ ] Clear console (optional)
- [ ] Refresh page

### Step 3.2: Find DEBUG_FIELD Log
- [ ] `DEBUG_FIELD` log entry visible
- [ ] Log shows object for `liver_echotexture`
- [ ] Copy full log output to: `console_log_field_debug.txt`
- [ ] Verify log matches Field Debug Panel: [ ] Yes [ ] No

### Step 3.3: Check for Errors
- [ ] No errors in console: [ ] Correct [ ] Errors present
- [ ] If errors, list them:
  1. ___________________________
  2. ___________________________

---

## PHASE 4: Field Interaction Testing

**Estimated Time**: 5 minutes

### Step 4.1: Test NA Toggle

**Initial State**:
- NA checkbox is: [ ] Checked [ ] Unchecked

**Action**: Click NA checkbox
- [ ] Checkbox toggles successfully
- [ ] Field becomes grayed/disabled: [ ] Yes [ ] No
- [ ] State Debug updates `is_not_applicable`: [ ] Yes [ ] No
- [ ] State Debug shows `value: null`: [ ] Yes [ ] No

**Action**: Uncheck NA
- [ ] Field becomes enabled
- [ ] Previous value restored: [ ] Yes [ ] No

---

### Step 4.2: Test Field Input (Checklist)

**If field shows multiple checkboxes**:

**Action**: Click first checkbox
- [ ] Checkbox becomes checked
- [ ] State Debug updates `value`: [ ] Yes [ ] No
- [ ] New value is: ___________________________
- [ ] Value typeof remains: `array`
- [ ] NA auto-unchecks: [ ] Yes [ ] No [ ] N/A (was already unchecked)

**Action**: Click second checkbox
- [ ] Second checkbox becomes checked
- [ ] State Debug shows array with 2 items: [ ] Yes [ ] No
- [ ] Array contents: ___________________________

**Action**: Uncheck first checkbox
- [ ] First checkbox unchecks
- [ ] State Debug shows array with 1 item: [ ] Yes [ ] No

---

### Step 4.3: Test Field Input (If Dropdown)

**If field shows dropdown**:

**Action**: Select an option
- [ ] Dropdown value changes
- [ ] State Debug updates `value`: [ ] Yes [ ] No
- [ ] New value is: ___________________________
- [ ] Value typeof is: `string`
- [ ] NA auto-unchecks: [ ] Yes [ ] No [ ] N/A

---

### Step 4.4: Test Field Input (If Single Checkbox)

**If field shows single checkbox labelled "Yes"**:

⚠️ **This is likely the bug!**

**Action**: Click checkbox
- [ ] Checkbox toggles
- [ ] State Debug updates: [ ] Yes [ ] No
- [ ] Value typeof is: ___________________________
- [ ] Expected typeof should be: `array` (for checklist) or `boolean` (if actually boolean)

**Document**:
- Expected field type: ___________________________
- Actual field type (from Field Debug): ___________________________
- Options exist: [ ] Yes [ ] No
- Renderer branch: ___________________________
- **Root cause identified**: [ ] Yes [ ] No

---

## PHASE 5: Root Cause Analysis

**Estimated Time**: 5 minutes

### Step 5.1: Compare Evidence

Fill in this comparison table:

| Check | Expected | Actual | Match? |
|-------|----------|--------|--------|
| Backend schema type | `checklist` | _________ | [ ] Yes [ ] No |
| Backend options exist | `true` | _________ | [ ] Yes [ ] No |
| Frontend type badge | `checklist` | _________ | [ ] Yes [ ] No |
| Renderer branch | `CHECKLIST_BRANCH` | _________ | [ ] Yes [ ] No |
| State value typeof | `array` | _________ | [ ] Yes [ ] No |
| UI component | Multiple checkboxes | _________ | [ ] Yes [ ] No |
| NA toggle visible | `true` | _________ | [ ] Yes [ ] No |

### Step 5.2: Identify Mismatch Layer

**Where is the first mismatch?**

- [ ] **Layer 1: Backend Schema** (template definition wrong)
- [ ] **Layer 2: API Serialization** (schema not sent correctly)
- [ ] **Layer 3: Frontend Type Detection** (wrong renderer branch)
- [ ] **Layer 4: State Management** (wrong value type)
- [ ] **Layer 5: UI Rendering** (CSS hiding elements)

**Root Cause Description**:
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________

### Step 5.3: Proposed Fix

**Fix Location**: [ ] Backend [ ] Frontend [ ] Both

**Fix Description**:
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________

**Patch Type**: [ ] Template JSON [ ] State coercion [ ] Type detection [ ] CSS [ ] Other: __________

---

## PHASE 6: Apply Minimal Patch (Only After Evidence)

**Do NOT proceed unless**:
- [ ] Root cause is clearly identified
- [ ] Evidence supports the diagnosis
- [ ] Fix is minimal and targeted

### Step 6.1: Apply Fix

**What did you change?**
_________________________________________________________________
_________________________________________________________________

**File(s) modified**:
1. ___________________________
2. ___________________________

### Step 6.2: Verify Fix

**Re-test the field**:
- [ ] Field now shows multiple checkboxes (if checklist)
- [ ] Options are visible and correct
- [ ] NA toggle is visible and functional
- [ ] State Debug shows correct typeof
- [ ] Renderer branch is correct
- [ ] No console errors

**Take After Screenshots**:
- [ ] Screenshot saved: `screenshot_6_after_fix_field.png`
- [ ] Screenshot saved: `screenshot_7_after_fix_debug.png`

### Step 6.3: Test Other Fields

**Test at least 2 more fields**:
1. Field: ___________________________ - Status: [ ] ✅ Works [ ] ❌ Broken
2. Field: ___________________________ - Status: [ ] ✅ Works [ ] ❌ Broken

### Step 6.4: Test Publish (If Applicable)

**If fix was for "No template schema" error**:

- [ ] Create a draft report
- [ ] Fill some fields
- [ ] Submit for verification
- [ ] Click Publish
- [ ] Publish succeeds: [ ] Yes [ ] No
- [ ] Error message (if failed): ___________________________
- [ ] PDF generated: [ ] Yes [ ] No

---

## PHASE 7: Cleanup

### Step 7.1: Remove Debug Tools

- [ ] Set `showDebugPanel = false` in `UsgStudyEditorPage.tsx`
- [ ] Remove blue API debug banner (or comment out)
- [ ] Remove console.log statements
- [ ] Optional: Remove red renderer banner

### Step 7.2: Test Without Debug

- [ ] Restart frontend
- [ ] Navigate to USG editor
- [ ] No debug panels visible: [ ] Correct
- [ ] Field still works correctly: [ ] Yes [ ] No
- [ ] No console errors: [ ] Correct

### Step 7.3: Final Screenshots

- [ ] Screenshot saved: `screenshot_8_final_clean.png`
- [ ] Screenshot shows working field without debug panels

---

## PHASE 8: Documentation & PR

### Step 8.1: Create Summary Document

**File**: `USG_FIX_PROOF_<DATE>.md`

Include:
- [ ] Root cause description
- [ ] Evidence (screenshot links)
- [ ] Before/After comparison
- [ ] Fix applied (code diff or description)
- [ ] Verification results

### Step 8.2: Prepare PR

- [ ] Commit changes
- [ ] Create PR with descriptive title
- [ ] Link all screenshots
- [ ] Reference investigation documents
- [ ] Request review

---

## Investigation Complete ✅

**Date Completed**: ___________________________  
**Root Cause**: ___________________________  
**Fix Applied**: [ ] Yes [ ] No  
**Verified**: [ ] Yes [ ] No  
**PR Created**: [ ] Yes [ ] No  

**Time Spent**:
- Phase 1 (Backend): ______ min
- Phase 2 (Frontend): ______ min
- Phase 3 (Console): ______ min
- Phase 4 (Testing): ______ min
- Phase 5 (Analysis): ______ min
- Phase 6 (Fix): ______ min
- Phase 7 (Cleanup): ______ min
- Phase 8 (Docs): ______ min
- **Total**: ______ min

---

## Notes

(Add any additional observations, gotchas, or learnings here)

_________________________________________________________________
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________

---

**End of Checklist**

Save this file with your filled-in values for future reference.
