# USG System Consolidation Plan
**Date**: January 22, 2026
**Status**: ANALYSIS & IMPLEMENTATION PLAN

---

## Problem Summary

The user has reported 5 critical issues with the USG reporting system:

1. **UI Issue**: USG JSON templates not showing "na" options or proper checklists
2. **Workflow Issue**: Reports don't appear under verification tab after submission
3. **Multiple Reports Issue**: No option to enter multiple reports when patient has multiple ultrasound services
4. **Static Files Issue**: Backend working but static files not being collected properly
5. **Model Confusion**: Too many overlapping models causing confusion and logic errors

---

## Current System Architecture

### Two Competing USG Systems

#### System A: USG App (apps/usg/) - **NEW, PROPER DESIGN**
**Models**:
- `UsgTemplate` - Stores schema_json with full template definition
- `UsgStudy` - Main study record with status (draft/verified/published)
- `UsgFieldValue` - **HAS `is_not_applicable` field** ✅
- `UsgPublishedSnapshot` - Immutable published version
- `UsgServiceProfile` - Maps services to templates

**Status**: Fully implemented, has proper NA support, NOT being used by frontend

**API Endpoints**:
- `/api/usg/templates/` - Template management
- `/api/usg/studies/` - Study management
- `/api/usg/studies/{id}/values/` - Bulk field value updates
- `/api/usg/studies/{id}/publish/` - Publish workflow

#### System B: Workflow App (apps/workflow/) - **OLD, CURRENTLY USED**
**Models**:
- `USGReport` - Legacy report model
- Uses `template_version` → links to old Template system
- Stores data in `report_json` field
- **NO proper `is_not_applicable` support** ❌

**Status**: Being used by frontend (USGWorklistPage.tsx), lacks proper NA support

**API Endpoints**:
- `/api/workflow/usg/` - Currently used by frontend
- `/api/workflow/usg/{id}/submit_for_verification/` - Verification submission

### Template System Confusion

#### Old Template System (apps/templates/)
- `Template` - Base template
- `TemplateVersion` - Versioned schemas
- `TemplateSection` - Section organization
- `TemplateField` - Individual fields

**Status**: Used by USGReport (System B), has sections, used in some places

#### New Template System (apps/templates/)
- `ReportTemplate` - Flat template
- `ReportTemplateField` - Flat fields (NO sections)
- `ReportTemplateFieldOption` - Field options
- `ServiceReportTemplate` - Service linking

**Status**: Used by template editor UI, flat structure, used in other places

---

## Root Cause Analysis

### Issue 1: NA Options Not Showing
**Cause**: 
- Frontend uses `/workflow/usg/` API (System B)
- USGReport model stores data in flat `report_json` without NA support
- UsgFieldValue model (System A) has `is_not_applicable` field but isn't being used
- ReportTemplate checkbox fields show only "Yes" checkbox, no NA option UI

**Evidence from Screenshots**:
- Screenshot 1 & 2: Checkbox fields only show "Yes" label, no NA checkbox
- Template editor shows field type "Checkbox" but no NA configuration

### Issue 2: Verification Workflow Not Working
**Cause**:
- ServiceVisitItem status transitions not working correctly
- Status should go: REGISTERED → IN_PROGRESS → PENDING_VERIFICATION → PUBLISHED
- Verification tab likely filters by PENDING_VERIFICATION status
- USGReport.submit_for_verification() might not update ServiceVisitItem.status

**Code Location**: 
- `apps/workflow/api.py` line 414: `submit_for_verification` endpoint
- Need to verify if ServiceVisitItem.status is updated

### Issue 3: Multiple Reports Per Visit
**Cause**:
- Frontend selects single USG item from visit
- Line 217-218 in USGWorklistPage.tsx: `usgItem = visit.items?.find(item => item.department_snapshot === "USG")`
- Uses `.find()` which only gets first USG item
- No UI to select which USG service to report on when multiple exist

### Issue 4: Static Files Not Collected
**Cause**: Likely deployment/configuration issue
- Need to run `python manage.py collectstatic`
- STATIC_ROOT and STATIC_URL configuration
- Frontend build may not be up to date

### Issue 5: Too Many Overlapping Models
**Cause**: 
- Multiple template systems developed at different times
- Two USG report systems (UsgStudy vs USGReport)
- Unclear which models are actually in use

---

## Consolidation Strategy

### Phase 1: Model Deprecation Plan

#### Keep (Active Models):
1. **USG Reporting** - System A (apps/usg/):
   - ✅ `UsgTemplate`
   - ✅ `UsgStudy`
   - ✅ `UsgFieldValue` (has is_not_applicable)
   - ✅ `UsgPublishedSnapshot`
   - ✅ `UsgServiceProfile`

2. **Template Management** - New system (apps/templates/):
   - ✅ `ReportTemplate`
   - ✅ `ReportTemplateField`
   - ✅ `ReportTemplateFieldOption`
   - ✅ `ServiceReportTemplate`

