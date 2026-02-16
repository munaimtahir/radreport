#!/bin/bash
set -e

echo "==> RIMS Backend Production Entrypoint"

# Run production bootstrap script
/app/scripts/prod_bootstrap.sh

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
