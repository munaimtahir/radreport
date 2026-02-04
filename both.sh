#!/bin/bash

# Full deployment script
# Rebuilds and redeploys both frontend and backend services
# Ensures database stays running and superuser credentials are available
# Usage: ./both.sh

set -e  # Exit on error

echo "=========================================="
echo "Full Application Deployment Script"
echo "=========================================="
echo "Use this script when you fix issues in both"
echo "frontend and backend, or for full rebuild"
echo "Location: /home/munaim/srv/apps/radreport"
echo "=========================================="

wait_for_health () {
    # Poll an HTTP endpoint until it returns expected content or timeout
    local url="$1"
    local expected="$2"
    local attempts="${3:-12}"
    local sleep_secs="${4:-5}"

    for i in $(seq 1 "$attempts"); do
        if curl -s --max-time 5 "$url" 2>/dev/null | grep -Eiq -- "$expected"; then
            echo "✓ OK after $i attempt(s): $url"
            return 0
        fi
        echo "… waiting for $url ($i/$attempts)"
        sleep "$sleep_secs"
    done

    echo "⚠ Timeout waiting for $url"
    return 1
}

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ ERROR: .env file not found!"
    echo "Please create .env file with required environment variables."
    exit 1
fi

# Ensure database is running (don't stop it)
echo "Checking database service..."
if ! docker compose -f docker-compose.yml ps db | grep -q "Up"; then
    echo "Starting database service..."
    docker compose -f docker-compose.yml up -d db
    echo "Waiting for database to be ready..."
    sleep 5
else
    echo "✓ Database is running"
fi

# Stop frontend and backend services only (not the database)
echo "Stopping frontend and backend services..."
docker compose -f docker-compose.yml stop frontend backend || true

# Remove containers if they exist
echo "Removing containers..."
docker compose -f docker-compose.yml rm -f frontend backend || true

# Remove existing images to force rebuild
echo "Removing existing images..."
docker rmi radreport-frontend 2>/dev/null || true
docker rmi radreport-backend 2>/dev/null || true

# Rebuild both images without cache
echo "Rebuilding frontend and backend images (no cache)..."
echo "This will take a few minutes..."
docker compose -f docker-compose.yml build --no-cache frontend backend

# Start both services (backend depends on db)
echo "Starting frontend and backend services..."
docker compose -f docker-compose.yml up -d frontend backend

# Wait for services to start and backend to run migrations
echo "Waiting for services to initialize..."
echo "  - Backend migrations and superuser creation..."
echo "  - Frontend Nginx startup..."
sleep 12

# Show logs
echo "=========================================="
echo "Frontend service logs (last 25 lines):"
echo "=========================================="
docker compose logs --tail=25 frontend

echo ""
echo "=========================================="
echo "Backend service logs (last 50 lines):"
echo "=========================================="
docker compose logs --tail=50 backend

# Verify superuser was created
echo "=========================================="
echo "Verifying superuser credentials..."
echo "=========================================="
if docker compose logs backend | grep -q "admin / admin123"; then
    echo "✓ Superuser credentials verified: admin / admin123"
elif docker compose logs backend | grep -q "Superuser 'admin' already exists"; then
    echo "✓ Superuser exists: admin / admin123"
elif docker compose logs backend | grep -q "Superuser exists: admin"; then
    echo "✓ Superuser exists: admin / admin123"
else
    echo "ℹ️  Superuser credentials: admin / admin123"
    echo "   (created automatically or preserved from previous)"
fi

echo ""
echo "💡 Superuser Info:"
echo "   The backend automatically creates/preserves superuser"
echo "   Username: admin"
echo "   Password: admin123"
echo "   - If exists: keeps existing user and password"
echo "   - If new: creates with these credentials"
echo "   - Always safe to redeploy (no credential loss)"

# Check service status
echo "=========================================="
echo "Full deployment complete!"
echo "Checking service status..."
docker compose -f docker-compose.yml ps frontend backend db

# Health checks
echo "=========================================="
echo "Testing service health..."
sleep 3

# Backend health (retry to avoid false negatives during boot)
if wait_for_health "http://127.0.0.1:8015/api/health/" '"status"[[:space:]]*:[[:space:]]*"ok"' 12 5; then
    echo "✓ Backend health check: OK"
else
    echo "⚠ Backend health check: FAILED after retries"
fi

# Frontend health
if wait_for_health "http://127.0.0.1:8081/" "<!doctype html>" 12 5; then
    echo "✓ Frontend is accessible"
else
    echo "⚠ Frontend check: FAILED after retries"
fi

# Public URLs
echo ""
echo "Testing public URLs..."
if wait_for_health "https://rims.alshifalab.pk" "html" 12 5; then
    echo "✓ Frontend is publicly accessible"
else
    echo "⚠ Public frontend check failed after retries"
fi

if wait_for_health "https://api.rims.alshifalab.pk/api/health/" '"status"[[:space:]]*:[[:space:]]*"ok"' 12 5; then
    echo "✓ Backend is publicly accessible"
else
    echo "⚠ Public backend check failed after retries"
fi

echo "=========================================="
echo "✅ Full Deployment Complete!"
echo "=========================================="
echo "Frontend URLs:"
echo "  Local:  http://127.0.0.1:8081"
echo "  Public: https://rims.alshifalab.pk"
echo ""
echo "Backend URLs:"
echo "  Local:  http://127.0.0.1:8015"
echo "  Public: https://api.rims.alshifalab.pk"
echo "  Admin:  https://rims.alshifalab.pk/admin/"
echo ""
echo "🔑 Superuser: admin / admin123"
echo ""
echo "💡 Tips:"
echo "  - Clear browser cache (Ctrl+Shift+R)"
echo "  - Check logs: docker compose logs -f"
echo "  - View status: docker compose ps"
echo "  - Test health: curl http://127.0.0.1:8015/api/health/"
echo "=========================================="
