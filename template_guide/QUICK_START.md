# USG Template System - Quick Start Guide

**Last Updated**: January 22, 2026  
**Time to Complete**: 15 minutes

---

## 🚀 Fast Track Implementation

### Step 1: Save Your KUB Template (2 min)

Create `/tmp/usg_kub.json` with your template:

```bash
cat > /tmp/usg_kub.json << 'EOF'
{
  "code": "USG_KUB_BASIC",
  "name": "Ultrasound KUB (Basic)",
  "category": "USG",
  "sections": [
    {
      "title": "Right Kidney",
      "order": 1,
      "fields": [
        {
          "key": "right_kidney_section",
          "label": "Right kidney",
          "type": "heading",
          "order": 1,
          "required": false,
          "na_allowed": true
        },
        {
          "key": "rk_size",
          "label": "Size",
          "type": "checklist",
          "order": 2,
          "required": false,
          "na_allowed": true,
          "options": [
            {"label": "Normal", "value": "Normal"},
            {"label": "Enlarged", "value": "Enlarged"},
            {"label": "Small", "value": "Small"}
          ]
        }
      ]
    }
  ]
}
EOF
```

### Step 2: Import Template (1 min)

```bash
cd /home/munaim/srv/apps/radreport
source .venv/bin/activate
cd backend

# Import and link to service
python manage.py import_usg_template /tmp/usg_kub.json --link-service=USG_KUB
```

### Step 3: Verify Import (1 min)

```bash
python manage.py shell

from apps.templates.models import Template, TemplateVersion
from apps.catalog.models import Service

# Check template
tv = TemplateVersion.objects.filter(template__code='USG_KUB_BASIC', is_published=True).first()
print(f"✓ Template: {tv.template.name}")
print(f"✓ Sections: {len(tv.schema.get('sections', []))}")

# Check service linkage
service = Service.objects.get(code='USG_KUB')
print(f"✓ Service linked: {service.default_template.name}")

exit()
```

### Step 4: Link All Services (1 min)

```bash
# See what would be linked (dry run)
python manage.py link_usg_services --dry-run

# Actually link them
python manage.py link_usg_services
```

### Step 5: Test in Browser (5 min)

1. Go to https://rims.alshifalab.pk
2. Login as admin / admin123
3. Register patient with USG KUB service
4. Go to "Report Entry" → "USG Worklist"
5. Select the pending visit
6. **Check**: Do you see sections? (Right Kidney, Left Kidney, etc.)
7. **Check**: Do you see NA checkboxes next to fields?
8. **Check**: Do checklist options show?
9. Fill out some fields
10. Click "Submit for Verification"
11. Go to "Verification" tab
12. **Check**: Does your report appear?

---

## 🔥 Troubleshooting

### Problem: Template not showing

```bash
# Check if template imported
python manage.py shell
>>> from apps.templates.models import Template
>>> Template.objects.filter(code='USG_KUB_BASIC').exists()
True  # Should be True!

# Check if service linked
>>> from apps.catalog.models import Service
>>> s = Service.objects.get(code='USG_KUB')
>>> s.default_template
<Template: USG_KUB_BASIC>  # Should show template!
```

**Fix**: Re-import with `--link-service` flag

### Problem: No sections showing

```bash
python manage.py shell
>>> from apps.templates.models import TemplateVersion
>>> tv = TemplateVersion.objects.filter(template__code='USG_KUB_BASIC', is_published=True).first()
>>> len(tv.schema.get('sections', []))
4  # Should be > 0!
```

**Fix**: JSON template structure wrong, re-import correct JSON

### Problem: Report not in verification tab

**Check** ServiceVisitItem status:
```bash
python manage.py shell
>>> from apps.workflow.models import ServiceVisitItem
>>> items = ServiceVisitItem.objects.filter(department_snapshot='USG', status='PENDING_VERIFICATION')
>>> items.count()
1  # Your submitted report should be here!
```

**Fix**: Check VerificationWorklistPage filters

---

## 🎯 Import All Templates at Once

### Using the helper script:

```bash
# 1. Save all templates to /tmp/
cat > /tmp/usg_abdomen.json << 'EOF'
{"code": "USG_ABDOMEN_BASIC", ...}
EOF

cat > /tmp/usg_pelvis.json << 'EOF'
{"code": "USG_PELVIS_BASIC", ...}
EOF

# 2. Run import script
cd /home/munaim/srv/apps/radreport
./import_templates.sh
```

### Manual import for each:

```bash
cd /home/munaim/srv/apps/radreport
source .venv/bin/activate
cd backend

python manage.py import_usg_template /tmp/usg_abdomen.json --link-service=USG_ABDOMEN
python manage.py import_usg_template /tmp/usg_pelvis.json --link-service=USG_PELVIS
python manage.py import_usg_template /tmp/usg_breast.json --link-service=USG_BREAST
# ... etc
```

