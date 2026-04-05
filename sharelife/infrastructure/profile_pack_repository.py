"""Repository implementations for profile-pack state persistence."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Protocol


class ProfilePackRepository(Protocol):
    """Storage contract used by ProfilePackService."""

    def load_state(self) -> dict[str, Any]:
        ...

    def save_state(self, payload: dict[str, Any]) -> None:
        ...


class KeyValueStateStore(Protocol):
    """Shared protocol for JSON and legacy sqlite key-value stores."""

    def load(self, default: dict[str, Any]) -> dict[str, Any]:
        ...

    def save(self, payload: dict[str, Any]) -> None:
        ...


class JsonProfilePackRepository:
    """JSON state-store backed repository."""

    def __init__(self, state_store: KeyValueStateStore):
        self.state_store = state_store

    def load_state(self) -> dict[str, Any]:
        payload = self.state_store.load(
            default={
                "exports": [],
                "imports": [],
                "submissions": [],
                "published": [],
                "plugin_install_confirmations": {},
                "plugin_install_executions": {},
            }
        )
        return {
            "exports": list(payload.get("exports", []) or []),
            "imports": list(payload.get("imports", []) or []),
            "submissions": list(payload.get("submissions", []) or []),
            "published": list(payload.get("published", []) or []),
            "plugin_install_confirmations": dict(payload.get("plugin_install_confirmations", {}) or {}),
            "plugin_install_executions": dict(payload.get("plugin_install_executions", {}) or {}),
        }

    def save_state(self, payload: dict[str, Any]) -> None:
        self.state_store.save(
            {
                "exports": list(payload.get("exports", []) or []),
                "imports": list(payload.get("imports", []) or []),
                "submissions": list(payload.get("submissions", []) or []),
                "published": list(payload.get("published", []) or []),
                "plugin_install_confirmations": dict(payload.get("plugin_install_confirmations", {}) or {}),
                "plugin_install_executions": dict(payload.get("plugin_install_executions", {}) or {}),
            }
        )


class SqliteProfilePackRepository:
    """SQLite profile-pack repository with normalized tables and indexed fields."""

    def __init__(
        self,
        db_path: Path | str,
        *,
        legacy_state_store: KeyValueStateStore | None = None,
    ):
        self.db_path = Path(db_path)
        self._init_db()
        if legacy_state_store is not None:
            legacy_payload = legacy_state_store.load(
                default={
                    "exports": [],
                    "imports": [],
                    "submissions": [],
                    "published": [],
                    "plugin_install_confirmations": {},
                    "plugin_install_executions": {},
                }
            )
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
                CREATE TABLE IF NOT EXISTS sharelife_profile_pack_exports (
                    artifact_id TEXT PRIMARY KEY,
                    pack_id TEXT NOT NULL,
                    version TEXT NOT NULL,
                    exported_at TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sharelife_profile_pack_imports (
                    import_id TEXT PRIMARY KEY,
                    pack_type TEXT NOT NULL,
                    pack_id TEXT NOT NULL,
                    version TEXT NOT NULL,
                    compatibility TEXT NOT NULL,
                    imported_at TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sharelife_profile_pack_submissions (
                    submission_id TEXT PRIMARY KEY,
                    pack_type TEXT NOT NULL,
                    pack_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    risk_level TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sharelife_profile_pack_published (
                    pack_id TEXT PRIMARY KEY,
                    pack_type TEXT NOT NULL,
                    risk_level TEXT NOT NULL,
                    published_at TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sharelife_profile_pack_plugin_install_confirmations (
                    import_id TEXT PRIMARY KEY,
                    plugin_ids_json TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sharelife_profile_pack_plugin_install_executions (
                    import_id TEXT PRIMARY KEY,
                    rows_json TEXT NOT NULL
                )
                """
            )

            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_profile_pack_exports_pack_id ON sharelife_profile_pack_exports(pack_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_profile_pack_exports_exported_at ON sharelife_profile_pack_exports(exported_at)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_profile_pack_imports_pack_id ON sharelife_profile_pack_imports(pack_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_profile_pack_imports_compatibility ON sharelife_profile_pack_imports(compatibility)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_profile_pack_imports_imported_at ON sharelife_profile_pack_imports(imported_at)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_profile_pack_submissions_pack_id ON sharelife_profile_pack_submissions(pack_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_profile_pack_submissions_status ON sharelife_profile_pack_submissions(status)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_profile_pack_submissions_risk_level ON sharelife_profile_pack_submissions(risk_level)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_profile_pack_submissions_created_at ON sharelife_profile_pack_submissions(created_at)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_profile_pack_published_risk_level ON sharelife_profile_pack_published(risk_level)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_profile_pack_published_published_at ON sharelife_profile_pack_published(published_at)"
            )
            conn.commit()

    @staticmethod
    def _encode_json(value: Any) -> str:
        return json.dumps(value, ensure_ascii=False)

    @staticmethod
    def _decode_json(raw: str | None, default: Any) -> Any:
        if raw in (None, ""):
            return default
        try:
            value = json.loads(raw)
        except json.JSONDecodeError:
            return default
        return value if value is not None else default

    @staticmethod
    def _manifest_field(item: dict[str, Any], field_name: str) -> str:
        manifest = item.get("manifest", {})
        if isinstance(manifest, dict):
            return str(manifest.get(field_name, "") or "")
        return ""

    def _tables_empty(self, conn: sqlite3.Connection) -> bool:
        table_names = [
            "sharelife_profile_pack_exports",
            "sharelife_profile_pack_imports",
            "sharelife_profile_pack_submissions",
            "sharelife_profile_pack_published",
            "sharelife_profile_pack_plugin_install_confirmations",
            "sharelife_profile_pack_plugin_install_executions",
        ]
        total = 0
        for table_name in table_names:
            row = conn.execute(f"SELECT COUNT(1) AS c FROM {table_name}").fetchone()
            total += int(row["c"] if row is not None else 0)
        return total == 0

    def import_legacy_payload(self, payload: dict[str, Any]) -> bool:
        if not isinstance(payload, dict):
            return False
        exports = payload.get("exports", [])
        imports = payload.get("imports", [])
        submissions = payload.get("submissions", [])
        published = payload.get("published", [])
        confirmations = payload.get("plugin_install_confirmations", {})
        executions = payload.get("plugin_install_executions", {})
        if not isinstance(exports, list) or not isinstance(imports, list):
            return False
        if not isinstance(submissions, list) or not isinstance(published, list):
            return False
        if not isinstance(confirmations, dict) or not isinstance(executions, dict):
            return False
        if not exports and not imports and not submissions and not published and not confirmations and not executions:
            return False

        with self._connect() as conn:
            if not self._tables_empty(conn):
                return False
            self._replace_state_in_tx(
                conn,
                exports=exports,
                imports=imports,
                submissions=submissions,
                published=published,
                confirmations=confirmations,
                executions=executions,
            )
            conn.commit()
        return True

    def load_state(self) -> dict[str, Any]:
        with self._connect() as conn:
            export_rows = conn.execute(
                """
                SELECT artifact_id, payload_json
                FROM sharelife_profile_pack_exports
                ORDER BY exported_at, artifact_id
                """
            ).fetchall()
            import_rows = conn.execute(
                """
                SELECT import_id, payload_json
                FROM sharelife_profile_pack_imports
                ORDER BY imported_at, import_id
                """
            ).fetchall()
            submission_rows = conn.execute(
                """
                SELECT submission_id, payload_json
                FROM sharelife_profile_pack_submissions
                ORDER BY created_at, submission_id
                """
            ).fetchall()
            published_rows = conn.execute(
                """
                SELECT pack_id, payload_json
                FROM sharelife_profile_pack_published
                ORDER BY pack_id
                """
            ).fetchall()
            confirmation_rows = conn.execute(
                """
                SELECT import_id, plugin_ids_json
                FROM sharelife_profile_pack_plugin_install_confirmations
                ORDER BY import_id
                """
            ).fetchall()
            execution_rows = conn.execute(
                """
                SELECT import_id, rows_json
                FROM sharelife_profile_pack_plugin_install_executions
                ORDER BY import_id
                """
            ).fetchall()

        exports: list[dict[str, Any]] = []
        for row in export_rows:
            payload = self._decode_json(row["payload_json"], {})
            if isinstance(payload, dict):
                payload.setdefault("artifact_id", row["artifact_id"])
                exports.append(payload)

        imports: list[dict[str, Any]] = []
        for row in import_rows:
            payload = self._decode_json(row["payload_json"], {})
            if isinstance(payload, dict):
                payload.setdefault("import_id", row["import_id"])
                imports.append(payload)

        submissions: list[dict[str, Any]] = []
        for row in submission_rows:
            payload = self._decode_json(row["payload_json"], {})
            if isinstance(payload, dict):
                payload.setdefault("submission_id", row["submission_id"])
                submissions.append(payload)

        published: list[dict[str, Any]] = []
        for row in published_rows:
            payload = self._decode_json(row["payload_json"], {})
            if isinstance(payload, dict):
                payload.setdefault("pack_id", row["pack_id"])
                published.append(payload)

        confirmations: dict[str, list[str]] = {}
        for row in confirmation_rows:
            import_id = str(row["import_id"] or "").strip()
            if not import_id:
                continue
            plugin_ids = self._decode_json(row["plugin_ids_json"], [])
            if isinstance(plugin_ids, list):
                confirmations[import_id] = [str(item or "") for item in plugin_ids if str(item or "").strip()]

        executions: dict[str, list[dict[str, Any]]] = {}
        for row in execution_rows:
            import_id = str(row["import_id"] or "").strip()
            if not import_id:
                continue
            values = self._decode_json(row["rows_json"], [])
            if isinstance(values, list):
                normalized_values: list[dict[str, Any]] = []
                for item in values:
                    if isinstance(item, dict):
                        normalized_values.append(dict(item))
                executions[import_id] = normalized_values

        return {
            "exports": exports,
            "imports": imports,
            "submissions": submissions,
            "published": published,
            "plugin_install_confirmations": confirmations,
            "plugin_install_executions": executions,
        }

    def save_state(self, payload: dict[str, Any]) -> None:
        exports = payload.get("exports", [])
        imports = payload.get("imports", [])
        submissions = payload.get("submissions", [])
        published = payload.get("published", [])
        confirmations = payload.get("plugin_install_confirmations", {})
        executions = payload.get("plugin_install_executions", {})

        exports = exports if isinstance(exports, list) else []
        imports = imports if isinstance(imports, list) else []
        submissions = submissions if isinstance(submissions, list) else []
        published = published if isinstance(published, list) else []
        confirmations = confirmations if isinstance(confirmations, dict) else {}
        executions = executions if isinstance(executions, dict) else {}

        with self._connect() as conn:
            self._replace_state_in_tx(
                conn,
                exports=exports,
                imports=imports,
                submissions=submissions,
                published=published,
                confirmations=confirmations,
                executions=executions,
            )
            conn.commit()

    def _replace_state_in_tx(
        self,
        conn: sqlite3.Connection,
        *,
        exports: list[dict[str, Any]],
        imports: list[dict[str, Any]],
        submissions: list[dict[str, Any]],
        published: list[dict[str, Any]],
        confirmations: dict[str, Any],
        executions: dict[str, Any],
    ) -> None:
        conn.execute("DELETE FROM sharelife_profile_pack_exports")
        conn.execute("DELETE FROM sharelife_profile_pack_imports")
        conn.execute("DELETE FROM sharelife_profile_pack_submissions")
        conn.execute("DELETE FROM sharelife_profile_pack_published")
        conn.execute("DELETE FROM sharelife_profile_pack_plugin_install_confirmations")
        conn.execute("DELETE FROM sharelife_profile_pack_plugin_install_executions")

        conn.executemany(
            """
            INSERT INTO sharelife_profile_pack_exports(
                artifact_id, pack_id, version, exported_at, payload_json
            ) VALUES(?, ?, ?, ?, ?)
            """,
            [
                (
                    str(item.get("artifact_id", "") or ""),
                    str(item.get("pack_id", "") or self._manifest_field(item, "pack_id")),
                    str(item.get("version", "") or self._manifest_field(item, "version")),
                    str(item.get("exported_at", "") or ""),
                    self._encode_json(item),
                )
                for item in exports
                if isinstance(item, dict) and str(item.get("artifact_id", "") or "").strip()
            ],
        )

        conn.executemany(
            """
            INSERT INTO sharelife_profile_pack_imports(
                import_id, pack_type, pack_id, version, compatibility, imported_at, payload_json
            ) VALUES(?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    str(item.get("import_id", "") or ""),
                    str(item.get("pack_type", "") or self._manifest_field(item, "pack_type") or "bot_profile_pack"),
                    str(item.get("pack_id", "") or self._manifest_field(item, "pack_id")),
                    str(item.get("version", "") or self._manifest_field(item, "version")),
                    str(item.get("compatibility", "") or "compatible"),
                    str(item.get("imported_at", "") or ""),
                    self._encode_json(item),
                )
                for item in imports
                if isinstance(item, dict) and str(item.get("import_id", "") or "").strip()
            ],
        )

        conn.executemany(
            """
            INSERT INTO sharelife_profile_pack_submissions(
                submission_id, pack_type, pack_id, status, risk_level, created_at, updated_at, payload_json
            ) VALUES(?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    str(item.get("submission_id", "") or ""),
                    str(item.get("pack_type", "") or "bot_profile_pack"),
                    str(item.get("pack_id", "") or ""),
                    str(item.get("status", "") or "pending"),
                    str(item.get("risk_level", "") or "low"),
                    str(item.get("created_at", "") or ""),
                    str(item.get("updated_at", "") or ""),
                    self._encode_json(item),
                )
                for item in submissions
                if isinstance(item, dict) and str(item.get("submission_id", "") or "").strip()
            ],
        )

        conn.executemany(
            """
            INSERT INTO sharelife_profile_pack_published(
                pack_id, pack_type, risk_level, published_at, payload_json
            ) VALUES(?, ?, ?, ?, ?)
            """,
            [
                (
                    str(item.get("pack_id", "") or ""),
                    str(item.get("pack_type", "") or "bot_profile_pack"),
                    str(item.get("risk_level", "") or "low"),
                    str(item.get("published_at", "") or ""),
                    self._encode_json(item),
                )
                for item in published
                if isinstance(item, dict) and str(item.get("pack_id", "") or "").strip()
            ],
        )

        conn.executemany(
            """
            INSERT INTO sharelife_profile_pack_plugin_install_confirmations(
                import_id, plugin_ids_json
            ) VALUES(?, ?)
            """,
            [
                (
                    str(import_id),
                    self._encode_json(list(plugin_ids) if isinstance(plugin_ids, list) else []),
                )
                for import_id, plugin_ids in confirmations.items()
                if str(import_id or "").strip()
            ],
        )

        conn.executemany(
            """
            INSERT INTO sharelife_profile_pack_plugin_install_executions(
                import_id, rows_json
            ) VALUES(?, ?)
            """,
            [
                (
                    str(import_id),
                    self._encode_json(list(rows) if isinstance(rows, list) else []),
                )
                for import_id, rows in executions.items()
                if str(import_id or "").strip()
            ],
        )
