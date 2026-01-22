# 📍 USG Template System Documentation

**All documentation has been moved to**: `template_guide/`

---

## 🚀 Quick Start

**Read First**: [`template_guide/START_HERE.md`](template_guide/START_HERE.md)

**Then**: [`template_guide/QUICK_START.md`](template_guide/QUICK_START.md)

---

## 📚 Full Index

See: [`template_guide/INDEX.md`](template_guide/INDEX.md) for complete documentation list

---

## ⚡ Quick Commands

```bash
# Import USG template
cd /home/munaim/srv/apps/radreport
source .venv/bin/activate
cd backend
python manage.py import_usg_template /tmp/template.json --link-service=USG_XXX

# Link services
python manage.py link_usg_services

# Fix receipts
python manage.py fix_receipt_snapshots
```

---

## 🎯 Key Files

| Purpose | File |
|---------|------|
| **Start here** | `template_guide/START_HERE.md` |
| **Quick guide** | `template_guide/QUICK_START.md` |
| **Frontend UI** | `template_guide/FRONTEND_TEMPLATE_GUIDE.md` |
| **Generate templates** | `template_guide/TEMPLATE_GENERATION_PROMPT.md` |
| **Deploy** | `template_guide/DEPLOYMENT_CHECKLIST.md` |

---

**Created**: January 22, 2026  
**Status**: ✅ Complete

**Navigate to**: [`template_guide/`](template_guide/) folder
