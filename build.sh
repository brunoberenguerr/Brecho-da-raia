#!/usr/bin/env bash
# Script de build executado pelo Render a cada implantação
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate
python manage.py popular_banco

# Cria o superusuário a partir de DJANGO_SUPERUSER_USERNAME/EMAIL/PASSWORD, se definidas
if [ -n "$DJANGO_SUPERUSER_USERNAME" ]; then
  python manage.py createsuperuser --no-input || true
fi
