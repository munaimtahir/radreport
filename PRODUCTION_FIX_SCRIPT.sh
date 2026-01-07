#!/bin/bash
# Production Fix Script for RIMS
# Run this on the VPS: bash PRODUCTION_FIX_SCRIPT.sh
# This script fixes common production deployment issues

set -e

PROJECT_DIR="/home/munaim/srv/apps/radreport"
BACKEND_DIR="$PROJECT_DIR/backend"

echo "=========================================="
echo "RIMS Production Fix Script"
echo "=========================================="
echo "Project Directory: $PROJECT_DIR"
echo "Date: $(date)"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then 
    echo -e "${YELLOW}⚠ Running without sudo. Some commands may require sudo.${NC}"
    SUDO=""
else
    SUDO=""
fi

cd "$PROJECT_DIR" || exit 1

# ==========================================
# PHASE 1: Verify Code Integrity
# ==========================================
echo "=========================================="
echo "PHASE 1: Code Integrity Check"
echo "=========================================="

echo -n "[1.1] Checking git status... "
if [ -d ".git" ]; then
    echo -e "${GREEN}✓ Git repository found${NC}"
    echo "Current branch: $(git branch --show-current)"
    echo "Latest commit: $(git log -1 --oneline)"
    echo ""
    echo "Fetching latest from GitHub..."
    git fetch --all --prune
    echo ""
    echo "Git status:"
    git status -sb
else
    echo -e "${RED}✗ Not a git repository${NC}"
fi
echo ""

# ==========================================
# PHASE 2: Fix Static Files (Bucket B)
# ==========================================
echo "=========================================="
echo "PHASE 2: Fix Static Files"
echo "=========================================="

cd "$BACKEND_DIR" || exit 1

# Check if virtual environment exists
if [ -d "venv" ]; then
    source venv/bin/activate
    echo -e "${GREEN}✓ Virtual environment activated${NC}"
else
    echo -e "${RED}✗ Virtual environment not found at $BACKEND_DIR/venv${NC}"
    exit 1
fi

# Load environment variables
if [ -f ".env.production" ]; then
    echo -e "${GREEN}✓ Loading .env.production${NC}"
    set -a
    source .env.production
    set +a
else
    echo -e "${YELLOW}⚠ .env.production not found${NC}"
fi

echo ""
echo "[2.1] Collecting static files..."
python manage.py collectstatic --noinput || {
    echo -e "${RED}✗ collectstatic failed${NC}"
    exit 1
}
echo -e "${GREEN}✓ Static files collected${NC}"
echo ""

# Check static files directory
STATIC_ROOT=$(python -c "import os; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rims_backend.settings'); import django; django.setup(); from django.conf import settings; print(settings.STATIC_ROOT)")
if [ -d "$STATIC_ROOT" ]; then
    echo "Static files location: $STATIC_ROOT"
    echo "Files count: $(find "$STATIC_ROOT" -type f | wc -l)"
    echo -e "${GREEN}✓ Static files directory exists${NC}"
else
    echo -e "${RED}✗ Static files directory not found: $STATIC_ROOT${NC}"
fi
echo ""

# ==========================================
# PHASE 3: Verify Database & Migrations
# ==========================================
echo "=========================================="
echo "PHASE 3: Database & Migrations"
echo "=========================================="

echo "[3.1] Checking database connection..."
python manage.py check --database default || {
    echo -e "${RED}✗ Database connection failed${NC}"
    exit 1
}
echo -e "${GREEN}✓ Database connection OK${NC}"
echo ""

echo "[3.2] Checking migrations..."
python manage.py showmigrations --plan | tail -20
echo ""

echo "[3.3] Applying pending migrations..."
python manage.py migrate --noinput || {
    echo -e "${RED}✗ Migrations failed${NC}"
    exit 1
}
echo -e "${GREEN}✓ Migrations applied${NC}"
echo ""

# ==========================================
# PHASE 4: Verify Services
# ==========================================
echo "=========================================="
echo "PHASE 4: Service Status"
echo "=========================================="

