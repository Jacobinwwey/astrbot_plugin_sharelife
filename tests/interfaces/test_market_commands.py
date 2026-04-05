from datetime import UTC, datetime, timedelta

from sharelife.application.services_market import MarketService
from sharelife.application.services_preferences import PreferenceService
from sharelife.application.services_queue import RetryQueueService
from sharelife.application.services_trial import TrialService
from sharelife.application.services_trial_request import TrialRequestService
from sharelife.infrastructure.notifier import InMemoryNotifier
from sharelife.interfaces.commands_admin import AdminCommands
from sharelife.interfaces.commands_user import UserCommands


class FrozenClock:
    def __init__(self, start: datetime):
        self.current = start

    def utcnow(self) -> datetime:
        return self.current

    def shift(self, **kwargs) -> None:
        self.current = self.current + timedelta(**kwargs)


def build_commands():
    clock = FrozenClock(datetime(2026, 3, 25, 10, 0, tzinfo=UTC))
    trial_request = TrialRequestService(
        trial_service=TrialService(clock=clock),
        retry_queue_service=RetryQueueService(clock=clock),
        notifier=InMemoryNotifier(),
    )
    market_service = MarketService(clock=clock)
    user = UserCommands(
        preference_service=PreferenceService(),
        trial_request_service=trial_request,
        market_service=market_service,
    )
    admin = AdminCommands(queue_service=RetryQueueService(clock=clock), market_service=market_service)
    return user, admin


def test_install_requires_approved_template():
    user, _ = build_commands()

    resp = user.install_template(user_id="u1", session_id="s1", template_id="community/basic")

    assert resp.data["status"] == "not_installable"


def test_submit_then_approve_then_install():
    user, admin = build_commands()

    submit = user.submit_template(user_id="u1", template_id="community/basic", version="1.0.0")
    sub_id = submit.data["submission_id"]
    admin.decide_submission(role="admin", submission_id=sub_id, decision="approve")

    install = user.install_template(user_id="u1", session_id="s1", template_id="community/basic")

    assert install.data["status"] == "trial_started"
    assert install.data["template_id"] == "community/basic"


def test_non_admin_cannot_decide_submission():
    user, admin = build_commands()
    submit = user.submit_template(user_id="u1", template_id="community/basic", version="1.0.0")

    resp = admin.decide_submission(
        role="member",
        submission_id=submit.data["submission_id"],
        decision="approve",
    )

    assert "permission" in resp.message.lower()
