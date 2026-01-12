#!/bin/bash

# Full deployment script
# Rebuilds and redeploys both frontend and backend services

set -e  # Exit on error

echo "=========================================="
echo "Full Application Deployment Script"
echo "=========================================="

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Set explicit project name to ensure we only affect radreport
COMPOSE_PROJECT_NAME="radreport"

# Stop both services
echo "Stopping frontend and backend services (radreport project only)..."
docker compose -p "$COMPOSE_PROJECT_NAME" stop frontend backend || true

# Remove containers if they exist
echo "Removing containers..."
docker compose -p "$COMPOSE_PROJECT_NAME" rm -f frontend backend || true

# Remove existing images to force rebuild (scoped to radreport project)
echo "Removing existing images..."
docker compose -p "$COMPOSE_PROJECT_NAME" rmi -f frontend backend || true
# Also remove by container name patterns specific to radreport
docker rmi $(docker images -q --filter "reference=radreport*frontend*" 2>/dev/null) 2>/dev/null || true
docker rmi $(docker images -q --filter "reference=radreport*backend*" 2>/dev/null) 2>/dev/null || true
docker rmi $(docker images -q --filter "reference=*rims_frontend_prod*" 2>/dev/null) 2>/dev/null || true
docker rmi $(docker images -q --filter "reference=*rims_backend_prod*" 2>/dev/null) 2>/dev/null || true

# Rebuild both images without cache
echo "Rebuilding frontend and backend images (no cache)..."
docker compose -p "$COMPOSE_PROJECT_NAME" build --no-cache frontend backend

# Start both services
echo "Starting frontend and backend services..."
docker compose -p "$COMPOSE_PROJECT_NAME" up -d frontend backend

# Wait a moment for services to start
echo "Waiting for services to start..."
sleep 5

# Show logs
echo "=========================================="
echo "Frontend service logs (last 20 lines):"
echo "=========================================="
docker compose -p "$COMPOSE_PROJECT_NAME" logs --tail=20 frontend

echo "=========================================="
echo "Backend service logs (last 30 lines):"
echo "=========================================="
docker compose -p "$COMPOSE_PROJECT_NAME" logs --tail=30 backend

# Check service status
echo "=========================================="
echo "Full deployment complete!"
echo "Checking service status..."
docker compose -p "$COMPOSE_PROJECT_NAME" ps frontend backend

echo "=========================================="
echo "Services are now running:"
echo "  Frontend: http://127.0.0.1:8081"
echo "  Backend:  http://127.0.0.1:8015"
echo "=========================================="
