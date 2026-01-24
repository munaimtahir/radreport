# USG Template System - Deployment Checklist

**Date**: January 22, 2026  
**Estimated Time**: 30 minutes  
**Status**: READY TO DEPLOY

---

## Pre-Deployment Verification

### ✅ Phase 1: Files Created (Already Done)

- [x] Import command: `import_usg_template.py`
- [x] Link services command: `link_usg_services.py`
- [x] Fix receipts command: `fix_receipt_snapshots.py`
- [x] Import helper script: `import_templates.sh`
- [x] Documentation files (6 files)
- [x] Static files collected
- [x] Migration created (na_allowed field)

---

## Deployment Steps

### 📋 Step 1: Backup Database (5 min)

```bash
cd /home/munaim/srv/apps/radreport

# Backup database
docker compose exec db pg_dump -U radreport radreport > backup_before_template_fix_$(date +%Y%m%d_%H%M%S).sql

# Verify backup
ls -lh backup_*.sql
```

### 🔧 Step 2: Run Migrations (2 min)

```bash
cd /home/munaim/srv/apps/radreport
source .venv/bin/activate
cd backend

# Run pending migrations
python manage.py migrate

# Verify
python manage.py showmigrations templates | grep na_allowed
```

**Expected**: `[X] 0005_add_na_allowed_to_report_template_field`

### 📥 Step 3: Import Your KUB Template (3 min)

```bash
# Verify your JSON file exists
ls -l /tmp/usg_kub.json

# Import template
python manage.py import_usg_template /tmp/usg_kub.json --link-service=USG_KUB

# Verify import success
python manage.py shell
>>> from apps.templates.models import Template, TemplateVersion
>>> tv = TemplateVersion.objects.filter(template__code='USG_KUB_BASIC', is_published=True).first()
>>> print(f"Sections: {len(tv.schema.get('sections', []))}")
>>> exit()
```

**Expected**: Sections: 4 (or however many you have)

### 🔗 Step 4: Link All USG Services (2 min)

```bash
# Dry run first to see what would be linked
python manage.py link_usg_services --dry-run

# Review output, then actually link
python manage.py link_usg_services

# Verify linkage
python manage.py shell
>>> from apps.catalog.models import Service
>>> usg = Service.objects.filter(modality__code='USG', default_template__isnull=False)
>>> print(f"Linked services: {usg.count()}")
>>> for s in usg: print(f"  {s.code} → {s.default_template.code}")
>>> exit()
```

**Expected**: At least 1 service linked (USG_KUB)

### 🧾 Step 5: Fix Receipt Snapshots (3 min)

```bash
# Check what needs fixing
python manage.py fix_receipt_snapshots --dry-run

# Apply fixes
python manage.py fix_receipt_snapshots

# Verify
python manage.py shell
>>> from apps.workflow.models import ServiceVisitItem
>>> missing = ServiceVisitItem.objects.filter(service__isnull=False, service_name_snapshot='')
>>> print(f"Items still missing snapshots: {missing.count()}")
>>> exit()
```

**Expected**: 0 items missing snapshots

### 🔄 Step 6: Restart Backend (2 min)

```bash
cd /home/munaim/srv/apps/radreport

# Restart backend container
./backend.sh

# Wait for startup (check logs)
docker compose logs -f backend --tail=50
```

**Look for**: "Listening at" or "spawned uWSGI worker"

### 🧪 Step 7: Browser Testing (10 min)

1. **Login**
   - Go to: https://rims.alshifalab.pk
   - Login: admin / admin123

2. **Register Test Patient**
   - Navigation: Registration
   - Add patient with USG KUB service
   - Note the Visit ID (e.g., 2601-0028)

3. **Test Report Entry**
   - Navigation: Report Entry → USG Worklist
   - Find your test visit
   - Click to open report form
   - **Verify**:
     - [ ] Sections show (Right Kidney, Left Kidney, etc.)
     - [ ] Fields grouped properly
     - [ ] NA checkboxes visible next to fields
     - [ ] Checklist options show as multiple choices
     - [ ] Can select/deselect options
   
