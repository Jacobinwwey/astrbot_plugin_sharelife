"""Repository implementations for preference state."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Protocol


class PreferenceRepository(Protocol):
    """Storage contract used by PreferenceService."""

    def load_state(self) -> dict[str, list[dict[str, Any]]]:
        ...

    def save_state(self, payload: dict[str, list[dict[str, Any]]]) -> None:
        ...


class KeyValueStateStore(Protocol):
    def load(self, default: dict[str, Any]) -> dict[str, Any]:
        ...

    def save(self, payload: dict[str, Any]) -> None:
        ...


class JsonPreferenceRepository:
    def __init__(self, state_store: KeyValueStateStore):
        self.state_store = state_store

    def load_state(self) -> dict[str, list[dict[str, Any]]]:
        payload = self.state_store.load(default={"preferences": []})
        values = payload.get("preferences", [])
        return {"preferences": values if isinstance(values, list) else []}

    def save_state(self, payload: dict[str, list[dict[str, Any]]]) -> None:
        self.state_store.save({"preferences": list(payload.get("preferences", []))})


class SqlitePreferenceRepository:
    def __init__(
        self,
        db_path: Path | str,
        *,
        legacy_state_store: KeyValueStateStore | None = None,
    ):
        self.db_path = Path(db_path)
        self._init_db()
        if legacy_state_store is not None:
            legacy_payload = legacy_state_store.load(default={"preferences": []})
            self.import_legacy_payload(legacy_payload)

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
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sharelife_preferences (
                    user_id TEXT PRIMARY KEY,
                    execution_mode TEXT NOT NULL,
                    observe_task_details INTEGER NOT NULL,
                    payload_json TEXT NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_preferences_execution_mode ON sharelife_preferences(execution_mode)"
            )
            conn.commit()

    def _table_empty(self, conn: sqlite3.Connection) -> bool:
        row = conn.execute("SELECT COUNT(1) AS c FROM sharelife_preferences").fetchone()
        return int(row["c"] if row is not None else 0) == 0

    @staticmethod
    def _encode_json(value: Any) -> str:
        return json.dumps(value, ensure_ascii=False)

    @staticmethod
    def _decode_json(raw: str | None, default: Any) -> Any:
        if raw in (None, ""):
            return default
        try:
            out = json.loads(raw)
        except json.JSONDecodeError:
            return default
        return out if out is not None else default

    def import_legacy_payload(self, payload: dict[str, Any]) -> bool:
        if not isinstance(payload, dict):
            return False
        preferences = payload.get("preferences", [])
        if not isinstance(preferences, list) or not preferences:
            return False

        with self._connect() as conn:
            if not self._table_empty(conn):
                return False
            self._replace_state_in_tx(conn, preferences=preferences)
            conn.commit()
        return True

    def load_state(self) -> dict[str, list[dict[str, Any]]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT user_id, payload_json
                FROM sharelife_preferences
                ORDER BY user_id
                """
            ).fetchall()

        out: list[dict[str, Any]] = []
        for row in rows:
            payload = self._decode_json(row["payload_json"], {})
            if isinstance(payload, dict):
                payload.setdefault("user_id", row["user_id"])
                out.append(payload)
        return {"preferences": out}

    def save_state(self, payload: dict[str, list[dict[str, Any]]]) -> None:
        preferences = payload.get("preferences", [])
        preferences = preferences if isinstance(preferences, list) else []
        with self._connect() as conn:
            self._replace_state_in_tx(conn, preferences=preferences)
            conn.commit()

    def _replace_state_in_tx(
        self,
        conn: sqlite3.Connection,
        *,
        preferences: list[dict[str, Any]],
    ) -> None:
        conn.execute("DELETE FROM sharelife_preferences")
        conn.executemany(
            """
            INSERT INTO sharelife_preferences(
                user_id, execution_mode, observe_task_details, payload_json
            ) VALUES(?, ?, ?, ?)
            """,
            [
                (
                    str(item.get("user_id", "") or ""),
                    str(item.get("execution_mode", "subagent_driven") or "subagent_driven"),
                    1 if bool(item.get("observe_task_details", False)) else 0,
                    self._encode_json(item),
                )
                for item in preferences
                if isinstance(item, dict) and str(item.get("user_id", "") or "").strip()
            ],
        )
