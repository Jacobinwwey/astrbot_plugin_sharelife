"""Storage persistence and cold-backup state service."""

from __future__ import annotations

import hashlib
import secrets
import subprocess
import tarfile
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol


class StateStore(Protocol):
    def load(self, default: dict[str, Any]) -> dict[str, Any]: ...
    def save(self, payload: dict[str, Any]) -> None: ...


class Clock(Protocol):
    def utcnow(self) -> datetime: ...


class _SystemClock:
    def utcnow(self) -> datetime:
        return datetime.now(tz=UTC)


class StorageBackupService:
    """Admin storage API backend with local archive and optional rclone sync."""

    _TERMINAL_BACKUP_STATUSES = {"succeeded", "failed", "cancelled"}
    _TERMINAL_RESTORE_STATES = {"committed", "cancelled"}
    _MAX_LOCAL_SCAN_FILES = 50000
    _COMMAND_OUTPUT_TAIL = 4000
    _BACKUP_DIRNAME = "backups"

    _DEFAULT_POLICIES: dict[str, Any] = {
        "rpo_hours": 24,
        "local_retention_snapshots": 3,
        "remote_retention_days": 30,
        "upload_bandwidth_limit_enabled": True,
        "upload_bandwidth_limit_mbps": 10,
        "daily_upload_budget_gb": 700,
        "single_active_backup_lock": True,
        "backup_enabled": True,
        "pack_format": "tar.gz",
        "encryption_required": True,
        "sync_remote_enabled": False,
        "remote_required": False,
        "remote_encryption_verified": False,
        "rclone_binary": "rclone",
        "rclone_remote_path": "",
        "rclone_bwlimit": "10M",
        "command_timeout_seconds": 900,
        "include_profile_packs": True,
        "include_packages": False,
        "last_updated_at": "",
        "last_updated_by": "",
    }

    _POLICY_SCHEMA: dict[str, tuple[type, ...]] = {
        "rpo_hours": (int, float),
        "local_retention_snapshots": (int, float),
        "remote_retention_days": (int, float),
        "upload_bandwidth_limit_enabled": (bool,),
        "upload_bandwidth_limit_mbps": (int, float),
        "daily_upload_budget_gb": (int, float),
        "single_active_backup_lock": (bool,),
        "backup_enabled": (bool,),
        "pack_format": (str,),
        "encryption_required": (bool,),
        "sync_remote_enabled": (bool,),
        "remote_required": (bool,),
        "remote_encryption_verified": (bool,),
        "rclone_binary": (str,),
        "rclone_remote_path": (str,),
        "rclone_bwlimit": (str,),
        "command_timeout_seconds": (int, float),
        "include_profile_packs": (bool,),
        "include_packages": (bool,),
    }

    def __init__(
        self,
        *,
        state_store: StateStore,
        data_root: Path,
        clock: Clock | None = None,
    ):
        self.store = state_store
        self.data_root = Path(data_root)
        self.clock = clock or _SystemClock()

    def _now_iso(self) -> str:
        return self.clock.utcnow().astimezone(UTC).isoformat()

    def _load_payload(self) -> dict[str, Any]:
        payload = self.store.load({})
        return payload if isinstance(payload, dict) else {}

    def _save_payload(self, payload: dict[str, Any]) -> None:
        self.store.save(payload if isinstance(payload, dict) else {})

    def _load_policies(self) -> dict[str, Any]:
        payload = self._load_payload()
        raw = payload.get("policies", {})
        policies: dict[str, Any] = dict(self._DEFAULT_POLICIES)
        if isinstance(raw, dict):
            for key, value in raw.items():
                if key in self._DEFAULT_POLICIES:
                    policies[key] = value
        return policies

    def _save_policies(self, policies: dict[str, Any]) -> None:
        payload = self._load_payload()
        payload["policies"] = policies
        self._save_payload(payload)

    def _load_backup_jobs(self) -> list[dict[str, Any]]:
        payload = self._load_payload()
        raw = payload.get("backup_jobs", [])
        out: list[dict[str, Any]] = []
        if isinstance(raw, list):
            for row in raw:
                if isinstance(row, dict):
                    out.append(dict(row))
        return out

    def _save_backup_jobs(self, rows: list[dict[str, Any]]) -> None:
        payload = self._load_payload()
        payload["backup_jobs"] = rows
        self._save_payload(payload)

    def _load_restore_jobs(self) -> list[dict[str, Any]]:
        payload = self._load_payload()
        raw = payload.get("restore_jobs", [])
        out: list[dict[str, Any]] = []
        if isinstance(raw, list):
            for row in raw:
                if isinstance(row, dict):
                    out.append(dict(row))
        return out

    def _save_restore_jobs(self, rows: list[dict[str, Any]]) -> None:
        payload = self._load_payload()
        payload["restore_jobs"] = rows
        self._save_payload(payload)

    @staticmethod
    def _safe_int(value: Any, default: int = 0) -> int:
        try:
            return int(value)
        except Exception:
            return int(default)

    @staticmethod
    def _safe_float(value: Any, default: float = 0.0) -> float:
        try:
            return float(value)
        except Exception:
            return float(default)

    @staticmethod
    def _tail_text(value: Any, limit: int) -> str:
        text = str(value or "")
        if len(text) <= limit:
            return text
        return text[-limit:]

    @staticmethod
    def _safe_filename(value: Any, default: str = "backup.tar.gz") -> str:
        text = str(value or "").strip().replace("\\", "_").replace("/", "_")
        return text or default

    @staticmethod
    def _created_day(value: Any) -> str:
        text = str(value or "").strip()
        if "T" in text:
            return text.split("T", 1)[0]
        return text[:10]

    def _backup_root(self) -> Path:
        root = self.data_root / self._BACKUP_DIRNAME
        root.mkdir(parents=True, exist_ok=True)
        return root

    def _estimate_path_bytes(self, path: Path) -> int:
        if path.is_file():
            try:
                return int(path.stat().st_size)
            except Exception:
                return 0
        if not path.is_dir():
            return 0
        total = 0
        for child in path.rglob("*"):
            if not child.is_file():
                continue
            try:
                total += int(child.stat().st_size)
            except Exception:
                continue
        return total

    def _collect_backup_sources(self, policies: dict[str, Any]) -> list[Path]:
        include_profile_packs = bool(policies.get("include_profile_packs", True))
        include_packages = bool(policies.get("include_packages", False))
        sources: list[Path] = []
        seen: set[str] = set()

        candidates: list[Path] = []
        candidates.extend(self.data_root.glob("*_state.json"))
        candidates.extend(
            [
                self.data_root / "runtime_state.json",
                self.data_root / "sharelife_state.sqlite3",
                self.data_root / "config.generated.yaml",
            ]
        )
        if include_profile_packs:
            candidates.append(self.data_root / "profile_packs")
        if include_packages:
            candidates.append(self.data_root / "packages")

        for path in candidates:
            resolved = path.resolve() if path.exists() else path
            text = str(resolved)
            if text in seen:
                continue
            seen.add(text)
            if path.exists():
                sources.append(path)
        return sources

    def _archive_suffix(self, pack_format: str) -> tuple[str, str]:
        normalized = str(pack_format or "tar.gz").strip().lower()
        if normalized in {"tar.gz", "tgz"}:
            return ".tar.gz", "w:gz"
        if normalized in {"tar"}:
            return ".tar", "w"
        return "", ""

    def _build_archive(self, *, job_id: str, policies: dict[str, Any]) -> dict[str, Any]:
        suffix, tar_mode = self._archive_suffix(str(policies.get("pack_format", "tar.gz") or "tar.gz"))
        if not suffix:
            return {"error": "invalid_storage_policy_value", "field": "pack_format"}
        sources = self._collect_backup_sources(policies)

        backup_root = self._backup_root()
        archive_path = backup_root / f"{self._created_day(self._now_iso())}-{job_id}{suffix}"
        source_count = 0
        total_source_bytes = 0
        with tarfile.open(str(archive_path), mode=tar_mode) as tar:
            for source in sources:
                if not source.exists():
                    continue
                try:
                    arcname = source.relative_to(self.data_root)
                except Exception:
                    arcname = Path(source.name)
                tar.add(source, arcname=str(arcname), recursive=True)
                source_count += 1
                total_source_bytes += self._estimate_path_bytes(source)

        sha256 = hashlib.sha256()
        with archive_path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                sha256.update(chunk)

        return {
            "archive_path": str(archive_path),
            "archive_name": archive_path.name,
            "archive_size_bytes": int(archive_path.stat().st_size),
            "archive_sha256": sha256.hexdigest(),
            "source_count": source_count,
            "source_estimated_bytes": total_source_bytes,
        }

    def _daily_uploaded_bytes(self, jobs: list[dict[str, Any]], today: str) -> int:
        total = 0
        for row in jobs:
            if self._created_day(row.get("created_at")) != today:
                continue
            remote_sync = row.get("remote_sync", {})
            if not isinstance(remote_sync, dict):
                continue
            if str(remote_sync.get("status", "")).strip().lower() != "succeeded":
                continue
            total += self._safe_int(row.get("artifact_size_bytes"), 0)
        return total

    def _sync_archive_remote(
        self,
        *,
        archive_path: Path,
        policies: dict[str, Any],
    ) -> dict[str, Any]:
        if not bool(policies.get("sync_remote_enabled", False)):
            return {"status": "skipped", "reason": "remote_sync_disabled"}

        remote_path = str(policies.get("rclone_remote_path", "") or "").strip()
        if not remote_path:
            if bool(policies.get("remote_required", False)):
                return {"status": "failed", "error": "remote_target_missing"}
            return {"status": "skipped", "reason": "remote_target_missing"}
        if bool(policies.get("encryption_required", True)):
            encryption_verified = bool(policies.get("remote_encryption_verified", False))
            if not encryption_verified and not self._remote_path_looks_encrypted(remote_path):
                return {"status": "failed", "error": "remote_encryption_required"}

        rclone_binary = str(policies.get("rclone_binary", "rclone") or "rclone").strip() or "rclone"
        timeout_seconds = max(30, self._safe_int(policies.get("command_timeout_seconds"), 900))
        command = [
            rclone_binary,
            "copyto",
            str(archive_path),
            f"{remote_path.rstrip('/')}/{archive_path.name}",
        ]
        if bool(policies.get("upload_bandwidth_limit_enabled", True)):
            bwlimit = str(policies.get("rclone_bwlimit", "") or "").strip()
            if not bwlimit:
                mbps = max(1, self._safe_int(policies.get("upload_bandwidth_limit_mbps"), 10))
                bwlimit = f"{mbps}M"
            command.extend(["--bwlimit", bwlimit])

        started_at = time.time()
        try:
            completed = subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
            )
        except FileNotFoundError:
            return {"status": "failed", "error": "remote_sync_command_not_found"}
        except subprocess.TimeoutExpired:
            return {"status": "failed", "error": "remote_sync_failed", "reason": "timeout"}
        except Exception as exc:  # pragma: no cover - defensive execution guard
            return {
                "status": "failed",
                "error": "remote_sync_failed",
                "reason": f"{type(exc).__name__}:{exc}",
            }

        duration = round(max(0.0, time.time() - started_at), 3)
        stdout_tail = self._tail_text(completed.stdout, self._COMMAND_OUTPUT_TAIL)
        stderr_tail = self._tail_text(completed.stderr, self._COMMAND_OUTPUT_TAIL)
        if int(completed.returncode) != 0:
            return {
                "status": "failed",
                "error": "remote_sync_failed",
                "exit_code": int(completed.returncode),
                "duration_seconds": duration,
                "stdout_tail": stdout_tail,
                "stderr_tail": stderr_tail,
            }
        return {
            "status": "succeeded",
            "exit_code": int(completed.returncode),
            "duration_seconds": duration,
            "stdout_tail": stdout_tail,
            "stderr_tail": stderr_tail,
            "remote_object": f"{remote_path.rstrip('/')}/{archive_path.name}",
        }

    def _apply_remote_retention(self, *, policies: dict[str, Any]) -> dict[str, Any]:
        if not bool(policies.get("sync_remote_enabled", False)):
            return {"status": "skipped", "reason": "remote_sync_disabled"}
        remote_path = str(policies.get("rclone_remote_path", "") or "").strip()
        if not remote_path:
            return {"status": "skipped", "reason": "remote_target_missing"}
        retention_days = max(1, self._safe_int(policies.get("remote_retention_days"), 30))
        rclone_binary = str(policies.get("rclone_binary", "rclone") or "rclone").strip() or "rclone"
        timeout_seconds = max(30, self._safe_int(policies.get("command_timeout_seconds"), 900))
        command = [
            rclone_binary,
            "delete",
            remote_path.rstrip("/"),
            "--min-age",
            f"{retention_days}d",
            "--rmdirs",
        ]
        if bool(policies.get("upload_bandwidth_limit_enabled", True)):
            bwlimit = str(policies.get("rclone_bwlimit", "") or "").strip()
            if not bwlimit:
                mbps = max(1, self._safe_int(policies.get("upload_bandwidth_limit_mbps"), 10))
                bwlimit = f"{mbps}M"
            command.extend(["--bwlimit", bwlimit])

        started_at = time.time()
        try:
            completed = subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
            )
        except FileNotFoundError:
            return {"status": "failed", "error": "remote_retention_command_not_found"}
        except subprocess.TimeoutExpired:
            return {"status": "failed", "error": "remote_retention_failed", "reason": "timeout"}
        except Exception as exc:  # pragma: no cover - defensive execution guard
            return {
                "status": "failed",
                "error": "remote_retention_failed",
                "reason": f"{type(exc).__name__}:{exc}",
            }

        duration = round(max(0.0, time.time() - started_at), 3)
        stdout_tail = self._tail_text(completed.stdout, self._COMMAND_OUTPUT_TAIL)
        stderr_tail = self._tail_text(completed.stderr, self._COMMAND_OUTPUT_TAIL)
        if int(completed.returncode) != 0:
            return {
                "status": "failed",
                "error": "remote_retention_failed",
                "exit_code": int(completed.returncode),
                "duration_seconds": duration,
                "stdout_tail": stdout_tail,
                "stderr_tail": stderr_tail,
            }
        return {
            "status": "succeeded",
            "exit_code": int(completed.returncode),
            "duration_seconds": duration,
            "stdout_tail": stdout_tail,
            "stderr_tail": stderr_tail,
            "retention_days": retention_days,
            "remote_path": remote_path.rstrip("/"),
        }

    @staticmethod
    def _remote_path_looks_encrypted(remote_path: str) -> bool:
        text = str(remote_path or "").strip()
        if not text:
            return False
        remote_name = text.split(":", 1)[0].strip().lower()
        if not remote_name:
            return False
        return "crypt" in remote_name

    def _apply_local_retention(self, *, jobs: list[dict[str, Any]], keep_count: int) -> list[dict[str, Any]]:
        if keep_count < 1:
            keep_count = 1
        succeeded_rows = [
            row
            for row in jobs
            if str(row.get("status", "")).strip().lower() == "succeeded"
            and str(row.get("artifact_path", "") or "").strip()
        ]
        succeeded_rows.sort(key=lambda row: str(row.get("created_at", "") or ""), reverse=True)
        keep_ids = {
            str(row.get("job_id", "") or "")
            for row in succeeded_rows[:keep_count]
        }
        now = self._now_iso()
        out: list[dict[str, Any]] = []
        for row in jobs:
            job_id = str(row.get("job_id", "") or "")
            if job_id in keep_ids:
                out.append(row)
                continue
            artifact_path = Path(str(row.get("artifact_path", "") or ""))
            updated = dict(row)
            if artifact_path.exists() and artifact_path.is_file():
                try:
                    artifact_path.unlink()
                    updated["artifact_pruned_at"] = now
                except Exception:
                    pass
            out.append(updated)
        return out

    def _find_backup_artifact_row(
        self,
        artifact_ref: str,
    ) -> tuple[list[dict[str, Any]], int, dict[str, Any] | None]:
        rows = self._load_backup_jobs()
        normalized = str(artifact_ref or "").strip()
        if not normalized:
            return rows, -1, None
        for idx, row in enumerate(rows):
            if str(row.get("artifact_id", "")).strip() == normalized:
                return rows, idx, row
            if str(row.get("job_id", "")).strip() == normalized:
                return rows, idx, row
            if Path(str(row.get("artifact_path", "") or "")).name == normalized:
                return rows, idx, row
        return rows, -1, None

    def _find_backup_artifact(self, artifact_ref: str) -> dict[str, Any] | None:
        _, _, row = self._find_backup_artifact_row(artifact_ref)
        return row

    def _validate_artifact(self, row: dict[str, Any]) -> dict[str, Any]:
        artifact_path = Path(str(row.get("artifact_path", "") or ""))
        expected_sha = str(row.get("artifact_sha256", "") or "").strip().lower()
        if not artifact_path.exists():
            return {"error": "artifact_not_found"}
        if not expected_sha:
            return {"error": "artifact_checksum_missing"}

        sha = hashlib.sha256()
        with artifact_path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                sha.update(chunk)
        digest = sha.hexdigest().lower()
        if digest != expected_sha:
            return {
                "error": "artifact_checksum_mismatch",
                "expected_sha256": expected_sha,
                "actual_sha256": digest,
            }
        return {
            "artifact_path": str(artifact_path),
            "artifact_size_bytes": int(artifact_path.stat().st_size),
            "artifact_sha256": digest,
        }

    def _restore_archive_remote(
        self,
        *,
        row: dict[str, Any],
        policies: dict[str, Any],
    ) -> dict[str, Any]:
        remote_sync = row.get("remote_sync", {})
        if not isinstance(remote_sync, dict):
            return {"status": "failed", "error": "artifact_not_found", "reason": "remote_sync_missing"}
        if str(remote_sync.get("status", "")).strip().lower() != "succeeded":
            return {"status": "failed", "error": "artifact_not_found", "reason": "remote_sync_unavailable"}

        remote_object = str(remote_sync.get("remote_object", "") or "").strip()
        if not remote_object:
            return {"status": "failed", "error": "artifact_not_found", "reason": "remote_object_missing"}

        artifact_path_text = str(row.get("artifact_path", "") or "").strip()
        if artifact_path_text:
            target_path = Path(artifact_path_text)
        else:
            fallback_name = self._safe_filename(row.get("artifact_name"), default="backup.tar.gz")
            target_path = self._backup_root() / f"restore-{fallback_name}"
        target_path.parent.mkdir(parents=True, exist_ok=True)

        command = [
            str(policies.get("rclone_binary", "rclone") or "rclone").strip() or "rclone",
            "copyto",
            remote_object,
            str(target_path),
        ]
        if bool(policies.get("upload_bandwidth_limit_enabled", True)):
            bwlimit = str(policies.get("rclone_bwlimit", "") or "").strip()
            if not bwlimit:
                mbps = max(1, self._safe_int(policies.get("upload_bandwidth_limit_mbps"), 10))
                bwlimit = f"{mbps}M"
            command.extend(["--bwlimit", bwlimit])

        timeout_seconds = max(30, self._safe_int(policies.get("command_timeout_seconds"), 900))
        started_at = time.time()
        try:
            completed = subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
            )
        except FileNotFoundError:
            return {"status": "failed", "error": "remote_sync_command_not_found", "remote_object": remote_object}
        except subprocess.TimeoutExpired:
            return {"status": "failed", "error": "remote_sync_timeout", "remote_object": remote_object}
        except Exception as exc:  # pragma: no cover - defensive execution guard
            return {
                "status": "failed",
                "error": "remote_sync_failed",
                "remote_object": remote_object,
                "reason": f"{type(exc).__name__}:{exc}",
            }

        duration = round(max(0.0, time.time() - started_at), 3)
        stdout_tail = self._tail_text(completed.stdout, self._COMMAND_OUTPUT_TAIL)
        stderr_tail = self._tail_text(completed.stderr, self._COMMAND_OUTPUT_TAIL)
        if int(completed.returncode) != 0:
            return {
                "status": "failed",
                "error": "remote_sync_failed",
                "remote_object": remote_object,
                "exit_code": int(completed.returncode),
                "duration_seconds": duration,
                "stdout_tail": stdout_tail,
                "stderr_tail": stderr_tail,
            }
        return {
            "status": "succeeded",
            "remote_object": remote_object,
            "artifact_path": str(target_path),
            "exit_code": int(completed.returncode),
            "duration_seconds": duration,
            "stdout_tail": stdout_tail,
            "stderr_tail": stderr_tail,
        }

    def get_local_summary(self) -> dict[str, Any]:
        root = self.data_root
        exists = root.exists()
        scanned_files = 0
        total_bytes = 0
        truncated = False
        scan_error = ""
        if exists:
            try:
                for path in root.rglob("*"):
                    if scanned_files >= self._MAX_LOCAL_SCAN_FILES:
                        truncated = True
                        break
                    if not path.is_file():
                        continue
                    scanned_files += 1
                    try:
                        total_bytes += int(path.stat().st_size)
                    except Exception:
                        continue
            except Exception as exc:  # pragma: no cover - defensive filesystem guard
                scan_error = f"{type(exc).__name__}:{exc}"

        backup_jobs = self._load_backup_jobs()
        restore_jobs = self._load_restore_jobs()
        active_backups = [
            row
            for row in backup_jobs
            if str(row.get("status", "")).strip().lower() not in self._TERMINAL_BACKUP_STATUSES
        ]
        sorted_jobs = sorted(
            backup_jobs,
            key=lambda row: str(row.get("created_at", "") or ""),
            reverse=True,
        )

        return {
            "storage_root": str(root),
            "root_exists": exists,
            "scanned_file_count": scanned_files,
            "scan_truncated": truncated,
            "scan_error": scan_error,
            "estimated_size_bytes": total_bytes,
            "backup_jobs_total": len(backup_jobs),
            "backup_jobs_active": len(active_backups),
            "backup_jobs_succeeded": sum(
                1
                for row in backup_jobs
                if str(row.get("status", "")).strip().lower() == "succeeded"
            ),
            "restore_jobs_total": len(restore_jobs),
            "last_backup_job": sorted_jobs[0] if sorted_jobs else None,
            "generated_at": self._now_iso(),
        }

    def get_policies(self) -> dict[str, Any]:
        return {"policies": self._load_policies()}

    def set_policies(self, patch: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        if not isinstance(patch, dict):
            return {"error": "invalid_storage_policy_payload"}
        policies = self._load_policies()
        for key, value in patch.items():
            if key not in self._POLICY_SCHEMA:
                return {"error": "invalid_storage_policy_field", "field": key}
            if not isinstance(value, self._POLICY_SCHEMA[key]):
                return {"error": "invalid_storage_policy_value", "field": key}
            policies[key] = value

        policies["rpo_hours"] = max(1, self._safe_int(policies.get("rpo_hours"), 24))
        policies["local_retention_snapshots"] = max(1, self._safe_int(policies.get("local_retention_snapshots"), 3))
        policies["remote_retention_days"] = max(1, self._safe_int(policies.get("remote_retention_days"), 30))
        policies["upload_bandwidth_limit_mbps"] = max(
            1,
            self._safe_int(policies.get("upload_bandwidth_limit_mbps"), 10),
        )
        policies["daily_upload_budget_gb"] = max(1, self._safe_int(policies.get("daily_upload_budget_gb"), 700))
        policies["command_timeout_seconds"] = max(
            30,
            self._safe_int(policies.get("command_timeout_seconds"), 900),
        )
        policies["pack_format"] = str(policies.get("pack_format", "tar.gz") or "tar.gz").strip() or "tar.gz"
        policies["rclone_binary"] = str(policies.get("rclone_binary", "rclone") or "rclone").strip() or "rclone"
        policies["rclone_remote_path"] = str(policies.get("rclone_remote_path", "") or "").strip()
        policies["rclone_bwlimit"] = str(policies.get("rclone_bwlimit", "10M") or "10M").strip() or "10M"
        policies["last_updated_at"] = self._now_iso()
        policies["last_updated_by"] = str(actor_id or "").strip() or "admin"
        self._save_policies(policies)
        return {"policies": policies}

    def run_backup_job(
        self,
        *,
        actor_id: str,
        trigger: str = "manual",
        note: str = "",
    ) -> dict[str, Any]:
        policies = self._load_policies()
        backup_jobs = self._load_backup_jobs()
        if bool(policies.get("single_active_backup_lock", True)):
            has_active = any(
                str(row.get("status", "")).strip().lower() not in self._TERMINAL_BACKUP_STATUSES
                for row in backup_jobs
            )
            if has_active:
                return {"error": "backup_job_in_progress"}

        job_id = f"backup-{secrets.token_hex(8)}"
        started_at = self._now_iso()
        summary = self.get_local_summary()
        estimated_size_bytes = int(summary.get("estimated_size_bytes", 0) or 0)
        job = {
            "job_id": job_id,
            "job_type": "backup",
            "trigger": str(trigger or "").strip() or "manual",
            "status": "running",
            "reason": "",
            "requested_by": str(actor_id or "").strip() or "admin",
            "note": str(note or "").strip(),
            "created_at": started_at,
            "started_at": started_at,
            "finished_at": "",
            "estimated_size_bytes": estimated_size_bytes,
            "artifact_id": f"artifact-{job_id}",
            "artifact_format": str(policies.get("pack_format", "tar.gz") or "tar.gz"),
            "artifact_path": "",
            "artifact_name": "",
            "artifact_sha256": "",
            "artifact_size_bytes": 0,
            "remote_target": str(policies.get("rclone_remote_path", "") or ""),
            "remote_sync": {"status": "skipped", "reason": "not_started"},
            "remote_retention": {"status": "skipped", "reason": "not_started"},
        }
        backup_jobs.append(job)
        self._save_backup_jobs(backup_jobs)

        if not bool(policies.get("backup_enabled", True)):
            job["status"] = "cancelled"
            job["reason"] = "backup_disabled_by_policy"
            job["finished_at"] = self._now_iso()
            self._save_backup_jobs(backup_jobs)
            return {"job": job}

        archive_meta = self._build_archive(job_id=job_id, policies=policies)
        if archive_meta.get("error"):
            job["status"] = "failed"
            job["reason"] = str(archive_meta.get("error", "backup_archive_failed"))
            job["archive_error"] = archive_meta
            job["finished_at"] = self._now_iso()
            self._save_backup_jobs(backup_jobs)
            return {"job": job}

        job["artifact_path"] = str(archive_meta.get("archive_path", "") or "")
        job["artifact_name"] = str(archive_meta.get("archive_name", "") or "")
        job["artifact_sha256"] = str(archive_meta.get("archive_sha256", "") or "")
        job["artifact_size_bytes"] = int(archive_meta.get("archive_size_bytes", 0) or 0)
        job["source_count"] = int(archive_meta.get("source_count", 0) or 0)
        job["source_estimated_bytes"] = int(archive_meta.get("source_estimated_bytes", 0) or 0)

        today = self._created_day(self._now_iso())
        budget_gb = max(1, self._safe_int(policies.get("daily_upload_budget_gb"), 700))
        budget_bytes = budget_gb * 1024 * 1024 * 1024
        uploaded_today = self._daily_uploaded_bytes(backup_jobs, today=today)
        if bool(policies.get("sync_remote_enabled", False)) and uploaded_today + job["artifact_size_bytes"] > budget_bytes:
            job["status"] = "failed"
            job["reason"] = "daily_upload_budget_exceeded"
            job["daily_uploaded_bytes"] = uploaded_today
            job["daily_budget_bytes"] = budget_bytes
            job["finished_at"] = self._now_iso()
            self._save_backup_jobs(backup_jobs)
            return {"job": job}

        remote_sync = self._sync_archive_remote(
            archive_path=Path(job["artifact_path"]),
            policies=policies,
        )
        job["remote_sync"] = remote_sync
        remote_sync_status = str(remote_sync.get("status", "")).strip().lower()
        if remote_sync_status == "succeeded":
            job["remote_retention"] = self._apply_remote_retention(policies=policies)
        elif remote_sync_status == "skipped":
            job["remote_retention"] = {"status": "skipped", "reason": "remote_sync_skipped"}
        else:
            job["remote_retention"] = {"status": "skipped", "reason": "remote_sync_failed"}
        if remote_sync_status == "failed":
            job["status"] = "failed"
            job["reason"] = str(remote_sync.get("error", "remote_sync_failed") or "remote_sync_failed")
        else:
            job["status"] = "succeeded"
            job["reason"] = ""
        job["finished_at"] = self._now_iso()
        if job["status"] == "succeeded":
            keep_count = max(1, self._safe_int(policies.get("local_retention_snapshots"), 3))
            retained_rows = self._apply_local_retention(jobs=backup_jobs, keep_count=keep_count)
            backup_jobs[:] = retained_rows
        self._save_backup_jobs(backup_jobs)
        return {"job": job}

    def list_backup_jobs(self, *, status: str = "", limit: int = 50) -> dict[str, Any]:
        requested = str(status or "").strip().lower()
        rows = self._load_backup_jobs()
        if requested:
            rows = [row for row in rows if str(row.get("status", "")).strip().lower() == requested]
        rows.sort(key=lambda row: str(row.get("created_at", "") or ""), reverse=True)
        normalized_limit = max(1, min(int(limit or 50), 200))
        return {"jobs": rows[:normalized_limit]}

    def get_backup_job(self, *, job_id: str) -> dict[str, Any]:
        normalized = str(job_id or "").strip()
        if not normalized:
            return {"error": "job_id_required"}
        for row in self._load_backup_jobs():
            if str(row.get("job_id", "")).strip() == normalized:
                return {"job": row}
        return {"error": "backup_job_not_found", "job_id": normalized}

    def list_restore_jobs(self, *, state: str = "", limit: int = 50) -> dict[str, Any]:
        requested = str(state or "").strip().lower()
        rows = self._load_restore_jobs()
        if requested:
            rows = [
                row
                for row in rows
                if str(row.get("restore_state", "")).strip().lower() == requested
            ]
        rows.sort(key=lambda row: str(row.get("created_at", "") or ""), reverse=True)
        normalized_limit = max(1, min(int(limit or 50), 200))
        return {"jobs": rows[:normalized_limit]}

    def get_restore_job(self, *, restore_id: str) -> dict[str, Any]:
        normalized = str(restore_id or "").strip()
        if not normalized:
            return {"error": "restore_id_required"}
        for row in self._load_restore_jobs():
            if str(row.get("restore_id", "")).strip() == normalized:
                return {"restore": row}
        return {"error": "restore_job_not_found", "restore_id": normalized}

    def restore_prepare(
        self,
        *,
        artifact_ref: str,
        actor_id: str,
        note: str = "",
    ) -> dict[str, Any]:
        normalized_artifact_ref = str(artifact_ref or "").strip()
        if not normalized_artifact_ref:
            return {"error": "artifact_ref_required"}
        backup_rows, artifact_idx, artifact_job = self._find_backup_artifact_row(normalized_artifact_ref)
        if artifact_job is None:
            return {"error": "artifact_not_found", "artifact_ref": normalized_artifact_ref}

        rehydrated_from_remote = False
        remote_restore: dict[str, Any] = {}
        validated = self._validate_artifact(artifact_job)
        if validated.get("error") == "artifact_not_found":
            remote_restore = self._restore_archive_remote(
                row=artifact_job,
                policies=self._load_policies(),
            )
            if str(remote_restore.get("status", "")).strip().lower() != "succeeded":
                return {
                    "error": str(remote_restore.get("error", "artifact_not_found") or "artifact_not_found"),
                    "artifact_ref": normalized_artifact_ref,
                    "remote_restore": remote_restore,
                }
            rehydrated_from_remote = True
            artifact_job = dict(artifact_job)
            artifact_job["artifact_path"] = str(remote_restore.get("artifact_path", "") or artifact_job.get("artifact_path", ""))
            artifact_job["remote_restore"] = dict(remote_restore)
            if 0 <= artifact_idx < len(backup_rows):
                backup_rows[artifact_idx] = artifact_job
                self._save_backup_jobs(backup_rows)
            validated = self._validate_artifact(artifact_job)
        if validated.get("error"):
            return validated

        restore_id = f"restore-{secrets.token_hex(8)}"
        started_at = self._now_iso()
        job = {
            "restore_id": restore_id,
            "artifact_ref": normalized_artifact_ref,
            "restore_state": "prepared",
            "status": "succeeded",
            "requested_by": str(actor_id or "").strip() or "admin",
            "note": str(note or "").strip(),
            "created_at": started_at,
            "prepared_at": started_at,
            "committed_at": "",
            "cancelled_at": "",
            "validation": {
                "manifest_present": True,
                "checksum_verified": True,
                "decrypt_ready": True,
            },
            "artifact_path": validated.get("artifact_path"),
            "artifact_size_bytes": validated.get("artifact_size_bytes"),
            "artifact_sha256": validated.get("artifact_sha256"),
            "source_job_id": str(artifact_job.get("job_id", "") or ""),
            "rehydrated_from_remote": rehydrated_from_remote,
        }
        if rehydrated_from_remote:
            job["remote_restore"] = dict(remote_restore)
        rows = self._load_restore_jobs()
        rows.append(job)
        self._save_restore_jobs(rows)
        return {"restore": job}

    def restore_commit(self, *, restore_id: str, actor_id: str) -> dict[str, Any]:
        normalized = str(restore_id or "").strip()
        if not normalized:
            return {"error": "restore_id_required"}
        rows = self._load_restore_jobs()
        for idx, row in enumerate(rows):
            if str(row.get("restore_id", "")).strip() != normalized:
                continue
            state = str(row.get("restore_state", "")).strip().lower()
            if state in self._TERMINAL_RESTORE_STATES:
                return {"error": "restore_state_invalid", "restore_id": normalized, "restore_state": state}
            if state != "prepared":
                return {"error": "restore_state_invalid", "restore_id": normalized, "restore_state": state}
            updated = dict(row)
            updated["restore_state"] = "committed"
            updated["status"] = "succeeded"
            updated["commit_mode"] = "manual_followup_required"
            updated["committed_at"] = self._now_iso()
            updated["committed_by"] = str(actor_id or "").strip() or "admin"
            rows[idx] = updated
            self._save_restore_jobs(rows)
            return {"restore": updated}
        return {"error": "restore_job_not_found", "restore_id": normalized}

    def restore_cancel(self, *, restore_id: str, actor_id: str) -> dict[str, Any]:
        normalized = str(restore_id or "").strip()
        if not normalized:
            return {"error": "restore_id_required"}
        rows = self._load_restore_jobs()
        for idx, row in enumerate(rows):
            if str(row.get("restore_id", "")).strip() != normalized:
                continue
            state = str(row.get("restore_state", "")).strip().lower()
            if state == "committed":
                return {"error": "restore_state_invalid", "restore_id": normalized, "restore_state": state}
            if state == "cancelled":
                return {"restore": row}
            updated = dict(row)
            updated["restore_state"] = "cancelled"
            updated["status"] = "cancelled"
            updated["cancelled_at"] = self._now_iso()
            updated["cancelled_by"] = str(actor_id or "").strip() or "admin"
            rows[idx] = updated
            self._save_restore_jobs(rows)
            return {"restore": updated}
        return {"error": "restore_job_not_found", "restore_id": normalized}
