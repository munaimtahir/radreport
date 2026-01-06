# Deployment Guide - RIMS Application

This guide provides step-by-step instructions for deploying the RIMS (Radiology Information Management System) to production.

## Prerequisites

- Python 3.11+ installed
- Node.js 18+ and npm installed
- PostgreSQL 14+ database server
- Redis 7+ (optional, for caching)
- Domain name with SSL certificate
- Web server (Nginx or Caddy) for reverse proxy

---

## Pre-Deployment Checklist

### ⚠️ CRITICAL: Security Configuration

Before deploying, complete these security steps:

1. **Generate Strong SECRET_KEY:**
   ```bash
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```
   Save this in your production `.env` file.

2. **Create Production .env File:**
   ```bash
   cd backend
   cp .env.example .env
   ```
   Update all values, especially:
   - `DJANGO_SECRET_KEY` (use generated key from step 1)
   - `DJANGO_DEBUG=0` (disable debug mode)
   - `DJANGO_ALLOWED_HOSTS` (your production domain)
   - `DB_PASSWORD` (strong database password)
   - `CORS_ALLOWED_ORIGINS` (your frontend domain)

3. **Verify Security Settings:**
   - [ ] SECRET_KEY is 50+ characters and random
   - [ ] DEBUG=0
   - [ ] Strong database password
   - [ ] ALLOWED_HOSTS configured
   - [ ] CORS_ALLOWED_ORIGINS configured

---

## Deployment Options

Choose one of the following deployment methods:

