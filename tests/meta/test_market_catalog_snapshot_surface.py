from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_market_catalog_snapshot_exists_and_exposes_rows():
    snapshot_path = REPO_ROOT / "docs" / "public" / "market" / "catalog.snapshot.json"
    assert snapshot_path.exists()

    payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
    assert payload.get("schema_version") == "v1"
    rows = payload.get("rows")
    assert isinstance(rows, list)
    assert len(rows) >= 1

    first = rows[0]
    assert isinstance(first.get("pack_id"), str)
    assert isinstance(first.get("version"), str)
    assert isinstance(first.get("package_path"), str)


def test_market_catalog_snapshot_matches_public_profile_pack_artifacts():
    snapshot_path = REPO_ROOT / "docs" / "public" / "market" / "catalog.snapshot.json"

    snapshot_payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
    rows = snapshot_payload.get("rows", [])
    snapshot_keys = set()

    for item in rows:
        pack_id = str(item.get("pack_id", "") or "").strip()
        version = str(item.get("version", "") or "").strip()
        assert pack_id
        assert version
        snapshot_keys.add((pack_id, version))
        package_path = str(item.get("package_path", "") or "")
        assert package_path.startswith("/market/packages/")
        demo_path = REPO_ROOT / "docs" / "public" / package_path.lstrip("/")
        assert demo_path.exists()
    assert snapshot_keys >= {
        ("profile/official-starter", "1.0.1"),
        ("profile/official-safe-reference", "1.0.1"),
    }


def test_docs_build_script_prepares_market_snapshot():
    package_json_path = REPO_ROOT / "docs" / "package.json"
    scripts = json.loads(package_json_path.read_text(encoding="utf-8")).get("scripts", {})

    prepare_script = scripts.get("docs:prepare:market", "")
    build_script = scripts.get("docs:build", "")
    assert "build_market_snapshot.py" in prepare_script
    assert "docs:prepare:market" in build_script


def test_build_market_snapshot_script_stays_docs_build_compatible():
    script_text = (REPO_ROOT / "scripts" / "build_market_snapshot.py").read_text(encoding="utf-8")

    assert "sharelife.application.services_profile_pack_bootstrap" not in script_text
    assert "sharelife.domain.profile_pack_models" not in script_text


def test_market_catalog_component_prefers_snapshot_with_fallback_rows():
    component_path = REPO_ROOT / "docs" / ".vitepress" / "theme" / "components" / "MarketCatalogPrototype.vue"
    text = component_path.read_text(encoding="utf-8")

    assert "fetch(withBase('/market/catalog.snapshot.json')" in text
    assert "const fallbackRows" in text
    assert "const rows = ref<Row[]>(fallbackRows)" in text
    assert "profile/official-starter" in text
