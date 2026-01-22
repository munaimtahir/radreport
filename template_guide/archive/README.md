# Archive - Old USG Investigation Files

**Date**: January 22, 2026  
**Status**: ARCHIVED - Superseded by current solution

---

## About This Archive

These files document a **previous investigation** into USG field rendering issues that identified a **field key mismatch** problem (backend sending `key` vs frontend expecting `field_key`).

---

## Why Archived?

The current investigation (January 22, 2026) revealed a **more fundamental issue**:

- **Previous Issue**: Field key naming mismatch
- **Current Issue**: Wrong template system being used entirely!
  - ReportTemplate (flat, no sections) ❌
  - Template/TemplateVersion (sectioned) ✅

The current fix addresses the root cause, making these investigation files obsolete.

---

## Files in This Archive

1. `USG_INVESTIGATION_RESULTS_2026_01_22.md` - Field key investigation results
2. `USG_DEBUG_TOOLS_ADDED.md` - Debug panels added to frontend
3. `USG_INVESTIGATION_CHECKLIST.md` - Investigation checklist
4. `USG_INVESTIGATION_COMPLETE.md` - Previous completion notice
5. `USG_INVESTIGATION_GUIDE.md` - Investigation methodology
6. `USG_INVESTIGATION_INDEX.md` - Previous investigation index
7. `README_USG_INVESTIGATION.md` - Previous investigation readme
8. `USG_FILE_MANIFEST.md` - File manifest from previous work
9. `USG_FIX_SUMMARY_2026_01_22.md` - Previous fix summary

---

## Current Solution

**See**: `../START_HERE.md` for the complete, current solution

**Key Difference**:
- **Old approach**: Fix field key mismatch
- **New approach**: Use correct template system (Template/TemplateVersion)

---

## Historical Value

These files are kept for:
- Historical reference
- Understanding previous investigations
- Learning how the issue evolved
- Audit trail

**For current implementation, use the files in `template_guide/` root, not this archive.**

---

**Archived**: January 22, 2026  
**Reason**: Superseded by template system consolidation  
**Current docs**: See `template_guide/` folder
