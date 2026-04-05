from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_public_market_docs_do_not_expose_privileged_api_or_commands():
    files = [
        REPO_ROOT / "docs" / "en" / "how-to" / "market-public-hub.md",
        REPO_ROOT / "docs" / "zh" / "how-to" / "market-public-hub.md",
        REPO_ROOT / "docs" / "ja" / "how-to" / "market-public-hub.md",
        REPO_ROOT / "docs" / ".vitepress" / "theme" / "components" / "MarketCatalogPrototype.vue",
    ]
    forbidden_tokens = [
        "/api/admin",
        "sharelife_apply",
        "sharelife_submission_decide",
        "sharelife_profile_import",
        "sharelife_profile_plugins_confirm",
    ]

    for file_path in files:
        text = file_path.read_text(encoding="utf-8")
        for token in forbidden_tokens:
            assert token not in text
