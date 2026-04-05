from __future__ import annotations

import json
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_ops_smoke_annotations_emit_notice_for_pass(tmp_path):
    triage_path = tmp_path / "triage.json"
    _write(
        triage_path,
        json.dumps(
            {
                "result": "PASS",
                "exit_code": 0,
                "last_step": "completed",
                "signals": [],
                "actions": [],
            }
        ),
    )
    completed = subprocess.run(
        [
            "python3",
            "scripts/publish_ops_smoke_annotations.py",
            "--triage-json",
            str(triage_path),
        ],
        cwd=REPO_ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    assert completed.returncode == 0
    assert "::notice title=ops-smoke::PASS" in completed.stdout


def test_ops_smoke_annotations_emit_errors_and_warnings_for_fail(tmp_path):
    triage_path = tmp_path / "triage.json"
    _write(
        triage_path,
        json.dumps(
            {
                "result": "FAIL",
                "exit_code": 1,
                "last_step": "verify_prometheus_target",
                "signals": [
                    {"key": "webui_health", "label": "WebUI `/api/health`", "ok": True},
                    {"key": "prometheus_target_sharelife_up", "label": "Prometheus target `sharelife-webui`", "ok": False},
                ],
                "actions": ["Open `http/prom-targets.json`; verify scrape target and reachability."],
            }
        ),
    )
    completed = subprocess.run(
        [
            "python3",
            "scripts/publish_ops_smoke_annotations.py",
            "--triage-json",
            str(triage_path),
        ],
        cwd=REPO_ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    assert completed.returncode == 0
    assert "::error title=ops-smoke::FAIL" in completed.stdout
    assert "ops-smoke-signal" in completed.stdout
    assert "ops-smoke-action" in completed.stdout
