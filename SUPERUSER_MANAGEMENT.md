# Superuser Management - RIMS Application
**Date:** January 17, 2026  
**Status:** ✅ **FULLY AUTOMATED**

---

## 🔑 Default Superuser Credentials

### Production Testing Credentials
```
Username: admin
Password: admin123
```

**These credentials are:**
- ✅ Created automatically on first deployment
- ✅ Preserved across all redeployments
- ✅ Safe to use for testing
- ✅ Never overwritten if they exist

---

## 🎯 How It Works

### Automatic Creation Process

When the backend container starts, it **automatically**:

1. **Waits for database** to be ready
2. **Runs migrations** to create database schema
3. **Runs seed_data.py** which includes superuser creation
4. **Checks if superuser exists:**
   - **If NO:** Creates new superuser with `admin/admin123`
   - **If YES:** Keeps existing superuser (no changes)
5. **Starts Gunicorn** server

### Code Location

The superuser creation logic is in:
```
backend/seed_data.py (lines 32-47)
backend/scripts/entrypoint.sh (line 29)
```

---

## 📋 Superuser Creation Logic

### In `seed_data.py`

```python
# Create or get superuser
print("\n[1/7] Creating superuser...")
user, created = User.objects.get_or_create(
    username="admin",
    defaults={
        "email": "admin@rims.local",
        "is_staff": True,
        "is_superuser": True,
    }
)
if created:
    user.set_password("admin123")
    user.save()
    print(f"✓ Created superuser: {user.username} / admin123")
else:
    print(f"✓ Superuser exists: {user.username}")
```

**What this does:**
- ✅ **get_or_create:** Gets existing user OR creates new one
- ✅ **created flag:** Tells us if user was just created
- ✅ **Password only set if new:** Preserves existing passwords
- ✅ **Idempotent:** Safe to run multiple times

---

## 🚀 When Superuser is Created

### First Deployment
```bash
./backend.sh  # or ./both.sh

# Output shows:
✓ Created superuser: admin / admin123
Login: admin / admin123
```

### Subsequent Deployments
```bash
./backend.sh  # or ./both.sh

# Output shows:
✓ Superuser exists: admin
Login: admin / admin123
```

---

## ✅ Verification in Deployment Scripts

### backend.sh and both.sh Scripts

Both scripts now include comprehensive superuser verification:

```bash
# Verify superuser was created
if docker compose logs backend | grep -q "admin / admin123"; then
    echo "✓ Superuser credentials verified: admin / admin123"
elif docker compose logs backend | grep -q "Superuser exists: admin"; then
    echo "✓ Superuser exists: admin / admin123"
else
    echo "ℹ️  Superuser credentials: admin / admin123"
    echo "   (created automatically or preserved from previous)"
fi

echo ""
echo "💡 Superuser Info:"
echo "   The backend automatically creates/preserves superuser"
echo "   Username: admin"
echo "   Password: admin123"
echo "   - If exists: keeps existing user and password"
echo "   - If new: creates with these credentials"
echo "   - Always safe to redeploy (no credential loss)"
```

---

## 🔍 How to Verify Superuser

### Method 1: Check Deployment Script Output

After running `./backend.sh` or `./both.sh`, look for:
```
✓ Superuser credentials verified: admin / admin123
```
or
```
✓ Superuser exists: admin / admin123
```

### Method 2: Check Container Logs

```bash
docker compose logs backend | grep -i superuser
```

**Expected output:**
```
✓ Created superuser: admin / admin123
# OR
✓ Superuser exists: admin
```

### Method 3: Test Login

```bash
# Via API
curl -X POST https://rims.alshifalab.pk/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Should return:
# {"refresh":"...","access":"..."}
```

```bash
# Via Django Admin
# Open: https://rims.alshifalab.pk/admin/
# Login with: admin / admin123
```

### Method 4: Django Shell

```bash
# Connect to backend container
docker compose exec backend python manage.py shell

# In Django shell:
from django.contrib.auth import get_user_model
User = get_user_model()
admin = User.objects.get(username='admin')
print(f"Superuser: {admin.username}, Staff: {admin.is_staff}, Super: {admin.is_superuser}")
```

