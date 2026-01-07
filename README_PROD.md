# RIMS Production Deployment Guide

This guide provides step-by-step instructions for deploying RIMS (Radiology Information Management System) to production using Docker and Caddy as a reverse proxy.

## Architecture Overview

- **Backend**: Django 5 + DRF + Gunicorn (port 8015)
- **Frontend**: React + Vite + Nginx (port 8081)
- **Database**: PostgreSQL 16
- **Reverse Proxy**: Caddy (handles TLS/SSL automatically)
- **Deployment Method**: Docker Compose

## Prerequisites

- Ubuntu VPS (20.04 or 22.04 recommended)
- Docker and Docker Compose installed
- Caddy installed and running (optional, see alternatives below)
- Domain name pointed to your server (e.g., rims.alshifalab.pk)
- Root or sudo access

## Quick Reference

```bash
# Build and start
docker-compose up -d --build

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Stop services
docker-compose down

# Stop and remove volumes (destructive!)
docker-compose down -v
```

---

## Part 1: Server Preparation

### 1.1 Install Docker and Docker Compose

```bash
# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version

# Log out and back in for group changes to take effect
```

### 1.2 Install Caddy (if not already installed)

```bash
# Install Caddy
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update
sudo apt install caddy

# Verify installation
caddy version
```

---

## Part 2: Application Deployment

### 2.1 Clone Repository

```bash
# Create application directory
sudo mkdir -p /opt/apps
cd /opt/apps

# Clone repository
sudo git clone https://github.com/munaimtahir/radreport.git rims
cd rims

# Set proper ownership
sudo chown -R $USER:$USER /opt/apps/rims
```

### 2.2 Configure Environment Variables

```bash
# Copy example environment file
cp .env.prod.example .env.prod

# Edit with your actual values
nano .env.prod
```

**Required changes in .env.prod:**

```bash
# Generate a secure secret key (run this command):
python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'

# Update these values:
DJANGO_SECRET_KEY=your_generated_secret_key_here
DJANGO_ALLOWED_HOSTS=rims.alshifalab.pk,your.domain.com
CORS_ALLOWED_ORIGINS=https://rims.alshifalab.pk,https://your.domain.com
DB_PASSWORD=your_secure_database_password_here
```

### 2.3 Build and Start Services

```bash
# Build images (this will take a few minutes)
docker-compose build

# Start services in detached mode
docker-compose up -d

# Check that all services are running
docker-compose ps

# Expected output:
# NAME                  STATUS              PORTS
# rims_backend_prod     Up (healthy)        127.0.0.1:8015->8000/tcp
# rims_frontend_prod    Up                  127.0.0.1:8081->80/tcp
# rims_db_prod          Up (healthy)        5432/tcp
```

### 2.4 Create Django Superuser

```bash
# Enter backend container
docker-compose exec backend python manage.py createsuperuser

# Follow prompts to create admin user
# Username: admin
# Email: admin@example.com
# Password: (choose a secure password)
```

### 2.5 Verify Services

```bash
# Check backend health
curl http://127.0.0.1:8015/api/health/
# Expected: {"status":"ok"}

# Check frontend
curl http://127.0.0.1:8081/
# Expected: HTML content

# View backend logs
docker-compose logs -f backend

# View frontend logs
docker-compose logs -f frontend
```

---

## Part 3: Caddy Configuration

### Option A: Using System Caddy (Recommended)

Add the following block to your Caddyfile (typically at `/etc/caddy/Caddyfile`):

```caddy
# RIMS - Radiology Information Management System
rims.alshifalab.pk {
    encode gzip zstd

    # Backend API routes
    handle /api/* {
        reverse_proxy 127.0.0.1:8015 {
            header_up Host {host}
            header_up X-Real-IP {remote}
            header_up X-Forwarded-For {remote}
            header_up X-Forwarded-Proto {scheme}
        }
    }

    # Django admin
    handle /admin/* {
        reverse_proxy 127.0.0.1:8015 {
            header_up Host {host}
            header_up X-Real-IP {remote}
            header_up X-Forwarded-For {remote}
            header_up X-Forwarded-Proto {scheme}
        }
    }

    # Health endpoints
    handle /health* {
        reverse_proxy 127.0.0.1:8015
    }

    # Static files (served from backend staticfiles volume)
    handle /static/* {
        reverse_proxy 127.0.0.1:8015
    }

    # Media files (served from backend media volume)
    handle /media/* {
        reverse_proxy 127.0.0.1:8015
    }

    # API documentation
    handle_path /docs* {
        reverse_proxy 127.0.0.1:8015
    }
    handle_path /schema* {
        reverse_proxy 127.0.0.1:8015
    }

    # Frontend SPA (catch-all for all other routes)
    @notBackend {
        not path /api/*
        not path /admin/*
        not path /health*
        not path /static/*
        not path /media/*
        not path /docs*
        not path /schema*
    }
    handle @notBackend {
        reverse_proxy 127.0.0.1:8081 {
            header_up Host {host}
            header_up X-Real-IP {remote}
            header_up X-Forwarded-For {remote}
            header_up X-Forwarded-Proto {scheme}
        }
    }
}
```

