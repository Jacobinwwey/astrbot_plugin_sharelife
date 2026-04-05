"""Repository implementations for trial request state."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Protocol


class TrialRequestRepository(Protocol):
    """Storage contract used by TrialRequestService."""

    def load_state(self) -> dict[str, list[str]]:
        ...

    def save_state(self, payload: dict[str, list[str]]) -> None:
        ...


class KeyValueStateStore(Protocol):
    def load(self, default: dict[str, Any]) -> dict[str, Any]:
        ...

    def save(self, payload: dict[str, Any]) -> None:
        ...


class JsonTrialRequestRepository:
    def __init__(self, state_store: KeyValueStateStore):
        self.state_store = state_store

    def load_state(self) -> dict[str, list[str]]:
        payload = self.state_store.load(default={"first_notice_sent_users": []})
        raw = payload.get("first_notice_sent_users", [])
        users = [str(item) for item in raw] if isinstance(raw, list) else []
        return {"first_notice_sent_users": users}

    def save_state(self, payload: dict[str, list[str]]) -> None:
        raw = payload.get("first_notice_sent_users", [])
        users = [str(item) for item in raw] if isinstance(raw, list) else []
        self.state_store.save({"first_notice_sent_users": users})


class SqliteTrialRequestRepository:
    def __init__(
        self,
        db_path: Path | str,
        *,
        legacy_state_store: KeyValueStateStore | None = None,
    ):
        self.db_path = Path(db_path)
        self._init_db()
        if legacy_state_store is not None:
            legacy_payload = legacy_state_store.load(default={"first_notice_sent_users": []})
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
                CREATE TABLE IF NOT EXISTS sharelife_trial_request_notices (
                    user_id TEXT PRIMARY KEY,
                    payload_json TEXT NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_trial_request_notices_user_id ON sharelife_trial_request_notices(user_id)"
            )
            conn.commit()

    def _table_empty(self, conn: sqlite3.Connection) -> bool:
        row = conn.execute("SELECT COUNT(1) AS c FROM sharelife_trial_request_notices").fetchone()
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
        raw = payload.get("first_notice_sent_users", [])
        if not isinstance(raw, list) or not raw:
            return False
        users = [str(item) for item in raw]

        with self._connect() as conn:
            if not self._table_empty(conn):
                return False
            self._replace_state_in_tx(conn, users=users)
            conn.commit()
        return True

    def load_state(self) -> dict[str, list[str]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT user_id, payload_json
                FROM sharelife_trial_request_notices
                ORDER BY user_id
                """
            ).fetchall()

        users: list[str] = []
        for row in rows:
            payload = self._decode_json(row["payload_json"], {})
            if isinstance(payload, dict):
                user_id = str(payload.get("user_id", row["user_id"]) or "").strip()
                if user_id:
                    users.append(user_id)
            else:
                fallback = str(row["user_id"] or "").strip()
                if fallback:
                    users.append(fallback)
        return {"first_notice_sent_users": users}

    def save_state(self, payload: dict[str, list[str]]) -> None:
        raw = payload.get("first_notice_sent_users", [])
        users = [str(item) for item in raw] if isinstance(raw, list) else []
        with self._connect() as conn:
            self._replace_state_in_tx(conn, users=users)
            conn.commit()

    def _replace_state_in_tx(self, conn: sqlite3.Connection, *, users: list[str]) -> None:
        conn.execute("DELETE FROM sharelife_trial_request_notices")
        conn.executemany(
            """
            INSERT INTO sharelife_trial_request_notices(user_id, payload_json)
            VALUES(?, ?)
            """,
            [
                (user_id, self._encode_json({"user_id": user_id}))
                for user_id in sorted(
                    {
                        str(item or "").strip()
                        for item in users
                        if str(item or "").strip()
                    }
                )
            ],
        )
