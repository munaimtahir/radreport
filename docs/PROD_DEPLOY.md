# Production Deployment Guide

This document provides step-by-step instructions for deploying RIMS to a VPS with Docker + Caddy.

## Prerequisites

- VPS with Docker and Docker Compose installed
- Caddy installed and configured on the host
- Domain name pointing to VPS IP
- SSH access to VPS

## Required Environment Variables

Create a `.env` file in the project root:

```bash
# Django settings
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=0
DJANGO_ALLOWED_HOSTS=rims.alshifalab.pk,api.rims.alshifalab.pk,localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=https://rims.alshifalab.pk
CSRF_TRUSTED_ORIGINS=https://rims.alshifalab.pk,https://api.rims.alshifalab.pk

# Database settings
DB_NAME=rims
DB_USER=rims
DB_PASSWORD=your-db-password-here
DB_HOST=db
DB_PORT=5432

# Backup settings (optional)
BACKUP_ROOT=/app/backups
BACKUP_RCLONE_REMOTE=offsite
BACKUP_RCLONE_PATH=radreport-backups

# Gunicorn tuning (optional)
GUNICORN_WORKERS=4
GUNICORN_TIMEOUT=120
```

## Docker Compose Commands

### Initial Deployment

```bash
# Clone repository (if not already done)
git clone <repository-url> /home/munaim/srv/apps/radreport
cd /home/munaim/srv/apps/radreport

# Create media directory
mkdir -p ./data/media

# Build and start services
docker compose -f docker-compose.prod.yml up -d --build

# Check logs
docker compose -f docker-compose.prod.yml logs -f backend
```

### Common Operations

```bash
# Stop services
docker compose -f docker-compose.prod.yml down

# Restart services
docker compose -f docker-compose.prod.yml restart

# View logs
docker compose -f docker-compose.prod.yml logs -f

# Rebuild after code changes
docker compose -f docker-compose.prod.yml up -d --build

# Execute commands in backend container
docker compose -f docker-compose.prod.yml exec backend python manage.py <command>
```

## Caddy Routing Summary

Caddy routes requests as follows:

- `/api/*` → Backend container (127.0.0.1:8015)
- `/media/*` → Host filesystem (served directly by Caddy)
- `/admin/*` → Backend container (127.0.0.1:8015)
- `/static/*` → Backend container or host filesystem (depending on setup)
- `/` → Frontend container (127.0.0.1:8081)

### Caddyfile Configuration

Add to your Caddyfile:

```caddy
rims.alshifalab.pk {
    encode gzip zstd

    # Media files - served directly from host
    handle /media/* {
        root * /home/munaim/srv/apps/radreport/data/media
        file_server
        header Cache-Control "public, max-age=604800"
    }

    # API endpoints - proxied to backend
    handle /api/* {
        reverse_proxy 127.0.0.1:8015 {
            header_up Host {host}
            header_up X-Real-IP {remote}
            header_up X-Forwarded-For {remote}
            header_up X-Forwarded-Proto {scheme}
            header_up X-Forwarded-Host {host}
        }
    }

    # Admin routes - proxied to backend
    handle /admin/* {
        reverse_proxy 127.0.0.1:8015 {
            header_up Host {host}
            header_up X-Real-IP {remote}
            header_up X-Forwarded-For {remote}
            header_up X-Forwarded-Proto {scheme}
            header_up X-Forwarded-Host {host}
        }
    }

    # Frontend - proxied to frontend container
    handle {
        reverse_proxy 127.0.0.1:8081 {
            header_up Host {host}
            header_up X-Real-IP {remote}
            header_up X-Forwarded-For {remote}
            header_up X-Forwarded-Proto {scheme}
        }
    }
}
```

After updating Caddyfile:

```bash
# Validate Caddyfile
caddy validate --config /etc/caddy/Caddyfile

# Reload Caddy
sudo systemctl reload caddy
```

## Running Smoke Tests

After deployment, run the production smoke test:

```bash
# Set environment variables
export BASE_URL=https://rims.alshifalab.pk
export ADMIN_USER=admin
export ADMIN_PASS=your-admin-password

# Run smoke test
./scripts/smoke_prod.sh
```

