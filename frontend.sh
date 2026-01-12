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

# Stop the frontend service
echo "Stopping frontend service..."
docker compose stop frontend || true

# Remove the frontend container if it exists
echo "Removing frontend container..."
docker compose rm -f frontend || true

# Clear Docker build cache for frontend
echo "Clearing Docker build cache for frontend..."
docker builder prune -f --filter "label=service=frontend" || true

# Remove the frontend image to force rebuild
echo "Removing existing frontend image..."
docker rmi $(docker images -q radreport-frontend 2>/dev/null) 2>/dev/null || true
docker rmi $(docker images -q rims_frontend_prod 2>/dev/null) 2>/dev/null || true
docker compose rmi -f frontend || true

# Rebuild the frontend image without cache
echo "Rebuilding frontend image (no cache)..."
docker compose build --no-cache frontend

# Start the frontend service
echo "Starting frontend service..."
docker compose up -d frontend

# Wait a moment for the service to start
sleep 3

# Show logs
echo "=========================================="
echo "Frontend service logs (last 20 lines):"
echo "=========================================="
docker compose logs --tail=20 frontend

# Check service status
echo "=========================================="
echo "Frontend deployment complete!"
echo "Checking service status..."
docker compose ps frontend

echo "=========================================="
echo "Frontend is now running on http://127.0.0.1:8081"
echo "=========================================="
