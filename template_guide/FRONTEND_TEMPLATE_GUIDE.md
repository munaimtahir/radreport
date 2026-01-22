# Frontend Template Upload Guide

**Date**: January 22, 2026  
**Critical**: Use the CORRECT UI for USG templates!

---

## 🎯 Which Frontend Page to Use?

### ✅ FOR USG TEMPLATES (With Sections) - USE THIS!

**Page**: **Template Import Manager**  
**URL**: `https://rims.alshifalab.pk/admin/templates/import`  
**API**: `/api/template-packages/import/`  
**Models**: Template → TemplateVersion (CORRECT!)  
**Supports**: Sections, NA options, checklists  

**This is the CORRECT interface for USG templates!**

### ❌ FOR NON-USG TEMPLATES ONLY (Flat Structure)

**Page**: **Report Templates**  
**URL**: `https://rims.alshifalab.pk/admin/report-templates`  
**API**: `/api/report-templates/`  
**Models**: ReportTemplate (Flat, NO sections)  
**Supports**: Only flat field list, no sections  

**DO NOT use this for USG templates!**

---

## 📊 Frontend Pages Breakdown

### 1. Template Import Manager ✅ CORRECT FOR USG

**File**: `frontend/src/views/TemplateImportManager.tsx`

**What it does**:
- Upload JSON template files
- Validates against schema
- Creates Template + TemplateVersion
- Preserves sections structure
- **This is what you want for USG!**

**How to use**:
1. Go to: https://rims.alshifalab.pk/admin/templates/import
2. Click "Choose File"
3. Select your JSON template (with sections)
4. Click "Validate Package"
5. Select "Create New" or "Update Existing"
6. Click "Import"

**API Endpoints Used**:
```
POST /api/template-packages/validate/  (validates JSON)
POST /api/template-packages/import/    (imports template)
```

**Backend Handler**:
```python
# backend/apps/templates/api.py - TemplatePackageViewSet
class TemplatePackageViewSet(viewsets.ViewSet):
    @action(detail=False, methods=["post"])
    def validate(self, request):
        # Validates JSON structure
        
    @action(detail=False, methods=["post"])
    def import_(self, request):
        # Uses TemplatePackageEngine.import_package()
        # Creates Template + TemplateVersion
        # ✅ CORRECT SYSTEM!
```

### 2. Report Templates ❌ WRONG FOR USG

**File**: `frontend/src/views/ReportTemplates.tsx`

**What it does**:
- Manages flat ReportTemplate records
- Creates/edits fields without sections
- **DO NOT use for USG!**

**API Endpoints Used**:
```
GET  /api/report-templates/           (lists flat templates)
POST /api/report-templates/           (creates flat template)
PUT  /api/report-templates/{id}/fields/  (saves flat fields)
```

**Backend Handler**:
```python
# backend/apps/templates/api.py - ReportTemplateViewSet
class ReportTemplateViewSet(viewsets.ModelViewSet):
    queryset = ReportTemplate.objects.all()
    # ❌ WRONG MODEL - No sections!
```

### 3. Service Templates ❌ WRONG FOR USG

**File**: `frontend/src/views/ServiceTemplates.tsx`

**What it does**:
- Links services to ReportTemplate
- **DO NOT use for USG services!**

**API Endpoints Used**:
```
GET  /api/services/{id}/templates/      (lists service links)
POST /api/services/{id}/templates/      (creates link to ReportTemplate)
```

**Backend Handler**:
```python
# backend/apps/catalog/api.py - ServiceViewSet
@action(detail=True, methods=["get", "post"])
def templates(self, request, pk=None):
    # Links to ServiceReportTemplate model
    # Which links to ReportTemplate (WRONG for USG!)
```

---

## 🔧 The Correct Workflow for USG

### Step 1: Generate Template JSON

Use AI prompt from `TEMPLATE_GENERATION_PROMPT.md`:

```json
{
  "code": "USG_KUB_BASIC",
  "name": "Ultrasound KUB (Basic)",
  "category": "USG",
  "sections": [
    {
      "title": "Right Kidney",
      "order": 1,
      "fields": [...]
    }
  ]
}
```

### Step 2: Import via Frontend

1. **Login**: https://rims.alshifalab.pk
2. **Navigate**: Settings → **Template Import Manager** (or `/admin/templates/import`)
3. **Upload**: Select your JSON file
4. **Validate**: Click "Validate Package"
5. **Import**: Click "Import as New Template"

### Step 3: Link Service to Template (Backend)

