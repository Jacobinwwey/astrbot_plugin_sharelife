from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
WEBUI_I18N_PATH = REPO_ROOT / "sharelife" / "webui" / "webui_i18n.js"
DETAIL_PANEL_PATH = REPO_ROOT / "sharelife" / "webui" / "detail_panel.js"
APP_JS_PATH = REPO_ROOT / "sharelife" / "webui" / "app.js"
WEBUI_HTML_PATHS = [
    REPO_ROOT / "sharelife" / "webui" / "index.html",
    REPO_ROOT / "sharelife" / "webui" / "member.html",
    REPO_ROOT / "sharelife" / "webui" / "admin.html",
    REPO_ROOT / "sharelife" / "webui" / "market.html",
]
_LOCALES = ("en-US", "zh-CN", "ja-JP")


def _extract_locale_keys(text: str, locale: str) -> set[str]:
    marker = f'"{locale}": {{'
    start = text.find(marker)
    assert start >= 0, f"locale block not found: {locale}"

    end = text.find("\n  }\n\n  function normalizeLocale", start)
    assert end >= 0, "normalizeLocale boundary not found"

    for sibling_locale in _LOCALES:
        if sibling_locale == locale:
            continue
        sibling_marker = f'"{sibling_locale}": {{'
        sibling_start = text.find(sibling_marker, start + len(marker))
        if sibling_start >= 0:
            end = min(end, sibling_start)

    block = text[start:end]
    return {match.group(1) for match in re.finditer(r'"([^"\\]+)"\s*:', block)}


def _html_i18n_keys(text: str) -> set[str]:
    keys = set(re.findall(r'data-i18n-key="([^"]+)"', text))
    keys.update(re.findall(r'data-i18n-placeholder-key="([^"]+)"', text))
    return keys


def _html_i18n_key_locations(html_path: Path, text: str) -> dict[str, list[str]]:
    locations: dict[str, list[str]] = {}
    pattern = re.compile(r'data-i18n(?:-placeholder)?-key="([^"]+)"')
    for line_number, line in enumerate(text.splitlines(), start=1):
        for match in pattern.finditer(line):
            key = match.group(1)
            locations.setdefault(key, []).append(f"{html_path.name}:{line_number}")
    return locations


def _js_i18n_key_locations(js_path: Path, text: str) -> dict[str, list[str]]:
    locations: dict[str, list[str]] = {}
    pattern = re.compile(r'\b(?:groupKey|titleKey|descriptionKey)\s*:\s*"([^"]+)"')
    for line_number, line in enumerate(text.splitlines(), start=1):
        for match in pattern.finditer(line):
            key = match.group(1)
            locations.setdefault(key, []).append(f"{js_path.name}:{line_number}")
    return locations


def _js_i18n_call_key_locations(js_path: Path, text: str) -> dict[str, list[str]]:
    locations: dict[str, list[str]] = {}
    pattern = re.compile(r'\bi18n(?:Message|Format)\(\s*"([^"]+)"')
    for line_number, line in enumerate(text.splitlines(), start=1):
        for match in pattern.finditer(line):
            key = match.group(1)
            locations.setdefault(key, []).append(f"{js_path.name}:{line_number}")
    return locations


def _render_missing_key_snapshot(
    locale: str,
    missing_keys: list[str],
    key_locations: dict[str, list[str]],
) -> str:
    lines = [f"[{locale}] missing {len(missing_keys)} keys"]
    for key in missing_keys:
        refs = ", ".join(key_locations.get(key, ["unknown"]))
        lines.append(f"- {key} <- {refs}")
    return "\n".join(lines)


def _missing_placeholder_key_tags(text: str) -> list[str]:
    missing: list[str] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        tags = re.findall(r"<input\b[^>]*\bplaceholder=\"[^\"]*\"[^>]*>", line)
        missing.extend(
            f"L{line_number}: {tag}"
            for tag in tags
            if 'data-i18n-placeholder-key="' not in tag
        )
    return missing


def _missing_option_key_tags(text: str) -> list[str]:
    missing: list[str] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        tags = re.findall(r"<option\b[^>]*>[^<]*</option>", line)
        missing.extend(
            f"L{line_number}: {tag}" for tag in tags if 'data-i18n-key="' not in tag
        )
    return missing


