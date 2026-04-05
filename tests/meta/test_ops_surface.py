from pathlib import Path
import json

import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_ops_assets_exist():
    required = [
        "ops/prometheus/sharelife-webui-alerts.rules.yml",
        "ops/prometheus/prometheus.sample.yml",
        "ops/grafana/provisioning/datasources/prometheus.yml",
        "ops/grafana/provisioning/dashboards/sharelife.yml",
        "ops/grafana/dashboards/sharelife-webui-dashboard.json",
        "docker-compose.observability.yml",
        "scripts/build_ops_smoke_triage.py",
        "scripts/publish_ops_smoke_annotations.py",
        "scripts/redact_ops_artifacts.py",
        "scripts/validate_ops_assets.py",
        "scripts/smoke_observability_stack.sh",
        ".github/workflows/ops-smoke.yml",
    ]
    for rel_path in required:
        assert (REPO_ROOT / rel_path).exists(), rel_path


def test_prometheus_alert_rules_cover_core_webui_signals():
    payload = yaml.safe_load(
        (REPO_ROOT / "ops/prometheus/sharelife-webui-alerts.rules.yml").read_text(encoding="utf-8")
    )
    groups = payload.get("groups", [])
    sharelife_group = next(
        (
            item
            for item in groups
            if isinstance(item, dict) and str(item.get("name", "")).strip() == "sharelife-webui"
        ),
        None,
    )
    assert isinstance(sharelife_group, dict)
    rules = sharelife_group.get("rules", [])
    by_name = {
        str(rule.get("alert", "")).strip(): rule
        for rule in rules
        if isinstance(rule, dict) and str(rule.get("alert", "")).strip()
    }

    assert "SharelifeWebUIHighErrorRatio" in by_name
    assert "SharelifeWebUIInternalErrorsDetected" in by_name
    assert "SharelifeWebUIRateLimitSpike" in by_name
    assert "SharelifeWebUILoginBruteforce" in by_name
    assert "SharelifeWebUISecurityAnomalyAlerts" in by_name

    assert "sharelife_webui_http_error_total" in by_name["SharelifeWebUIHighErrorRatio"]["expr"]
    assert "sharelife_webui_rate_limit_total" in by_name["SharelifeWebUIRateLimitSpike"]["expr"]
    assert "sharelife_webui_auth_events_total" in by_name["SharelifeWebUILoginBruteforce"]["expr"]
    assert "sharelife_webui_security_alert_total" in by_name["SharelifeWebUISecurityAnomalyAlerts"]["expr"]


def test_observability_compose_wires_prometheus_and_grafana():
    payload = yaml.safe_load((REPO_ROOT / "docker-compose.observability.yml").read_text(encoding="utf-8"))
    services = payload.get("services", {})
    assert isinstance(services, dict)
    assert "prometheus" in services
    assert "grafana" in services

    prometheus = services["prometheus"]
    assert "${SHARELIFE_PROM_HOST_PORT:-9090}:9090" in [str(item) for item in prometheus.get("ports", [])]
    assert any(
        str(item).startswith("./ops/prometheus/prometheus.sample.yml:")
        for item in prometheus.get("volumes", [])
    )

    grafana = services["grafana"]
    assert "${SHARELIFE_GRAFANA_HOST_PORT:-3000}:3000" in [str(item) for item in grafana.get("ports", [])]
    assert any(
        str(item).startswith("./ops/grafana/dashboards:")
        for item in grafana.get("volumes", [])
    )


def test_grafana_dashboard_tracks_auth_rate_limit_and_security_alert_series():
    payload = json.loads((REPO_ROOT / "ops/grafana/dashboards/sharelife-webui-dashboard.json").read_text(encoding="utf-8"))
    assert payload.get("title") == "Sharelife WebUI Observability"
    panels = payload.get("panels", [])
    panel_titles = []
    expressions = []
    for panel in panels:
        if not isinstance(panel, dict):
            continue
        title = panel.get("title")
        if isinstance(title, str):
            panel_titles.append(title)
        for target in panel.get("targets", []):
            if isinstance(target, dict):
                expr = target.get("expr")
                if isinstance(expr, str):
                    expressions.append(expr)
    joined = "\n".join(expressions)
    assert "sharelife_webui_auth_events_total" in joined
    assert "sharelife_webui_rate_limit_total" in joined
    assert "sharelife_webui_security_alert_total" in joined
    assert "Auth and Rate-Limit Event Rates" in panel_titles
    assert "Security Anomaly Alert Rates" in panel_titles
    assert "Security Alerts by Path (1h)" in panel_titles


def test_private_observability_runbook_is_not_published_in_public_docs():
    config_text = (REPO_ROOT / "docs" / ".vitepress" / "config.ts").read_text(encoding="utf-8")
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

    for locale in ("en", "zh", "ja"):
        assert not (REPO_ROOT / "docs" / locale / "how-to" / "webui-observability-runbook.md").exists()
        assert f"/{locale}/how-to/webui-observability-runbook" not in config_text

    assert "docs-private/" in readme


