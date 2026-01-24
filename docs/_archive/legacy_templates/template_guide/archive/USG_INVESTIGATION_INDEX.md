# USG Investigation - Complete File Index

**Status**: ✅ All investigation tools ready  
**Date**: January 22, 2026

---

## 📖 START HERE

**Primary Entry Point**: [`README_USG_INVESTIGATION.md`](./README_USG_INVESTIGATION.md)
- Quick start guide (3 steps)
- Documentation overview
- Common scenarios
- Timeline and workflow

---

## 📚 Documentation Files

### 1. For Action (Use These)

| File | Purpose | When to Use | Time |
|------|---------|-------------|------|
| **[README_USG_INVESTIGATION.md](./README_USG_INVESTIGATION.md)** | Start here, overview | First read | 5 min |
| **[USG_INVESTIGATION_CHECKLIST.md](./USG_INVESTIGATION_CHECKLIST.md)** | Step-by-step form | During investigation | 30 min |
| **[USG_INVESTIGATION_GUIDE.md](./USG_INVESTIGATION_GUIDE.md)** | Detailed reference | When stuck or need details | 15 min |

### 2. For Reference (Refer As Needed)

| File | Purpose | When to Use | Time |
|------|---------|-------------|------|
| **[USG_DEBUG_TOOLS_ADDED.md](./USG_DEBUG_TOOLS_ADDED.md)** | Tool documentation | Understanding debug panels | 10 min |
| **[USG_INVESTIGATION_COMPLETE.md](./USG_INVESTIGATION_COMPLETE.md)** | Executive summary | Quick overview, sharing | 5 min |
| **[USG_FIX_SUMMARY_2026_01_22.md](./USG_FIX_SUMMARY_2026_01_22.md)** | Previous fixes | Historical context | As needed |
| **[USG_INVESTIGATION_INDEX.md](./USG_INVESTIGATION_INDEX.md)** | This file - file index | Finding right document | 2 min |

---

## 🔧 Code Files Modified

### Frontend (1 file)

**[`frontend/src/views/UsgStudyEditorPage.tsx`](./frontend/src/views/UsgStudyEditorPage.tsx)**
- **Changes**: Added 5 debug panels + console logging
- **Lines**: ~660-750 (field rendering loop)
- **Lines**: ~520-560 (backend API debug banner)
- **Status**: ✅ Ready for testing
- **Revert**: Remove debug panels after fix

**Debug Features Added**:
1. Blue banner (backend API debug) - Top of page
2. Gray panel (field object debug) - Per-field
3. Orange panel (state value debug) - Per-field
4. Green/yellow badge (renderer branch) - Per-field
5. Gray text (type badge) - Per-field
6. Console log - Browser console

---

### Backend (3 files)

**[`backend/apps/workflow/management/commands/verify_usg_template_resolution.py`](./backend/apps/workflow/management/commands/verify_usg_template_resolution.py)**
- **Type**: New file
- **Purpose**: Django management command for verification
- **Usage**: `python manage.py verify_usg_template_resolution`
- **Status**: ✅ Functional
- **Keep**: Yes (useful for monitoring)

**[`backend/verify_usg_template_resolution.py`](./backend/verify_usg_template_resolution.py)**
- **Type**: New file
- **Purpose**: Standalone verification script
- **Usage**: `python backend/verify_usg_template_resolution.py`
- **Status**: ✅ Functional
- **Keep**: Optional (duplicate of management command)

**[`backend/apps/workflow/template_resolution.py`](./backend/apps/workflow/template_resolution.py)**
- **Type**: Existing (from previous fix)
- **Purpose**: Template resolution utilities
- **Status**: Already functional
- **No changes needed**: Already working

**[`backend/apps/workflow/serializers.py`](./backend/apps/workflow/serializers.py)**
- **Type**: Existing (from previous fix)
- **Purpose**: API serialization with auto-resolve
- **Status**: Already functional
- **No changes needed**: Already working

**[`backend/apps/workflow/api.py`](./backend/apps/workflow/api.py)**
- **Type**: Existing (from previous fix)
- **Purpose**: Publish/finalize endpoints with template checks
- **Status**: Already functional
- **No changes needed**: Already working

---

## 📋 Quick Reference Matrix

