#!/bin/bash

# Backend deployment script
# Rebuilds and redeploys only the backend service

set -e  # Exit on error

echo "=========================================="
echo "Backend Deployment Script"
echo "=========================================="

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Set explicit project name to ensure we only affect radreport
COMPOSE_PROJECT_NAME="radreport"

# Stop the backend service
echo "Stopping backend service (radreport project only)..."
docker compose -p "$COMPOSE_PROJECT_NAME" stop backend || true

# Remove the backend container if it exists
echo "Removing backend container..."
docker compose -p "$COMPOSE_PROJECT_NAME" rm -f backend || true

# Remove the backend image to force rebuild (scoped to radreport project)
echo "Removing existing backend image..."
docker compose -p "$COMPOSE_PROJECT_NAME" rmi -f backend || true
# Also remove by container name pattern specific to radreport
docker rmi $(docker images -q --filter "reference=radreport*backend*" 2>/dev/null) 2>/dev/null || true
docker rmi $(docker images -q --filter "reference=*rims_backend_prod*" 2>/dev/null) 2>/dev/null || true

# Rebuild the backend image without cache
echo "Rebuilding backend image (no cache)..."
docker compose -p "$COMPOSE_PROJECT_NAME" build --no-cache backend

# Start the backend service
echo "Starting backend service..."
docker compose -p "$COMPOSE_PROJECT_NAME" up -d backend

# Wait a moment for the service to start
sleep 5

# Show logs
echo "=========================================="
echo "Backend service logs (last 30 lines):"
echo "=========================================="
docker compose -p "$COMPOSE_PROJECT_NAME" logs --tail=30 backend

# Check service status
echo "=========================================="
echo "Backend deployment complete!"
echo "Checking service status..."
docker compose -p "$COMPOSE_PROJECT_NAME" ps backend

echo "=========================================="
echo "Backend is now running on http://127.0.0.1:8015"
echo "=========================================="