#### Deprecate (Mark for removal):
1. **Old USG System**:
   - ❌ `USGReport` (workflow app) - Replace with UsgStudy
   - ❌ `Report` (reporting app) - Generic, not USG specific

2. **Old Template System**:
   - ❌ `Template` - Replace with ReportTemplate
   - ❌ `TemplateVersion` - Versioning moved to ReportTemplate.version field
   - ❌ `TemplateSection` - Flatten to fields only
   - ❌ `TemplateField` - Replace with ReportTemplateField

### Phase 2: Implementation Plan

#### Step 1: Fix Static Files (Immediate)
```bash
# Run collectstatic
python manage.py collectstatic --no-input

# Verify STATIC_ROOT in settings.py
# Ensure nginx/apache serving static files correctly
```

#### Step 2: Fix NA Options UI (Immediate)
Update `ReportTemplateField` model to support NA:
- Add `na_allowed` boolean field
- Update serializer to include na_allowed
- Update frontend to render NA checkbox when na_allowed=True

#### Step 3: Fix Verification Workflow (Immediate)
Update `USGReport.submit_for_verification()`:
- Ensure ServiceVisitItem.status is updated to PENDING_VERIFICATION
- Add status audit log entry
- Trigger ServiceVisit.update_derived_status()

#### Step 4: Fix Multiple Reports (Medium Priority)
Update USGWorklistPage.tsx:
- Show all USG items in visit, not just first one
- Allow selecting which item to report on
- UI: Dropdown or tabs to switch between services

#### Step 5: Migration to New System (Long-term)
1. Create data migration from USGReport to UsgStudy
2. Update frontend to use `/api/usg/studies/` instead of `/api/workflow/usg/`
3. Update all USG-related views to use new API
4. Mark old models as deprecated
5. Eventually remove old models after migration complete

---

## Immediate Action Items

### Priority 1 (Fix Today):
1. ✅ Document current state (this file)
2. 🔧 Run collectstatic and verify static files
3. 🔧 Add na_allowed field to ReportTemplateField
4. 🔧 Update frontend to render NA checkbox
5. 🔧 Fix verification workflow status update

### Priority 2 (Fix This Week):
6. 🔧 Add multiple report entry UI
7. 🔧 Create model deprecation plan
8. 🔧 Add warnings to deprecated models

### Priority 3 (Plan for Migration):
9. 📋 Design data migration strategy
10. 📋 Create migration scripts
11. 📋 Test migration on staging
12. 📋 Execute migration on production

---

## Technical Details

### ReportTemplate NA Support Implementation

**Database Change**:
```python
# Add to ReportTemplateField model
na_allowed = models.BooleanField(
    default=False, 
    help_text="Allow 'Not Applicable' option for this field"
)
```

**Serializer Update**:
```python
class ReportTemplateFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportTemplateField
        fields = [..., 'na_allowed']
```

**Frontend Update** (USGWorklistPage.tsx):
```typescript
// Add NA state management
const [naState, setNaState] = useState<Record<string, boolean>>({});

// Render NA checkbox for fields that allow it
{field.na_allowed && (
  <label>
    <input 
      type="checkbox" 
      checked={naState[field.key] || false}
      onChange={(e) => handleNAToggle(field.key, e.target.checked)}
    />
    N/A
  </label>
)}
```

### Verification Workflow Fix

**Update submit_for_verification**:
```python
@action(detail=True, methods=['post'])
def submit_for_verification(self, request, pk=None):
    report = self.get_object()
    
    # Update item status
    if report.service_visit_item:
        report.service_visit_item.status = 'PENDING_VERIFICATION'
        report.service_visit_item.submitted_at = timezone.now()
        report.service_visit_item.save()
        
        # Update derived visit status
        report.service_visit_item.service_visit.update_derived_status()
        
        # Log status transition
        StatusAuditLog.objects.create(
            service_visit_item=report.service_visit_item,
            service_visit=report.service_visit_item.service_visit,
            from_status='IN_PROGRESS',
            to_status='PENDING_VERIFICATION',
            changed_by=request.user
        )
    
    return Response({'detail': 'Submitted for verification'})
```

---

## Success Criteria

- ✅ NA checkboxes visible and functional in template editor and report entry
- ✅ Reports appear in verification tab after submission
- ✅ Can enter multiple reports when multiple USG services ordered
- ✅ Static files properly served, no 404s
- ✅ Clear documentation of which models are active vs deprecated
- ✅ All existing reports continue to work during migration

---

## Next Steps

1. Review this plan with stakeholders
2. Implement Priority 1 fixes
3. Test on staging environment
4. Deploy to production
5. Begin Priority 2 work

---

**Prepared by**: AI Assistant  
**For Review by**: Development Team  
**Last Updated**: January 22, 2026