### Documentation Purpose Matrix

| Document | Overview | Workflow | Reference | Technical | Checklist |
|----------|----------|----------|-----------|-----------|-----------|
| README | ✅ | ✅ | ❌ | ❌ | ❌ |
| CHECKLIST | ❌ | ✅ | ❌ | ❌ | ✅ |
| GUIDE | ✅ | ✅ | ✅ | ✅ | ❌ |
| TOOLS | ❌ | ❌ | ✅ | ✅ | ❌ |
| COMPLETE | ✅ | ❌ | ✅ | ❌ | ❌ |
| INDEX (this) | ❌ | ❌ | ✅ | ❌ | ❌ |

---

### Documentation Flow

```
START
  ↓
README_USG_INVESTIGATION.md
  ├─ Quick Start (3 steps) ──→ Run commands, inspect UI
  ├─ Document Overview ──────→ Choose next document
  └─ Common Scenarios ───────→ Quick diagnosis
  ↓
CHOOSE PATH:
  ↓
  ├─ QUICK (20 min) ────→ COMPLETE.md + commands + visual check
  ├─ THOROUGH (60 min) ─→ GUIDE.md + CHECKLIST.md + full evidence
  └─ MINIMAL (10 min) ──→ Commands only + blue banner check
  ↓
INVESTIGATION PHASE
  ↓
  ├─ Backend Check ─────→ verify_usg_template_resolution command
  ├─ Frontend Check ────→ Debug panels + screenshots
  ├─ Console Check ─────→ Browser DevTools
  └─ Interaction Test ──→ Field behavior testing
  ↓
ANALYSIS PHASE
  ↓
  ├─ Use CHECKLIST.md ──→ Systematic evidence collection
  ├─ Use GUIDE.md ──────→ Diagnosis flowchart
  └─ Use TOOLS.md ──────→ Interpret debug panel output
  ↓
ROOT CAUSE IDENTIFIED
  ↓
APPLY FIX
  ↓
VERIFY FIX
  ↓
CLEANUP (Remove debug tools)
  ↓
DOCUMENT & PR
  ↓
DONE ✅
```

---

## 🎯 Use Case Guide

### Use Case 1: "I need to investigate NOW"
1. Open: `README_USG_INVESTIGATION.md`
2. Follow: Quick Start section (3 steps)
3. Time: 15 minutes
4. Outcome: High-level diagnosis

### Use Case 2: "I need proof for a bug report"
1. Open: `USG_INVESTIGATION_CHECKLIST.md`
2. Fill out: All sections with screenshots
3. Time: 30 minutes
4. Outcome: Complete evidence package

### Use Case 3: "I'm stuck and need help"
1. Open: `USG_INVESTIGATION_GUIDE.md`
2. Find: Your symptom in diagnosis table
3. Follow: Flowchart to root cause
4. Time: 10 minutes
5. Outcome: Next steps identified

### Use Case 4: "What does this debug panel mean?"
1. Open: `USG_DEBUG_TOOLS_ADDED.md`
2. Find: Debug panel section
3. Read: Explanation + verification points
4. Time: 5 minutes
5. Outcome: Panel output interpreted

### Use Case 5: "I need to brief my team"
1. Open: `USG_INVESTIGATION_COMPLETE.md`
2. Share: Summary section
3. Time: 5 minutes to read, 2 minutes to explain
4. Outcome: Team understands investigation

### Use Case 6: "Which document do I need?"
1. Open: `USG_INVESTIGATION_INDEX.md` (this file)
2. Find: Use case that matches yours
3. Time: 2 minutes
4. Outcome: Right document identified

---

## 📊 File Statistics

### Documentation
- Total files: 7
- Total pages (estimated): ~50
- Total words (estimated): ~15,000
- Reading time (all): ~2 hours
- Essential reading time: ~20 minutes

### Code Changes
- Frontend files modified: 1
- Backend files added: 2
- Backend files already working: 3
- Lines of code added (frontend): ~100
- Lines of code added (backend): ~300

---

## ✅ Validation Checklist

Before starting investigation, verify:

