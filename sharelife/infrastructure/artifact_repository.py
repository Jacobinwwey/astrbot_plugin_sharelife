"""Repository implementations for local artifact metadata."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Protocol


class ArtifactRepository(Protocol):
    """Storage contract used by LocalArtifactStore."""

    def load_state(self) -> dict[str, list[dict[str, Any]]]:
        ...

    def save_state(self, payload: dict[str, list[dict[str, Any]]]) -> None:
        ...


class KeyValueStateStore(Protocol):
    def load(self, default: dict[str, Any]) -> dict[str, Any]:
        ...

    def save(self, payload: dict[str, Any]) -> None:
        ...


_DEFAULT_STATE = {"artifacts": []}


class JsonArtifactRepository:
    def __init__(self, state_store: KeyValueStateStore):
        self.state_store = state_store

    def load_state(self) -> dict[str, list[dict[str, Any]]]:
        payload = self.state_store.load(default=_DEFAULT_STATE)
        artifacts = payload.get("artifacts", [])
        return {"artifacts": artifacts if isinstance(artifacts, list) else []}

    def save_state(self, payload: dict[str, list[dict[str, Any]]]) -> None:
        self.state_store.save({"artifacts": list(payload.get("artifacts", []))})


class SqliteArtifactRepository:
    def __init__(
        self,
        db_path: Path | str,
        *,
        legacy_state_store: KeyValueStateStore | None = None,
    ):
        self.db_path = Path(db_path)
        self._init_db()
        if legacy_state_store is not None:
            legacy_payload = legacy_state_store.load(default=_DEFAULT_STATE)
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
                CREATE TABLE IF NOT EXISTS sharelife_artifacts (
                    artifact_id TEXT PRIMARY KEY,
                    artifact_kind TEXT NOT NULL,
                    storage_backend TEXT NOT NULL,
                    file_key TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    sha256 TEXT NOT NULL,
                    size_bytes INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_artifacts_kind ON sharelife_artifacts(artifact_kind)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_artifacts_file_key ON sharelife_artifacts(file_key)"
            )
            conn.commit()

    def _table_empty(self, conn: sqlite3.Connection) -> bool:
        row = conn.execute("SELECT COUNT(1) AS c FROM sharelife_artifacts").fetchone()
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
        artifacts = payload.get("artifacts", [])
        if not isinstance(artifacts, list) or not artifacts:
            return False
        with self._connect() as conn:
            if not self._table_empty(conn):
                return False
            self._replace_state_in_tx(conn, artifacts=artifacts)
            conn.commit()
        return True

    def load_state(self) -> dict[str, list[dict[str, Any]]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT artifact_id, payload_json
                FROM sharelife_artifacts
                ORDER BY created_at, artifact_id
                """
            ).fetchall()
        artifacts: list[dict[str, Any]] = []
        for row in rows:
            payload = self._decode_json(row["payload_json"], {})
            if isinstance(payload, dict):
                payload.setdefault("artifact_id", row["artifact_id"])
                artifacts.append(payload)
        return {"artifacts": artifacts}

    def save_state(self, payload: dict[str, list[dict[str, Any]]]) -> None:
        artifacts = payload.get("artifacts", [])
        artifacts = artifacts if isinstance(artifacts, list) else []
        with self._connect() as conn:
            self._replace_state_in_tx(conn, artifacts=artifacts)
            conn.commit()

    def _replace_state_in_tx(
        self,
        conn: sqlite3.Connection,
        *,
        artifacts: list[dict[str, Any]],
    ) -> None:
        conn.execute("DELETE FROM sharelife_artifacts")
        conn.executemany(
            """
            INSERT INTO sharelife_artifacts(
                artifact_id, artifact_kind, storage_backend, file_key, filename,
                sha256, size_bytes, created_at, updated_at, payload_json
            ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    str(item.get("artifact_id", "") or ""),
                    str(item.get("artifact_kind", "") or "artifact"),
                    str(item.get("storage_backend", "") or "local"),
                    str(item.get("file_key", "") or ""),
                    str(item.get("filename", "") or ""),
                    str(item.get("sha256", "") or ""),
                    int(item.get("size_bytes", 0) or 0),
                    str(item.get("created_at", "") or ""),
                    str(item.get("updated_at", "") or ""),
                    self._encode_json(item),
                )
                for item in artifacts
                if isinstance(item, dict) and str(item.get("artifact_id", "") or "").strip()
            ],
        )
