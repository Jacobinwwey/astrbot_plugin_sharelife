#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

BUILD_IMAGE=1
KEEP_STACK=0
TIMEOUT_SECONDS=240
ARTIFACTS_DIR="${SHARELIFE_SMOKE_ARTIFACTS_DIR:-output/ops-smoke}"
REQUESTED_ARTIFACTS_DIR="${ARTIFACTS_DIR}"
ARTIFACTS_DIR_FALLBACK=0
ARTIFACTS_PATH_FILE="${SHARELIFE_SMOKE_ARTIFACTS_PATH_FILE:-.ops-smoke-last-artifacts-path}"
DEFAULT_DOCKER_DATA_DIR="output/docker-data"
DEFAULT_PROMETHEUS_DATA_DIR="output/docker-data/prometheus"
DEFAULT_GRAFANA_DATA_DIR="output/docker-data/grafana"
DOCKER_DATA_DIR="${SHARELIFE_SMOKE_DOCKER_DATA_DIR:-${DEFAULT_DOCKER_DATA_DIR}}"
REQUESTED_DOCKER_DATA_DIR="${DOCKER_DATA_DIR}"
DOCKER_DATA_DIR_FALLBACK=0
PRIVACY_MODE="${SHARELIFE_SMOKE_PRIVACY_MODE:-strict}"
ALLOW_CONTAINER_CONFLICT="${SHARELIFE_SMOKE_ALLOW_CONTAINER_CONFLICT:-0}"
ALLOW_PORT_CONFLICT="${SHARELIFE_SMOKE_ALLOW_PORT_CONFLICT:-0}"
AUTO_PORTS="${SHARELIFE_SMOKE_AUTO_PORTS:-1}"
LAST_STEP="bootstrap"
DOCKER_DATA_DIR_READY=0
DOCKER_DATA_PERMISSION_RELAXED=0

usage() {
  cat <<'EOF'
Usage: bash scripts/smoke_observability_stack.sh [options]

Options:
  --no-build           Start compose stack without --build.
  --keep-stack         Keep containers running after smoke check.
  --timeout-seconds N  Total wait budget for each readiness phase (default: 240).
  --artifacts-dir PATH Directory for smoke diagnostics (default: output/ops-smoke).
  --privacy-mode MODE  Artifact redaction mode: strict|off (default: strict).
  -h, --help           Show this help.

Environment overrides:
  SHARELIFE_SMOKE_WEBUI_URL      Default: http://127.0.0.1:8106
  SHARELIFE_SMOKE_PROM_URL       Default: http://127.0.0.1:9090
  SHARELIFE_SMOKE_GRAFANA_URL    Default: http://127.0.0.1:3000
  SHARELIFE_SMOKE_WEBUI_HOST_PORT  Default: 8106
  SHARELIFE_SMOKE_PROM_HOST_PORT   Default: 9090
  SHARELIFE_SMOKE_GRAFANA_HOST_PORT  Default: 3000
  SHARELIFE_SMOKE_GRAFANA_USER   Default: admin
  SHARELIFE_SMOKE_GRAFANA_PASS   Default: sharelife-change-me
  SHARELIFE_SMOKE_ARTIFACTS_DIR  Default: output/ops-smoke
  SHARELIFE_SMOKE_ARTIFACTS_PATH_FILE  Default: .ops-smoke-last-artifacts-path
  SHARELIFE_SMOKE_DOCKER_DATA_DIR  Default: output/docker-data
  SHARELIFE_SMOKE_PRIVACY_MODE   Default: strict
  SHARELIFE_SMOKE_ALLOW_CONTAINER_CONFLICT  Default: 0
  SHARELIFE_SMOKE_ALLOW_PORT_CONFLICT  Default: 0
  SHARELIFE_SMOKE_AUTO_PORTS     Default: 1
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --no-build)
      BUILD_IMAGE=0
      shift
      ;;
    --keep-stack)
      KEEP_STACK=1
      shift
      ;;
    --timeout-seconds)
      if [[ $# -lt 2 ]]; then
        echo "[ops-smoke] --timeout-seconds requires a numeric value" >&2
        exit 1
      fi
      TIMEOUT_SECONDS="$2"
      shift 2
      ;;
    --artifacts-dir)
      if [[ $# -lt 2 ]]; then
        echo "[ops-smoke] --artifacts-dir requires a path value" >&2
        exit 1
      fi
      ARTIFACTS_DIR="$2"
      shift 2
      ;;
    --privacy-mode)
      if [[ $# -lt 2 ]]; then
        echo "[ops-smoke] --privacy-mode requires a value: strict|off" >&2
        exit 1
      fi
      PRIVACY_MODE="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "[ops-smoke] unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

REQUESTED_ARTIFACTS_DIR="${ARTIFACTS_DIR}"

case "${PRIVACY_MODE}" in
  strict|off)
    ;;
  *)
    echo "[ops-smoke] invalid --privacy-mode: ${PRIVACY_MODE} (expected strict|off)" >&2
    exit 1
    ;;
esac

case "${AUTO_PORTS}" in
  0|1)
    ;;
  *)
    echo "[ops-smoke] invalid SHARELIFE_SMOKE_AUTO_PORTS: ${AUTO_PORTS} (expected 0|1)" >&2
    exit 1
    ;;