def test_ops_smoke_workflow_uses_smoke_script():
    workflow_text = (REPO_ROOT / ".github" / "workflows" / "ops-smoke.yml").read_text(encoding="utf-8")
    workflow = yaml.safe_load(workflow_text)
    assert "scripts/smoke_observability_stack.sh" in workflow_text
    assert "scripts/build_ops_smoke_triage.py" in workflow_text
    assert "scripts/publish_ops_smoke_annotations.py" in workflow_text
    assert "scripts/redact_ops_artifacts.py" in workflow_text
    assert "workflow_dispatch" in workflow_text
    assert "schedule:" in workflow_text

    smoke_job = workflow.get("jobs", {}).get("smoke", {})
    assert isinstance(smoke_job, dict)
    env = smoke_job.get("env", {})
    assert env.get("SHARELIFE_SMOKE_ARTIFACTS_DIR") == "output/ops-smoke"
    assert env.get("SHARELIFE_SMOKE_ARTIFACTS_PATH_FILE") == ".ops-smoke-last-artifacts-path"
    assert env.get("SHARELIFE_SMOKE_PRIVACY_MODE") == "strict"
    assert env.get("SHARELIFE_SMOKE_AUTO_PORTS") == "1"
    assert env.get("SHARELIFE_SMOKE_DOCKER_DATA_DIR") == "output/docker-data"

    steps = smoke_job.get("steps", [])
    assert isinstance(steps, list)
    assert any(
        isinstance(item, dict) and "scripts/smoke_observability_stack.sh" in str(item.get("run", ""))
        for item in steps
    )
    assert any(
        isinstance(item, dict) and "actions/upload-artifact@" in str(item.get("uses", ""))
        for item in steps
    )
    assert any(
        isinstance(item, dict) and "GITHUB_STEP_SUMMARY" in str(item.get("run", ""))
        for item in steps
    )
    assert any(
        isinstance(item, dict) and "publish_ops_smoke_annotations.py" in str(item.get("run", ""))
        for item in steps
    )
    assert any(
        isinstance(item, dict) and "SHARELIFE_SMOKE_ARTIFACTS_EFFECTIVE_DIR" in str(item.get("run", ""))
        for item in steps
    )


def test_smoke_script_supports_artifact_snapshot_surface():
    text = (REPO_ROOT / "scripts" / "smoke_observability_stack.sh").read_text(encoding="utf-8")
    assert "--artifacts-dir" in text
    assert "SHARELIFE_SMOKE_ARTIFACTS_DIR" in text
    assert "output/ops-smoke" in text
    assert "LAST_STEP=" in text
    assert "build_ops_smoke_triage.py" in text
    assert "redact_ops_artifacts.py" in text
    assert "triage.md" in text
    assert "triage.json" in text
    assert "compose/logs-all.txt" in text
    assert "http/prom-targets.json" in text
    assert "http/grafana-search.json" in text
    assert "--privacy-mode" in text
    assert "SHARELIFE_SMOKE_ARTIFACTS_PATH_FILE" in text
    assert "SHARELIFE_SMOKE_PRIVACY_MODE" in text
    assert "SHARELIFE_SMOKE_AUTO_PORTS" in text
    assert "SHARELIFE_SMOKE_WEBUI_HOST_PORT" in text
    assert "SHARELIFE_SMOKE_PROM_HOST_PORT" in text
    assert "SHARELIFE_SMOKE_GRAFANA_HOST_PORT" in text
    assert "SHARELIFE_SMOKE_DOCKER_DATA_DIR" in text
    assert "SHARELIFE_DOCKER_DATA_DIR" in text
    assert "SHARELIFE_SMOKE_ALLOW_PORT_CONFLICT" in text
    assert "ensure_artifacts_dir_writable" in text
    assert "resolve_host_ports" in text
    assert "choose_host_port" in text
    assert "requested_artifacts_dir" in text
    assert "effective_artifacts_dir" in text
    assert "artifacts_dir_fallback" in text
    assert "output/docker-data/prometheus" in text
    assert "output/docker-data/grafana" in text
    assert "chmod -R a+rwX" in text
    assert "docker_data_permission_relaxed" in text
    assert "requested_docker_data_dir" in text
    assert "effective_docker_data_dir" in text
    assert "docker_data_dir_fallback" in text
    assert "effective_webui_host_port" in text
    assert "effective_prom_host_port" in text
    assert "effective_grafana_host_port" in text


def test_makefile_exposes_triage_and_annotation_helpers():
    text = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    assert "ops-triage:" in text
    assert "--json-output output/ops-smoke/triage.json" in text
    assert "ops-annotate:" in text
    assert "publish_ops_smoke_annotations.py" in text
