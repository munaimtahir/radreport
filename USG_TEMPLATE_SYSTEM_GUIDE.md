# USG Template System - Complete Guide

**Date**: January 22, 2026  
**Status**: CRITICAL FIX NEEDED

---

## The Problem

You have **TWO template systems** that were created for different purposes:

### System A: Template/TemplateVersion (OLD - HAS SECTIONS) ✅
- **Structure**: Template → TemplateSection → TemplateField → FieldOption
- **Storage**: Schema stored in `TemplateVersion.schema` (JSONField with full section structure)
- **Used by**: USGReport model (via `template_version` ForeignKey)
- **Supports**: Sections, na_allowed, checklists, all field types
- **Status**: **THIS IS THE CORRECT SYSTEM FOR USG**

### System B: ReportTemplate (NEW - FLAT, NO SECTIONS) ❌
- **Structure**: ReportTemplate → ReportTemplateField (FLAT, no sections)
- **Storage**: Individual field records in database (loses section organization)
- **Used by**: Template editor UI
- **Supports**: Fields but NO section grouping
- **Status**: **WRONG FOR USG - Cannot handle your sectioned JSON**

---

## Your JSON Format

Your JSON template has this structure:

```json
{
  "code": "USG_KUB_BASIC",
  "name": "Ultrasound KUB (Basic)",
  "category": "USG",
  "sections": [           ← REQUIRES SECTIONS!
    {
      "title": "Right Kidney",
      "order": 1,
      "fields": [
        {
          "key": "rk_size",
          "label": "Size",
          "type": "checklist",  ← Maps to dropdown/checkbox
          "required": false,
          "na_allowed": true,
          "options": [...]
        }
      ]
    }
  ]
}
```

**This JSON REQUIRES the OLD Template system because it has sections!**

---

## How Template Import Works

File: `backend/apps/templates/engine.py` - `TemplatePackageEngine.import_package()`

When you import your JSON:

1. **Creates Template** (line 77-82):
   ```python
   template = Template.objects.create(
       code=code,
       name=data["name"],
       modality_code=data.get("category", "")
   )
   ```

2. **Creates TemplateVersion with FULL schema** (lines 117-139):
   ```python
   version = TemplateVersion.objects.create(
       template=template,
       version=next_version,
       schema=data,  ← YOUR FULL JSON WITH SECTIONS!
       is_published=True
   )
   ```

3. **Creates ReportTemplate (FLATTENED)** (lines 98-115):
   ```python
   report_template = ReportTemplate.objects.create(
       code=code,
       name=data["name"]
   )
   # Then creates ReportTemplateField (NO SECTIONS)
   ```

**Result**: TemplateVersion has your sectioned schema, ReportTemplate loses sections!

---

## The Correct Solution

### Step 1: Import Your Template Using The Engine

Create a management command or use the existing importer:

```bash
python manage.py import_template /path/to/your/template.json
```

Or via the API endpoint:

```bash
POST /api/templates/import/
Content-Type: application/json

{
  "code": "USG_KUB_BASIC",
  "name": "Ultrasound KUB (Basic)",
  "category": "USG",
  "sections": [...]
}
```

### Step 2: Link Service to Template (NOT ReportTemplate)

```python
from apps.catalog.models import Service
from apps.templates.models import Template

# Find your service
service = Service.objects.get(code="USG_KUB")

# Find the template
template = Template.objects.get(code="USG_KUB_BASIC")

# Set as default template for this service
service.default_template = template
service.save()
```

### Step 3: Verify Template Version Exists

```python
from apps.templates.models import TemplateVersion

# Check published version exists
version = TemplateVersion.objects.filter(
    template__code="USG_KUB_BASIC",
    is_published=True
).order_by('-version').first()

print(f"Template: {version.template.name}")
print(f"Version: {version.version}")
print(f"Sections: {len(version.schema.get('sections', []))}")
```

### Step 4: USGReport Will Auto-Link

When creating a USGReport, the system automatically:

```python
# In workflow/api.py - USGReportViewSet.create()
template_version = usg_item.service.default_template.versions.filter(
    is_published=True
).order_by("-version").first()

report = USGReport.objects.create(
    service_visit_item=usg_item,
    template_version=template_version,  ← Links to Template system!
    ...
)
```

---

## Frontend Rendering

The frontend (`USGWorklistPage.tsx`) should receive the template schema from the report:

```typescript
// From API response
const report = {
  id: "...",
  template_schema: {
    name: "Ultrasound KUB (Basic)",
    sections: [              ← SECTIONS PRESERVED!
      {
        title: "Right Kidney",
        fields: [
          {
            key: "rk_size",
            label: "Size",
            type: "checklist",
            na_allowed: true,
            options: [...]
          }
        ]
      }
    ]
  }
}

// Frontend renders sections properly
{templateSchema.sections.map((section) => (
  <div key={section.title}>
    <h3>{section.title}</h3>
    {section.fields.map((field) => (
      // Render field with NA support if na_allowed
    ))}
  </div>
))}
```

---

## Field Type Mapping

Your JSON uses these types, which map to the frontend:

