from datetime import UTC, datetime, timedelta

from sharelife.application.services_continuity import ConfigContinuityService
from sharelife.infrastructure.json_state_store import JsonStateStore


class FrozenClock:
    def __init__(self, start: datetime):
        self.current = start

    def utcnow(self) -> datetime:
        return self.current

    def shift(self, **kwargs) -> None:
        self.current = self.current + timedelta(**kwargs)


def test_continuity_service_tracks_active_snapshot_and_persists_audit_projection(tmp_path):
    clock = FrozenClock(datetime(2026, 4, 8, 1, 0, tzinfo=UTC))
    store = JsonStateStore(tmp_path / "continuity_state.json")
    service = ConfigContinuityService(state_store=store, clock=clock)

    applied = service.record_apply(
        plan_id="plan-1",
        pre_snapshot={"plugins": {"sharelife": {"enabled": True}}},
        post_snapshot={"plugins": {"sharelife": {"enabled": False}}},
        metadata={
            "actor_id": "admin",
            "actor_role": "admin",
            "source_id": "profile/official-starter",
            "source_kind": "profile_pack",
            "selected_sections": ["plugins"],
            "recovery_class": "config_snapshot_restore",
        },
    )

    assert applied["status"] == "applied"
    assert applied["source_kind"] == "profile_pack"
    assert applied["selected_sections"] == ["plugins"]
    assert service.get_active_snapshot("plan-1") == {"plugins": {"sharelife": {"enabled": True}}}

    clock.shift(minutes=5)
    rolled_back = service.record_rollback(
        plan_id="plan-1",
        restored_snapshot={"plugins": {"sharelife": {"enabled": True}}},
    )

    assert rolled_back["status"] == "rolled_back"
    assert rolled_back["restore_verification"] == "matched"
    assert service.get_active_snapshot("plan-1") is None

    reloaded = ConfigContinuityService(state_store=store, clock=clock)
    described = reloaded.describe("plan-1")
    assert described is not None
    assert described["source_id"] == "profile/official-starter"
    assert described["restore_verification"] == "matched"
