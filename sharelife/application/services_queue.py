"""Retry queue service for community-first flow."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import uuid4

from ..infrastructure.json_state_store import JsonStateStore
from ..infrastructure.retry_queue_repository import (
    JsonRetryQueueRepository,
    RetryQueueRepository,
    SqliteRetryQueueRepository,
)
from ..infrastructure.sqlite_state_store import SqliteStateStore
from ..infrastructure.system_clock import SystemClock


ACTIVE_STATES = {"queued", "reviewing", "manual_backlog"}
FINAL_STATES = {"approved", "rejected", "closed"}


@dataclass(slots=True)
class RetryRequest:
    id: str
    user_id: str
    template_id: str
    state: str
    created_at: datetime
    updated_at: datetime
    version: int = 1


@dataclass(slots=True)
class ReviewLock:
    request_id: str
    holder_id: str
    lock_version: int
    acquired_at: datetime
    expires_at: datetime
    force_reason: str = ""


class RetryQueueService:
    BACKLOG_AFTER_HOURS = 72
    LOCK_MINUTES = 10

    def __init__(
        self,
        clock: SystemClock,
        state_store: JsonStateStore | SqliteStateStore | None = None,
        repository: RetryQueueRepository | None = None,
    ):
        self.clock = clock
        self.state_store = state_store
        self.repository = self._build_repository(state_store=state_store, repository=repository)
        self._requests: dict[str, RetryRequest] = {}
        self._locks: dict[str, ReviewLock] = {}
        self._load_state()

    @staticmethod
    def _build_repository(
        *,
        state_store: JsonStateStore | SqliteStateStore | None,
        repository: RetryQueueRepository | None,
    ) -> RetryQueueRepository | None:
        if repository is not None:
            return repository
        if state_store is None:
            return None
        if isinstance(state_store, SqliteStateStore):
            return SqliteRetryQueueRepository(state_store.db_path, legacy_state_store=state_store)
        return JsonRetryQueueRepository(state_store)

    def enqueue(self, user_id: str, template_id: str) -> RetryRequest:
        for req in self._requests.values():
            if (
                req.user_id == user_id
                and req.template_id == template_id
                and req.state in ACTIVE_STATES
            ):
                self._touch(req)
                self._flush_state()
                return req

        now = self.clock.utcnow()
        req = RetryRequest(
            id=str(uuid4()),
            user_id=user_id,
            template_id=template_id,
            state="queued",
            created_at=now,
            updated_at=now,
            version=1,
        )
        self._requests[req.id] = req
        self._flush_state()
        return req

    def get(self, request_id: str) -> RetryRequest:
        return self._requests[request_id]

    def list_requests(self) -> list[RetryRequest]:
        return sorted(self._requests.values(), key=lambda req: req.created_at)

    def mark_reviewing(self, request_id: str) -> RetryRequest:
        req = self.get(request_id)
        if req.state in FINAL_STATES:
            return req
        req.state = "reviewing"
        self._touch(req)
        self._flush_state()
        return req

    def acquire_lock(
        self,
        request_id: str,
        admin_id: str,
        force: bool = False,
        reason: str = "",
    ) -> ReviewLock:
        req = self.get(request_id)
        now = self.clock.utcnow()
        current = self._locks.get(request_id)
        active = bool(current and current.expires_at > now)
        if active and current and current.holder_id != admin_id:
            if not force:
                raise PermissionError("REVIEW_LOCK_HELD")
            if not reason.strip():
                raise ValueError("TAKEOVER_REASON_REQUIRED")

        next_version = (current.lock_version + 1) if current else 1
        lock = ReviewLock(
            request_id=request_id,
            holder_id=admin_id,
            lock_version=next_version,
            acquired_at=now,
            expires_at=now + timedelta(minutes=self.LOCK_MINUTES),
            force_reason=reason.strip(),
        )
        self._locks[request_id] = lock
        if req.state not in FINAL_STATES:
            req.state = "reviewing"
            self._touch(req)
        self._flush_state()
        return lock

    def get_lock(self, request_id: str) -> ReviewLock | None:
        lock = self._locks.get(request_id)
        if not lock:
            return None
        if lock.expires_at <= self.clock.utcnow():
            return None
        return lock

    def decide(
        self,
        request_id: str,
        decision: str,
        admin_id: str | None = None,
        request_version: int | None = None,
        lock_version: int | None = None,
    ) -> RetryRequest:
        req = self.get(request_id)
        normalized = decision.strip().lower()
        if normalized not in {"approve", "approved", "reject", "rejected"}:
            raise ValueError("INVALID_RETRY_DECISION")

        if request_version is not None and request_version != req.version:
            raise ValueError("REQUEST_VERSION_CONFLICT")

        if admin_id is not None or lock_version is not None:
            lock = self.get_lock(request_id)
            if lock is None:
                raise PermissionError("REVIEW_LOCK_REQUIRED")
            if admin_id is not None and lock.holder_id != admin_id:
                raise PermissionError("REVIEW_LOCK_NOT_OWNER")
            if lock_version is not None and lock.lock_version != lock_version:
                raise PermissionError("LOCK_VERSION_CONFLICT")

        req.state = "approved" if normalized.startswith("approve") else "rejected"
        self._touch(req)
        self._locks.pop(request_id, None)
        self._flush_state()
        return req

    def reconcile_timeouts(self) -> None:
        now = self.clock.utcnow()
        threshold = timedelta(hours=self.BACKLOG_AFTER_HOURS)
        dirty = False
        for req in self._requests.values():
            if req.state in {"queued", "reviewing"} and now - req.created_at >= threshold:
                req.state = "manual_backlog"
                self._touch(req, now=now)
                dirty = True
        if dirty:
            self._flush_state()

    def _load_state(self) -> None:
        if self.repository is None:
            return
        payload = self.repository.load_state()
        for item in payload.get("requests", []):
            req = RetryRequest(
                id=item["id"],
                user_id=item["user_id"],
                template_id=item["template_id"],
                state=item["state"],
                created_at=datetime.fromisoformat(item["created_at"]),
                updated_at=datetime.fromisoformat(item["updated_at"]),
                version=int(item.get("version", 1)),
            )
            self._requests[req.id] = req
        for item in payload.get("locks", []):
            lock = ReviewLock(
                request_id=item["request_id"],
                holder_id=item["holder_id"],
                lock_version=int(item["lock_version"]),
                acquired_at=datetime.fromisoformat(item["acquired_at"]),
                expires_at=datetime.fromisoformat(item["expires_at"]),
                force_reason=item.get("force_reason", ""),
            )
            self._locks[lock.request_id] = lock

    def _flush_state(self) -> None:
        if self.repository is None:
            return
        now = self.clock.utcnow()
        locks = [
            item
            for item in self._locks.values()
            if item.expires_at > now
        ]
        payload = {
            "requests": [
                {
                    "id": item.id,
                    "user_id": item.user_id,
                    "template_id": item.template_id,
                    "state": item.state,
                    "created_at": item.created_at.isoformat(),
                    "updated_at": item.updated_at.isoformat(),
                    "version": item.version,
                }
                for item in self._requests.values()
            ],
            "locks": [
                {
                    "request_id": item.request_id,
                    "holder_id": item.holder_id,
                    "lock_version": item.lock_version,
                    "acquired_at": item.acquired_at.isoformat(),
                    "expires_at": item.expires_at.isoformat(),
                    "force_reason": item.force_reason,
                }
                for item in locks
            ],
        }
        self.repository.save_state(payload)

    def _touch(self, req: RetryRequest, now: datetime | None = None) -> None:
        req.updated_at = now or self.clock.utcnow()
        req.version += 1
