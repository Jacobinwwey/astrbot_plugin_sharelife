"""Repository implementations for notifier state."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Protocol


class NotifierRepository(Protocol):
    """Storage contract used by InMemoryNotifier."""

    def load_state(self) -> dict[str, list[dict[str, Any]]]:
        ...

    def save_state(self, payload: dict[str, list[dict[str, Any]]]) -> None:
        ...


class KeyValueStateStore(Protocol):
    def load(self, default: dict[str, Any]) -> dict[str, Any]:
        ...

    def save(self, payload: dict[str, Any]) -> None:
        ...


class JsonNotifierRepository:
    def __init__(self, state_store: KeyValueStateStore):
        self.state_store = state_store

    def load_state(self) -> dict[str, list[dict[str, Any]]]:
        payload = self.state_store.load(default={"events": []})
        events = payload.get("events", [])
        return {"events": events if isinstance(events, list) else []}

    def save_state(self, payload: dict[str, list[dict[str, Any]]]) -> None:
        self.state_store.save({"events": list(payload.get("events", []))})


class SqliteNotifierRepository:
    def __init__(
        self,
        db_path: Path | str,
        *,
        legacy_state_store: KeyValueStateStore | None = None,
    ):
        self.db_path = Path(db_path)
        self._init_db()
        if legacy_state_store is not None:
            legacy_payload = legacy_state_store.load(default={"events": []})
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
                CREATE TABLE IF NOT EXISTS sharelife_notification_events (
                    row_order INTEGER PRIMARY KEY,
                    channel TEXT NOT NULL,
                    target TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_notification_events_channel ON sharelife_notification_events(channel)"
            )
            conn.commit()

    def _table_empty(self, conn: sqlite3.Connection) -> bool:
        row = conn.execute("SELECT COUNT(1) AS c FROM sharelife_notification_events").fetchone()
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
        events = payload.get("events", [])
        if not isinstance(events, list) or not events:
            return False
        with self._connect() as conn:
            if not self._table_empty(conn):
                return False
            self._replace_state_in_tx(conn, events=events)
            conn.commit()
        return True

    def load_state(self) -> dict[str, list[dict[str, Any]]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT row_order, payload_json
                FROM sharelife_notification_events
                ORDER BY row_order
                """
            ).fetchall()

        events: list[dict[str, Any]] = []
        for row in rows:
            payload = self._decode_json(row["payload_json"], {})
            if isinstance(payload, dict):
                events.append(payload)
        return {"events": events}

    def save_state(self, payload: dict[str, list[dict[str, Any]]]) -> None:
        events = payload.get("events", [])
        events = events if isinstance(events, list) else []
        with self._connect() as conn:
            self._replace_state_in_tx(conn, events=events)
            conn.commit()

    def _replace_state_in_tx(
        self,
        conn: sqlite3.Connection,
        *,
        events: list[dict[str, Any]],
    ) -> None:
        conn.execute("DELETE FROM sharelife_notification_events")
        conn.executemany(
            """
            INSERT INTO sharelife_notification_events(row_order, channel, target, payload_json)
            VALUES(?, ?, ?, ?)
            """,
            [
                (
                    idx + 1,
                    str(item.get("channel", "") or ""),
                    str(item.get("target", "") or ""),
                    self._encode_json(item),
                )
                for idx, item in enumerate(events)
                if isinstance(item, dict)
            ],
        )
