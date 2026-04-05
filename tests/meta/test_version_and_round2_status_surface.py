from __future__ import annotations

import re
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]


def _extract(pattern: str, text: str, *, label: str) -> str:
    match = re.search(pattern, text, flags=re.DOTALL)
    assert match is not None, f"{label} not found"
    return str(match.group(1))


def test_plugin_metadata_and_webui_server_versions_are_aligned() -> None:
    main_text = (REPO_ROOT / "main.py").read_text(encoding="utf-8")
    webui_server_text = (REPO_ROOT / "sharelife" / "interfaces" / "webui_server.py").read_text(encoding="utf-8")
    metadata = yaml.safe_load((REPO_ROOT / "metadata.yaml").read_text(encoding="utf-8"))

    register_version = _extract(
        r'@register\(\s*"sharelife",[\s\S]*?\s*"([0-9]+\.[0-9]+\.[0-9]+)",\s*\)',
        main_text,
        label="register version",
    )
    profile_pack_plugin_version = _extract(
        r'plugin_version="([0-9]+\.[0-9]+\.[0-9]+)"',
        main_text,
        label="profile_pack plugin_version",
    )
    webui_version = _extract(
        r'FastAPI\([\s\S]*?version="([0-9]+\.[0-9]+\.[0-9]+)"',
        webui_server_text,
        label="webui FastAPI version",
    )

    metadata_version = str(metadata.get("version", "") or "").strip()
    assert metadata_version.startswith("v")
    assert metadata_version[1:] == register_version
    assert profile_pack_plugin_version == register_version
    assert webui_version == register_version


def test_round2_baseline_docs_pin_version_and_mark_m6_done() -> None:
    metadata = yaml.safe_load((REPO_ROOT / "metadata.yaml").read_text(encoding="utf-8"))
    metadata_version = str(metadata.get("version", "") or "").strip()
    assert metadata_version.startswith("v")

    cases = [
        (
            REPO_ROOT / "docs" / "zh" / "how-to" / "plugin-ecosystem-round2-baseline.md",
            "`M6` 完成",
            "进行中",
        ),
        (
            REPO_ROOT / "docs" / "en" / "how-to" / "plugin-ecosystem-round2-baseline.md",
            "`M6` done",
            "in progress",
        ),
        (
            REPO_ROOT / "docs" / "ja" / "how-to" / "plugin-ecosystem-round2-baseline.md",
            "`M6` 完了",
            "進行中",
        ),
    ]

    for path, done_marker, progress_marker in cases:
        text = path.read_text(encoding="utf-8")
        first_line = text.splitlines()[0] if text else ""
        assert metadata_version in first_line
        assert "`M6`" in text
        assert "plan -> confirm -> execute" in text
        assert done_marker in text
        assert progress_marker not in text
