from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_repo_ships_bundled_official_templates_index() -> None:
    index_path = REPO_ROOT / "templates" / "index.json"

    assert index_path.exists()

    payload = json.loads(index_path.read_text(encoding="utf-8"))
    templates = payload.get("templates", [])

    assert len(templates) >= 6
    assert any(item.get("template_id") == "community/basic" for item in templates)
    assert any(item.get("template_id") == "community/writing-polish" for item in templates)
    assert any(item.get("template_id") == "community/coding-review" for item in templates)

    basic = next(item for item in templates if item.get("template_id") == "community/basic")
    assert basic["version"] == "1.0.0"
    assert basic["title_i18n"]["zh-CN"]
    assert basic["title_i18n"]["en-US"]
    assert basic["prompt_template"]
    assert basic["category"] == "general"
    assert basic["maintainer"] == "Sharelife"
    assert basic["source_channel"] == "bundled_official"
    assert "strict-mode" in " ".join(basic["tags"])
