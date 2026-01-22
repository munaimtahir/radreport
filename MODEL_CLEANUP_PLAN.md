# Template Model Cleanup Plan

**Date**: January 22, 2026  
**Status**: READY TO EXECUTE

---

## Current State - Too Many Template Models!

### KEEP - Active USG Template System ✅

**File**: `backend/apps/templates/models.py`

```python
# OLD SYSTEM - HAS SECTIONS (Keep for USG)
class Template(models.Model):
    # Base template with code/name
    
class TemplateVersion(models.Model):
    # Versioned schema with FULL JSON (including sections)
    schema = models.JSONField()  # ← STORES YOUR SECTIONED JSON!
    
class TemplateSection(models.Model):
    # Section grouping (used for database structure)
    
class TemplateField(models.Model):
    # Individual fields within sections
    
class FieldOption(models.Model):
    # Options for dropdown/checklist fields
```

**Status**: ✅ **KEEP - This is the correct system for USG!**

### DEPRECATE - Flat ReportTemplate System ❌

```python
# NEW SYSTEM - NO SECTIONS (Deprecate for USG)
class ReportTemplate(models.Model):
    # Flat template (no section support)
    
class ReportTemplateField(models.Model):
    # Flat fields (loses section organization)
    # We added na_allowed but it's not useful without sections
    
class ReportTemplateFieldOption(models.Model):
    # Options for fields
    
class ServiceReportTemplate(models.Model):
    # Links services to ReportTemplate (wrong system!)
```

**Status**: ❌ **DEPRECATE for USG - Keep only for non-sectioned reports (OPD, simple forms)**

---

## The Fix

### Step 1: Mark Models as Deprecated

Add deprecation warnings to ReportTemplate models:

```python
# backend/apps/templates/models.py

class ReportTemplate(models.Model):
    """
    DEPRECATED FOR USG: Use Template/TemplateVersion instead.
    This flat model does not support sections required by USG templates.
    Only use for simple, non-sectioned forms (OPD, etc.)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    # ... rest of fields
    
    class Meta:
        ordering = ["name"]
        verbose_name = "Report Template (Flat - Deprecated for USG)"
        verbose_name_plural = "Report Templates (Flat - Deprecated for USG)"
```

### Step 2: Update Service Model

Services should link to `Template` (not `ReportTemplate`):

```python
# backend/apps/catalog/models.py

class Service(models.Model):
    # ... existing fields ...
    
    # CORRECT - Links to Template (with sections)
    default_template = models.ForeignKey(
        'templates.Template', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text="Default template for this service (use for USG)"
    )
    
    # DEPRECATED - Don't use for USG
    # report_template = models.ForeignKey(
    #     'templates.ReportTemplate', 
    #     ...
    # )
```

### Step 3: Ensure USGReport Uses TemplateVersion

```python
# backend/apps/workflow/models.py

class USGReport(models.Model):
    # ... existing fields ...
    
    # CORRECT - Links to TemplateVersion (has sectioned schema)
    template_version = models.ForeignKey(
        "templates.TemplateVersion", 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text="Template version with sectioned schema"
    )
    
    # DON'T ADD - Would be wrong
    # report_template = models.ForeignKey('templates.ReportTemplate', ...)
```

---

## Migration Path

### Phase 1: Immediate (Do Now)

1. **Import your KUB template using the correct system**:
   ```bash
   python manage.py import_usg_template /tmp/usg_kub.json --link-service=USG_KUB
   ```

2. **Link all USG services to Template (not ReportTemplate)**:
   ```python
   python manage.py shell
   
   from apps.catalog.models import Service
   from apps.templates.models import Template
   
   # Map your services to templates
   mappings = {
       'USG_ABDOMEN': 'USG_ABDOMEN_BASIC',
       'USG_PELVIS': 'USG_PELVIS_BASIC',
       'USG_KUB': 'USG_KUB_BASIC',
       'USG_BREAST': 'USG_BREAST_BASIC',
       # Add all your USG services...
   }
   
   for service_code, template_code in mappings.items():
       try:
           service = Service.objects.get(code=service_code)
           template = Template.objects.get(code=template_code)
           service.default_template = template
           service.save()
           print(f"✓ Linked {service_code} → {template_code}")
       except Exception as e:
           print(f"✗ Failed {service_code}: {e}")
   ```

