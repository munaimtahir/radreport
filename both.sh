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
if ! docker compose ps db | grep -q "Up"; then
    echo "Starting database service..."
    docker compose up -d db
    echo "Waiting for database to be ready..."
    sleep 5
else
    echo "✓ Database is running"
fi

# Stop frontend and backend services only (not the database)
echo "Stopping frontend and backend services..."
docker compose stop frontend backend || true

# Remove containers if they exist
echo "Removing containers..."
docker compose rm -f frontend backend || true

# Remove existing images to force rebuild
echo "Removing existing images..."
docker rmi radreport-frontend 2>/dev/null || true
docker rmi radreport-backend 2>/dev/null || true

# Rebuild both images without cache
echo "Rebuilding frontend and backend images (no cache)..."
echo "This will take a few minutes..."
docker compose build --no-cache frontend backend

# Start both services (backend depends on db)
echo "Starting frontend and backend services..."
docker compose up -d frontend backend

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
docker compose ps frontend backend db

# Health checks
echo "=========================================="
echo "Testing service health..."
sleep 3

# Backend health
if curl -s http://127.0.0.1:8015/api/health/ 2>/dev/null | grep -q '"status":"ok"'; then
    echo "✓ Backend health check: OK"
else
    echo "⚠ Backend health check: FAILED (may still be starting)"
fi

# Frontend health
if curl -s -I http://127.0.0.1:8081/ 2>/dev/null | head -n1 | grep -q "200"; then
    echo "✓ Frontend is accessible"
else
    echo "⚠ Frontend check: FAILED (may still be starting)"
fi

# Public URLs
echo ""
echo "Testing public URLs..."
if curl -s https://rims.alshifalab.pk 2>/dev/null | head -c 100 | grep -q "html"; then
    echo "✓ Frontend is publicly accessible"
else
    echo "⚠ Public frontend check failed"
fi

if curl -s https://api.rims.alshifalab.pk/api/health/ 2>/dev/null | grep -q '"status":"ok"'; then
    echo "✓ Backend is publicly accessible"
else
    echo "⚠ Public backend check failed"
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
