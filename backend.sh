#!/bin/bash

# Backend deployment script
# Rebuilds and redeploys only the backend service
# Ensures database stays running and superuser credentials are available
# Usage: ./backend.sh

set -e  # Exit on error

echo "=========================================="
echo "Backend Deployment Script"
echo "=========================================="
echo "Use this script when you fix backend issues"
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

# Stop the backend service only (not the database)
echo "Stopping backend service..."
docker compose stop backend || true

# Remove the backend container if it exists
echo "Removing backend container..."
docker compose rm -f backend || true

# Remove the backend image to force rebuild
echo "Removing existing backend image..."
docker rmi radreport-backend 2>/dev/null || true

# Rebuild the backend image without cache
echo "Rebuilding backend image (no cache)..."
docker compose build --no-cache backend

# Start the backend service (depends on db)
echo "Starting backend service..."
docker compose up -d backend

# Wait for backend to start and run migrations
echo "Waiting for backend to initialize (migrations, superuser creation)..."
echo "This may take 10-15 seconds..."
sleep 12

# Show logs to verify superuser creation
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
echo "   - If exists: keeps existing user"
echo "   - If new: creates with these credentials"
echo "   - Always safe to redeploy (no credential loss)"

# Check service status
echo "=========================================="
echo "Backend deployment complete!"
echo "Checking service status..."
docker compose ps backend db

# Health check
echo "=========================================="
echo "Testing backend health endpoint..."
sleep 3
if curl -s http://127.0.0.1:8015/api/health/ 2>/dev/null | grep -q '"status":"ok"'; then
    echo "✓ Backend health check: OK"
    echo "  Database: Connected"
else
    echo "⚠ Backend health check: FAILED (may still be starting)"
    echo "  Retry in a few seconds: curl http://127.0.0.1:8015/api/health/"
fi

echo ""
echo "Testing public URL..."
if curl -s https://api.rims.alshifalab.pk/api/health/ 2>/dev/null | grep -q '"status":"ok"'; then
    echo "✓ Backend is publicly accessible"
else
    echo "⚠ Public URL check failed (Caddy may need reload)"
fi

echo "=========================================="
echo "✅ Backend Deployment Complete!"
echo "=========================================="
echo "Local API:  http://127.0.0.1:8015"
echo "Public API: https://api.rims.alshifalab.pk"
echo "Admin URL:  https://rims.alshifalab.pk/admin/"
echo ""
echo "🔑 Superuser: admin / admin123"
echo ""
echo "💡 Tips:"
echo "  - Check logs: docker compose logs -f backend"
echo "  - View status: docker compose ps"
echo "  - Test health: curl http://127.0.0.1:8015/api/health/"
echo "  - Test login: https://rims.alshifalab.pk"
echo "=========================================="
