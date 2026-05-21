#!/bin/bash
set -e

echo "⏳ Waiting for PostgreSQL..."
while ! python -c "
import socket, os
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(2)
try:
    s.connect((os.environ.get('POSTGRES_HOST', 'db'), int(os.environ.get('POSTGRES_PORT', 5432))))
    s.close()
except Exception:
    exit(1)
" 2>/dev/null; do
    sleep 1
done
echo "✅ PostgreSQL is ready"

echo "📦 Running makemigrations..."
python manage.py makemigrations districts sos --noinput

echo "🔄 Running migrate..."
python manage.py migrate --noinput

echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

if [ "${CREATE_SUPERUSER:-false}" = "true" ]; then
    python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@sosbot.local', 'admin123')
    print('Superuser created: admin / admin123')
"
fi

exec "$@"
