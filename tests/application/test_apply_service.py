import pytest

from sharelife.application.services_apply import ApplyService


class FakeRuntime:
    def __init__(self, fail=False):
        self.fail = fail
        self.applied = []
        self.restored = []

    def snapshot(self):
        return {"snap": "v1"}

    def apply_patch(self, patch):
        if self.fail:
            raise RuntimeError("apply failed")
        self.applied.append(patch)

    def restore_snapshot(self, snapshot):
        self.restored.append(snapshot)


def test_apply_requires_existing_dryrun_plan():
    service = ApplyService(runtime=FakeRuntime())

    with pytest.raises(ValueError):
        service.apply(plan_id="missing")


def test_apply_rolls_back_when_runtime_apply_fails():
    runtime = FakeRuntime(fail=True)
    service = ApplyService(runtime=runtime)
    service.register_plan(plan_id="p1", patch={"a": 1})

    with pytest.raises(RuntimeError):
        service.apply("p1")

    assert runtime.restored == [{"snap": "v1"}]


def test_rollback_restores_last_snapshot_after_successful_apply():
    runtime = FakeRuntime(fail=False)
    service = ApplyService(runtime=runtime)
    service.register_plan(plan_id="p1", patch={"a": 1})

    service.apply("p1")
    service.rollback("p1")

    assert runtime.applied == [{"a": 1}]
    assert runtime.restored == [{"snap": "v1"}]