Reload Caddy:

```bash
sudo systemctl reload caddy

# Check Caddy status
sudo systemctl status caddy

# View Caddy logs if issues occur
sudo journalctl -u caddy -f
```

### Option B: Alternative - Serve Frontend Static Files Directly with Caddy

If you prefer to serve frontend files directly from Caddy instead of proxying to the nginx container:

1. Build frontend locally and copy dist to Caddy root:

```bash
# Build frontend
cd frontend
npm install
npm run build

# Copy to Caddy serving directory
sudo mkdir -p /var/www/rims
sudo cp -r dist/* /var/www/rims/
```

2. Update Caddyfile frontend section:

```caddy
    # Frontend - serve static files directly
    @notBackend {
        not path /api/*
        not path /admin/*
        not path /health*
        not path /static/*
        not path /media/*
        not path /docs*
        not path /schema*
    }
    handle @notBackend {
        root * /var/www/rims
        try_files {path} {path}/ /index.html
        file_server
    }
```

---

## Part 4: Verification & Testing

### 4.1 Health Checks

```bash
# Backend health
curl https://rims.alshifalab.pk/api/health/
# Expected: {"status":"ok"}

# Frontend (should return HTML)
curl -I https://rims.alshifalab.pk/
# Expected: HTTP/2 200

# Django admin
curl -I https://rims.alshifalab.pk/admin/
# Expected: HTTP/2 302 (redirect to login)
```

### 4.2 Browser Testing

1. Open `https://rims.alshifalab.pk` in a browser
2. Verify frontend loads without errors
3. Check browser console for any errors
4. Test login functionality
5. Navigate to `https://rims.alshifalab.pk/admin/`
6. Login with superuser credentials
7. Verify admin interface works

### 4.3 API Testing

```bash
# Test authentication endpoint
curl -X POST https://rims.alshifalab.pk/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"your_password"}'

# Expected: {"access":"...","refresh":"..."}
```

---

## Part 5: Operational Tasks

### 5.1 View Logs

```bash
# All services
docker-compose logs -f

# Backend only
docker-compose logs -f backend

# Frontend only
docker-compose logs -f frontend

# Database only
docker-compose logs -f db

# Last 100 lines
docker-compose logs --tail=100 backend
```

### 5.2 Database Backup

```bash
# Create backup
docker-compose exec db pg_dump -U rims rims > backup_$(date +%Y%m%d_%H%M%S).sql

# Or using Docker directly
docker exec rims_db_prod pg_dump -U rims rims > backup_$(date +%Y%m%d_%H%M%S).sql
```

### 5.3 Database Restore

```bash
# Restore from backup
cat backup_20260107_120000.sql | docker-compose exec -T db psql -U rims rims

# Or using Docker directly
cat backup_20260107_120000.sql | docker exec -i rims_db_prod psql -U rims rims
```

### 5.4 Restart Services

```bash
# Restart all services
docker-compose restart

# Restart specific service
docker-compose restart backend
docker-compose restart frontend
docker-compose restart db
```

### 5.5 Update Application

```bash
# Navigate to application directory
cd /opt/apps/rims

# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose up -d --build

# Check logs for any issues
docker-compose logs -f
```

### 5.6 Execute Django Management Commands

```bash
# Run migrations
docker-compose exec backend python manage.py migrate

# Create superuser
docker-compose exec backend python manage.py createsuperuser

# Collect static files
docker-compose exec backend python manage.py collectstatic --noinput

# Django shell
docker-compose exec backend python manage.py shell

# Custom management command
docker-compose exec backend python manage.py your_custom_command
```

---

## Part 6: Rollback Strategy

### 6.1 Quick Rollback

If a deployment fails, you can quickly rollback:

```bash
# Stop current deployment
docker-compose down

# Checkout previous version
git log --oneline -5  # Find previous commit
git checkout <previous-commit-hash>

# Rebuild and start
docker-compose up -d --build

# Verify services
docker-compose ps
curl http://127.0.0.1:8015/api/health/
```

### 6.2 Database Rollback

If migrations fail:

```bash
# Restore database from backup
docker-compose down
docker volume rm rims_postgres_data

# Start database only
docker-compose up -d db

# Wait for DB to be ready
sleep 10

# Restore backup
cat backup_YYYYMMDD_HHMMSS.sql | docker-compose exec -T db psql -U rims rims

# Start all services
docker-compose up -d
```

