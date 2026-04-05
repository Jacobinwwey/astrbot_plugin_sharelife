from __future__ import annotations

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _run_redactor(source: Path, *, mode: str) -> str:
    out = source.parent / f"{source.stem}.{mode}.txt"
    completed = subprocess.run(
        [
            "python3",
            "scripts/redact_ops_artifacts.py",
            "--input",
            str(source),
            "--output",
            str(out),
            "--mode",
            mode,
        ],
        cwd=REPO_ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    assert completed.returncode == 0, completed.stderr
    return out.read_text(encoding="utf-8")


def test_ops_artifact_redaction_masks_secrets_ips_and_home_paths(tmp_path):
    source = tmp_path / "artifact.txt"
    _write(
        source,
        "\n".join(
            [
                "api_key=sk-test-abc",
                "Authorization: Bearer tok_live_123",
                "url=http://alice:pwd123@192.168.10.3:3000/api/search?token=abc&lang=en",
                'payload={"token":"tok-1","password":"pwd-2","job":"sharelife-webui"}',
                "home=/root/astrbot_plugin_sharelife/output/ops-smoke",
                "loopback=http://127.0.0.1:8106/api/health",
                "container=sharelife-webui:8106",
            ]
        )
        + "\n",
    )

    redacted = _run_redactor(source, mode="strict")
    assert "sk-test-abc" not in redacted
    assert "tok_live_123" not in redacted
    assert "pwd123" not in redacted
    assert "tok-1" not in redacted
    assert "pwd-2" not in redacted
    assert "192.168.10.3" not in redacted
    assert "/root/astrbot_plugin_sharelife" not in redacted

    assert "<redacted>" in redacted
    assert "<redacted-token>" in redacted or "<redacted-auth>" in redacted
    assert "<redacted-ip>" in redacted
    assert "<redacted-home-path>" in redacted
    assert "127.0.0.1:8106" in redacted
    assert "sharelife-webui:8106" in redacted


def test_ops_artifact_redaction_off_mode_keeps_original_content(tmp_path):
    source = tmp_path / "artifact.txt"
    original = "api_key=sk-test-abc\nurl=http://192.168.10.3:8106/api?token=abc\n"
    _write(source, original)
    off = _run_redactor(source, mode="off")
    assert off == original
