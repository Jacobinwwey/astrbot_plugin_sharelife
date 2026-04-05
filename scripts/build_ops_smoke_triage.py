#!/usr/bin/env python3
"""Build markdown + JSON triage summaries for ops-smoke diagnostics."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def _parse_summary(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    text = _read_text(path)
    for line in text.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            continue
        out[key] = value.strip()
    return out


def _json_load(path: Path):
    text = _read_text(path).strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except Exception:
        return None


def _json_load_text(text: str):
    source = text.strip()
    if not source:
        return None
    try:
        return json.loads(source)
    except Exception:
        return None


def _contains_all(text: str, tokens: Iterable[str]) -> bool:
    for token in tokens:
        if token not in text:
            return False
    return True


def _bool_icon(ok: bool) -> str:
    return "PASS" if ok else "FAIL"


def _check_webui_health(text: str) -> bool:
    payload = _json_load_text(text)
    if not isinstance(payload, dict):
        return False
    return bool(payload.get("ok", False))


def _check_prometheus_health(text: str) -> bool:
    probe = text.strip()
    if not probe:
        return False
    lowered = probe.lower()
    if lowered.startswith("curl:"):
        return False
    return "healthy" in lowered


def _check_grafana_health(text: str) -> bool:
    payload = _json_load_text(text)
    if not isinstance(payload, dict):
        return False
    database = str(payload.get("database", "")).strip().lower()
    return database == "ok"


def _check_prom_target_up(payload) -> bool:
    if not isinstance(payload, dict):
        return False
    data = payload.get("data")
    if not isinstance(data, dict):
        return False
    active = data.get("activeTargets")
    if not isinstance(active, list):
        return False
    for item in active:
        if not isinstance(item, dict):
            continue
        labels = item.get("labels")
        if not isinstance(labels, dict):
            continue
        if str(labels.get("job", "")).strip() != "sharelife-webui":
            continue
        health = str(item.get("health", "")).strip().lower()
        if health == "up":
            return True
    return False


def _check_grafana_dashboard(payload) -> bool:
    if not isinstance(payload, list):
        return False
    for item in payload:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title", "")).strip()
        if title == "Sharelife WebUI Observability":
            return True
    return False


def _normalize_exit_code(summary: dict[str, str], explicit_exit_code: int | None) -> int:
    if explicit_exit_code is not None:
        return int(explicit_exit_code)
    recorded_exit = summary.get("exit_code", "").strip()
    if not recorded_exit:
        return 1
    try:
        return int(recorded_exit)
    except ValueError:
        return 1


def _build_actions(
    checks: dict[str, bool],
    *,
    result_ok: bool,
    last_step: str = "-",
    summary: dict[str, str] | None = None,
) -> list[str]:
    summary = summary or {}
    last_step = str(last_step or "-").strip()
    if result_ok and all(checks.values()):
        return [
            "No immediate action required.",
            "Keep this run as the current observability baseline.",
        ]

    actions: list[str] = []
    if last_step == "preflight_container_conflict":
        actions.append(
            "Resolve pre-existing container name conflicts (`sharelife-webui`, `sharelife-prometheus`, `sharelife-grafana`) or set `SHARELIFE_SMOKE_ALLOW_CONTAINER_CONFLICT=1` only in isolated local debugging."
        )
    elif last_step == "preflight_port_conflict":
        actions.append(
            "Free required host ports (8106, 9090, 3000), or enable auto-port fallback (`SHARELIFE_SMOKE_AUTO_PORTS=1`), or set `SHARELIFE_SMOKE_ALLOW_PORT_CONFLICT=1` only in isolated local debugging."
        )
    elif last_step == "compose_up":
        actions.append(
            "Check compose startup conflicts (existing container names, port collisions, daemon errors) in `compose/logs-all.txt` and `compose/ps.txt`."
        )

    if str(summary.get("artifacts_dir_fallback", "")).strip() in {"1", "true", "True"}:
        actions.append(
            "Artifact directory fallback was activated. Use `effective_artifacts_dir` from `summary.txt` for diagnostics upload and triage references."
        )
    if str(summary.get("docker_data_dir_fallback", "")).strip() in {"1", "true", "True"}:
        actions.append(
            "Docker data directory fallback was activated. Verify mounted storage path stability using `requested_docker_data_dir` and `effective_docker_data_dir` from `summary.txt`."
        )

    if not checks["webui_health"]:
        actions.append(
            "Check `compose/logs-all.txt` for `sharelife-webui` startup/auth errors and validate env values in `compose/rendered.yml`."
        )
    if not checks["prometheus_health"]:
        actions.append(
            "Inspect Prometheus container health and rule load errors (`compose/logs-all.txt`, `http/prom-health.txt`)."
        )
    if not checks["grafana_health"]:
        actions.append(
            "Inspect Grafana startup/provisioning errors (`compose/logs-all.txt`, `http/grafana-health.json`)."
        )
    if not checks["webui_metrics_surface"]:
        actions.append(
            "Verify `/api/metrics` output and middleware initialization (`http/webui-metrics.txt`)."
        )
    if not checks["prometheus_target_sharelife_up"]:
        actions.append(
            "Open `http/prom-targets.json`; verify scrape target `sharelife-webui:8106` and network reachability."
        )
    if not checks["grafana_dashboard_provisioned"]:
        actions.append(
            "Check Grafana search payload (`http/grafana-search.json`) and dashboard provisioning mounts in compose."
        )
    if not actions:
        actions.append("Review `compose/logs-all.txt` and `summary.txt`; failure occurred before signal checks completed.")
    return actions


def build_triage_data(artifacts_dir: Path, *, explicit_exit_code: int | None = None) -> dict[str, Any]:
    summary = _parse_summary(artifacts_dir / "summary.txt")
    exit_code = _normalize_exit_code(summary, explicit_exit_code)
    result_ok = exit_code == 0
    last_step = summary.get("last_step", "-")
    timestamp_utc = summary.get("timestamp_utc", "-")

    webui_health = _read_text(artifacts_dir / "http/webui-health.txt")
    prom_health = _read_text(artifacts_dir / "http/prom-health.txt")
    grafana_health = _read_text(artifacts_dir / "http/grafana-health.json")
    metrics_text = _read_text(artifacts_dir / "http/webui-metrics.txt")
    prom_targets_payload = _json_load(artifacts_dir / "http/prom-targets.json")
    grafana_search_payload = _json_load(artifacts_dir / "http/grafana-search.json")

    checks: dict[str, bool] = {
        "webui_health": _check_webui_health(webui_health),
        "prometheus_health": _check_prometheus_health(prom_health),
        "grafana_health": _check_grafana_health(grafana_health),
        "webui_metrics_surface": _contains_all(
            metrics_text,
            (
                "sharelife_webui_http_requests_total",
                "sharelife_webui_http_error_total",
                "sharelife_webui_auth_events_total",
                "sharelife_webui_rate_limit_total",
                "sharelife_webui_security_alert_total",
            ),
        ),
        "prometheus_target_sharelife_up": _check_prom_target_up(prom_targets_payload),
        "grafana_dashboard_provisioned": _check_grafana_dashboard(grafana_search_payload),
    }

    signals = [
        {"key": "webui_health", "label": "WebUI `/api/health`", "ok": checks["webui_health"]},
        {"key": "prometheus_health", "label": "Prometheus `/-/healthy`", "ok": checks["prometheus_health"]},
        {"key": "grafana_health", "label": "Grafana `/api/health`", "ok": checks["grafana_health"]},
        {"key": "webui_metrics_surface", "label": "WebUI metrics surface", "ok": checks["webui_metrics_surface"]},
        {
            "key": "prometheus_target_sharelife_up",
            "label": "Prometheus target `sharelife-webui`",
            "ok": checks["prometheus_target_sharelife_up"],
        },
        {
            "key": "grafana_dashboard_provisioned",
            "label": "Grafana dashboard provisioning",
            "ok": checks["grafana_dashboard_provisioned"],
        },
    ]

    actions = _build_actions(checks, result_ok=result_ok, last_step=last_step, summary=summary)
    key_artifacts = [
        "summary.txt",
        "triage.md",
        "triage.json",
        "compose/rendered.yml",
        "compose/ps.txt",
        "compose/logs-all.txt",
        "http/webui-health.txt",
        "http/webui-metrics.txt",
        "http/prom-health.txt",
        "http/prom-targets.json",
        "http/grafana-health.json",
        "http/grafana-search.json",
    ]

    return {
        "result": "PASS" if result_ok else "FAIL",
        "result_ok": result_ok,
        "exit_code": exit_code,
        "last_step": last_step,
        "timestamp_utc": timestamp_utc,
        "signals": signals,
        "checks": checks,
        "actions": actions,
        "key_artifacts": key_artifacts,
        "summary": summary,
    }


def build_triage_markdown(data: dict[str, Any]) -> str:
    signals = data.get("signals", []) if isinstance(data.get("signals"), list) else []
    actions = data.get("actions", []) if isinstance(data.get("actions"), list) else []
    key_artifacts = data.get("key_artifacts", []) if isinstance(data.get("key_artifacts"), list) else []
    summary = data.get("summary", {}) if isinstance(data.get("summary"), dict) else {}
    requested_artifacts_dir = str(summary.get("requested_artifacts_dir", "")).strip()
    effective_artifacts_dir = str(summary.get("effective_artifacts_dir", "")).strip()
    fallback_used = str(summary.get("artifacts_dir_fallback", "0")).strip()
    requested_webui_port = str(summary.get("requested_webui_host_port", "")).strip()
    requested_prom_port = str(summary.get("requested_prom_host_port", "")).strip()
    requested_grafana_port = str(summary.get("requested_grafana_host_port", "")).strip()
    effective_webui_port = str(summary.get("effective_webui_host_port", "")).strip()
    effective_prom_port = str(summary.get("effective_prom_host_port", "")).strip()
    effective_grafana_port = str(summary.get("effective_grafana_host_port", "")).strip()
    requested_docker_data_dir = str(summary.get("requested_docker_data_dir", "")).strip()
    effective_docker_data_dir = str(summary.get("effective_docker_data_dir", "")).strip()
    docker_data_fallback_used = str(summary.get("docker_data_dir_fallback", "0")).strip()

    lines = [
        "# Ops Smoke Triage",
        "",
        f"- Result: **{data.get('result', 'FAIL')}**",
        f"- Exit code: `{data.get('exit_code', 1)}`",
        f"- Last step: `{data.get('last_step', '-')}`",
        f"- Generated at (UTC): `{data.get('timestamp_utc', '-')}`",
    ]
    if requested_artifacts_dir:
        lines.append(f"- Requested artifacts dir: `{requested_artifacts_dir}`")
    if effective_artifacts_dir:
        lines.append(f"- Effective artifacts dir: `{effective_artifacts_dir}`")
    lines.append(f"- Artifacts dir fallback used: `{'yes' if fallback_used in {'1', 'true', 'True'} else 'no'}`")
    if requested_webui_port or requested_prom_port or requested_grafana_port:
        lines.append(
            f"- Requested host ports: `webui={requested_webui_port or '-'} prom={requested_prom_port or '-'} grafana={requested_grafana_port or '-'}`"
        )
    if effective_webui_port or effective_prom_port or effective_grafana_port:
        lines.append(
            f"- Effective host ports: `webui={effective_webui_port or '-'} prom={effective_prom_port or '-'} grafana={effective_grafana_port or '-'}`"
        )
    if requested_docker_data_dir:
        lines.append(f"- Requested docker data dir: `{requested_docker_data_dir}`")
    if effective_docker_data_dir:
        lines.append(f"- Effective docker data dir: `{effective_docker_data_dir}`")
    lines.append(f"- Docker data dir fallback used: `{'yes' if docker_data_fallback_used in {'1', 'true', 'True'} else 'no'}`")
    lines.extend(["", "## Signal Matrix", "", "| Signal | Status |", "|---|---|"])
    for signal in signals:
        if not isinstance(signal, dict):
            continue
        label = str(signal.get("label", signal.get("key", "unknown"))).strip()
        ok = bool(signal.get("ok", False))
        lines.append(f"| {label} | {_bool_icon(ok)} |")

    lines.extend(["", "## Suggested Triage Actions", ""])
    for idx, action in enumerate(actions, start=1):
        lines.append(f"{idx}. {action}")

    lines.extend(["", "## Key Artifacts", ""])
    for item in key_artifacts:
        lines.append(f"- `{item}`")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build markdown/json triage summaries for ops-smoke artifacts.")
    parser.add_argument("--artifacts-dir", required=True, help="Directory containing ops-smoke artifacts.")
    parser.add_argument("--output", default="", help="Output markdown file path (default: <artifacts-dir>/triage.md).")
    parser.add_argument(
        "--json-output",
        default="",
        help="Output JSON file path (default: <artifacts-dir>/triage.json).",
    )
    parser.add_argument("--exit-code", type=int, default=None, help="Override exit code for result line.")
    args = parser.parse_args()

    artifacts_dir = Path(args.artifacts_dir).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve() if args.output else artifacts_dir / "triage.md"
    json_output_path = Path(args.json_output).expanduser().resolve() if args.json_output else artifacts_dir / "triage.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    json_output_path.parent.mkdir(parents=True, exist_ok=True)

    data = build_triage_data(artifacts_dir=artifacts_dir, explicit_exit_code=args.exit_code)
    markdown = build_triage_markdown(data)

    output_path.write_text(markdown, encoding="utf-8")
    json_output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"triage markdown written: {output_path}")
    print(f"triage json written: {json_output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
