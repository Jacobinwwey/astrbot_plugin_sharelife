from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "check_public_promotion_gate.py"


def _load_gate_module():
    spec = importlib.util.spec_from_file_location("promotion_gate", SCRIPT_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_promotion_gate_blocks_private_paths() -> None:
    gate = _load_gate_module()
    changed = [
        "docs/zh/private/index.md",
        "docs/private/index.md",
        "output/standalone-data/secrets/webui-auth.local.toml",
        "docs/en/reference/api-v1.md",
    ]
    report = gate.evaluate_change_set(changed, {})
    blocked_paths = {item["path"] for item in report["blocked_paths"]}

    assert report["promotable"] is False
    assert "docs/zh/private/index.md" in blocked_paths
    assert "docs/private/index.md" in blocked_paths
    assert "output/standalone-data/secrets/webui-auth.local.toml" in blocked_paths
    assert "docs/en/reference/api-v1.md" not in blocked_paths


def test_promotion_gate_blocks_inline_secret_but_allows_marked_redacted_line() -> None:
    gate = _load_gate_module()
    report = gate.evaluate_change_set(
        changed_paths=["docs/en/how-to/demo.md"],
        added_lines_by_path={
            "docs/en/how-to/demo.md": [
                (12, 'admin_password = "realSecret42"'),
                (13, 'passphrase = "<redacted>" # promotion:allow'),
            ]
        },
    )

    assert report["promotable"] is False
    blocked = report["blocked_content"]
    assert len(blocked) == 1
    assert blocked[0]["path"] == "docs/en/how-to/demo.md"
    assert blocked[0]["line_no"] == 12
    assert blocked[0]["rule"] == "inline_auth_secret"


def test_promotion_gate_cli_passes_for_empty_diff_and_writes_json(tmp_path: Path) -> None:
    output_path = tmp_path / "gate-report.json"
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--from-ref",
            "HEAD",
            "--to-ref",
            "HEAD",
            "--json-output",
            str(output_path),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "[promotion-gate] PASS" in result.stdout
    report = json.loads(output_path.read_text(encoding="utf-8"))
    assert report["promotable"] is True
    assert report["status"] == "PASS"
    assert report["comparison_mode"] == "merge-base"
    assert report["changed_files_count"] == 0
