#!/bin/sh
set -e

echo ">> Ma'lumotlar bazasi migratsiyalari ishga tushmoqda..."
python manage.py migrate --noinput

echo ">> Statik fayllar yig'ilmoqda..."
python manage.py collectstatic --noinput

echo ">> Gunicorn ishga tushmoqda..."
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --timeout 60
