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

# Stop the backend service
echo "Stopping backend service..."
docker compose stop backend || true

# Remove the backend container if it exists
echo "Removing backend container..."
docker compose rm -f backend || true

# Clear Docker build cache for backend
echo "Clearing Docker build cache for backend..."
docker builder prune -f --filter "label=service=backend" || true

# Remove the backend image to force rebuild
echo "Removing existing backend image..."
docker rmi $(docker images -q radreport-backend 2>/dev/null) 2>/dev/null || true
docker rmi $(docker images -q rims_backend_prod 2>/dev/null) 2>/dev/null || true
docker compose rmi -f backend || true

# Rebuild the backend image without cache
echo "Rebuilding backend image (no cache)..."
docker compose build --no-cache backend

# Start the backend service
echo "Starting backend service..."
docker compose up -d backend

# Wait a moment for the service to start
sleep 5

# Show logs
echo "=========================================="
echo "Backend service logs (last 30 lines):"
echo "=========================================="
docker compose logs --tail=30 backend

# Check service status
echo "=========================================="
echo "Backend deployment complete!"
echo "Checking service status..."
docker compose ps backend

echo "=========================================="
echo "Backend is now running on http://127.0.0.1:8015"
echo "=========================================="
