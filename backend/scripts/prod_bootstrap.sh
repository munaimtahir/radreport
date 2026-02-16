#!/bin/bash
set -e

# Production Bootstrap Script
# Runs inside backend container to prepare Django for production
# Called by entrypoint.sh before starting Gunicorn

echo "==> RIMS Backend Production Bootstrap"

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

# Run database migrations
echo "==> Running database migrations..."
python manage.py migrate --noinput
if [ $? -ne 0 ]; then
    echo "✗ FAIL: Database migrations failed"
    exit 1
fi
echo "✓ Migrations completed"

# Collect static files
echo "==> Collecting static files..."
python manage.py collectstatic --noinput
if [ $? -ne 0 ]; then
    echo "✗ FAIL: Static file collection failed"
    exit 1
fi
echo "✓ Static files collected"

# Run Django system check
echo "==> Running Django system check..."
python manage.py check
if [ $? -ne 0 ]; then
    echo "✗ FAIL: Django system check failed"
    exit 1
fi
echo "✓ System check passed"

echo "==> Bootstrap completed successfully"