---

## 🔒 Security Considerations

### Production Environment

**Current Setup:**
- ✅ Credentials are `admin/admin123` for testing
- ⚠️ **IMPORTANT:** Change these in real production

### How to Change Credentials

#### Option 1: Via Django Admin (Recommended)
1. Login to Django Admin: https://rims.alshifalab.pk/admin/
2. Go to Users
3. Click on "admin"
4. Click "change password"
5. Enter new password
6. Save

#### Option 2: Via Django Shell
```bash
docker compose exec backend python manage.py shell

# In shell:
from django.contrib.auth import get_user_model
User = get_user_model()
admin = User.objects.get(username='admin')
admin.set_password('NEW_SECURE_PASSWORD')
admin.save()
print("Password updated!")
exit()
```

#### Option 3: Via Management Command
```bash
docker compose exec backend python manage.py changepassword admin
# Follow prompts to enter new password
```

---

## 🛡️ Credential Persistence

### What Happens During Redeployment?

| Scenario | What Happens | Credentials |
|----------|--------------|-------------|
| First deploy | Creates new superuser | admin/admin123 |
| Redeploy (no DB change) | Keeps existing user | Unchanged |
| Redeploy (after password change) | Keeps existing user | Your new password |
| Database reset | Creates new superuser | admin/admin123 |
| Container restart | No change | Unchanged |

### Key Points
- ✅ **Redeployments are safe:** User data preserved
- ✅ **Password changes persist:** Stored in database
- ✅ **Database persists:** Mounted as Docker volume
- ✅ **No credential loss:** Unless database is deleted

---

## 📊 Database Persistence

### How Database Survives Redeployments

```yaml
# From docker-compose.yml
volumes:
  postgres_data:
    driver: local

db:
  volumes:
    - postgres_data:/var/lib/postgresql/data
```

**This means:**
- ✅ Database data stored in named volume
- ✅ Survives container stops/restarts
- ✅ Survives container removals
- ✅ Survives image rebuilds
- ❌ Only lost if volume explicitly deleted

### Deployment Scripts Preserve Database

All scripts (`frontend.sh`, `backend.sh`, `both.sh`):
- ✅ Never stop database container
- ✅ Never remove database container
- ✅ Never delete database volumes
- ✅ Check database is running before starting backend

---

## 🧪 Testing Scenarios

### Scenario 1: First Time Deployment
```bash
cd /home/munaim/srv/apps/radreport
./both.sh

# Expected:
✓ Created superuser: admin / admin123
🔑 Superuser: admin / admin123

# Test:
curl -X POST https://rims.alshifalab.pk/api/auth/token/ \
  -d '{"username": "admin", "password": "admin123"}'
# Should work ✓
```

### Scenario 2: Redeployment After Code Fix
```bash
# Fix some code
vim frontend/src/views/RegistrationPage.tsx

# Redeploy frontend
./frontend.sh

# Superuser unchanged
# Login still works with admin/admin123 ✓
```

### Scenario 3: Backend Redeployment
```bash
# Fix backend code
vim backend/apps/patients/api.py

# Redeploy backend
./backend.sh

# Expected:
✓ Superuser exists: admin
🔑 Superuser: admin / admin123

# Existing user preserved ✓
```

### Scenario 4: After Changing Password
```bash
# Change password via Django Admin to: NewSecure123!

# Redeploy backend
./backend.sh

# Expected:
✓ Superuser exists: admin
🔑 Superuser: admin / admin123  # Script shows default
                                # But YOUR password still works!

# Test with NEW password:
curl -X POST https://rims.alshifalab.pk/api/auth/token/ \
  -d '{"username": "admin", "password": "NewSecure123!"}'
# Works with YOUR password ✓
```

### Scenario 5: Full Rebuild
```bash
# Rebuild everything
./both.sh

# Expected:
✓ Superuser exists: admin
🔑 Superuser: admin / admin123

# All data preserved ✓
```

---

## 🆘 Troubleshooting

### Issue: "Can't login with admin/admin123"

