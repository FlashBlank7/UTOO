#!/bin/sh
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Starting Azure App Service web server..."
exec gunicorn -w 2 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 app.main:app
