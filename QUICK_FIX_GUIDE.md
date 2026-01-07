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

Edit `/etc/caddy/Caddyfile` and replace the entire RIMS section (lines 118-183) with:

```caddy
# =========================
# RIMS (Radiology Information Management System) - React + Django
# Domain: rims.alshifalab.pk
# Frontend container: 127.0.0.1:8081 (nginx serving built React app)
# Backend: 127.0.0.1:8015
# =========================
rims.alshifalab.pk {
	encode gzip zstd

	# ---- Static + media (served directly by Caddy for production) ----
	handle /static/* {
		root * /home/munaim/srv/apps/radreport/backend/staticfiles
		file_server
	}
	handle /media/* {
		root * /home/munaim/srv/apps/radreport/backend/media
		file_server
	}

	# ---- Backend routes ----
	handle /api/* {
		reverse_proxy 127.0.0.1:8015 {
			header_up Host {host}
			header_up X-Real-IP {remote}
		}
	}

	handle /admin/* {
		reverse_proxy 127.0.0.1:8015 {
			header_up Host {host}
			header_up X-Real-IP {remote}
		}
	}

	# Health endpoints
	handle /health* {
		reverse_proxy 127.0.0.1:8015
	}
	handle /healthz* {
		reverse_proxy 127.0.0.1:8015
	}

	# Optional API docs / schema
	handle_path /docs* {
		reverse_proxy 127.0.0.1:8015
	}
	handle_path /schema* {
		reverse_proxy 127.0.0.1:8015
	}

	# ---- Frontend SPA (proxied to frontend container) ----
	@notBackend {
		not path /api/*
		not path /admin/*
		not path /health*
		not path /healthz*
		not path /static/*
		not path /media/*
		not path /docs*
		not path /schema*
	}
	handle @notBackend {
		reverse_proxy 127.0.0.1:8081 {
			header_up Host {host}
			header_up X-Real-IP {remote}
		}
	}
}
```

**Key changes:**
- Lines 150-156: Changed from `reverse_proxy` to `file_server` with direct file paths
- Static files now served from `/home/munaim/srv/apps/radreport/backend/staticfiles`
- Media files served from `/home/munaim/srv/apps/radreport/backend/media`

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