esac

WEBUI_HOST_PORT="${SHARELIFE_SMOKE_WEBUI_HOST_PORT:-8106}"
PROM_HOST_PORT="${SHARELIFE_SMOKE_PROM_HOST_PORT:-9090}"
GRAFANA_HOST_PORT="${SHARELIFE_SMOKE_GRAFANA_HOST_PORT:-3000}"
REQUESTED_WEBUI_HOST_PORT="${WEBUI_HOST_PORT}"
REQUESTED_PROM_HOST_PORT="${PROM_HOST_PORT}"
REQUESTED_GRAFANA_HOST_PORT="${GRAFANA_HOST_PORT}"

WEBUI_URL_OVERRIDE="${SHARELIFE_SMOKE_WEBUI_URL:-}"
PROM_URL_OVERRIDE="${SHARELIFE_SMOKE_PROM_URL:-}"
GRAFANA_URL_OVERRIDE="${SHARELIFE_SMOKE_GRAFANA_URL:-}"

WEBUI_URL="${WEBUI_URL_OVERRIDE:-http://127.0.0.1:${WEBUI_HOST_PORT}}"
PROM_URL="${PROM_URL_OVERRIDE:-http://127.0.0.1:${PROM_HOST_PORT}}"
GRAFANA_URL="${GRAFANA_URL_OVERRIDE:-http://127.0.0.1:${GRAFANA_HOST_PORT}}"
GRAFANA_USER="${SHARELIFE_SMOKE_GRAFANA_USER:-admin}"
GRAFANA_PASS="${SHARELIFE_SMOKE_GRAFANA_PASS:-sharelife-change-me}"

if ! command -v docker >/dev/null 2>&1; then
  echo "[ops-smoke] docker is required" >&2
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "[ops-smoke] python3 is required" >&2
  exit 1
fi

COMPOSE_CMD=(docker compose -f docker-compose.yml -f docker-compose.observability.yml)

log() {
  echo "[ops-smoke] $*"
}

mark_step() {
  LAST_STEP="$1"
  log "step=${LAST_STEP}"
}

persist_artifacts_dir_hint() {
  if [[ -z "${ARTIFACTS_PATH_FILE}" ]]; then
    return 0
  fi
  local path_file="${ARTIFACTS_PATH_FILE}"
  local parent_dir
  parent_dir="$(dirname "${path_file}")"
  mkdir -p "${parent_dir}" >/dev/null 2>&1 || true
  printf '%s\n' "${ARTIFACTS_DIR}" >"${path_file}" 2>/dev/null || true
}

