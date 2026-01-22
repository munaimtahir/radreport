# 🧪 USG Template System - Testing Guide

**Date**: January 22, 2026  
**Status**: Ready for manual testing

---

## ✅ What to Test

### Test 1: Template Import (5 min)

**Goal**: Verify Template Import Manager works

1. Login: https://rims.alshifalab.pk (admin / admin123)
2. Navigate: Settings → Template Import Manager
3. **Check**: Green success banner shows "✅ This is the correct interface for USG templates!"
4. Click "Choose File"
5. Upload a JSON template (use usg_kub_basic.json from backend/)
6. Click "Validate Package"
7. **Check**: Validation passes, shows sections count
8. Select "Create New"
9. Click "Import"
10. **Check**: Success message appears

**Expected Result**: Template imported successfully ✅

---

### Test 2: Report Entry with Sections (10 min)

**Goal**: Verify template renders with sections, NA checkboxes, checklists

1. Navigate: Registration
2. Register new patient
3. Add service: US010 (Ultrasound KUB)
4. Note the Visit ID (e.g., 2601-0029)
5. Navigate: Report Entry → USG Worklist
6. Find your visit in Pending Visits
7. Click to open

**Check these**:
- [ ] Patient info shows at top
- [ ] Service name shows: "Ultrasound KUB"
- [ ] Template name shows: "Ultrasound KUB (Basic)"
- [ ] **Sections visible**: Right Kidney, Left Kidney, Ureters, Urinary Bladder
- [ ] Fields organized under each section
- [ ] **NA checkboxes** visible next to field labels
- [ ] **Checklist options** show as multiple choices:
  - Size: Normal, Enlarged, Small (can check multiple)
  - Hydronephrosis: Absent, Mild, Moderate, Severe
  - Etc.
- [ ] Can check/uncheck checklist options
- [ ] Can toggle NA checkboxes
- [ ] Text fields work (Additional findings)
- [ ] Heading fields show as section headers

**Expected Result**: Organized form with sections and proper field types ✅

---

### Test 3: Multiple USG Services (5 min)

**Goal**: Verify multiple USG service support

1. Register new patient
2. Add TWO USG services:
   - US010 (Ultrasound KUB)
   - US008 (Ultrasound Abdomen)
3. Go to USG Worklist
4. Select the visit

**Check these**:
- [ ] Blue banner appears: "📋 Multiple USG Services (2) - Select which service to report:"
- [ ] Two buttons show:
  - "1. Ultrasound KUB (REGISTERED)"
  - "2. Ultrasound Abdomen (REGISTERED)"
- [ ] Can click each button to switch services
- [ ] Form updates when switching
- [ ] Can enter separate report for each service
- [ ] Status indicator shows which service is being edited

**Expected Result**: Can switch between services and enter multiple reports ✅

---

### Test 4: Save and Submit Workflow (10 min)

**Goal**: Verify workflow transitions work

1. Open a USG report (from Test 2 or 3)
2. Fill some fields:
   - Check "Normal" for Size
   - Check "Preserved" for Corticomedullary differentiation
   - Toggle NA for Calculi
   - Add text in Additional findings
3. Click "Save Draft"
4. **Check**: Success message "Draft saved successfully"
5. Reload page
6. **Check**: Values persist
7. Click "Submit for Verification"
8. **Check**: Success message appears
9. Navigate: Verification tab
10. **Check**: Your report appears in the list
11. Click report
12. Review and verify
13. Click "Publish" or appropriate action

**Expected Result**: Full workflow works from entry to verification to publish ✅

---

### Test 5: Receipts Include USG (5 min)

**Goal**: Verify USG services show on receipts

1. Find a visit with USG service (US010)
2. Generate or view receipt
3. **Check**: Receipt PDF includes:
   - Service name: "Ultrasound KUB"
   - Service price
   - Line item shows clearly

**Expected Result**: USG services visible on receipts ✅

---

### Test 6: Frontend Warnings (2 min)

**Goal**: Verify warnings prevent using wrong pages

