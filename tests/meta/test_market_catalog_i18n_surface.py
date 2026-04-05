from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def _key_occurrence(text: str, key: str) -> int:
    quoted_single = f"'{key}':"
    quoted_double = f'"{key}":'
    plain = f"{key}:"
    return text.count(quoted_single) + text.count(quoted_double) + text.count(plain)


def test_market_catalog_component_covers_public_profile_pack_taxonomy_in_i18n_maps():
    snapshot = json.loads(
        (REPO_ROOT / "docs" / "public" / "market" / "catalog.snapshot.json").read_text(encoding="utf-8")
    )
    rows = snapshot.get("rows", [])
    pack_types: set[str] = set()
    risks: set[str] = set()
    sources: set[str] = set()
    labels: set[str] = set()
    for item in rows:
        if not isinstance(item, dict):
            continue
        pack_type = str(item.get("pack_type", "") or "").strip()
        risk = str(item.get("risk_level", "") or "").strip()
        source = str(item.get("source_channel", "") or "").strip()
        if pack_type:
            pack_types.add(pack_type)
        if risk:
            risks.add(risk)
        if source:
            sources.add(source)
        for tag in item.get("review_labels", []) or []:
            text = str(tag or "").strip()
            if text:
                labels.add(text)

    component_text = (
        REPO_ROOT / "docs" / ".vitepress" / "theme" / "components" / "MarketCatalogPrototype.vue"
    ).read_text(encoding="utf-8")

    for pack_type in pack_types:
        assert _key_occurrence(component_text, pack_type) >= 3

    for risk in risks:
        assert _key_occurrence(component_text, risk) >= 3

    for source in sources:
        assert _key_occurrence(component_text, source) >= 3

    for label in labels:
        assert _key_occurrence(component_text, label) >= 3
