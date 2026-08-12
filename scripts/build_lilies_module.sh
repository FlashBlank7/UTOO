#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(CDPATH= cd -- "${SCRIPT_DIR}/.." && pwd)"
LILIES_SOURCE="${PROJECT_ROOT}/modules/lilies"
LILIES_FRONTEND="${LILIES_SOURCE}/platform/frontend"
STAGE_DIR="${PROJECT_ROOT}/backend/lilies"
BUNDLE_NODE=false

if [[ "${1:-}" == "--bundle-node" ]]; then
  BUNDLE_NODE=true
elif [[ -n "${1:-}" ]]; then
  echo "Usage: $0 [--bundle-node]" >&2
  exit 2
fi

if [[ ! -f "${LILIES_FRONTEND}/package-lock.json" ]] || \
   [[ ! -f "${LILIES_SOURCE}/platform/backend/src/agent_platform/api.py" ]]; then
  echo "Vendored Lilies source is incomplete under ${LILIES_SOURCE}" >&2
  exit 1
fi

echo "Building vendored Lilies Studio..."
(
  cd "${LILIES_FRONTEND}"
  npm ci
  npm run build
)

STAGE_TMP="$(mktemp -d "${TMPDIR:-/tmp}/utoo-lilies-stage.XXXXXX")"
cleanup() {
  rm -rf "${STAGE_TMP}"
}
trap cleanup EXIT

mkdir -p "${STAGE_TMP}/backend" "${STAGE_TMP}/frontend/.next"
cp -R "${LILIES_SOURCE}/platform/backend/src/agent_platform" "${STAGE_TMP}/backend/"
cp -R "${LILIES_FRONTEND}/.next/standalone/." "${STAGE_TMP}/frontend/"
cp -R "${LILIES_FRONTEND}/.next/static" "${STAGE_TMP}/frontend/.next/"
if [[ -d "${LILIES_FRONTEND}/public" ]]; then
  cp -R "${LILIES_FRONTEND}/public" "${STAGE_TMP}/frontend/"
fi

if [[ "${BUNDLE_NODE}" == true ]]; then
  NODE_SOURCE="$(command -v node)"
  mkdir -p "${STAGE_TMP}/runtime"
  cp -L "${NODE_SOURCE}" "${STAGE_TMP}/runtime/node"
  chmod 755 "${STAGE_TMP}/runtime/node"
fi

if [[ "${STAGE_DIR}" != "${PROJECT_ROOT}/backend/lilies" ]]; then
  echo "Refusing to replace unexpected stage directory: ${STAGE_DIR}" >&2
  exit 1
fi
rm -rf "${STAGE_DIR}"
mv "${STAGE_TMP}" "${STAGE_DIR}"
trap - EXIT

echo "Lilies module staged at ${STAGE_DIR}"
