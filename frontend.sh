#!/bin/bash

# Frontend deployment script
# Rebuilds and redeploys only the frontend service
# Usage: ./frontend.sh

set -e  # Exit on error

echo "=========================================="
echo "Frontend Deployment Script"
echo "=========================================="
echo "Use this script when you fix frontend issues"
echo "Location: /home/munaim/srv/apps/radreport"
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

# Remove the frontend image to force rebuild
echo "Removing existing frontend image..."
docker rmi radreport-frontend 2>/dev/null || true

# Rebuild the frontend image without cache
echo "Rebuilding frontend image (no cache)..."
docker compose build --no-cache frontend

# Start the frontend service
echo "Starting frontend service..."
docker compose up -d frontend

# Wait a moment for the service to start
echo "Waiting for frontend to start..."
sleep 5

# Show logs
echo "=========================================="
echo "Frontend service logs (last 30 lines):"
echo "=========================================="
docker compose logs --tail=30 frontend

# Check service status
echo "=========================================="
echo "Frontend deployment complete!"
echo "Checking service status..."
docker compose ps frontend

# Health check
echo "=========================================="
echo "Testing frontend accessibility..."
sleep 2
if curl -s -I http://127.0.0.1:8081/ 2>/dev/null | head -n1 | grep -q "200"; then
    echo "✓ Frontend is accessible on localhost"
else
    echo "⚠ Frontend localhost check failed (may still be starting)"
fi

echo ""
echo "Testing public URL..."
if curl -s -I https://rims.alshifalab.pk 2>/dev/null | head -n1 | grep -q "200"; then
    echo "✓ Frontend is publicly accessible"
else
    echo "⚠ Public URL check failed (Caddy may need reload)"
fi

echo "=========================================="
echo "✅ Frontend Deployment Complete!"
echo "=========================================="
echo "Local URL:  http://127.0.0.1:8081"
echo "Public URL: https://rims.alshifalab.pk"
echo ""
echo "💡 Tips:"
echo "  - Clear browser cache (Ctrl+Shift+R)"
echo "  - Check logs: docker compose logs -f frontend"
echo "  - View status: docker compose ps"
echo "=========================================="
