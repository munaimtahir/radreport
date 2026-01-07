# RIMS Production Docker Deployment - Complete Summary

This document provides the complete file tree and contents of all production deployment files.

---

## File Tree

```
/opt/apps/rims/  (or your deployment directory)
├── .env.prod.example              # Environment template (no secrets)
├── .env.prod                      # Actual secrets (git-ignored, create from example)
├── .gitignore                     # Git ignore patterns
├── docker-compose.yml             # Production orchestration
├── README_PROD.md                 # Comprehensive deployment guide
├── CADDYFILE_SNIPPET.md          # Caddy configuration
├── DEPLOYMENT_SUMMARY.md          # This file
│
├── backend/
│   ├── Dockerfile                 # Backend production image
│   ├── requirements.txt           # Python dependencies (includes whitenoise)
│   ├── manage.py
│   ├── rims_backend/
│   │   ├── settings.py           # Updated with WhiteNoise
│   │   └── urls.py               # Updated for production static serving
│   └── apps/
│
├── frontend/
│   ├── Dockerfile                 # Frontend production image
│   ├── nginx.prod.conf           # Nginx configuration for container
│   ├── package.json
│   └── src/
│
└── scripts/
    ├── entrypoint.sh             # Backend startup script
    ├── validate-deployment.sh    # Pre-deployment validation
    └── test-deployment.sh        # Deployment testing script
```

---

## Complete File Contents

### 1. `.gitignore`

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
*.egg-info/
dist/
build/
*.egg
.venv/
venv/
ENV/
env/

# Django
*.log
db.sqlite3
db.sqlite3-journal
/backend/media/
/backend/staticfiles/
/backend/static/

# Node
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
/frontend/dist/
/frontend/.vite/

# Environment files
.env
.env.local
.env.*.local
.env.production

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Docker
*.pid
*.seed
*.log

# Build artifacts
*.tsbuildinfo
```

---

### 2. `.env.prod.example`

```bash
# ===========================================
# RIMS Production Environment Variables
# ===========================================
# Copy this file to .env.prod and fill in the values
# NEVER commit .env.prod with actual secrets

# ============================================
# Django Configuration
# ============================================
DJANGO_SECRET_KEY=CHANGE_ME_TO_RANDOM_50_CHAR_STRING
DJANGO_DEBUG=0
DJANGO_ALLOWED_HOSTS=rims.alshifalab.pk,rims.yourdomain.com
CORS_ALLOWED_ORIGINS=https://rims.alshifalab.pk,https://rims.yourdomain.com

# ============================================
# Database Configuration
# ============================================
DB_NAME=rims
DB_USER=rims
DB_PASSWORD=CHANGE_ME_TO_SECURE_PASSWORD
# Note: DB_HOST is set to 'db' in docker-compose.yml (service name)
# Note: DB_PORT is set to '5432' in docker-compose.yml (internal container port)

# ============================================
# Optional: Production Tuning
# ============================================
# GUNICORN_WORKERS=4
# GUNICORN_TIMEOUT=120
```

---

### 3. `docker-compose.yml`

```yaml
version: '3.8'

services:
  # PostgreSQL Database
  db:
    image: postgres:16-alpine
    container_name: rims_db_prod
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${DB_NAME:-rims}
      POSTGRES_USER: ${DB_USER:-rims}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - rims_network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-rims}"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Django Backend
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: rims_backend_prod
    restart: unless-stopped
    depends_on:
      db:
        condition: service_healthy
    environment:
      # Django settings
      DJANGO_SECRET_KEY: ${DJANGO_SECRET_KEY}
      DJANGO_DEBUG: "0"
      DJANGO_ALLOWED_HOSTS: ${DJANGO_ALLOWED_HOSTS}
      CORS_ALLOWED_ORIGINS: ${CORS_ALLOWED_ORIGINS}
      
      # Database settings
      DB_ENGINE: postgresql
      DB_NAME: ${DB_NAME:-rims}
      DB_USER: ${DB_USER:-rims}
      DB_PASSWORD: ${DB_PASSWORD}
      DB_HOST: db
      DB_PORT: "5432"
    volumes:
      # Persist media files
      - media_data:/app/media
      # Optionally mount staticfiles if serving via Caddy on host
      - static_data:/app/staticfiles
    ports:
      # Bind to localhost only for security (Caddy will reverse proxy)
      - "127.0.0.1:8015:8000"
    networks:
      - rims_network

  # React Frontend
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: rims_frontend_prod
    restart: unless-stopped
    ports:
      # Bind to localhost only (Caddy will reverse proxy)
      - "127.0.0.1:8081:80"
    networks:
      - rims_network

networks:
  rims_network:
    driver: bridge

volumes:
  postgres_data:
    driver: local
  media_data:
    driver: local
  static_data:
    driver: local
