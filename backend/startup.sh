#!/bin/sh
set -e

mkdir -p /home/data
export PYTHONPATH="/home/site/wwwroot/.python_packages/lib/site-packages:${PYTHONPATH}"

echo "Running database migrations..."
alembic upgrade head

echo "Starting Azure App Service web server..."
exec gunicorn -w 1 -k uvicorn.workers.UvicornWorker -b "0.0.0.0:${PORT:-8000}" --timeout 120 --access-logfile - --error-logfile - app.main:app
