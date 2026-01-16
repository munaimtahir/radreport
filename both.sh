#!/bin/bash

# Full deployment script
# Rebuilds and redeploys both frontend and backend services
# Ensures database stays running and superuser credentials are available

set -e  # Exit on error

echo "=========================================="
echo "Full Application Deployment Script"
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

# Stop frontend and backend services only (not the database)
echo "Stopping frontend and backend services (radreport project only)..."
docker compose -p "$COMPOSE_PROJECT_NAME" stop frontend backend || true

# Remove containers if they exist
echo "Removing containers..."
docker compose -p "$COMPOSE_PROJECT_NAME" rm -f frontend backend || true

# Remove existing images to force rebuild
echo "Removing existing images..."
docker compose -p "$COMPOSE_PROJECT_NAME" rmi -f frontend backend || true
# Also remove by container name patterns specific to radreport
docker rmi $(docker images -q --filter "reference=radreport-frontend" 2>/dev/null) 2>/dev/null || true
docker rmi $(docker images -q --filter "reference=radreport-backend" 2>/dev/null) 2>/dev/null || true
docker rmi $(docker images -q --filter "reference=*rims_frontend_prod*" 2>/dev/null) 2>/dev/null || true
docker rmi $(docker images -q --filter "reference=*rims_backend_prod*" 2>/dev/null) 2>/dev/null || true

# Rebuild both images without cache
echo "Rebuilding frontend and backend images (no cache)..."
docker compose -p "$COMPOSE_PROJECT_NAME" build --no-cache frontend backend

# Start both services (backend depends on db)
echo "Starting frontend and backend services..."
docker compose -p "$COMPOSE_PROJECT_NAME" up -d frontend backend

# Wait for services to start and backend to run migrations
echo "Waiting for services to initialize..."
echo "  - Backend migrations and superuser creation..."
sleep 10

# Show logs
echo "=========================================="
echo "Frontend service logs (last 20 lines):"
echo "=========================================="
docker compose -p "$COMPOSE_PROJECT_NAME" logs --tail=20 frontend

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
echo "Full deployment complete!"
echo "Checking service status..."
docker compose -p "$COMPOSE_PROJECT_NAME" ps frontend backend db

# Health checks
echo "=========================================="
echo "Testing service health..."
if curl -s -f http://127.0.0.1:8015/api/health/ > /dev/null; then
    echo "✓ Backend health check: OK"
else
    echo "⚠ Backend health check: FAILED (may still be starting)"
fi

if curl -s -f -I http://127.0.0.1:8081/ | grep -q "HTTP"; then
    echo "✓ Frontend is accessible"
else
    echo "⚠ Frontend may still be starting..."
fi

echo "=========================================="
echo "Services are now running:"
echo "  Frontend: http://127.0.0.1:8081"
echo "            https://rims.alshifalab.pk"
echo "  Backend:  http://127.0.0.1:8015"
echo "            https://api.rims.alshifalab.pk"
echo ""
echo "Superuser credentials: admin / admin123"
echo "=========================================="