| JSON Type | Frontend Renders | Notes |
|-----------|-----------------|-------|
| `heading` | `<h4>` | Section header |
| `short_text` | `<input type="text">` | Single line |
| `long_text` / `paragraph` | `<textarea>` | Multi-line |
| `number` | `<input type="number">` | Numeric |
| `dropdown` | `<select>` | Single choice |
| `checklist` | Multiple `<checkbox>` | Multi-select |
| `checkbox` / `boolean` | Single `<checkbox>` | Yes/No |
| `radio` | `<radio>` buttons | Single choice |
| `separator` | `<hr>` | Visual divider |

---

## Fixing The Receipt Issue

You mentioned: "USG services shown on registration but not printed on receipts"

### Check Receipt Template

File: `backend/apps/studies/templates/receipts/receipt_a4_dual.html`

Ensure USG services are included in the items list:

```django
{% for item in items %}
<tr>
    <td>{{ item.service_name_snapshot }}</td>
    <td>{{ item.quantity }}</td>
    <td>{{ item.unit_price }}</td>
    <td>{{ item.line_total }}</td>
</tr>
{% endfor %}
```

### Check ServiceVisitItem

```python
# Verify USG items have correct snapshots
usg_item = ServiceVisitItem.objects.get(id="...")
print(f"Service: {usg_item.service_name_snapshot}")
print(f"Department: {usg_item.department_snapshot}")
print(f"Price: {usg_item.price_snapshot}")
```

If snapshots are empty, fix in the save() method:

```python
# In ServiceVisitItem.save()
if not self.service_name_snapshot and self.service:
    self.service_name_snapshot = self.service.name
if not self.department_snapshot and self.service:
    self.department_snapshot = self.service.modality.code  # USG, CT, etc
if not self.price_snapshot and self.service:
    self.price_snapshot = self.service.price
```

---

## Command-Line Template Import

Create: `backend/apps/templates/management/commands/import_usg_template.py`

```python
from django.core.management.base import BaseCommand
from apps.templates.engine import TemplatePackageEngine
import json

class Command(BaseCommand):
    help = 'Import USG template from JSON file'

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str)
        parser.add_argument('--mode', type=str, default='create', choices=['create', 'update'])

    def handle(self, *args, **options):
        with open(options['json_file'], 'r') as f:
            data = json.load(f)
        
        try:
            result = TemplatePackageEngine.import_package(
                data, 
                mode=options['mode']
            )
            self.stdout.write(self.style.SUCCESS(
                f"Successfully imported template: {data['code']}"
            ))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Import failed: {str(e)}"))
```

Usage:

```bash
# Save your JSON to a file
cat > /tmp/usg_kub.json << 'EOF'
{
  "code": "USG_KUB_BASIC",
  "name": "Ultrasound KUB (Basic)",
  ...
}
EOF

# Import it
python manage.py import_usg_template /tmp/usg_kub.json

# Or update existing
python manage.py import_usg_template /tmp/usg_kub.json --mode=update
```

---

## Verification Workflow Fix

The verification workflow issue is separate. Fix in `workflow/api.py`:

```python
@action(detail=True, methods=['post'])
def submit_for_verification(self, request, pk=None):
    report = self.get_object()
    
    # CRITICAL: Update ServiceVisitItem status
    if report.service_visit_item:
        report.service_visit_item.status = 'PENDING_VERIFICATION'
        report.service_visit_item.submitted_at = timezone.now()
        report.service_visit_item.save()  ← THIS WAS MISSING!
        
        # Update derived visit status
        report.service_visit_item.service_visit.update_derived_status()
        
        # Add audit log
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

## Summary - Action Items

### Immediate (Do Now):
1. ✅ Save your JSON template to a file (you already have it)
2. 🔧 Import using: `POST /api/templates/import/` OR create management command
3. 🔧 Link services to Template (NOT ReportTemplate):
   ```python
   service.default_template = template  # Template, not ReportTemplate!
   service.save()
   ```
4. 🔧 Fix verification workflow status update (see code above)
5. 🔧 Check receipt template includes `service_name_snapshot`

### Medium Priority:
6. 📝 Add deprecation warnings to ReportTemplate for USG usage
7. 📝 Update frontend to always use `template_schema` from USGReport
8. 📝 Add multiple USG service entry support (dropdown to select which service)

### Long Term:
9. 📋 Migrate all USG templates to Template/TemplateVersion system
10. 📋 Deprecate ReportTemplate for USG (keep for non-sectioned reports like OPD)

---

## Quick Test

```bash
# Test template exists and has sections
python manage.py shell

from apps.templates.models import Template, TemplateVersion
tv = TemplateVersion.objects.filter(template__code="USG_KUB_BASIC", is_published=True).first()
print(f"Found: {tv.template.name}")
print(f"Sections: {len(tv.schema.get('sections', []))}")
for section in tv.schema.get('sections', []):
    print(f"  - {section['title']}: {len(section['fields'])} fields")
```

---

**Key Takeaway**: Use Template/TemplateVersion (OLD system with sections), NOT ReportTemplate (NEW flat system) for USG templates!
