"""User-facing command handlers."""

from __future__ import annotations

from ..application.services_market import MarketService
from ..application.services_package import PackageService
from ..application.services_preferences import PreferenceService
from ..application.services_trial_request import TrialRequestService
from .dto import CommandResponse


class UserCommands:
    def __init__(
        self,
        preference_service: PreferenceService,
        trial_request_service: TrialRequestService | None = None,
        market_service: MarketService | None = None,
        package_service: PackageService | None = None,
    ):
        self.preference_service = preference_service
        self.trial_request_service = trial_request_service
        self.market_service = market_service
        self.package_service = package_service

    def get_preferences(self, user_id: str) -> CommandResponse:
        pref = self.preference_service.get(user_id=user_id)
        return CommandResponse(
            message="preferences loaded",
            data={
                "user_id": pref.user_id,
                "execution_mode": pref.execution_mode,
                "observe_task_details": pref.observe_task_details,
            },
        )

    def set_mode(self, user_id: str, mode: str) -> CommandResponse:
        pref = self.preference_service.set_execution_mode(user_id=user_id, mode=mode)  # type: ignore[arg-type]
        return CommandResponse(
            message="execution mode updated",
            data={
                "user_id": pref.user_id,
                "execution_mode": pref.execution_mode,
                "observe_task_details": pref.observe_task_details,
            },
        )

    def set_observe_details(self, user_id: str, enabled: bool) -> CommandResponse:
        pref = self.preference_service.set_observe_details(user_id=user_id, enabled=enabled)
        return CommandResponse(
            message="task detail observability updated",
            data={
                "user_id": pref.user_id,
                "execution_mode": pref.execution_mode,
                "observe_task_details": pref.observe_task_details,
            },
        )

    def request_trial(
        self,
        user_id: str,
        session_id: str,
        template_id: str,
    ) -> CommandResponse:
        if self.trial_request_service is None:
            return CommandResponse(
                message="trial service unavailable",
                data={"status": "unavailable", "template_id": template_id},
            )

        result = self.trial_request_service.request_trial(
            user_id=user_id,
            session_id=session_id,
            template_id=template_id,
        )

        if result.status == "trial_started":
            return CommandResponse(
                message="trial started",
                data={
                    "status": result.status,
                    "template_id": template_id,
                    "trial_id": result.trial_id,
                },
            )

        return CommandResponse(
            message="retry request queued",
            data={
                "status": result.status,
                "template_id": template_id,
                "retry_request_id": result.retry_request_id,
            },
        )

    def get_trial_status(
        self,
        user_id: str,
        session_id: str,
        template_id: str,
    ) -> CommandResponse:
        if self.trial_request_service is None:
            return CommandResponse(
                message="trial service unavailable",
                data={"status": "unavailable", "template_id": template_id},
            )

        status = self.trial_request_service.trial_service.get_status(
            user_id=user_id,
            session_id=session_id,
            template_id=template_id,
        )
        return CommandResponse(
            message="trial status loaded",
            data=status,
        )

    def submit_template(self, user_id: str, template_id: str, version: str) -> CommandResponse:
        if self.market_service is None:
            return CommandResponse(
                message="market service unavailable",
                data={"status": "unavailable", "template_id": template_id},
            )

        submission = self.market_service.submit_template(
            user_id=user_id,
            template_id=template_id,
            version=version,
        )
        return CommandResponse(
            message="template submitted",
            data={
                "status": submission.status,
                "submission_id": submission.id,
                "template_id": submission.template_id,
                "version": submission.version,
            },
        )

    def list_market(self) -> CommandResponse:
        if self.market_service is None:
            return CommandResponse(
                message="market service unavailable",
                data={"templates": []},
            )
        templates = [
            {
                "template_id": item.template_id,
                "version": item.version,
                "source_submission_id": item.source_submission_id,
            }
            for item in self.market_service.list_published_templates()
        ]
        return CommandResponse(message="market templates listed", data={"templates": templates})

    def install_template(self, user_id: str, session_id: str, template_id: str) -> CommandResponse:
        if self.market_service is None:
            return CommandResponse(
                message="market service unavailable",
                data={"status": "unavailable", "template_id": template_id},
            )

        published = self.market_service.get_published_template(template_id=template_id)
        if not published:
            return CommandResponse(
                message="template is not approved for install",
                data={"status": "not_installable", "template_id": template_id},
            )

        trial_result = self.request_trial(
            user_id=user_id,
            session_id=session_id,
            template_id=template_id,
        )
        bundle = self.market_service.build_prompt_bundle(template_id=template_id)
        merged = dict(trial_result.data)
        merged["prompt_bundle"] = bundle
        if self.package_service is not None:
            artifact = self.package_service.export_template_package(template_id=template_id)
            merged["package_artifact"] = {
                "path": str(artifact.path),
                "sha256": artifact.sha256,
                "version": artifact.version,
            }
        return CommandResponse(message="template install processed", data=merged)

    def build_prompt_bundle(self, template_id: str) -> CommandResponse:
        if self.market_service is None:
            return CommandResponse(
                message="market service unavailable",
                data={"template_id": template_id},
            )
        bundle = self.market_service.build_prompt_bundle(template_id=template_id)
        return CommandResponse(message="prompt bundle generated", data=bundle)

    def export_template_package(self, template_id: str) -> CommandResponse:
        if self.package_service is None:
            return CommandResponse(
                message="package service unavailable",
                data={"template_id": template_id},
            )
        try:
            artifact = self.package_service.export_template_package(template_id=template_id)
        except ValueError:
            return CommandResponse(
                message="template is not approved for install",
                data={"status": "not_installable", "template_id": template_id},
            )
        return CommandResponse(
            message="template package generated",
            data={
                "template_id": artifact.template_id,
                "version": artifact.version,
                "path": str(artifact.path),
                "sha256": artifact.sha256,
            },
        )