ensure_artifacts_dir_writable() {
  if mkdir -p "${ARTIFACTS_DIR}" >/dev/null 2>&1 && [[ -w "${ARTIFACTS_DIR}" ]]; then
    persist_artifacts_dir_hint
    return 0
  fi

  local requested="${ARTIFACTS_DIR}"
  local fallback=""
  fallback="$(mktemp -d "/tmp/sharelife-ops-smoke.XXXXXX" 2>/dev/null || true)"
  if [[ -z "${fallback}" ]]; then
    echo "[ops-smoke] failed to prepare writable artifacts dir (${requested})" >&2
    exit 1
  fi

  ARTIFACTS_DIR="${fallback}"
  ARTIFACTS_DIR_FALLBACK=1
  log "artifacts dir not writable (${requested}); using fallback ${ARTIFACTS_DIR}"
  persist_artifacts_dir_hint
}

prepare_host_data_dir() {
  local requested="${DOCKER_DATA_DIR}"
  if [[ "${DOCKER_DATA_DIR}" != /* ]]; then
    DOCKER_DATA_DIR="${ROOT_DIR}/${DOCKER_DATA_DIR#./}"
  fi
  local root_dir="${DOCKER_DATA_DIR}"
  local prom_dir="${DOCKER_DATA_DIR}/prometheus"
  local grafana_dir="${DOCKER_DATA_DIR}/grafana"

  ensure_data_dirs() {
    local targets=(
      "${root_dir}"
      "${prom_dir}"
      "${grafana_dir}"
    )
    local dir
    for dir in "${targets[@]}"; do
      if ! mkdir -p "${dir}" >/dev/null 2>&1; then
        return 1
      fi
    done
    return 0
  }

  if ! ensure_data_dirs; then
    local fallback=""
    fallback="$(mktemp -d "/tmp/sharelife-ops-smoke-data.XXXXXX" 2>/dev/null || true)"
    if [[ -z "${fallback}" ]]; then
      log "warning: cannot pre-create ${prom_dir} and ${grafana_dir} (observability containers may fail to write)"
      return 0
    fi
    DOCKER_DATA_DIR="${fallback}"
    DOCKER_DATA_DIR_FALLBACK=1
    root_dir="${DOCKER_DATA_DIR}"
    prom_dir="${DOCKER_DATA_DIR}/prometheus"
    grafana_dir="${DOCKER_DATA_DIR}/grafana"
    if ! ensure_data_dirs; then
      log "warning: fallback docker data dir is not writable (${DOCKER_DATA_DIR})"
      return 0
    fi
    log "docker data dir not writable (${requested}); using fallback ${DOCKER_DATA_DIR}"
  fi

  export SHARELIFE_DOCKER_DATA_DIR="${DOCKER_DATA_DIR}"

  DOCKER_DATA_DIR_READY=1
  chmod a+rx "${root_dir}" >/dev/null 2>&1 || true

  # Prometheus/Grafana run as non-root users by default. Relax rwx on bind-mounted
  # subtrees to avoid CI/local startup failures from host UID/GID mismatch.
  for dir in "${prom_dir}" "${grafana_dir}"; do
    if chmod -R a+rwX "${dir}" >/dev/null 2>&1; then
      DOCKER_DATA_PERMISSION_RELAXED=1
    else
      log "warning: cannot relax permissions for ${dir} (permission mismatch may block startup)"
    fi
  done

  if [[ "${DOCKER_DATA_PERMISSION_RELAXED}" == "1" ]]; then
    log "prepared writable bind-mount dirs for prometheus/grafana"
  fi
}

preflight_container_conflicts() {
  if [[ "${ALLOW_CONTAINER_CONFLICT}" == "1" ]]; then
    return 0
  fi

  local raw_config
  if ! raw_config="$("${COMPOSE_CMD[@]}" config 2>/dev/null)"; then
    return 0
  fi
  local names=()
  while IFS= read -r line; do
    local name
    name="${line#container_name:}"
    name="$(xargs <<<"${name}")"
    name="${name%\"}"
    name="${name#\"}"
    if [[ -n "${name}" ]]; then
      names+=("${name}")
    fi
  done < <(grep -E '^[[:space:]]*container_name:' <<<"${raw_config}")

  if [[ "${#names[@]}" == "0" ]]; then
    return 0
  fi

  local conflicts=()
  local name
  for name in "${names[@]}"; do
    if docker ps -a --format '{{.Names}}' | grep -Fxq "${name}"; then
      local project_label
      project_label="$(docker inspect -f '{{ index .Config.Labels "com.docker.compose.project" }}' "${name}" 2>/dev/null || true)"
      if [[ "${project_label}" != "astrbot_plugin_sharelife" ]]; then
        conflicts+=("${name}")
      fi
    fi
  done

  if [[ "${#conflicts[@]}" == "0" ]]; then
    return 0
  fi

  mark_step "preflight_container_conflict"
  log "conflicting container names detected: ${conflicts[*]}"
  log "set SHARELIFE_SMOKE_ALLOW_CONTAINER_CONFLICT=1 to bypass preflight"
  return 1
}

is_port_bindable() {
  local port="$1"
  python3 - "$port" <<'PY'
import socket
import sys

port = int(sys.argv[1])
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
try:
    sock.bind(("0.0.0.0", port))
except OSError:
    raise SystemExit(1)
finally:
    sock.close()
raise SystemExit(0)
PY
}

find_next_bindable_port() {
  local start_port="$1"
  local end_port=$((start_port + 200))
  local candidate="${start_port}"
  while (( candidate <= end_port )); do
    if is_port_bindable "${candidate}"; then
      echo "${candidate}"
      return 0
    fi
    candidate=$((candidate + 1))
  done
  return 1
}

choose_host_port() {
  local requested_port="$1"
  local label="$2"
  if is_port_bindable "${requested_port}"; then
    echo "${requested_port}"
    return 0
  fi

  if [[ "${ALLOW_PORT_CONFLICT}" == "1" ]]; then
    echo "${requested_port}"
    return 0
  fi

  if [[ "${AUTO_PORTS}" != "1" ]]; then
    return 1
  fi

  local next_port=""
  next_port="$(find_next_bindable_port "$((requested_port + 1))" || true)"
  if [[ -z "${next_port}" ]]; then
    return 1
  fi
  echo "[ops-smoke] port ${requested_port} for ${label} is busy; using ${next_port}" >&2
  echo "${next_port}"
  return 0
}

resolve_host_ports() {
  local chosen_webui=""
  local chosen_prom=""
  local chosen_grafana=""

  chosen_webui="$(choose_host_port "${WEBUI_HOST_PORT}" "sharelife-webui")" || true
  chosen_prom="$(choose_host_port "${PROM_HOST_PORT}" "prometheus")" || true
  chosen_grafana="$(choose_host_port "${GRAFANA_HOST_PORT}" "grafana")" || true

  if [[ -z "${chosen_webui}" || -z "${chosen_prom}" || -z "${chosen_grafana}" ]]; then
    mark_step "preflight_port_conflict"
    log "unable to resolve required host ports (webui=${WEBUI_HOST_PORT}, prom=${PROM_HOST_PORT}, grafana=${GRAFANA_HOST_PORT})"
    log "set SHARELIFE_SMOKE_ALLOW_PORT_CONFLICT=1 or SHARELIFE_SMOKE_AUTO_PORTS=1 to relax preflight"
    return 1
  fi

  WEBUI_HOST_PORT="${chosen_webui}"
  PROM_HOST_PORT="${chosen_prom}"
  GRAFANA_HOST_PORT="${chosen_grafana}"

  export SHARELIFE_WEBUI_HOST_PORT="${WEBUI_HOST_PORT}"
  export SHARELIFE_PROM_HOST_PORT="${PROM_HOST_PORT}"
  export SHARELIFE_GRAFANA_HOST_PORT="${GRAFANA_HOST_PORT}"

  if [[ -z "${WEBUI_URL_OVERRIDE}" ]]; then
    WEBUI_URL="http://127.0.0.1:${WEBUI_HOST_PORT}"
  fi
  if [[ -z "${PROM_URL_OVERRIDE}" ]]; then
    PROM_URL="http://127.0.0.1:${PROM_HOST_PORT}"
  fi
  if [[ -z "${GRAFANA_URL_OVERRIDE}" ]]; then
    GRAFANA_URL="http://127.0.0.1:${GRAFANA_HOST_PORT}"
  fi
  return 0
}

write_artifact() {
  local file_name="$1"
  shift
  local output_path="${ARTIFACTS_DIR}/${file_name}"
  mkdir -p "$(dirname "${output_path}")"
  "$@" >"${output_path}" 2>&1 || true
  redact_artifact "${output_path}"
}

redact_artifact() {
  local output_path="$1"
  if [[ "${PRIVACY_MODE}" == "off" ]]; then
    return 0
  fi
  python3 scripts/redact_ops_artifacts.py \
    --input "${output_path}" \
    --output "${output_path}" \
    --mode "${PRIVACY_MODE}" >/dev/null 2>&1 || true
}

collect_diagnostics() {
  local exit_code="$1"
  ensure_artifacts_dir_writable

  {
    echo "timestamp_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "exit_code=${exit_code}"
    echo "webui_url=${WEBUI_URL}"
    echo "prom_url=${PROM_URL}"
    echo "grafana_url=${GRAFANA_URL}"
    echo "requested_webui_host_port=${REQUESTED_WEBUI_HOST_PORT}"
    echo "requested_prom_host_port=${REQUESTED_PROM_HOST_PORT}"
    echo "requested_grafana_host_port=${REQUESTED_GRAFANA_HOST_PORT}"
    echo "effective_webui_host_port=${WEBUI_HOST_PORT}"
    echo "effective_prom_host_port=${PROM_HOST_PORT}"
    echo "effective_grafana_host_port=${GRAFANA_HOST_PORT}"
    echo "build_image=${BUILD_IMAGE}"
    echo "keep_stack=${KEEP_STACK}"
    echo "timeout_seconds=${TIMEOUT_SECONDS}"
    echo "auto_ports=${AUTO_PORTS}"
    echo "requested_artifacts_dir=${REQUESTED_ARTIFACTS_DIR}"
    echo "effective_artifacts_dir=${ARTIFACTS_DIR}"
    echo "artifacts_dir_fallback=${ARTIFACTS_DIR_FALLBACK}"
    echo "docker_data_dir_ready=${DOCKER_DATA_DIR_READY}"
    echo "docker_data_permission_relaxed=${DOCKER_DATA_PERMISSION_RELAXED}"
    echo "requested_docker_data_dir=${REQUESTED_DOCKER_DATA_DIR}"
    echo "effective_docker_data_dir=${DOCKER_DATA_DIR}"
    echo "docker_data_dir_fallback=${DOCKER_DATA_DIR_FALLBACK}"
    echo "artifacts_path_file=${ARTIFACTS_PATH_FILE}"
    echo "privacy_mode=${PRIVACY_MODE}"
    echo "last_step=${LAST_STEP}"
  } >"${ARTIFACTS_DIR}/summary.txt"
  redact_artifact "${ARTIFACTS_DIR}/summary.txt"

  write_artifact "compose/rendered.yml" "${COMPOSE_CMD[@]}" config
  write_artifact "compose/ps.txt" "${COMPOSE_CMD[@]}" ps
  write_artifact "compose/logs-all.txt" "${COMPOSE_CMD[@]}" logs --no-color --timestamps

  write_artifact "http/webui-health.txt" curl -fsS "${WEBUI_URL}/api/health"
  write_artifact "http/webui-metrics.txt" curl -fsS "${WEBUI_URL}/api/metrics"

  write_artifact "http/prom-health.txt" curl -fsS "${PROM_URL}/-/healthy"
  write_artifact "http/prom-targets.json" curl -fsS "${PROM_URL}/api/v1/targets"

  write_artifact "http/grafana-health.json" curl -fsS "${GRAFANA_URL}/api/health"
  write_artifact "http/grafana-search.json" curl -fsS -u "${GRAFANA_USER}:${GRAFANA_PASS}" "${GRAFANA_URL}/api/search?query=Sharelife"

  if command -v python3 >/dev/null 2>&1; then
    python3 scripts/build_ops_smoke_triage.py \
      --artifacts-dir "${ARTIFACTS_DIR}" \
      --output "${ARTIFACTS_DIR}/triage.md" \
      --json-output "${ARTIFACTS_DIR}/triage.json" \
      --exit-code "${exit_code}" >/dev/null 2>&1 || true
  fi
}

cleanup() {
  local exit_code="${1:-0}"
  set +e

  collect_diagnostics "${exit_code}"

  if [[ "${KEEP_STACK}" == "1" ]]; then
    log "skip cleanup (--keep-stack enabled)"
    return 0
  fi

  log "stopping compose stack"
  "${COMPOSE_CMD[@]}" down --remove-orphans >/dev/null 2>&1 || true
  return 0
}

trap '_status=$?; trap - EXIT; cleanup "${_status}"; exit "${_status}"' EXIT

wait_http_ok() {
  local url="$1"
  local label="$2"
  local service_name="${3:-}"
  local elapsed=0
  local interval=2
  while (( elapsed < TIMEOUT_SECONDS )); do
    if curl -fsS "${url}" >/dev/null 2>&1; then
      log "${label} ready: ${url}"
      return 0
    fi
    if [[ -n "${service_name}" ]]; then
      local cid
      cid="$("${COMPOSE_CMD[@]}" ps -q "${service_name}" 2>/dev/null | head -n 1 || true)"
      if [[ -n "${cid}" ]]; then
        local lifecycle
        lifecycle="$(docker inspect -f '{{.State.Status}}' "${cid}" 2>/dev/null || true)"
        local health
        health="$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' "${cid}" 2>/dev/null || true)"
        if [[ "${lifecycle}" == "exited" || "${lifecycle}" == "dead" ]]; then
          log "${label} container is ${lifecycle}; failing fast"
          return 1
        fi
        if [[ "${health}" == "unhealthy" ]]; then
          log "${label} container health is unhealthy; failing fast"
          return 1
        fi
      fi
    fi
    sleep "${interval}"
    elapsed=$((elapsed + interval))
  done
  log "timeout waiting for ${label}: ${url}"
  return 1
}

wait_prometheus_health() {
  local healthy_url="${PROM_URL}/-/healthy"
  local ready_url="${PROM_URL}/-/ready"
  local elapsed=0
  local interval=2
  while (( elapsed < TIMEOUT_SECONDS )); do
    if curl -fsS "${healthy_url}" >/dev/null 2>&1 || curl -fsS "${ready_url}" >/dev/null 2>&1; then
      log "prometheus ready: ${healthy_url} (fallback ${ready_url})"
      return 0
    fi
    local cid
    cid="$("${COMPOSE_CMD[@]}" ps -q prometheus 2>/dev/null | head -n 1 || true)"
    if [[ -n "${cid}" ]]; then
      local lifecycle
      lifecycle="$(docker inspect -f '{{.State.Status}}' "${cid}" 2>/dev/null || true)"
      local health
      health="$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' "${cid}" 2>/dev/null || true)"
      if [[ "${lifecycle}" == "exited" || "${lifecycle}" == "dead" ]]; then
        log "prometheus container is ${lifecycle}; failing fast"
        return 1
      fi
      if [[ "${health}" == "unhealthy" ]]; then
        log "prometheus container health is unhealthy; failing fast"
        return 1
      fi
    fi
    sleep "${interval}"
    elapsed=$((elapsed + interval))
  done
  log "timeout waiting for prometheus: ${healthy_url} or ${ready_url}"
  return 1
}

wait_grafana_dashboard() {
  local elapsed=0
  local interval=3
  local target_title="Sharelife WebUI Observability"
  while (( elapsed < TIMEOUT_SECONDS )); do
    local body
    if ! body="$(curl -fsS -u "${GRAFANA_USER}:${GRAFANA_PASS}" "${GRAFANA_URL}/api/search?query=Sharelife" 2>/dev/null)"; then
      sleep "${interval}"
      elapsed=$((elapsed + interval))
      continue
    fi

    if SMOKE_GRAFANA_SEARCH_PAYLOAD="${body}" python3 - "${target_title}" <<'PY'
import json
import os
import sys

target = sys.argv[1]
raw = os.environ.get("SMOKE_GRAFANA_SEARCH_PAYLOAD", "")
try:
    payload = json.loads(raw)
except Exception:
    raise SystemExit(1)

if not isinstance(payload, list):
    raise SystemExit(1)

for item in payload:
    if isinstance(item, dict) and str(item.get("title", "")).strip() == target:
        raise SystemExit(0)

raise SystemExit(1)
PY
    then
      log "grafana dashboard ready: ${target_title}"
      return 0
    fi
    sleep "${interval}"
    elapsed=$((elapsed + interval))
  done
  log "timeout waiting for grafana dashboard provisioning"
  return 1
}

verify_prometheus_target() {
  local target_url="${PROM_URL}/api/v1/targets"
  local elapsed=0
  local interval=3
  while (( elapsed < TIMEOUT_SECONDS )); do
    local body
    if ! body="$(curl -fsS "${target_url}" 2>/dev/null)"; then
      sleep "${interval}"
      elapsed=$((elapsed + interval))
      continue
    fi
    if SMOKE_PROM_TARGETS_PAYLOAD="${body}" python3 - <<'PY'
import json
import os
import sys

raw = os.environ.get("SMOKE_PROM_TARGETS_PAYLOAD", "")
payload = json.loads(raw)
data = payload.get("data", {}) if isinstance(payload, dict) else {}
active = data.get("activeTargets", []) if isinstance(data, dict) else []

for item in active:
    if not isinstance(item, dict):
        continue
    labels = item.get("labels", {})
    if not isinstance(labels, dict):
        continue
    if str(labels.get("job", "")).strip() != "sharelife-webui":
        continue
    health = str(item.get("health", "")).strip().lower()
    if health == "up":
        raise SystemExit(0)

raise SystemExit(1)
PY
    then
      log "prometheus target sharelife-webui is UP"
      return 0
    fi
    sleep "${interval}"
    elapsed=$((elapsed + interval))
  done
  log "timeout waiting for prometheus target sharelife-webui to become UP"
  return 1
}

verify_webui_metrics_surface() {
  local body
  body="$(curl -fsS "${WEBUI_URL}/api/metrics")"
  local required=(
    "sharelife_webui_http_requests_total"
    "sharelife_webui_http_error_total"
    "sharelife_webui_auth_events_total"
    "sharelife_webui_rate_limit_total"
  )
  local metric
  for metric in "${required[@]}"; do
    if ! grep -q "${metric}" <<<"${body}"; then
      log "missing metric token: ${metric}"
      return 1
    fi
  done
  log "webui metric surface contains required tokens"
}

ensure_artifacts_dir_writable
prepare_host_data_dir
preflight_container_conflicts
resolve_host_ports

mark_step "compose_validate"
log "validating compose overlay"
"${COMPOSE_CMD[@]}" config > /dev/null

mark_step "compose_up"
log "starting stack (build=${BUILD_IMAGE})"
if [[ "${BUILD_IMAGE}" == "1" ]]; then
  "${COMPOSE_CMD[@]}" up -d --build
else
  "${COMPOSE_CMD[@]}" up -d
fi

mark_step "wait_webui_health"
wait_http_ok "${WEBUI_URL}/api/health" "sharelife-webui" "sharelife-webui"
mark_step "wait_prometheus_health"
wait_prometheus_health
mark_step "wait_grafana_health"
wait_http_ok "${GRAFANA_URL}/api/health" "grafana" "grafana"
mark_step "verify_webui_metrics"
verify_webui_metrics_surface
mark_step "verify_prometheus_target"
verify_prometheus_target
mark_step "verify_grafana_dashboard"
wait_grafana_dashboard

mark_step "completed"
log "observability stack smoke passed"
log "diagnostics written to ${ARTIFACTS_DIR}"
