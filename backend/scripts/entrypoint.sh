#!/bin/bash
set -e

echo "==> RIMS Backend Production Entrypoint"

# Set default values for DB variables if not provided
DB_HOST=${DB_HOST:-db}
DB_PORT=${DB_PORT:-5432}
DB_USER=${DB_USER:-rims}

# Wait for database to be ready
echo "==> Waiting for PostgreSQL..."
while ! pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" > /dev/null 2>&1; do
    echo "    PostgreSQL not ready, waiting..."
    sleep 2
done
echo "==> PostgreSQL is ready"

# Collect static files
echo "==> Collecting static files..."
python manage.py collectstatic --noinput

# Run database migrations
echo "==> Running database migrations..."
python manage.py migrate --noinput

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