**Option A: Via Management Command** (Recommended):
```bash
python manage.py import_usg_template /path/to/template.json --link-service=USG_KUB
```

**Option B: Via Django Shell**:
```python
python manage.py shell
>>> from apps.catalog.models import Service
>>> from apps.templates.models import Template
>>> service = Service.objects.get(code='USG_KUB')
>>> template = Template.objects.get(code='USG_KUB_BASIC')
>>> service.default_template = template
>>> service.save()
```

**Option C: Via Django Admin**:
1. Go to: https://rims.alshifalab.pk/admin/catalog/service/
2. Find your USG service
3. Edit it
4. Set "Default template" field to your imported template
5. Save

### Step 4: Test

1. Register patient with USG service
2. Go to USG Worklist
3. Select visit
4. **Verify**: Sections show up properly
5. **Verify**: NA checkboxes visible
6. **Verify**: Checklist options work

---

## 🚨 Common Mistakes

### Mistake 1: Using Report Templates Page for USG

**Wrong**:
```
1. Go to "Report Templates" page
2. Click "Create Template"
3. Add fields manually (no sections!)
4. Save
❌ Result: Flat template, no sections, doesn't work for USG!
```

**Correct**:
```
1. Generate JSON with sections
2. Go to "Template Import Manager" page
3. Upload JSON
4. Import
✅ Result: Sectioned template, works perfectly for USG!
```

### Mistake 2: Linking Service via Service Templates Page

**Wrong**:
```
1. Go to "Service Templates" page
2. Select USG service
3. Select template
4. Click "Attach"
❌ Result: Links to ReportTemplate (wrong model!)
```

**Correct**:
```bash
# Use management command or Django admin
python manage.py import_usg_template /tmp/template.json --link-service=USG_KUB
✅ Result: Links to Template (correct model!)
```

---

## 📋 API Endpoint Reference

| Endpoint | Model | Use For | Status |
|----------|-------|---------|--------|
| `/api/template-packages/import/` | Template/TemplateVersion | ✅ USG templates | CORRECT |
| `/api/template-packages/validate/` | Template/TemplateVersion | ✅ Validate USG JSON | CORRECT |
| `/api/templates/` | Template | ✅ List USG templates | CORRECT |
| `/api/template-versions/` | TemplateVersion | ✅ Template versions | CORRECT |
| `/api/report-templates/` | ReportTemplate | ❌ Flat templates only | WRONG FOR USG |
| `/api/services/{id}/templates/` | ServiceReportTemplate | ❌ Links to wrong model | WRONG FOR USG |

---

## 🎯 Quick Reference

### To Import USG Template:

**Frontend**:
1. Go to: `https://rims.alshifalab.pk/admin/templates/import`
2. Upload JSON
3. Click Import

**Backend (recommended)**:
```bash
python manage.py import_usg_template /tmp/template.json --link-service=USG_KUB
```

### To Check What's Linked:

```bash
python manage.py shell
>>> from apps.catalog.models import Service
>>> service = Service.objects.get(code='USG_KUB')
>>> print(f"Linked to: {service.default_template}")  # Should show Template, not ReportTemplate!
```

### To Verify Template Has Sections:

```python
>>> from apps.templates.models import TemplateVersion
>>> tv = TemplateVersion.objects.filter(template__code='USG_KUB_BASIC', is_published=True).first()
>>> print(f"Sections: {len(tv.schema.get('sections', []))}")
```

---

## ✅ Summary

| Task | Use This | Not This |
|------|----------|----------|
| **Upload USG template** | Template Import Manager | ❌ Report Templates page |
| **Link USG service** | `import_usg_template` command | ❌ Service Templates page |
| **Verify template** | Check Template/TemplateVersion | ❌ Check ReportTemplate |
| **Edit USG template** | Re-import JSON | ❌ Report Templates editor |

---

## 🔮 Future Enhancement (Optional)

We could create a new frontend page specifically for USG template management:

**New Page**: "USG Template Manager"
- List all Templates (with sections)
- Show which services are linked
- Import/export functionality
- Visual section editor

But for now, **Template Import Manager works perfectly!** ✅

---

**Key Takeaway**: 

✅ **USE**: Template Import Manager (`/admin/templates/import`)  
❌ **DON'T USE**: Report Templates page for USG  

**The Template Import Manager is already connected to the CORRECT model system!**

---

**Date**: January 22, 2026  
**Status**: Current frontend setup is CORRECT, just use the right page!
