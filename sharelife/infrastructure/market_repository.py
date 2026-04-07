"""Repository implementations for market submissions and published templates."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Protocol


class MarketRepository(Protocol):
    """Market storage contract used by MarketService."""

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


class JsonMarketRepository:
    """JSON state-store backed market repository."""

    def __init__(self, state_store: KeyValueStateStore):
        self.state_store = state_store

    def load_state(self) -> dict[str, list[dict[str, Any]]]:
        payload = self.state_store.load(default={"submissions": [], "published": []})
        submissions = payload.get("submissions", [])
        published = payload.get("published", [])
        return {
            "submissions": submissions if isinstance(submissions, list) else [],
            "published": published if isinstance(published, list) else [],
        }

    def save_state(self, payload: dict[str, list[dict[str, Any]]]) -> None:
        self.state_store.save(
            {
                "submissions": list(payload.get("submissions", [])),
                "published": list(payload.get("published", [])),
            }
        )


class SqliteMarketRepository:
    """SQLite repository with normalized tables and query indexes."""

    def __init__(
        self,
        db_path: Path | str,
        *,
        legacy_state_store: KeyValueStateStore | None = None,
    ):
        self.db_path = Path(db_path)
        self._init_db()
        if legacy_state_store is not None:
            legacy_payload = legacy_state_store.load(default={"submissions": [], "published": []})
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
                # Keep fallback defaults if another writer holds the lock.
                pass
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sharelife_market_submissions (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    template_id TEXT NOT NULL,
                    version TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    reviewer_id TEXT,
                    review_note TEXT NOT NULL,
                    prompt_template TEXT NOT NULL,
                    package_artifact_json TEXT,
                    scan_summary_json TEXT,
                    upload_options_json TEXT,
                    review_labels_json TEXT NOT NULL,
                    warning_flags_json TEXT NOT NULL,
                    risk_level TEXT NOT NULL,
                    category TEXT NOT NULL,
                    tags_json TEXT NOT NULL,
                    maintainer TEXT NOT NULL,
                    source_channel TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sharelife_market_published (
                    template_id TEXT PRIMARY KEY,
                    version TEXT NOT NULL,
                    source_submission_id TEXT NOT NULL,
                    prompt_template TEXT NOT NULL,
                    published_at TEXT NOT NULL,
                    review_note TEXT NOT NULL,
                    package_artifact_json TEXT,
                    scan_summary_json TEXT,
                    review_labels_json TEXT NOT NULL,
                    warning_flags_json TEXT NOT NULL,
                    risk_level TEXT NOT NULL,
                    category TEXT NOT NULL,
                    tags_json TEXT NOT NULL,
                    maintainer TEXT NOT NULL,
                    source_channel TEXT NOT NULL,
                    engagement_json TEXT NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_market_submissions_template_id ON sharelife_market_submissions(template_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_market_submissions_status ON sharelife_market_submissions(status)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_market_submissions_risk_level ON sharelife_market_submissions(risk_level)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_market_submissions_created_at ON sharelife_market_submissions(created_at)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_market_published_risk_level ON sharelife_market_published(risk_level)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_market_published_published_at ON sharelife_market_published(published_at)"
            )
            self._ensure_submission_schema(conn)
            conn.commit()

    def _ensure_submission_schema(self, conn: sqlite3.Connection) -> None:
        columns = conn.execute("PRAGMA table_info('sharelife_market_submissions')").fetchall()
        names = {str(row["name"]) for row in columns}
        if "upload_options_json" not in names:
            conn.execute("ALTER TABLE sharelife_market_submissions ADD COLUMN upload_options_json TEXT")

    def _decode_json(self, raw: str | None, default: Any) -> Any:
        if raw in (None, ""):
            return default
        try:
            value = json.loads(raw)
        except json.JSONDecodeError:
            return default
        return value if value is not None else default

    @staticmethod
    def _encode_json(value: Any) -> str:
        return json.dumps(value, ensure_ascii=False)

    def _tables_empty(self, conn: sqlite3.Connection) -> bool:
        row_a = conn.execute(
            "SELECT COUNT(1) AS c FROM sharelife_market_submissions"
        ).fetchone()
        row_b = conn.execute(
            "SELECT COUNT(1) AS c FROM sharelife_market_published"
        ).fetchone()
        count_a = int(row_a["c"] if row_a is not None else 0)
        count_b = int(row_b["c"] if row_b is not None else 0)
        return (count_a + count_b) == 0

    def import_legacy_payload(self, payload: dict[str, Any]) -> bool:
        if not isinstance(payload, dict):
            return False
        submissions = payload.get("submissions", [])
        published = payload.get("published", [])
        if not isinstance(submissions, list) or not isinstance(published, list):
            return False
        if not submissions and not published:
            return False

        with self._connect() as conn:
            if not self._tables_empty(conn):
                return False
            self._replace_state_in_tx(conn, submissions=submissions, published=published)
            conn.commit()
        return True

    def load_state(self) -> dict[str, list[dict[str, Any]]]:
        with self._connect() as conn:
            submission_rows = conn.execute(
                """
                SELECT
                    id, user_id, template_id, version, status, created_at, updated_at,
                    reviewer_id, review_note, prompt_template,
                    package_artifact_json, scan_summary_json, upload_options_json, review_labels_json,
                    warning_flags_json, risk_level, category, tags_json, maintainer,
                    source_channel
                FROM sharelife_market_submissions
                ORDER BY created_at, id
                """
            ).fetchall()
            published_rows = conn.execute(
                """
                SELECT
                    template_id, version, source_submission_id, prompt_template,
                    published_at, review_note, package_artifact_json,
                    scan_summary_json, review_labels_json, warning_flags_json,
                    risk_level, category, tags_json, maintainer,
                    source_channel, engagement_json
                FROM sharelife_market_published
                ORDER BY template_id
                """
            ).fetchall()

        submissions: list[dict[str, Any]] = []
        for row in submission_rows:
            submissions.append(
                {
                    "id": row["id"],
                    "user_id": row["user_id"],
                    "template_id": row["template_id"],
                    "version": row["version"],
                    "status": row["status"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                    "reviewer_id": row["reviewer_id"],
                    "review_note": row["review_note"],
                    "prompt_template": row["prompt_template"],
                    "package_artifact": self._decode_json(row["package_artifact_json"], None),
                    "scan_summary": self._decode_json(row["scan_summary_json"], None),
                    "upload_options": self._decode_json(row["upload_options_json"], None),
                    "review_labels": self._decode_json(row["review_labels_json"], []),
                    "warning_flags": self._decode_json(row["warning_flags_json"], []),
                    "risk_level": row["risk_level"],
                    "category": row["category"],
                    "tags": self._decode_json(row["tags_json"], []),
                    "maintainer": row["maintainer"],
                    "source_channel": row["source_channel"],
                }
            )

        published: list[dict[str, Any]] = []
        for row in published_rows:
            published.append(
                {
                    "template_id": row["template_id"],
                    "version": row["version"],
                    "source_submission_id": row["source_submission_id"],
                    "prompt_template": row["prompt_template"],
                    "published_at": row["published_at"],
                    "review_note": row["review_note"],
                    "package_artifact": self._decode_json(row["package_artifact_json"], None),
                    "scan_summary": self._decode_json(row["scan_summary_json"], None),
                    "review_labels": self._decode_json(row["review_labels_json"], []),
                    "warning_flags": self._decode_json(row["warning_flags_json"], []),
                    "risk_level": row["risk_level"],
                    "category": row["category"],
                    "tags": self._decode_json(row["tags_json"], []),
                    "maintainer": row["maintainer"],
                    "source_channel": row["source_channel"],
                    "engagement": self._decode_json(row["engagement_json"], {}),
                }
            )

        return {"submissions": submissions, "published": published}

    def save_state(self, payload: dict[str, list[dict[str, Any]]]) -> None:
        submissions = payload.get("submissions", [])
        published = payload.get("published", [])
        submissions = submissions if isinstance(submissions, list) else []
        published = published if isinstance(published, list) else []
        with self._connect() as conn:
            self._replace_state_in_tx(conn, submissions=submissions, published=published)
            conn.commit()

    def _replace_state_in_tx(
        self,
        conn: sqlite3.Connection,
        *,
        submissions: list[dict[str, Any]],
        published: list[dict[str, Any]],
    ) -> None:
        conn.execute("DELETE FROM sharelife_market_submissions")
        conn.execute("DELETE FROM sharelife_market_published")

        conn.executemany(
            """
            INSERT INTO sharelife_market_submissions(
                id, user_id, template_id, version, status, created_at, updated_at,
                reviewer_id, review_note, prompt_template, package_artifact_json,
                scan_summary_json, upload_options_json, review_labels_json, warning_flags_json,
                risk_level, category, tags_json, maintainer, source_channel
            ) VALUES(
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
            """,
            [
                (
                    str(item.get("id", "") or ""),
                    str(item.get("user_id", "") or ""),
                    str(item.get("template_id", "") or ""),
                    str(item.get("version", "") or ""),
                    str(item.get("status", "") or ""),
                    str(item.get("created_at", "") or ""),
                    str(item.get("updated_at", "") or ""),
                    (None if item.get("reviewer_id") is None else str(item.get("reviewer_id"))),
                    str(item.get("review_note", "") or ""),
                    str(item.get("prompt_template", "") or ""),
                    self._encode_json(item.get("package_artifact")),
                    self._encode_json(item.get("scan_summary")),
                    self._encode_json(item.get("upload_options")),
                    self._encode_json(list(item.get("review_labels", []) or [])),
                    self._encode_json(list(item.get("warning_flags", []) or [])),
                    str(item.get("risk_level", "low") or "low"),
                    str(item.get("category", "") or ""),
                    self._encode_json(list(item.get("tags", []) or [])),
                    str(item.get("maintainer", "") or ""),
                    str(item.get("source_channel", "") or ""),
                )
                for item in submissions
            ],
        )

        conn.executemany(
            """
            INSERT INTO sharelife_market_published(
                template_id, version, source_submission_id, prompt_template,
                published_at, review_note, package_artifact_json, scan_summary_json,
                review_labels_json, warning_flags_json, risk_level, category,
                tags_json, maintainer, source_channel, engagement_json
            ) VALUES(
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
            """,
            [
                (
                    str(item.get("template_id", "") or ""),
                    str(item.get("version", "") or ""),
                    str(item.get("source_submission_id", "") or ""),
                    str(item.get("prompt_template", "") or ""),
                    str(item.get("published_at", "") or ""),
                    str(item.get("review_note", "") or ""),
                    self._encode_json(item.get("package_artifact")),
                    self._encode_json(item.get("scan_summary")),
                    self._encode_json(list(item.get("review_labels", []) or [])),
                    self._encode_json(list(item.get("warning_flags", []) or [])),
                    str(item.get("risk_level", "low") or "low"),
                    str(item.get("category", "") or ""),
                    self._encode_json(list(item.get("tags", []) or [])),
                    str(item.get("maintainer", "") or ""),
                    str(item.get("source_channel", "") or ""),
                    self._encode_json(dict(item.get("engagement", {}) or {})),
                )
                for item in published
            ],
        )
