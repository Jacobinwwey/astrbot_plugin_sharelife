from __future__ import annotations

import json
import re
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
_CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")


def _contains_cjk(text: str) -> bool:
    return bool(_CJK_RE.search(text or ""))


def _iter_descriptions(node: object) -> list[str]:
    values: list[str] = []
    if isinstance(node, dict):
        description = node.get("description")
        if isinstance(description, str):
            values.append(description)
        for value in node.values():
            values.extend(_iter_descriptions(value))
    elif isinstance(node, list):
        for value in node:
            values.extend(_iter_descriptions(value))
    return values


def test_plugin_metadata_display_text_is_chinese_first() -> None:
    metadata = yaml.safe_load((REPO_ROOT / "metadata.yaml").read_text(encoding="utf-8"))

    assert _contains_cjk(str(metadata.get("display_name", "") or ""))
    assert _contains_cjk(str(metadata.get("desc", "") or ""))


def test_register_description_is_chinese_first() -> None:
    main_text = (REPO_ROOT / "main.py").read_text(encoding="utf-8")
    match = re.search(
        r'@register\(\s*"sharelife",\s*"[^"]+",\s*"([^"]+)",\s*"([0-9]+\.[0-9]+\.[0-9]+)",',
        main_text,
    )
    assert match is not None
    assert _contains_cjk(match.group(1))


def test_conf_schema_descriptions_are_chinese_first() -> None:
    schema = json.loads((REPO_ROOT / "_conf_schema.json").read_text(encoding="utf-8"))
    descriptions = _iter_descriptions(schema)

    assert descriptions
    assert all(_contains_cjk(text) for text in descriptions)
