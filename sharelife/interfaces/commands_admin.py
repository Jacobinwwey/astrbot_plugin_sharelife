"""Admin-facing command handlers."""

from __future__ import annotations

from ..application.services_apply import ApplyService
from ..application.services_market import MarketService
from ..application.services_queue import RetryQueueService
from .dto import CommandResponse


class AdminCommands:
    def __init__(
        self,
        apply_service: ApplyService | None = None,
        queue_service: RetryQueueService | None = None,
        market_service: MarketService | None = None,
    ):
        self.apply_service = apply_service
        self.queue_service = queue_service
        self.market_service = market_service

    def apply(self, role: str, plan_id: str) -> CommandResponse:
        if role != "admin":
            return CommandResponse(message="permission denied", data={"plan_id": plan_id})

        if self.apply_service is None:
            return CommandResponse(message="apply service unavailable", data={"plan_id": plan_id})

        try:
            self.apply_service.apply(plan_id)
        except ValueError as exc:
            return CommandResponse(
                message=self._apply_error_message(exc),
                data={"plan_id": plan_id},
            )
        return CommandResponse(message="plan applied", data={"plan_id": plan_id})

    def dryrun(self, role: str, plan_id: str, patch: dict) -> CommandResponse:
        if role != "admin":
            return CommandResponse(message="permission denied", data={"plan_id": plan_id})
        if self.apply_service is None:
            return CommandResponse(message="apply service unavailable", data={"plan_id": plan_id})

        plan = self.apply_service.register_plan(plan_id=plan_id, patch=patch)
        return CommandResponse(
            message="dryrun prepared",
            data={"plan_id": plan.plan_id, "status": "dryrun_ready", "patch": plan.patch},
        )

    def rollback(self, role: str, plan_id: str) -> CommandResponse:
        if role != "admin":
            return CommandResponse(message="permission denied", data={"plan_id": plan_id})
        if self.apply_service is None:
            return CommandResponse(message="apply service unavailable", data={"plan_id": plan_id})

        try:
            self.apply_service.rollback(plan_id)
        except ValueError as exc:
            return CommandResponse(
                message=self._apply_error_message(exc),
                data={"plan_id": plan_id},
            )
        return CommandResponse(message="plan rolled back", data={"plan_id": plan_id})

    def list_retry_requests(self, role: str) -> CommandResponse:
        if role != "admin":
            return CommandResponse(message="permission denied", data={})

        if self.queue_service is None:
            return CommandResponse(message="queue service unavailable", data={"requests": []})

        requests = [
            {
                "id": req.id,
                "user_id": req.user_id,
                "template_id": req.template_id,
                "state": req.state,
            }
            for req in self.queue_service.list_requests()
        ]
        return CommandResponse(message="retry requests listed", data={"requests": requests})

    def decide_retry_request(self, role: str, request_id: str, decision: str) -> CommandResponse:
        if role != "admin":
            return CommandResponse(
                message="permission denied",
                data={"request_id": request_id},
            )

        if self.queue_service is None:
            return CommandResponse(
                message="queue service unavailable",
                data={"request_id": request_id},
            )

        req = self.queue_service.decide(request_id=request_id, decision=decision)
        return CommandResponse(
            message="retry request decided",
            data={
                "request_id": req.id,
                "template_id": req.template_id,
                "state": req.state,
            },
        )

    def list_submissions(self, role: str, status: str = "") -> CommandResponse:
        if role != "admin":
            return CommandResponse(message="permission denied", data={})

        if self.market_service is None:
            return CommandResponse(message="market service unavailable", data={"submissions": []})

        filter_status = status.strip().lower() or None
        submissions = [
            {
                "id": item.id,
                "template_id": item.template_id,
                "version": item.version,
                "user_id": item.user_id,
                "status": item.status,
            }
            for item in self.market_service.list_submissions(status=filter_status)
        ]
        return CommandResponse(message="submissions listed", data={"submissions": submissions})

    def decide_submission(
        self,
        role: str,
        submission_id: str,
        decision: str,
        review_note: str = "",
    ) -> CommandResponse:
        if role != "admin":
            return CommandResponse(
                message="permission denied",
                data={"submission_id": submission_id},
            )
        if self.market_service is None:
            return CommandResponse(
                message="market service unavailable",
                data={"submission_id": submission_id},
            )

        record = self.market_service.decide_submission(
            submission_id=submission_id,
            reviewer_id="admin",
            decision=decision,
            review_note=review_note,
        )
        return CommandResponse(
            message="submission decided",
            data={
                "submission_id": record.id,
                "template_id": record.template_id,
                "status": record.status,
            },
        )

    @staticmethod
    def _apply_error_message(exc: Exception) -> str:
        code = str(exc)
        if "PLAN_NOT_FOUND" in code:
            return "plan not found"
        if "PLAN_NOT_APPLIED" in code:
            return "plan has not been applied yet"
        raise exc
