"""HTTP-facing adapter over SharelifeApiV1."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from .api_v1 import SharelifeApiV1


class NotificationReader(Protocol):
    events: list[Any]


@dataclass(slots=True)
class WebApiResult:
    ok: bool
    message: str
    data: dict[str, Any] | list[Any] = field(default_factory=dict)
    status_code: int = 200
    error_code: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "ok": self.ok,
            "message": self.message,
            "data": self.data,
        }
        if not self.ok:
            payload["error"] = {
                "code": self.error_code or "request_failed",
                "message": self.message,
            }
        return payload


class SharelifeWebApiV1:
    """Web adapter to expose Sharelife use-cases to HTTP handlers."""

    def __init__(
        self,
        api: SharelifeApiV1,
        notifier: NotificationReader | None = None,
    ):
        self.api = api
        self.notifier = notifier

    def get_preferences(self, user_id: str) -> WebApiResult:
        return self._ok(self.api.get_preferences(user_id=user_id), "preferences loaded")

    def set_preference_mode(self, user_id: str, mode: str) -> WebApiResult:
        if mode not in {"subagent_driven", "inline_execution"}:
            return self._error(
                code="invalid_mode",
                message="Invalid mode. Use subagent_driven or inline_execution.",
                status_code=400,
            )
        updated = self.api.set_preference_mode(user_id=user_id, mode=mode)
        return self._ok(updated, "execution mode updated")

    def set_preference_observe(self, user_id: str, enabled: bool) -> WebApiResult:
        updated = self.api.set_preference_observe(user_id=user_id, enabled=enabled)
        return self._ok(updated, "task detail observability updated")

    def list_templates(
        self,
        template_query: str = "",
        risk_level: str = "",
        review_label: str = "",
        warning_flag: str = "",
        category: str = "",
        tag: str = "",
        source_channel: str = "",
        sort_by: str = "",
        sort_order: str = "",
    ) -> WebApiResult:
        return self._ok(
            self.api.list_templates(
                template_query=template_query,
                risk_level=risk_level,
                review_label=review_label,
                warning_flag=warning_flag,
                category=category,
                tag=tag,
                source_channel=source_channel,
                sort_by=sort_by,
                sort_order=sort_order,
            ),
            "templates listed",
        )

    def get_template_detail(self, template_id: str) -> WebApiResult:
        if not template_id:
            return self._error(
                code="template_id_required",
                message="template_id is required",
                status_code=400,
            )
        response = self.api.get_template_detail(template_id=template_id)
        return self._from_api_error_or_ok(response, default_message="template detail ready")

    def submit_template(
        self,
        user_id: str,
        template_id: str,
        version: str,
        upload_options: dict[str, Any] | None = None,
    ) -> WebApiResult:
        if not template_id:
            return self._error(
                code="template_id_required",
                message="template_id is required",
                status_code=400,
            )
        response = self.api.submit_template(
            user_id=user_id,
            template_id=template_id,
            version=version,
            upload_options=upload_options,
        )
        return self._from_api_error_or_ok(response, default_message="template submitted")

    def submit_template_package(
        self,
        user_id: str,
        template_id: str,
        version: str,
        filename: str,
        content_base64: str,
        upload_options: dict[str, Any] | None = None,
    ) -> WebApiResult:
        if not template_id:
            return self._error(
                code="template_id_required",
                message="template_id is required",
                status_code=400,
            )
        if not filename or not content_base64:
            return self._error(
                code="package_payload_required",
                message="filename and package content are required",
                status_code=400,
            )
        response = self.api.submit_template_package(
            user_id=user_id,
            template_id=template_id,
            version=version,
            filename=filename,
            content_base64=content_base64,
            upload_options=upload_options,
        )
        if response.get("error") == "package_service_unavailable":
            return self._error(
                code="package_service_unavailable",
                message="package service unavailable",
                status_code=503,
                data=response,
            )
        if response.get("error") == "invalid_package_payload":
            return self._error(
                code="invalid_package_payload",
                message="invalid package payload",
                status_code=400,
                data=response,
            )
        if response.get("error") == "package_too_large":
            limit_bytes = int(response.get("max_size_bytes", 0) or 0)
            limit_mib = max(1, limit_bytes // (1024 * 1024)) if limit_bytes else 20
            return self._error(
                code="package_too_large",
                message=f"package exceeds {limit_mib} MiB limit",
                status_code=413,
                data=response,
            )
        return self._from_api_error_or_ok(response, default_message="template package submitted")

    def request_trial(self, user_id: str, session_id: str, template_id: str) -> WebApiResult:
        if not template_id:
            return self._error(
                code="template_id_required",
                message="template_id is required",
                status_code=400,
            )
        response = self.api.request_trial(
            user_id=user_id,
            session_id=session_id,
            template_id=template_id,
        )
        return self._ok(response, "trial request processed")

    def get_trial_status(self, user_id: str, session_id: str, template_id: str) -> WebApiResult:
        if not template_id:
            return self._error(
                code="template_id_required",
                message="template_id is required",
                status_code=400,
            )
        response = self.api.get_trial_status(
            user_id=user_id,
            session_id=session_id,
            template_id=template_id,
        )
        return self._ok(response, "trial status loaded")

    def install_template(
        self,
        user_id: str,
        session_id: str,
        template_id: str,
        install_options: dict[str, Any] | None = None,
    ) -> WebApiResult:
        if not template_id:
            return self._error(
                code="template_id_required",
                message="template_id is required",
                status_code=400,
            )
        response = self.api.install_template(
            user_id=user_id,
            session_id=session_id,
            template_id=template_id,
            install_options=install_options,
        )
        if response.get("status") == "not_installable":
            return self._error(
                code="template_not_installable",
                message="template is not approved for install",
                status_code=404,
                data=response,
            )
        return self._ok(response, "template install processed")

    def list_member_installations(self, user_id: str, limit: int = 50) -> WebApiResult:
        response = self.api.list_member_installations(user_id=user_id, limit=limit)
        return self._ok(response, "member installations listed")

    def refresh_member_installations(self, user_id: str, limit: int = 50) -> WebApiResult:
        response = self.api.refresh_member_installations(user_id=user_id, limit=limit)
        return self._ok(response, "member installations refreshed")

    def list_member_tasks(self, user_id: str, limit: int = 50) -> WebApiResult:
        response = self.api.list_member_tasks(user_id=user_id, limit=limit)
        return self._ok(response, "member tasks listed")

    def refresh_member_tasks(self, user_id: str, limit: int = 50) -> WebApiResult:
        response = self.api.refresh_member_tasks(user_id=user_id, limit=limit)
        return self._ok(response, "member tasks refreshed")

    def list_member_transfer_jobs(
        self,
        user_id: str,
        direction: str = "",
        status: str = "",
        limit: int = 50,
    ) -> WebApiResult:
        response = self.api.list_member_transfer_jobs(
            user_id=user_id,
            direction=direction,
            status=status,
            limit=limit,
        )
        return self._ok(response, "member transfers listed")

    def refresh_member_transfer_jobs(
        self,
        user_id: str,
        direction: str = "",
        status: str = "",
        limit: int = 50,
    ) -> WebApiResult:
        response = self.api.refresh_member_transfer_jobs(
            user_id=user_id,
            direction=direction,
            status=status,
            limit=limit,
        )
        return self._ok(response, "member transfers refreshed")

    def uninstall_member_installation(self, user_id: str, template_id: str) -> WebApiResult:
        response = self.api.uninstall_member_installation(
            user_id=user_id,
            template_id=template_id,
        )
        if response.get("error") == "template_id_required":
            return self._error(
                code="template_id_required",
                message="template_id is required",
                status_code=400,
                data=response,
            )
        if response.get("error") == "member_installation_not_found":
            return self._error(
                code="member_installation_not_found",
                message="member installation not found",
                status_code=404,
                data=response,
            )
        return self._ok(response, "member installation removed")

    def member_list_submissions(
        self,
        user_id: str,
        status: str = "",
        template_query: str = "",
        risk_level: str = "",
        review_label: str = "",
        warning_flag: str = "",
    ) -> WebApiResult:
        response = self.api.member_list_submissions(
            user_id=user_id,
            status=status,
            template_query=template_query,
            risk_level=risk_level,
            review_label=review_label,
            warning_flag=warning_flag,
        )
        return self._from_api_error_or_ok(response, default_message="member submissions listed")

    def member_get_submission_detail(self, user_id: str, submission_id: str) -> WebApiResult:
        if not submission_id:
            return self._error(
                code="submission_id_required",
                message="submission_id is required",
                status_code=400,
            )
        response = self.api.member_get_submission_detail(user_id=user_id, submission_id=submission_id)
        return self._from_api_error_or_ok(response, default_message="member submission detail ready")

    def member_get_submission_package(
        self,
        user_id: str,
        submission_id: str,
        idempotency_key: str = "",
    ) -> WebApiResult:
        if not submission_id:
            return self._error(
                code="submission_id_required",
                message="submission_id is required",
                status_code=400,
            )
        response = self.api.member_get_submission_package(
            user_id=user_id,
            submission_id=submission_id,
            idempotency_key=idempotency_key,
        )
        return self._from_api_error_or_ok(response, default_message="member submission package ready")

    def generate_prompt_bundle(self, template_id: str) -> WebApiResult:
        if not template_id:
            return self._error(
                code="template_id_required",
                message="template_id is required",
                status_code=400,
            )
        try:
            bundle = self.api.generate_prompt_bundle(template_id=template_id)
        except ValueError:
            return self._error(
                code="template_not_installable",
                message="template is not approved for install",
                status_code=404,
                data={"template_id": template_id},
            )
        return self._ok(bundle, "prompt bundle generated")

    def generate_package(self, template_id: str) -> WebApiResult:
        if not template_id:
            return self._error(
                code="template_id_required",
                message="template_id is required",
                status_code=400,
            )
        response = self.api.generate_package(template_id=template_id)
        if response.get("error") == "package_service_unavailable":
            return self._error(
                code="package_service_unavailable",
                message="package service unavailable",
                status_code=503,
                data=response,
            )
        if response.get("error") == "template_not_installable":
            return self._error(
                code="template_not_installable",
                message="template is not approved for install",
                status_code=404,
                data=response,
            )
        return self._ok(response, "template package generated")

    def submit_profile_pack(
        self,
        user_id: str,
        artifact_id: str,
        submit_options: dict[str, Any] | None = None,
    ) -> WebApiResult:
        if not artifact_id:
            return self._error(
                code="profile_pack_source_required",
                message="artifact_id is required",
                status_code=400,
            )
        response = self.api.submit_profile_pack(
            user_id=user_id,
            artifact_id=artifact_id,
            submit_options=submit_options,
        )
        return self._from_api_error_or_ok(response, default_message="profile pack submitted")

    def member_list_profile_pack_submissions(
        self,
        user_id: str,
        status: str = "",
        pack_query: str = "",
        pack_type: str = "",
        risk_level: str = "",
        review_label: str = "",
        warning_flag: str = "",
    ) -> WebApiResult:
        response = self.api.member_list_profile_pack_submissions(
            user_id=user_id,
            status=status,
            pack_query=pack_query,
            pack_type=pack_type,
            risk_level=risk_level,
            review_label=review_label,
            warning_flag=warning_flag,
        )
        return self._from_api_error_or_ok(
            response,
            default_message="member profile pack submissions listed",
        )

    def member_withdraw_profile_pack_submission(
        self,
        user_id: str,
        submission_id: str,
    ) -> WebApiResult:
        if not submission_id:
            return self._error(
                code="submission_id_required",
                message="submission_id is required",
                status_code=400,
            )
        response = self.api.member_withdraw_profile_pack_submission(
            user_id=user_id,
            submission_id=submission_id,
        )
        return self._from_api_error_or_ok(
            response,
            default_message="member profile pack submission withdrawn",
        )

    def member_get_profile_pack_submission_detail(
        self,
        user_id: str,
        submission_id: str,
    ) -> WebApiResult:
        if not submission_id:
            return self._error(
                code="submission_id_required",
                message="submission_id is required",
                status_code=400,
            )
        response = self.api.member_get_profile_pack_submission_detail(
            user_id=user_id,
            submission_id=submission_id,
        )
        return self._from_api_error_or_ok(
            response,
            default_message="member profile pack submission detail ready",
        )

    def member_get_profile_pack_submission_export(
        self,
        user_id: str,
        submission_id: str,
    ) -> WebApiResult:
        if not submission_id:
            return self._error(
                code="submission_id_required",
                message="submission_id is required",
                status_code=400,
            )
        response = self.api.member_get_profile_pack_submission_export(
            user_id=user_id,
            submission_id=submission_id,
        )
        return self._from_api_error_or_ok(
            response,
            default_message="member profile pack export ready",
        )

    def list_profile_pack_catalog(
        self,
        pack_query: str = "",
        pack_type: str = "",
        risk_level: str = "",
        review_label: str = "",
        warning_flag: str = "",
        featured: str = "",
    ) -> WebApiResult:
        response = self.api.list_profile_pack_catalog(
            pack_query=pack_query,
            pack_type=pack_type,
            risk_level=risk_level,
            review_label=review_label,
            warning_flag=warning_flag,
            featured=featured,
        )
        return self._from_api_error_or_ok(response, default_message="profile pack catalog listed")

    def list_profile_pack_catalog_insights(
        self,
        pack_query: str = "",
        pack_type: str = "",
        risk_level: str = "",
        review_label: str = "",
        warning_flag: str = "",
        featured: str = "",
    ) -> WebApiResult:
        response = self.api.list_profile_pack_catalog_insights(
            pack_query=pack_query,
            pack_type=pack_type,
            risk_level=risk_level,
            review_label=review_label,
            warning_flag=warning_flag,
            featured=featured,
        )
        return self._from_api_error_or_ok(
            response,
            default_message="profile pack catalog insights ready",
        )

    def get_profile_pack_catalog_detail(self, pack_id: str) -> WebApiResult:
        if not pack_id:
            return self._error(
                code="pack_id_required",
                message="pack_id is required",
                status_code=400,
            )
        response = self.api.get_profile_pack_catalog_detail(pack_id=pack_id)
        return self._from_api_error_or_ok(response, default_message="profile pack detail ready")

    def compare_profile_pack_catalog(
        self,
        pack_id: str,
        selected_sections: list[str] | None = None,
    ) -> WebApiResult:
        if not pack_id:
            return self._error(
                code="pack_id_required",
                message="pack_id is required",
                status_code=400,
            )
        response = self.api.compare_profile_pack_catalog(
            pack_id=pack_id,
            selected_sections=selected_sections,
        )
        return self._from_api_error_or_ok(response, default_message="profile pack compare ready")

    def admin_storage_local_summary(self, role: str) -> WebApiResult:
        response = self.api.admin_storage_local_summary(role=role)
        return self._from_api_error_or_ok(response, default_message="storage local summary ready")

    def admin_storage_get_policies(self, role: str) -> WebApiResult:
        response = self.api.admin_storage_get_policies(role=role)
        return self._from_api_error_or_ok(response, default_message="storage policies ready")

    def admin_storage_set_policies(
        self,
        role: str,
        patch: dict[str, Any],
        admin_id: str = "admin",
    ) -> WebApiResult:
        if not isinstance(patch, dict):
            return self._error(
                code="invalid_storage_policy_payload",
                message="policy_patch must be an object",
                status_code=400,
            )
        response = self.api.admin_storage_set_policies(
            role=role,
            patch=patch,
            admin_id=admin_id,
        )
        return self._from_api_error_or_ok(response, default_message="storage policies updated")

    def admin_storage_run_job(
        self,
        role: str,
        admin_id: str = "admin",
        trigger: str = "manual",
        note: str = "",
    ) -> WebApiResult:
        response = self.api.admin_storage_run_job(
            role=role,
            admin_id=admin_id,
            trigger=trigger,
            note=note,
        )
        return self._from_api_error_or_ok(response, default_message="storage backup job started")

    def admin_storage_list_jobs(self, role: str, status: str = "", limit: int = 50) -> WebApiResult:
        response = self.api.admin_storage_list_jobs(
            role=role,
            status=status,
            limit=max(1, min(int(limit or 50), 200)),
        )
        return self._from_api_error_or_ok(response, default_message="storage jobs listed")

    def admin_storage_get_job(self, role: str, job_id: str) -> WebApiResult:
        if not job_id:
            return self._error(
                code="job_id_required",
                message="job_id is required",
                status_code=400,
            )
        response = self.api.admin_storage_get_job(role=role, job_id=job_id)
        return self._from_api_error_or_ok(response, default_message="storage job detail ready")

    def admin_storage_list_restore_jobs(self, role: str, state: str = "", limit: int = 50) -> WebApiResult:
        response = self.api.admin_storage_list_restore_jobs(
            role=role,
            state=state,
            limit=max(1, min(int(limit or 50), 200)),
        )
        return self._from_api_error_or_ok(response, default_message="storage restore jobs listed")

    def admin_storage_get_restore_job(self, role: str, restore_id: str) -> WebApiResult:
        if not restore_id:
            return self._error(
                code="restore_id_required",
                message="restore_id is required",
                status_code=400,
            )
        response = self.api.admin_storage_get_restore_job(role=role, restore_id=restore_id)
        return self._from_api_error_or_ok(response, default_message="storage restore job detail ready")

    def admin_storage_restore_prepare(
        self,
        role: str,
        artifact_ref: str,
        admin_id: str = "admin",
        note: str = "",
    ) -> WebApiResult:
        if not artifact_ref:
            return self._error(
                code="artifact_ref_required",
                message="artifact_ref is required",
                status_code=400,
            )
        response = self.api.admin_storage_restore_prepare(
            role=role,
            artifact_ref=artifact_ref,
            admin_id=admin_id,
            note=note,
        )
        return self._from_api_error_or_ok(response, default_message="storage restore prepared")

    def admin_storage_restore_commit(
        self,
        role: str,
        restore_id: str,
        admin_id: str = "admin",
    ) -> WebApiResult:
        if not restore_id:
            return self._error(
                code="restore_id_required",
                message="restore_id is required",
                status_code=400,
            )
        response = self.api.admin_storage_restore_commit(
            role=role,
            restore_id=restore_id,
            admin_id=admin_id,
        )
        return self._from_api_error_or_ok(response, default_message="storage restore committed")

    def admin_storage_restore_cancel(
        self,
        role: str,
        restore_id: str,
        admin_id: str = "admin",
    ) -> WebApiResult:
        if not restore_id:
            return self._error(
                code="restore_id_required",
                message="restore_id is required",
                status_code=400,
            )
        response = self.api.admin_storage_restore_cancel(
            role=role,
            restore_id=restore_id,
            admin_id=admin_id,
        )
        return self._from_api_error_or_ok(response, default_message="storage restore cancelled")

    def admin_list_artifacts(
        self,
        role: str,
        artifact_kind: str = "",
        limit: int = 50,
    ) -> WebApiResult:
        response = self.api.admin_list_artifacts(
            role=role,
            artifact_kind=artifact_kind,
            limit=max(1, min(int(limit or 50), 200)),
        )
        return self._from_api_error_or_ok(response, default_message="artifacts listed")

    def admin_mirror_artifact(
        self,
        role: str,
        artifact_id: str,
        admin_id: str = "admin",
        remote_path: str = "",
        rclone_binary: str = "rclone",
        timeout_seconds: int = 300,
        bwlimit: str = "",
        encryption_required: bool = True,
        remote_encryption_verified: bool = False,
    ) -> WebApiResult:
        if not artifact_id:
            return self._error(
                code="artifact_id_required",
                message="artifact_id is required",
                status_code=400,
            )
        if not remote_path:
            return self._error(
                code="remote_path_required",
                message="remote_path is required",
                status_code=400,
            )
        response = self.api.admin_mirror_artifact(
            role=role,
            artifact_id=artifact_id,
            admin_id=admin_id,
            remote_path=remote_path,
            rclone_binary=rclone_binary,
            timeout_seconds=int(timeout_seconds or 300),
            bwlimit=bwlimit,
            encryption_required=bool(encryption_required),
            remote_encryption_verified=bool(remote_encryption_verified),
        )
        return self._from_api_error_or_ok(response, default_message="artifact mirrored")

    def admin_create_reviewer_invite(
        self,
        role: str,
        admin_id: str,
        expires_in_seconds: int = 3600,
    ) -> WebApiResult:
        response = self.api.admin_create_reviewer_invite(
            role=role,
            admin_id=admin_id,
            expires_in_seconds=int(expires_in_seconds or 0),
        )
        return self._from_api_error_or_ok(response, default_message="reviewer invite created")

    def admin_list_reviewer_invites(self, role: str, status: str = "") -> WebApiResult:
        response = self.api.admin_list_reviewer_invites(role=role, status=status)
        return self._from_api_error_or_ok(response, default_message="reviewer invites listed")

    def admin_revoke_reviewer_invite(
        self,
        role: str,
        invite_code: str,
        admin_id: str,
    ) -> WebApiResult:
        if not invite_code:
            return self._error(
                code="invite_code_required",
                message="invite_code is required",
                status_code=400,
            )
        if not admin_id:
            return self._error(
                code="admin_id_required",
                message="admin_id is required",
                status_code=400,
            )
        response = self.api.admin_revoke_reviewer_invite(
            role=role,
            invite_code=invite_code,
            admin_id=admin_id,
        )
        return self._from_api_error_or_ok(response, default_message="reviewer invite revoked")

    def reviewer_redeem_invite(self, invite_code: str, reviewer_id: str) -> WebApiResult:
        if not invite_code:
            return self._error(
                code="invite_code_required",
                message="invite_code is required",
                status_code=400,
            )
        if not reviewer_id:
            return self._error(
                code="reviewer_id_required",
                message="reviewer_id is required",
                status_code=400,
            )
        response = self.api.reviewer_redeem_invite(
            invite_code=invite_code,
            reviewer_id=reviewer_id,
        )
        return self._from_api_error_or_ok(response, default_message="reviewer invite redeemed")

    def reviewer_register_device(self, reviewer_id: str, label: str = "") -> WebApiResult:
        if not reviewer_id:
            return self._error(
                code="reviewer_id_required",
                message="reviewer_id is required",
                status_code=400,
            )
        response = self.api.reviewer_register_device(reviewer_id=reviewer_id, label=label)
        return self._from_api_error_or_ok(response, default_message="reviewer device registered")

    def reviewer_list_devices(self, reviewer_id: str) -> WebApiResult:
        if not reviewer_id:
            return self._error(
                code="reviewer_id_required",
                message="reviewer_id is required",
                status_code=400,
            )
        response = self.api.reviewer_list_devices(reviewer_id=reviewer_id)
        return self._from_api_error_or_ok(response, default_message="reviewer devices listed")

    def reviewer_revoke_device(self, reviewer_id: str, device_id: str) -> WebApiResult:
        if not reviewer_id:
            return self._error(
                code="reviewer_id_required",
                message="reviewer_id is required",
                status_code=400,
            )
        if not device_id:
            return self._error(
                code="device_id_required",
                message="device_id is required",
                status_code=400,
            )
        response = self.api.reviewer_revoke_device(reviewer_id=reviewer_id, device_id=device_id)
        return self._from_api_error_or_ok(response, default_message="reviewer device revoked")

    def admin_list_reviewers(self, role: str) -> WebApiResult:
        response = self.api.admin_list_reviewers(role=role)
        return self._from_api_error_or_ok(response, default_message="reviewers listed")

    def admin_force_reset_reviewer_devices(
        self,
        role: str,
        reviewer_id: str,
        admin_id: str,
    ) -> WebApiResult:
        if not reviewer_id:
            return self._error(
                code="reviewer_id_required",
                message="reviewer_id is required",
                status_code=400,
            )
        response = self.api.admin_force_reset_reviewer_devices(
            role=role,
            reviewer_id=reviewer_id,
            admin_id=admin_id,
        )
        return self._from_api_error_or_ok(response, default_message="reviewer devices reset")

    def admin_record_reviewer_session_revoke(
        self,
        role: str,
        reviewer_id: str,
        admin_id: str,
        revoked_sessions: int,
        device_id: str = "",
        session_id: str = "",
    ) -> WebApiResult:
        if not reviewer_id:
            return self._error(
                code="reviewer_id_required",
                message="reviewer_id is required",
                status_code=400,
            )
        response = self.api.admin_record_reviewer_session_revoke(
            role=role,
            reviewer_id=reviewer_id,
            admin_id=admin_id,
            revoked_sessions=max(0, int(revoked_sessions or 0)),
            device_id=device_id,
            session_id=session_id,
        )
        return self._from_api_error_or_ok(response, default_message="reviewer sessions revoked")

    def admin_list_profile_pack_submissions(
        self,
        role: str,
        status: str = "",
        pack_query: str = "",
        pack_type: str = "",
        risk_level: str = "",
        review_label: str = "",
        warning_flag: str = "",
    ) -> WebApiResult:
        response = self.api.admin_list_profile_pack_submissions(
            role=role,
            status=status,
            pack_query=pack_query,
            pack_type=pack_type,
            risk_level=risk_level,
            review_label=review_label,
            warning_flag=warning_flag,
        )
        return self._from_api_error_or_ok(response, default_message="profile pack submissions listed")

    def admin_decide_profile_pack_submission(
        self,
        role: str,
        submission_id: str,
        decision: str,
        review_note: str = "",
        review_labels: list[str] | None = None,
        reviewer_id: str = "",
    ) -> WebApiResult:
        if not submission_id:
            return self._error(
                code="submission_id_required",
                message="submission_id is required",
                status_code=400,
            )
        if decision.strip().lower() not in {"approve", "approved", "reject", "rejected"}:
            return self._error(
                code="invalid_submission_decision",
                message="invalid decision. Use approve or reject.",
                status_code=400,
            )
        response = self.api.admin_decide_profile_pack_submission(
            role=role,
            submission_id=submission_id,
            decision=decision,
            review_note=review_note,
            review_labels=review_labels,
            reviewer_id=reviewer_id,
        )
        return self._from_api_error_or_ok(response, default_message="profile pack submission decided")

    def admin_set_profile_pack_featured(
        self,
        role: str,
        pack_id: str,
        featured: bool,
        note: str = "",
    ) -> WebApiResult:
        if not pack_id:
            return self._error(
                code="pack_id_required",
                message="pack_id is required",
                status_code=400,
            )
        response = self.api.admin_set_profile_pack_featured(
            role=role,
            pack_id=pack_id,
            featured=featured,
            note=note,
        )
        return self._from_api_error_or_ok(response, default_message="profile pack featured state updated")

    def admin_list_submissions(
        self,
        role: str,
        status: str = "",
        template_query: str = "",
        risk_level: str = "",
        review_label: str = "",
        warning_flag: str = "",
    ) -> WebApiResult:
        response = self.api.admin_list_submissions(
            role=role,
            status=status,
            template_query=template_query,
            risk_level=risk_level,
            review_label=review_label,
            warning_flag=warning_flag,
        )
        return self._from_api_error_or_ok(response, default_message="submissions listed")

    def admin_dryrun(self, role: str, plan_id: str, patch: dict[str, Any]) -> WebApiResult:
        if not plan_id:
            return self._error(
                code="plan_id_required",
                message="plan_id is required",
                status_code=400,
            )
        if not isinstance(patch, dict):
            return self._error(
                code="invalid_patch",
                message="patch must be an object",
                status_code=400,
            )
        response = self.api.admin_dryrun(role=role, plan_id=plan_id, patch=patch)
        return self._from_api_error_or_ok(response, default_message="dryrun prepared")

    def admin_apply(self, role: str, plan_id: str) -> WebApiResult:
        if not plan_id:
            return self._error(
                code="plan_id_required",
                message="plan_id is required",
                status_code=400,
            )
        response = self.api.admin_apply(role=role, plan_id=plan_id)
        return self._from_api_error_or_ok(response, default_message="plan applied")

    def admin_rollback(self, role: str, plan_id: str) -> WebApiResult:
        if not plan_id:
            return self._error(
                code="plan_id_required",
                message="plan_id is required",
                status_code=400,
            )
        response = self.api.admin_rollback(role=role, plan_id=plan_id)
        return self._from_api_error_or_ok(response, default_message="plan rolled back")

    def admin_list_continuity(self, role: str, limit: int = 20) -> WebApiResult:
        response = self.api.admin_list_continuity(role=role, limit=limit)
        return self._from_api_error_or_ok(response, default_message="continuity entries listed")

    def admin_get_continuity(self, role: str, plan_id: str) -> WebApiResult:
        if not plan_id:
            return self._error(
                code="plan_id_required",
                message="plan_id is required",
                status_code=400,
            )
        response = self.api.admin_get_continuity(role=role, plan_id=plan_id)
        return self._from_api_error_or_ok(response, default_message="continuity entry ready")

    def admin_run_pipeline(
        self,
        role: str,
        contract: dict[str, Any],
        input_payload: Any,
        actor_id: str = "admin",
        run_id: str = "",
    ) -> WebApiResult:
        if not isinstance(contract, dict):
            return self._error(
                code="invalid_pipeline_contract",
                message="pipeline contract must be an object",
                status_code=400,
            )
        response = self.api.admin_run_pipeline(
            role=role,
            contract=contract,
            input_payload=input_payload,
            actor_id=actor_id,
            run_id=run_id,
        )
        return self._from_api_error_or_ok(response, default_message="pipeline run completed")

    def admin_decide_submission(
        self,
        role: str,
        submission_id: str,
        decision: str,
        review_note: str = "",
        review_labels: list[str] | None = None,
        reviewer_id: str = "",
    ) -> WebApiResult:
        if not submission_id:
            return self._error(
                code="submission_id_required",
                message="submission_id is required",
                status_code=400,
            )
        if decision.strip().lower() not in {"approve", "approved", "reject", "rejected"}:
            return self._error(
                code="invalid_decision",
                message="invalid decision. Use approve or reject.",
                status_code=400,
            )
        response = self.api.admin_decide_submission(
            role=role,
            submission_id=submission_id,
            decision=decision,
            review_note=review_note,
            review_labels=review_labels,
            reviewer_id=reviewer_id,
        )
        return self._from_api_error_or_ok(response, default_message="submission decided")

    def admin_update_submission_review(
        self,
        role: str,
        submission_id: str,
        review_note: str = "",
        review_labels: list[str] | None = None,
        reviewer_id: str = "",
    ) -> WebApiResult:
        if not submission_id:
            return self._error(
                code="submission_id_required",
                message="submission_id is required",
                status_code=400,
            )
        response = self.api.admin_update_submission_review(
            role=role,
            submission_id=submission_id,
            review_note=review_note,
            review_labels=review_labels,
            reviewer_id=reviewer_id,
        )
        return self._from_api_error_or_ok(response, default_message="submission review updated")

    def admin_get_submission_package(self, role: str, submission_id: str) -> WebApiResult:
        if not submission_id:
            return self._error(
                code="submission_id_required",
                message="submission_id is required",
                status_code=400,
            )
        response = self.api.admin_get_submission_package(role=role, submission_id=submission_id)
        return self._from_api_error_or_ok(response, default_message="submission package ready")

    def admin_export_profile_pack(
        self,
        role: str,
        pack_id: str,
        version: str,
        pack_type: str = "bot_profile_pack",
        redaction_mode: str = "exclude_secrets",
        sections: list[str] | None = None,
        mask_paths: list[str] | None = None,
        drop_paths: list[str] | None = None,
    ) -> WebApiResult:
        if not pack_id:
            return self._error(
                code="pack_id_required",
                message="pack_id is required",
                status_code=400,
            )
        response = self.api.admin_export_profile_pack(
            role=role,
            pack_id=pack_id,
            version=version or "1.0.0",
            pack_type=pack_type or "bot_profile_pack",
            redaction_mode=redaction_mode or "exclude_secrets",
            sections=sections,
            mask_paths=mask_paths,
            drop_paths=drop_paths,
        )
        return self._from_api_error_or_ok(response, default_message="profile pack exported")

    def admin_get_profile_pack_export(self, role: str, artifact_id: str) -> WebApiResult:
        if not artifact_id:
            return self._error(
                code="artifact_id_required",
                message="artifact_id is required",
                status_code=400,
            )
        response = self.api.admin_get_profile_pack_export(role=role, artifact_id=artifact_id)
        return self._from_api_error_or_ok(response, default_message="profile pack artifact ready")

    def admin_list_profile_pack_exports(self, role: str, limit: int = 50) -> WebApiResult:
        response = self.api.admin_list_profile_pack_exports(role=role, limit=max(1, min(limit, 200)))
        return self._from_api_error_or_ok(response, default_message="profile pack exports listed")

    def admin_import_profile_pack(self, role: str, filename: str, content_base64: str) -> WebApiResult:
        if not filename or not content_base64:
            return self._error(
                code="profile_pack_payload_required",
                message="filename and package content are required",
                status_code=400,
        )
        response = self.api.admin_import_profile_pack(
            role=role,
            filename=filename,
            content_base64=content_base64,
        )
        return self._from_api_error_or_ok(response, default_message="profile pack imported")

    def member_import_profile_pack(
        self,
        user_id: str,
        filename: str,
        content_base64: str,
    ) -> WebApiResult:
        if not filename or not content_base64:
            return self._error(
                code="profile_pack_payload_required",
                message="filename and package content are required",
                status_code=400,
            )
        response = self.api.member_import_profile_pack(
            user_id=user_id,
            filename=filename,
            content_base64=content_base64,
        )
        return self._from_api_error_or_ok(response, default_message="member profile pack imported")

    def member_import_local_astrbot_config(self, user_id: str) -> WebApiResult:
        response = self.api.member_import_local_astrbot_config(user_id=user_id)
        return self._from_api_error_or_ok(
            response,
            default_message="local AstrBot config imported",
        )

    def member_probe_local_astrbot_config(self, user_id: str) -> WebApiResult:
        response = self.api.member_probe_local_astrbot_config(user_id=user_id)
        return self._from_api_error_or_ok(
            response,
            default_message="local AstrBot config probe completed",
        )

    def member_delete_profile_pack_import(self, user_id: str, import_id: str) -> WebApiResult:
        if not import_id:
            return self._error(
                code="profile_import_not_found",
                message="profile pack import record not found",
                status_code=404,
            )
        response = self.api.member_delete_profile_pack_import(
            user_id=user_id,
            import_id=import_id,
        )
        return self._from_api_error_or_ok(
            response,
            default_message="member profile pack import deleted",
        )

    def admin_import_profile_pack_from_export(self, role: str, artifact_id: str) -> WebApiResult:
        if not artifact_id:
            return self._error(
                code="artifact_id_required",
                message="artifact_id is required",
                status_code=400,
            )
        response = self.api.admin_import_profile_pack_from_export(
            role=role,
            artifact_id=artifact_id,
        )
        return self._from_api_error_or_ok(response, default_message="profile pack imported from export")

    def admin_import_profile_pack_and_dryrun(
        self,
        role: str,
        plan_id: str,
        selected_sections: list[str] | None = None,
        filename: str = "",
        content_base64: str = "",
        artifact_id: str = "",
    ) -> WebApiResult:
        normalized_artifact_id = str(artifact_id or "").strip()
        if not normalized_artifact_id and (not filename or not content_base64):
            return self._error(
                code="profile_pack_import_source_required",
                message="artifact_id or file payload is required",
                status_code=400,
            )
        if not plan_id:
            return self._error(
                code="plan_id_required",
                message="plan_id is required",
                status_code=400,
            )
        response = self.api.admin_import_profile_pack_and_dryrun(
            role=role,
            plan_id=plan_id,
            selected_sections=selected_sections,
            filename=filename,
            content_base64=content_base64,
            artifact_id=normalized_artifact_id,
        )
        return self._from_api_error_or_ok(response, default_message="profile pack import+dryrun ready")

    def admin_list_profile_pack_imports(self, role: str, limit: int = 50) -> WebApiResult:
        response = self.api.admin_list_profile_pack_imports(role=role, limit=max(1, min(limit, 200)))
        return self._from_api_error_or_ok(response, default_message="profile pack imports listed")

    def member_list_profile_pack_imports(self, user_id: str, limit: int = 50) -> WebApiResult:
        response = self.api.member_list_profile_pack_imports(
            user_id=user_id,
            limit=max(1, min(limit, 200)),
        )
        return self._from_api_error_or_ok(response, default_message="member profile pack imports listed")

    def admin_profile_pack_dryrun(
        self,
        role: str,
        import_id: str,
        plan_id: str,
        selected_sections: list[str] | None = None,
    ) -> WebApiResult:
        if not import_id:
            return self._error(
                code="import_id_required",
                message="import_id is required",
                status_code=400,
            )
        if not plan_id:
            return self._error(
                code="plan_id_required",
                message="plan_id is required",
                status_code=400,
            )
        response = self.api.admin_profile_pack_dryrun(
            role=role,
            import_id=import_id,
            plan_id=plan_id,
            selected_sections=selected_sections,
        )
        return self._from_api_error_or_ok(response, default_message="profile pack dryrun prepared")

    def admin_profile_pack_plugin_install_plan(self, role: str, import_id: str) -> WebApiResult:
        if not import_id:
            return self._error(
                code="import_id_required",
                message="import_id is required",
                status_code=400,
            )
        response = self.api.admin_profile_pack_plugin_install_plan(
            role=role,
            import_id=import_id,
        )
        return self._from_api_error_or_ok(response, default_message="profile pack plugin install plan ready")

    def admin_profile_pack_confirm_plugin_install(
        self,
        role: str,
        import_id: str,
        plugin_ids: list[str] | None = None,
    ) -> WebApiResult:
        if not import_id:
            return self._error(
                code="import_id_required",
                message="import_id is required",
                status_code=400,
            )
        response = self.api.admin_profile_pack_confirm_plugin_install(
            role=role,
            import_id=import_id,
            plugin_ids=plugin_ids,
        )
        return self._from_api_error_or_ok(response, default_message="profile pack plugin install confirmed")

    def admin_profile_pack_execute_plugin_install(
        self,
        role: str,
        import_id: str,
        plugin_ids: list[str] | None = None,
        dry_run: bool = False,
    ) -> WebApiResult:
        if not import_id:
            return self._error(
                code="import_id_required",
                message="import_id is required",
                status_code=400,
            )
        response = self.api.admin_profile_pack_execute_plugin_install(
            role=role,
            import_id=import_id,
            plugin_ids=plugin_ids,
            dry_run=bool(dry_run),
        )
        return self._from_api_error_or_ok(response, default_message="profile pack plugin install executed")

    def admin_profile_pack_apply(self, role: str, plan_id: str) -> WebApiResult:
        if not plan_id:
            return self._error(
                code="plan_id_required",
                message="plan_id is required",
                status_code=400,
            )
        response = self.api.admin_profile_pack_apply(role=role, plan_id=plan_id)
        return self._from_api_error_or_ok(response, default_message="profile pack applied")

    def admin_profile_pack_rollback(self, role: str, plan_id: str) -> WebApiResult:
        if not plan_id:
            return self._error(
                code="plan_id_required",
                message="plan_id is required",
                status_code=400,
            )
        response = self.api.admin_profile_pack_rollback(role=role, plan_id=plan_id)
        return self._from_api_error_or_ok(response, default_message="profile pack rolled back")

    def admin_get_submission_detail(self, role: str, submission_id: str) -> WebApiResult:
        if not submission_id:
            return self._error(
                code="submission_id_required",
                message="submission_id is required",
                status_code=400,
            )
        response = self.api.admin_get_submission_detail(role=role, submission_id=submission_id)
        return self._from_api_error_or_ok(response, default_message="submission detail ready")

    def admin_compare_submission(self, role: str, submission_id: str) -> WebApiResult:
        if not submission_id:
            return self._error(
                code="submission_id_required",
                message="submission_id is required",
                status_code=400,
            )
        response = self.api.admin_compare_submission(role=role, submission_id=submission_id)
        return self._from_api_error_or_ok(response, default_message="submission comparison ready")

    def admin_list_retry_requests(self, role: str) -> WebApiResult:
        self.api.retry_queue_service.reconcile_timeouts()
        response = self.api.admin_list_retry_requests(role=role)
        return self._from_api_error_or_ok(response, default_message="retry requests listed")

    def admin_acquire_retry_lock(
        self,
        role: str,
        request_id: str,
        admin_id: str,
        force: bool = False,
        reason: str = "",
    ) -> WebApiResult:
        if not request_id:
            return self._error(
                code="request_id_required",
                message="request_id is required",
                status_code=400,
            )
        response = self.api.admin_acquire_retry_lock(
            role=role,
            request_id=request_id,
            admin_id=admin_id,
            force=force,
            reason=reason,
        )
        return self._from_api_error_or_ok(response, default_message="retry review lock acquired")

    def admin_decide_retry_request(
        self,
        role: str,
        request_id: str,
        decision: str,
        admin_id: str,
        request_version: int | None = None,
        lock_version: int | None = None,
    ) -> WebApiResult:
        if not request_id:
            return self._error(
                code="request_id_required",
                message="request_id is required",
                status_code=400,
            )
        response = self.api.admin_decide_retry_request(
            role=role,
            request_id=request_id,
            decision=decision,
            admin_id=admin_id,
            request_version=request_version,
            lock_version=lock_version,
        )
        return self._from_api_error_or_ok(response, default_message="retry request decided")

    def admin_list_audit(
        self,
        role: str,
        limit: int = 100,
        *,
        action_prefix: str = "",
        reviewer_id: str = "",
        device_id: str = "",
        lifecycle_only: bool = False,
        inspect_limit: int = 1000,
    ) -> WebApiResult:
        response = self.api.admin_list_audit(
            role=role,
            limit=max(1, min(limit, 200)),
            action_prefix=action_prefix,
            reviewer_id=reviewer_id,
            device_id=device_id,
            lifecycle_only=bool(lifecycle_only),
            inspect_limit=max(1, min(int(inspect_limit or 1000), 2000)),
        )
        return self._from_api_error_or_ok(response, default_message="audit events listed")

    def list_notifications(self, limit: int = 100) -> WebApiResult:
        if self.notifier is None:
            return self._ok({"events": []}, "notifications listed")
        if limit <= 0:
            return self._ok({"events": []}, "notifications listed")

        rows = []
        for item in self.notifier.events[-limit:]:
            rows.append(
                {
                    "channel": str(getattr(item, "channel", "unknown")),
                    "target": str(getattr(item, "target", "")),
                    "message": str(getattr(item, "message", "")),
                }
            )
        return self._ok({"events": rows}, "notifications listed")

    def _from_api_error_or_ok(
        self,
        payload: dict[str, Any],
        default_message: str,
    ) -> WebApiResult:
        error_code = payload.get("error")
        if not error_code:
            return self._ok(payload, default_message)

        status_map = {
            "permission_denied": 403,
            "package_service_unavailable": 503,
            "profile_pack_service_unavailable": 503,
            "astrbot_local_config_not_found": 404,
            "astrbot_local_config_read_failed": 409,
            "reviewer_auth_service_unavailable": 503,
            "storage_service_unavailable": 503,
            "artifact_service_unavailable": 503,
            "profile_pack_source_required": 400,
            "profile_pack_submission_not_found": 404,
            "profile_pack_submission_state_invalid": 409,
            "submission_id_required": 400,
            "profile_pack_not_published": 404,
            "reviewer_id_required": 400,
            "device_id_required": 400,
            "device_not_found": 404,
            "reviewer_not_registered": 404,
            "device_limit_exceeded": 409,
            "invite_code_required": 400,
            "invite_not_found": 404,
            "invite_expired": 410,
            "invite_already_redeemed": 409,
            "invite_revoked": 409,
            "admin_id_required": 400,
            "review_lock_held": 409,
            "takeover_reason_required": 400,
            "request_version_conflict": 409,
            "lock_version_conflict": 409,
            "review_lock_required": 409,
            "review_lock_not_owner": 403,
            "invalid_retry_decision": 400,
            "submission_package_not_available": 404,
            "template_not_found": 404,
            "submission_not_found": 404,
            "plan_not_found": 404,
            "plan_not_applied": 409,
            "profile_pack_not_found": 404,
            "profile_import_not_found": 404,
            "profile_import_in_use": 409,
            "profile_pack_incompatible": 409,
            "profile_pack_plugin_install_confirm_required": 409,
            "profile_pack_plugin_not_in_plan": 400,
            "profile_pack_plugin_id_required": 400,
            "profile_pack_plugin_install_exec_disabled": 409,
            "profile_pack_plugin_install_exec_required": 409,
            "profile_pack_plugin_install_exec_failed": 409,
            "invalid_profile_section": 400,
            "invalid_pack_type": 400,
            "invalid_profile_pack_payload": 400,
            "invalid_redaction_mode": 400,
            "invalid_redaction_path": 400,
            "pack_id_required": 400,
            "profile_pack_encryption_key_required": 400,
            "pipeline_service_unavailable": 503,
            "invalid_pipeline_contract": 400,
            "pipeline_execution_failed": 409,
            "invalid_storage_policy_payload": 400,
            "invalid_storage_policy_field": 400,
            "invalid_storage_policy_value": 400,
            "backup_job_in_progress": 409,
            "job_id_required": 400,
            "backup_job_not_found": 404,
            "artifact_ref_required": 400,
            "restore_id_required": 400,
            "restore_job_not_found": 404,
            "restore_state_invalid": 409,
            "backup_source_not_found": 409,
            "daily_upload_budget_exceeded": 409,
            "remote_sync_failed": 409,
            "remote_sync_command_not_found": 409,
            "remote_encryption_required": 409,
            "artifact_not_found": 404,
            "artifact_id_required": 400,
            "artifact_checksum_missing": 409,
            "artifact_checksum_mismatch": 409,
            "remote_path_invalid": 400,
            "remote_sync_timeout": 409,
            "idempotency_key_conflict": 409,
        }
        message_map = {
            "permission_denied": "permission denied",
            "package_service_unavailable": "package service unavailable",
            "profile_pack_service_unavailable": "profile pack service unavailable",
            "astrbot_local_config_not_found": "local AstrBot config not found",
            "astrbot_local_config_read_failed": "local AstrBot config could not be read",
            "reviewer_auth_service_unavailable": "reviewer auth service unavailable",
            "storage_service_unavailable": "storage service unavailable",
            "artifact_service_unavailable": "artifact service unavailable",
            "profile_pack_source_required": "profile pack source required",
            "profile_pack_submission_not_found": "profile pack submission not found",
            "profile_pack_submission_state_invalid": "profile pack submission state does not allow this operation",
            "submission_id_required": "submission_id is required",
            "profile_pack_not_published": "profile pack not published",
            "reviewer_id_required": "reviewer_id is required",
            "device_id_required": "device_id is required",
            "device_not_found": "device not found",
            "reviewer_not_registered": "reviewer is not registered",
            "device_limit_exceeded": "reviewer device limit exceeded",
            "invite_code_required": "invite_code is required",
            "invite_not_found": "invite code not found",
            "invite_expired": "invite code expired",
            "invite_already_redeemed": "invite code already redeemed",
            "invite_revoked": "invite code revoked",
            "admin_id_required": "admin_id is required",
            "review_lock_held": "review lock already held by another admin",
            "takeover_reason_required": "takeover reason required when force=true",
            "request_version_conflict": "request version conflict, refresh and retry",
            "lock_version_conflict": "lock version conflict, refresh and retry",
            "review_lock_required": "review lock required",
            "review_lock_not_owner": "you are not lock owner for this request",
            "invalid_retry_decision": "invalid retry decision",
            "submission_package_not_available": "submission package not available",
            "template_not_found": "template not found",
            "submission_not_found": "submission not found",
            "plan_not_found": "plan not found",
            "plan_not_applied": "plan has not been applied yet",
            "profile_pack_not_found": "profile pack artifact not found",
            "profile_import_not_found": "profile pack import record not found",
            "profile_import_in_use": "profile pack import is referenced by a submission",
            "profile_pack_incompatible": "profile pack blocked by compatibility gate",
            "profile_pack_plugin_install_confirm_required": "plugin install confirmation required for this import",
            "profile_pack_plugin_not_in_plan": "plugin id not found in install plan",
            "profile_pack_plugin_id_required": "plugin id is required",
            "profile_pack_plugin_install_exec_disabled": "plugin install execution is disabled; set profile_pack.plugin_install.enabled=true to allow execution",
            "profile_pack_plugin_install_exec_required": "plugin install execution required before apply",
            "profile_pack_plugin_install_exec_failed": "plugin install execution failed; fix and retry",
            "invalid_profile_section": "invalid profile section selection",
            "invalid_pack_type": "invalid profile pack type",
            "invalid_profile_pack_payload": "invalid profile pack payload",
            "invalid_redaction_mode": "invalid redaction mode",
            "invalid_redaction_path": "invalid redaction path",
            "pack_id_required": "pack_id is required",
            "profile_pack_encryption_key_required": "encryption key required for include_encrypted_secrets mode",
            "pipeline_service_unavailable": "pipeline service unavailable",
            "invalid_pipeline_contract": "invalid pipeline contract",
            "pipeline_execution_failed": "pipeline execution failed",
            "invalid_storage_policy_payload": "invalid storage policy payload",
            "invalid_storage_policy_field": "invalid storage policy field",
            "invalid_storage_policy_value": "invalid storage policy value",
            "backup_job_in_progress": "backup job already in progress",
            "job_id_required": "job_id is required",
            "backup_job_not_found": "backup job not found",
            "artifact_ref_required": "artifact_ref is required",
            "restore_id_required": "restore_id is required",
            "restore_job_not_found": "restore job not found",
            "restore_state_invalid": "restore state does not allow this operation",
            "backup_source_not_found": "no backup source found",
            "daily_upload_budget_exceeded": "daily upload budget exceeded",
            "remote_sync_failed": "remote sync failed",
            "remote_sync_command_not_found": "rclone binary not found",
            "remote_encryption_required": "remote encryption required",
            "artifact_not_found": "artifact not found",
            "artifact_id_required": "artifact_id is required",
            "artifact_checksum_missing": "artifact checksum missing",
            "artifact_checksum_mismatch": "artifact checksum mismatch",
            "remote_path_invalid": "remote_path is invalid",
            "remote_sync_timeout": "remote sync timed out",
            "idempotency_key_conflict": "idempotency key conflict",
        }
        return self._error(
            code=str(error_code),
            message=message_map.get(str(error_code), str(error_code)),
            status_code=status_map.get(str(error_code), 400),
            data=payload,
        )

    @staticmethod
    def _ok(data: dict[str, Any] | list[Any], message: str) -> WebApiResult:
        return WebApiResult(ok=True, message=message, data=data, status_code=200)

    @staticmethod
    def _error(
        code: str,
        message: str,
        status_code: int,
        data: dict[str, Any] | list[Any] | None = None,
    ) -> WebApiResult:
        return WebApiResult(
            ok=False,
            message=message,
            data=data or {},
            status_code=status_code,
            error_code=code,
        )