- [ ] All 7 documentation files exist and are readable
- [ ] Frontend file has debug panels added (check `UsgStudyEditorPage.tsx`)
- [ ] Backend verification command exists and runs
- [ ] You've read `README_USG_INVESTIGATION.md`
- [ ] You have `USG_INVESTIGATION_CHECKLIST.md` open
- [ ] Prerequisites met (backend accessible, frontend can start)

---

## 🚀 Quick Commands

### Backend Verification
```bash
cd backend
source ../.venv/bin/activate
python manage.py verify_usg_template_resolution
```

### Frontend Start
```bash
cd frontend
npm run dev
```

### Find Documentation
```bash
# All investigation docs
ls -1 USG_*.md

# All code files
find . -name "*template_resolution*" -o -name "UsgStudyEditorPage.tsx"
```

---

## 📞 Getting Help

### If Commands Don't Work
- Check virtualenv path: `source .venv/bin/activate`
- Check Python version: `python --version` (need 3.8+)
- Check Django installed: `pip list | grep -i django`

### If Frontend Won't Start
- Check Node version: `node --version` (need 16+)
- Run: `npm install` first
- Check port: Default is 5173, may vary

### If Can't Find Files
- Check current directory: `pwd`
- Should be in: `/home/munaim/srv/apps/radreport`
- List docs: `ls -la *.md`

### If Debug Panels Don't Show
- Check file modified correctly: `git diff frontend/src/views/UsgStudyEditorPage.tsx`
- Restart dev server: `npm run dev`
- Hard refresh browser: Ctrl+Shift+R

---

## 🔄 Update History

- **2026-01-22**: Initial investigation tools added
  - All documentation files created
  - Frontend debug panels added
  - Backend verification commands added
  - No patches applied yet (investigation phase only)

---

## 📌 Important Notes

1. **These are investigation tools, not fixes**
   - Purpose is to collect evidence
   - Patches should only be applied AFTER evidence proves root cause

2. **Debug tools should be removed after fix**
   - They're temporary for investigation
   - Remove before production deployment

3. **Backend verification is critical**
   - Always run backend check first
   - Frontend symptoms often have backend root causes

4. **Evidence is required**
   - Screenshots, logs, filled checklist
   - Needed for bug reports and PRs

5. **Minimal patches only**
   - Fix the proven root cause
   - Don't add unnecessary changes

---

## 🎓 Learning Path

### For Newcomers (2 hours)
1. Read: `README_USG_INVESTIGATION.md` (5 min)
2. Read: `USG_INVESTIGATION_GUIDE.md` (15 min)
3. Skim: `USG_DEBUG_TOOLS_ADDED.md` (10 min)
4. Run: Backend verification (5 min)
5. Test: Frontend inspection (15 min)
6. Practice: Fill partial checklist (30 min)
7. Review: Example scenarios (15 min)
8. Understand: Diagnosis flowchart (10 min)

### For Experienced (30 minutes)
1. Skim: `README_USG_INVESTIGATION.md` (2 min)
2. Run: Backend verification (3 min)
3. Test: Frontend visual check (5 min)
4. Use: Checklist for evidence (20 min)

### For Experts (10 minutes)
1. Run: Backend command (2 min)
2. Check: Debug panels only (3 min)
3. Diagnose: Based on evidence (5 min)

---

## 🏁 Success Metrics

Investigation is complete when:

| Metric | Target | How to Verify |
|--------|--------|---------------|
| Backend verification | All ✅ | Run command, check output |
| Frontend panels visible | 5 panels | Visual inspection |
| Evidence collected | Screenshots + logs | Check checklist |
| Root cause identified | 1 primary cause | Diagnosis section filled |
| Minimal patch proposed | <20 lines changed | Code diff review |
| Fix verified | All tests pass | Re-run verification |
| Debug removed | No debug code | Git diff check |
| PR created | 1 PR with proof | GitHub/GitLab |

---

## 🎯 Final Recommendation

**Start with**: [`README_USG_INVESTIGATION.md`](./README_USG_INVESTIGATION.md)  
**Follow with**: [`USG_INVESTIGATION_CHECKLIST.md`](./USG_INVESTIGATION_CHECKLIST.md)  
**Reference**: Other documents as needed

**Estimated total time**: 30-60 minutes from start to root cause identification

---

**Need more help? Check the appropriate document from the index above. Good luck! 🚀**
