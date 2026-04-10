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
    secret_line = "admin_" + 'password = "realSecret42"'
    report = gate.evaluate_change_set(
        changed_paths=["docs/en/how-to/demo.md"],
        added_lines_by_path={
            "docs/en/how-to/demo.md": [
                (12, secret_line),
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


def test_promotion_gate_blocks_gitlink_mode_entries() -> None:
    gate = _load_gate_module()
    report = gate.evaluate_change_set(
        changed_paths=["ref/AstrBot"],
        added_lines_by_path={},
        changed_entries=[
            {
                "path": "ref/AstrBot",
                "old_path": "",
                "status": "A",
                "old_mode": "000000",
                "new_mode": "160000",
            }
        ],
        projection_manifest={
            "include": ["sharelife/**", "docs/**", "tests/**"],
            "exclude": ["ref/**"],
        },
    )
    assert report["promotable"] is False
    rules = {item["rule"] for item in report["blocked_paths"]}
    assert "gitlink_mode_block" in rules


def test_promotion_gate_blocks_added_paths_outside_projection_manifest_allowlist() -> None:
    gate = _load_gate_module()
    manifest = {
        "include": ["sharelife/**", "docs/**", "tests/**"],
        "exclude": ["docs/private/**", "ref/**"],
    }
    blocked = gate.evaluate_change_set(
        changed_paths=["tmp/new-notes.md"],
        added_lines_by_path={},
        changed_entries=[
            {
                "path": "tmp/new-notes.md",
                "old_path": "",
                "status": "A",
                "old_mode": "000000",
                "new_mode": "100644",
            }
        ],
        projection_manifest=manifest,
    )
    assert blocked["promotable"] is False
    assert any(item["rule"] == "manifest_path_not_projectable" for item in blocked["blocked_paths"])

    allowed = gate.evaluate_change_set(
        changed_paths=["sharelife/webui/market_page.js"],
        added_lines_by_path={},
        changed_entries=[
            {
                "path": "sharelife/webui/market_page.js",
                "old_path": "",
                "status": "A",
                "old_mode": "000000",
                "new_mode": "100644",
            }
        ],
        projection_manifest=manifest,
    )
    assert allowed["promotable"] is True
