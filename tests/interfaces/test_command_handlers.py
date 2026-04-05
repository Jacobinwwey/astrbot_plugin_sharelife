from sharelife.interfaces.commands_admin import AdminCommands
from sharelife.interfaces.commands_user import UserCommands
from sharelife.application.services_apply import ApplyService
from sharelife.application.services_preferences import PreferenceService
from sharelife.application.services_queue import RetryQueueService
from sharelife.application.services_trial import TrialService
from sharelife.application.services_trial_request import TrialRequestService
from sharelife.infrastructure.notifier import InMemoryNotifier
from sharelife.infrastructure.runtime_bridge import InMemoryRuntimeBridge


class FrozenClock:
    def __init__(self, start):
        self.current = start

    def utcnow(self):
        return self.current


def test_user_cannot_call_admin_apply():
    commands = AdminCommands()

    resp = commands.apply(role="member", plan_id="plan-1")

    assert "permission" in resp.message.lower()


def test_user_second_trial_call_is_queued():
    from datetime import UTC, datetime

    clock = FrozenClock(datetime(2026, 3, 24, 12, 0, tzinfo=UTC))
    queue_service = RetryQueueService(clock=clock)
    flow = TrialRequestService(
        trial_service=TrialService(clock=clock),
        retry_queue_service=queue_service,
        notifier=InMemoryNotifier(),
    )
    user_commands = UserCommands(
        preference_service=PreferenceService(),
        trial_request_service=flow,
    )

    first = user_commands.request_trial(user_id="u1", session_id="s1", template_id="t1")
    second = user_commands.request_trial(user_id="u1", session_id="s2", template_id="t1")

    assert first.data["status"] == "trial_started"
    assert second.data["status"] == "retry_queued"
    assert queue_service.get(second.data["retry_request_id"]).state == "queued"


def test_admin_can_decide_retry_request():
    from datetime import UTC, datetime

    clock = FrozenClock(datetime(2026, 3, 24, 12, 0, tzinfo=UTC))
    queue_service = RetryQueueService(clock=clock)
    flow = TrialRequestService(
        trial_service=TrialService(clock=clock),
        retry_queue_service=queue_service,
        notifier=InMemoryNotifier(),
    )
    user_commands = UserCommands(
        preference_service=PreferenceService(),
        trial_request_service=flow,
    )
    admin_commands = AdminCommands(queue_service=queue_service)

    user_commands.request_trial(user_id="u1", session_id="s1", template_id="t1")
    queued = user_commands.request_trial(user_id="u1", session_id="s2", template_id="t1")
    request_id = queued.data["retry_request_id"]

    decision = admin_commands.decide_retry_request(
        role="admin",
        request_id=request_id,
        decision="approve",
    )

    assert decision.data["state"] == "approved"


def test_user_can_query_trial_status():
    from datetime import UTC, datetime

    clock = FrozenClock(datetime(2026, 3, 24, 12, 0, tzinfo=UTC))
    trial_service = TrialService(clock=clock)
    flow = TrialRequestService(
        trial_service=trial_service,
        retry_queue_service=RetryQueueService(clock=clock),
        notifier=InMemoryNotifier(),
    )
    user_commands = UserCommands(
        preference_service=PreferenceService(),
        trial_request_service=flow,
    )

    missing = user_commands.get_trial_status(user_id="u1", session_id="s1", template_id="t1")
    assert missing.data["status"] == "not_started"

    user_commands.request_trial(user_id="u1", session_id="s1", template_id="t1")
    active = user_commands.get_trial_status(user_id="u1", session_id="s1", template_id="t1")
    assert active.data["status"] == "active"
    assert active.data["ttl_seconds"] == 7200


def test_admin_can_prepare_apply_and_rollback_plan():
    runtime = InMemoryRuntimeBridge(initial_state={"mode": "safe"})
    commands = AdminCommands(apply_service=ApplyService(runtime=runtime))

    dryrun = commands.dryrun(
        role="admin",
        plan_id="plan-community-basic",
        patch={"template_id": "community/basic", "version": "1.0.0"},
    )
    assert dryrun.data["status"] == "dryrun_ready"

    applied = commands.apply(role="admin", plan_id="plan-community-basic")
    assert applied.message == "plan applied"
    assert runtime.state["template_id"] == "community/basic"

    rolled_back = commands.rollback(role="admin", plan_id="plan-community-basic")
    assert rolled_back.message == "plan rolled back"
    assert runtime.state == {"mode": "safe"}
