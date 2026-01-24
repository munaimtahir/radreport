# USG Field Mis-Rendering Investigation - START HERE

**Date**: January 22, 2026  
**Purpose**: Systematic root cause investigation before applying patches  
**Status**: ✅ All tools ready

---

## Quick Start (3 Steps)

### 1. Run Backend Check (5 min)
```bash
cd backend
source ../.venv/bin/activate
python manage.py verify_usg_template_resolution
```

**Look for**: All ✅ (green checkmarks). Any ❌ means backend issues need fixing first.

---

### 2. Start Frontend & Inspect (10 min)
```bash
cd frontend
npm run dev
# Open browser, navigate to USG Abdomen editor
# Look for debug panels (blue, gray, orange)
```

**Look for**: Debug panels showing field properties, renderer branch, state values.

---

### 3. Collect Evidence (5 min)
- Take screenshots of all debug panels
- Check browser console for `DEBUG_FIELD` log
- Fill out `USG_INVESTIGATION_CHECKLIST.md`

**Result**: Root cause identified with proof!

---

## Documentation Overview

We've created 5 documents to guide you:

### 📋 1. **USG_INVESTIGATION_CHECKLIST.md** ← START HERE
- **Purpose**: Step-by-step evidence collection form
- **Format**: Fill-in-the-blanks checklist
- **Time**: 30 minutes to complete
- **Outcome**: Root cause identification + proof
- **Use this**: As your primary workflow guide

### 📚 2. **USG_INVESTIGATION_GUIDE.md**
- **Purpose**: Detailed reference guide
- **Format**: Comprehensive documentation with flowcharts
- **Time**: 15 minutes to read, reference as needed
- **Outcome**: Understanding of all failure modes
- **Use this**: When you need deeper explanation or troubleshooting

### 🔧 3. **USG_DEBUG_TOOLS_ADDED.md**
- **Purpose**: Tool reference manual
- **Format**: Documentation of each debug feature
- **Time**: 10 minutes to skim, reference as needed
- **Outcome**: Know what each debug panel shows
- **Use this**: When interpreting debug panel output

### ✅ 4. **USG_INVESTIGATION_COMPLETE.md**
- **Purpose**: Executive summary + quick reference
- **Format**: High-level overview with examples
- **Time**: 5 minutes to read
- **Outcome**: Big picture understanding
- **Use this**: For a quick overview or to share with team

### 📜 5. **USG_FIX_SUMMARY_2026_01_22.md** (Existing)
- **Purpose**: Previous fixes documentation
- **Format**: Historical record of changes made
- **Time**: Reference as needed
- **Outcome**: Context on what was already fixed
- **Use this**: To understand what was done before investigation tools

---

## What's Been Added

### Frontend Debug Tools
Located in: `frontend/src/views/UsgStudyEditorPage.tsx`

1. **Blue API Debug Banner** (top of page)
   - Shows if backend sends valid schema
   - Shows section count
   - Warns if schema is NULL

2. **Field Debug Panel** (gray box)
   - Shows full field object as JSON
   - Verifies identifier, type, options, NA support
   - For: `liver_echotexture`, `liver_size`

3. **Renderer Branch Badge** (colored pill)
   - Shows which UI component is rendering
   - Green = CHECKLIST_BRANCH
   - Yellow = other branches

4. **State Value Debug Panel** (orange box)
   - Shows value storage type (array, string, boolean)
   - Shows actual value
   - Shows NA state

5. **Type Badge** (gray text)
   - Shows field type from backend
   - Format: `(type=checklist)`

6. **Console Logging**
   - Logs full field object for `liver_echotexture`
   - Find in DevTools console

### Backend Debug Tools
Located in: `backend/apps/workflow/management/commands/`

1. **Management Command**: `verify_usg_template_resolution`
   - Tests template resolution for all reports
   - Checks service configuration
   - Verifies publish readiness
   - Provides detailed ✅/❌ output

2. **Standalone Script**: `backend/verify_usg_template_resolution.py`
   - Same functionality as management command
   - Can run outside Django manage.py

---

## Recommended Workflow

### For Quick Diagnosis (20 min)
1. Read: `USG_INVESTIGATION_COMPLETE.md` (5 min)
2. Run: Backend verification command (5 min)
3. Test: Frontend visual inspection (10 min)
4. Result: Root cause likely identified

### For Thorough Investigation (60 min)
1. Read: `USG_INVESTIGATION_GUIDE.md` (15 min)
2. Follow: `USG_INVESTIGATION_CHECKLIST.md` (30 min)
3. Reference: `USG_DEBUG_TOOLS_ADDED.md` as needed (15 min)
4. Result: Root cause proven with full evidence

### For Minimal Time (10 min)
1. Run: Backend command (5 min)
2. Check: Frontend blue banner only (2 min)
3. Check: One field's debug panels (3 min)
4. Result: High-level diagnosis (may need more investigation)

---

## Common Scenarios

### Scenario A: "Checklist shows single Yes checkbox"

**Quick Check**:
```bash
# Backend
python manage.py verify_usg_template_resolution
# Look for: Sample checklist field type
```

**Expected Finding**:
- Field Debug Panel shows `type: "boolean"` (WRONG)
- Should be `type: "checklist"`

**Fix**: Update template JSON to correct type

---

### Scenario B: "NA toggle not visible"

**Quick Check**:
- Look at Field Debug Panel
- Check: `na_allowed: false`

**Expected Finding**:
- Template has `na_allowed` not set or false

**Fix**: Update template to set `na_allowed: true`

---

### Scenario C: "Options not displayed"

**Quick Check**:
- Look at Field Debug Panel
- Check: `options_exists: false` or `options_length: 0`