4. **Fill and Save Draft**
   - Fill some fields
   - Check some NA boxes
   - Click "Save Draft"
   - **Verify**: Success message shows

5. **Submit for Verification**
   - Fill required fields if any
   - Click "Submit for Verification"
   - **Verify**: Success message shows

6. **Check Verification Tab**
   - Navigation: Verification
   - **Verify**: Your report appears in list
   - Click to review
   - Click "Publish" or "Verify"

7. **Check Receipt**
   - Go back to patient visit
   - View/Generate receipt
   - **Verify**: USG KUB service shows with price

8. **Generate PDF Report**
   - After publishing, download PDF
   - **Verify**: PDF generates successfully

---

## Post-Deployment Verification

### ✅ Verification Checklist

Run these checks after deployment:

```bash
cd /home/munaim/srv/apps/radreport
source .venv/bin/activate
cd backend
python manage.py shell
```

**Check 1: Templates Exist**
```python
from apps.templates.models import Template, TemplateVersion

templates = Template.objects.filter(modality_code='USG')
print(f"✓ USG Templates: {templates.count()}")
for t in templates:
    versions = t.versions.filter(is_published=True).count()
    print(f"  - {t.code}: {versions} published version(s)")
```

**Expected**: At least 1 template with 1 published version

**Check 2: Services Linked**
```python
from apps.catalog.models import Service

services = Service.objects.filter(default_template__isnull=False, modality__code='USG')
print(f"✓ Linked Services: {services.count()}")
for s in services:
    print(f"  - {s.code} → {s.default_template.code}")
```

**Expected**: All USG services linked

**Check 3: Reports Can Be Created**
```python
from apps.workflow.models import USGReport, ServiceVisitItem

# Check recent USG items have template_version
items = ServiceVisitItem.objects.filter(department_snapshot='USG').order_by('-created_at')[:5]
for item in items:
    report = USGReport.objects.filter(service_visit_item=item).first()
    if report and report.template_version:
        print(f"✓ Item {str(item.id)[:8]}: template_version = {report.template_version.template.code}")
    else:
        print(f"⚠ Item {str(item.id)[:8]}: No template_version (needs report entry)")
```

**Check 4: Snapshots Fixed**
```python
from apps.workflow.models import ServiceVisitItem

missing = ServiceVisitItem.objects.filter(
    service__isnull=False,
    service_name_snapshot=''
).count()

print(f"Items missing snapshots: {missing}")
if missing == 0:
    print("✓ All snapshots fixed!")
else:
    print("⚠ Some items need fixing")
```

**Check 5: Static Files Served**
```python
import os
from django.conf import settings

static_root = settings.STATIC_ROOT
static_files = len([f for root, dirs, files in os.walk(static_root) for f in files])
print(f"✓ Static files collected: {static_files}")
```

**Expected**: 165+ files

**Exit shell**:
```python
exit()
```

---

## Rollback Plan (If Needed)

If something goes wrong:

### Quick Rollback

```bash
cd /home/munaim/srv/apps/radreport

# 1. Restore database backup
cat backup_before_template_fix_*.sql | docker compose exec -T db psql -U radreport radreport

# 2. Restart backend
./backend.sh

# 3. Verify system works as before
```

### Undo Template Import Only

```bash
python manage.py shell

from apps.templates.models import Template, TemplateVersion

# Delete imported templates
Template.objects.filter(code='USG_KUB_BASIC').delete()
# This cascades to TemplateVersion automatically

exit()
```

---

## Success Criteria

✅ **Deployment is successful if**:

1. [ ] Template import completes without errors
2. [ ] At least 1 USG service linked to template
3. [ ] Report entry shows organized sections (not flat list)
4. [ ] NA checkboxes visible and functional
5. [ ] Checklist options show as multiple choices
6. [ ] Reports submit to verification tab
7. [ ] Reports appear in verification list
8. [ ] Receipts include USG service name and price
9. [ ] PDF generation works
10. [ ] No errors in backend logs

---

## Next Steps After Successful Deployment

### 📝 Import More Templates (15 min each)

