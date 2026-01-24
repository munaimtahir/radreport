# UI Navigation Guide - Which Page to Use?

**Date**: January 22, 2026  
**Purpose**: Visual guide to avoid confusion

---

## 🎯 Quick Decision Tree

```
Do you need to upload a USG template with sections?
│
├─ YES → Use "Template Import Manager" ✅
│        https://rims.alshifalab.pk/admin/templates/import
│
└─ NO  → Is it a simple flat form (OPD, etc.)?
         │
         ├─ YES → Use "Report Templates" ✅
         │        https://rims.alshifalab.pk/admin/report-templates
         │
         └─ NO  → Use "Template Import Manager" ✅
```

---

## 📱 UI Pages Overview

### 1. Template Import Manager ✅ **USE THIS FOR USG!**

**URL**: `/admin/templates/import`  
**Purpose**: Import JSON templates with sections  
**Use for**: USG, any sectioned templates  
**Models**: Template → TemplateVersion (CORRECT!)

**What you'll see**:
```
┌─────────────────────────────────────────┐
│ Template Import Manager                 │
│ Import sectioned templates (USG, etc.)  │
├─────────────────────────────────────────┤
│ ✅ This is the correct interface for    │
│    USG templates!                       │
│    Upload JSON templates with sections, │
│    NA support, and checklists.          │
├─────────────────────────────────────────┤
│ 1. Select Template Package              │
│ [Choose File]                           │
│ [Validate Package]                      │
│                                         │
│ 2. Validation Result                    │
│ ✓ Package Valid                         │
│                                         │
│ 3. Import Options                       │
│ ○ Create New                            │
│ ○ Update Existing                       │
│ [Import]                                │
└─────────────────────────────────────────┘
```

**Features**:
- ✅ Validates JSON structure
- ✅ Preserves sections
- ✅ Supports NA options
- ✅ Handles checklists properly
- ✅ Creates versioned templates

### 2. Report Templates ⚠️ **NOT FOR USG!**

**URL**: `/admin/report-templates`  
**Purpose**: Manage flat templates (no sections)  
**Use for**: Simple forms (OPD notes, etc.)  
**Models**: ReportTemplate (Flat, NO sections)

**What you'll see**:
```
┌─────────────────────────────────────────┐
│ Report Templates                        │
│ For non-sectioned templates only        │
├─────────────────────────────────────────┤
│ ⚠️ Important: This page manages flat    │
│    templates without sections.          │
│    For USG templates (with sections):   │
│    Use Template Import Manager instead! │
├─────────────────────────────────────────┤
│ [Search templates...]                   │
│ [Create Template]  [Import JSON]        │
│                                         │
│ Template List:                          │
│ • Template 1                            │
│   [Edit] [Duplicate] [Export]          │
└─────────────────────────────────────────┘
```

**Limitations**:
- ❌ No sections (flat structure only)
- ❌ Not suitable for USG templates
- ✅ OK for simple flat forms

### 3. Service Templates ⚠️ **NOT FOR USG LINKING!**

**URL**: `/admin/service-templates`  
**Purpose**: Link services to flat templates  
**Use for**: Non-USG services only  
**Models**: ServiceReportTemplate → ReportTemplate (WRONG for USG!)

**What you'll see**:
```
┌─────────────────────────────────────────┐
│ Service Template Linking                │
│ For flat templates only                 │
├─────────────────────────────────────────┤
│ ⚠️ For USG Services: Use backend        │
│    command to link services to          │
│    sectioned templates.                 │
│    Command: python manage.py            │
│    import_usg_template ... --link-...   │
├─────────────────────────────────────────┤
│ [Search services...]                    │
│                                         │
│ Service List:                           │
│ • USG Abdomen                           │
│ • USG Pelvis                            │
└─────────────────────────────────────────┘
```

**Limitations**:
- ❌ Links to wrong model (ReportTemplate, not Template)
- ❌ Not suitable for USG services
- ✅ OK for non-USG services

---

## 🎨 Visual Comparison

### ✅ Correct Flow (USG Templates)

```
Step 1: Generate JSON
┌──────────────────┐
│ Use AI Prompt    │
│ Get JSON with    │
│ sections         │
└────────┬─────────┘
         │
         ↓
Step 2: Upload
┌──────────────────────────┐
│ Template Import Manager  │ ← Use this page!
│ /admin/templates/import  │
└────────┬─────────────────┘
         │
         ↓
Step 3: Link (Backend)
┌──────────────────────────┐
│ python manage.py         │
│ import_usg_template      │
│ --link-service=USG_XXX   │
└────────┬─────────────────┘
         │
         ↓
Step 4: Test
┌──────────────────────────┐
│ USG Worklist             │
│ - Sections show ✅       │
│ - NA checkboxes ✅       │
│ - Checklists work ✅     │
└──────────────────────────┘
```

