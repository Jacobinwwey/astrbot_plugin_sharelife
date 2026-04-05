"""Repository implementations for retry queue state."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Protocol


class RetryQueueRepository(Protocol):
    """Storage contract used by RetryQueueService."""

    def load_state(self) -> dict[str, list[dict[str, Any]]]:
        ...

    def save_state(self, payload: dict[str, list[dict[str, Any]]]) -> None:
        ...


class KeyValueStateStore(Protocol):
    def load(self, default: dict[str, Any]) -> dict[str, Any]:
        ...

    def save(self, payload: dict[str, Any]) -> None:
        ...


class JsonRetryQueueRepository:
    def __init__(self, state_store: KeyValueStateStore):
        self.state_store = state_store

    def load_state(self) -> dict[str, list[dict[str, Any]]]:
        payload = self.state_store.load(default={"requests": [], "locks": []})
        requests = payload.get("requests", [])
        locks = payload.get("locks", [])
        return {
            "requests": requests if isinstance(requests, list) else [],
            "locks": locks if isinstance(locks, list) else [],
        }

    def save_state(self, payload: dict[str, list[dict[str, Any]]]) -> None:
        self.state_store.save(
            {
                "requests": list(payload.get("requests", [])),
                "locks": list(payload.get("locks", [])),
            }
        )


class SqliteRetryQueueRepository:
    def __init__(
        self,
        db_path: Path | str,
        *,
        legacy_state_store: KeyValueStateStore | None = None,
    ):
        self.db_path = Path(db_path)
        self._init_db()
        if legacy_state_store is not None:
            legacy_payload = legacy_state_store.load(default={"requests": [], "locks": []})
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
                CREATE TABLE IF NOT EXISTS sharelife_retry_requests (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    template_id TEXT NOT NULL,
                    state TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    payload_json TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sharelife_retry_locks (
                    request_id TEXT PRIMARY KEY,
                    holder_id TEXT NOT NULL,
                    lock_version INTEGER NOT NULL,
                    expires_at TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_retry_requests_template_id ON sharelife_retry_requests(template_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_retry_requests_state ON sharelife_retry_requests(state)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_retry_requests_created_at ON sharelife_retry_requests(created_at)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_retry_locks_expires_at ON sharelife_retry_locks(expires_at)"
            )
            conn.commit()

    def _tables_empty(self, conn: sqlite3.Connection) -> bool:
        req = conn.execute("SELECT COUNT(1) AS c FROM sharelife_retry_requests").fetchone()
        locks = conn.execute("SELECT COUNT(1) AS c FROM sharelife_retry_locks").fetchone()
        return int(req["c"] if req is not None else 0) + int(locks["c"] if locks is not None else 0) == 0

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
        requests = payload.get("requests", [])
        locks = payload.get("locks", [])
        if not isinstance(requests, list) or not isinstance(locks, list):
            return False
        if not requests and not locks:
            return False

        with self._connect() as conn:
            if not self._tables_empty(conn):
                return False
            self._replace_state_in_tx(conn, requests=requests, locks=locks)
            conn.commit()
        return True

    def load_state(self) -> dict[str, list[dict[str, Any]]]:
        with self._connect() as conn:
            req_rows = conn.execute(
                """
                SELECT id, payload_json
                FROM sharelife_retry_requests
                ORDER BY created_at, id
                """
            ).fetchall()
            lock_rows = conn.execute(
                """
                SELECT request_id, payload_json
                FROM sharelife_retry_locks
                ORDER BY request_id
                """
            ).fetchall()
        requests: list[dict[str, Any]] = []
        for row in req_rows:
            payload = self._decode_json(row["payload_json"], {})
            if isinstance(payload, dict):
                payload.setdefault("id", row["id"])
                requests.append(payload)

        locks: list[dict[str, Any]] = []
        for row in lock_rows:
            payload = self._decode_json(row["payload_json"], {})
            if isinstance(payload, dict):
                payload.setdefault("request_id", row["request_id"])
                locks.append(payload)
        return {"requests": requests, "locks": locks}

    def save_state(self, payload: dict[str, list[dict[str, Any]]]) -> None:
        requests = payload.get("requests", [])
        locks = payload.get("locks", [])
        requests = requests if isinstance(requests, list) else []
        locks = locks if isinstance(locks, list) else []

        with self._connect() as conn:
            self._replace_state_in_tx(conn, requests=requests, locks=locks)
            conn.commit()

    def _replace_state_in_tx(
        self,
        conn: sqlite3.Connection,
        *,
        requests: list[dict[str, Any]],
        locks: list[dict[str, Any]],
    ) -> None:
        conn.execute("DELETE FROM sharelife_retry_requests")
        conn.execute("DELETE FROM sharelife_retry_locks")
        conn.executemany(
            """
            INSERT INTO sharelife_retry_requests(
                id, user_id, template_id, state, created_at, updated_at, version, payload_json
            ) VALUES(?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    str(item.get("id", "") or ""),
                    str(item.get("user_id", "") or ""),
                    str(item.get("template_id", "") or ""),
                    str(item.get("state", "") or "queued"),
                    str(item.get("created_at", "") or ""),
                    str(item.get("updated_at", "") or ""),
                    int(item.get("version", 1) or 1),
                    self._encode_json(item),
                )
                for item in requests
                if isinstance(item, dict) and str(item.get("id", "") or "").strip()
            ],
        )
        conn.executemany(
            """
            INSERT INTO sharelife_retry_locks(
                request_id, holder_id, lock_version, expires_at, payload_json
            ) VALUES(?, ?, ?, ?, ?)
            """,
            [
                (
                    str(item.get("request_id", "") or ""),
                    str(item.get("holder_id", "") or ""),
                    int(item.get("lock_version", 1) or 1),
                    str(item.get("expires_at", "") or ""),
                    self._encode_json(item),
                )
                for item in locks
                if isinstance(item, dict) and str(item.get("request_id", "") or "").strip()
            ],
        )
