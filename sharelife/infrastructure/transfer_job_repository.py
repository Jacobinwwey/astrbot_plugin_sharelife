"""Repository implementations for upload/download transfer job state."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Protocol


class TransferJobRepository(Protocol):
    """Storage contract used by TransferJobService."""

    def load_state(self) -> dict[str, list[dict[str, Any]]]:
        ...

    def save_state(self, payload: dict[str, list[dict[str, Any]]]) -> None:
        ...


class KeyValueStateStore(Protocol):
    def load(self, default: dict[str, Any]) -> dict[str, Any]:
        ...

    def save(self, payload: dict[str, Any]) -> None:
        ...


_DEFAULT_STATE = {"upload_jobs": [], "download_jobs": []}


class JsonTransferJobRepository:
    def __init__(self, state_store: KeyValueStateStore):
        self.state_store = state_store

    def load_state(self) -> dict[str, list[dict[str, Any]]]:
        payload = self.state_store.load(default=_DEFAULT_STATE)
        upload_jobs = payload.get("upload_jobs", [])
        download_jobs = payload.get("download_jobs", [])
        return {
            "upload_jobs": upload_jobs if isinstance(upload_jobs, list) else [],
            "download_jobs": download_jobs if isinstance(download_jobs, list) else [],
        }

    def save_state(self, payload: dict[str, list[dict[str, Any]]]) -> None:
        self.state_store.save(
            {
                "upload_jobs": list(payload.get("upload_jobs", [])),
                "download_jobs": list(payload.get("download_jobs", [])),
            }
        )


class SqliteTransferJobRepository:
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
            for table in ("sharelife_upload_jobs", "sharelife_download_jobs"):
                conn.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS {table} (
                        job_id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        actor_id TEXT NOT NULL,
                        actor_role TEXT NOT NULL,
                        status TEXT NOT NULL,
                        logical_key TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        payload_json TEXT NOT NULL
                    )
                    """
                )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_upload_jobs_user_id ON sharelife_upload_jobs(user_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_upload_jobs_status ON sharelife_upload_jobs(status)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_upload_jobs_logical_key ON sharelife_upload_jobs(logical_key)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_download_jobs_user_id ON sharelife_download_jobs(user_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_download_jobs_status ON sharelife_download_jobs(status)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_download_jobs_logical_key ON sharelife_download_jobs(logical_key)"
            )
            conn.commit()

    def _tables_empty(self, conn: sqlite3.Connection) -> bool:
        upload = conn.execute("SELECT COUNT(1) AS c FROM sharelife_upload_jobs").fetchone()
        download = conn.execute("SELECT COUNT(1) AS c FROM sharelife_download_jobs").fetchone()
        return int(upload["c"] if upload is not None else 0) + int(download["c"] if download is not None else 0) == 0

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
        upload_jobs = payload.get("upload_jobs", [])
        download_jobs = payload.get("download_jobs", [])
        if not isinstance(upload_jobs, list) or not isinstance(download_jobs, list):
            return False
        if not upload_jobs and not download_jobs:
            return False

        with self._connect() as conn:
            if not self._tables_empty(conn):
                return False
            self._replace_state_in_tx(
                conn,
                upload_jobs=upload_jobs,
                download_jobs=download_jobs,
            )
            conn.commit()
        return True

    def load_state(self) -> dict[str, list[dict[str, Any]]]:
        with self._connect() as conn:
            upload_rows = conn.execute(
                """
                SELECT job_id, payload_json
                FROM sharelife_upload_jobs
                ORDER BY created_at, job_id
                """
            ).fetchall()
            download_rows = conn.execute(
                """
                SELECT job_id, payload_json
                FROM sharelife_download_jobs
                ORDER BY created_at, job_id
                """
            ).fetchall()
        upload_jobs: list[dict[str, Any]] = []
        for row in upload_rows:
            payload = self._decode_json(row["payload_json"], {})
            if isinstance(payload, dict):
                payload.setdefault("job_id", row["job_id"])
                upload_jobs.append(payload)
        download_jobs: list[dict[str, Any]] = []
        for row in download_rows:
            payload = self._decode_json(row["payload_json"], {})
            if isinstance(payload, dict):
                payload.setdefault("job_id", row["job_id"])
                download_jobs.append(payload)
        return {"upload_jobs": upload_jobs, "download_jobs": download_jobs}

    def save_state(self, payload: dict[str, list[dict[str, Any]]]) -> None:
        upload_jobs = payload.get("upload_jobs", [])
        download_jobs = payload.get("download_jobs", [])
        upload_jobs = upload_jobs if isinstance(upload_jobs, list) else []
        download_jobs = download_jobs if isinstance(download_jobs, list) else []
        with self._connect() as conn:
            self._replace_state_in_tx(
                conn,
                upload_jobs=upload_jobs,
                download_jobs=download_jobs,
            )
            conn.commit()

    def _replace_state_in_tx(
        self,
        conn: sqlite3.Connection,
        *,
        upload_jobs: list[dict[str, Any]],
        download_jobs: list[dict[str, Any]],
    ) -> None:
        conn.execute("DELETE FROM sharelife_upload_jobs")
        conn.execute("DELETE FROM sharelife_download_jobs")
        conn.executemany(
            """
            INSERT INTO sharelife_upload_jobs(
                job_id, user_id, actor_id, actor_role, status, logical_key, created_at, updated_at, payload_json
            ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    str(item.get("job_id", "") or ""),
                    str(item.get("user_id", "") or ""),
                    str(item.get("actor_id", "") or ""),
                    str(item.get("actor_role", "") or ""),
                    str(item.get("status", "") or "queued"),
                    str(item.get("logical_key", "") or ""),
                    str(item.get("created_at", "") or ""),
                    str(item.get("updated_at", "") or ""),
                    self._encode_json(item),
                )
                for item in upload_jobs
                if isinstance(item, dict) and str(item.get("job_id", "") or "").strip()
            ],
        )
        conn.executemany(
            """
            INSERT INTO sharelife_download_jobs(
                job_id, user_id, actor_id, actor_role, status, logical_key, created_at, updated_at, payload_json
            ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    str(item.get("job_id", "") or ""),
                    str(item.get("user_id", "") or ""),
                    str(item.get("actor_id", "") or ""),
                    str(item.get("actor_role", "") or ""),
                    str(item.get("status", "") or "queued"),
                    str(item.get("logical_key", "") or ""),
                    str(item.get("created_at", "") or ""),
                    str(item.get("updated_at", "") or ""),
                    self._encode_json(item),
                )
                for item in download_jobs
                if isinstance(item, dict) and str(item.get("job_id", "") or "").strip()
            ],
        )
