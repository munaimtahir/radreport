# Quick Test Guide - RIMS Application
**Date:** January 17, 2026  
**URL:** https://rims.alshifalab.pk

---

## 🔑 Admin Login Credentials

```
Username: admin
Password: admin123
```

---

## 🌐 Access Points

### 1. Main Application (Frontend)
**URL:** https://rims.alshifalab.pk

**What to test:**
- ✅ Login page loads
- ✅ Can login with admin credentials
- ✅ Dashboard displays correctly
- ✅ Navigation works
- ✅ Patient registration
- ✅ Service selection
- ✅ Report viewing

### 2. Django Admin Panel
**URL:** https://rims.alshifalab.pk/admin/

**What to test:**
- ✅ Admin login works
- ✅ Can view all models
- ✅ Can create/edit records
- ✅ Can view patients, services, studies
- ✅ Can manage users and permissions

### 3. API Endpoints
**Base URL:** https://rims.alshifalab.pk/api/

**Key endpoints to test:**

#### Authentication
```bash
# Get JWT Token
curl -X POST https://rims.alshifalab.pk/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Get User Info
curl https://rims.alshifalab.pk/api/auth/me/ \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

#### Health Check
```bash
curl https://rims.alshifalab.pk/api/health/
```

#### Patients
```bash
# List patients
curl https://rims.alshifalab.pk/api/patients/ \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

#### Services
```bash
# List services
curl https://rims.alshifalab.pk/api/services/ \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

---

## 🧪 Testing New USG Functionality

### 1. USG Worklist
**Frontend Route:** `/usg-worklist`

**What to test:**
- ✅ View pending USG studies
- ✅ Select a study to work on
- ✅ Create new USG study
- ✅ Filter and search functionality

### 2. USG Templates
**API Endpoint:** `/api/usg/templates/`

**What to test:**
```bash
# List USG templates
curl https://rims.alshifalab.pk/api/usg/templates/ \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### 3. USG Service Profiles
**API Endpoint:** `/api/usg/service-profiles/`

**What to test:**
```bash
# List service profiles
curl https://rims.alshifalab.pk/api/usg/service-profiles/ \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### 4. USG Studies
**API Endpoint:** `/api/usg/studies/`

**What to test:**
- ✅ Create new USG study
- ✅ Update study with findings
- ✅ Publish study
- ✅ Generate report PDF

---

## 📋 Testing Patient Registration Flow

### Frontend Flow
1. Navigate to **Registration Page**
2. Enter patient phone number
3. Fill in patient details:
   - Name
   - Age/DOB
   - Gender
   - Address
   - CNIC
   - Father/Husband name
4. Select services from catalog
5. Apply discount (if any)
6. Enter payment amount
7. Generate receipt

### API Flow
```bash
# 1. Create patient
curl -X POST https://rims.alshifalab.pk/api/patients/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "mrn": "TEST001",
    "name": "Test Patient",
    "age": 30,
    "gender": "Male",
    "phone": "03001234567"
  }'

# 2. Create service visit
curl -X POST https://rims.alshifalab.pk/api/workflow/visits/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "PATIENT_UUID",
    "items": [
      {
        "service_id": "SERVICE_UUID",
        "quantity": 1
      }
    ]
  }'
```

---

## 🧾 Testing Receipt Generation

### Via Frontend
1. Complete patient registration
2. Generate receipt
3. View receipt PDF
4. Print receipt

### Via API
```bash
# Get receipt PDF
curl https://rims.alshifalab.pk/api/pdf/receipt/VISIT_UUID/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -o receipt.pdf
```

---

## 📊 Testing Report Templates

### Frontend Routes
- **Report Templates:** `/report-templates`
- **Service Templates:** `/service-templates`

### API Endpoints
```bash
# List report templates
curl https://rims.alshifalab.pk/api/report-templates/ \
  -H "Authorization: Bearer YOUR_TOKEN"

# List template versions
curl https://rims.alshifalab.pk/api/template-versions/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 🔍 Testing Search Functionality

### Patient Search
1. Go to registration page
2. Enter phone number in search
3. Should show matching patients
4. Select existing patient or create new

### Service Search
1. In registration page
2. Search for services by:
   - Service name
   - Service code
   - Category

---

