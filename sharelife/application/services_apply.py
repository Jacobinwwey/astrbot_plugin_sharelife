"""Guarded apply service with snapshot rollback."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .services_continuity import ConfigContinuityService
from .ports import RuntimePort


@dataclass(slots=True)
class ApplyPlan:
    plan_id: str
    patch: dict[str, Any]
    metadata: dict[str, Any]


class ApplyService:
    def __init__(
        self,
        runtime: RuntimePort,
        continuity_service: ConfigContinuityService | None = None,
    ):
        self.runtime = runtime
        self.continuity_service = continuity_service
        self._plans: dict[str, ApplyPlan] = {}
        self._applied_snapshots: dict[str, Any] = {}

    def register_plan(
        self,
        plan_id: str,
        patch: dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ) -> ApplyPlan:
        plan = ApplyPlan(plan_id=plan_id, patch=patch, metadata=dict(metadata or {}))
        self._plans[plan_id] = plan
        return plan

    def apply(self, plan_id: str) -> dict[str, Any]:
        plan = self._plans.get(plan_id)
        if not plan:
            raise ValueError("PLAN_NOT_FOUND")

        snap = self.runtime.snapshot()
        try:
            self.runtime.apply_patch(plan.patch)
        except Exception:
            self.runtime.restore_snapshot(snap)
            raise
        if self.continuity_service is not None:
            post_snapshot = self.runtime.snapshot()
            return self.continuity_service.record_apply(
                plan_id=plan_id,
                pre_snapshot=snap,
                post_snapshot=post_snapshot,
                metadata=plan.metadata,
            )
        self._applied_snapshots[plan_id] = snap
        return {}

    def rollback(self, plan_id: str) -> dict[str, Any]:
        snapshot = (
            self.continuity_service.get_active_snapshot(plan_id)
            if self.continuity_service is not None
            else self._applied_snapshots.get(plan_id)
        )
        if snapshot is None:
            raise ValueError("PLAN_NOT_APPLIED")
        self.runtime.restore_snapshot(snapshot)
        if self.continuity_service is not None:
            restored_snapshot = self.runtime.snapshot()
            return self.continuity_service.record_rollback(
                plan_id=plan_id,
                restored_snapshot=restored_snapshot,
            )
        del self._applied_snapshots[plan_id]
        return {}
