# Repository Cleanup Instructions
## Step-by-Step Guide to Fix radreport Repository Bloat

**Total Estimated Time:** 30 minutes (Phase 1) to 4 hours (Phase 1 + 2)  
**Risk Level:** Low (Phase 1), Medium (Phase 2)

---

## Prerequisites

### Required Tools
- Git (version 2.30+)
- Python 3.12+ (for backend setup verification)
- Node.js 18+ and npm (for frontend setup verification)
- git-filter-repo (for Phase 2 only): `pip install git-filter-repo`

### Required Access
- Write access to the GitHub repository
- Ability to notify collaborators (if doing Phase 2)
- Ability to coordinate with team (if doing Phase 2)

### Backup First! (Critical)
```bash
# Clone a backup before making any changes
git clone --mirror https://github.com/munaimtahir/radreport.git radreport-backup-$(date +%Y%m%d)
```

---

## Phase 1: Remove Files from Current Tree (Safe - Recommended Start)

**Goal:** Remove dependency directories and build artifacts from the current commit  
**Impact:** Safe, no history rewrite, no force-push needed  
**Time:** 30 minutes

### Step 1.1: Clone Repository (If Not Already)
```bash
cd ~/projects
git clone https://github.com/munaimtahir/radreport.git
cd radreport
```

### Step 1.2: Create New Branch for Cleanup
```bash
git checkout -b cleanup/remove-bloat-files
```

### Step 1.3: Remove Problematic Files/Directories
```bash
# Remove Python virtual environment
git rm -r backend/venv/
echo "✓ Removed backend/venv/ (8,372 files, ~135 MB)"

# Remove Node.js dependencies
git rm -r frontend/node_modules/
echo "✓ Removed frontend/node_modules/ (2,484 files, ~77 MB)"

# Remove Django static files (build artifacts)
git rm -r backend/staticfiles/
echo "✓ Removed backend/staticfiles/ (164 files, ~3.3 MB)"

# Remove SQLite database
git rm backend/db.sqlite3
echo "✓ Removed backend/db.sqlite3 (1 file, ~508 KB)"

# Remove generated PDF receipts
git rm backend/media/pdfs/receipts/2026/01/2601-001.pdf
echo "✓ Removed backend/media/pdfs/receipts/ (1 file, ~2 KB)"

# Optional: Remove VS Code config (IDE-specific)
git rm .vscode/tasks.json
echo "✓ Removed .vscode/tasks.json"
```

### Step 1.4: Verify .gitignore Is Correct
```bash
cat .gitignore | grep -E "(venv|node_modules|staticfiles|db.sqlite3|media)"
```

Expected output should include:
```
venv/
node_modules/
/backend/staticfiles/
/backend/media/
db.sqlite3
```

If any patterns are missing, update .gitignore (see .gitignore section below).

### Step 1.5: Commit Changes
```bash
git commit -m "Remove dependency directories and build artifacts from repository

- Removed backend/venv/ (Python virtual environment)
- Removed frontend/node_modules/ (Node.js dependencies)
- Removed backend/staticfiles/ (Django static files)
- Removed backend/db.sqlite3 (SQLite database)
- Removed backend/media/pdfs/ (generated PDF files)

These files should never be committed to version control.
Developers should run 'pip install -r requirements.txt' and 'npm install' locally.

Relates to: Repository bloat cleanup (82 MB → target 5-10 MB)
"
```

### Step 1.6: Push to GitHub
```bash
# Push to your cleanup branch
git push origin cleanup/remove-bloat-files

# Create Pull Request on GitHub
# Title: "Remove dependency directories and build artifacts"
# Description: See commit message + link to REPOSITORY_BLOAT_DIAGNOSTIC.md
```

### Step 1.7: Verify Local Development Still Works

**Backend Setup:**
```bash
cd backend

# Create new virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # On Linux/Mac
# OR
venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Verify it runs
python manage.py runserver
# Should start without errors
```

**Frontend Setup:**
```bash
cd ../frontend

# Install dependencies
npm install

# Verify it builds
npm run build

# Verify dev server runs
npm run dev
# Should start without errors
```

### Step 1.8: Update README.md

Add to README.md (if not already present):

```markdown
## Setup Instructions

### Backend Setup
1. Navigate to backend directory: `cd backend`
2. Create virtual environment: `python -m venv venv`
3. Activate virtual environment:
   - Linux/Mac: `source venv/bin/activate`
   - Windows: `venv\Scripts\activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Run migrations: `python manage.py migrate`
