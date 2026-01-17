# Quick Deployment Scripts - User Guide
**Updated:** January 17, 2026  
**Location:** `/home/munaim/srv/apps/radreport`

---

## 📋 Overview

These scripts allow you to quickly rebuild and redeploy services after fixing code issues. They handle stopping, rebuilding, and restarting containers with proper error handling and health checks.

---

## 🚀 Available Scripts

### 1. `frontend.sh` - Frontend Only Deployment
**Use when:** You fix issues in React/TypeScript frontend code

```bash
cd /home/munaim/srv/apps/radreport
./frontend.sh
```

**What it does:**
- ✅ Stops frontend container
- ✅ Removes old frontend container and image
- ✅ Rebuilds frontend with no cache
- ✅ Starts new frontend container
- ✅ Shows logs and health checks
- ⏱️ **Time:** ~1-2 minutes

**When to use:**
- Fixed React component errors
- Updated TypeScript files
- Changed frontend styles/UI
- Fixed JavaScript crashes
- Updated package dependencies

---

### 2. `backend.sh` - Backend Only Deployment
**Use when:** You fix issues in Django/Python backend code

```bash
cd /home/munaim/srv/apps/radreport
./backend.sh
```

**What it does:**
- ✅ Keeps database running (no data loss)
- ✅ Stops backend container
- ✅ Removes old backend container and image
- ✅ Rebuilds backend with no cache
- ✅ Starts new backend container
- ✅ Runs migrations automatically
- ✅ Creates/verifies superuser (admin/admin123)
- ✅ Shows logs and health checks
- ⏱️ **Time:** ~2-3 minutes

**When to use:**
- Fixed Python/Django errors
- Updated API endpoints
- Changed database models
- Fixed business logic
- Updated requirements.txt

---

### 3. `both.sh` - Full Application Deployment
**Use when:** You fix issues in both frontend and backend

```bash
cd /home/munaim/srv/apps/radreport
./both.sh
```

**What it does:**
- ✅ Keeps database running (no data loss)
- ✅ Stops both frontend and backend
- ✅ Removes old containers and images
- ✅ Rebuilds both services with no cache
- ✅ Starts both containers
- ✅ Runs migrations automatically
- ✅ Creates/verifies superuser
- ✅ Shows logs and health checks for both
- ⏱️ **Time:** ~3-4 minutes

**When to use:**
- Multiple fixes across frontend and backend
- API contract changes affecting both sides
- Major updates requiring full rebuild
- After pulling latest code from git
- When in doubt, use this for safety

---

## 🎯 Quick Decision Guide

### "Which script should I use?"

```
Did you change files in frontend/src/?
  └─> YES → Use ./frontend.sh

Did you change files in backend/?
  └─> YES → Use ./backend.sh

Did you change files in BOTH?
  └─> YES → Use ./both.sh

Not sure? Or changed config files?
  └─> Use ./both.sh (safest option)
```

---

## 📝 Step-by-Step Usage

### Example: Fixing Frontend Issue

1. **Identify the issue** (e.g., page crash on service selection)

2. **Fix the code** (e.g., edit `frontend/src/views/RegistrationPage.tsx`)

3. **Run the frontend script:**
   ```bash
   cd /home/munaim/srv/apps/radreport
   ./frontend.sh
   ```

4. **Wait for completion** (~1-2 minutes)

5. **Clear browser cache** (Ctrl+Shift+R or Cmd+Shift+R)

6. **Test the fix** at https://rims.alshifalab.pk

---

### Example: Fixing Backend Issue

1. **Identify the issue** (e.g., API endpoint error)

2. **Fix the code** (e.g., edit `backend/apps/patients/api.py`)

3. **Run the backend script:**
   ```bash
   cd /home/munaim/srv/apps/radreport
   ./backend.sh
   ```

4. **Wait for completion** (~2-3 minutes)

5. **Check the logs** for superuser confirmation

6. **Test the API** at https://api.rims.alshifalab.pk/api/health/

---

## ✅ Success Indicators

### What to Look For

After running any script, you should see:

1. **Build Success:**
   ```
   ✓ built in X.XXs
   ```

2. **Container Status:**
   ```
   STATUS: Up X seconds (healthy)
   ```

3. **Health Check:**
   ```
   ✓ Backend health check: OK
   ✓ Frontend is accessible
   ✓ Backend is publicly accessible
   ```

4. **Superuser (backend only):**
   ```
   ✓ Superuser credentials verified: admin / admin123
   ```

---

## ⚠️ Common Issues & Solutions

### Issue: "ERROR: .env file not found!"
**Solution:**
```bash
cd /home/munaim/srv/apps/radreport
ls -la .env  # Check if file exists
```
The .env file contains database credentials and secret keys.

---

### Issue: "Health check: FAILED"
**Possible causes:**
1. Service still starting (wait 10-20 seconds)
2. Port conflict (check with `docker compose ps`)
3. Configuration error (check logs)

**Solution:**
```bash
# Check logs
docker compose logs -f backend  # or frontend

# Check if running
docker compose ps

# Restart if needed
docker compose restart backend  # or frontend
```

---

### Issue: Build fails with TypeScript errors
**Solution:**
```bash
# Check the error in the output
# Fix the TypeScript error in the code
# Run the script again
./frontend.sh
```

---

### Issue: Database connection error
**Solution:**
```bash
# Check database status
docker compose ps db

# If not running, start it
docker compose up -d db

# Wait 5 seconds then retry
sleep 5
./backend.sh
```

---

### Issue: "Permission denied"
**Solution:**
```bash
cd /home/munaim/srv/apps/radreport
chmod +x frontend.sh backend.sh both.sh
```