1. Navigate: Settings → Report Templates
2. **Check**: Yellow warning banner shows:
   - "⚠️ Important: This page manages flat templates without sections."
   - Link to Template Import Manager for USG

3. Navigate: Settings → Service Templates
4. **Check**: Yellow warning banner shows:
   - "⚠️ For USG Services: Use backend command..."
   - Shows command to use

**Expected Result**: Users directed to correct interfaces ✅

---

### Test 7: Template Import Manager (3 min)

**Goal**: Verify correct interface is highlighted

1. Navigate: Settings → Template Import Manager
2. **Check**: Green success banner shows:
   - "✅ This is the correct interface for USG templates!"
   - Mentions sections, NA support, checklists
   - Shows command hint for linking services

**Expected Result**: Correct interface clearly marked ✅

---

## 🔍 Verification Checklist

After all tests, verify:

### Backend:
- [ ] Health check returns OK
- [ ] Template imported in database
- [ ] Service linked to template
- [ ] TemplateVersion has sections in schema

### Frontend:
- [ ] Report entry shows sections
- [ ] NA checkboxes visible and functional
- [ ] Checklists allow multiple selections
- [ ] Can enter multiple reports per visit
- [ ] Warnings show on wrong pages
- [ ] Success banner shows on correct page

### Workflow:
- [ ] Draft saves successfully
- [ ] Submit transitions to PENDING_VERIFICATION
- [ ] Report appears in Verification tab
- [ ] Can verify/publish reports
- [ ] PDF generates

### Data:
- [ ] Receipts include USG services
- [ ] Service snapshots populated
- [ ] Report data persists correctly

---

## 🆘 Troubleshooting

### Template Not Showing?
```bash
python manage.py shell
>>> from apps.templates.models import Template
>>> Template.objects.filter(code='USG_KUB_BASIC').exists()
# Should be True
```

### No Sections?
```python
>>> from apps.templates.models import TemplateVersion
>>> tv = TemplateVersion.objects.filter(template__code='USG_KUB_BASIC', is_published=True).first()
>>> len(tv.schema.get('sections', []))
# Should be 4
```

### Service Not Linked?
```python
>>> from apps.catalog.models import Service
>>> s = Service.objects.get(code='US010')
>>> s.default_template
# Should show Template object
```

### Report Not in Verification?
```python
>>> from apps.workflow.models import ServiceVisitItem
>>> ServiceVisitItem.objects.filter(department_snapshot='USG', status='PENDING_VERIFICATION').count()
# Should include your report
```

---

## 📊 Expected Test Results

| Test | Expected Result | Time |
|------|----------------|------|
| Template Import | ✅ Success | 5 min |
| Report Entry Sections | ✅ Visible | 10 min |
| Multiple USG Services | ✅ Selector shows | 5 min |
| Workflow | ✅ End-to-end works | 10 min |
| Receipts | ✅ USG included | 5 min |
| Frontend Warnings | ✅ Visible | 2 min |
| Template Import Manager | ✅ Success banner | 3 min |
| **Total** | **All pass** | **40 min** |

---

## 🎉 Success Criteria

All tests should pass:
- ✅ Template import works via frontend
- ✅ Sections render properly
- ✅ NA checkboxes functional
- ✅ Checklists allow multiple selections
- ✅ Multiple USG service selector works
- ✅ Workflow completes successfully
- ✅ Receipts include USG services
- ✅ Warnings guide users correctly

---

## 📞 After Testing

### If All Tests Pass:
1. 🎉 Celebrate! Everything works!
2. Generate more templates using AI prompt
3. Import Abdomen, Pelvis, Breast templates
4. Train users on system

### If Any Test Fails:
1. Check troubleshooting section above
2. Review logs: `docker compose logs backend --tail=100`
3. Verify commands ran successfully
4. Check documentation for specific issue

---

**Ready to test?** Start with Test 1!

**Documentation**: `template_guide/` folder  
**Commands**: See `template_guide/QUICK_START.md`  
**Support**: Check `template_guide/INDEX.md`

---

**Created**: January 22, 2026  
**Testing Time**: 40 minutes total  
**All systems**: ✅ Ready for testing

🧪 **Happy testing!** 🧪