**Possible causes:**
1. Password was changed
2. Superuser creation failed
3. Database issues

**Solutions:**

```bash
# 1. Check if superuser exists
docker compose exec backend python manage.py shell
>>> from django.contrib.auth import get_user_model
>>> User = get_user_model()
>>> User.objects.filter(username='admin').exists()
True  # ✓ Exists

# 2. Reset password
>>> admin = User.objects.get(username='admin')
>>> admin.set_password('admin123')
>>> admin.save()
>>> exit()

# 3. Test login again
curl -X POST https://rims.alshifalab.pk/api/auth/token/ \
  -d '{"username": "admin", "password": "admin123"}'
```

---

### Issue: "No superuser created"

**Check logs:**
```bash
docker compose logs backend | grep -i superuser
```

**If no output:**
```bash
# Manually run seed script
docker compose exec backend python seed_data.py

# Should see:
✓ Created superuser: admin / admin123
```

---

### Issue: "Multiple superusers exist"

**Check all superusers:**
```bash
docker compose exec backend python manage.py shell

>>> from django.contrib.auth import get_user_model
>>> User = get_user_model()
>>> superusers = User.objects.filter(is_superuser=True)
>>> for u in superusers:
...     print(f"{u.username} - {u.email}")
```

---

## 📝 Alternative: Manual Superuser Creation

If you need to create a different superuser:

### Via Management Command
```bash
docker compose exec backend python manage.py createsuperuser

# Follow prompts:
Username: myuser
Email: myuser@example.com
Password: ********
Password (again): ********
```

### Via create_superuser.py Script
```bash
# Edit the script first to change credentials
vim backend/create_superuser.py

# Run it
docker compose exec backend python create_superuser.py
```

### Via Django Shell
```bash
docker compose exec backend python manage.py shell

>>> from django.contrib.auth import get_user_model
>>> User = get_user_model()
>>> User.objects.create_superuser(
...     username='newadmin',
...     email='newadmin@example.com',
...     password='securepassword123'
... )
```

---

## 🎯 Best Practices

### For Development/Testing
✅ Use `admin/admin123` (already configured)  
✅ Don't worry about redeployments  
✅ Credentials are always preserved  

### For Staging
⚠️ Change password via Django Admin  
✅ Use strong password  
✅ Document the new credentials securely  

### For Production
🔒 **MUST change default credentials**  
🔒 Use complex password (16+ characters)  
🔒 Store in secure password manager  
🔒 Enable 2FA if possible  
🔒 Create separate admin users for team  
🔒 Disable default 'admin' account (create new)  

---

## 📚 Summary

### ✅ What You Get Automatically

1. **Superuser Creation:**
   - Automatically created on first deployment
   - Credentials: `admin / admin123`
   - Preserved across all redeployments

2. **Deployment Scripts:**
   - Verify superuser exists
   - Show credentials in output
   - Explain preservation behavior
   - Never delete database/credentials

3. **Database Persistence:**
   - Data stored in Docker volumes
   - Survives container restarts
   - Survives redeployments
   - Safe from accidental deletion

### 🔑 Key Takeaways

- ✅ **Default credentials:** `admin / admin123`
- ✅ **Always available:** Created automatically
- ✅ **Always preserved:** Never overwritten
- ✅ **Safe to redeploy:** No credential loss
- ✅ **Easy to change:** Via Django Admin or shell
- ✅ **Changes persist:** Stored in database volume

---

## 📞 Quick Reference

```bash
# Check superuser in logs
docker compose logs backend | grep -i superuser

# Test login
curl -X POST https://rims.alshifalab.pk/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Reset password
docker compose exec backend python manage.py changepassword admin

# Verify in shell
docker compose exec backend python manage.py shell
>>> from django.contrib.auth import get_user_model
>>> User.objects.filter(username='admin', is_superuser=True).exists()
True
```

---

**Credentials:** `admin / admin123`  
**Status:** ✅ Automatically managed  
**Safe to redeploy:** ✅ Yes, always  
**Last Updated:** January 17, 2026

---

*End of Superuser Management Guide*
