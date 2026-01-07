# RIMS (Radiology Information Management System) - Deployment Plan

## Current Caddy Configuration Review

### Existing Setup
- **Caddy Version**: Installed and running as systemd service
- **Caddyfile Location**: `/etc/caddy/Caddyfile`
- **Service Status**: Active and running
- **Log Location**: `/home/munaim/srv/proxy/caddy/logs/caddy.log`
- **Email**: Munaim.carled@gmail.com (for Let's Encrypt)

### Current Applications Configured
1. **SIMS** - `sims.alshifalab.pk`, `sims.pmc.edu.pk`
   - Frontend: `127.0.0.1:8080` (nginx container)
   - Backend: `127.0.0.1:8010`
   - Routes: `/api/*`, `/admin/*`, `/static/*`, `/media/*`, `/docs*`, `/schema*`

2. **CONSULT** - `consult.alshifalab.pk`
   - Backend: `127.0.0.1:8011`

3. **PG SIMS** - `pgsims.alshifalab.pk`
   - Backend: `127.0.0.1:8012`

4. **LIMS** - `lims.alshifalab.pk`, `lims.alshifalab.pka`
   - Backend: `127.0.0.1:8013`

5. **PHC** - `phc.alshifalab.pk`
   - Backend: `127.0.0.1:8014`

### Port Availability
- **Available ports**: 8015, 8016, 8017+ (for backend)
- **Available ports**: 8081, 8082+ (for frontend if using nginx container)
- **Ports in use**: 80, 443 (Caddy), 8010, 8013, 8080

### Issues Identified
1. **Log Permission Issue**: Caddy validation shows permission denied for log file (but service is running)
2. **Unnecessary Headers**: Warnings about redundant `X-Forwarded-For` and `X-Forwarded-Proto` headers
3. **Caddyfile Formatting**: Not formatted (can be fixed with `caddy fmt`)

---

## Deployment Plan for RIMS (radreport)

### Step 1: Choose Domain and Ports

**Recommended Configuration:**
- **Domain**: `rims.alshifalab.pk` ✅ (DNS configured and propagated)
- **Backend Port**: `8015` (Django/Gunicorn)
- **Frontend Port**: `8081` (nginx serving built React app) OR direct Vite dev server on `5173` (development only)

### Step 2: Backend Deployment

#### 2.1 Environment Setup
- Create production `.env` file or use environment variables
- Configure database (PostgreSQL via Docker Compose)
- Set production settings:
  - `DJANGO_DEBUG=0`
  - `DJANGO_SECRET_KEY=<strong-secret-key>`
  - `DJANGO_ALLOWED_HOSTS=rims.alshifalab.pk,localhost,127.0.0.1`
  - `CORS_ALLOWED_ORIGINS=https://rims.alshifalab.pk`

#### 2.2 Database Migration
- Use PostgreSQL (already configured in docker-compose.yml)
- Run migrations
- Create superuser

#### 2.3 Gunicorn Service
- Create systemd service for Gunicorn
- Bind to `127.0.0.1:8015`
- Use 3-4 workers
- Enable auto-restart

### Step 3: Frontend Deployment

#### Option A: Production Build with Nginx (Recommended)
- Build React app: `npm run build`
- Serve via nginx container on port `8081`
- Similar to SIMS setup

#### Option B: Direct Static File Serving
- Build React app: `npm run build`
- Serve static files via Django or separate nginx
- Configure Caddy to serve static files directly

### Step 4: Caddy Configuration

Add to `/etc/caddy/Caddyfile`:

```caddy
# =========================
# RIMS (Radiology Information Management System)
# Domain: radreport.alshifalab.pk
# Frontend: 127.0.0.1:8081 (nginx) or static files
# Backend: 127.0.0.1:8015
# =========================
rims.alshifalab.pk {
	encode gzip zstd

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

	# Static + media
	handle /static/* {
		reverse_proxy 127.0.0.1:8015
	}
	handle /media/* {
		reverse_proxy 127.0.0.1:8015
	}

	# API docs / schema
	handle_path /docs* {
		reverse_proxy 127.0.0.1:8015
	}
	handle_path /schema* {
		reverse_proxy 127.0.0.1:8015
	}

	# ---- Frontend SPA ----
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

### Step 5: DNS Configuration

Ensure DNS A record points to your VPS IP:
- `radreport.alshifalab.pk` → VPS IP address

---

## Implementation Steps

### Phase 1: Backend Setup
1. ✅ Review current configuration
2. ⬜ Create production environment file
3. ⬜ Set up PostgreSQL database
4. ⬜ Run migrations
5. ⬜ Create Gunicorn systemd service
6. ⬜ Test backend on port 8015

### Phase 2: Frontend Setup
1. ⬜ Build production frontend
2. ⬜ Set up nginx container OR configure static serving
3. ⬜ Test frontend on port 8081

### Phase 3: Caddy Integration
1. ✅ Add RIMS configuration to Caddyfile
2. ✅ Validate Caddyfile
3. ✅ Reload Caddy service
4. ⬜ Test SSL certificate generation (will happen automatically on first request)

### Phase 4: Testing & Verification
1. ⬜ Test API endpoints
2. ⬜ Test frontend routing
3. ⬜ Verify static/media file serving
4. ⬜ Check SSL certificate
5. ⬜ Test authentication flow

---

## Files to Create/Modify

1. **Backend**:
   - `.env` or environment variables
   - `gunicorn.service` (systemd service file)
   - `gunicorn_config.py` (optional)

2. **Frontend**:
   - Production build
   - `nginx.conf` (if using nginx container)
   - `docker-compose.yml` update (if using container)

3. **Caddy**:
   - Update `/etc/caddy/Caddyfile`

4. **Deployment Scripts**:
   - `deploy.sh` (optional automation)

---

## Security Considerations

1. **Environment Variables**: Never commit secrets to git
2. **DEBUG Mode**: Disable in production
3. **ALLOWED_HOSTS**: Restrict to specific domains
4. **CORS**: Configure allowed origins properly
5. **SSL**: Caddy handles automatically via Let's Encrypt
6. **Database**: Use strong PostgreSQL password
7. **Secret Key**: Generate strong Django secret key

---

## Monitoring & Maintenance

1. **Logs**:
   - Caddy: `/home/munaim/srv/proxy/caddy/logs/caddy.log`
   - Gunicorn: Configure logging in systemd service
   - Django: Configure logging in settings.py

2. **Health Checks**:
   - `/health` endpoint for monitoring
   - Systemd service status

3. **Updates**:
   - Regular dependency updates
   - Database migrations
   - Frontend rebuilds

---

## Next Steps

Would you like me to:
1. Create the production environment configuration?
2. Set up the Gunicorn systemd service?
3. Create the nginx configuration for frontend?
4. Update the Caddyfile with RIMS configuration?
5. Create deployment scripts?

## ✅ Completed Steps

- ✅ **Domain configured**: `rims.alshifalab.pk` (DNS propagated)
- ✅ **Caddy configuration added**: RIMS block added to `/etc/caddy/Caddyfile`
- ✅ **Caddy reloaded**: Service reloaded successfully

## Next Steps

Please confirm:
- **Deployment approach** (nginx container vs direct static serving)
- **Database preference** (PostgreSQL via Docker Compose or external)
