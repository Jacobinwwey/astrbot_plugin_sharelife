from datetime import UTC, datetime, timedelta

from sharelife.application.services_queue import RetryQueueService
from sharelife.application.services_trial import TrialService
from sharelife.application.services_trial_request import TrialRequestService
from sharelife.infrastructure.notifier import InMemoryNotifier


class FrozenClock:
    def __init__(self, start: datetime):
        self.current = start

    def utcnow(self) -> datetime:
        return self.current

    def shift(self, **kwargs) -> None:
        self.current = self.current + timedelta(**kwargs)


def make_flow() -> tuple[TrialRequestService, InMemoryNotifier, RetryQueueService]:
    clock = FrozenClock(datetime(2026, 3, 24, 12, 0, tzinfo=UTC))
    trial_service = TrialService(clock=clock)
    retry_queue = RetryQueueService(clock=clock)
    notifier = InMemoryNotifier()
    flow = TrialRequestService(
        trial_service=trial_service,
        retry_queue_service=retry_queue,
        notifier=notifier,
    )
    return flow, notifier, retry_queue


def test_first_trial_starts_and_dual_notice_fires_once_per_user():
    flow, notifier, _ = make_flow()

    first = flow.request_trial(user_id="u1", session_id="s1", template_id="t1")
    second_template = flow.request_trial(user_id="u1", session_id="s2", template_id="t2")

    assert first.status == "trial_started"
    assert first.trial_id
    assert second_template.status == "trial_started"
    assert len(notifier.events) == 2
    channels = {event.channel for event in notifier.events}
    assert channels == {"user_dm", "admin_dm"}


def test_second_trial_on_same_template_moves_to_retry_queue():
    flow, _, retry_queue = make_flow()

    first = flow.request_trial(user_id="u1", session_id="s1", template_id="t1")
    second = flow.request_trial(user_id="u1", session_id="s2", template_id="t1")

    assert first.status == "trial_started"
    assert second.status == "retry_queued"
    assert second.retry_request_id
    queued = retry_queue.get(second.retry_request_id)
    assert queued.state == "queued"