Expected output:
```
==========================================
Production Smoke Test
==========================================
Base URL: https://rims.alshifalab.pk
Admin User: admin

[1/5] Testing health endpoint...
✓ PASS: Health endpoint
  HTTP 200

[2/5] Testing authentication...
✓ PASS: Authentication
  Token obtained

[3/5] Testing printing config endpoint...
✓ PASS: Printing config endpoint
  HTTP 200 + JSON

[4/5] Testing sequence next endpoint...
✓ PASS: Sequence next endpoint
  HTTP 200 + next=2602-0001

[5/5] Testing backups endpoint...
✓ PASS: Backups endpoint
  HTTP 200 + JSON

==========================================
✓ All smoke tests PASSED
==========================================
```

## Running Restore Drill (Scratch)

To test backup restore functionality on a clean database:

### 1. Create a Backup

```bash
# Via API (requires auth token)
TOKEN=$(curl -s -X POST https://rims.alshifalab.pk/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}' | \
  grep -o '"access":"[^"]*' | cut -d'"' -f4)

curl -X POST https://rims.alshifalab.pk/api/backups/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"force":false,"deletable":true}'
```

Or via management command:

```bash
docker compose -f docker-compose.prod.yml exec backend python manage.py backup_run
```

### 2. Stop Services and Clear Database

```bash
# Stop services
docker compose -f docker-compose.prod.yml down

# Remove database volume (WARNING: This deletes all data)
docker volume rm PROD_radreport_pgdata

# Or if using bind mount, remove data directory
# rm -rf /path/to/postgres/data/*
```

### 3. Restore from Backup

```bash
# Start services (will create fresh database)
docker compose -f docker-compose.prod.yml up -d db
sleep 10  # Wait for database to be ready

# Restore backup (replace BACKUP_ID with actual backup ID)
docker compose -f docker-compose.prod.yml exec backend python manage.py backup_restore BACKUP_ID --yes

# Or via API
curl -X POST https://rims.alshifalab.pk/api/backups/BACKUP_ID/restore/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"confirm_phrase":"RESTORE","dry_run":false,"yes":true}'
```

### 4. Verify Restore

```bash
# Run smoke tests
./scripts/smoke_prod.sh

# Check data integrity
docker compose -f docker-compose.prod.yml exec backend python manage.py shell
# In Django shell:
# >>> from apps.patients.models import Patient
# >>> Patient.objects.count()  # Should match pre-restore count
```

## Troubleshooting

### Database Connection Issues

```bash
# Check database container logs
docker compose -f docker-compose.prod.yml logs db

# Test database connection
docker compose -f docker-compose.prod.yml exec backend python manage.py dbshell
```

### Backend Not Starting

```bash
# Check backend logs
docker compose -f docker-compose.prod.yml logs backend

# Check if migrations ran
docker compose -f docker-compose.prod.yml exec backend python manage.py showmigrations

# Run migrations manually if needed
docker compose -f docker-compose.prod.yml exec backend python manage.py migrate
```

### Media Files Not Accessible

1. Verify media directory exists: `ls -la ./data/media`
2. Check Caddyfile has `/media/*` handler
3. Verify Caddy has read permissions: `sudo chmod -R 755 ./data/media`
4. Test media URL: `curl -I https://rims.alshifalab.pk/media/test.txt`

### Port Conflicts

If ports 8015 or 8081 are already in use:

```bash
# Check what's using the port
sudo lsof -i :8015
sudo lsof -i :8081

# Update docker-compose.prod.yml to use different ports
# Then update Caddyfile accordingly
```

## Maintenance

### Regular Backups

Set up a cron job for automated backups:

```bash
# Add to crontab (crontab -e)
0 2 * * * cd /home/munaim/srv/apps/radreport && docker compose -f docker-compose.prod.yml exec -T backend python manage.py backup_run
```

### Log Rotation

Configure log rotation for Docker containers:

```bash
# Create /etc/docker/daemon.json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

### Updates

To update the application:

```bash
# Pull latest code
git pull

# Rebuild and restart
docker compose -f docker-compose.prod.yml up -d --build

# Run migrations if needed
docker compose -f docker-compose.prod.yml exec backend python manage.py migrate

# Run smoke tests
./scripts/smoke_prod.sh
```
