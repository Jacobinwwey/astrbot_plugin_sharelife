from datetime import UTC, datetime, timedelta

import pytest

from sharelife.application.services_queue import RetryQueueService


class FrozenClock:
    def __init__(self, start: datetime):
        self.current = start

    def utcnow(self) -> datetime:
        return self.current

    def shift(self, **kwargs) -> None:
        self.current = self.current + timedelta(**kwargs)


def test_lock_prevents_parallel_reviewer_without_takeover_reason():
    clock = FrozenClock(datetime(2026, 3, 25, 12, 0, tzinfo=UTC))
    service = RetryQueueService(clock=clock)
    req = service.enqueue("u1", "community/basic")
    service.acquire_lock(request_id=req.id, admin_id="admin-1")

    with pytest.raises(PermissionError):
        service.acquire_lock(request_id=req.id, admin_id="admin-2")

    with pytest.raises(ValueError):
        service.acquire_lock(request_id=req.id, admin_id="admin-2", force=True, reason="")


def test_force_takeover_increments_lock_version():
    clock = FrozenClock(datetime(2026, 3, 25, 12, 0, tzinfo=UTC))
    service = RetryQueueService(clock=clock)
    req = service.enqueue("u1", "community/basic")
    lock1 = service.acquire_lock(request_id=req.id, admin_id="admin-1")
    lock2 = service.acquire_lock(
        request_id=req.id,
        admin_id="admin-2",
        force=True,
        reason="on-call handover",
    )

    assert lock1.lock_version == 1
    assert lock2.lock_version == 2
    assert lock2.holder_id == "admin-2"


def test_decide_rejects_stale_request_or_lock_versions():
    clock = FrozenClock(datetime(2026, 3, 25, 12, 0, tzinfo=UTC))
    service = RetryQueueService(clock=clock)
    req = service.enqueue("u1", "community/basic")
    lock = service.acquire_lock(request_id=req.id, admin_id="admin-1")

    with pytest.raises(ValueError):
        service.decide(
            request_id=req.id,
            decision="approve",
            admin_id="admin-1",
            request_version=req.version + 1,
            lock_version=lock.lock_version,
        )

    with pytest.raises(PermissionError):
        service.decide(
            request_id=req.id,
            decision="approve",
            admin_id="admin-1",
            request_version=req.version,
            lock_version=lock.lock_version + 1,
        )
