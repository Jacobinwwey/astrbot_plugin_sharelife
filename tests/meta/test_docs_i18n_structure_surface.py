from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS_ROOT = REPO_ROOT / "docs"
LOCALES = ("zh", "en", "ja")


def _config_locale_links() -> set[str]:
    config_text = (DOCS_ROOT / ".vitepress" / "config.ts").read_text(encoding="utf-8")
    return set(re.findall(r"link:\s*'(/(?:zh|en|ja)(?:/[^']*)?)'", config_text))


def _route_exists(route: str) -> bool:
    relative = route.lstrip("/")
    markdown_path = DOCS_ROOT / f"{relative}.md"
    index_path = DOCS_ROOT / relative / "index.md"
    return markdown_path.exists() or index_path.exists()


def _locale_public_doc_set(locale: str) -> set[str]:
    locale_root = DOCS_ROOT / locale
    docs: set[str] = set()
    for path in locale_root.rglob("*.md"):
        rel = path.relative_to(locale_root).as_posix()
        if rel.startswith("private/"):
            continue
        docs.add(rel)
    return docs


def _locale_private_doc_set(locale: str) -> set[str]:
    locale_private_root = DOCS_ROOT / locale / "private"
    if not locale_private_root.exists():
        return set()
    return {
        path.relative_to(locale_private_root).as_posix()
        for path in locale_private_root.rglob("*.md")
        if path.is_file()
    }


def test_locale_sidebar_links_resolve_to_existing_docs_pages():
    missing = sorted(route for route in _config_locale_links() if not _route_exists(route))
    assert not missing, f"sidebar links point to missing docs pages: {missing}"


def test_public_docs_follow_trilingual_structure_parity():
    locale_sets = {locale: _locale_public_doc_set(locale) for locale in LOCALES}
    baseline = locale_sets["zh"]
    assert locale_sets["en"] == baseline, (
        "public docs parity mismatch between zh and en. "
        f"zh-only={sorted(baseline - locale_sets['en'])}, "
        f"en-only={sorted(locale_sets['en'] - baseline)}"
    )
    assert locale_sets["ja"] == baseline, (
        "public docs parity mismatch between zh and ja. "
        f"zh-only={sorted(baseline - locale_sets['ja'])}, "
        f"ja-only={sorted(locale_sets['ja'] - baseline)}"
    )


def test_private_docs_follow_trilingual_structure_parity_when_portal_enabled():
    locale_sets = {locale: _locale_private_doc_set(locale) for locale in LOCALES}
    if not any(locale_sets.values()):
        return
    baseline = locale_sets["zh"]
    assert locale_sets["en"] == baseline, (
        "private docs parity mismatch between zh and en. "
        f"zh-only={sorted(baseline - locale_sets['en'])}, "
        f"en-only={sorted(locale_sets['en'] - baseline)}"
    )
    assert locale_sets["ja"] == baseline, (
        "private docs parity mismatch between zh and ja. "
        f"zh-only={sorted(baseline - locale_sets['ja'])}, "
        f"ja-only={sorted(locale_sets['ja'] - baseline)}"
    )
