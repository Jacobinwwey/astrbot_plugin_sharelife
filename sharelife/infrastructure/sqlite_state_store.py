"""SQLite-backed state store for plugin services."""

from __future__ import annotations

import json
import sqlite3
import time
from copy import deepcopy
from pathlib import Path
from typing import Any


class SqliteStateStore:
    """Drop-in replacement for JsonStateStore using SQLite row storage."""

    def __init__(self, db_path: Path | str, store_key: str):
        self.db_path = Path(db_path)
        self.store_key = str(store_key or "").strip()
        if not self.store_key:
            raise ValueError("store_key is required")
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.db_path), timeout=30.0)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sharelife_state_store (
                    store_key TEXT PRIMARY KEY,
                    payload_json TEXT NOT NULL,
                    updated_at REAL NOT NULL
                )
                """
            )
            conn.commit()

    def has_state(self) -> bool:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM sharelife_state_store WHERE store_key = ? LIMIT 1",
                (self.store_key,),
            ).fetchone()
        return row is not None

    def load(self, default: dict[str, Any]) -> dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT payload_json FROM sharelife_state_store WHERE store_key = ?",
                (self.store_key,),
            ).fetchone()
        if row is None:
            return deepcopy(default)

        raw = str(row[0] or "").strip()
        if not raw:
            return deepcopy(default)

        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            return deepcopy(default)
        if not isinstance(payload, dict):
            return deepcopy(default)
        return payload

    def save(self, payload: dict[str, Any]) -> None:
        text = json.dumps(payload, ensure_ascii=False, indent=2)
        now = float(time.time())
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO sharelife_state_store(store_key, payload_json, updated_at)
                VALUES(?, ?, ?)
                ON CONFLICT(store_key) DO UPDATE SET
                    payload_json = excluded.payload_json,
                    updated_at = excluded.updated_at
                """,
                (self.store_key, text, now),
            )
            conn.commit()

    def import_from_json_file(self, json_path: Path | str) -> bool:
        """Import legacy JSON-file payload once when SQLite row is empty."""
        if self.has_state():
            return False
        path = Path(json_path)
        if not path.exists():
            return False
        raw = path.read_text(encoding="utf-8").strip()
        if not raw:
            return False
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            return False
        if not isinstance(payload, dict):
            return False
        self.save(payload)
        return True
