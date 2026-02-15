#!/bin/bash
set -e
set -x

# Ensure backend directory exists
mkdir -p backend

# Ensure backend/.env.local exists
if [ ! -f backend/.env.local ]; then
    echo "Creating backend/.env.local from defaults..."
    cat <<EOT > backend/.env.local
DJANGO_SECRET_KEY=dev-secret-key
DJANGO_DEBUG=1
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,backend
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:8080
DB_ENGINE=postgresql
DB_NAME=rims
DB_USER=rims
DB_PASSWORD=rims
DB_HOST=db
DB_PORT=5432
EOT
else
    echo "backend/.env.local already exists"
fi

ls -l backend/.env.local

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