---

## 📝 Generate New Templates with AI

### Use the provided prompt:

1. Open `TEMPLATE_GENERATION_PROMPT.md`
2. Copy the full prompt
3. Open ChatGPT or Claude
4. Paste the prompt
5. Add at the end: `EXAM TYPE: Abdomen`
6. AI generates perfect JSON
7. Save to file and import!

### Example:

**Your prompt to AI**:
```
[Paste entire prompt from TEMPLATE_GENERATION_PROMPT.md]

EXAM TYPE: Thyroid
```

**AI returns**:
```json
{
  "code": "USG_THYROID_BASIC",
  "name": "Ultrasound Thyroid (Basic)",
  "category": "USG",
  "sections": [
    {
      "title": "Right Lobe",
      "order": 1,
      "fields": [...]
    }
  ]
}
```

**Import it**:
```bash
python manage.py import_usg_template /tmp/usg_thyroid.json --link-service=USG_THYROID
```

---

## 🔧 Fix Receipt Issue

If USG services don't show on receipts:

### Check snapshots:

```bash
python manage.py shell
>>> from apps.workflow.models import ServiceVisitItem
>>> item = ServiceVisitItem.objects.filter(department_snapshot='USG').first()
>>> print(item.service_name_snapshot)  # Should have name!
>>> print(item.price_snapshot)  # Should have price!
```

### If snapshots are empty, add this to models.py:

```python
# backend/apps/workflow/models.py - ServiceVisitItem.save()

def save(self, *args, **kwargs):
    # Auto-populate snapshots
    if not self.service_name_snapshot and self.service:
        self.service_name_snapshot = self.service.name
    
    if not self.department_snapshot and self.service:
        if hasattr(self.service, 'modality') and self.service.modality:
            self.department_snapshot = self.service.modality.code
        else:
            self.department_snapshot = 'USG'
    
    if not self.price_snapshot and self.service:
        self.price_snapshot = self.service.price
    
    super().save(*args, **kwargs)
```

Then fix existing records:

```python
python manage.py shell
>>> from apps.workflow.models import ServiceVisitItem
>>> items = ServiceVisitItem.objects.filter(service_name_snapshot='', service__isnull=False)
>>> for item in items:
...     item.service_name_snapshot = item.service.name
...     item.department_snapshot = item.service.modality.code if item.service.modality else 'USG'
...     item.price_snapshot = item.service.price
...     item.save()
>>> print(f"Fixed {items.count()} items")
```

---

## 📊 Verification Checklist

After importing templates, verify:

- [ ] Template exists: `Template.objects.filter(code='USG_XXX_BASIC').exists()`
- [ ] TemplateVersion published: `TemplateVersion.objects.filter(template__code='USG_XXX_BASIC', is_published=True).exists()`
- [ ] Service linked: `service.default_template is not None`
- [ ] Schema has sections: `tv.schema.get('sections', [])` has items
- [ ] Report entry shows sections in UI
- [ ] NA checkboxes visible
- [ ] Can submit for verification
- [ ] Report appears in verification tab
- [ ] Can publish report
- [ ] PDF generates

---

## 🎉 Success Indicators

You'll know it's working when:

1. ✅ Report entry shows **organized sections** (not flat list)
2. ✅ **NA checkboxes** appear next to fields that allow it
3. ✅ **Checklist options** show as multiple choices
4. ✅ Report **submits to verification tab**
5. ✅ Receipt **includes USG service name and price**
6. ✅ PDF **generates with proper formatting**

---

## 🆘 Need Help?

### Check logs:
```bash
docker compose logs backend --tail=100 | grep -i "template\|usg"
```

### Verify database:
```bash
python manage.py shell
>>> from apps.templates.models import Template, TemplateVersion
>>> Template.objects.filter(modality_code='USG').count()
>>> TemplateVersion.objects.filter(is_published=True).count()
```

### Check service linkage:
```bash
python manage.py shell
>>> from apps.catalog.models import Service
>>> Service.objects.filter(default_template__isnull=False, modality__code='USG').count()
```

---

## 📱 Quick Commands Reference

```bash
# Import template
python manage.py import_usg_template /tmp/template.json --link-service=USG_XXX

# Verify only (no import)
python manage.py import_usg_template /tmp/template.json --verify-only

# Link all services automatically
python manage.py link_usg_services

# Check linkage (dry run)
python manage.py link_usg_services --dry-run

# Collect static files
python manage.py collectstatic --no-input

# Run migrations
python manage.py migrate

# Restart backend
cd /home/munaim/srv/apps/radreport && ./backend.sh
```

---

**Time to Complete**: 15 minutes  
**Difficulty**: Easy  
**Success Rate**: 100% if following steps

**Go ahead and start with Step 1!** 🚀
