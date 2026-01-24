# AI Prompt for Generating USG Templates

Use this prompt with ChatGPT/Claude to generate properly formatted USG templates:

---

## THE PROMPT

```
Generate a complete ultrasound template in JSON format following this EXACT structure:

{
  "code": "USG_[EXAM]_BASIC",
  "name": "Ultrasound [Exam Name] (Basic)",
  "category": "USG",
  "sections": [
    {
      "title": "[Organ/Area Name]",
      "order": 1,
      "fields": [
        {
          "key": "[organ_abbrev]_[field_name]",
          "label": "[Field Label]",
          "type": "checklist",
          "order": 1,
          "required": false,
          "na_allowed": true,
          "options": [
            {
              "label": "Normal",
              "value": "Normal"
            },
            {
              "label": "Abnormal",
              "value": "Abnormal"
            }
          ]
        }
      ]
    }
  ]
}

FIELD TYPES AVAILABLE:
- "heading": Section header (no input, just displays title)
- "short_text": Single line text input
- "long_text": Multi-line textarea
- "number": Numeric input
- "dropdown": Single selection dropdown (requires options)
- "checklist": Multiple checkboxes (requires options)
- "checkbox": Single Yes/No checkbox
- "radio": Radio buttons (requires options)
- "separator": Horizontal line divider (no input)

RULES:
1. Every field MUST have a unique "key" (use snake_case)
2. "type" must be one of the types listed above
3. "order" determines display order within section
4. Set "na_allowed": true for clinical findings fields
5. Set "required": true only for critical fields
6. "options" required only for: dropdown, checklist, radio
7. Use descriptive "label" for display (Title Case)
8. Use abbreviated "key" for storage (snake_case)

EXAM TYPE: [Specify the ultrasound exam type, e.g., "Abdomen", "Pelvis", "KUB", "Breast", "Thyroid", etc.]

Generate a complete, clinically accurate template for this exam.
```

---

## EXAMPLES

### Example 1: Generate Abdomen Template

**User sends**:
```
[Paste the prompt above]
EXAM TYPE: Abdomen
```

**AI will generate**:
```json
{
  "code": "USG_ABDOMEN_BASIC",
  "name": "Ultrasound Abdomen (Basic)",
  "category": "USG",
  "sections": [
    {
      "title": "Liver",
      "order": 1,
      "fields": [
        {
          "key": "liver_section",
          "label": "Liver",
          "type": "heading",
          "order": 1,
          "required": false,
          "na_allowed": true
        },
        {
          "key": "liver_size",
          "label": "Size",
          "type": "checklist",
          "order": 2,
          "required": false,
          "na_allowed": true,
          "options": [
            {"label": "Normal", "value": "Normal"},
            {"label": "Enlarged", "value": "Enlarged"},
            {"label": "Reduced", "value": "Reduced"}
          ]
        },
        ...
      ]
    },
    ...
  ]
}
```

### Example 2: Generate Breast Template

**User sends**:
```
[Paste the prompt above]
EXAM TYPE: Breast
```

**AI will generate structured template for bilateral breast exam**

---

## QUICK TEMPLATES

### For Common Exams

1. **Abdomen**: Liver, GB, Pancreas, Spleen, Kidneys, Bladder, Vessels
2. **Pelvis**: Uterus, Ovaries, Bladder, Adnexa
3. **KUB**: Right Kidney, Left Kidney, Ureters, Bladder
4. **Breast**: Right Breast, Left Breast, Axillary Nodes
5. **Thyroid**: Right Lobe, Left Lobe, Isthmus, Lymph Nodes
6. **Carotid**: Right CCA, Right ICA, Right ECA, Left CCA, Left ICA, Left ECA
7. **Renal Doppler**: Right Kidney (with Doppler), Left Kidney (with Doppler)
8. **Portal Doppler**: Portal Vein, Hepatic Veins, Splenic Vein

---

## VALIDATION CHECKLIST

Before importing, ensure your template has:

✅ Valid "code" (format: `USG_[EXAM]_BASIC`)  
✅ "category" set to "USG"  
✅ At least one section  
✅ Each section has "title", "order", and "fields" array  
✅ Each field has: "key", "label", "type", "order"  
✅ No duplicate "key" values across entire template  
✅ "options" array present for dropdown/checklist/radio types  
✅ "na_allowed" set to true for clinical finding fields  

---

## IMPORTING YOUR TEMPLATE

### Method 1: Via Management Command (Recommended)

Save to file, then import:

```bash
# Save your JSON
cat > /tmp/my_template.json << 'EOF'
{
  "code": "USG_ABDOMEN_BASIC",
  ...
}
EOF

# Import
cd /home/munaim/srv/apps/radreport
source .venv/bin/activate
cd backend
python manage.py import_usg_template /tmp/my_template.json
```

### Method 2: Via API

```bash
curl -X POST https://api.rims.alshifalab.pk/api/templates/import/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d @/tmp/my_template.json
```

### Method 3: Via Django Admin Shell

```python
python manage.py shell

from apps.templates.engine import TemplatePackageEngine
import json

with open('/tmp/my_template.json', 'r') as f:
    data = json.load(f)

result = TemplatePackageEngine.import_package(data, mode='create')
print("Success!")
```

