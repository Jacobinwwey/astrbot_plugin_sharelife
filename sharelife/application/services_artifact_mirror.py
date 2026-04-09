"""Remote mirror operations for package artifacts."""

from __future__ import annotations

import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol

from ..infrastructure.local_artifact_store import ArtifactRecord, ArtifactStore


class Clock(Protocol):
    def utcnow(self) -> datetime: ...


class ArtifactMirrorService:
    _COMMAND_OUTPUT_TAIL = 4000

    def __init__(self, *, artifact_store: ArtifactStore, clock: Clock):
        self.artifact_store = artifact_store
        self.clock = clock

    def list_artifacts(self, *, artifact_kind: str = "", limit: int = 50) -> dict[str, Any]:
        rows = [self._artifact_payload(item) for item in self.artifact_store.list(artifact_kind=artifact_kind, limit=limit)]
        return {
            "count": len(rows),
            "artifacts": rows,
        }

    def mirror_artifact(
        self,
        *,
        artifact_id: str,
        remote_path: str,
        actor_id: str,
        rclone_binary: str = "rclone",
        timeout_seconds: int = 300,
        bwlimit: str = "",
        encryption_required: bool = True,
        remote_encryption_verified: bool = False,
    ) -> dict[str, Any]:
        normalized_artifact_id = str(artifact_id or "").strip()
        if not normalized_artifact_id:
            return {"error": "artifact_id_required"}
        normalized_remote_path = str(remote_path or "").strip().rstrip("/")
        if ":" not in normalized_remote_path:
            return {"error": "remote_path_invalid", "artifact_id": normalized_artifact_id}
        if bool(encryption_required) and not bool(remote_encryption_verified):
            if not self._remote_path_looks_encrypted(normalized_remote_path):
                return {"error": "remote_encryption_required", "artifact_id": normalized_artifact_id}
        try:
            record = self.artifact_store.get(normalized_artifact_id)
        except KeyError:
            return {"error": "artifact_not_found", "artifact_id": normalized_artifact_id}
        try:
            local_path = self.artifact_store.resolve(normalized_artifact_id)
        except FileNotFoundError:
            return {"error": "artifact_missing", "artifact_id": normalized_artifact_id}

        target_remote_path = self._build_remote_path(
            remote_root=normalized_remote_path,
            artifact=record,
        )
        command = [
            str(rclone_binary or "rclone").strip() or "rclone",
            "copyto",
            str(local_path),
            target_remote_path,
        ]
        if str(bwlimit or "").strip():
            command.extend(["--bwlimit", str(bwlimit).strip()])
        timeout = max(30, int(timeout_seconds or 300))
        started_at = time.monotonic()
        try:
            completed = subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except FileNotFoundError:
            mirror = {
                "status": "failed",
                "error": "remote_sync_command_not_found",
                "remote_path": target_remote_path,
                "mirrored_at": self._now_iso(),
                "actor_id": actor_id,
            }
            self.artifact_store.update_metadata(normalized_artifact_id, {"remote_mirror": mirror})
            return {"error": "remote_sync_command_not_found", "artifact_id": normalized_artifact_id, "mirror": mirror}
        except subprocess.TimeoutExpired:
            mirror = {
                "status": "failed",
                "error": "remote_sync_timeout",
                "remote_path": target_remote_path,
                "mirrored_at": self._now_iso(),
                "actor_id": actor_id,
            }
            self.artifact_store.update_metadata(normalized_artifact_id, {"remote_mirror": mirror})
            return {"error": "remote_sync_timeout", "artifact_id": normalized_artifact_id, "mirror": mirror}

        duration = round(max(0.0, time.monotonic() - started_at), 3)
        stdout_tail = self._tail_text(completed.stdout, self._COMMAND_OUTPUT_TAIL)
        stderr_tail = self._tail_text(completed.stderr, self._COMMAND_OUTPUT_TAIL)
        if int(completed.returncode) != 0:
            mirror = {
                "status": "failed",
                "error": "remote_sync_failed",
                "remote_path": target_remote_path,
                "mirrored_at": self._now_iso(),
                "actor_id": actor_id,
                "duration_seconds": duration,
                "exit_code": int(completed.returncode),
                "stdout_tail": stdout_tail,
                "stderr_tail": stderr_tail,
            }
            self.artifact_store.update_metadata(normalized_artifact_id, {"remote_mirror": mirror})
            return {"error": "remote_sync_failed", "artifact_id": normalized_artifact_id, "mirror": mirror}

        mirror = {
            "status": "succeeded",
            "remote_path": target_remote_path,
            "mirrored_at": self._now_iso(),
            "actor_id": actor_id,
            "duration_seconds": duration,
            "exit_code": int(completed.returncode),
            "stdout_tail": stdout_tail,
            "stderr_tail": stderr_tail,
            "sha256": record.sha256,
            "size_bytes": record.size_bytes,
        }
        updated = self.artifact_store.update_metadata(normalized_artifact_id, {"remote_mirror": mirror})
        return {
            "artifact": self._artifact_payload(updated),
            "mirror": mirror,
        }

    def _artifact_payload(self, artifact: ArtifactRecord) -> dict[str, Any]:
        local_path = ""
        try:
            local_path = str(self.artifact_store.resolve(artifact.artifact_id))
        except FileNotFoundError:
            local_path = ""
        return {
            "artifact_id": artifact.artifact_id,
            "artifact_kind": artifact.artifact_kind,
            "storage_backend": artifact.storage_backend,
            "file_key": artifact.file_key,
            "filename": artifact.filename,
            "sha256": artifact.sha256,
            "size_bytes": artifact.size_bytes,
            "created_at": artifact.created_at,
            "updated_at": artifact.updated_at,
            "path": local_path,
            "metadata": dict(artifact.metadata or {}),
        }

    @staticmethod
    def _tail_text(value: Any, limit: int) -> str:
        text = str(value or "")
        if len(text) <= limit:
            return text
        return text[-limit:]

    @staticmethod
    def _remote_path_looks_encrypted(remote_path: str) -> bool:
        text = str(remote_path or "").strip()
        if not text:
            return False
        remote_name = text.split(":", 1)[0].strip().lower()
        if not remote_name:
            return False
        return "crypt" in remote_name

    @staticmethod
    def _safe_remote_segment(value: str) -> str:
        text = str(value or "").strip().replace("\\", "_").replace("/", "_")
        return text or "artifact"

    def _build_remote_path(self, *, remote_root: str, artifact: ArtifactRecord) -> str:
        return "/".join(
            [
                remote_root.rstrip("/"),
                self._safe_remote_segment(artifact.artifact_kind),
                self._safe_remote_segment(artifact.artifact_id),
                self._safe_remote_segment(artifact.filename),
            ]
        )

    def _now_iso(self) -> str:
        return self.clock.utcnow().astimezone(UTC).isoformat()
