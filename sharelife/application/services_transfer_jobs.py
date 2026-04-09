"""Transfer job state for upload/download operations."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4

from ..infrastructure.json_state_store import JsonStateStore
from ..infrastructure.sqlite_state_store import SqliteStateStore
from ..infrastructure.system_clock import SystemClock
from ..infrastructure.transfer_job_repository import (
    JsonTransferJobRepository,
    SqliteTransferJobRepository,
    TransferJobRepository,
)


TRANSFER_JOB_STATUSES = {"queued", "running", "done", "failed", "cancelled"}
TRANSFER_JOB_FINAL_STATUSES = {"done", "failed", "cancelled"}


@dataclass(slots=True)
class TransferJob:
    job_id: str
    direction: str
    job_type: str
    actor_id: str
    actor_role: str
    user_id: str
    logical_key: str
    status: str
    created_at: datetime
    updated_at: datetime
    template_id: str = ""
    submission_id: str = ""
    filename: str = ""
    size_bytes: int = 0
    sha256: str = ""
    attempt_count: int = 1
    retry_count: int = 0
    max_attempts: int = 1
    idempotency_key: str = ""
    started_at: datetime | None = None
    finished_at: datetime | None = None
    failure_reason: str = ""
    failure_detail: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class TransferJobClaim:
    job: TransferJob
    should_execute: bool
    replayed: bool = False


class TransferJobService:
    def __init__(
        self,
        clock: SystemClock,
        state_store: JsonStateStore | SqliteStateStore | None = None,
        repository: TransferJobRepository | None = None,
    ):
        self.clock = clock
        self.state_store = state_store
        self.repository = self._build_repository(state_store=state_store, repository=repository)
        self._upload_jobs: dict[str, TransferJob] = {}
        self._download_jobs: dict[str, TransferJob] = {}
        self._job_ids_by_logical_key: dict[str, str] = {}
        self._load_state()

    @staticmethod
    def _build_repository(
        *,
        state_store: JsonStateStore | SqliteStateStore | None,
        repository: TransferJobRepository | None,
    ) -> TransferJobRepository | None:
        if repository is not None:
            return repository
        if state_store is None:
            return None
        if isinstance(state_store, SqliteStateStore):
            return SqliteTransferJobRepository(state_store.db_path, legacy_state_store=state_store)
        return JsonTransferJobRepository(state_store)

    def claim_job(
        self,
        *,
        direction: str,
        job_type: str,
        actor_id: str,
        actor_role: str,
        user_id: str = "",
        logical_key: str = "",
        template_id: str = "",
        submission_id: str = "",
        filename: str = "",
        idempotency_key: str = "",
        max_attempts: int = 1,
        metadata: dict[str, Any] | None = None,
    ) -> TransferJobClaim:
        normalized_direction = self._normalize_direction(direction)
        normalized_actor_id = str(actor_id or "").strip() or "anonymous"
        normalized_actor_role = str(actor_role or "").strip() or "member"
        normalized_user_id = str(user_id or "").strip()
        normalized_logical_key = str(logical_key or "").strip() or f"{normalized_direction}:{uuid4()}"
        effective_max_attempts = max(1, int(max_attempts or 1))
        now = self.clock.utcnow()

        existing = self._get_by_logical_key(normalized_logical_key)
        if existing is not None:
            existing.updated_at = now
            existing.max_attempts = max(existing.max_attempts, effective_max_attempts)
            if existing.status == "done":
                existing.attempt_count += 1
                existing.retry_count += 1
                self._flush_state()
                return TransferJobClaim(job=existing, should_execute=False, replayed=True)
            if existing.status in {"queued", "running"}:
                existing.attempt_count += 1
                existing.retry_count += 1
                self._flush_state()
                return TransferJobClaim(job=existing, should_execute=False, replayed=False)
            if existing.status == "failed" and existing.attempt_count < existing.max_attempts:
                existing.attempt_count += 1
                existing.retry_count += 1
                existing.status = "queued"
                existing.started_at = None
                existing.finished_at = None
                existing.failure_reason = ""
                existing.failure_detail = ""
                if filename:
                    existing.filename = str(filename or "").strip()
                if template_id:
                    existing.template_id = str(template_id or "").strip()
                if submission_id:
                    existing.submission_id = str(submission_id or "").strip()
                if idempotency_key:
                    existing.idempotency_key = str(idempotency_key or "").strip()
                if metadata:
                    existing.metadata = self._merge_metadata(existing.metadata, metadata)
                self._flush_state()
                return TransferJobClaim(job=existing, should_execute=True, replayed=False)
            self._flush_state()
            return TransferJobClaim(job=existing, should_execute=False, replayed=False)

        job = TransferJob(
            job_id=str(uuid4()),
            direction=normalized_direction,
            job_type=str(job_type or "").strip() or "transfer",
            actor_id=normalized_actor_id,
            actor_role=normalized_actor_role,
            user_id=normalized_user_id,
            logical_key=normalized_logical_key,
            status="queued",
            created_at=now,
            updated_at=now,
            template_id=str(template_id or "").strip(),
            submission_id=str(submission_id or "").strip(),
            filename=str(filename or "").strip(),
            max_attempts=effective_max_attempts,
            idempotency_key=str(idempotency_key or "").strip(),
            metadata=dict(metadata or {}),
        )
        self._jobs_for_direction(normalized_direction)[job.job_id] = job
        self._job_ids_by_logical_key[job.logical_key] = job.job_id
        self._flush_state()
        return TransferJobClaim(job=job, should_execute=True, replayed=False)

    def get(self, job_id: str) -> TransferJob:
        normalized_job_id = str(job_id or "").strip()
        if normalized_job_id in self._upload_jobs:
            return self._upload_jobs[normalized_job_id]
        return self._download_jobs[normalized_job_id]

    def mark_running(self, job_id: str) -> TransferJob:
        job = self.get(job_id)
        now = self.clock.utcnow()
        job.status = "running"
        job.updated_at = now
        if job.started_at is None:
            job.started_at = now
        self._flush_state()
        return job

    def mark_done(
        self,
        job_id: str,
        *,
        template_id: str = "",
        submission_id: str = "",
        filename: str = "",
        size_bytes: int | None = None,
        sha256: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> TransferJob:
        job = self.get(job_id)
        now = self.clock.utcnow()
        job.status = "done"
        job.updated_at = now
        job.finished_at = now
        if template_id:
            job.template_id = str(template_id or "").strip()
        if submission_id:
            job.submission_id = str(submission_id or "").strip()
        if filename:
            job.filename = str(filename or "").strip()
        if size_bytes is not None:
            job.size_bytes = max(0, int(size_bytes or 0))
        if sha256:
            job.sha256 = str(sha256 or "").strip()
        if metadata:
            job.metadata = self._merge_metadata(job.metadata, metadata)
        job.failure_reason = ""
        job.failure_detail = ""
        self._flush_state()
        return job

    def mark_failed(
        self,
        job_id: str,
        *,
        failure_reason: str,
        failure_detail: str = "",
        template_id: str = "",
        submission_id: str = "",
        filename: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> TransferJob:
        job = self.get(job_id)
        now = self.clock.utcnow()
        job.status = "failed"
        job.updated_at = now
        job.finished_at = now
        if template_id:
            job.template_id = str(template_id or "").strip()
        if submission_id:
            job.submission_id = str(submission_id or "").strip()
        if filename:
            job.filename = str(filename or "").strip()
        job.failure_reason = self._normalize_failure_reason(failure_reason)
        job.failure_detail = str(failure_detail or "").strip()
        if metadata:
            job.metadata = self._merge_metadata(job.metadata, metadata)
        self._flush_state()
        return job

    def cancel(self, job_id: str, *, failure_reason: str = "cancelled", failure_detail: str = "") -> TransferJob:
        job = self.get(job_id)
        now = self.clock.utcnow()
        job.status = "cancelled"
        job.updated_at = now
        job.finished_at = now
        job.failure_reason = self._normalize_failure_reason(failure_reason)
        job.failure_detail = str(failure_detail or "").strip()
        self._flush_state()
        return job

    def list_jobs(
        self,
        *,
        user_id: str = "",
        direction: str = "",
        status: str = "",
        limit: int = 50,
    ) -> list[TransferJob]:
        normalized_direction = str(direction or "").strip().lower()
        normalized_status = str(status or "").strip().lower()
        normalized_user_id = str(user_id or "").strip()
        rows: list[TransferJob] = []
        if normalized_direction in {"", "upload"}:
            rows.extend(self._upload_jobs.values())
        if normalized_direction in {"", "download"}:
            rows.extend(self._download_jobs.values())
        if normalized_user_id:
            rows = [row for row in rows if row.user_id == normalized_user_id]
        if normalized_status:
            rows = [row for row in rows if row.status == normalized_status]
        rows.sort(
            key=lambda row: (
                row.updated_at,
                row.created_at,
                row.job_id,
            ),
            reverse=True,
        )
        normalized_limit = max(1, min(int(limit or 50), 200))
        return rows[:normalized_limit]

    @staticmethod
    def _normalize_direction(direction: str) -> str:
        normalized = str(direction or "").strip().lower()
        if normalized not in {"upload", "download"}:
            return "upload"
        return normalized

    @staticmethod
    def _normalize_failure_reason(value: str) -> str:
        normalized = str(value or "").strip().lower().replace(" ", "_").replace("-", "_")
        return normalized or "unknown_error"

    @staticmethod
    def _merge_metadata(current: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
        merged = dict(current or {})
        for key, value in (patch or {}).items():
            if value is not None:
                merged[str(key)] = value
        return merged

    def _jobs_for_direction(self, direction: str) -> dict[str, TransferJob]:
        return self._upload_jobs if direction == "upload" else self._download_jobs

    def _get_by_logical_key(self, logical_key: str) -> TransferJob | None:
        job_id = self._job_ids_by_logical_key.get(logical_key)
        if not job_id:
            return None
        if job_id in self._upload_jobs:
            return self._upload_jobs[job_id]
        if job_id in self._download_jobs:
            return self._download_jobs[job_id]
        return None

    def _load_state(self) -> None:
        if self.repository is None:
            return
        payload = self.repository.load_state()
        for item in payload.get("upload_jobs", []):
            job = self._job_from_payload(item, direction="upload")
            self._upload_jobs[job.job_id] = job
            self._job_ids_by_logical_key[job.logical_key] = job.job_id
        for item in payload.get("download_jobs", []):
            job = self._job_from_payload(item, direction="download")
            self._download_jobs[job.job_id] = job
            self._job_ids_by_logical_key[job.logical_key] = job.job_id

    def _flush_state(self) -> None:
        if self.repository is None:
            return
        self.repository.save_state(
            {
                "upload_jobs": [self._job_payload(job) for job in self._upload_jobs.values()],
                "download_jobs": [self._job_payload(job) for job in self._download_jobs.values()],
            }
        )

    @staticmethod
    def _job_from_payload(item: dict[str, Any], *, direction: str) -> TransferJob:
        started_at = str(item.get("started_at", "") or "").strip()
        finished_at = str(item.get("finished_at", "") or "").strip()
        return TransferJob(
            job_id=str(item["job_id"]),
            direction=direction,
            job_type=str(item.get("job_type", "") or "transfer"),
            actor_id=str(item.get("actor_id", "") or ""),
            actor_role=str(item.get("actor_role", "") or ""),
            user_id=str(item.get("user_id", "") or ""),
            logical_key=str(item.get("logical_key", "") or ""),
            status=str(item.get("status", "") or "queued"),
            created_at=datetime.fromisoformat(str(item["created_at"])),
            updated_at=datetime.fromisoformat(str(item["updated_at"])),
            template_id=str(item.get("template_id", "") or ""),
            submission_id=str(item.get("submission_id", "") or ""),
            filename=str(item.get("filename", "") or ""),
            size_bytes=int(item.get("size_bytes", 0) or 0),
            sha256=str(item.get("sha256", "") or ""),
            attempt_count=max(1, int(item.get("attempt_count", 1) or 1)),
            retry_count=max(0, int(item.get("retry_count", 0) or 0)),
            max_attempts=max(1, int(item.get("max_attempts", 1) or 1)),
            idempotency_key=str(item.get("idempotency_key", "") or ""),
            started_at=datetime.fromisoformat(started_at) if started_at else None,
            finished_at=datetime.fromisoformat(finished_at) if finished_at else None,
            failure_reason=str(item.get("failure_reason", "") or ""),
            failure_detail=str(item.get("failure_detail", "") or ""),
            metadata=dict(item.get("metadata", {}) or {}),
        )

    @staticmethod
    def _job_payload(job: TransferJob) -> dict[str, Any]:
        return {
            "job_id": job.job_id,
            "direction": job.direction,
            "job_type": job.job_type,
            "actor_id": job.actor_id,
            "actor_role": job.actor_role,
            "user_id": job.user_id,
            "logical_key": job.logical_key,
            "status": job.status,
            "created_at": job.created_at.isoformat(),
            "updated_at": job.updated_at.isoformat(),
            "template_id": job.template_id,
            "submission_id": job.submission_id,
            "filename": job.filename,
            "size_bytes": job.size_bytes,
            "sha256": job.sha256,
            "attempt_count": job.attempt_count,
            "retry_count": job.retry_count,
            "max_attempts": job.max_attempts,
            "idempotency_key": job.idempotency_key,
            "started_at": job.started_at.isoformat() if job.started_at is not None else "",
            "finished_at": job.finished_at.isoformat() if job.finished_at is not None else "",
            "failure_reason": job.failure_reason,
            "failure_detail": job.failure_detail,
            "metadata": dict(job.metadata or {}),
        }