6. Start server: `python manage.py runserver`

### Frontend Setup
1. Navigate to frontend directory: `cd frontend`
2. Install dependencies: `npm install`
3. Start dev server: `npm run dev`

**Important:** Do NOT commit `node_modules/`, `venv/`, `staticfiles/`, or `db.sqlite3` to Git.
```

### Step 1.9: Merge Pull Request
Once PR is reviewed and approved:
```bash
# Merge on GitHub, then locally:
git checkout main
git pull origin main
```

### Step 1.10: Verify .gitignore Works
```bash
# Rebuild dependencies
cd backend && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt
cd ../frontend && npm install
cd ..

# Check git status
git status

# Should output: "nothing to commit, working tree clean"
# Should NOT show venv/, node_modules/, etc.
```

**✓ Phase 1 Complete!**

**Results:**
- ✅ Working tree cleaned of bloat files
- ✅ New commits won't include these files
- ✅ Safe (no history rewrite, no force-push)
- ⚠️ Git history still contains files (repo clone still ~60 MB)

---

## Phase 2: Clean Git History (Complete Fix - Requires Coordination)

**Goal:** Remove files from entire Git history to shrink repository permanently  
**Impact:** Requires force-push, all collaborators must re-clone  
**Time:** 2-4 hours (including coordination)

**⚠️ WARNING:** Only proceed if you understand the implications:
- All commit SHAs will change
- All collaborators must delete and re-clone
- All open PRs will need to be rebased
- Cannot be easily undone (use backup from Prerequisites)

### Step 2.1: Coordinate with Team

**Send notification to all collaborators:**

```
Subject: [ACTION REQUIRED] Repository Cleanup - Re-clone Required

We're cleaning up the radreport repository to remove accidentally committed 
dependency directories (node_modules, venv) from Git history.

Timeline:
- [DATE/TIME]: Repository will be set to read-only
- [DATE/TIME]: Cleanup will begin (1-2 hours)
- [DATE/TIME]: Repository will be available for re-cloning

Actions Required:
1. Commit and push all your work before [DATE/TIME]
2. After cleanup completes, DELETE your local clone
3. Re-clone from GitHub: git clone https://github.com/munaimtahir/radreport.git
4. Recreate your branches if needed

DO NOT:
- Pull changes into existing clones (will cause conflicts)
- Try to merge old branches (will bring back deleted files)

Questions? Reply to this email.
```

### Step 2.2: Set Repository to Read-Only (Optional but Recommended)

On GitHub:
1. Go to Settings → Branches
2. Add branch protection rule for `main`:
   - ✓ Lock branch (makes it read-only)
3. Save changes

### Step 2.3: Ensure Phase 1 Is Merged
```bash
git checkout main
git pull origin main

# Verify files are gone from tree
ls backend/venv 2>/dev/null && echo "ERROR: venv still exists!" || echo "✓ venv removed"
ls frontend/node_modules 2>/dev/null && echo "ERROR: node_modules still exists!" || echo "✓ node_modules removed"
```

### Step 2.4: Install git-filter-repo
```bash
# Using pip (recommended)
pip install git-filter-repo

# Or download standalone script
# wget https://raw.githubusercontent.com/newren/git-filter-repo/main/git-filter-repo
# chmod +x git-filter-repo
# sudo mv git-filter-repo /usr/local/bin/
```

### Step 2.5: Create Fresh Clone for Filtering
```bash
# IMPORTANT: git-filter-repo requires a fresh clone
cd ~/projects
git clone https://github.com/munaimtahir/radreport.git radreport-filter
cd radreport-filter
```

### Step 2.6: Create Paths-to-Remove File
```bash
cat > paths-to-remove.txt <<EOF
backend/venv/
frontend/node_modules/
backend/staticfiles/
backend/db.sqlite3
backend/media/pdfs/
.vscode/
EOF
```

### Step 2.7: Run git-filter-repo
```bash
# This rewrites all commits to remove the specified paths
git-filter-repo --invert-paths --paths-from-file paths-to-remove.txt --force

# Expected output:
# Parsed X commits
# Rewriting commits... done
# ...
# Completely finished after X seconds
```

### Step 2.8: Verify the Cleanup
```bash
# Check repository size
git count-objects -vH

