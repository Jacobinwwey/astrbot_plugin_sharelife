from pathlib import Path
import json


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_conf_schema_exposes_state_store_backend_and_sqlite_file():
    payload = json.loads((REPO_ROOT / "_conf_schema.json").read_text(encoding="utf-8"))
    state_store = payload.get("state_store", {})
    assert isinstance(state_store, dict)
    assert state_store.get("type") == "object"
    items = state_store.get("items", {})
    assert "backend" in items
    assert "sqlite_file" in items
    assert "migrate_from_json" in items
    assert items["backend"]["default"] == "json"

    webui = payload.get("webui", {})
    assert isinstance(webui, dict)
    webui_items = webui.get("items", {})
    assert isinstance(webui_items, dict)
    observability = webui_items.get("observability", {})
    assert isinstance(observability, dict)
    assert observability.get("type") == "object"
    observability_items = observability.get("items", {})
    assert "metrics_max_paths" in observability_items
    assert "metrics_overflow_path_label" in observability_items
    assert "security_alert_window_seconds" in observability_items
    assert "security_alert_threshold" in observability_items
    assert "security_alert_cooldown_seconds" in observability_items


def test_config_template_documents_state_store_and_api_rate_limit():
    text = (REPO_ROOT / "config.template.yaml").read_text(encoding="utf-8")
    assert "state_store:" in text
    assert "backend: \"json\"" in text
    assert "sqlite_file:" in text
    assert "migrate_from_json: true" in text
    assert "api_rate_limit_window_seconds" in text
    assert "api_rate_limit_max_requests" in text
    assert "metrics_max_paths" in text
    assert "metrics_overflow_path_label" in text
    assert "security_alert_window_seconds" in text
    assert "security_alert_threshold" in text
    assert "security_alert_cooldown_seconds" in text
