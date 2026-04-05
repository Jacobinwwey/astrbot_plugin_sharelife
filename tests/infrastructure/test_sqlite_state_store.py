from pathlib import Path

from sharelife.infrastructure.sqlite_state_store import SqliteStateStore


def test_sqlite_state_store_loads_default_when_empty(tmp_path: Path) -> None:
    db_path = tmp_path / "state.sqlite3"
    store = SqliteStateStore(db_path, store_key="preferences")
    payload = store.load(default={"preferences": []})
    assert payload == {"preferences": []}


def test_sqlite_state_store_roundtrip_persists_payload(tmp_path: Path) -> None:
    db_path = tmp_path / "state.sqlite3"
    store = SqliteStateStore(db_path, store_key="market_state")
    source = {"submissions": [{"id": "sub-1", "status": "pending"}], "published": []}
    store.save(source)

    reloaded = SqliteStateStore(db_path, store_key="market_state").load(default={})
    assert reloaded == source


def test_sqlite_state_store_imports_legacy_json_once(tmp_path: Path) -> None:
    db_path = tmp_path / "state.sqlite3"
    legacy = tmp_path / "legacy.json"
    legacy.write_text('{"events": [{"id": "evt-1"}]}', encoding="utf-8")

    store = SqliteStateStore(db_path, store_key="audit_state")
    imported = store.import_from_json_file(legacy)
    assert imported is True
    assert store.load(default={}) == {"events": [{"id": "evt-1"}]}

    legacy.write_text('{"events": [{"id": "evt-2"}]}', encoding="utf-8")
    imported_again = store.import_from_json_file(legacy)
    assert imported_again is False
    assert store.load(default={}) == {"events": [{"id": "evt-1"}]}