3. **Verify linkage**:
   ```python
   from apps.catalog.models import Service
   
   usg_services = Service.objects.filter(modality__code='USG')
   for s in usg_services:
       if s.default_template:
           print(f"✓ {s.code}: {s.default_template.name}")
       else:
           print(f"✗ {s.code}: NO TEMPLATE!")
   ```

### Phase 2: Testing (This Week)

1. Test report entry with newly linked templates
2. Verify sections show correctly
3. Verify NA checkboxes work
4. Verify report submission → verification workflow
5. Test PDF generation

### Phase 3: Cleanup (After Testing)

1. Add deprecation warnings to ReportTemplate admin
2. Hide ReportTemplate from main admin navigation (or mark as deprecated)
3. Document which apps still use ReportTemplate (if any)
4. Eventually: Remove ReportTemplate if not used by anything else

---

## Don't Delete - Just Deprecate!

**Don't actually delete ReportTemplate yet** because:

1. Other parts of the system might use it (OPD, etc.)
2. There might be existing data
3. Deprecation is safer than deletion

**Instead**:
- Add deprecation warnings
- Update documentation
- Stop using it for new USG templates
- Mark clearly in admin as "For non-USG use only"

---

## Verification Commands

### Check Template Exists
```bash
python manage.py shell

from apps.templates.models import Template, TemplateVersion
tv = TemplateVersion.objects.filter(
    template__code="USG_KUB_BASIC", 
    is_published=True
).first()

if tv:
    print(f"✓ Found: {tv.template.name}")
    print(f"  Sections: {len(tv.schema.get('sections', []))}")
else:
    print("✗ Template not found!")
```

### Check Service Linkage
```bash
from apps.catalog.models import Service
service = Service.objects.get(code="USG_KUB")

if service.default_template:
    print(f"✓ Linked to: {service.default_template.name}")
    versions = service.default_template.versions.filter(is_published=True)
    print(f"  Published versions: {versions.count()}")
else:
    print("✗ No template linked!")
```

### Check USGReport Linkage
```bash
from apps.workflow.models import USGReport
reports = USGReport.objects.filter(template_version__isnull=False)[:5]

for r in reports:
    print(f"Report {r.id}:")
    print(f"  Template: {r.template_version.template.name}")
    print(f"  Version: {r.template_version.version}")
    print(f"  Sections: {len(r.template_version.schema.get('sections', []))}")
```

---

## Summary

### What to Do

1. ✅ Import USG templates using `import_usg_template` command
2. ✅ Link services to `Template` (not `ReportTemplate`)
3. ✅ USGReport automatically uses `TemplateVersion`
4. ✅ Frontend receives sectioned schema in `template_schema`
5. ✅ Everything works with sections and NA support!

### What NOT to Do

1. ❌ Don't use `ReportTemplate` for USG templates
2. ❌ Don't delete models yet (deprecate first)
3. ❌ Don't manually create `TemplateVersion` records (use import)
4. ❌ Don't link services to `ReportTemplate` for USG

### Files to Ignore

These models exist but you don't need to touch them:
- `ReportTemplate` - Deprecated for USG, keep for other uses
- `ReportTemplateField` - Part of deprecated system
- `ServiceReportTemplate` - Links to wrong template system

---

## Next Steps

1. Run the import command for each USG template
2. Link services using the shell script above
3. Test one service end-to-end (registration → report → verification → publish)
4. Fix any issues found
5. Roll out to all USG services

---

**Remember**: The Template/TemplateVersion system (OLD) is correct for USG because it supports sections!

**Created**: January 22, 2026  
**Status**: Ready to implement