echo "[4.1] Checking backend service..."
if systemctl is-active --quiet rims-backend; then
    echo -e "${GREEN}✓ rims-backend service is running${NC}"
    systemctl status rims-backend --no-pager -l | head -10
else
    echo -e "${RED}✗ rims-backend service is not running${NC}"
    echo "Attempting to start..."
    sudo systemctl start rims-backend || echo "Failed to start"
fi
echo ""

echo "[4.2] Checking nginx service..."
if systemctl is-active --quiet nginx; then
    echo -e "${GREEN}✓ nginx service is running${NC}"
else
    echo -e "${RED}✗ nginx service is not running${NC}"
fi
echo ""

echo "[4.3] Checking caddy service..."
if systemctl is-active --quiet caddy; then
    echo -e "${GREEN}✓ caddy service is running${NC}"
else
    echo -e "${RED}✗ caddy service is not running${NC}"
fi
echo ""

# ==========================================
# PHASE 5: Fix Caddy Configuration (if needed)
# ==========================================
echo "=========================================="
echo "PHASE 5: Caddy Configuration"
echo "=========================================="

echo "[5.1] Validating Caddyfile..."
if sudo caddy validate --config /etc/caddy/Caddyfile 2>&1; then
    echo -e "${GREEN}✓ Caddyfile is valid${NC}"
else
    echo -e "${RED}✗ Caddyfile validation failed${NC}"
fi
echo ""

echo "[5.2] Checking RIMS configuration in Caddyfile..."
if grep -q "rims.alshifalab.pk" /etc/caddy/Caddyfile; then
    echo -e "${GREEN}✓ RIMS configuration found in Caddyfile${NC}"
    echo "RIMS section:"
    grep -A 60 "rims.alshifalab.pk" /etc/caddy/Caddyfile | head -20
else
    echo -e "${RED}✗ RIMS configuration not found in Caddyfile${NC}"
fi
echo ""

# ==========================================
# PHASE 6: Test Local Connectivity
# ==========================================
echo "=========================================="
echo "PHASE 6: Local Connectivity Tests"
echo "=========================================="

echo "[6.1] Testing backend (127.0.0.1:8015)..."
if curl -s -f http://127.0.0.1:8015/api/health/ > /dev/null; then
    echo -e "${GREEN}✓ Backend responding${NC}"
else
    echo -e "${RED}✗ Backend not responding${NC}"
fi
echo ""

echo "[6.2] Testing frontend (127.0.0.1:8081)..."
if curl -s -f http://127.0.0.1:8081/ > /dev/null; then
    echo -e "${GREEN}✓ Frontend responding${NC}"
else
    echo -e "${RED}✗ Frontend not responding${NC}"
fi
echo ""

# ==========================================
# PHASE 7: Restart Services
# ==========================================
echo "=========================================="
echo "PHASE 7: Restart Services"
echo "=========================================="

echo "[7.1] Restarting backend service..."
sudo systemctl restart rims-backend || echo "Failed to restart"
sleep 2
if systemctl is-active --quiet rims-backend; then
    echo -e "${GREEN}✓ Backend restarted successfully${NC}"
else
    echo -e "${RED}✗ Backend failed to start${NC}"
fi
echo ""

echo "[7.2] Reloading nginx..."
sudo systemctl reload nginx || echo "Failed to reload"
echo -e "${GREEN}✓ Nginx reloaded${NC}"
echo ""

echo "[7.3] Reloading caddy..."
sudo systemctl reload caddy || echo "Failed to reload"
echo -e "${GREEN}✓ Caddy reloaded${NC}"
echo ""

# ==========================================
# Summary
# ==========================================
echo "=========================================="
echo "Fix Script Complete"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Run the smoke test: ./smoke_test_production.sh"
echo "2. Check logs if issues persist:"
echo "   - Backend: sudo journalctl -u rims-backend -n 50"
echo "   - Caddy: sudo tail -50 /home/munaim/srv/proxy/caddy/logs/caddy.log"
echo "   - Nginx: sudo tail -50 /var/log/nginx/error.log"
echo ""