# Expected: size-pack should be 5-10 MiB (down from 60 MiB)

# Verify files are gone from history
git log --all --name-only | grep -E "(venv|node_modules)" && echo "ERROR: Still in history!" || echo "✓ Removed from history"

# Check branches still exist
git branch -a
```

### Step 2.9: Add Remote and Force Push
```bash
# git-filter-repo removes remotes for safety
# Add it back
git remote add origin https://github.com/munaimtahir/radreport.git

# Force push all branches
git push origin --force --all

# Force push all tags
git push origin --force --tags
```

### Step 2.10: Verify on GitHub
1. Go to https://github.com/munaimtahir/radreport
2. Check commits - SHAs should be different
3. Browse files - verify venv/, node_modules/ are gone
4. Check Insights → Network → Clone size should be reduced

### Step 2.11: Notify Team to Re-clone

**Send notification:**

```
Subject: [COMPLETE] Repository Cleanup - Please Re-clone Now

The radreport repository cleanup is complete!

Repository size: 82 MB → 10 MB ✓

Next Steps:
1. Delete your local clone:
   rm -rf radreport
   
2. Re-clone from GitHub:
   git clone https://github.com/munaimtahir/radreport.git
   cd radreport
   
3. Recreate branches if needed:
   git checkout -b your-branch-name
   
4. Set up dependencies:
   - Backend: cd backend && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt
   - Frontend: cd frontend && npm install

If you have unpushed commits:
1. Save them to patch files before deleting:
   git format-patch origin/main..HEAD -o ~/radreport-patches/