### ❌ Wrong Flow (Don't Use for USG)

```
Step 1: Create Template
┌──────────────────────────┐
│ Report Templates page    │ ← Don't use for USG!
│ /admin/report-templates  │
│ - No sections            │
│ - Flat fields only       │
└────────┬─────────────────┘
         │
         ↓
Step 2: Link (Frontend)
┌──────────────────────────┐
│ Service Templates page   │ ← Don't use for USG!
│ /admin/service-templates │
│ - Links to wrong model   │
└────────┬─────────────────┘
         │
         ↓
Step 3: Test
┌──────────────────────────┐
│ USG Worklist             │
│ - No sections ❌         │
│ - No NA checkboxes ❌    │
│ - Doesn't work ❌        │
└──────────────────────────┘
```

---

## 🗺️ Site Navigation Map

```
https://rims.alshifalab.pk
│
├─ Dashboard
├─ WORKFLOW
│  ├─ Registration
│  ├─ Patient workflow
│  ├─ Report Entry → USG Worklist ← Report entry happens here
│  ├─ Verification
│  └─ Final Reports
│
└─ SETTINGS
   ├─ Consultants
   ├─ Report Templates ← ⚠️ For flat templates only (not USG!)
   ├─ Service Templates ← ⚠️ For flat templates only (not USG!)
   ├─ Template Import Manager ← ✅ USE THIS FOR USG!
   └─ Consultant Settlements
```

---

## 🔍 How to Identify Which Model You're Using

### Check in Django Admin

1. Go to: https://rims.alshifalab.pk/admin/
2. Look for "TEMPLATES" section

**You'll see**:
```
TEMPLATES
├─ Report template fields        ← ReportTemplate system (flat)
├─ Report templates              ← ReportTemplate system (flat)
├─ Service report templates      ← ReportTemplate system (flat)
├─ Template fields               ← Template system (sectioned) ✅
├─ Template sections             ← Template system (sectioned) ✅
├─ Template versions             ← Template system (sectioned) ✅
└─ Templates                     ← Template system (sectioned) ✅
```

### Check in Code

**Correct for USG**:
```python
from apps.templates.models import Template, TemplateVersion
template = Template.objects.get(code='USG_KUB_BASIC')
version = template.versions.filter(is_published=True).first()
sections = version.schema.get('sections', [])  # ✅ Has sections!
```

**Wrong for USG**:
```python
from apps.templates.models import ReportTemplate
template = ReportTemplate.objects.get(code='USG_KUB_BASIC')
fields = template.fields.all()  # ❌ Flat fields, no sections!
```

---

## 📊 API Endpoints Reference

| Endpoint | Model | Sections? | Use For |
|----------|-------|-----------|---------|
| `/api/template-packages/import/` | Template/TemplateVersion | ✅ Yes | USG templates |
| `/api/template-packages/validate/` | Template/TemplateVersion | ✅ Yes | Validate USG JSON |
| `/api/templates/` | Template | ✅ Yes | List templates |
| `/api/template-versions/` | TemplateVersion | ✅ Yes | List versions |
| `/api/report-templates/` | ReportTemplate | ❌ No | Flat templates only |
| `/api/services/{id}/templates/` | ServiceReportTemplate | ❌ No | Non-USG linking |

---

## ✅ Final Checklist

Before using the system:

- [x] Frontend updated with warnings ✅
- [x] Template Import Manager identified as correct ✅
- [x] Report Templates page marked as flat-only ✅
- [x] Service Templates page marked as non-USG ✅
- [x] Documentation created ✅
- [x] Commands created ✅
- [x] Static files collected ✅

**Everything is ready! Use Template Import Manager for USG templates.** 🎉

---

**Navigation**:
- **Start here**: `COMPLETE_SOLUTION.md` (overview)
- **Quick implementation**: `QUICK_START.md`
- **Frontend guide**: `FRONTEND_TEMPLATE_GUIDE.md` (this file)
- **Generate templates**: `TEMPLATE_GENERATION_PROMPT.md`

---

**Date**: January 22, 2026  
**Status**: ✅ Complete and verified
