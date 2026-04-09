#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

HOST="${SHARELIFE_E2E_HOST:-127.0.0.1}"
PORT="${SHARELIFE_E2E_PORT:-38107}"
ARTIFACT_DIR="${SHARELIFE_E2E_ARTIFACT_DIR:-${REPO_ROOT}/output/playwright}"
SERVER_LOG="${ARTIFACT_DIR}/sharelife-webui-market-auth-e2e-server.log"

mkdir -p "${ARTIFACT_DIR}"

pick_available_port() {
  python3 - "${HOST}" "${PORT}" "${SHARELIFE_E2E_PORT+x}" <<'PY'
import socket
import sys

host = sys.argv[1]
preferred = int(sys.argv[2])
port_explicitly_set = len(sys.argv[3]) > 0

def bindable(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((host, port))
        except OSError:
            return False
        return True

if port_explicitly_set or bindable(preferred):
    print(preferred)
else:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((host, 0))
        print(sock.getsockname()[1])
PY
}

PORT="$(pick_available_port)"
BASE_URL="http://${HOST}:${PORT}"

cleanup() {
  if [[ -n "${SERVER_PID:-}" ]] && kill -0 "${SERVER_PID}" 2>/dev/null; then
    kill "${SERVER_PID}" 2>/dev/null || true
    wait "${SERVER_PID}" 2>/dev/null || true
  fi
}

trap cleanup EXIT

cd "${REPO_ROOT}"
python3 tests/e2e/serve_webui.py \
  --host "${HOST}" \
  --port "${PORT}" \
  --auth-enabled \
  --member-password "${SHARELIFE_E2E_MEMBER_PASSWORD:-member-secret}" \
  --reviewer-password "${SHARELIFE_E2E_REVIEWER_PASSWORD:-reviewer-secret}" \
  --admin-password "${SHARELIFE_E2E_ADMIN_PASSWORD:-admin-secret}" \
  >"${SERVER_LOG}" 2>&1 &
SERVER_PID=$!

for attempt in $(seq 1 60); do
  if curl -fsS "${BASE_URL}/api/health" >/dev/null 2>&1; then
    break
  fi
  if ! kill -0 "${SERVER_PID}" 2>/dev/null; then
    printf '[sharelife] Auth E2E server exited early. Log follows:\n' >&2
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
node "'"${REPO_ROOT}"'/tests/e2e/sharelife_webui_market_auth_e2e.cjs"
'
