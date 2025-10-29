#!/bin/bash
set -e

echo "Starting Face Blur API with Docker..."

# Build and start containers
docker compose down || true
docker compose up --build -d

# Apply migrations and collect static files
echo " Running migrations..."
docker compose exec -T web python manage.py makemigrations
docker compose exec -T web python manage.py migrate
docker compose exec -T web python manage.py collectstatic --noinput

# Optional: Create superuser
read -p "Create superuser? (y/n): " s
[ "$s" = "y" ] && docker compose exec web python manage.py createsuperuser

echo "http://localhost:8000/"