**Expected Finding**:
- Backend not sending options in schema

**Fix**: Update template to include options array

---

### Scenario D: "Publish fails: No template schema"

**Quick Check**:
```bash
python manage.py verify_usg_template_resolution
```

**Expected Finding**:
- Reports WITHOUT template_version: > 0
- Or: Service has no default_template

**Fix**: Run backfill command or assign templates to services

---

## File Locations

### Frontend
```
frontend/src/views/UsgStudyEditorPage.tsx
```

### Backend
```
backend/apps/workflow/management/commands/verify_usg_template_resolution.py
backend/verify_usg_template_resolution.py
backend/apps/workflow/template_resolution.py (already exists)
backend/apps/workflow/serializers.py (already exists)
backend/apps/workflow/api.py (already exists)
```

### Documentation
```
README_USG_INVESTIGATION.md (this file)
USG_INVESTIGATION_CHECKLIST.md (fill-in form)
USG_INVESTIGATION_GUIDE.md (detailed reference)
USG_DEBUG_TOOLS_ADDED.md (tool reference)
USG_INVESTIGATION_COMPLETE.md (summary)
USG_FIX_SUMMARY_2026_01_22.md (previous fixes)
```

---

## Prerequisites

### Required
- [ ] Backend database accessible
- [ ] Python virtualenv with Django installed
- [ ] Frontend dev server can start
- [ ] Browser with DevTools (F12)
- [ ] Can create or access USG reports

### Optional but Helpful
- [ ] Multiple USG reports in database (for testing)
- [ ] Fresh USG Abdomen report (for clean test)
- [ ] Screenshot tool ready
- [ ] Text editor for filling checklist

---

## What NOT to Do

❌ **Don't apply patches before evidence collection**  
❌ **Don't skip backend verification**  
❌ **Don't ignore debug panels**  
❌ **Don't assume root cause without proof**  
❌ **Don't apply complex fixes when simple ones work**

✅ **Do collect evidence systematically**  
✅ **Do use the checklist**  
✅ **Do take screenshots**  
✅ **Do verify fixes before cleanup**  
✅ **Do document findings**

---

## Success Criteria

Investigation is successful when:

1. ✅ Backend verification runs without errors
2. ✅ All debug panels display correctly
3. ✅ Evidence collected (screenshots + logs)
4. ✅ Root cause identified with proof
5. ✅ Minimal patch proposed
6. ✅ Fix applied and verified
7. ✅ Debug tools removed
8. ✅ Documentation updated

---

## Support

### If Backend Verification Fails
- Check service configuration
- Verify templates are published
- Run backfill command if needed
- See: `USG_INVESTIGATION_GUIDE.md` Phase 5

### If Frontend Shows Errors
- Check browser console for JavaScript errors
- Verify API response in Network tab
- Check blue API debug banner for schema status
- See: `USG_INVESTIGATION_GUIDE.md` Phase 4

### If Root Cause Unclear
- Fill out complete checklist
- Compare all evidence points
- Use diagnosis flowchart in guide
- See: `USG_INVESTIGATION_GUIDE.md` diagnosis section

### If Fix Doesn't Work
- Re-verify evidence
- Check if fix was applied correctly
- Test with fresh report
- Collect new evidence with fix applied

---

## Timeline

| Phase | Time | Activity |
|-------|------|----------|
| Setup | 5 min | Read this file, gather prerequisites |
| Backend Check | 5 min | Run verification command |
| Frontend Inspect | 10 min | Visual inspection of debug panels |
| Console Check | 2 min | Browser DevTools verification |
| Interaction Test | 5 min | Test field behavior |
| Analysis | 5 min | Identify root cause |
| Apply Fix | 5 min | Make minimal code change |
| Verify Fix | 5 min | Re-test all functionality |
| Cleanup | 5 min | Remove debug tools |
| Documentation | 10 min | Update docs, create PR |
| **Total** | **~60 min** | **Complete investigation** |

---

## Next Steps

### Right Now (5 min)
1. Read this file completely ✅ (you're doing it!)
2. Skim `USG_INVESTIGATION_COMPLETE.md`
3. Print or open `USG_INVESTIGATION_CHECKLIST.md`

### In Next 30 Minutes
1. Run backend verification
2. Start frontend and inspect
3. Fill out checklist sections 1-5

### Within 1 Hour
1. Complete checklist
2. Identify root cause
3. Apply minimal fix
4. Verify fix works

### After Fix Verified
1. Remove debug tools
2. Create documentation
3. Submit PR with proof

---

## Questions & Answers

**Q: Can I skip backend verification?**  
A: No. Backend issues will cause frontend symptoms. Always check backend first.

**Q: Do I need to test all fields?**  
A: No. Test 1-2 representative fields (like `liver_echotexture`). Debug panels show full picture.

**Q: What if no USG reports exist?**  
A: Create a new USG Abdomen report through the registration flow.

**Q: How do I know which fix to apply?**  
A: The evidence will point to the layer (backend schema, frontend state, etc.). Checklist helps identify.

**Q: Can I keep debug tools after fix?**  
A: No. They're for investigation only. Remove before PR.

**Q: What if multiple issues exist?**  
A: Prioritize: 1) Backend schema, 2) State coercion, 3) Renderer detection, 4) CSS/styling.

---

## Contact

For help:
- Check relevant documentation file first
- Run backend verification command
- Collect full evidence before asking
- Include screenshots and logs in question

---

## Version History

- **2026-01-22**: Initial investigation tools added
- **Previous**: Fixes documented in `USG_FIX_SUMMARY_2026_01_22.md`

---

**Ready to start? → Open `USG_INVESTIGATION_CHECKLIST.md` and begin! 🚀**
