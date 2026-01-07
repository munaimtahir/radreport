# RIMS Production Deployment - Quick Start Guide

## 🚀 One-Command Deployment

For those who want to get started quickly:

```bash
# Clone and setup
git clone https://github.com/munaimtahir/radreport.git /opt/apps/rims
cd /opt/apps/rims
cp .env.prod.example .env.prod

# Edit .env.prod with your settings
nano .env.prod

# Deploy!
docker compose --env-file .env.prod up -d --build

# Create admin user
docker compose exec backend python manage.py createsuperuser

# Done! Now configure Caddy using CADDYFILE_SNIPPET.md
```

---

## 📋 Step-by-Step (Detailed)

### 1. Server Preparation (5 minutes)

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Log out and back in for group changes to take effect
exit
```

### 2. Clone Repository (1 minute)

```bash
# Create app directory
sudo mkdir -p /opt/apps
cd /opt/apps

# Clone repo
sudo git clone https://github.com/munaimtahir/radreport.git rims
cd rims

# Set ownership
sudo chown -R $USER:$USER /opt/apps/rims
```

### 3. Configure Environment (2 minutes)

```bash
# Copy example environment
cp .env.prod.example .env.prod

# Generate secret key
python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'

# Edit environment file
nano .env.prod
```

**Required changes in .env.prod:**
```bash
DJANGO_SECRET_KEY=<paste_generated_key>
DJANGO_ALLOWED_HOSTS=your.domain.com
CORS_ALLOWED_ORIGINS=https://your.domain.com
DB_PASSWORD=<your_secure_password>
```

### 4. Validate Configuration (30 seconds)

```bash
bash scripts/validate-deployment.sh
```

### 5. Deploy Application (5-10 minutes)

```bash
# Build images
docker compose --env-file .env.prod build

# Start services
docker compose --env-file .env.prod up -d

# Check status
docker compose ps

# View logs
docker compose logs -f
```

**Expected output:**
```
NAME                  STATUS              PORTS
rims_backend_prod     Up (healthy)        127.0.0.1:8015->8000/tcp
rims_frontend_prod    Up                  127.0.0.1:8081->80/tcp
rims_db_prod          Up (healthy)        5432/tcp
```

### 6. Create Admin User (1 minute)

```bash
docker compose exec backend python manage.py createsuperuser

# Follow prompts:
# Username: admin
# Email: admin@yourdomain.com
# Password: <secure_password>
```

### 7. Configure Caddy (3 minutes)

```bash
# Edit Caddyfile
sudo nano /etc/caddy/Caddyfile

# Add RIMS block (see CADDYFILE_SNIPPET.md)
# Then validate and reload
caddy validate --config /etc/caddy/Caddyfile
sudo systemctl reload caddy
```

### 8. Verify Deployment (2 minutes)

```bash
# Test backend locally
curl http://127.0.0.1:8015/api/health/
# Expected: {"status":"ok"}

# Test frontend locally
curl -I http://127.0.0.1:8081/
# Expected: HTTP/1.1 200 OK

# Test via domain
curl https://your.domain.com/api/health/
# Expected: {"status":"ok"}

# Test in browser
open https://your.domain.com
open https://your.domain.com/admin
```

---

## 🔧 Common Tasks

### View Logs

```bash
# All services
docker compose logs -f

# Backend only
docker compose logs -f backend

# Last 100 lines
docker compose logs --tail=100 backend
```

### Restart Services

```bash
# All services
docker compose restart

# Single service
docker compose restart backend
```

### Update Application

```bash
cd /opt/apps/rims
git pull origin main
docker compose up -d --build
```

### Database Operations

```bash
# Backup
docker compose exec db pg_dump -U rims rims > backup_$(date +%Y%m%d).sql

# Restore
cat backup.sql | docker compose exec -T db psql -U rims rims

# Connect to database
docker compose exec db psql -U rims rims
```

### Django Management Commands

```bash
# Run migrations
docker compose exec backend python manage.py migrate

# Create superuser
docker compose exec backend python manage.py createsuperuser

# Django shell
docker compose exec backend python manage.py shell

# Collect static files (if needed manually)
docker compose exec backend python manage.py collectstatic --noinput
```

---

## 🐛 Troubleshooting

### Services Won't Start

```bash
# Check logs
docker compose logs

# Verify .env.prod
cat .env.prod

# Check disk space
df -h

# Check Docker
docker system df
```

### Database Connection Error

```bash
# Check database status
docker compose ps db

# Check database logs
docker compose logs db

# Test connection
docker compose exec backend python manage.py dbshell
```

### Frontend Not Loading

```bash
# Check nginx logs
docker compose logs frontend

# Verify build
docker compose exec frontend ls -la /usr/share/nginx/html

# Test directly
curl http://127.0.0.1:8081/
```

### Caddy SSL Issues

```bash
# Check Caddy logs
sudo journalctl -u caddy -f

# Verify DNS
dig your.domain.com

# Test without Caddy
curl http://127.0.0.1:8015/api/health/
curl http://127.0.0.1:8081/
```

---

## 📊 Monitoring

### Health Checks

```bash
# Backend
curl http://127.0.0.1:8015/api/health/

# Frontend
curl http://127.0.0.1:8081/healthz

# Via domain
curl https://your.domain.com/api/health/
```

### Resource Usage

```bash
# Docker stats
docker stats

# Service-specific
docker stats rims_backend_prod
docker stats rims_frontend_prod
docker stats rims_db_prod

# Disk usage
docker system df
```

### Log Monitoring

```bash
# Real-time logs
docker compose logs -f --tail=50

# Error logs only
docker compose logs | grep -i error

# Warning logs
docker compose logs | grep -i warning
```

---

## 🔒 Security

### After Deployment

1. **Restrict file permissions**:
   ```bash
   chmod 600 .env.prod
   ```

2. **Enable firewall**:
   ```bash
   sudo ufw allow 22/tcp
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw enable
   ```

3. **Setup SSH keys**:
   ```bash
   ssh-keygen -t ed25519
   # Copy public key to server
   # Disable password authentication
   ```

4. **Configure automatic updates**:
   ```bash
   sudo apt install unattended-upgrades
   sudo dpkg-reconfigure -plow unattended-upgrades
   ```

---

## 📚 Documentation

- **Full Guide**: README_PROD.md
- **Caddy Config**: CADDYFILE_SNIPPET.md
- **File Reference**: DEPLOYMENT_SUMMARY.md
- **Checklist**: PRODUCTION_DEPLOYMENT_CHECKLIST.md

---

## 🆘 Support

- **Repository**: https://github.com/munaimtahir/radreport
- **Issues**: https://github.com/munaimtahir/radreport/issues

---

## 📝 Notes

- **Default Ports**: Backend 8015, Frontend 8081, Database 5432
- **Data Persistence**: Postgres data, media files, and static files are persisted in Docker volumes
- **Logs**: Docker handles log rotation automatically
- **Updates**: Always backup before updating
- **Scaling**: Adjust Gunicorn workers in `scripts/entrypoint.sh` based on CPU cores

---

**Total Setup Time**: ~20-30 minutes  
**Difficulty**: Intermediate  
**Prerequisites**: Basic Linux, Docker, and DNS knowledge