def test_webui_html_placeholders_and_options_are_explicitly_i18n_keyed() -> None:
    for html_path in WEBUI_HTML_PATHS:
        text = html_path.read_text(encoding="utf-8")
        missing_placeholders = _missing_placeholder_key_tags(text)
        missing_options = _missing_option_key_tags(text)
        assert not missing_placeholders, (
            f"{html_path.name} has placeholder inputs without data-i18n-placeholder-key: "
            + ", ".join(missing_placeholders[:5])
        )
        assert not missing_options, (
            f"{html_path.name} has options without data-i18n-key: "
            + ", ".join(missing_options[:5])
        )


def test_webui_html_i18n_keys_exist_in_all_supported_locales() -> None:
    i18n_text = WEBUI_I18N_PATH.read_text(encoding="utf-8")
    locale_keys = {locale: _extract_locale_keys(i18n_text, locale) for locale in _LOCALES}

    used_key_locations: dict[str, list[str]] = {}
    for html_path in WEBUI_HTML_PATHS:
        text = html_path.read_text(encoding="utf-8")
        for key, locations in _html_i18n_key_locations(html_path, text).items():
            used_key_locations.setdefault(key, []).extend(locations)
    used_keys = set(used_key_locations)

    snapshots: list[str] = []
    for locale in _LOCALES:
        missing = sorted(key for key in used_keys if key not in locale_keys[locale])
        if missing:
            snapshots.append(
                _render_missing_key_snapshot(locale, missing, used_key_locations)
            )

    assert not snapshots, (
        "webui i18n key coverage mismatch.\n"
        "Missing keys snapshot (key <- file:line):\n"
        + "\n\n".join(snapshots)
    )


def test_webui_risk_glossary_i18n_keys_exist_in_all_supported_locales() -> None:
    i18n_text = WEBUI_I18N_PATH.read_text(encoding="utf-8")
    locale_keys = {locale: _extract_locale_keys(i18n_text, locale) for locale in _LOCALES}

    detail_panel_text = DETAIL_PANEL_PATH.read_text(encoding="utf-8")
    key_locations = _js_i18n_key_locations(DETAIL_PANEL_PATH, detail_panel_text)
    used_keys = set(key_locations)

    snapshots: list[str] = []
    for locale in _LOCALES:
        missing = sorted(key for key in used_keys if key not in locale_keys[locale])
        if missing:
            snapshots.append(
                _render_missing_key_snapshot(locale, missing, key_locations)
            )

    assert not snapshots, (
        "webui risk glossary i18n key coverage mismatch.\n"
        "Missing keys snapshot (key <- file:line):\n"
        + "\n\n".join(snapshots)
    )


def test_webui_profile_pack_runtime_i18n_keys_exist_in_all_supported_locales() -> None:
    i18n_text = WEBUI_I18N_PATH.read_text(encoding="utf-8")
    locale_keys = {locale: _extract_locale_keys(i18n_text, locale) for locale in _LOCALES}

    app_text = APP_JS_PATH.read_text(encoding="utf-8")
    key_locations = _js_i18n_call_key_locations(APP_JS_PATH, app_text)
    used_keys = sorted(
        key
        for key in key_locations
        if key.startswith("profile_pack.review.")
        or key.startswith("profile_pack.compatibility.")
        or key.startswith("profile_pack.action.shortcut.")
        or key in {
            "profile_pack.issue.section_hash_mismatch_with_section",
            "profile_pack.section.badge.stateful",
            "profile_pack.section.badge.local_data",
        }
    )

    snapshots: list[str] = []
    for locale in _LOCALES:
        missing = sorted(key for key in used_keys if key not in locale_keys[locale])
        if missing:
            snapshots.append(
                _render_missing_key_snapshot(locale, missing, key_locations)
            )

    assert not snapshots, (
        "webui profile-pack runtime i18n key coverage mismatch.\n"
        "Missing keys snapshot (key <- file:line):\n"
        + "\n\n".join(snapshots)
    )
