#!/bin/sh
set -e

if [ -n "$DATABASE_HOST" ]; then
  echo "Waiting for PostgreSQL at $DATABASE_HOST:$DATABASE_PORT..."
  until nc -z "$DATABASE_HOST" "$DATABASE_PORT"; do
    sleep 1
  done
fi

python manage.py migrate
python manage.py runserver 0.0.0.0:8000
