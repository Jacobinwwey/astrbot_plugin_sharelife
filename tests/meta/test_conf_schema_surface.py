import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def _collect_object_nodes_missing_items(field: dict, field_path: str) -> list[str]:
    if not isinstance(field, dict):
        return []

    missing: list[str] = []
    if field.get("type") == "object":
        if "items" not in field:
            missing.append(field_path)
            return missing
        items = field.get("items")
        if not isinstance(items, dict):
            missing.append(field_path)
            return missing
        for child_name, child_field in items.items():
            child_path = f"{field_path}.{child_name}"
            missing.extend(_collect_object_nodes_missing_items(child_field, child_path))
    return missing


def test_conf_schema_object_fields_always_define_items():
    schema = json.loads((REPO_ROOT / "_conf_schema.json").read_text(encoding="utf-8"))

    missing_paths: list[str] = []
    for name, field in schema.items():
        missing_paths.extend(_collect_object_nodes_missing_items(field, name))

    assert missing_paths == []


def test_profile_pack_trusted_signing_keys_has_object_items_map_shape():
    schema = json.loads((REPO_ROOT / "_conf_schema.json").read_text(encoding="utf-8"))
    trusted = schema["profile_pack"]["items"]["trusted_signing_keys"]

    assert trusted["type"] == "object"
    assert trusted["items"] == {}
    assert trusted["default"] == {}
