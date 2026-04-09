"""Local artifact registry and resolver."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Protocol
from uuid import uuid4

from .artifact_repository import (
    ArtifactRepository,
    JsonArtifactRepository,
    SqliteArtifactRepository,
)
from .json_state_store import JsonStateStore
from .sqlite_state_store import SqliteStateStore
from .system_clock import SystemClock


class ArtifactStore(Protocol):
    def register_local_file(
        self,
        *,
        artifact_kind: str,
        path: Path | str,
        filename: str = "",
        sha256: str = "",
        size_bytes: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> "ArtifactRecord":
        ...

    def get(self, artifact_id: str) -> "ArtifactRecord":
        ...

    def resolve(self, artifact_id: str) -> Path:
        ...

    def list(self, *, artifact_kind: str = "", limit: int = 100) -> list["ArtifactRecord"]:
        ...

    def update_metadata(self, artifact_id: str, metadata_patch: dict[str, Any]) -> "ArtifactRecord":
        ...


@dataclass(slots=True)
class ArtifactRecord:
    artifact_id: str
    artifact_kind: str
    storage_backend: str
    file_key: str
    filename: str
    sha256: str
    size_bytes: int
    created_at: str
    updated_at: str
    metadata: dict[str, Any] = field(default_factory=dict)


class LocalArtifactStore:
    def __init__(
        self,
        output_root: Path | str,
        clock: SystemClock,
        state_store: JsonStateStore | SqliteStateStore | None = None,
        repository: ArtifactRepository | None = None,
    ):
        self.output_root = Path(output_root)
        self.clock = clock
        self.state_store = state_store
        self.repository = self._build_repository(state_store=state_store, repository=repository)
        self._records: dict[str, ArtifactRecord] = {}
        self._artifact_ids_by_file_key: dict[str, str] = {}
        self._load_state()

    @staticmethod
    def _build_repository(
        *,
        state_store: JsonStateStore | SqliteStateStore | None,
        repository: ArtifactRepository | None,
    ) -> ArtifactRepository | None:
        if repository is not None:
            return repository
        if state_store is None:
            return None
        if isinstance(state_store, SqliteStateStore):
            return SqliteArtifactRepository(state_store.db_path, legacy_state_store=state_store)
        return JsonArtifactRepository(state_store)

    def register_local_file(
        self,
        *,
        artifact_kind: str,
        path: Path | str,
        filename: str = "",
        sha256: str = "",
        size_bytes: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ArtifactRecord:
        resolved_path = Path(path).expanduser().resolve()
        if not resolved_path.exists():
            raise FileNotFoundError(str(resolved_path))
        file_key = self._file_key(resolved_path)
        existing = self._records.get(self._artifact_ids_by_file_key.get(file_key, ""))
        now = self.clock.utcnow().isoformat()
        record_sha256 = str(sha256 or "").strip() or self._sha256_file(resolved_path)
        record_size = max(0, int(size_bytes if size_bytes is not None else resolved_path.stat().st_size))
        if existing is not None:
            existing.artifact_kind = str(artifact_kind or existing.artifact_kind or "artifact")
            existing.filename = str(filename or existing.filename or resolved_path.name)
            existing.sha256 = record_sha256
            existing.size_bytes = record_size
            existing.updated_at = now
            if metadata:
                existing.metadata = self._merge_metadata(existing.metadata, metadata)
            self._flush_state()
            return existing

        record = ArtifactRecord(
            artifact_id=f"artifact-{uuid4()}",
            artifact_kind=str(artifact_kind or "artifact").strip() or "artifact",
            storage_backend="local",
            file_key=file_key,
            filename=str(filename or resolved_path.name).strip() or resolved_path.name,
            sha256=record_sha256,
            size_bytes=record_size,
            created_at=now,
            updated_at=now,
            metadata=dict(metadata or {}),
        )
        self._records[record.artifact_id] = record
        self._artifact_ids_by_file_key[file_key] = record.artifact_id
        self._flush_state()
        return record

    def get(self, artifact_id: str) -> ArtifactRecord:
        return self._records[str(artifact_id or "").strip()]

    def resolve(self, artifact_id: str) -> Path:
        record = self.get(artifact_id)
        path = self._path_from_file_key(record.file_key)
        if not path.exists():
            raise FileNotFoundError(str(path))
        return path

    def list(self, *, artifact_kind: str = "", limit: int = 100) -> list[ArtifactRecord]:
        normalized_kind = str(artifact_kind or "").strip().lower()
        normalized_limit = max(1, min(int(limit or 100), 500))
        rows = list(self._records.values())
        if normalized_kind:
            rows = [item for item in rows if str(item.artifact_kind or "").strip().lower() == normalized_kind]
        rows.sort(key=lambda item: (str(item.created_at or ""), item.artifact_id), reverse=True)
        return rows[:normalized_limit]

    def update_metadata(self, artifact_id: str, metadata_patch: dict[str, Any]) -> ArtifactRecord:
        record = self.get(artifact_id)
        record.metadata = self._merge_metadata(record.metadata, metadata_patch)
        record.updated_at = self.clock.utcnow().isoformat()
        self._flush_state()
        return record

    def _file_key(self, path: Path) -> str:
        try:
            return str(path.relative_to(self.output_root.resolve()))
        except ValueError:
            return f"abs::{path}"

    def _path_from_file_key(self, file_key: str) -> Path:
        text = str(file_key or "").strip()
        if text.startswith("abs::"):
            return Path(text[5:])
        return (self.output_root / text).resolve()

    @staticmethod
    def _merge_metadata(current: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
        merged = dict(current or {})
        for key, value in (patch or {}).items():
            if value is not None:
                merged[str(key)] = value
        return merged

    @staticmethod
    def _sha256_file(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            while True:
                chunk = handle.read(1024 * 1024)
                if not chunk:
                    break
                digest.update(chunk)
        return digest.hexdigest()

    def _load_state(self) -> None:
        if self.repository is None:
            return
        payload = self.repository.load_state()
        for item in payload.get("artifacts", []):
            try:
                record = ArtifactRecord(
                    artifact_id=str(item.get("artifact_id", "") or ""),
                    artifact_kind=str(item.get("artifact_kind", "") or "artifact"),
                    storage_backend=str(item.get("storage_backend", "") or "local"),
                    file_key=str(item.get("file_key", "") or ""),
                    filename=str(item.get("filename", "") or ""),
                    sha256=str(item.get("sha256", "") or ""),
                    size_bytes=int(item.get("size_bytes", 0) or 0),
                    created_at=str(item.get("created_at", "") or ""),
                    updated_at=str(item.get("updated_at", "") or ""),
                    metadata=dict(item.get("metadata", {}) or {}),
                )
            except Exception:
                continue
            if not record.artifact_id:
                continue
            self._records[record.artifact_id] = record
            self._artifact_ids_by_file_key[record.file_key] = record.artifact_id

    def _flush_state(self) -> None:
        if self.repository is None:
            return
        self.repository.save_state(
            {
                "artifacts": [
                    {
                        "artifact_id": item.artifact_id,
                        "artifact_kind": item.artifact_kind,
                        "storage_backend": item.storage_backend,
                        "file_key": item.file_key,
                        "filename": item.filename,
                        "sha256": item.sha256,
                        "size_bytes": item.size_bytes,
                        "created_at": item.created_at,
                        "updated_at": item.updated_at,
                        "metadata": dict(item.metadata or {}),
                    }
                    for item in self._records.values()
                ]
            }
        )
