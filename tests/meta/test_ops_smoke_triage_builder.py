from __future__ import annotations

import json
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_ops_smoke_triage_builder_marks_pass_when_signals_are_healthy(tmp_path):
    artifacts = tmp_path / "ops-smoke"
    _write(
        artifacts / "summary.txt",
        "\n".join(
            [
                "timestamp_utc=2026-04-02T00:00:00Z",
                "exit_code=0",
                "last_step=completed",
            ]
        )
        + "\n",
    )
    _write(
        artifacts / "http/webui-metrics.txt",
        "\n".join(
            [
                "sharelife_webui_http_requests_total 1",
                "sharelife_webui_http_error_total 0",
                "sharelife_webui_auth_events_total 0",
                "sharelife_webui_rate_limit_total 0",
                "sharelife_webui_security_alert_total 0",
            ]
        ),
    )
    _write(artifacts / "http/webui-health.txt", '{"ok": true}')
    _write(artifacts / "http/prom-health.txt", "Prometheus is Healthy.\n")
    _write(artifacts / "http/grafana-health.json", '{"database":"ok"}')
    _write(
        artifacts / "http/prom-targets.json",
        json.dumps(
            {
                "status": "success",
                "data": {
                    "activeTargets": [
                        {
                            "labels": {"job": "sharelife-webui"},
                            "health": "up",
                        }
                    ]
                },
            }
        ),
    )
    _write(
        artifacts / "http/grafana-search.json",
        json.dumps([{"title": "Sharelife WebUI Observability"}]),
    )

    completed = subprocess.run(
        [
            "python3",
            "scripts/build_ops_smoke_triage.py",
            "--artifacts-dir",
            str(artifacts),
        ],
        cwd=REPO_ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    assert completed.returncode == 0, completed.stderr

    triage = (artifacts / "triage.md").read_text(encoding="utf-8")
    triage_json = json.loads((artifacts / "triage.json").read_text(encoding="utf-8"))
    assert "Result: **PASS**" in triage
    assert "Last step: `completed`" in triage
    assert "| Prometheus target `sharelife-webui` | PASS |" in triage
    assert "| Grafana dashboard provisioning | PASS |" in triage
    assert triage_json["result"] == "PASS"
    assert triage_json["last_step"] == "completed"
    assert any(item["key"] == "prometheus_target_sharelife_up" and item["ok"] for item in triage_json["signals"])


def test_ops_smoke_triage_builder_marks_fail_and_includes_actions(tmp_path):
    artifacts = tmp_path / "ops-smoke"
    _write(
        artifacts / "summary.txt",
        "\n".join(
            [
                "timestamp_utc=2026-04-02T00:00:00Z",
                "exit_code=1",
                "last_step=wait_prometheus_health",
            ]
        )
        + "\n",
    )
    _write(artifacts / "http/webui-health.txt", "")
    _write(artifacts / "http/prom-health.txt", "")
    _write(artifacts / "http/grafana-health.json", "")
    _write(artifacts / "http/webui-metrics.txt", "")
    _write(artifacts / "http/prom-targets.json", "{}")
    _write(artifacts / "http/grafana-search.json", "[]")

    completed = subprocess.run(
        [
            "python3",
            "scripts/build_ops_smoke_triage.py",
            "--artifacts-dir",
            str(artifacts),
        ],
        cwd=REPO_ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    assert completed.returncode == 0, completed.stderr

    triage = (artifacts / "triage.md").read_text(encoding="utf-8")
    triage_json = json.loads((artifacts / "triage.json").read_text(encoding="utf-8"))
    assert "Result: **FAIL**" in triage
    assert "Last step: `wait_prometheus_health`" in triage
    assert "Suggested Triage Actions" in triage
    assert "compose/logs-all.txt" in triage
    assert triage_json["result"] == "FAIL"
    assert triage_json["last_step"] == "wait_prometheus_health"
    assert any(item["key"] == "prometheus_health" and (not item["ok"]) for item in triage_json["signals"])


def test_ops_smoke_triage_builder_includes_compose_and_fallback_guidance(tmp_path):
    artifacts = tmp_path / "ops-smoke"
    _write(
        artifacts / "summary.txt",
        "\n".join(
            [
                "timestamp_utc=2026-04-02T00:00:00Z",
                "exit_code=1",
                "last_step=compose_up",
                "requested_artifacts_dir=output/ops-smoke",
                "effective_artifacts_dir=/tmp/sharelife-ops-smoke.abcdef",
                "artifacts_dir_fallback=1",
                "requested_docker_data_dir=output/docker-data",
                "effective_docker_data_dir=/tmp/sharelife-ops-smoke-data.abcdef",
                "docker_data_dir_fallback=1",
                "requested_webui_host_port=8106",
                "requested_prom_host_port=9090",
                "requested_grafana_host_port=3000",
                "effective_webui_host_port=18106",
                "effective_prom_host_port=19090",
                "effective_grafana_host_port=13000",
            ]
        )
        + "\n",
    )
    _write(artifacts / "http/webui-health.txt", "")
    _write(artifacts / "http/prom-health.txt", "")
    _write(artifacts / "http/grafana-health.json", "")
    _write(artifacts / "http/webui-metrics.txt", "")
    _write(artifacts / "http/prom-targets.json", "{}")
    _write(artifacts / "http/grafana-search.json", "[]")

    completed = subprocess.run(
        [
            "python3",
            "scripts/build_ops_smoke_triage.py",
            "--artifacts-dir",
            str(artifacts),
        ],
        cwd=REPO_ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    assert completed.returncode == 0, completed.stderr

    triage = (artifacts / "triage.md").read_text(encoding="utf-8")
    triage_json = json.loads((artifacts / "triage.json").read_text(encoding="utf-8"))
    assert "Requested artifacts dir: `output/ops-smoke`" in triage
    assert "Effective artifacts dir: `/tmp/sharelife-ops-smoke.abcdef`" in triage
    assert "Artifacts dir fallback used: `yes`" in triage
    assert "Requested docker data dir: `output/docker-data`" in triage
    assert "Effective docker data dir: `/tmp/sharelife-ops-smoke-data.abcdef`" in triage
    assert "Docker data dir fallback used: `yes`" in triage
    assert "Requested host ports: `webui=8106 prom=9090 grafana=3000`" in triage
    assert "Effective host ports: `webui=18106 prom=19090 grafana=13000`" in triage
    assert any("compose startup conflicts" in item for item in triage_json["actions"])
    assert any("Artifact directory fallback was activated" in item for item in triage_json["actions"])
    assert any("Docker data directory fallback was activated" in item for item in triage_json["actions"])


def test_ops_smoke_triage_builder_includes_preflight_port_conflict_action(tmp_path):
    artifacts = tmp_path / "ops-smoke"
    _write(
        artifacts / "summary.txt",
        "\n".join(
            [
                "timestamp_utc=2026-04-02T00:00:00Z",
                "exit_code=1",
                "last_step=preflight_port_conflict",
            ]
        )
        + "\n",
    )
    _write(artifacts / "http/webui-health.txt", "")
    _write(artifacts / "http/prom-health.txt", "")
    _write(artifacts / "http/grafana-health.json", "")
    _write(artifacts / "http/webui-metrics.txt", "")
    _write(artifacts / "http/prom-targets.json", "{}")
    _write(artifacts / "http/grafana-search.json", "[]")

    completed = subprocess.run(
        [
            "python3",
            "scripts/build_ops_smoke_triage.py",
            "--artifacts-dir",
            str(artifacts),
        ],
        cwd=REPO_ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    assert completed.returncode == 0, completed.stderr

    triage_json = json.loads((artifacts / "triage.json").read_text(encoding="utf-8"))
    assert any("Free required host ports" in item for item in triage_json["actions"])


def test_ops_smoke_triage_builder_treats_curl_errors_as_unhealthy(tmp_path):
    artifacts = tmp_path / "ops-smoke"
    _write(
        artifacts / "summary.txt",
        "\n".join(
            [
                "timestamp_utc=2026-04-02T00:00:00Z",
                "exit_code=1",
                "last_step=wait_prometheus_health",
            ]
        )
        + "\n",
    )
    _write(artifacts / "http/webui-health.txt", "curl: (7) Failed to connect to 127.0.0.1 port 8106")
    _write(artifacts / "http/prom-health.txt", "curl: (7) Failed to connect to 127.0.0.1 port 9090")
    _write(artifacts / "http/grafana-health.json", "curl: (7) Failed to connect to 127.0.0.1 port 3000")
    _write(artifacts / "http/webui-metrics.txt", "curl: (7) Failed to connect")
    _write(artifacts / "http/prom-targets.json", "curl: (7) Failed to connect")
    _write(artifacts / "http/grafana-search.json", "curl: (7) Failed to connect")

    completed = subprocess.run(
        [
            "python3",
            "scripts/build_ops_smoke_triage.py",
            "--artifacts-dir",
            str(artifacts),
        ],
        cwd=REPO_ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    assert completed.returncode == 0, completed.stderr

    triage_json = json.loads((artifacts / "triage.json").read_text(encoding="utf-8"))
    checks = triage_json.get("checks", {})
    assert checks.get("webui_health") is False
    assert checks.get("prometheus_health") is False
    assert checks.get("grafana_health") is False


def test_ops_smoke_triage_builder_requires_security_alert_metric_in_surface_check(tmp_path):
    artifacts = tmp_path / "ops-smoke"
    _write(
        artifacts / "summary.txt",
        "\n".join(
            [
                "timestamp_utc=2026-04-02T00:00:00Z",
                "exit_code=1",
                "last_step=verify_webui_metrics",
            ]
        )
        + "\n",
    )
    _write(
        artifacts / "http/webui-metrics.txt",
        "\n".join(
            [
                "sharelife_webui_http_requests_total 1",
                "sharelife_webui_http_error_total 0",
                "sharelife_webui_auth_events_total 0",
                "sharelife_webui_rate_limit_total 0",
            ]
        ),
    )
    _write(artifacts / "http/webui-health.txt", '{"ok": true}')
    _write(artifacts / "http/prom-health.txt", "Prometheus is Healthy.\n")
    _write(artifacts / "http/grafana-health.json", '{"database":"ok"}')
    _write(
        artifacts / "http/prom-targets.json",
        json.dumps(
            {
                "status": "success",
                "data": {
                    "activeTargets": [
                        {
                            "labels": {"job": "sharelife-webui"},
                            "health": "up",
                        }
                    ]
                },
            }
        ),
    )
    _write(
        artifacts / "http/grafana-search.json",
        json.dumps([{"title": "Sharelife WebUI Observability"}]),
    )

    completed = subprocess.run(
        [
            "python3",
            "scripts/build_ops_smoke_triage.py",
            "--artifacts-dir",
            str(artifacts),
        ],
        cwd=REPO_ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    assert completed.returncode == 0, completed.stderr

    triage_json = json.loads((artifacts / "triage.json").read_text(encoding="utf-8"))
    checks = triage_json.get("checks", {})
    assert checks.get("webui_metrics_surface") is False
