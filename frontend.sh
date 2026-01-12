#!/bin/bash

# Frontend deployment script
# Rebuilds and redeploys only the frontend service

set -e  # Exit on error

echo "=========================================="
echo "Frontend Deployment Script"
echo "=========================================="

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Set explicit project name to ensure we only affect radreport
COMPOSE_PROJECT_NAME="radreport"

# Stop the frontend service
echo "Stopping frontend service (radreport project only)..."
docker compose -p "$COMPOSE_PROJECT_NAME" stop frontend || true

# Remove the frontend container if it exists
echo "Removing frontend container..."
docker compose -p "$COMPOSE_PROJECT_NAME" rm -f frontend || true

# Remove the frontend image to force rebuild (scoped to radreport project)
echo "Removing existing frontend image..."
docker compose -p "$COMPOSE_PROJECT_NAME" rmi -f frontend || true
# Also remove by container name pattern specific to radreport
docker rmi $(docker images -q --filter "reference=radreport*frontend*" 2>/dev/null) 2>/dev/null || true
docker rmi $(docker images -q --filter "reference=*rims_frontend_prod*" 2>/dev/null) 2>/dev/null || true

# Rebuild the frontend image without cache
echo "Rebuilding frontend image (no cache)..."
docker compose -p "$COMPOSE_PROJECT_NAME" build --no-cache frontend

# Start the frontend service
echo "Starting frontend service..."
docker compose -p "$COMPOSE_PROJECT_NAME" up -d frontend

# Wait a moment for the service to start
sleep 3

# Show logs
echo "=========================================="
echo "Frontend service logs (last 20 lines):"
echo "=========================================="
docker compose -p "$COMPOSE_PROJECT_NAME" logs --tail=20 frontend

# Check service status
echo "=========================================="
echo "Frontend deployment complete!"
echo "Checking service status..."
docker compose -p "$COMPOSE_PROJECT_NAME" ps frontend

echo "=========================================="
echo "Frontend is now running on http://127.0.0.1:8081"
echo "=========================================="
