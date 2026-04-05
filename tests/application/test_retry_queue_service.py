from datetime import UTC, datetime, timedelta

from sharelife.application.services_queue import RetryQueueService


class FrozenClock:
    def __init__(self, start: datetime):
        self.current = start

    def utcnow(self) -> datetime:
        return self.current

    def shift(self, **kwargs) -> None:
        self.current = self.current + timedelta(**kwargs)


def test_retry_request_moves_to_manual_backlog_after_72h():
    clock = FrozenClock(datetime(2026, 3, 24, 12, 0, tzinfo=UTC))
    service = RetryQueueService(clock=clock)

    req = service.enqueue("u1", "t1")
    clock.shift(hours=73)
    service.reconcile_timeouts()

    assert service.get(req.id).state == "manual_backlog"


def test_retry_request_deduplicates_active_records():
    clock = FrozenClock(datetime(2026, 3, 24, 12, 0, tzinfo=UTC))
    service = RetryQueueService(clock=clock)

    req1 = service.enqueue("u1", "t1")
    req2 = service.enqueue("u1", "t1")

    assert req1.id == req2.id
