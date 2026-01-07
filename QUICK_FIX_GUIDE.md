# Quick Fix Guide - RIMS Production

## 🚨 Critical Issue Found

**Static files returning 404** - All other workflows working (13/14 PASS)

## ⚡ Quick Fix (5 minutes)

### Step 1: SSH into VPS
```bash
ssh user@34.124.150.231
cd /home/munaim/srv/apps/radreport
```

### Step 2: Run Fix Script
```bash
bash PRODUCTION_FIX_SCRIPT.sh
```

### Step 3: Fix Static Files in Caddy

Edit `/etc/caddy/Caddyfile` and update the RIMS section:

```caddy
rims.alshifalab.pk {
    encode gzip zstd

    # ADD THESE LINES - Serve static files directly
    handle /static/* {
        root * /home/munaim/srv/apps/radreport/backend/staticfiles
        file_server
    }
    
    handle /media/* {
        root * /home/munaim/srv/apps/radreport/backend/media
        file_server
    }

    # Existing backend routes...
    handle /api/* {
        reverse_proxy 127.0.0.1:8015 {
            header_up Host {host}
            header_up X-Real-IP {remote}
        }
    }
    # ... rest of config
}
```

### Step 4: Reload Caddy
```bash
sudo caddy validate --config /etc/caddy/Caddyfile
sudo systemctl reload caddy
```

### Step 5: Verify
```bash
curl -I https://rims.alshifalab.pk/static/admin/css/base.css
# Should return HTTP 200
```

## ✅ What's Working

- ✅ Authentication
- ✅ Patient registration  
- ✅ Study/exam registration
- ✅ Report generation
- ✅ Receipt generation
- ✅ All API endpoints

## 📋 Full Report

See `PRODUCTION_DEBUG_REPORT.md` for complete details.