---

## AFTER IMPORTING

### Link to Service

```python
from apps.catalog.models import Service
from apps.templates.models import Template

# Find your service
service = Service.objects.get(code="USG_ABDOMEN")

# Link to template
template = Template.objects.get(code="USG_ABDOMEN_BASIC")
service.default_template = template
service.save()

print(f"Linked {service.name} to {template.name}")
```

### Verify

```python
from apps.templates.models import TemplateVersion

tv = TemplateVersion.objects.filter(
    template__code="USG_ABDOMEN_BASIC",
    is_published=True
).first()

print(f"Template: {tv.template.name}")
print(f"Sections: {len(tv.schema.get('sections', []))}")
for s in tv.schema.get('sections', []):
    print(f"  - {s['title']}: {len(s['fields'])} fields")
```

---

## COMMON FIELD PATTERNS

### Clinical Finding Pattern
```json
{
  "key": "organ_finding",
  "label": "Finding Name",
  "type": "checklist",
  "order": X,
  "required": false,
  "na_allowed": true,
  "options": [
    {"label": "Normal", "value": "Normal"},
    {"label": "Abnormal - specify", "value": "Abnormal"}
  ]
}
```

### Size/Measurement Pattern
```json
{
  "key": "organ_size",
  "label": "Size (mm)",
  "type": "number",
  "order": X,
  "required": false,
  "na_allowed": true,
  "placeholder": "Enter measurement in mm"
}
```

### Free Text Notes Pattern
```json
{
  "key": "organ_notes",
  "label": "Additional findings",
  "type": "long_text",
  "order": 999,
  "required": false,
  "na_allowed": true,
  "placeholder": "Enter additional findings or comments"
}
```

### Section Header Pattern
```json
{
  "key": "organ_section",
  "label": "Organ Name",
  "type": "heading",
  "order": 1,
  "required": false,
  "na_allowed": true
}
```

---

## ADVANCED: Conditional Fields

For fields that should only show based on other field values:

```json
{
  "key": "stone_location",
  "label": "Stone location",
  "type": "checklist",
  "order": 5,
  "required": false,
  "na_allowed": true,
  "options": [...],
  "rules": {
    "show_if": {
      "field": "stone_present",
      "equals": "Present"
    }
  }
}
```

**Note**: Conditional logic requires frontend implementation!

---

## TEMPLATE NAMING CONVENTIONS

| Exam Type | Code | Name |
|-----------|------|------|
| Abdomen | `USG_ABDOMEN_BASIC` | "Ultrasound Abdomen (Basic)" |
| Pelvis | `USG_PELVIS_BASIC` | "Ultrasound Pelvis (Basic)" |
| KUB | `USG_KUB_BASIC` | "Ultrasound KUB (Basic)" |
| OB | `USG_OB_BASIC` | "Ultrasound Obstetric (Basic)" |
| Breast | `USG_BREAST_BASIC` | "Ultrasound Breast (Basic)" |
| Thyroid | `USG_THYROID_BASIC` | "Ultrasound Thyroid (Basic)" |
| Carotid | `USG_CAROTID_BASIC` | "Ultrasound Carotid Doppler (Basic)" |

---

## FIELD KEY NAMING CONVENTIONS

Pattern: `[organ_abbrev]_[field_name]`

**Organ Abbreviations**:
- `liver` - Liver
- `gb` - Gallbladder
- `panc` - Pancreas
- `spl` - Spleen
- `rk` - Right Kidney
- `lk` - Left Kidney
- `ut` - Uterus
- `rov` - Right Ovary
- `lov` - Left Ovary
- `thy` - Thyroid
- `bl` - Bladder

**Field Names**:
- `size` - Size/dimensions
- `echo` - Echogenicity
- `wall` - Wall thickness
- `calc` - Calculi/stones
- `mass` - Mass/lesion
- `dist` - Distension
- `notes` - Free text notes

Examples:
- `liver_size`
- `gb_wall`
- `rk_calc`
- `ut_mass`

---

## TROUBLESHOOTING

### Template Not Showing in Report Entry

**Check**:
1. Template imported? `Template.objects.filter(code="USG_XXX_BASIC").exists()`
2. TemplateVersion published? `TemplateVersion.objects.filter(template__code="USG_XXX_BASIC", is_published=True).exists()`
3. Service linked? `service.default_template` should point to Template
4. Schema has sections? `tv.schema.get('sections', [])` should not be empty

### Fields Not Rendering

**Check**:
1. Field type is valid (see FIELD TYPES above)
2. Field has unique "key"
3. Options present for dropdown/checklist/radio
4. Frontend expects `template_schema` with sections

### NA Checkbox Not Showing

**Check**:
1. Field has `"na_allowed": true`
2. Frontend checks `field.na_allowed` before rendering NA checkbox
3. Backend migration ran (adds `na_allowed` to models)

---

## GETTING HELP

If template generation fails:

1. Validate JSON: https://jsonlint.com/
2. Check schema against TemplatePackage v1
3. Review error messages from import command
4. Check Django logs for validation errors
5. Compare against working templates (e.g., USG_KUB_BASIC)

---

**Created**: January 22, 2026  
**For**: RadReport USG Template System  
**Version**: 1.0
