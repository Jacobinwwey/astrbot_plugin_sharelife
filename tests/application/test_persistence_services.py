from datetime import UTC, datetime, timedelta

from sharelife.application.services_audit import AuditService
from sharelife.application.services_preferences import PreferenceService
from sharelife.application.services_queue import RetryQueueService
from sharelife.application.services_trial import TrialService
from sharelife.application.services_trial_request import TrialRequestService
from sharelife.infrastructure.json_state_store import JsonStateStore
from sharelife.infrastructure.notifier import InMemoryNotifier
from sharelife.infrastructure.sqlite_state_store import SqliteStateStore


class FrozenClock:
    def __init__(self, start: datetime):
        self.current = start

    def utcnow(self) -> datetime:
        return self.current

    def shift(self, **kwargs) -> None:
        self.current = self.current + timedelta(**kwargs)


def test_preference_state_persists(tmp_path):
    store = JsonStateStore(tmp_path / "preferences.json")

    service1 = PreferenceService(state_store=store)
    service1.set_execution_mode(user_id="u1", mode="inline_execution")
    service1.set_observe_details(user_id="u1", enabled=True)

    service2 = PreferenceService(state_store=store)
    pref = service2.get("u1")
    assert pref.execution_mode == "inline_execution"
    assert pref.observe_task_details is True


def test_retry_queue_state_persists(tmp_path):
    store = JsonStateStore(tmp_path / "retry-queue.json")
    clock = FrozenClock(datetime(2026, 3, 25, 12, 0, tzinfo=UTC))

    queue1 = RetryQueueService(clock=clock, state_store=store)
    req = queue1.enqueue("u1", "community/basic")

    queue2 = RetryQueueService(clock=clock, state_store=store)
    loaded = queue2.get(req.id)
    assert loaded.template_id == "community/basic"
    assert loaded.state == "queued"


def test_trial_state_and_notice_guard_persist(tmp_path):
    trial_store = JsonStateStore(tmp_path / "trial-state.json")
    notice_store = JsonStateStore(tmp_path / "trial-request-state.json")
    notifier_store = JsonStateStore(tmp_path / "notifications.json")

    clock = FrozenClock(datetime(2026, 3, 25, 12, 0, tzinfo=UTC))
    trial1 = TrialService(clock=clock, state_store=trial_store)
    queue1 = RetryQueueService(clock=clock)
    notifier1 = InMemoryNotifier(state_store=notifier_store)
    flow1 = TrialRequestService(
        trial_service=trial1,
        retry_queue_service=queue1,
        notifier=notifier1,
        state_store=notice_store,
    )
    flow1.request_trial(user_id="u1", session_id="s1", template_id="t1")
    assert len(notifier1.events) == 2

    trial2 = TrialService(clock=clock, state_store=trial_store)
    queue2 = RetryQueueService(clock=clock)
    notifier2 = InMemoryNotifier(state_store=notifier_store)
    flow2 = TrialRequestService(
        trial_service=trial2,
        retry_queue_service=queue2,
        notifier=notifier2,
        state_store=notice_store,
    )
    flow2.request_trial(user_id="u1", session_id="s2", template_id="t2")

    # No second first-trial dual-notice after restart.
    assert len(notifier2.events) == 2


