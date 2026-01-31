#!/bin/bash

# Start all services in detached mode
docker compose -f docker-compose.dev.yml up -d

# Wait for the backend service to be healthy
echo "Waiting for backend service to be healthy..."
while [ "$(docker inspect -f {{.State.Health.Status}} rims_backend_local)" != "healthy" ]; do
    sleep 5;
done

# Create a superuser and set password
echo "Creating superuser..."
docker compose -f docker-compose.dev.yml exec backend sh -c "python manage.py createsuperuser --username admin --noinput || echo 'Superuser already exists, setting password...'; python manage.py shell -c \"from django.contrib.auth import get_user_model; User = get_user_model(); u = User.objects.get(username='admin'); u.set_password('admin123'); u.save()\""
