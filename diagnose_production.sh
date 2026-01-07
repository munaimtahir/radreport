#!/bin/bash
# Production Diagnostic Script for RIMS
# Run this on the VPS: bash diagnose_production.sh

set -e

echo "=========================================="
echo "PHASE 0: System Information"
echo "=========================================="
echo ""
echo "--- User and System ---"
whoami
hostnamectl
date
echo ""

echo "--- Project Directory ---"
PROJECT_DIR="/home/munaim/srv/apps/radreport"
if [ -d "$PROJECT_DIR" ]; then
    echo "Found project at: $PROJECT_DIR"
    ls -la "$PROJECT_DIR" | head -20
else
    echo "⚠ Project directory not found at $PROJECT_DIR"
    echo "Searching common locations..."
    for dir in /srv /opt /var/www /home; do
        if [ -d "$dir" ]; then
            echo "Checking $dir..."
            find "$dir" -name "radreport" -type d 2>/dev/null | head -5
        fi
    done
fi
echo ""

echo "--- Active Processes (Top 10 by memory) ---"
ps aux --sort=-%mem | head -11
echo ""

echo "--- Listening Ports ---"
ss -lntp | grep -E ':(80|443|8015|8081|5434|6381)' || echo "No matching ports found"
echo ""

echo "--- Running Services ---"
systemctl list-units --type=service --state=running | grep -E '(rims|caddy|nginx|postgres)' | head -20
echo ""

echo "--- Docker Containers ---"
docker ps 2>/dev/null || echo "Docker not available or not running"
docker compose ps 2>/dev/null || echo "Docker Compose not available"
echo ""

echo "=========================================="
echo "PHASE 1: Code Integrity Check"
echo "=========================================="
if [ -d "$PROJECT_DIR" ]; then
    cd "$PROJECT_DIR"
    echo "--- Git Remote ---"
    git remote -v 2>/dev/null || echo "Not a git repository"
    echo ""
    
    echo "--- Git Status ---"
    git status 2>/dev/null || echo "Git status failed"
    echo ""
    
    echo "--- Current Branch ---"
    git branch --show-current 2>/dev/null || echo "Could not determine branch"
    echo ""
    
    echo "--- Latest Commit ---"
    git log -1 --oneline 2>/dev/null || echo "Could not get commit info"
    echo ""
    
    echo "--- Fetch and Compare ---"
    git fetch --all --prune 2>/dev/null || echo "Git fetch failed"
    git status -sb 2>/dev/null || echo "Git status failed"
    echo ""
else
    echo "⚠ Cannot check git - project directory not found"
fi
echo ""

echo "=========================================="
echo "PHASE 1: Environment Files Check"
echo "=========================================="
if [ -d "$PROJECT_DIR/backend" ]; then
    echo "--- Environment Files (names only, no secrets) ---"
    find "$PROJECT_DIR/backend" -name ".env*" -o -name "*.env" 2>/dev/null | while read f; do
        echo "Found: $f"
        echo "Variables: $(grep -E '^[A-Z_]+=' "$f" 2>/dev/null | cut -d'=' -f1 | tr '\n' ' ' || echo 'N/A')"
    done
    echo ""
    
    echo "--- Settings Files ---"
    find "$PROJECT_DIR/backend" -name "settings.py" 2>/dev/null | head -3
    echo ""
fi
echo ""

echo "=========================================="
echo "PHASE 0: Service Logs (Last 50 lines)"
echo "=========================================="
echo "--- RIMS Backend Service ---"
journalctl -u rims-backend -n 50 --no-pager 2>/dev/null || echo "Service not found or no logs"
echo ""

echo "--- Caddy Service ---"
journalctl -u caddy -n 50 --no-pager 2>/dev/null || echo "Service not found or no logs"
echo ""

echo "--- Nginx Service ---"
journalctl -u nginx -n 50 --no-pager 2>/dev/null || echo "Service not found or no logs"
tail -50 /var/log/nginx/error.log 2>/dev/null || echo "Nginx error log not accessible"
echo ""

echo "--- Docker Logs (if applicable) ---"
docker logs --tail=50 backend-db-1 2>/dev/null || echo "Database container not found"
echo ""

echo "=========================================="
echo "PHASE 0: Caddy Configuration"
echo "=========================================="
echo "--- Caddy Version ---"
caddy version 2>/dev/null || echo "Caddy not found"
echo ""

echo "--- Caddyfile Validation ---"
caddy validate --config /etc/caddy/Caddyfile 2>&1 || echo "Validation failed"
echo ""

echo "--- Caddyfile Content (RIMS section) ---"
grep -A 60 "rims.alshifalab.pk" /etc/caddy/Caddyfile 2>/dev/null || echo "RIMS section not found in Caddyfile"
echo ""

echo "=========================================="
echo "PHASE 0: Local Connectivity Tests"
echo "=========================================="
echo "--- Backend (127.0.0.1:8015) ---"
curl -I http://127.0.0.1:8015/api/health/ 2>&1 | head -5 || echo "Backend not responding"
echo ""

echo "--- Frontend (127.0.0.1:8081) ---"
curl -I http://127.0.0.1:8081/ 2>&1 | head -5 || echo "Frontend not responding"
echo ""

echo "--- Database Connection Test ---"
if command -v psql &> /dev/null; then
    PGPASSWORD=rims psql -h 127.0.0.1 -p 5434 -U rims -d rims -c "SELECT version();" 2>&1 | head -3 || echo "Database connection failed"
else
    echo "psql not available, trying docker exec..."
    docker exec backend-db-1 psql -U rims -d rims -c "SELECT version();" 2>&1 | head -3 || echo "Database check failed"
fi
echo ""

echo "=========================================="
echo "Diagnostic Complete"
echo "=========================================="
