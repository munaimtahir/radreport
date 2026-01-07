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

# Create superuser if needed (optional, only for first deployment)
# Uncomment the following lines if you want to auto-create a superuser
# python manage.py shell << EOF
# from django.contrib.auth import get_user_model
# User = get_user_model()
# if not User.objects.filter(username='admin').exists():
#     User.objects.create_superuser('admin', 'admin@example.com', 'changeme')
#     print('Superuser created: admin/changeme')
# EOF

echo "==> Starting Gunicorn..."
# Bind to all interfaces inside container (Docker network isolation provides security)
exec gunicorn rims_backend.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info