---

## 🔍 Monitoring & Debugging

### View Real-Time Logs
```bash
# Frontend logs
docker compose logs -f frontend

# Backend logs
docker compose logs -f backend

# Both services
docker compose logs -f frontend backend

# All services including database
docker compose logs -f
```

### Check Service Status
```bash
docker compose ps
```

### Test Services Manually
```bash
# Frontend
curl -I http://127.0.0.1:8081/
curl -I https://rims.alshifalab.pk

# Backend
curl http://127.0.0.1:8015/api/health/
curl https://api.rims.alshifalab.pk/api/health/
```

### Restart Without Rebuilding
```bash
# If just need restart (not rebuild)
docker compose restart frontend
docker compose restart backend
docker compose restart  # All services
```

---

## 📊 Script Output Explained

### Frontend Script Output
```
==========================================
Frontend Deployment Script
==========================================
Stopping frontend service...           ← Stopping old version
Removing frontend container...         ← Cleanup
Removing existing frontend image...    ← Force fresh build
Rebuilding frontend image...           ← Building new version
Starting frontend service...           ← Starting new version
Waiting for frontend to start...      ← Health check delay
Frontend service logs...               ← Recent activity
✓ Frontend is accessible              ← Success!
==========================================
✅ Frontend Deployment Complete!
==========================================
```

---

## 💡 Best Practices

### 1. **Always Check Logs**
After deployment, review logs for errors or warnings.

### 2. **Clear Browser Cache**
Frontend changes require cache clear (Ctrl+Shift+R).

### 3. **Test After Deployment**
Always verify the fix worked before closing.

### 4. **Use Version Control**
Commit working code before making new changes.

### 5. **One Service at a Time**
If possible, fix and deploy one service at a time for easier debugging.

### 6. **Document Changes**
Note what you fixed and when you deployed.

---

## 🆘 Emergency Commands

### Stop Everything
```bash
cd /home/munaim/srv/apps/radreport
docker compose down
```

### Start Everything
```bash
cd /home/munaim/srv/apps/radreport
docker compose up -d
```

### Nuclear Option (Full Reset)
```bash
cd /home/munaim/srv/apps/radreport
docker compose down
docker system prune -f
./both.sh
```

### View All Containers
```bash
docker ps -a
```

### Remove Stuck Containers
```bash
docker compose down --remove-orphans
```

---

## 📁 File Locations

```
/home/munaim/srv/apps/radreport/
├── frontend.sh          ← Frontend deployment script
├── backend.sh           ← Backend deployment script
├── both.sh              ← Full deployment script
├── docker-compose.yml   ← Docker configuration
├── .env                 ← Environment variables (secrets)
├── frontend/            ← React source code
│   └── src/
│       └── views/
│           └── RegistrationPage.tsx
└── backend/             ← Django source code
    ├── apps/
    ├── manage.py
    └── requirements.txt
```

---

## 🎓 Example Scenarios

### Scenario 1: Fixed Registration Page Crash
```bash
# 1. Fixed the bug in frontend code
# 2. Deploy frontend only
./frontend.sh

# 3. Wait for completion
# 4. Clear browser cache (Ctrl+Shift+R)
# 5. Test at https://rims.alshifalab.pk
```

### Scenario 2: Updated API Endpoint
```bash
# 1. Fixed the endpoint in backend code
# 2. Deploy backend only
./backend.sh

# 3. Wait for migrations to run
# 4. Test API: curl http://127.0.0.1:8015/api/health/
```

### Scenario 3: Updated Both Frontend and Backend
```bash
# 1. Made changes to both codebases
# 2. Deploy both services
./both.sh

# 3. Wait for full deployment
# 4. Clear browser cache
# 5. Test full workflow
```

### Scenario 4: After Git Pull
```bash
# 1. Pulled latest code
git pull origin main

# 2. Rebuild everything to be safe
./both.sh

# 3. Verify all features work
```

---

## ⏱️ Deployment Times

| Script | Average Time | What's Happening |
|--------|-------------|------------------|
| `frontend.sh` | 1-2 min | npm install, TypeScript compile, build |
| `backend.sh` | 2-3 min | pip install, migrations, superuser |
| `both.sh` | 3-4 min | Both above steps |

*Times may vary based on server load and changes*

---

## 🔐 Important Notes

### Database Persistence
- ✅ All scripts preserve database data
- ✅ No data loss during deployments
- ✅ Migrations run automatically

### Superuser Credentials
- **Username:** `admin`
- **Password:** `admin123`
- Created automatically on backend deployment
- If exists, scripts will detect and skip creation

### Zero Downtime
- Database keeps running during deployments
- Brief interruption (few seconds) during container restart
- Frontend and backend can restart independently

---

## 📞 Quick Reference

```bash
# Deploy frontend only (1-2 min)
./frontend.sh

# Deploy backend only (2-3 min)
./backend.sh

# Deploy both (3-4 min)
./both.sh

# View logs
docker compose logs -f

# Check status
docker compose ps

# Restart service
docker compose restart [service_name]

# Stop all
docker compose down

# Start all
docker compose up -d
```

---

## ✅ Checklist After Deployment

- [ ] Script completed without errors
- [ ] Containers show "healthy" status
- [ ] Health check passed
- [ ] Logs show no errors
- [ ] Browser cache cleared (frontend changes)
- [ ] Application accessible at public URL
- [ ] Login works (admin/admin123)
- [ ] Fixed issue is resolved
- [ ] Related features still work

---

**Remember:** When in doubt, use `./both.sh` - it's the safest option!

---

*Last Updated: January 17, 2026*