## 📱 Testing Receipt Settings

### Frontend Route
`/receipt-settings`

### What to test
- ✅ Update clinic name
- ✅ Update clinic address
- ✅ Update clinic phone
- ✅ Update footer text
- ✅ Save settings
- ✅ Verify changes in generated receipts

### API Endpoint
```bash
# Get receipt settings
curl https://rims.alshifalab.pk/api/receipt-settings/1/ \
  -H "Authorization: Bearer YOUR_TOKEN"

# Update receipt settings
curl -X PUT https://rims.alshifalab.pk/api/receipt-settings/1/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "clinic_name": "Your Clinic Name",
    "address": "Your Address",
    "phone": "Your Phone"
  }'
```

---

## 🩺 Testing Study Workflow

### Complete Workflow
1. **Registration:** Create patient and service visit
2. **Worklist:** View study in appropriate worklist (USG/XRAY/CT)
3. **Reporting:** Open study and create report
4. **Finalization:** Review and finalize report
5. **PDF Generation:** Download/print final report

### API Workflow
```bash
# 1. List studies
curl https://rims.alshifalab.pk/api/studies/ \
  -H "Authorization: Bearer YOUR_TOKEN"

# 2. Create report for study
curl -X POST https://rims.alshifalab.pk/api/reports/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "study_id": "STUDY_UUID",
    "findings": "Normal findings",
    "impression": "No abnormality detected"
  }'

# 3. Finalize report
curl -X POST https://rims.alshifalab.pk/api/reports/REPORT_UUID/finalize/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 🎯 Quick Smoke Test Checklist

Run these tests to quickly verify everything is working:

### Frontend Tests (5 minutes)
- [ ] Open https://rims.alshifalab.pk
- [ ] Login with admin/admin123
- [ ] Check dashboard loads
- [ ] Navigate to registration page
- [ ] Search for a patient
- [ ] View USG worklist
- [ ] Check receipt settings page

### Backend Tests (3 minutes)
- [ ] Health check returns OK
- [ ] Login API returns JWT token
- [ ] /api/auth/me/ returns user info
- [ ] /api/patients/ returns patient list
- [ ] /api/services/ returns services

### Admin Tests (2 minutes)
- [ ] Login to Django admin
- [ ] View patients list
- [ ] View services list
- [ ] Check system is in DEBUG=False mode

---

## 🐛 Common Issues & Solutions

### Issue: Cannot login
**Solution:** 
- Verify credentials: admin/admin123
- Check backend logs: `docker compose logs backend`
- Verify backend is running: `docker compose ps`

### Issue: API returns 502/503
**Solution:**
- Check container status: `docker compose ps`
- Check backend health: `curl https://rims.alshifalab.pk/api/health/`
- Restart backend: `docker compose restart backend`

### Issue: Frontend shows blank page
**Solution:**
- Check browser console for errors
- Verify frontend container: `docker compose logs frontend`
- Clear browser cache
- Try incognito/private mode

### Issue: CORS errors in browser
**Solution:**
- Verify CORS settings include https://rims.alshifalab.pk
- Check backend logs for CORS errors
- Verify CSRF_TRUSTED_ORIGINS is set correctly

---

## 📞 Quick Reference Commands

```bash
# Check all containers
cd /home/munaim/srv/apps/radreport
docker compose ps

# View backend logs
docker compose logs -f backend

# View frontend logs
docker compose logs -f frontend

# Restart everything
docker compose restart

# Check Caddy status
sudo systemctl status caddy

# View Caddy logs
sudo journalctl -u caddy -f
```

---

## ✅ Testing Completion Checklist

After testing, verify:

- [ ] Login functionality works
- [ ] Patient registration works
- [ ] Service selection works
- [ ] Receipt generation works
- [ ] USG worklist displays
- [ ] Report creation works
- [ ] PDF downloads work
- [ ] Admin panel accessible
- [ ] All API endpoints respond
- [ ] No console errors in browser
- [ ] No server errors in logs

---

**Happy Testing! 🎉**

For issues or questions, check:
- Backend logs: `docker compose logs backend`
- Frontend logs: `docker compose logs frontend`
- Health endpoint: https://rims.alshifalab.pk/api/health/

---

*Last Updated: January 17, 2026*