```bash
# Generate template using AI
# (Use TEMPLATE_GENERATION_PROMPT.md with ChatGPT/Claude)

# Import each template
python manage.py import_usg_template /tmp/usg_abdomen.json --link-service=USG_ABDOMEN
python manage.py import_usg_template /tmp/usg_pelvis.json --link-service=USG_PELVIS
python manage.py import_usg_template /tmp/usg_breast.json --link-service=USG_BREAST
# ... etc

# Or use helper script if multiple files in /tmp/
./import_templates.sh
```

### 🎯 Priority Templates to Create

1. **USG Abdomen** (liver, GB, pancreas, spleen, kidneys)
2. **USG Pelvis** (uterus, ovaries, bladder)
3. **USG KUB** (kidneys, ureters, bladder) ✅ Already done
4. **USG Breast** (bilateral breast, axillary nodes)
5. **USG Thyroid** (right lobe, left lobe, isthmus)
6. **USG OB** (obstetric scan)
7. **USG Carotid Doppler** (carotid vessels)
8. **USG Renal Doppler** (renal vessels)

### 📊 Train Users (30 min)

1. Show report entry interface
2. Demonstrate section organization
3. Explain NA checkbox usage
4. Show verification workflow
5. Demonstrate PDF generation

### 🔧 Monitor & Optimize

- Monitor backend logs for template-related errors
- Collect user feedback on template fields
- Add/remove fields as needed
- Create advanced templates (e.g., _DETAILED versions)

---

## Troubleshooting Common Issues

### Issue: "Template not found for service"

**Solution**:
```bash
python manage.py shell
>>> from apps.catalog.models import Service
>>> service = Service.objects.get(code='USG_XXX')
>>> from apps.templates.models import Template
>>> template = Template.objects.get(code='USG_XXX_BASIC')
>>> service.default_template = template
>>> service.save()
>>> exit()
```

### Issue: "No sections showing in UI"

**Check**: Frontend receiving correct schema
```bash
# Check API response
curl -H "Authorization: Token YOUR_TOKEN" \
  https://api.rims.alshifalab.pk/api/workflow/usg/?visit_id=2601-0028 | jq '.[] | .template_schema.sections'
```

**Solution**: Re-import template with correct JSON structure

### Issue: "NA checkbox not showing"

**Check**: Field has `na_allowed: true` in JSON
**Solution**: Update template JSON, re-import

### Issue: "Receipts still missing services"

**Solution**: Run fix command again
```bash
python manage.py fix_receipt_snapshots
```

---

## Documentation Reference

| Topic | File | Purpose |
|-------|------|---------|
| Quick start | `QUICK_START.md` | 15-min implementation guide |
| AI templates | `TEMPLATE_GENERATION_PROMPT.md` | Generate templates with AI |
| System guide | `USG_TEMPLATE_SYSTEM_GUIDE.md` | How the system works |
| Model cleanup | `MODEL_CLEANUP_PLAN.md` | What to keep/deprecate |
| Full analysis | `USG_SYSTEM_CONSOLIDATION_PLAN.md` | Complete problem analysis |
| Summary | `IMPLEMENTATION_SUMMARY.md` | What was fixed |
| This file | `DEPLOYMENT_CHECKLIST.md` | Step-by-step deployment |

---

## Support Commands

```bash
# Check backend logs
docker compose logs backend --tail=100 | grep -i template

# Check Django errors
docker compose logs backend --tail=100 | grep -i error

# Interactive shell
python manage.py shell

# Database shell
docker compose exec db psql -U radreport radreport

# Restart backend
./backend.sh

# Collect static files
python manage.py collectstatic --no-input
```

---

## Final Notes

- **Backup before deploying**: Always backup database first
- **Test on staging**: If you have a staging environment, test there first
- **Monitor logs**: Watch logs during first few report entries
- **User feedback**: Collect feedback and iterate on templates
- **Version control**: Commit changes before deploying

---

**Deployment Status**: ✅ READY  
**Risk Level**: LOW (can rollback easily)  
**Estimated Downtime**: 0 minutes (no downtime needed)  
**Rollback Time**: < 5 minutes if needed

**Go ahead and deploy!** 🚀

**Date**: January 22, 2026  
**Prepared by**: AI Assistant  
**Reviewed**: Ready for implementation
