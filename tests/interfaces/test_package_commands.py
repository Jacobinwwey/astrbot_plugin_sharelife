from datetime import UTC, datetime, timedelta

from sharelife.application.services_market import MarketService
from sharelife.application.services_package import PackageService
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


def test_install_returns_package_artifact_after_approval(tmp_path):
    clock = FrozenClock(datetime(2026, 3, 25, 10, 0, tzinfo=UTC))
    market = MarketService(clock=clock)
    package = PackageService(market_service=market, output_root=tmp_path, clock=clock)

    trial = TrialRequestService(
        trial_service=TrialService(clock=clock),
        retry_queue_service=RetryQueueService(clock=clock),
        notifier=InMemoryNotifier(),
    )
    user = UserCommands(
        preference_service=PreferenceService(),
        trial_request_service=trial,
        market_service=market,
        package_service=package,
    )
    admin = AdminCommands(market_service=market)

    sub = user.submit_template(user_id="u1", template_id="community/basic", version="1.0.0")
    admin.decide_submission(role="admin", submission_id=sub.data["submission_id"], decision="approve")

    install = user.install_template(user_id="u1", session_id="s1", template_id="community/basic")

    artifact = install.data["package_artifact"]
    assert artifact["sha256"]
    assert artifact["path"].endswith(".zip")


def test_export_package_requires_approved_template(tmp_path):
    clock = FrozenClock(datetime(2026, 3, 25, 10, 0, tzinfo=UTC))
    market = MarketService(clock=clock)
    package = PackageService(market_service=market, output_root=tmp_path, clock=clock)
    user = UserCommands(
        preference_service=PreferenceService(),
        market_service=market,
        package_service=package,
    )

    resp = user.export_template_package(template_id="community/basic")

    assert resp.data["status"] == "not_installable"
