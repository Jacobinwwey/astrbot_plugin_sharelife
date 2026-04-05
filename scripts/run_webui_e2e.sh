#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

HOST="${SHARELIFE_E2E_HOST:-127.0.0.1}"
PORT="${SHARELIFE_E2E_PORT:-38106}"
BASE_URL="http://${HOST}:${PORT}"
ARTIFACT_DIR="${SHARELIFE_E2E_ARTIFACT_DIR:-${REPO_ROOT}/output/playwright}"
SERVER_LOG="${ARTIFACT_DIR}/sharelife-webui-e2e-server.log"

mkdir -p "${ARTIFACT_DIR}"

cleanup() {
  if [[ -n "${SERVER_PID:-}" ]] && kill -0 "${SERVER_PID}" 2>/dev/null; then
    kill "${SERVER_PID}" 2>/dev/null || true
    wait "${SERVER_PID}" 2>/dev/null || true
  fi
}

trap cleanup EXIT

cd "${REPO_ROOT}"
python3 tests/e2e/serve_webui.py --host "${HOST}" --port "${PORT}" >"${SERVER_LOG}" 2>&1 &
SERVER_PID=$!

for attempt in $(seq 1 60); do
  if curl -fsS "${BASE_URL}/api/health" >/dev/null 2>&1; then
    break
  fi
  if ! kill -0 "${SERVER_PID}" 2>/dev/null; then
    printf '[sharelife] E2E server exited early. Log follows:\n' >&2
    cat "${SERVER_LOG}" >&2
    exit 1
  fi
  sleep 0.5
  if [[ "${attempt}" == "60" ]]; then
    printf '[sharelife] Timed out waiting for %s/api/health\n' "${BASE_URL}" >&2
    cat "${SERVER_LOG}" >&2
    exit 1
  fi
done

export SHARELIFE_WEBUI_URL="${BASE_URL}"
export SHARELIFE_E2E_ARTIFACT_DIR="${ARTIFACT_DIR}"

npx --yes --package=playwright bash -lc '
set -euo pipefail
BIN_PATH="${PATH%%:*}"
NODE_MODULES_DIR="$(cd "${BIN_PATH}/.." && pwd)"
export NODE_PATH="${NODE_MODULES_DIR}${NODE_PATH:+:${NODE_PATH}}"
node "'"${REPO_ROOT}"'/tests/e2e/sharelife_webui_e2e.cjs"
'
