#!/bin/bash
set -e

echo "==> RIMS Backend Production Entrypoint"

# Run production bootstrap script
/app/scripts/prod_bootstrap.sh

# Create superuser and seed initial data (idempotent - safe to run multiple times)
echo "==> Creating superuser and seeding initial data..."
python seed_data.py

echo "==> Starting Gunicorn..."
# Bind to all interfaces inside container (Docker network isolation provides security)
# Workers: Use GUNICORN_WORKERS env var or default to 4
WORKERS=${GUNICORN_WORKERS:-4}
TIMEOUT=${GUNICORN_TIMEOUT:-120}

exec gunicorn rims_backend.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers $WORKERS \
    --timeout $TIMEOUT \
    --access-logfile - \
    --error-logfile - \
    --log-level info
