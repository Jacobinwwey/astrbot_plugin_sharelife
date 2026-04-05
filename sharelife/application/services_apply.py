"""Guarded apply service with snapshot rollback."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .ports import RuntimePort


@dataclass(slots=True)
class ApplyPlan:
    plan_id: str
    patch: dict[str, Any]


class ApplyService:
    def __init__(self, runtime: RuntimePort):
        self.runtime = runtime
        self._plans: dict[str, ApplyPlan] = {}
        self._applied_snapshots: dict[str, Any] = {}

    def register_plan(self, plan_id: str, patch: dict[str, Any]) -> ApplyPlan:
        plan = ApplyPlan(plan_id=plan_id, patch=patch)
        self._plans[plan_id] = plan
        return plan

    def apply(self, plan_id: str) -> None:
        plan = self._plans.get(plan_id)
        if not plan:
            raise ValueError("PLAN_NOT_FOUND")

        snap = self.runtime.snapshot()
        try:
            self.runtime.apply_patch(plan.patch)
        except Exception:
            self.runtime.restore_snapshot(snap)
            raise
        self._applied_snapshots[plan_id] = snap

    def rollback(self, plan_id: str) -> None:
        snapshot = self._applied_snapshots.get(plan_id)
        if snapshot is None:
            raise ValueError("PLAN_NOT_APPLIED")
        self.runtime.restore_snapshot(snapshot)
        del self._applied_snapshots[plan_id]
