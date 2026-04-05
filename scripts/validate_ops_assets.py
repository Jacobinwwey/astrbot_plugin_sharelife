#!/usr/bin/env python3
"""Validate bundled Sharelife observability assets (Prometheus/Grafana/compose)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = (
    "ops/prometheus/sharelife-webui-alerts.rules.yml",
    "ops/prometheus/prometheus.sample.yml",
    "ops/grafana/provisioning/datasources/prometheus.yml",
    "ops/grafana/provisioning/dashboards/sharelife.yml",
    "ops/grafana/dashboards/sharelife-webui-dashboard.json",
    "docker-compose.observability.yml",
    "scripts/build_ops_smoke_triage.py",
    "scripts/publish_ops_smoke_annotations.py",
    "scripts/redact_ops_artifacts.py",
    "scripts/smoke_observability_stack.sh",
    ".github/workflows/ops-smoke.yml",
)

REQUIRED_ALERT_RULE_TOKENS: dict[str, tuple[str, ...]] = {
    "SharelifeWebUIHighErrorRatio": (
        "sharelife_webui_http_error_total",
        "sharelife_webui_http_requests_total",
    ),
    "SharelifeWebUIInternalErrorsDetected": ("internal_server_error",),
    "SharelifeWebUIRateLimitSpike": ("sharelife_webui_rate_limit_total",),
    "SharelifeWebUILoginBruteforce": ("sharelife_webui_auth_events_total", "login_invalid_credentials"),
}

REQUIRED_DASHBOARD_METRIC_TOKENS = (
    "sharelife_webui_http_requests_total",
    "sharelife_webui_http_error_total",
    "sharelife_webui_http_request_duration_ms_sum",
    "sharelife_webui_http_request_duration_ms_count",
    "sharelife_webui_auth_events_total",
    "sharelife_webui_rate_limit_total",
    "sharelife_webui_security_alert_total",
)


def _read_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        return payload
    return {}


def _collect_dashboard_expressions(payload: dict[str, Any]) -> list[str]:
    out: list[str] = []
    panels = payload.get("panels", [])
    if not isinstance(panels, list):
        return out
    for panel in panels:
        if not isinstance(panel, dict):
            continue
        targets = panel.get("targets", [])
        if not isinstance(targets, list):
            continue
        for target in targets:
            if not isinstance(target, dict):
                continue
            expr = target.get("expr")
            if isinstance(expr, str) and expr.strip():
                out.append(expr)
    return out


def _validate_alert_rules(errors: list[str]) -> None:
    path = ROOT / "ops/prometheus/sharelife-webui-alerts.rules.yml"
    payload = _read_yaml(path)
    groups = payload.get("groups")
    if not isinstance(groups, list) or not groups:
        errors.append(f"{path}: missing groups")
        return

    sharelife_group = None
    for group in groups:
        if isinstance(group, dict) and str(group.get("name", "")).strip() == "sharelife-webui":
            sharelife_group = group
            break
    if not isinstance(sharelife_group, dict):
        errors.append(f"{path}: group 'sharelife-webui' not found")
        return

    rules = sharelife_group.get("rules")
    if not isinstance(rules, list):
        errors.append(f"{path}: 'rules' is missing")
        return

    by_name: dict[str, dict[str, Any]] = {}
    for item in rules:
        if not isinstance(item, dict):
            continue
        alert_name = str(item.get("alert", "")).strip()
        if alert_name:
            by_name[alert_name] = item

    for alert_name, required_tokens in REQUIRED_ALERT_RULE_TOKENS.items():
        rule = by_name.get(alert_name)
        if not isinstance(rule, dict):
            errors.append(f"{path}: alert '{alert_name}' missing")
            continue
        labels = rule.get("labels")
        if not isinstance(labels, dict) or str(labels.get("service", "")).strip() != "sharelife-webui":
            errors.append(f"{path}: alert '{alert_name}' must set labels.service=sharelife-webui")
        expr = str(rule.get("expr", "") or "")
        for token in required_tokens:
            if token not in expr:
                errors.append(f"{path}: alert '{alert_name}' expr missing token '{token}'")


def _validate_prometheus_sample(errors: list[str]) -> None:
    path = ROOT / "ops/prometheus/prometheus.sample.yml"
    payload = _read_yaml(path)

    rule_files = payload.get("rule_files")
    if not isinstance(rule_files, list) or "/etc/prometheus/sharelife-webui-alerts.rules.yml" not in rule_files:
        errors.append(f"{path}: rule_files must include /etc/prometheus/sharelife-webui-alerts.rules.yml")

    scrape_configs = payload.get("scrape_configs")
    if not isinstance(scrape_configs, list):
        errors.append(f"{path}: scrape_configs missing")
        return

    target_job = None
    for item in scrape_configs:
        if isinstance(item, dict) and str(item.get("job_name", "")).strip() == "sharelife-webui":
            target_job = item
            break

    if not isinstance(target_job, dict):
        errors.append(f"{path}: scrape job 'sharelife-webui' missing")
        return

    if str(target_job.get("metrics_path", "")).strip() != "/api/metrics":
        errors.append(f"{path}: scrape job 'sharelife-webui' must use metrics_path=/api/metrics")

    static_configs = target_job.get("static_configs")
    if not isinstance(static_configs, list) or not static_configs:
        errors.append(f"{path}: scrape job 'sharelife-webui' missing static_configs")
        return

    targets: list[str] = []
    for block in static_configs:
        if not isinstance(block, dict):
            continue
        raw_targets = block.get("targets")
        if isinstance(raw_targets, list):
            targets.extend(str(item).strip() for item in raw_targets if str(item).strip())
    if "sharelife-webui:8106" not in targets:
        errors.append(f"{path}: scrape target sharelife-webui:8106 missing")


def _validate_grafana_assets(errors: list[str]) -> None:
    datasource_path = ROOT / "ops/grafana/provisioning/datasources/prometheus.yml"
    datasource = _read_yaml(datasource_path)
    datasources = datasource.get("datasources")
    if not isinstance(datasources, list) or not datasources:
        errors.append(f"{datasource_path}: datasources missing")
    else:
        first = datasources[0]
        if isinstance(first, dict):
            if str(first.get("uid", "")).strip() != "sharelife-prometheus":
                errors.append(f"{datasource_path}: datasource uid must be sharelife-prometheus")
            if str(first.get("url", "")).strip() != "http://prometheus:9090":
                errors.append(f"{datasource_path}: datasource url must be http://prometheus:9090")
        else:
            errors.append(f"{datasource_path}: first datasource entry must be a mapping")

    provider_path = ROOT / "ops/grafana/provisioning/dashboards/sharelife.yml"
    provider = _read_yaml(provider_path)
    providers = provider.get("providers")
    if not isinstance(providers, list) or not providers:
        errors.append(f"{provider_path}: providers missing")
    else:
        first = providers[0]
        if isinstance(first, dict):
            options = first.get("options", {})
            if not isinstance(options, dict) or str(options.get("path", "")).strip() != "/var/lib/grafana/dashboards":
                errors.append(f"{provider_path}: providers[0].options.path must be /var/lib/grafana/dashboards")
        else:
            errors.append(f"{provider_path}: first provider entry must be a mapping")

    dashboard_path = ROOT / "ops/grafana/dashboards/sharelife-webui-dashboard.json"
    dashboard = json.loads(dashboard_path.read_text(encoding="utf-8"))
    if str(dashboard.get("title", "")).strip() != "Sharelife WebUI Observability":
        errors.append(f"{dashboard_path}: dashboard title mismatch")

    expr_text = "\n".join(_collect_dashboard_expressions(dashboard))
    for token in REQUIRED_DASHBOARD_METRIC_TOKENS:
        if token not in expr_text:
            errors.append(f"{dashboard_path}: metric token '{token}' not found in panel expressions")


def _validate_observability_compose(errors: list[str]) -> None:
    path = ROOT / "docker-compose.observability.yml"
    payload = _read_yaml(path)
    services = payload.get("services")
    if not isinstance(services, dict):
        errors.append(f"{path}: services missing")
        return

    for service_name in ("prometheus", "grafana"):
        if service_name not in services:
            errors.append(f"{path}: service '{service_name}' missing")

    prometheus = services.get("prometheus")
    if isinstance(prometheus, dict):
        ports = prometheus.get("ports")
        expected = "${SHARELIFE_PROM_HOST_PORT:-9090}:9090"
        if not isinstance(ports, list) or expected not in [str(item) for item in ports]:
            errors.append(f"{path}: prometheus service should expose {expected}")
    else:
        errors.append(f"{path}: prometheus service must be a mapping")

    grafana = services.get("grafana")
    if isinstance(grafana, dict):
        ports = grafana.get("ports")
        expected = "${SHARELIFE_GRAFANA_HOST_PORT:-3000}:3000"
        if not isinstance(ports, list) or expected not in [str(item) for item in ports]:
            errors.append(f"{path}: grafana service should expose {expected}")
    else:
        errors.append(f"{path}: grafana service must be a mapping")


def _validate_ops_smoke_workflow(errors: list[str]) -> None:
    path = ROOT / ".github/workflows/ops-smoke.yml"
    payload = _read_yaml(path)
    workflow_text = path.read_text(encoding="utf-8")

    jobs = payload.get("jobs")
    if not isinstance(jobs, dict):
        errors.append(f"{path}: jobs missing")
        return
    smoke_job = jobs.get("smoke")
    if not isinstance(smoke_job, dict):
        errors.append(f"{path}: jobs.smoke missing")
        return
    steps = smoke_job.get("steps")
    if not isinstance(steps, list) or not steps:
        errors.append(f"{path}: jobs.smoke.steps missing")
        return

    has_script = False
    has_upload = False
    has_summary = False
    has_annotations = False
    for step in steps:
        if not isinstance(step, dict):
            continue
        run_cmd = str(step.get("run", "") or "").strip()
        if "scripts/smoke_observability_stack.sh" in run_cmd:
            has_script = True
        if "GITHUB_STEP_SUMMARY" in run_cmd and "triage.md" in run_cmd:
            has_summary = True
        if "publish_ops_smoke_annotations.py" in run_cmd and "triage.json" in run_cmd:
            has_annotations = True
        uses = str(step.get("uses", "") or "").strip()
        if "actions/upload-artifact@" in uses:
            has_upload = True
    if not has_script:
        errors.append(f"{path}: smoke workflow must execute scripts/smoke_observability_stack.sh")
    if not has_upload:
        errors.append(f"{path}: smoke workflow must upload diagnostics via actions/upload-artifact")
    if not has_summary:
        errors.append(f"{path}: smoke workflow must publish triage to GITHUB_STEP_SUMMARY")
    if not has_annotations:
        errors.append(f"{path}: smoke workflow must publish triage annotations from triage.json")

    for token in (
        "scripts/smoke_observability_stack.sh",
        "scripts/build_ops_smoke_triage.py",
        "scripts/publish_ops_smoke_annotations.py",
        "scripts/redact_ops_artifacts.py",
        "SHARELIFE_SMOKE_PRIVACY_MODE",
        "SHARELIFE_SMOKE_ARTIFACTS_PATH_FILE",
        "SHARELIFE_SMOKE_ARTIFACTS_EFFECTIVE_DIR",
        "Resolve diagnostics directory",
        "SHARELIFE_SMOKE_AUTO_PORTS",
        "SHARELIFE_SMOKE_DOCKER_DATA_DIR",
    ):
        if token not in workflow_text:
            errors.append(f"{path}: missing path/run token '{token}'")

    env = smoke_job.get("env")
    if not isinstance(env, dict):
        errors.append(f"{path}: jobs.smoke.env missing")
    else:
        artifacts_dir = str(env.get("SHARELIFE_SMOKE_ARTIFACTS_DIR", "")).strip()
        if not artifacts_dir:
            errors.append(f"{path}: jobs.smoke.env must set SHARELIFE_SMOKE_ARTIFACTS_DIR")
        artifacts_path_file = str(env.get("SHARELIFE_SMOKE_ARTIFACTS_PATH_FILE", "")).strip()
        if not artifacts_path_file:
            errors.append(f"{path}: jobs.smoke.env must set SHARELIFE_SMOKE_ARTIFACTS_PATH_FILE")
        privacy_mode = str(env.get("SHARELIFE_SMOKE_PRIVACY_MODE", "")).strip()
        if privacy_mode != "strict":
            errors.append(f"{path}: jobs.smoke.env must set SHARELIFE_SMOKE_PRIVACY_MODE=strict")
        auto_ports = str(env.get("SHARELIFE_SMOKE_AUTO_PORTS", "")).strip()
        if auto_ports != "1":
            errors.append(f"{path}: jobs.smoke.env must set SHARELIFE_SMOKE_AUTO_PORTS=1")
        docker_data_dir = str(env.get("SHARELIFE_SMOKE_DOCKER_DATA_DIR", "")).strip()
        if not docker_data_dir:
            errors.append(f"{path}: jobs.smoke.env must set SHARELIFE_SMOKE_DOCKER_DATA_DIR")


def _validate_smoke_script_surface(errors: list[str]) -> None:
    path = ROOT / "scripts/smoke_observability_stack.sh"
    text = path.read_text(encoding="utf-8")
    required_tokens = (
        "--artifacts-dir",
        "SHARELIFE_SMOKE_ARTIFACTS_DIR",
        "output/ops-smoke",
        "LAST_STEP=",
        "build_ops_smoke_triage.py",
        "redact_ops_artifacts.py",
        "triage.md",
        "triage.json",
        "compose/logs-all.txt",
        "http/prom-targets.json",
        "http/grafana-search.json",
        "SHARELIFE_SMOKE_ARTIFACTS_PATH_FILE",
        "SHARELIFE_SMOKE_PRIVACY_MODE",
        "SHARELIFE_SMOKE_AUTO_PORTS",
        "SHARELIFE_SMOKE_WEBUI_HOST_PORT",
        "SHARELIFE_SMOKE_PROM_HOST_PORT",
        "SHARELIFE_SMOKE_GRAFANA_HOST_PORT",
        "SHARELIFE_SMOKE_DOCKER_DATA_DIR",
        "SHARELIFE_DOCKER_DATA_DIR",
        "resolve_host_ports",
        "choose_host_port",
        "effective_webui_host_port",
        "effective_prom_host_port",
        "effective_grafana_host_port",
        "SHARELIFE_SMOKE_ALLOW_PORT_CONFLICT",
        "ensure_artifacts_dir_writable",
        "requested_artifacts_dir",
        "effective_artifacts_dir",
        "artifacts_dir_fallback",
        "output/docker-data/prometheus",
        "output/docker-data/grafana",
        "chmod -R a+rwX",
        "docker_data_permission_relaxed",
        "requested_docker_data_dir",
        "effective_docker_data_dir",
        "docker_data_dir_fallback",
        ".ops-smoke-last-artifacts-path",
        "--privacy-mode",
    )
    for token in required_tokens:
        if token not in text:
            errors.append(f"{path}: missing token '{token}'")


def main() -> int:
    errors: list[str] = []
    for rel_path in REQUIRED_FILES:
        path = ROOT / rel_path
        if not path.exists():
            errors.append(f"missing required file: {path}")

    if errors:
        for item in errors:
            print(f"[ops-validate] {item}")
        return 1

    _validate_alert_rules(errors)
    _validate_prometheus_sample(errors)
    _validate_grafana_assets(errors)
    _validate_observability_compose(errors)
    _validate_ops_smoke_workflow(errors)
    _validate_smoke_script_surface(errors)

    if errors:
        for item in errors:
            print(f"[ops-validate] {item}")
        return 1

    print("ops observability assets are valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