def test_trial_state_and_notice_guard_persist_with_sqlite(tmp_path):
    sqlite_file = tmp_path / "sharelife_state.sqlite3"
    trial_store = SqliteStateStore(sqlite_file, store_key="trial_state")
    notice_store = SqliteStateStore(sqlite_file, store_key="trial_request_state")
    notifier_store = SqliteStateStore(sqlite_file, store_key="notification_state")

    clock = FrozenClock(datetime(2026, 3, 25, 12, 0, tzinfo=UTC))
    trial1 = TrialService(clock=clock, state_store=trial_store)
    queue1 = RetryQueueService(clock=clock)
    notifier1 = InMemoryNotifier(state_store=notifier_store)
    flow1 = TrialRequestService(
        trial_service=trial1,
        retry_queue_service=queue1,
        notifier=notifier1,
        state_store=notice_store,
    )
    flow1.request_trial(user_id="u1", session_id="s1", template_id="t1")
    assert len(notifier1.events) == 2

    trial2 = TrialService(clock=clock, state_store=trial_store)
    queue2 = RetryQueueService(clock=clock)
    notifier2 = InMemoryNotifier(state_store=notifier_store)
    flow2 = TrialRequestService(
        trial_service=trial2,
        retry_queue_service=queue2,
        notifier=notifier2,
        state_store=notice_store,
    )
    flow2.request_trial(user_id="u1", session_id="s2", template_id="t2")

    # No second first-trial dual-notice after restart.
    assert len(notifier2.events) == 2


def test_audit_state_persists(tmp_path):
    store = JsonStateStore(tmp_path / "audit-state.json")
    clock = FrozenClock(datetime(2026, 3, 25, 12, 0, tzinfo=UTC))

    audit1 = AuditService(clock=clock, state_store=store)
    event = audit1.record(
        action="submission.approved",
        actor_id="admin",
        actor_role="admin",
        target_id="sub-1",
        status="approved",
        detail={"template_id": "community/basic"},
    )

    audit2 = AuditService(clock=clock, state_store=store)
    events = audit2.list_events(limit=10)
    assert len(events) == 1
    assert events[0].id == event.id


def test_preference_state_persists_with_sqlite(tmp_path):
    store = SqliteStateStore(tmp_path / "sharelife_state.sqlite3", store_key="preference_state")

    service1 = PreferenceService(state_store=store)
    service1.set_execution_mode(user_id="u1", mode="inline_execution")
    service1.set_observe_details(user_id="u1", enabled=True)

    service2 = PreferenceService(state_store=store)
    pref = service2.get("u1")
    assert pref.execution_mode == "inline_execution"
    assert pref.observe_task_details is True


def test_retry_queue_state_persists_with_sqlite(tmp_path):
    store = SqliteStateStore(tmp_path / "sharelife_state.sqlite3", store_key="retry_state")
    clock = FrozenClock(datetime(2026, 3, 25, 12, 0, tzinfo=UTC))

    queue1 = RetryQueueService(clock=clock, state_store=store)
    req = queue1.enqueue("u1", "community/basic")

    queue2 = RetryQueueService(clock=clock, state_store=store)
    loaded = queue2.get(req.id)
    assert loaded.template_id == "community/basic"
    assert loaded.state == "queued"


def test_trial_state_persists_with_sqlite(tmp_path):
    store = SqliteStateStore(tmp_path / "sharelife_state.sqlite3", store_key="trial_state")
    clock = FrozenClock(datetime(2026, 3, 25, 12, 0, tzinfo=UTC))

    trial1 = TrialService(clock=clock, state_store=store)
    created = trial1.start_trial(user_id="u1", session_id="s1", template_id="t1")

    trial2 = TrialService(clock=clock, state_store=store)
    loaded = trial2.get_status(user_id="u1", session_id="s1", template_id="t1")
    assert loaded["status"] == "active"
    assert loaded["trial_id"] == created.id


def test_audit_state_persists_with_sqlite(tmp_path):
    store = SqliteStateStore(tmp_path / "sharelife_state.sqlite3", store_key="audit_state")
    clock = FrozenClock(datetime(2026, 3, 25, 12, 0, tzinfo=UTC))

    audit1 = AuditService(clock=clock, state_store=store)
    event = audit1.record(
        action="submission.approved",
        actor_id="admin",
        actor_role="admin",
        target_id="sub-1",
        status="approved",
        detail={"template_id": "community/basic"},
    )

    audit2 = AuditService(clock=clock, state_store=store)
    events = audit2.list_events(limit=10)
    assert len(events) == 1
    assert events[0].id == event.id