2. After re-cloning, apply patches:
   git am ~/radreport-patches/*.patch
```

### Step 2.12: Remove Repository Lock
On GitHub:
1. Go to Settings → Branches
2. Edit branch protection rule for `main`
3. Uncheck "Lock branch"
4. Save changes

### Step 2.13: Update CI/CD Systems
If you have CI/CD (GitHub Actions, etc.), they may need to:
- Clear caches
- Re-clone repositories
- Update any hardcoded commit SHAs

**✓ Phase 2 Complete!**

**Results:**
- ✅ Git history cleaned of bloat files
- ✅ Repository size reduced by 85-90%
- ✅ Faster clones and operations
- ✅ All collaborators on clean repository

---

## Phase 3: Prevent Future Bloat (Ongoing Maintenance)

### Option A: Pre-commit Hooks
Install pre-commit framework:

```bash
pip install pre-commit
```

Create `.pre-commit-config.yaml`:
```yaml
repos:
  - repo: local
    hooks:
      - id: check-large-files
        name: Check for large files
        entry: bash -c 'if git diff --cached --name-only | xargs du -ab 2>/dev/null | awk "\$1 > 1000000 {print; exit 1}"; then echo "ERROR: Large file detected"; exit 1; fi'
        language: system
        
      - id: check-forbidden-files
        name: Check for forbidden files
        entry: bash -c 'if git diff --cached --name-only | grep -E "(node_modules|venv|__pycache__|\.pyc$|db\.sqlite3|staticfiles)"; then echo "ERROR: Forbidden file/directory detected"; exit 1; fi'
        language: system
```

Install hooks:
```bash
pre-commit install
```

### Option B: GitHub Actions Check
Create `.github/workflows/check-repo-size.yml`:

```yaml
name: Check Repository Health

on: [push, pull_request]

jobs:
  check-files:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Check for large files
        run: |
          find . -type f -size +1M -not -path "./.git/*" | while read file; do
            echo "ERROR: Large file detected: $file"
            exit 1
          done
          
      - name: Check for forbidden directories
        run: |
          if [ -d "backend/venv" ] || [ -d "frontend/node_modules" ] || [ -d "backend/staticfiles" ]; then
            echo "ERROR: Forbidden directory detected"
            exit 1
          fi
          
      - name: Check for database files
        run: |
          if [ -f "backend/db.sqlite3" ]; then
            echo "ERROR: Database file should not be committed"
            exit 1
          fi
```

### Option C: Git LFS for Legitimate Large Files
If you need to version large files (documentation, diagrams, etc.):

```bash
# Install Git LFS
git lfs install

# Track specific file types
git lfs track "*.pdf"
git lfs track "*.psd"
git lfs track "*.sketch"

# Commit .gitattributes
git add .gitattributes
git commit -m "Configure Git LFS for large files"
```

### Option D: Regular Audits
Schedule quarterly reviews:

```bash
# Check repository size
git count-objects -vH

# Find largest files in history
git rev-list --all --objects | \
  sed -n $(git rev-list --all --count)~1p | \
  cut -f 2 -d\  | \
  sort | uniq -c | sort -rn | head -20

# Check for newly added large files
git diff --stat main HEAD
```

---

## Troubleshooting

### Problem: "git-filter-repo not found"
**Solution:**
```bash
pip install --user git-filter-repo
# Or
pip3 install --user git-filter-repo
# Make sure ~/.local/bin is in PATH
export PATH=$PATH:~/.local/bin
```

### Problem: "remote 'origin' already exists"
**Solution:**
```bash
git remote remove origin
git remote add origin https://github.com/munaimtahir/radreport.git
```

### Problem: "failed to push some refs"
**Solution:**
```bash
# If you're doing Phase 2, you MUST force push
git push origin --force --all
git push origin --force --tags
```

### Problem: Collaborator has conflicts after re-clone
**Solution:**
Tell them to:
```bash
# Save work
git stash
# OR save to patches
git format-patch origin/main..HEAD -o ~/patches/

# Delete and re-clone
cd ..
rm -rf radreport
git clone https://github.com/munaimtahir/radreport.git
cd radreport

# Restore work
git stash pop
# OR apply patches
git am ~/patches/*.patch
```

### Problem: CI/CD failing after history cleanup
**Solution:**
- Clear CI/CD caches in GitHub Actions settings
- Update any hardcoded commit SHAs in workflows
- Ensure CI/CD uses fresh clones, not cached repositories

### Problem: "The repository still shows as 82 MB on GitHub"
**Solution:**
- GitHub may cache the repository size - wait 24-48 hours for update
- Try viewing in Insights → Network to see actual size
- Ask GitHub support to refresh repository size if needed

---

## Verification Checklist

After completing cleanup:

### Phase 1 Verification
- [ ] `git status` shows clean working tree
- [ ] `git ls-files | grep venv` returns nothing
- [ ] `git ls-files | grep node_modules` returns nothing
- [ ] `git ls-files backend/staticfiles` returns nothing
- [ ] `git ls-files backend/db.sqlite3` returns nothing
- [ ] Backend runs after `pip install -r requirements.txt`
- [ ] Frontend runs after `npm install`
- [ ] README includes setup instructions

### Phase 2 Verification
- [ ] `git count-objects -vH` shows size-pack < 10 MiB
- [ ] `git log --all --name-only | grep venv` returns nothing
- [ ] `git log --all --name-only | grep node_modules` returns nothing
- [ ] All branches pushed successfully
- [ ] All tags pushed successfully
- [ ] GitHub shows reduced repository size (may take 24-48 hours)
- [ ] All collaborators notified and have re-cloned
- [ ] CI/CD systems updated and working

### Phase 3 Verification
- [ ] Pre-commit hooks installed (optional)
- [ ] GitHub Actions check added (optional)
- [ ] Git LFS configured if needed (optional)
- [ ] Team educated on not committing dependencies

---

## Rollback Procedure (If Something Goes Wrong)

### Rollback Phase 1 (Easy)
```bash
git checkout main
git revert <commit-sha-of-removal>
git push origin main
```

### Rollback Phase 2 (Uses Backup)
```bash
# Delete the broken repository
cd ~/projects
rm -rf radreport

# Restore from backup mirror
git clone radreport-backup-YYYYMMDD radreport
cd radreport

# Force push back to GitHub
git remote add origin https://github.com/munaimtahir/radreport.git
git push origin --force --all
git push origin --force --tags
```

---

## Success Metrics

After completing all phases:

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Repository Size (Pack) | 60 MB | 5-10 MB | 85-90% |
| Clone Time | ~30s | ~5s | 83% |
| Number of Tracked Files | 14,207 | ~3,000 | 79% |
| Working Tree Size (fresh) | 258 MB | 88 KB | 99.9% |

---

## Contact and Support

If you encounter issues:
1. Check the Troubleshooting section above
2. Review the REPOSITORY_BLOAT_DIAGNOSTIC.md for technical details
3. Contact repository administrator
4. Refer to git-filter-repo documentation: https://github.com/newren/git-filter-repo

---

**Document Version:** 1.0  
**Last Updated:** January 7, 2026  
**Maintained By:** Repository Maintainers
