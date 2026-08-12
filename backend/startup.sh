#!/bin/sh
set -e

mkdir -p /home/data
export PYTHONPATH="/home/site/wwwroot/.python_packages/lib/site-packages:${PYTHONPATH}"
export PATH="/home/site/wwwroot/.python_packages/lib/site-packages/bin:${PATH}"

APP_ROOT="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
LILIES_ROOT="${APP_ROOT}/lilies"

if [ -f "${LILIES_ROOT}/backend/agent_platform/api.py" ] && [ -f "${LILIES_ROOT}/frontend/server.js" ]; then
    export PYTHONPATH="${LILIES_ROOT}/backend:${PYTHONPATH}"
    export DATA_DIR="${LILIES_DATA_DIR:-/home/data/lilies}"
    export WORKSPACE_ROOT="${LILIES_WORKSPACE_ROOT:-/home/data/lilies-workspaces}"
    export API_TOKEN="${LILIES_API_TOKEN:-change-me}"
    export MODEL_EGRESS_ENABLED="${LILIES_MODEL_EGRESS_ENABLED:-false}"
    export AGENT_PLATFORM_URL="http://127.0.0.1:${LILIES_API_PORT:-8001}"
    export LILIES_FRONTEND_URL="http://127.0.0.1:${LILIES_FRONTEND_PORT:-3000}"
    mkdir -p "${DATA_DIR}" "${WORKSPACE_ROOT}"

    LILIES_LOG_DIR="${LILIES_LOG_DIR:-/home/LogFiles}"
    if [ ! -d "${LILIES_LOG_DIR}" ] || [ ! -w "${LILIES_LOG_DIR}" ]; then
        LILIES_LOG_DIR="/tmp"
    fi

    echo "Starting Lilies API on loopback..."
    python -m uvicorn agent_platform.api:app \
        --host 127.0.0.1 \
        --port "${LILIES_API_PORT:-8001}" \
        >"${LILIES_LOG_DIR}/lilies-api.log" 2>&1 &

    LILIES_NODE="${LILIES_NODE_BINARY:-${LILIES_ROOT}/runtime/node}"
    if [ ! -x "${LILIES_NODE}" ]; then
        LILIES_NODE="$(command -v node || true)"
    fi
    if [ -n "${LILIES_NODE}" ]; then
        echo "Starting Lilies Studio on loopback..."
        (
            cd "${LILIES_ROOT}/frontend"
            HOSTNAME=127.0.0.1 PORT="${LILIES_FRONTEND_PORT:-3000}" \
                exec "${LILIES_NODE}" server.js
        ) >"${LILIES_LOG_DIR}/lilies-frontend.log" 2>&1 &
    else
        echo "Lilies Studio was not started: Node.js runtime not found."
    fi
else
    echo "Lilies module artifacts are missing; starting UTOO without the module."
fi

echo "Running database migrations..."
python -m alembic upgrade head

echo "Starting Azure App Service web server..."
exec python -m gunicorn -w 1 -k uvicorn.workers.UvicornWorker -b "0.0.0.0:${PORT:-8000}" --timeout 120 --access-logfile - --error-logfile - app.main:app