---

## Part 7: Monitoring & Maintenance

### 7.1 Disk Space Monitoring

```bash
# Check Docker disk usage
docker system df

# Clean up unused images and containers
docker system prune -a

# Clean up volumes (careful - this removes data!)
docker volume prune
```

### 7.2 Log Rotation

Docker handles log rotation by default, but you can configure it:

Create or edit `/etc/docker/daemon.json`:

```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

Restart Docker:

```bash
sudo systemctl restart docker
```

### 7.3 Security Updates

```bash
# Update base images regularly
docker-compose pull
docker-compose up -d --build

# Update system packages
sudo apt-get update
sudo apt-get upgrade -y
```

---

## Part 8: Troubleshooting

### 8.1 Backend Not Starting

```bash
# Check logs
docker-compose logs backend

# Common issues:
# - Database not ready: Wait for DB healthcheck
# - Environment variables missing: Check .env.prod
# - Port already in use: Check with `sudo netstat -tlnp | grep 8015`
```

### 8.2 Database Connection Errors

```bash
# Verify database is running
docker-compose ps db

# Check database logs
docker-compose logs db

# Test connection
docker-compose exec backend python -c "from django.db import connection; connection.ensure_connection(); print('Connected!')"
```

### 8.3 Frontend Not Loading

```bash
# Check nginx logs
docker-compose logs frontend

# Verify build succeeded
docker-compose exec frontend ls -la /usr/share/nginx/html

# Test directly
curl http://127.0.0.1:8081/
```

### 8.4 Caddy SSL Certificate Issues

```bash
# Check Caddy logs
sudo journalctl -u caddy -f

# Verify DNS points to your server
dig rims.alshifalab.pk

# Check firewall allows ports 80 and 443
sudo ufw status
```

### 8.5 Permission Issues

```bash
# Fix media directory permissions
docker-compose exec backend chown -R appuser:appuser /app/media

# Fix staticfiles permissions
docker-compose exec backend chown -R appuser:appuser /app/staticfiles
```

---

## Part 9: Performance Tuning

### 9.1 Gunicorn Workers

Edit `scripts/entrypoint.sh` to adjust worker count:

```bash
# Rule of thumb: (2 x CPU cores) + 1
exec gunicorn rims_backend.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \  # Adjust based on CPU
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info
```

### 9.2 PostgreSQL Optimization

Add to docker-compose.yml under db service:

```yaml
    command: >
      postgres
      -c shared_buffers=256MB
      -c max_connections=200
      -c effective_cache_size=1GB
```

### 9.3 Connection Pooling

Consider adding PgBouncer for connection pooling in high-traffic scenarios.

---

## Part 10: Security Checklist

- [ ] Strong `DJANGO_SECRET_KEY` generated
- [ ] Strong `DB_PASSWORD` set
- [ ] `DJANGO_DEBUG=0` in production
- [ ] `ALLOWED_HOSTS` properly configured
- [ ] Services bound to `127.0.0.1` (not `0.0.0.0`)
- [ ] Firewall configured (only 80, 443, 22 open)
- [ ] Regular backups scheduled
- [ ] SSL/TLS enabled via Caddy
- [ ] Regular security updates applied
- [ ] Strong superuser password set
- [ ] `.env.prod` not committed to git

---

## Support & Resources

- **Repository**: https://github.com/munaimtahir/radreport
- **Django Documentation**: https://docs.djangoproject.com/
- **Docker Documentation**: https://docs.docker.com/
- **Caddy Documentation**: https://caddyserver.com/docs/

---

## Appendix: File Structure

```
/opt/apps/rims/
├── backend/
│   ├── Dockerfile               # Backend Docker image
│   ├── manage.py
│   ├── requirements.txt
│   ├── rims_backend/
│   │   └── settings.py
│   └── apps/
├── frontend/
│   ├── Dockerfile               # Frontend Docker image
│   ├── nginx.prod.conf          # Nginx configuration
│   ├── package.json
│   └── src/
├── scripts/
│   └── entrypoint.sh            # Backend startup script
├── docker-compose.yml           # Production orchestration
├── .env.prod.example            # Environment template
├── .env.prod                    # Actual secrets (git-ignored)
└── README_PROD.md              # This file
```

---

## Quick Commands Reference

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Restart service
docker-compose restart backend

# Execute command in backend
docker-compose exec backend python manage.py <command>

# Database backup
docker-compose exec db pg_dump -U rims rims > backup.sql

# Update deployment
git pull && docker-compose up -d --build

# Clean up
docker system prune -a
```
