import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_conf_schema_exposes_webui_security_headers_block():
    schema = json.loads((REPO_ROOT / "_conf_schema.json").read_text(encoding="utf-8"))
    webui = schema.get("webui", {})
    items = webui.get("items", {}) if isinstance(webui, dict) else {}
    security_headers = items.get("security_headers", {})
    security_items = security_headers.get("items", {}) if isinstance(security_headers, dict) else {}

    assert security_headers.get("type") == "object"
    assert "enabled" in security_items
    assert "X-Content-Type-Options" in security_items
    assert "X-Frame-Options" in security_items
    assert "Referrer-Policy" in security_items
    assert "Permissions-Policy" in security_items
    assert "Content-Security-Policy" in security_items


def test_config_template_includes_security_headers_examples():
    text = (REPO_ROOT / "config.template.yaml").read_text(encoding="utf-8")

    assert "security_headers:" in text
    assert "X-Content-Type-Options" in text
    assert "X-Frame-Options" in text
    assert "Referrer-Policy" in text
    assert "Permissions-Policy" in text
    assert "Content-Security-Policy" in text


def test_webui_docs_mention_security_headers_in_all_locales():
    for locale in ("en", "zh", "ja"):
        text = (REPO_ROOT / "docs" / locale / "how-to" / "webui-page.md").read_text(
            encoding="utf-8"
        )
        assert "security_headers" in text
        assert "Content-Security-Policy" in text

