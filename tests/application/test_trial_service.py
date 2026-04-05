from datetime import UTC, datetime, timedelta

import pytest

from sharelife.application.services_trial import TrialService


class FrozenClock:
    def __init__(self, start: datetime):
        self.current = start

    def utcnow(self) -> datetime:
        return self.current

    def shift(self, **kwargs) -> None:
        self.current = self.current + timedelta(**kwargs)


def test_trial_defaults_to_two_hours():
    clock = FrozenClock(datetime(2026, 3, 24, 12, 0, tzinfo=UTC))
    service = TrialService(clock=clock)

    trial = service.start_trial(user_id="u1", session_id="s1", template_id="t1")

    assert trial.ttl_seconds == 7200
    assert trial.expires_at == clock.utcnow() + timedelta(seconds=7200)


def test_trial_renew_is_forbidden():
    clock = FrozenClock(datetime(2026, 3, 24, 12, 0, tzinfo=UTC))
    service = TrialService(clock=clock)

    trial = service.start_trial(user_id="u1", session_id="s1", template_id="t1")

    with pytest.raises(PermissionError):
        service.renew_trial(trial.id)


def test_trial_status_distinguishes_not_started_active_and_expired():
    clock = FrozenClock(datetime(2026, 3, 24, 12, 0, tzinfo=UTC))
    service = TrialService(clock=clock)

    missing = service.get_status(user_id="u1", session_id="s1", template_id="t1")
    assert missing["status"] == "not_started"

    service.start_trial(user_id="u1", session_id="s1", template_id="t1")
    active = service.get_status(user_id="u1", session_id="s1", template_id="t1")
    assert active["status"] == "active"
    assert active["ttl_seconds"] == 7200

    clock.shift(hours=3)
    expired = service.get_status(user_id="u1", session_id="s1", template_id="t1")
    assert expired["status"] == "expired"