```

---

### 4. `backend/Dockerfile`

```dockerfile
# Multi-stage build for production Django backend
FROM python:3.11-slim as builder

# Install system dependencies for building Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create and activate virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install Python dependencies
COPY requirements.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# ============================================
# Production stage
FROM python:3.11-slim

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy application code
COPY . /app/

# Create necessary directories
RUN mkdir -p /app/media /app/staticfiles /app/static

# Collect static files during build
RUN python manage.py collectstatic --noinput

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port (internal only, not host-bound)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health/').read()" || exit 1

# Use entrypoint script for migrations and startup
ENTRYPOINT ["/app/scripts/entrypoint.sh"]
```

---

### 5. `frontend/Dockerfile`

```dockerfile
# Multi-stage build for production React frontend
FROM node:18-alpine as builder

WORKDIR /app

# Copy package files and install dependencies
COPY package*.json ./
RUN npm ci --only=production

# Copy source code and build
COPY . .
RUN npm run build

# ============================================
# Production stage with nginx
FROM nginx:1.25-alpine

# Copy custom nginx configuration
COPY nginx.prod.conf /etc/nginx/conf.d/default.conf

# Copy built assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose port (internal only)
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost/ || exit 1

# nginx runs as root by default but drops privileges
# No need to change user as nginx handles this internally
CMD ["nginx", "-g", "daemon off;"]
```

---

### 6. `frontend/nginx.prod.conf`

```nginx
server {
    listen 80;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml+rss application/json application/javascript;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # SPA routing - serve index.html for all routes
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Don't log favicon requests
    location = /favicon.ico {
        log_not_found off;
        access_log off;
    }

    # Health check endpoint
    location /healthz {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
```

---

### 7. `scripts/entrypoint.sh`

```bash
#!/bin/bash
set -e

echo "==> RIMS Backend Production Entrypoint"

# Wait for database to be ready
echo "==> Waiting for PostgreSQL..."
while ! pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" > /dev/null 2>&1; do
    echo "    PostgreSQL not ready, waiting..."
    sleep 2
done
echo "==> PostgreSQL is ready"

# Run database migrations
echo "==> Running database migrations..."
python manage.py migrate --noinput

# Create superuser if needed (optional, only for first deployment)
# Uncomment the following lines if you want to auto-create a superuser
# python manage.py shell << EOF
# from django.contrib.auth import get_user_model
# User = get_user_model()
# if not User.objects.filter(username='admin').exists():
#     User.objects.create_superuser('admin', 'admin@example.com', 'changeme')
#     print('Superuser created: admin/changeme')
# EOF

echo "==> Starting Gunicorn..."
# Bind to all interfaces inside container (Docker network isolation provides security)
exec gunicorn rims_backend.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info
```

---

### 8. `scripts/validate-deployment.sh`

```bash
#!/bin/bash
# Validation script for production Docker deployment
# Run this before deploying to production

set -e

echo "==================================="
echo "RIMS Production Deployment Validator"
echo "==================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

errors=0
warnings=0

# Check if running in project root
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}ERROR: docker-compose.yml not found. Run this script from project root.${NC}"
    exit 1
fi

echo "✓ Running from project root"
echo ""

# Check required files
echo "Checking required files..."
required_files=(
    "docker-compose.yml"
    "backend/Dockerfile"
    "backend/requirements.txt"
    "frontend/Dockerfile"
    "frontend/nginx.prod.conf"
    "scripts/entrypoint.sh"
    ".env.prod.example"
    "README_PROD.md"
)

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo -e "  ${GREEN}✓${NC} $file"
    else
        echo -e "  ${RED}✗${NC} $file - MISSING"
        ((errors++))
    fi
done
echo ""

# Check .env.prod exists
echo "Checking environment configuration..."
if [ -f ".env.prod" ]; then
    echo -e "  ${GREEN}✓${NC} .env.prod exists"
    
    # Check for placeholder values
    if grep -q "CHANGE_ME" .env.prod; then
        echo -e "  ${YELLOW}⚠${NC} .env.prod contains placeholder values (CHANGE_ME)"
        ((warnings++))
    fi
    
    # Check for required variables
    required_vars=("DJANGO_SECRET_KEY" "DB_PASSWORD" "DJANGO_ALLOWED_HOSTS")
    for var in "${required_vars[@]}"; do
        if grep -q "^${var}=" .env.prod; then
            echo -e "  ${GREEN}✓${NC} $var is set"
        else
            echo -e "  ${RED}✗${NC} $var is missing"
            ((errors++))
        fi
    done
else
    echo -e "  ${YELLOW}⚠${NC} .env.prod not found (copy from .env.prod.example)"
    ((warnings++))
fi
echo ""

# Check Docker
echo "Checking Docker installation..."
if command -v docker &> /dev/null; then
    docker_version=$(docker --version)
    echo -e "  ${GREEN}✓${NC} Docker installed: $docker_version"
else
    echo -e "  ${RED}✗${NC} Docker not found"
    ((errors++))
fi

if docker compose version &> /dev/null; then
    compose_version=$(docker compose version)
    echo -e "  ${GREEN}✓${NC} Docker Compose installed: $compose_version"
else
    echo -e "  ${RED}✗${NC} Docker Compose not found"
    ((errors++))
fi
echo ""

# Check entrypoint script is executable
echo "Checking script permissions..."
if [ -x "scripts/entrypoint.sh" ]; then
    echo -e "  ${GREEN}✓${NC} scripts/entrypoint.sh is executable"
else
    echo -e "  ${YELLOW}⚠${NC} scripts/entrypoint.sh is not executable (will be handled by Docker)"
    ((warnings++))
fi
echo ""

# Check for common issues in docker-compose.yml
echo "Validating docker-compose.yml..."
if grep -q "version:" docker-compose.yml; then
    echo -e "  ${GREEN}✓${NC} docker-compose.yml syntax appears valid"
else
    echo -e "  ${YELLOW}⚠${NC} docker-compose.yml may have syntax issues"
    ((warnings++))
fi

if grep -q "127.0.0.1:8015:8000" docker-compose.yml; then
    echo -e "  ${GREEN}✓${NC} Backend bound to localhost only (secure)"
else
    echo -e "  ${YELLOW}⚠${NC} Backend port binding not found or insecure"
    ((warnings++))
fi

if grep -q "127.0.0.1:8081:80" docker-compose.yml; then
    echo -e "  ${GREEN}✓${NC} Frontend bound to localhost only (secure)"
else
    echo -e "  ${YELLOW}⚠${NC} Frontend port binding not found or insecure"
    ((warnings++))
fi
echo ""

# Summary
echo "==================================="
echo "Validation Summary"
echo "==================================="
if [ $errors -eq 0 ] && [ $warnings -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed! Ready for deployment.${NC}"
    exit 0
elif [ $errors -eq 0 ]; then
    echo -e "${YELLOW}⚠ $warnings warning(s) found. Review before deployment.${NC}"
    exit 0
else
    echo -e "${RED}✗ $errors error(s) and $warnings warning(s) found. Fix errors before deployment.${NC}"
    exit 1
fi
```

---

## Deployment Commands

### Quick Start (Production VPS)

```bash
# 1. Clone repository
cd /opt/apps
git clone https://github.com/munaimtahir/radreport.git rims
cd rims

# 2. Create environment file
cp .env.prod.example .env.prod
nano .env.prod  # Edit with your actual values

# 3. Validate configuration
bash scripts/validate-deployment.sh

# 4. Build and start services
docker compose --env-file .env.prod up -d --build

# 5. Create superuser
docker compose exec backend python manage.py createsuperuser

# 6. Configure Caddy (see CADDYFILE_SNIPPET.md)
sudo nano /etc/caddy/Caddyfile
sudo systemctl reload caddy

# 7. Verify deployment
curl https://rims.alshifalab.pk/api/health/
```

### Maintenance Commands

```bash
# View logs
docker compose logs -f backend
docker compose logs -f frontend

# Restart services
docker compose restart backend

# Update application
git pull origin main
docker compose up -d --build

# Database backup
docker compose exec db pg_dump -U rims rims > backup_$(date +%Y%m%d).sql

# Database restore
cat backup_20260107.sql | docker compose exec -T db psql -U rims rims
```

---

## Verification Checklist

After deployment, verify:

- [ ] Backend health: `curl https://your.domain/api/health/`
- [ ] Frontend loads: `curl -I https://your.domain/`
- [ ] Django admin accessible: `https://your.domain/admin/`
- [ ] API docs accessible: `https://your.domain/api/docs/`
- [ ] Static files load correctly
- [ ] Media files upload/download works
- [ ] SSL/TLS certificate issued by Caddy
- [ ] Services auto-restart after reboot

---

## Security Notes

✓ **Implemented:**
- Services bound to 127.0.0.1 (localhost only)
- Non-root user in backend container
- DEBUG=False in production
- WhiteNoise for secure static file serving
- ALLOWED_HOSTS properly configured
- Health checks for all services
- Multi-stage Docker builds (smaller images)
- Secrets via environment variables (not in code)
- HTTPS via Caddy with automatic TLS

⚠ **Additional Recommendations:**
- Use strong passwords for DJANGO_SECRET_KEY and DB_PASSWORD
- Regularly update Docker images
- Set up automated backups
- Monitor logs for suspicious activity
- Consider using cloud storage (S3) for media files in high-traffic scenarios
- Implement rate limiting via Caddy or Django middleware

---

## Support

For issues or questions:
- Repository: https://github.com/munaimtahir/radreport
- See README_PROD.md for comprehensive troubleshooting guide
- Check CADDYFILE_SNIPPET.md for Caddy configuration help
