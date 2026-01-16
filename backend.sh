#!/bin/bash

# Backend deployment script
# Rebuilds and redeploys only the backend service
# Ensures database stays running and superuser credentials are available

set -e  # Exit on error

echo "=========================================="
echo "Backend Deployment Script"
echo "=========================================="

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if .env file exists
if [ ! -f .env ]; then
    echo "ERROR: .env file not found!"
    echo "Please create .env file with required environment variables."
    exit 1
fi

# Set explicit project name to ensure we only affect radreport
COMPOSE_PROJECT_NAME="radreport"

# Ensure database is running (don't stop it)
echo "Checking database service..."
if ! docker compose -p "$COMPOSE_PROJECT_NAME" ps db | grep -q "Up"; then
    echo "Starting database service..."
    docker compose -p "$COMPOSE_PROJECT_NAME" up -d db
    echo "Waiting for database to be ready..."
    sleep 5
fi

# Stop the backend service only (not the database)
echo "Stopping backend service (radreport project only)..."
docker compose -p "$COMPOSE_PROJECT_NAME" stop backend || true

# Remove the backend container if it exists
echo "Removing backend container..."
docker compose -p "$COMPOSE_PROJECT_NAME" rm -f backend || true

# Remove the backend image to force rebuild
echo "Removing existing backend image..."
docker compose -p "$COMPOSE_PROJECT_NAME" rmi -f backend || true
# Also remove by container name pattern specific to radreport
docker rmi $(docker images -q --filter "reference=radreport-backend" 2>/dev/null) 2>/dev/null || true
docker rmi $(docker images -q --filter "reference=*rims_backend_prod*" 2>/dev/null) 2>/dev/null || true

# Rebuild the backend image without cache
echo "Rebuilding backend image (no cache)..."
docker compose -p "$COMPOSE_PROJECT_NAME" build --no-cache backend

# Start the backend service (depends on db)
echo "Starting backend service..."
docker compose -p "$COMPOSE_PROJECT_NAME" up -d backend

# Wait for backend to start and run migrations
echo "Waiting for backend to initialize (migrations, superuser creation)..."
sleep 10

# Show logs to verify superuser creation
echo "=========================================="
echo "Backend service logs (last 40 lines):"
echo "=========================================="
docker compose -p "$COMPOSE_PROJECT_NAME" logs --tail=40 backend

# Verify superuser was created
echo "=========================================="
echo "Verifying superuser credentials..."
echo "=========================================="
if docker compose -p "$COMPOSE_PROJECT_NAME" logs backend | grep -q "Created superuser: admin / admin123"; then
    echo "✓ Superuser credentials verified: admin / admin123"
else
    echo "⚠ Warning: Could not verify superuser creation in logs"
    echo "  Superuser should be: admin / admin123"
fi

# Check service status
echo "=========================================="
echo "Backend deployment complete!"
echo "Checking service status..."
docker compose -p "$COMPOSE_PROJECT_NAME" ps backend db

# Health check
echo "=========================================="
echo "Testing backend health endpoint..."
if curl -s -f http://127.0.0.1:8015/api/health/ > /dev/null; then
    echo "✓ Backend health check: OK"
else
    echo "⚠ Backend health check: FAILED (may still be starting)"
fi

echo "=========================================="
echo "Backend is now running on http://127.0.0.1:8015"
echo "API accessible via: https://api.rims.alshifalab.pk"
echo "Superuser: admin / admin123"
echo "=========================================="