- [Option 1: Traditional Server (Gunicorn + Nginx)](#option-1-traditional-server)
- [Option 2: Docker Deployment](#option-2-docker-deployment)
- [Option 3: Platform-as-a-Service (Heroku, Railway, etc.)](#option-3-platform-as-a-service)

---

## Option 1: Traditional Server (Gunicorn + Nginx)

### 1. Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3.11 python3-pip python3-venv postgresql postgresql-contrib nginx redis-server

# Create application user
sudo useradd -m -s /bin/bash rims
sudo su - rims
```

### 2. Clone Repository

```bash
cd /home/rims
git clone https://github.com/munaimtahir/radreport.git
cd radreport
```

### 3. Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn  # Production WSGI server

# Create .env file
cp .env.example .env
nano .env  # Edit with production values

# Create media and logs directories
mkdir -p media logs staticfiles
```

### 4. Database Setup

```bash
# Create PostgreSQL database and user
sudo -u postgres psql
```

In PostgreSQL shell:
```sql
CREATE DATABASE rims;
CREATE USER rims WITH PASSWORD 'your-strong-password-here';
ALTER ROLE rims SET client_encoding TO 'utf8';
ALTER ROLE rims SET default_transaction_isolation TO 'read committed';
ALTER ROLE rims SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE rims TO rims;
\q
```

Run migrations:
```bash
source .venv/bin/activate
python manage.py migrate
python manage.py collectstatic --no-input
python manage.py createsuperuser
```

### 5. Test Backend

```bash
# Test with Gunicorn
gunicorn --bind 0.0.0.0:8000 rims_backend.wsgi:application
```

Visit `http://your-server-ip:8000/api/health/` to verify.

### 6. Frontend Build

```bash
cd ../../frontend

# Install dependencies
npm install

# Build for production
npm run build
```

The build output will be in `frontend/dist/`.

### 7. Gunicorn Systemd Service

Create `/etc/systemd/system/rims.service`:

```ini
[Unit]
Description=RIMS Gunicorn daemon
After=network.target

[Service]
User=rims
Group=rims
WorkingDirectory=/home/rims/radreport/backend
Environment="PATH=/home/rims/radreport/backend/.venv/bin"
Environment="DJANGO_SETTINGS_MODULE=rims_backend.settings_production"
ExecStart=/home/rims/radreport/backend/.venv/bin/gunicorn \
    --workers 4 \
    --bind unix:/home/rims/radreport/backend/rims.sock \
    --timeout 120 \
    --access-logfile /home/rims/radreport/backend/logs/gunicorn-access.log \
    --error-logfile /home/rims/radreport/backend/logs/gunicorn-error.log \
    rims_backend.wsgi:application

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable rims
sudo systemctl start rims
sudo systemctl status rims
```

### 8. Nginx Configuration

Create `/etc/nginx/sites-available/rims`:

```nginx
upstream rims_backend {
    server unix:/home/rims/radreport/backend/rims.sock fail_timeout=0;
}

server {
    listen 80;
    server_name your-domain.com;

    client_max_body_size 50M;

    # Frontend (React build)
    location / {
        root /home/rims/radreport/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api {
        proxy_pass http://rims_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }

    # Static files
    location /static {
        alias /home/rims/radreport/backend/staticfiles;
    }

    # Media files
    location /media {
        alias /home/rims/radreport/backend/media;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/rims /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 9. SSL with Certbot (Let's Encrypt)

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### 10. Final Verification

- [ ] Backend API: `https://your-domain.com/api/health/`
- [ ] API Docs: `https://your-domain.com/api/docs/`
- [ ] Frontend: `https://your-domain.com/`
- [ ] Login works
- [ ] Can create patient/study
- [ ] PDF generation works

---

## Option 2: Docker Deployment

### 1. Create Backend Dockerfile

Create `backend/Dockerfile`:

```dockerfile
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy application
COPY . .

# Create directories
RUN mkdir -p media logs staticfiles

# Collect static files
RUN python manage.py collectstatic --no-input

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "rims_backend.wsgi:application"]
```

### 2. Create Frontend Dockerfile

Create `frontend/Dockerfile`:

```dockerfile
FROM node:20-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### 3. Create Docker Compose Production

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  db:
    image: postgres:16
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7
    restart: unless-stopped

  backend:
    build: ./backend
    environment:
      - DJANGO_SETTINGS_MODULE=rims_backend.settings_production
      - DJANGO_SECRET_KEY=${DJANGO_SECRET_KEY}
      - DB_NAME=${DB_NAME}
      - DB_USER=${DB_USER}
      - DB_PASSWORD=${DB_PASSWORD}
      - DB_HOST=db
      - DB_PORT=5432
    volumes:
      - media_files:/app/media
      - static_files:/app/staticfiles
    depends_on:
      - db
      - redis
    restart: unless-stopped

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: unless-stopped

volumes:
  postgres_data:
  media_files:
  static_files:
```

### 4. Deploy with Docker

```bash
# Build and start
docker-compose -f docker-compose.prod.yml up -d

# Run migrations
docker-compose -f docker-compose.prod.yml exec backend python manage.py migrate

# Create superuser
docker-compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser
```

---

## Option 3: Platform-as-a-Service

### Heroku Deployment

1. **Install Heroku CLI:**
   ```bash
   curl https://cli-assets.heroku.com/install.sh | sh
   ```

2. **Create Heroku App:**
   ```bash
   heroku create rims-app
   heroku addons:create heroku-postgresql:mini
   heroku addons:create heroku-redis:mini
   ```

3. **Set Environment Variables:**
   ```bash
   heroku config:set DJANGO_SECRET_KEY="your-secret-key"
   heroku config:set DJANGO_DEBUG=0
   heroku config:set DJANGO_SETTINGS_MODULE=rims_backend.settings_production
   ```

4. **Deploy:**
   ```bash
   git push heroku main
   heroku run python backend/manage.py migrate
   heroku run python backend/manage.py createsuperuser
   ```

---

## Post-Deployment

### 1. Health Checks

Set up monitoring:
- Health endpoint: `/api/health/`
- Monitor response time
- Monitor error rates
- Set up alerts

### 2. Backup Strategy

```bash
# Database backup script
#!/bin/bash
BACKUP_DIR="/home/rims/backups"
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump -U rims -h localhost rims > "$BACKUP_DIR/rims_$DATE.sql"
find $BACKUP_DIR -name "rims_*.sql" -mtime +7 -delete
```

Schedule with cron:
```bash
0 2 * * * /home/rims/scripts/backup.sh
```

### 3. Log Rotation

Create `/etc/logrotate.d/rims`:

```
/home/rims/radreport/backend/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 rims rims
    sharedscripts
    postrotate
        systemctl reload rims
    endscript
}
```

### 4. Monitoring

Consider adding:
- Sentry for error tracking
- New Relic or Datadog for APM
- Uptime monitoring (UptimeRobot, Pingdom)

---

## Troubleshooting

### Backend Issues

**502 Bad Gateway:**
```bash
# Check Gunicorn status
sudo systemctl status rims
sudo journalctl -u rims -f

# Check logs
tail -f /home/rims/radreport/backend/logs/gunicorn-error.log
```

**Database Connection Errors:**
```bash
# Test database connection
python manage.py dbshell
```

**Static Files Not Loading:**
```bash
python manage.py collectstatic --no-input
sudo systemctl restart rims
```

### Frontend Issues

**404 on Refresh:**
- Ensure Nginx `try_files` is configured correctly
- Check frontend build exists in correct location

---

## Rollback Procedure

```bash
# 1. Switch to previous version
cd /home/rims/radreport
git checkout <previous-commit>

# 2. Rebuild frontend
cd frontend
npm run build

# 3. Restart backend
sudo systemctl restart rims

# 4. Rollback migrations if needed
cd ../backend
source .venv/bin/activate
python manage.py migrate <app_name> <migration_number>
```

---

## Security Best Practices

1. **Keep Dependencies Updated:**
   ```bash
   pip list --outdated
   npm outdated
   ```

2. **Regular Security Audits:**
   ```bash
   pip-audit
   npm audit
   ```

3. **Firewall Configuration:**
   ```bash
   sudo ufw allow 22
   sudo ufw allow 80
   sudo ufw allow 443
   sudo ufw enable
   ```

4. **Fail2Ban for Brute Force Protection:**
   ```bash
   sudo apt install fail2ban
   ```

---

## Maintenance

### Regular Tasks:

**Daily:**
- [ ] Monitor error logs
- [ ] Check application health
- [ ] Review audit logs

**Weekly:**
- [ ] Database backup verification
- [ ] Disk space check
- [ ] Security updates

**Monthly:**
- [ ] Review and update dependencies
- [ ] Performance analysis
- [ ] Security audit

---

## Support

For issues or questions:
- GitHub Issues: https://github.com/munaimtahir/radreport/issues
- Documentation: See `docs/` directory

---

**Last Updated:** January 6, 2026
