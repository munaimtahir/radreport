#!/bin/bash
# Quick deployment test script
# Tests that services can be built and started (without full deployment)

set -e

echo "==================================="
echo "RIMS Deployment Test"
echo "==================================="
echo ""

# Check if .env.prod exists
if [ ! -f ".env.prod" ]; then
    echo "ERROR: .env.prod not found. Copy from .env.prod.example"
    exit 1
fi

echo "Step 1: Validating configuration..."
if [ ! -x "scripts/validate-deployment.sh" ]; then
    chmod +x scripts/validate-deployment.sh
fi
bash scripts/validate-deployment.sh
echo ""

echo "Step 2: Building images..."
echo "  Building backend..."
docker compose --env-file .env.prod build backend
echo "  Building frontend..."
docker compose --env-file .env.prod build frontend
echo ""

echo "Step 3: Starting services..."
docker compose --env-file .env.prod up -d
echo ""

echo "Step 4: Waiting for services to be healthy..."
sleep 10

# Check backend health
echo "  Checking backend health..."
max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if curl -f http://127.0.0.1:8015/api/health/ > /dev/null 2>&1; then
        echo "  ✓ Backend is healthy"
        break
    fi
    attempt=$((attempt + 1))
    if [ $attempt -eq $max_attempts ]; then
        echo "  ✗ Backend health check failed after $max_attempts attempts"
        docker compose logs backend
        exit 1
    fi
    sleep 2
done

# Check frontend
echo "  Checking frontend..."
if curl -f http://127.0.0.1:8081/ > /dev/null 2>&1; then
    echo "  ✓ Frontend is responding"
else
    echo "  ✗ Frontend check failed"
    docker compose logs frontend
    exit 1
fi
echo ""

echo "Step 5: Showing running services..."
docker compose ps
echo ""

echo "==================================="
echo "Test Summary"
echo "==================================="
echo "✓ All services are running successfully!"
echo ""
echo "Next steps:"
echo "  - Configure Caddy using CADDYFILE_SNIPPET.md"
echo "  - Test via your domain"
echo "  - Create Django superuser: docker compose exec backend python manage.py createsuperuser"
echo ""
echo "To stop services: docker compose down"
echo "To view logs: docker compose logs -f"
