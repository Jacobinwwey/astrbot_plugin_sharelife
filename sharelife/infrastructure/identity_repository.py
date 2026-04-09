"""Repository implementations for identity, credentials, sessions, and reviewer devices."""

from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Any, Protocol


class IdentityRepository(Protocol):
    """Identity storage contract used by reviewer/session services."""

    def load_state(self) -> dict[str, list[dict[str, Any]]]:
        ...

    def save_state(self, payload: dict[str, list[dict[str, Any]]]) -> None:
        ...


class KeyValueStateStore(Protocol):
    """Minimal state-store protocol shared by JSON and legacy sqlite key-value stores."""

    def load(self, default: dict[str, Any]) -> dict[str, Any]:
        ...

    def save(self, payload: dict[str, Any]) -> None:
        ...


_DEFAULT_STATE: dict[str, list[dict[str, Any]]] = {
    "users": [],
    "credentials": [],
    "sessions": [],
    "reviewer_devices": [],
    "reviewer_invites": [],
}

_TABLES: tuple[tuple[str, str, str], ...] = (
    ("users", "sharelife_identity_users", "user_id"),
    ("credentials", "sharelife_identity_credentials", "credential_id"),
    ("sessions", "sharelife_identity_sessions", "session_id"),
    ("reviewer_devices", "sharelife_identity_reviewer_devices", "device_id"),
    ("reviewer_invites", "sharelife_identity_reviewer_invites", "code"),
)


class JsonIdentityRepository:
    """JSON state-store backed identity repository."""

    def __init__(self, state_store: KeyValueStateStore):
        self.state_store = state_store

    def load_state(self) -> dict[str, list[dict[str, Any]]]:
        payload = self.state_store.load(default=_DEFAULT_STATE)
        return {
            key: list(payload.get(key, [])) if isinstance(payload.get(key), list) else []
            for key in _DEFAULT_STATE
        }

    def save_state(self, payload: dict[str, list[dict[str, Any]]]) -> None:
        self.state_store.save(
            {
                key: list(payload.get(key, []))
                for key in _DEFAULT_STATE
            }
        )


class SqliteIdentityRepository:
    """SQLite repository with dedicated identity tables."""

    def __init__(self, db_path: Path | str):
        self.db_path = Path(db_path)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.db_path), timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA busy_timeout=30000")
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            try:
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("PRAGMA synchronous=NORMAL")
            except sqlite3.OperationalError:
                pass
            for _collection, table, _id_field in _TABLES:
                conn.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS {table} (
                        row_id TEXT PRIMARY KEY,
                        payload_json TEXT NOT NULL,
                        updated_at REAL NOT NULL
                    )
                    """
                )
            conn.commit()

    @staticmethod
    def _decode_rows(rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for row in rows:
            raw = str(row["payload_json"] or "").strip()
            if not raw:
                continue
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                out.append(payload)
        return out

    def load_state(self) -> dict[str, list[dict[str, Any]]]:
        out: dict[str, list[dict[str, Any]]] = {key: [] for key in _DEFAULT_STATE}
        with self._connect() as conn:
            for collection, table, _id_field in _TABLES:
                rows = conn.execute(
                    f"SELECT payload_json FROM {table} ORDER BY updated_at ASC, row_id ASC"
                ).fetchall()
                out[collection] = self._decode_rows(rows)
        return out

    def save_state(self, payload: dict[str, list[dict[str, Any]]]) -> None:
        now = float(time.time())
        with self._connect() as conn:
            for collection, table, id_field in _TABLES:
                rows = payload.get(collection, [])
                conn.execute(f"DELETE FROM {table}")
                if not isinstance(rows, list):
                    continue
                for item in rows:
                    if not isinstance(item, dict):
                        continue
                    row_id = str(item.get(id_field, "") or "").strip()
                    if not row_id:
                        continue
                    conn.execute(
                        f"INSERT INTO {table}(row_id, payload_json, updated_at) VALUES(?, ?, ?)",
                        (
                            row_id,
                            json.dumps(item, ensure_ascii=False, sort_keys=True),
                            now,
                        ),
                    )
            conn.commit()
