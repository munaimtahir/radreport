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

# Stop both services
echo "Stopping frontend and backend services..."
docker compose stop frontend backend || true

# Remove containers if they exist
echo "Removing containers..."
docker compose rm -f frontend backend || true

# Clear Docker build cache
echo "Clearing Docker build cache..."
docker builder prune -f || true

# Remove existing images to force rebuild
echo "Removing existing images..."
docker rmi $(docker images -q radreport-frontend 2>/dev/null) 2>/dev/null || true
docker rmi $(docker images -q radreport-backend 2>/dev/null) 2>/dev/null || true
docker rmi $(docker images -q rims_frontend_prod 2>/dev/null) 2>/dev/null || true
docker rmi $(docker images -q rims_backend_prod 2>/dev/null) 2>/dev/null || true
docker compose rmi -f frontend backend || true

# Rebuild both images without cache
echo "Rebuilding frontend and backend images (no cache)..."
docker compose build --no-cache frontend backend

# Start both services
echo "Starting frontend and backend services..."
docker compose up -d frontend backend

# Wait a moment for services to start
echo "Waiting for services to start..."
sleep 5

# Show logs
echo "=========================================="
echo "Frontend service logs (last 20 lines):"
echo "=========================================="
docker compose logs --tail=20 frontend

echo "=========================================="
echo "Backend service logs (last 30 lines):"
echo "=========================================="
docker compose logs --tail=30 backend

# Check service status
echo "=========================================="
echo "Full deployment complete!"
echo "Checking service status..."
docker compose ps frontend backend

echo "=========================================="
echo "Services are now running:"
echo "  Frontend: http://127.0.0.1:8081"
echo "  Backend:  http://127.0.0.1:8015"
echo "=========================================="
