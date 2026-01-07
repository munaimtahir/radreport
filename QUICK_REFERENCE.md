# Repository Bloat Quick Reference
## TL;DR - What's Wrong and How to Fix It

---

## The Problem in 30 Seconds

**Repository Size:** 82 MB (should be ~5-10 MB)

**Root Cause:** Dependency directories and build artifacts were accidentally committed:
- `backend/venv/` - 135 MB, 8,372 files ❌
- `frontend/node_modules/` - 77 MB, 2,484 files ❌
- `backend/staticfiles/` - 3.3 MB, 164 files ❌
- `backend/db.sqlite3` - 508 KB ❌

**Impact:**
- Slow clones (30s instead of 5s)
- Wasted bandwidth and storage
- Violates Git best practices

---

## Quick Fix (30 minutes, Safe)

```bash
# Remove from current tree (doesn't change history)
git rm -r backend/venv/ frontend/node_modules/ backend/staticfiles/
git rm backend/db.sqlite3
git commit -m "Remove dependency directories and build artifacts"
git push
```

**Result:** New commits are clean, but old history still contains bloat.

---

## Complete Fix (2-4 hours, Requires Coordination)

```bash
# 1. Install tool
pip install git-filter-repo

# 2. Fresh clone
git clone https://github.com/munaimtahir/radreport.git radreport-filter
cd radreport-filter

# 3. Remove from history
echo "backend/venv/
frontend/node_modules/
backend/staticfiles/
backend/db.sqlite3
backend/media/pdfs/" > paths-to-remove.txt

git-filter-repo --invert-paths --paths-from-file paths-to-remove.txt --force

# 4. Force push
git remote add origin https://github.com/munaimtahir/radreport.git
git push origin --force --all
git push origin --force --tags

# 5. Tell everyone to re-clone
# (Send email to team)
```

**Result:** Repository size drops to ~5-10 MB permanently.

**⚠️ Warning:** All collaborators must delete and re-clone their local repos!

---

## What Developers Should Do

### After Quick Fix (Phase 1)
Just pull and continue working:
```bash
git pull origin main
cd backend && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt
cd ../frontend && npm install
```

### After Complete Fix (Phase 2)
Delete and re-clone:
```bash
# Save work first if needed
git format-patch origin/main..HEAD -o ~/patches/

# Delete old clone
rm -rf radreport

# Re-clone
git clone https://github.com/munaimtahir/radreport.git
cd radreport

# Apply saved work
git am ~/patches/*.patch

# Set up dependencies
cd backend && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt
cd ../frontend && npm install
```

---

## How to Prevent This in Future

### Rule #1: Never Commit These
- ❌ `venv/`, `node_modules/`, `.venv/`
- ❌ `staticfiles/`, `dist/`, `build/`
- ❌ `db.sqlite3`, `*.db`
- ❌ Generated files (PDFs, CSVs, logs)

### Rule #2: Use .gitignore
The repository already has a good `.gitignore`. Make sure it includes:
```gitignore
venv/
node_modules/
staticfiles/
db.sqlite3
media/
```

### Rule #3: Check Before Committing
```bash
# Always review what you're committing
git status
git diff --cached

# If you see node_modules or venv, STOP and investigate!
```

### Rule #4: Use Pre-commit Hooks (Optional)
```bash
pip install pre-commit
# Add .pre-commit-config.yaml with size/path checks
pre-commit install
```

---

## Decision Matrix

| Situation | Recommended Action |
|-----------|-------------------|
| Team of 1-2, no active PRs | Do Complete Fix immediately |
| Active team, multiple PRs | Do Quick Fix now, Complete Fix later during quiet period |
| Need fast fix before demo | Do Quick Fix only |
| Production repository | Do Quick Fix, schedule Complete Fix during maintenance window |
| Forked repository | Do Complete Fix in your fork, don't worry about force-push |

---

## Files Created

| File | Purpose |
|------|---------|
| `REPOSITORY_BLOAT_DIAGNOSTIC.md` | Detailed analysis (read this for full context) |
| `CLEANUP_INSTRUCTIONS.md` | Step-by-step guide (follow this to fix) |
| `PROPOSED_GITIGNORE.txt` | Enhanced .gitignore template |
| `QUICK_REFERENCE.md` | This file (quick overview) |

---

## Key Commands Reference

### Check Repository Size
```bash
git count-objects -vH
du -sh .git
```

### Check What's Tracked
```bash
git ls-files backend/venv/ | head
git ls-files frontend/node_modules/ | head
```

### Remove from Working Tree
```bash
git rm -r backend/venv/
git rm -r frontend/node_modules/
git commit -m "Remove bloat files"
```

### Remove from History (Complete)
```bash
pip install git-filter-repo
git-filter-repo --invert-paths --paths-from-file paths-to-remove.txt --force
git push origin --force --all
```

### Verify .gitignore Works
```bash
# Rebuild dependencies
cd backend && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt
cd ../frontend && npm install

# Check status
git status
# Should show "nothing to commit" - NOT show venv/ or node_modules/
```

---

## FAQ

### Q: Will this delete my local venv/node_modules?
**A:** Phase 1 removes them from Git but leaves your working directory. You can recreate them immediately with `pip install -r requirements.txt` and `npm install`.

### Q: Can I skip Phase 2?
**A:** Yes. Phase 1 prevents future bloat. Phase 2 cleans history but requires coordination.

### Q: What if I already committed more bloat after the initial issue?
**A:** The cleanup will remove all instances from history. Just make sure Phase 1 is complete first.

### Q: Will this break CI/CD?
**A:** Phase 1: No. Phase 2: May need to clear caches and re-clone in CI environments.

### Q: How long will Phase 2 take?
**A:** git-filter-repo: ~5-15 minutes. Coordination and verification: 2-4 hours.

### Q: Can I undo this?
**A:** Phase 1: Yes, with `git revert`. Phase 2: Yes, if you made a backup mirror first (see CLEANUP_INSTRUCTIONS.md).

---

## Success Criteria

After completing cleanup:

✅ `git count-objects -vH` shows size-pack < 10 MiB  
✅ `git ls-files | grep venv` returns nothing  
✅ `git ls-files | grep node_modules` returns nothing  
✅ Backend runs after `pip install -r requirements.txt`  
✅ Frontend runs after `npm install`  
✅ `git status` shows clean tree after rebuilding dependencies  

---

## Get Help

1. **Read the detailed diagnostic:** `REPOSITORY_BLOAT_DIAGNOSTIC.md`
2. **Follow step-by-step guide:** `CLEANUP_INSTRUCTIONS.md`
3. **Check proposed .gitignore:** `PROPOSED_GITIGNORE.txt`
4. **Contact:** Repository administrator

---

**Created:** January 7, 2026  
**Repository:** munaimtahir/radreport  
**Analysis Branch:** copilot/diagnose-repo-bloat-sources
