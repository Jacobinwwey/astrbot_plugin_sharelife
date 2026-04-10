"""Sharelife v1 API-like interface for unified use-cases."""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
import os
import shutil
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from ..application.services_apply import ApplyService
from ..application.services_audit import AuditService
from ..application.services_artifact_mirror import ArtifactMirrorService
from ..application.services_market import MarketService
from ..application.services_package import PackageService
from ..application.services_preferences import PreferenceService
from ..application.services_pipeline import PipelineOrchestrator
from ..application.services_profile_pack import ProfilePackService
from ..application.services_queue import RetryQueueService
from ..application.services_reviewer_auth import ReviewerAuthService
from ..application.services_storage_backup import StorageBackupService
from ..application.services_transfer_jobs import TransferJob, TransferJobService
from ..application.services_trial_request import TrialRequestService
from ..domain.option_contracts import (
    normalize_install_options as normalize_install_option_contract,
    normalize_profile_pack_submit_options as normalize_profile_pack_submit_option_contract,
    normalize_upload_options as normalize_upload_option_contract,
)


class SharelifeApiV1:
    _IDEMPOTENCY_KEY_MAX_LEN = 128
    _MEMBER_TASK_ACTIONS: set[str] = {
        "submission.created",
        "submission.package_uploaded",
        "submission.pending_replaced",
        "submission.idempotency_replayed",
        "submission.idempotency_conflict",
        "trial.requested",
        "template.installed",
        "template.uninstalled",
        "member.installations.refreshed",
        "member.tasks.refreshed",
        "member.transfers.refreshed",
        "profile_pack.exported",
        "profile_pack.imported",
        "profile_pack.import_deleted",
        "profile_pack.imported_from_export",
        "profile_pack.dryrun_prepared",
        "profile_pack.plugin_install_plan_viewed",
        "profile_pack.plugin_install_confirmed",
        "profile_pack.plugin_install_executed",
        "profile_pack.applied",
        "profile_pack.rolled_back",
        "profile_pack.submission_created",
        "profile_pack.submission.pending_replaced",
        "profile_pack.submission_withdrawn",
        "profile_pack.submission.idempotency_replayed",
        "profile_pack.submission.idempotency_conflict",
    }
    _MEMBER_TASK_ERROR_STATUSES: set[str] = {
        "error",
        "failed",
        "conflict",
        "denied",
        "rejected",
        "not_found",
    }
    _REVIEWER_LIFECYCLE_ACTIONS: set[str] = {
        "reviewer.invite_created",
        "reviewer.invite_revoked",
        "reviewer.invite_redeemed",
        "reviewer.device_registered",
        "reviewer.device_revoked",
        "reviewer.device_force_reset",
        "reviewer.session_force_revoke",
    }

    def __init__(
        self,
        preference_service: PreferenceService,
        retry_queue_service: RetryQueueService,
        trial_request_service: TrialRequestService,
        market_service: MarketService,
        package_service: PackageService | None,
        apply_service: ApplyService,
        audit_service: AuditService,
        profile_pack_service: ProfilePackService | None = None,
        pipeline_orchestrator: PipelineOrchestrator | None = None,
        reviewer_auth_service: ReviewerAuthService | None = None,
        artifact_mirror_service: ArtifactMirrorService | None = None,
        storage_backup_service: StorageBackupService | None = None,
        transfer_job_service: TransferJobService | None = None,
        public_market_auto_publish_profile_pack_approve: bool = False,
        public_market_root: Path | str | None = None,
        public_market_rebuild_snapshot_on_publish: bool = True,
    ):
        self.preference_service = preference_service
        self.retry_queue_service = retry_queue_service
        self.trial_request_service = trial_request_service
        self.market_service = market_service
        self.package_service = package_service
        self.profile_pack_service = profile_pack_service
        self.apply_service = apply_service
        self.audit_service = audit_service
        self.pipeline_orchestrator = pipeline_orchestrator
        self.reviewer_auth_service = reviewer_auth_service
        self.artifact_mirror_service = artifact_mirror_service
        self.storage_backup_service = storage_backup_service
        self.transfer_job_service = transfer_job_service
        self.public_market_auto_publish_profile_pack_approve = bool(
            public_market_auto_publish_profile_pack_approve,
        )
        if public_market_root:
            self.public_market_root = Path(public_market_root).expanduser().resolve()
        else:
            self.public_market_root = Path(__file__).resolve().parents[2] / "docs" / "public"
        self.public_market_rebuild_snapshot_on_publish = bool(public_market_rebuild_snapshot_on_publish)

    @staticmethod
    def _normalize_role(role: str) -> str:
        text = str(role or "").strip().lower()
        if text in {"member", "user"}:
            return "member"
        if text in {"reviewer", "admin"}:
            return text
        return "member"

    @classmethod
    def _is_admin_role(cls, role: str) -> bool:
        return cls._normalize_role(role) == "admin"

    @classmethod
    def _is_reviewer_role(cls, role: str) -> bool:
        normalized = cls._normalize_role(role)
        return normalized in {"reviewer", "admin"}

    @classmethod
    def _reviewer_actor(cls, role: str, reviewer_id: str = "") -> tuple[str, str]:
        normalized_role = cls._normalize_role(role)
        actor_role = "admin" if normalized_role == "admin" else "reviewer"
        actor_id = str(reviewer_id or "").strip()
        if not actor_id:
            actor_id = "admin" if actor_role == "admin" else "reviewer"
        return actor_id, actor_role

    def _submission_package_limit_bytes(self) -> int:
        if self.package_service is None:
            return PackageService.DEFAULT_MAX_SUBMISSION_PACKAGE_BYTES
        value = getattr(
            self.package_service,
            "max_submission_package_bytes",
            PackageService.DEFAULT_MAX_SUBMISSION_PACKAGE_BYTES,
        )
        return max(1, int(value or PackageService.DEFAULT_MAX_SUBMISSION_PACKAGE_BYTES))

    def _continuity_service(self):
        return getattr(self.apply_service, "continuity_service", None)

    @staticmethod
    def _estimate_base64_decoded_size(content_base64: str) -> int:
        text = str(content_base64 or "").strip()
        if not text:
            return 0
        padding = len(text) - len(text.rstrip("="))
        return max(0, (len(text) * 3) // 4 - padding)

    @classmethod
    def _normalize_idempotency_key(cls, value: object) -> str:
        text = str(value or "").strip()
        if not text:
            return ""
        allowed = []
        for ch in text:
            if ch.isalnum() or ch in {"-", "_", ".", ":"}:
                allowed.append(ch)
        normalized = "".join(allowed).strip()
        if not normalized:
            return ""
        return normalized[: cls._IDEMPOTENCY_KEY_MAX_LEN]

    @classmethod
    def _idempotency_key_fingerprint(cls, value: object) -> str:
        normalized = cls._normalize_idempotency_key(value)
        if not normalized:
            return ""
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]

    @staticmethod
    def _transfer_job_payload(job: TransferJob) -> dict[str, Any]:
        return {
            "job_id": job.job_id,
            "direction": job.direction,
            "job_type": job.job_type,
            "actor_id": job.actor_id,
            "actor_role": job.actor_role,
            "user_id": job.user_id,
            "template_id": job.template_id,
            "submission_id": job.submission_id,
            "status": job.status,
            "filename": job.filename,
            "size_bytes": job.size_bytes,
            "sha256": job.sha256,
            "attempt_count": job.attempt_count,
            "retry_count": job.retry_count,
            "max_attempts": job.max_attempts,
            "idempotency_key": job.idempotency_key,
            "failure_reason": job.failure_reason,
            "failure_detail": job.failure_detail,
            "created_at": job.created_at.isoformat(),
            "updated_at": job.updated_at.isoformat(),
            "started_at": job.started_at.isoformat() if job.started_at is not None else "",
            "finished_at": job.finished_at.isoformat() if job.finished_at is not None else "",
            "metadata": dict(job.metadata or {}),
        }

    def _attach_transfer_job(self, payload: dict[str, Any], job: TransferJob | None) -> dict[str, Any]:
        if job is not None:
            payload["transfer_job"] = self._transfer_job_payload(job)
        return payload

    def _claim_transfer_job(
        self,
        *,
        direction: str,
        job_type: str,
        actor_id: str,
        actor_role: str,
        user_id: str = "",
        logical_key: str = "",
        template_id: str = "",
        submission_id: str = "",
        filename: str = "",
        idempotency_key: str = "",
        max_attempts: int = 1,
        metadata: dict[str, Any] | None = None,
    ):
        if self.transfer_job_service is None:
            return None
        return self.transfer_job_service.claim_job(
            direction=direction,
            job_type=job_type,
            actor_id=actor_id,
            actor_role=actor_role,
            user_id=user_id,
            logical_key=logical_key,
            template_id=template_id,
            submission_id=submission_id,
            filename=filename,
            idempotency_key=idempotency_key,
            max_attempts=max_attempts,
            metadata=metadata,
        )

    @staticmethod
    def _new_transfer_logical_key(prefix: str) -> str:
        return f"{prefix}:{uuid4()}"

    def _find_existing_submission_by_idempotency(
        self,
        *,
        user_id: str,
        template_id: str,
        version: str,
        idempotency_key: str,
    ):
        normalized_key = self._normalize_idempotency_key(idempotency_key)
        if not normalized_key:
            return None
        normalized_user_id = str(user_id or "").strip() or "webui-user"
        normalized_template_id = str(template_id or "").strip()
        normalized_version = str(version or "").strip()
        matches = []
        for item in self.market_service.list_submissions():
            if str(getattr(item, "user_id", "") or "").strip() != normalized_user_id:
                continue
            if str(getattr(item, "template_id", "") or "").strip() != normalized_template_id:
                continue
            if str(getattr(item, "version", "") or "").strip() != normalized_version:
                continue
            options = item.upload_options if isinstance(item.upload_options, dict) else {}
            if self._normalize_idempotency_key(options.get("idempotency_key")) != normalized_key:
                continue
            matches.append(item)
        if not matches:
            return None
        matches.sort(key=lambda row: row.updated_at, reverse=True)
        return matches[0]

    def _find_any_template_submission_by_idempotency(
        self,
        *,
        user_id: str,
        idempotency_key: str,
    ):
        normalized_key = self._normalize_idempotency_key(idempotency_key)
        if not normalized_key:
            return None
        normalized_user_id = str(user_id or "").strip() or "webui-user"
        matches = []
        for item in self.market_service.list_submissions():
            if str(getattr(item, "user_id", "") or "").strip() != normalized_user_id:
                continue
            options = item.upload_options if isinstance(item.upload_options, dict) else {}
            if self._normalize_idempotency_key(options.get("idempotency_key")) != normalized_key:
                continue
            matches.append(item)
        if not matches:
            return None
        matches.sort(key=lambda row: row.updated_at, reverse=True)
        return matches[0]

    @staticmethod
    def _template_idempotency_scope_matches(*, submission, template_id: str, version: str) -> bool:
        normalized_template_id = str(template_id or "").strip()
        normalized_version = str(version or "").strip()
        return (
            str(getattr(submission, "template_id", "") or "").strip() == normalized_template_id
            and str(getattr(submission, "version", "") or "").strip() == normalized_version
        )

    def _find_any_profile_pack_submission_by_idempotency(
        self,
        *,
        user_id: str,
        idempotency_key: str,
    ):
        if self.profile_pack_service is None:
            return None
        normalized_key = self._normalize_idempotency_key(idempotency_key)
        if not normalized_key:
            return None
        normalized_user_id = str(user_id or "").strip() or "member"
        for item in self.profile_pack_service.list_submissions():
            if str(getattr(item, "user_id", "") or "").strip() != normalized_user_id:
                continue
            options = item.submit_options if isinstance(item.submit_options, dict) else {}
            if self._normalize_idempotency_key(options.get("idempotency_key")) != normalized_key:
                continue
            return item
        return None

    def get_preferences(self, user_id: str) -> dict:
        pref = self.preference_service.get(user_id=user_id)
        return {
            "user_id": pref.user_id,
            "execution_mode": pref.execution_mode,
            "observe_task_details": pref.observe_task_details,
        }

    def set_preference_mode(self, user_id: str, mode: str) -> dict:
        pref = self.preference_service.set_execution_mode(user_id=user_id, mode=mode)  # type: ignore[arg-type]
        self._audit(
            action="preference.mode_updated",
            actor_id=user_id,
            actor_role="member",
            target_id=user_id,
            status="updated",
            detail={"execution_mode": pref.execution_mode},
        )
        return {
            "user_id": pref.user_id,
            "execution_mode": pref.execution_mode,
            "observe_task_details": pref.observe_task_details,
        }

    def set_preference_observe(self, user_id: str, enabled: bool) -> dict:
        pref = self.preference_service.set_observe_details(user_id=user_id, enabled=enabled)
        self._audit(
            action="preference.observe_updated",
            actor_id=user_id,
            actor_role="member",
            target_id=user_id,
            status="updated",
            detail={"observe_task_details": pref.observe_task_details},
        )
        return {
            "user_id": pref.user_id,
            "execution_mode": pref.execution_mode,
            "observe_task_details": pref.observe_task_details,
        }

    def submit_template(
        self,
        user_id: str,
        template_id: str,
        version: str,
        upload_options: dict | None = None,
    ) -> dict:
        normalized_upload_options = self._normalize_upload_options(upload_options)
        normalized_idempotency_key = self._normalize_idempotency_key(
            normalized_upload_options.get("idempotency_key"),
        )
        transfer_claim = self._claim_transfer_job(
            direction="upload",
            job_type="template_submission",
            actor_id=user_id,
            actor_role="member",
            user_id=user_id,
            logical_key=(
                f"upload:{user_id}:{template_id}:{version}:{normalized_idempotency_key}"
                if normalized_idempotency_key
                else self._new_transfer_logical_key(f"upload:{user_id}:{template_id}:{version}")
            ),
            template_id=template_id,
            idempotency_key=normalized_idempotency_key,
            max_attempts=3,
            metadata={"version": version},
        )
        if transfer_claim is not None and transfer_claim.should_execute:
            self.transfer_job_service.mark_running(transfer_claim.job.job_id)
        if normalized_idempotency_key:
            existing_any = self._find_any_template_submission_by_idempotency(
                user_id=user_id,
                idempotency_key=normalized_idempotency_key,
            )
            if existing_any is not None and not self._template_idempotency_scope_matches(
                submission=existing_any,
                template_id=template_id,
                version=version,
            ):
                self._audit(
                    action="submission.idempotency_conflict",
                    actor_id=user_id,
                    actor_role="member",
                    target_id=str(getattr(existing_any, "id", "") or ""),
                    status="conflict",
                    detail={
                        "template_id": template_id,
                        "version": version,
                        "existing_template_id": str(getattr(existing_any, "template_id", "") or ""),
                        "existing_version": str(getattr(existing_any, "version", "") or ""),
                        "idempotency_key_fingerprint": self._idempotency_key_fingerprint(
                            normalized_idempotency_key,
                        ),
                    },
                )
                payload = {
                    "error": "idempotency_key_conflict",
                    "template_id": template_id,
                    "version": version,
                    "existing_submission_id": str(getattr(existing_any, "id", "") or ""),
                }
                if transfer_claim is not None:
                    self.transfer_job_service.mark_failed(
                        transfer_claim.job.job_id,
                        failure_reason="idempotency_conflict",
                        failure_detail="submission idempotency scope conflict",
                        template_id=template_id,
                        submission_id=str(getattr(existing_any, "id", "") or ""),
                    )
                    self._attach_transfer_job(payload, self.transfer_job_service.get(transfer_claim.job.job_id))
                return payload
            existing = self._find_existing_submission_by_idempotency(
                user_id=user_id,
                template_id=template_id,
                version=version,
                idempotency_key=normalized_idempotency_key,
            )
            if existing is not None:
                self._audit(
                    action="submission.idempotency_replayed",
                    actor_id=user_id,
                    actor_role="member",
                    target_id=existing.id,
                    status=existing.status,
                    detail={
                        "template_id": template_id,
                        "version": version,
                        "idempotency_key_fingerprint": self._idempotency_key_fingerprint(
                            normalized_idempotency_key,
                        ),
                        "submission_id": existing.id,
                    },
                )
                payload = self._submission_payload(existing)
                payload["idempotent_replay"] = True
                payload["replaced_submission_ids"] = []
                payload["replaced_submission_count"] = 0
                if transfer_claim is not None:
                    self.transfer_job_service.mark_done(
                        transfer_claim.job.job_id,
                        template_id=template_id,
                        submission_id=existing.id,
                        metadata={"idempotent_replay": True},
                    )
                    self._attach_transfer_job(payload, self.transfer_job_service.get(transfer_claim.job.job_id))
                return payload
        replaced_submission_ids: list[str] = []
        if normalized_upload_options.get("replace_existing"):
            replaced_submission_ids = self.market_service.replace_pending_submissions(
                user_id=user_id,
                template_id=template_id,
            )
            if replaced_submission_ids:
                self._audit(
                    action="submission.pending_replaced",
                    actor_id=user_id,
                    actor_role="member",
                    target_id=template_id,
                    status="replaced",
                    detail={
                        "template_id": template_id,
                        "replaced_submission_ids": list(replaced_submission_ids),
                        "replace_existing": True,
                    },
                )
        sub = self.market_service.submit_template(
            user_id=user_id,
            template_id=template_id,
            version=version,
            upload_options=normalized_upload_options,
        )
        self._audit(
            action="submission.created",
            actor_id=user_id,
            actor_role="member",
            target_id=sub.id,
            status=sub.status,
            detail={
                "template_id": template_id,
                "version": version,
                "upload_options": normalized_upload_options,
                "replaced_submission_ids": list(replaced_submission_ids),
                "replaced_submission_count": len(replaced_submission_ids),
            },
        )
        payload = self._submission_payload(sub)
        payload["replaced_submission_ids"] = list(replaced_submission_ids)
        payload["replaced_submission_count"] = len(replaced_submission_ids)
        if transfer_claim is not None:
            self.transfer_job_service.mark_done(
                transfer_claim.job.job_id,
                template_id=template_id,
                submission_id=sub.id,
                metadata={"replaced_submission_count": len(replaced_submission_ids)},
            )
            self._attach_transfer_job(payload, self.transfer_job_service.get(transfer_claim.job.job_id))
        return payload

    def submit_template_package(
        self,
        user_id: str,
        template_id: str,
        version: str,
        filename: str,
        content_base64: str,
        upload_options: dict | None = None,
    ) -> dict:
        if self.package_service is None:
            return {"error": "package_service_unavailable", "template_id": template_id}
        normalized_upload_options = self._normalize_upload_options(upload_options)
        normalized_idempotency_key = self._normalize_idempotency_key(
            normalized_upload_options.get("idempotency_key"),
        )
        transfer_claim = self._claim_transfer_job(
            direction="upload",
            job_type="template_submission_package",
            actor_id=user_id,
            actor_role="member",
            user_id=user_id,
            logical_key=(
                f"upload:{user_id}:{template_id}:{version}:{normalized_idempotency_key}"
                if normalized_idempotency_key
                else self._new_transfer_logical_key(f"upload:{user_id}:{template_id}:{version}")
            ),
            template_id=template_id,
            filename=filename,
            idempotency_key=normalized_idempotency_key,
            max_attempts=3,
            metadata={"version": version},
        )
        if transfer_claim is not None and transfer_claim.should_execute:
            self.transfer_job_service.mark_running(transfer_claim.job.job_id)
        if normalized_idempotency_key:
            existing_any = self._find_any_template_submission_by_idempotency(
                user_id=user_id,
                idempotency_key=normalized_idempotency_key,
            )
            if existing_any is not None and not self._template_idempotency_scope_matches(
                submission=existing_any,
                template_id=template_id,
                version=version,
            ):
                self._audit(
                    action="submission.idempotency_conflict",
                    actor_id=user_id,
                    actor_role="member",
                    target_id=str(getattr(existing_any, "id", "") or ""),
                    status="conflict",
                    detail={
                        "template_id": template_id,
                        "version": version,
                        "existing_template_id": str(getattr(existing_any, "template_id", "") or ""),
                        "existing_version": str(getattr(existing_any, "version", "") or ""),
                        "idempotency_key_fingerprint": self._idempotency_key_fingerprint(
                            normalized_idempotency_key,
                        ),
                        "filename": str(filename or "").strip(),
                    },
                )
                payload = {
                    "error": "idempotency_key_conflict",
                    "template_id": template_id,
                    "version": version,
                    "existing_submission_id": str(getattr(existing_any, "id", "") or ""),
                }
                if transfer_claim is not None:
                    self.transfer_job_service.mark_failed(
                        transfer_claim.job.job_id,
                        failure_reason="idempotency_conflict",
                        failure_detail="submission idempotency scope conflict",
                        template_id=template_id,
                        submission_id=str(getattr(existing_any, "id", "") or ""),
                        filename=filename,
                    )
                    self._attach_transfer_job(payload, self.transfer_job_service.get(transfer_claim.job.job_id))
                return payload
            existing = self._find_existing_submission_by_idempotency(
                user_id=user_id,
                template_id=template_id,
                version=version,
                idempotency_key=normalized_idempotency_key,
            )
            if existing is not None:
                self._audit(
                    action="submission.idempotency_replayed",
                    actor_id=user_id,
                    actor_role="member",
                    target_id=existing.id,
                    status=existing.status,
                    detail={
                        "template_id": template_id,
                        "version": version,
                        "idempotency_key_fingerprint": self._idempotency_key_fingerprint(
                            normalized_idempotency_key,
                        ),
                        "submission_id": existing.id,
                        "filename": str(filename or "").strip(),
                    },
                )
                payload = self._submission_payload(existing)
                payload["idempotent_replay"] = True
                payload["replaced_submission_ids"] = []
                payload["replaced_submission_count"] = 0
                if transfer_claim is not None:
                    self.transfer_job_service.mark_done(
                        transfer_claim.job.job_id,
                        template_id=template_id,
                        submission_id=existing.id,
                        filename=str(filename or "").strip(),
                        metadata={"idempotent_replay": True},
                    )
                    self._attach_transfer_job(payload, self.transfer_job_service.get(transfer_claim.job.job_id))
                return payload
        max_size_bytes = self._submission_package_limit_bytes()
        estimated_size_bytes = self._estimate_base64_decoded_size(content_base64)
        if estimated_size_bytes > max_size_bytes:
            payload = {
                "error": "package_too_large",
                "template_id": template_id,
                "max_size_bytes": max_size_bytes,
                "estimated_size_bytes": estimated_size_bytes,
            }
            if transfer_claim is not None:
                self.transfer_job_service.mark_failed(
                    transfer_claim.job.job_id,
                    failure_reason="payload_too_large",
                    failure_detail="submission package exceeds configured limit",
                    template_id=template_id,
                    filename=filename,
                )
                self._attach_transfer_job(payload, self.transfer_job_service.get(transfer_claim.job.job_id))
            return payload
        try:
            content = base64.b64decode(content_base64.encode("ascii"), validate=True)
        except (binascii.Error, ValueError):
            payload = {"error": "invalid_package_payload", "template_id": template_id}
            if transfer_claim is not None:
                self.transfer_job_service.mark_failed(
                    transfer_claim.job.job_id,
                    failure_reason="invalid_payload",
                    failure_detail="invalid base64 payload",
                    template_id=template_id,
                    filename=filename,
                )
                self._attach_transfer_job(payload, self.transfer_job_service.get(transfer_claim.job.job_id))
            return payload
        if len(content) > max_size_bytes:
            payload = {
                "error": "package_too_large",
                "template_id": template_id,
                "max_size_bytes": max_size_bytes,
                "estimated_size_bytes": len(content),
            }
            if transfer_claim is not None:
                self.transfer_job_service.mark_failed(
                    transfer_claim.job.job_id,
                    failure_reason="payload_too_large",
                    failure_detail="submission package exceeds configured limit",
                    template_id=template_id,
                    filename=filename,
                )
                self._attach_transfer_job(payload, self.transfer_job_service.get(transfer_claim.job.job_id))
            return payload
        try:
            uploaded = self.package_service.ingest_submission_package(
                template_id=template_id,
                version=version,
                filename=filename,
                content=content,
            )
        except ValueError as exc:
            if str(exc) == "PACKAGE_TOO_LARGE":
                payload = {
                    "error": "package_too_large",
                    "template_id": template_id,
                    "max_size_bytes": max_size_bytes,
                    "estimated_size_bytes": len(content),
                }
                if transfer_claim is not None:
                    self.transfer_job_service.mark_failed(
                        transfer_claim.job.job_id,
                        failure_reason="payload_too_large",
                        failure_detail="submission package exceeds configured limit",
                        template_id=template_id,
                        filename=filename,
                    )
                    self._attach_transfer_job(payload, self.transfer_job_service.get(transfer_claim.job.job_id))
                return payload
            raise
        replaced_submission_ids: list[str] = []
        if normalized_upload_options.get("replace_existing"):
            replaced_submission_ids = self.market_service.replace_pending_submissions(
                user_id=user_id,
                template_id=template_id,
            )
            if replaced_submission_ids:
                self._audit(
                    action="submission.pending_replaced",
                    actor_id=user_id,
                    actor_role="member",
                    target_id=template_id,
                    status="replaced",
                    detail={
                        "template_id": template_id,
                        "replaced_submission_ids": list(replaced_submission_ids),
                        "replace_existing": True,
                    },
                )
        sub = self.market_service.submit_template(
            user_id=user_id,
            template_id=template_id,
            version=version,
            prompt_template=uploaded.prompt_template,
            package_artifact={
                "artifact_id": uploaded.artifact_id,
                "sha256": uploaded.sha256,
                "filename": uploaded.filename,
                "source": "uploaded_submission",
                "size_bytes": uploaded.size_bytes,
            },
            scan_summary=uploaded.scan_summary,
            upload_options=normalized_upload_options,
            review_labels=uploaded.review_labels,
            warning_flags=uploaded.warning_flags,
            risk_level=uploaded.risk_level,
        )
        self._audit(
            action="submission.package_uploaded",
            actor_id=user_id,
            actor_role="member",
            target_id=sub.id,
            status=sub.status,
            detail={
                "template_id": template_id,
                "version": version,
                "filename": uploaded.filename,
                "upload_options": normalized_upload_options,
                "replaced_submission_ids": list(replaced_submission_ids),
                "replaced_submission_count": len(replaced_submission_ids),
            },
        )
        payload = self._submission_payload(sub)
        payload["replaced_submission_ids"] = list(replaced_submission_ids)
        payload["replaced_submission_count"] = len(replaced_submission_ids)
        if transfer_claim is not None:
            self.transfer_job_service.mark_done(
                transfer_claim.job.job_id,
                template_id=template_id,
                submission_id=sub.id,
                filename=uploaded.filename,
                size_bytes=uploaded.size_bytes,
                sha256=uploaded.sha256,
                metadata={"replaced_submission_count": len(replaced_submission_ids)},
            )
            self._attach_transfer_job(payload, self.transfer_job_service.get(transfer_claim.job.job_id))
        return payload

    def request_trial(self, user_id: str, session_id: str, template_id: str) -> dict:
        result = self._request_trial_with_preference(
            user_id=user_id,
            session_id=session_id,
            template_id=template_id,
        )
        if result["status"] in {"trial_started", "retry_queued"}:
            self.market_service.record_template_event(template_id=template_id, event="trial_request")
        detail = {
            "template_id": template_id,
            "trial_id": result.get("trial_id"),
            "retry_request_id": result.get("retry_request_id"),
            "execution_mode": result.get("execution_mode"),
            "observe_task_details": result.get("observe_task_details"),
        }
        self._audit(
            action="trial.requested",
            actor_id=user_id,
            actor_role="member",
            target_id=template_id,
            status=str(result["status"]),
            detail=detail,
        )
        return {
            "status": str(result["status"]),
            "template_id": template_id,
            "trial_id": result.get("trial_id"),
            "retry_request_id": result.get("retry_request_id"),
            "execution_mode": result.get("execution_mode"),
            "observe_task_details": result.get("observe_task_details"),
            **({"task_details": result.get("task_details")} if result.get("task_details") else {}),
        }

    def get_trial_status(self, user_id: str, session_id: str, template_id: str) -> dict:
        return self.trial_request_service.trial_service.get_status(
            user_id=user_id,
            session_id=session_id,
            template_id=template_id,
        )

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
    ) -> dict:
        templates = []
        query = template_query.strip().lower()
        normalized_risk = risk_level.strip().lower()
        normalized_review_label = review_label.strip().lower()
        normalized_warning_flag = warning_flag.strip().lower()
        normalized_category = category.strip().lower()
        normalized_tag = tag.strip().lower()
        normalized_source_channel = source_channel.strip().lower()
        matched = []
        for item in self.market_service.list_published_templates():
            if query and query not in item.template_id.lower():
                continue
            if normalized_risk and item.risk_level.lower() != normalized_risk:
                continue
            if normalized_category and str(item.category or "").strip().lower() != normalized_category:
                continue
            if normalized_source_channel and str(item.source_channel or "").strip().lower() != normalized_source_channel:
                continue
            if normalized_tag and not any(str(entry).strip().lower() == normalized_tag for entry in (item.tags or [])):
                continue
            if not self._matches_metadata_filters(
                review_labels=item.review_labels or [],
                warning_flags=item.warning_flags or [],
                review_label=normalized_review_label,
                warning_flag=normalized_warning_flag,
            ):
                continue
            matched.append(item)
        for item in self._sort_templates(matched, sort_by=sort_by, sort_order=sort_order):
            row = self._published_payload(item, self.market_service)
            templates.append(row)
        return {"templates": templates}

    def get_template_detail(self, template_id: str) -> dict:
        published = self.market_service.get_published_template(template_id=template_id)
        if published is None:
            return {"error": "template_not_found", "template_id": template_id}
        return self._published_detail_payload(published, self.market_service)

    def list_member_installations(self, user_id: str, limit: int = 50) -> dict:
        normalized_user_id = str(user_id or "").strip() or "webui-user"
        normalized_limit = max(1, min(int(limit or 50), 200))
        rows = self._member_installations_payload(user_id=normalized_user_id, limit=normalized_limit)
        return {
            "user_id": normalized_user_id,
            "count": len(rows),
            "installations": rows,
        }

    def refresh_member_installations(self, user_id: str, limit: int = 50) -> dict:
        normalized_user_id = str(user_id or "").strip() or "webui-user"
        normalized_limit = max(1, min(int(limit or 50), 200))
        rows = self._member_installations_payload(user_id=normalized_user_id, limit=normalized_limit)
        refreshed_at = self.audit_service.clock.utcnow().isoformat()
        self._audit(
            action="member.installations.refreshed",
            actor_id=normalized_user_id,
            actor_role="member",
            target_id=normalized_user_id,
            status="ok",
            detail={"count": len(rows), "limit": normalized_limit},
        )
        return {
            "user_id": normalized_user_id,
            "count": len(rows),
            "refreshed_at": refreshed_at,
            "installations": rows,
        }

    def list_member_tasks(self, user_id: str, limit: int = 50) -> dict:
        normalized_user_id = str(user_id or "").strip() or "webui-user"
        normalized_limit = max(1, min(int(limit or 50), 200))
        rows = self._member_tasks_payload(user_id=normalized_user_id, limit=normalized_limit)
        return {
            "user_id": normalized_user_id,
            "count": len(rows),
            "tasks": rows,
        }

    def refresh_member_tasks(self, user_id: str, limit: int = 50) -> dict:
        normalized_user_id = str(user_id or "").strip() or "webui-user"
        normalized_limit = max(1, min(int(limit or 50), 200))
        rows = self._member_tasks_payload(user_id=normalized_user_id, limit=normalized_limit)
        refreshed_at = self.audit_service.clock.utcnow().isoformat()
        self._audit(
            action="member.tasks.refreshed",
            actor_id=normalized_user_id,
            actor_role="member",
            target_id=normalized_user_id,
            status="ok",
            detail={"count": len(rows), "limit": normalized_limit},
        )
        return {
            "user_id": normalized_user_id,
            "count": len(rows),
            "refreshed_at": refreshed_at,
            "tasks": rows,
        }

    def list_member_transfer_jobs(
        self,
        user_id: str,
        direction: str = "",
        status: str = "",
        limit: int = 50,
    ) -> dict:
        normalized_user_id = str(user_id or "").strip() or "webui-user"
        normalized_limit = max(1, min(int(limit or 50), 200))
        if self.transfer_job_service is None:
            return {"user_id": normalized_user_id, "count": 0, "jobs": []}
        rows = [
            self._transfer_job_payload(item)
            for item in self.transfer_job_service.list_jobs(
                user_id=normalized_user_id,
                direction=direction,
                status=status,
                limit=normalized_limit,
            )
        ]
        return {
            "user_id": normalized_user_id,
            "count": len(rows),
            "jobs": rows,
        }

    def refresh_member_transfer_jobs(
        self,
        user_id: str,
        direction: str = "",
        status: str = "",
        limit: int = 50,
    ) -> dict:
        normalized_user_id = str(user_id or "").strip() or "webui-user"
        normalized_limit = max(1, min(int(limit or 50), 200))
        payload = self.list_member_transfer_jobs(
            user_id=normalized_user_id,
            direction=direction,
            status=status,
            limit=normalized_limit,
        )
        refreshed_at = self.audit_service.clock.utcnow().isoformat()
        self._audit(
            action="member.transfers.refreshed",
            actor_id=normalized_user_id,
            actor_role="member",
            target_id=normalized_user_id,
            status="ok",
            detail={
                "count": int(payload.get("count", 0) or 0),
                "limit": normalized_limit,
                "direction": str(direction or "").strip().lower(),
                "status_filter": str(status or "").strip().lower(),
            },
        )
        payload["refreshed_at"] = refreshed_at
        return payload

    def uninstall_member_installation(self, user_id: str, template_id: str) -> dict:
        normalized_user_id = str(user_id or "").strip() or "webui-user"
        normalized_template_id = str(template_id or "").strip()
        if not normalized_template_id:
            return {"error": "template_id_required"}
        visible = self._member_installations_payload(user_id=normalized_user_id, limit=200)
        if not any(str(item.get("template_id") or "") == normalized_template_id for item in visible):
            return {
                "error": "member_installation_not_found",
                "user_id": normalized_user_id,
                "template_id": normalized_template_id,
            }
        uninstalled_at = self.audit_service.clock.utcnow().isoformat()
        self._audit(
            action="template.uninstalled",
            actor_id=normalized_user_id,
            actor_role="member",
            target_id=normalized_template_id,
            status="uninstalled",
            detail={},
        )
        return {
            "user_id": normalized_user_id,
            "template_id": normalized_template_id,
            "status": "uninstalled",
            "uninstalled_at": uninstalled_at,
        }

    def install_template(
        self,
        user_id: str,
        session_id: str,
        template_id: str,
        install_options: dict | None = None,
    ) -> dict:
        published = self.market_service.get_published_template(template_id=template_id)
        if not published:
            return {"status": "not_installable", "template_id": template_id}
        normalized_install_options = self._normalize_install_options(install_options)
        if normalized_install_options["preflight"]:
            return {
                "status": "preflight_ready",
                "template_id": template_id,
                "install_options": normalized_install_options,
                "can_install": True,
                "version": published.version,
                "risk_level": published.risk_level,
                "review_labels": list(published.review_labels or []),
                "warning_flags": list(published.warning_flags or []),
                "scan_summary": published.scan_summary or {},
                "prompt_bundle": self.market_service.build_prompt_bundle(template_id=template_id),
            }

        trial = self._request_trial_with_preference(
            user_id=user_id,
            session_id=session_id,
            template_id=template_id,
        )
        result = {
            "status": str(trial["status"]),
            "template_id": template_id,
            "trial_id": trial.get("trial_id"),
            "retry_request_id": trial.get("retry_request_id"),
            "execution_mode": trial.get("execution_mode"),
            "observe_task_details": trial.get("observe_task_details"),
            "prompt_bundle": self.market_service.build_prompt_bundle(template_id=template_id),
            "install_options": normalized_install_options,
        }
        if trial.get("task_details"):
            result["task_details"] = trial["task_details"]
        if self.package_service is not None:
            artifact = self.package_service.export_template_package(
                template_id=template_id,
                source_preference=normalized_install_options["source_preference"],
            )
            result["package_artifact"] = {
                "artifact_id": artifact.artifact_id,
                "path": str(artifact.path),
                "sha256": artifact.sha256,
                "version": artifact.version,
                "filename": artifact.filename,
                "source": artifact.source,
                "size_bytes": artifact.size_bytes,
            }
        result["risk_level"] = published.risk_level
        result["review_note"] = published.review_note
        result["review_labels"] = list(published.review_labels or [])
        result["warning_flags"] = list(published.warning_flags or [])
        result["scan_summary"] = published.scan_summary or {}
        self.market_service.record_template_event(template_id=template_id, event="install")
        self._audit(
            action="template.installed",
            actor_id=user_id,
            actor_role="member",
            target_id=template_id,
            status=str(result["status"]),
            detail={
                "session_id": session_id,
                "execution_mode": result.get("execution_mode"),
                "observe_task_details": result.get("observe_task_details"),
                "install_options": normalized_install_options,
            },
        )
        return result

    def generate_prompt_bundle(self, template_id: str) -> dict:
        bundle = self.market_service.build_prompt_bundle(template_id=template_id)
        self.market_service.record_template_event(template_id=template_id, event="prompt_generation")
        return bundle

    def generate_package(self, template_id: str) -> dict:
        if self.package_service is None:
            return {"error": "package_service_unavailable", "template_id": template_id}
        try:
            artifact = self.package_service.export_template_package(template_id=template_id)
        except ValueError:
            return {"error": "template_not_installable", "template_id": template_id}
        self.market_service.record_template_event(template_id=template_id, event="package_generation")
        return {
            "artifact_id": artifact.artifact_id,
            "template_id": artifact.template_id,
            "version": artifact.version,
            "path": str(artifact.path),
            "sha256": artifact.sha256,
            "filename": artifact.filename,
            "source": artifact.source,
            "size_bytes": artifact.size_bytes,
        }

    def admin_storage_local_summary(self, role: str) -> dict:
        if not self._is_admin_role(role):
            return {"error": "permission_denied"}
        if self.storage_backup_service is None:
            return {"error": "storage_service_unavailable"}
        summary = self.storage_backup_service.get_local_summary()
        self._audit(
            action="storage.local_summary.read",
            actor_id="admin",
            actor_role="admin",
            target_id="storage",
            status="ok",
            detail={},
        )
        return summary

    def admin_storage_get_policies(self, role: str) -> dict:
        if not self._is_admin_role(role):
            return {"error": "permission_denied"}
        if self.storage_backup_service is None:
            return {"error": "storage_service_unavailable"}
        policies = self.storage_backup_service.get_policies()
        self._audit(
            action="storage.policies.read",
            actor_id="admin",
            actor_role="admin",
            target_id="storage-policy",
            status="ok",
            detail={},
        )
        return policies

    def admin_storage_set_policies(self, role: str, patch: dict, admin_id: str = "admin") -> dict:
        if not self._is_admin_role(role):
            return {"error": "permission_denied"}
        if self.storage_backup_service is None:
            return {"error": "storage_service_unavailable"}
        result = self.storage_backup_service.set_policies(
            patch=patch,
            actor_id=admin_id or "admin",
        )
        if result.get("error"):
            return result
        self._audit(
            action="storage.policies.updated",
            actor_id=admin_id or "admin",
            actor_role="admin",
            target_id="storage-policy",
            status="updated",
            detail={"fields": sorted(list((patch or {}).keys())) if isinstance(patch, dict) else []},
        )
        return result

    def admin_storage_run_job(
        self,
        role: str,
        admin_id: str = "admin",
        trigger: str = "manual",
        note: str = "",
    ) -> dict:
        if not self._is_admin_role(role):
            return {"error": "permission_denied"}
        if self.storage_backup_service is None:
            return {"error": "storage_service_unavailable"}
        result = self.storage_backup_service.run_backup_job(
            actor_id=admin_id or "admin",
            trigger=trigger,
            note=note,
        )
        if result.get("error"):
            return result
        job = result.get("job") if isinstance(result.get("job"), dict) else {}
        self._audit(
            action="storage.backup.run",
            actor_id=admin_id or "admin",
            actor_role="admin",
            target_id=str(job.get("job_id", "") or "backup-job"),
            status=str(job.get("status", "") or "unknown"),
            detail={
                "trigger": str(job.get("trigger", "") or ""),
                "artifact_id": str(job.get("artifact_id", "") or ""),
            },
        )
        return result

    def admin_storage_list_jobs(
        self,
        role: str,
        status: str = "",
        limit: int = 50,
    ) -> dict:
        if not self._is_admin_role(role):
            return {"error": "permission_denied"}
        if self.storage_backup_service is None:
            return {"error": "storage_service_unavailable"}
        return self.storage_backup_service.list_backup_jobs(status=status, limit=limit)

    def admin_storage_get_job(self, role: str, job_id: str) -> dict:
        if not self._is_admin_role(role):
            return {"error": "permission_denied", "job_id": job_id}
        if self.storage_backup_service is None:
            return {"error": "storage_service_unavailable", "job_id": job_id}
        return self.storage_backup_service.get_backup_job(job_id=job_id)

    def admin_storage_list_restore_jobs(
        self,
        role: str,
        state: str = "",
        limit: int = 50,
    ) -> dict:
        if not self._is_admin_role(role):
            return {"error": "permission_denied"}
        if self.storage_backup_service is None:
            return {"error": "storage_service_unavailable"}
        result = self.storage_backup_service.list_restore_jobs(state=state, limit=limit)
        self._audit(
            action="storage.restore.jobs.read",
            actor_id="admin",
            actor_role="admin",
            target_id="storage-restore-jobs",
            status="ok",
            detail={"state": str(state or "").strip().lower()},
        )
        return result

    def admin_storage_get_restore_job(self, role: str, restore_id: str) -> dict:
        if not self._is_admin_role(role):
            return {"error": "permission_denied", "restore_id": restore_id}
        if self.storage_backup_service is None:
            return {"error": "storage_service_unavailable", "restore_id": restore_id}
        return self.storage_backup_service.get_restore_job(restore_id=restore_id)

    def admin_storage_restore_prepare(
        self,
        role: str,
        artifact_ref: str,
        admin_id: str = "admin",
        note: str = "",
    ) -> dict:
        if not self._is_admin_role(role):
            return {"error": "permission_denied"}
        if self.storage_backup_service is None:
            return {"error": "storage_service_unavailable"}
        result = self.storage_backup_service.restore_prepare(
            artifact_ref=artifact_ref,
            actor_id=admin_id or "admin",
            note=note,
        )
        if result.get("error"):
            return result
        restore = result.get("restore") if isinstance(result.get("restore"), dict) else {}
        self._audit(
            action="storage.restore.prepare",
            actor_id=admin_id or "admin",
            actor_role="admin",
            target_id=str(restore.get("restore_id", "") or "restore-job"),
            status=str(restore.get("restore_state", "") or "prepared"),
            detail={"artifact_ref": str(restore.get("artifact_ref", "") or "")},
        )
        return result

    def admin_storage_restore_commit(
        self,
        role: str,
        restore_id: str,
        admin_id: str = "admin",
    ) -> dict:
        if not self._is_admin_role(role):
            return {"error": "permission_denied", "restore_id": restore_id}
        if self.storage_backup_service is None:
            return {"error": "storage_service_unavailable", "restore_id": restore_id}
        result = self.storage_backup_service.restore_commit(
            restore_id=restore_id,
            actor_id=admin_id or "admin",
        )
        if result.get("error"):
            return result
        self._audit(
            action="storage.restore.commit",
            actor_id=admin_id or "admin",
            actor_role="admin",
            target_id=restore_id,
            status="committed",
            detail={},
        )
        return result

    def admin_storage_restore_cancel(
        self,
        role: str,
        restore_id: str,
        admin_id: str = "admin",
    ) -> dict:
        if not self._is_admin_role(role):
            return {"error": "permission_denied", "restore_id": restore_id}
        if self.storage_backup_service is None:
            return {"error": "storage_service_unavailable", "restore_id": restore_id}
        result = self.storage_backup_service.restore_cancel(
            restore_id=restore_id,
            actor_id=admin_id or "admin",
        )
        if result.get("error"):
            return result
        self._audit(
            action="storage.restore.cancel",
            actor_id=admin_id or "admin",
            actor_role="admin",
            target_id=restore_id,
            status="cancelled",
            detail={},
        )
        return result

    def admin_list_artifacts(
        self,
        role: str,
        artifact_kind: str = "",
        limit: int = 50,
    ) -> dict:
        if not self._is_admin_role(role):
            return {"error": "permission_denied"}
        if self.artifact_mirror_service is None:
            return {"error": "artifact_service_unavailable"}
        result = self.artifact_mirror_service.list_artifacts(
            artifact_kind=artifact_kind,
            limit=limit,
        )
        self._audit(
            action="artifact.list.read",
            actor_id="admin",
            actor_role="admin",
            target_id="artifacts",
            status="ok",
            detail={"artifact_kind": str(artifact_kind or "").strip().lower(), "limit": int(limit or 50)},
        )
        return result

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
    ) -> dict:
        normalized_artifact_id = str(artifact_id or "").strip()
        if not self._is_admin_role(role):
            return {"error": "permission_denied", "artifact_id": normalized_artifact_id}
        if self.artifact_mirror_service is None:
            return {"error": "artifact_service_unavailable", "artifact_id": normalized_artifact_id}
        result = self.artifact_mirror_service.mirror_artifact(
            artifact_id=normalized_artifact_id,
            remote_path=remote_path,
            actor_id=admin_id or "admin",
            rclone_binary=rclone_binary,
            timeout_seconds=timeout_seconds,
            bwlimit=bwlimit,
            encryption_required=encryption_required,
            remote_encryption_verified=remote_encryption_verified,
        )
        if result.get("error"):
            self._audit(
                action="artifact.remote_mirror",
                actor_id=admin_id or "admin",
                actor_role="admin",
                target_id=normalized_artifact_id or "artifact",
                status="failed",
                detail={
                    "error": str(result.get("error", "") or ""),
                    "remote_path": str(remote_path or "").strip(),
                },
            )
            return result
        mirror = result.get("mirror") if isinstance(result.get("mirror"), dict) else {}
        self._audit(
            action="artifact.remote_mirror",
            actor_id=admin_id or "admin",
            actor_role="admin",
            target_id=normalized_artifact_id or "artifact",
            status=str(mirror.get("status", "") or "succeeded"),
            detail={"remote_path": str(mirror.get("remote_path", "") or "")},
        )
        return result

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
    ) -> dict:
        if role != "admin":
            return {"error": "permission_denied", "pack_id": pack_id}
        if self.profile_pack_service is None:
            return {"error": "profile_pack_service_unavailable", "pack_id": pack_id}
        try:
            artifact = self.profile_pack_service.export_bot_profile_pack(
                pack_id=pack_id,
                version=version,
                pack_type=pack_type,
                redaction_mode=redaction_mode,
                sections=sections,
                mask_paths=mask_paths,
                drop_paths=drop_paths,
            )
        except ValueError as exc:
            return self._profile_pack_error_payload(exc=exc, fallback_id=pack_id)
        self._audit(
            action="profile_pack.exported",
            actor_id="admin",
            actor_role="admin",
            target_id=artifact.artifact_id,
            status="exported",
            detail={"pack_id": artifact.pack_id, "version": artifact.version},
        )
        return {
            "artifact_id": artifact.artifact_id,
            "pack_type": artifact.manifest.pack_type,
            "pack_id": artifact.pack_id,
            "version": artifact.version,
            "path": str(artifact.path),
            "filename": artifact.filename,
            "sha256": artifact.sha256,
            "size_bytes": artifact.size_bytes,
            "sections": list(artifact.manifest.sections),
            "redaction_mode": artifact.manifest.redaction_policy.mode,
            "redaction_notes": list(artifact.redaction_notes),
        }

    def admin_get_profile_pack_export(self, role: str, artifact_id: str) -> dict:
        if role != "admin":
            return {"error": "permission_denied", "artifact_id": artifact_id}
        if self.profile_pack_service is None:
            return {"error": "profile_pack_service_unavailable", "artifact_id": artifact_id}
        try:
            artifact = self.profile_pack_service.get_export_artifact(artifact_id=artifact_id)
        except ValueError as exc:
            return self._profile_pack_error_payload(exc=exc, fallback_id=artifact_id)
        return {
            "artifact_id": artifact.artifact_id,
            "pack_type": artifact.manifest.pack_type,
            "pack_id": artifact.pack_id,
            "version": artifact.version,
            "exported_at": artifact.exported_at,
            "path": str(artifact.path),
            "filename": artifact.filename,
            "sha256": artifact.sha256,
            "size_bytes": artifact.size_bytes,
        }

    def admin_list_profile_pack_exports(self, role: str, limit: int = 50) -> dict:
        if role != "admin":
            return {"error": "permission_denied"}
        if self.profile_pack_service is None:
            return {"error": "profile_pack_service_unavailable"}
        return {"exports": self.profile_pack_service.list_exports(limit=limit)}

    def admin_import_profile_pack(
        self,
        role: str,
        filename: str,
        content_base64: str,
    ) -> dict:
        if role != "admin":
            return {"error": "permission_denied"}
        if self.profile_pack_service is None:
            return {"error": "profile_pack_service_unavailable"}
        try:
            content = base64.b64decode(content_base64.encode("ascii"), validate=True)
        except (binascii.Error, ValueError):
            return {"error": "invalid_profile_pack_payload"}
        try:
            imported = self.profile_pack_service.import_bot_profile_pack(
                filename=filename,
                content=content,
            )
        except ValueError as exc:
            return self._profile_pack_error_payload(exc=exc, fallback_id=filename)
        self._audit(
            action="profile_pack.imported",
            actor_id="admin",
            actor_role="admin",
            target_id=imported.import_id,
            status=imported.compatibility,
            detail={"filename": imported.filename},
        )
        return self._profile_pack_import_payload(imported)

    def member_import_profile_pack(
        self,
        user_id: str,
        filename: str,
        content_base64: str,
    ) -> dict:
        if self.profile_pack_service is None:
            return {"error": "profile_pack_service_unavailable"}
        try:
            content = base64.b64decode(content_base64.encode("ascii"), validate=True)
        except (binascii.Error, ValueError):
            return {"error": "invalid_profile_pack_payload"}
        try:
            imported = self.profile_pack_service.import_member_profile_pack(
                user_id=user_id,
                filename=filename,
                content=content,
            )
        except ValueError as exc:
            return self._profile_pack_error_payload(exc=exc, fallback_id=filename)
        self._audit(
            action="profile_pack.imported",
            actor_id=str(user_id or "").strip() or "member",
            actor_role="member",
            target_id=imported.import_id,
            status=imported.compatibility,
            detail={
                "filename": imported.filename,
                "source_artifact_id": imported.source_artifact_id,
            },
        )
        return self._profile_pack_import_payload(imported)

    def member_import_local_astrbot_config(self, user_id: str) -> dict:
        if self.profile_pack_service is None:
            return {"error": "profile_pack_service_unavailable"}
        config_path, probe = self._probe_local_astrbot_config_path()
        if config_path is None:
            return {"error": "astrbot_local_config_not_found", "probe": probe}
        try:
            content = config_path.read_bytes()
        except OSError:
            return {"error": "astrbot_local_config_read_failed", "probe": probe}
        try:
            imported = self.profile_pack_service.import_member_profile_pack(
                user_id=user_id,
                filename=config_path.name,
                content=content,
                import_origin="local_astrbot_detected",
                source_fingerprint=self._local_astrbot_source_fingerprint(config_path),
                refresh_existing=True,
            )
        except ValueError as exc:
            return self._profile_pack_error_payload(exc=exc, fallback_id=config_path.name)
        self._audit(
            action="profile_pack.imported",
            actor_id=str(user_id or "").strip() or "member",
            actor_role="member",
            target_id=imported.import_id,
            status=imported.compatibility,
            detail={
                "filename": imported.filename,
                "source_artifact_id": imported.source_artifact_id,
                "source": "local_astrbot_config",
            },
        )
        payload = self._profile_pack_import_payload(imported)
        payload["probe"] = probe
        return payload

    def member_probe_local_astrbot_config(self, user_id: str) -> dict:
        if self.profile_pack_service is None:
            return {"error": "profile_pack_service_unavailable"}
        _path, probe = self._probe_local_astrbot_config_path()
        return probe

    def member_delete_profile_pack_import(self, user_id: str, import_id: str) -> dict:
        if self.profile_pack_service is None:
            return {"error": "profile_pack_service_unavailable"}
        normalized_user_id = str(user_id or "").strip() or "member"
        normalized_import_id = str(import_id or "").strip()
        if not normalized_import_id:
            return {"error": "profile_import_not_found", "import_id": normalized_import_id}
        try:
            deleted = self.profile_pack_service.delete_import(
                user_id=normalized_user_id,
                import_id=normalized_import_id,
            )
        except ValueError as exc:
            return self._profile_pack_error_payload(exc=exc, fallback_id=normalized_import_id)
        self._audit(
            action="profile_pack.import_deleted",
            actor_id=normalized_user_id,
            actor_role="member",
            target_id=deleted.import_id,
            status="deleted",
            detail={
                "pack_id": deleted.manifest.pack_id,
                "source_artifact_id": deleted.source_artifact_id,
            },
        )
        return {
            "deleted": True,
            "import_id": deleted.import_id,
            "user_id": normalized_user_id,
        }

    def admin_import_profile_pack_from_export(
        self,
        role: str,
        artifact_id: str,
    ) -> dict:
        if role != "admin":
            return {"error": "permission_denied", "artifact_id": artifact_id}
        if self.profile_pack_service is None:
            return {"error": "profile_pack_service_unavailable", "artifact_id": artifact_id}
        try:
            artifact = self.profile_pack_service.get_export_artifact(artifact_id=artifact_id)
        except ValueError as exc:
            return self._profile_pack_error_payload(exc=exc, fallback_id=artifact_id)
        if not artifact.path.exists():
            return {"error": "profile_pack_not_found", "artifact_id": artifact_id}
        try:
            imported = self.profile_pack_service.import_bot_profile_pack(
                filename=artifact.filename,
                content=artifact.path.read_bytes(),
            )
        except ValueError as exc:
            return self._profile_pack_error_payload(exc=exc, fallback_id=artifact_id)
        self._audit(
            action="profile_pack.imported_from_export",
            actor_id="admin",
            actor_role="admin",
            target_id=imported.import_id,
            status=imported.compatibility,
            detail={"filename": imported.filename, "source_artifact_id": artifact_id},
        )
        payload = self._profile_pack_import_payload(imported)
        payload["source_artifact_id"] = artifact_id
        return payload

    @classmethod
    def _detect_local_astrbot_config_path(cls) -> Path:
        path, _probe = cls._probe_local_astrbot_config_path()
        if path is None:
            raise FileNotFoundError("local AstrBot cmd_config.json not found")
        return path

    @classmethod
    def _probe_local_astrbot_config_path(cls) -> tuple[Path | None, dict[str, Any]]:
        configured_hint = str(os.getenv("SHARELIFE_ASTRBOT_CONFIG_PATH", "") or "").strip()
        repo_root = Path(__file__).resolve().parents[2]
        workspace_root = Path(__file__).resolve().parents[3]
        cwd_root = Path.cwd()
        home_root = Path.home()
        user_profile_text = str(os.getenv("USERPROFILE", "") or "").strip()
        user_profile_root = Path(user_profile_text).expanduser() if user_profile_text else home_root

        candidate_entries: list[tuple[Path, str]] = []
        candidate_entries.extend(cls._astrbot_candidates_from_env_hint(configured_hint))

        search_roots: list[Path] = []
        env_home_roots = cls._astrbot_env_paths(os.getenv("SHARELIFE_ASTRBOT_HOME", ""))
        env_search_roots = cls._astrbot_env_paths(os.getenv("SHARELIFE_ASTRBOT_SEARCH_ROOTS", ""))
        search_roots.extend(env_home_roots)
        search_roots.extend(env_search_roots)
        default_roots = [
            cwd_root,
            cwd_root.parent,
            repo_root,
            repo_root.parent,
            workspace_root,
            home_root,
            home_root / "astrbot",
            home_root / ".astrbot",
            home_root / ".config" / "astrbot",
            home_root / ".local" / "share" / "astrbot",
            home_root / "Library" / "Application Support" / "AstrBot",
            home_root / "Library" / "Application Support" / "astrbot",
            user_profile_root / "AppData" / "Roaming" / "AstrBot",
            user_profile_root / "AppData" / "Local" / "AstrBot",
            Path("/opt/astrbot"),
            Path("/var/lib/astrbot"),
        ]
        search_roots.extend(
            default_roots
        )

        xdg_config_home = str(os.getenv("XDG_CONFIG_HOME", "") or "").strip()
        xdg_data_home = str(os.getenv("XDG_DATA_HOME", "") or "").strip()
        default_root_count = len(default_roots)
        if xdg_config_home:
            search_roots.append(Path(xdg_config_home).expanduser() / "astrbot")
            default_root_count += 1
        if xdg_data_home:
            search_roots.append(Path(xdg_data_home).expanduser() / "astrbot")
            default_root_count += 1

        seen_roots: set[str] = set()
        env_home_root_set = {str(root.expanduser()) for root in env_home_roots}
        env_search_root_set = {str(root.expanduser()) for root in env_search_roots}
        for root in search_roots:
            normalized_root = str(root.expanduser())
            if not normalized_root or normalized_root in seen_roots:
                continue
            seen_roots.add(normalized_root)
            source_kind = "default_roots"
            if normalized_root in env_home_root_set:
                source_kind = "astrbot_home"
            elif normalized_root in env_search_root_set:
                source_kind = "search_roots"
            candidate_entries.extend(cls._astrbot_candidates_from_root(root, source_kind=source_kind))

        checked_candidate_count = 0
        matched_source = ""
        seen_candidates: set[str] = set()
        for candidate, source_kind in candidate_entries:
            resolved = candidate.expanduser()
            normalized = str(resolved)
            if not normalized or normalized in seen_candidates:
                continue
            seen_candidates.add(normalized)
            checked_candidate_count += 1
            if resolved.is_file():
                matched_source = source_kind
                return resolved.resolve(), {
                    "detected": True,
                    "filename": resolved.name,
                    "matched_source": matched_source,
                    "checked_candidate_count": checked_candidate_count,
                    "hint_env_keys": [
                        "SHARELIFE_ASTRBOT_CONFIG_PATH",
                        "SHARELIFE_ASTRBOT_SEARCH_ROOTS",
                        "SHARELIFE_ASTRBOT_HOME",
                    ],
                    "path_list_separator": os.pathsep,
                }
        return None, {
            "detected": False,
            "filename": "",
            "matched_source": "",
            "checked_candidate_count": checked_candidate_count,
            "hint_env_keys": [
                "SHARELIFE_ASTRBOT_CONFIG_PATH",
                "SHARELIFE_ASTRBOT_SEARCH_ROOTS",
                "SHARELIFE_ASTRBOT_HOME",
            ],
            "path_list_separator": os.pathsep,
            "default_root_count": default_root_count,
        }

    @staticmethod
    def _astrbot_env_paths(raw_text: str | None) -> list[Path]:
        text = str(raw_text or "").strip()
        if not text:
            return []
        paths: list[Path] = []
        for part in text.split(os.pathsep):
            candidate = str(part or "").strip()
            if not candidate:
                continue
            paths.append(Path(candidate).expanduser())
        return paths

    @classmethod
    def _astrbot_candidates_from_env_hint(cls, raw_text: str) -> list[tuple[Path, str]]:
        paths = cls._astrbot_env_paths(raw_text)
        if not paths:
            return []
        out: list[tuple[Path, str]] = []
        for hint_path in paths:
            if hint_path.suffix.lower() == ".json":
                out.append((hint_path, "config_path_file"))
                continue
            out.extend(cls._astrbot_candidates_from_root(hint_path, source_kind="config_path_root"))
        return out

    @classmethod
    def _astrbot_candidates_from_root(cls, root: Path, *, source_kind: str) -> list[tuple[Path, str]]:
        normalized_root = root.expanduser()
        suffixes = (
            ("cmd_config.json",),
            ("data", "cmd_config.json"),
            ("config", "cmd_config.json"),
            ("astrbot", "data", "cmd_config.json"),
            ("astrbot", "config", "cmd_config.json"),
            ("AstrBot", "data", "cmd_config.json"),
            ("AstrBot", "config", "cmd_config.json"),
            (".astrbot", "data", "cmd_config.json"),
            (".config", "astrbot", "cmd_config.json"),
            (".local", "share", "astrbot", "cmd_config.json"),
            ("AppData", "Roaming", "AstrBot", "data", "cmd_config.json"),
            ("AppData", "Local", "AstrBot", "data", "cmd_config.json"),
        )
        out: list[tuple[Path, str]] = []
        for segments in suffixes:
            out.append((normalized_root.joinpath(*segments), source_kind))
        return out

    def admin_import_profile_pack_and_dryrun(
        self,
        role: str,
        plan_id: str,
        selected_sections: list[str] | None = None,
        filename: str = "",
        content_base64: str = "",
        artifact_id: str = "",
    ) -> dict:
        if role != "admin":
            return {"error": "permission_denied", "plan_id": plan_id}
        normalized_plan_id = str(plan_id or "").strip()
        if not normalized_plan_id:
            return {"error": "plan_id_required"}

        normalized_artifact_id = str(artifact_id or "").strip()
        if normalized_artifact_id:
            imported = self.admin_import_profile_pack_from_export(role=role, artifact_id=normalized_artifact_id)
        else:
            imported = self.admin_import_profile_pack(
                role=role,
                filename=filename,
                content_base64=content_base64,
            )
        if imported.get("error"):
            return imported

        dryrun = self.admin_profile_pack_dryrun(
            role=role,
            import_id=str(imported.get("import_id", "") or ""),
            plan_id=normalized_plan_id,
            selected_sections=selected_sections,
        )
        if dryrun.get("error"):
            return {
                "error": str(dryrun.get("error", "") or "request_failed"),
                "import_id": str(imported.get("import_id", "") or ""),
                "plan_id": normalized_plan_id,
                "import": imported,
            }
        return {
            "status": "imported_dryrun_ready",
            "import_id": str(imported.get("import_id", "") or ""),
            "plan_id": str(dryrun.get("plan_id", normalized_plan_id) or normalized_plan_id),
            "pack_id": str(imported.get("pack_id", "") or ""),
            "selected_sections": list(dryrun.get("selected_sections", []) or []),
            "compatibility": str(imported.get("compatibility", "") or "unknown"),
            "compatibility_issues": list(imported.get("compatibility_issues", []) or []),
            "scan_summary": imported.get("scan_summary", {}) or {},
            "source_artifact_id": str(imported.get("source_artifact_id", "") or ""),
            "import": imported,
            "dryrun": dryrun,
        }

    def admin_list_profile_pack_imports(self, role: str, limit: int = 50) -> dict:
        if role != "admin":
            return {"error": "permission_denied"}
        if self.profile_pack_service is None:
            return {"error": "profile_pack_service_unavailable"}
        return {"imports": self.profile_pack_service.list_imports(limit=limit)}

    def member_list_profile_pack_imports(self, user_id: str, limit: int = 50) -> dict:
        if self.profile_pack_service is None:
            return {"error": "profile_pack_service_unavailable"}
        normalized_user_id = str(user_id or "").strip() or "member"
        return {
            "user_id": normalized_user_id,
            "imports": self.profile_pack_service.list_imports(
                limit=limit,
                user_id=normalized_user_id,
            ),
        }

    @staticmethod
    def _local_astrbot_source_fingerprint(config_path: Path) -> str:
        normalized = str(config_path.expanduser().resolve())
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def admin_profile_pack_dryrun(
        self,
        role: str,
        import_id: str,
        plan_id: str,
        selected_sections: list[str] | None = None,
    ) -> dict:
        if role != "admin":
            return {"error": "permission_denied", "import_id": import_id}
        if self.profile_pack_service is None:
            return {"error": "profile_pack_service_unavailable", "import_id": import_id}
        try:
            result = self.profile_pack_service.prepare_apply_plan(
                import_id=import_id,
                plan_id=plan_id,
                selected_sections=selected_sections,
            )
        except ValueError as exc:
            return self._profile_pack_error_payload(exc=exc, fallback_id=import_id)
        self._audit(
            action="profile_pack.dryrun_prepared",
            actor_id="admin",
            actor_role="admin",
            target_id=result["plan_id"],
            status=result["status"],
            detail={"import_id": import_id, "selected_sections": result.get("selected_sections", [])},
        )
        return result

    def admin_profile_pack_plugin_install_plan(
        self,
        role: str,
        import_id: str,
    ) -> dict:
        if role != "admin":
            return {"error": "permission_denied", "import_id": import_id}
        if self.profile_pack_service is None:
            return {"error": "profile_pack_service_unavailable", "import_id": import_id}
        try:
            result = self.profile_pack_service.profile_pack_plugin_install_plan(import_id=import_id)
        except ValueError as exc:
            return self._profile_pack_error_payload(exc=exc, fallback_id=import_id)
        self._audit(
            action="profile_pack.plugin_install_plan_viewed",
            actor_id="admin",
            actor_role="admin",
            target_id=import_id,
            status=str(result.get("status", "unknown") or "unknown"),
            detail={
                "required_plugins": list(result.get("required_plugins", []) or []),
                "missing_plugins": list(result.get("missing_plugins", []) or []),
            },
        )
        return result

    def admin_profile_pack_confirm_plugin_install(
        self,
        role: str,
        import_id: str,
        plugin_ids: list[str] | None = None,
    ) -> dict:
        if role != "admin":
            return {"error": "permission_denied", "import_id": import_id}
        if self.profile_pack_service is None:
            return {"error": "profile_pack_service_unavailable", "import_id": import_id}
        try:
            result = self.profile_pack_service.confirm_profile_pack_plugin_install(
                import_id=import_id,
                plugin_ids=plugin_ids,
            )
        except ValueError as exc:
            return self._profile_pack_error_payload(exc=exc, fallback_id=import_id)
        self._audit(
            action="profile_pack.plugin_install_confirmed",
            actor_id="admin",
            actor_role="admin",
            target_id=import_id,
            status=str(result.get("status", "unknown") or "unknown"),
            detail={
                "confirmed_plugins": list(result.get("confirmed_plugins", []) or []),
                "missing_plugins": list(result.get("missing_plugins", []) or []),
            },
        )
        return result

    def admin_profile_pack_execute_plugin_install(
        self,
        role: str,
        import_id: str,
        plugin_ids: list[str] | None = None,
        dry_run: bool = False,
    ) -> dict:
        if role != "admin":
            return {"error": "permission_denied", "import_id": import_id}
        if self.profile_pack_service is None:
            return {"error": "profile_pack_service_unavailable", "import_id": import_id}
        try:
            result = self.profile_pack_service.execute_profile_pack_plugin_install(
                import_id=import_id,
                plugin_ids=plugin_ids,
                dry_run=bool(dry_run),
            )
        except ValueError as exc:
            return self._profile_pack_error_payload(exc=exc, fallback_id=import_id)
        execution = result.get("execution", {}) if isinstance(result, dict) else {}
        output = execution.get("result", {}) if isinstance(execution, dict) else {}
        self._audit(
            action="profile_pack.plugin_install_executed",
            actor_id="admin",
            actor_role="admin",
            target_id=import_id,
            status=str(result.get("status", "unknown") or "unknown"),
            detail={
                "dry_run": bool(dry_run),
                "requested_plugins": list(execution.get("requested_plugins", []) or []),
                "installed_count": int(output.get("installed_count", 0) or 0),
                "failed_count": int(output.get("failed_count", 0) or 0),
                "blocked_count": int(output.get("blocked_count", 0) or 0),
            },
        )
        return result

    def admin_profile_pack_apply(self, role: str, plan_id: str) -> dict:
        if role != "admin":
            return {"error": "permission_denied", "plan_id": plan_id}
        try:
            continuity = self.apply_service.apply(plan_id=plan_id)
        except ValueError as exc:
            return self._apply_error_payload(plan_id=plan_id, exc=exc)
        self._audit(
            action="profile_pack.applied",
            actor_id="admin",
            actor_role="admin",
            target_id=plan_id,
            status="applied",
            detail={"continuity": continuity},
        )
        payload = {"plan_id": plan_id, "status": "applied"}
        if continuity:
            payload["continuity"] = continuity
        return payload

    def admin_profile_pack_rollback(self, role: str, plan_id: str) -> dict:
        if role != "admin":
            return {"error": "permission_denied", "plan_id": plan_id}
        try:
            continuity = self.apply_service.rollback(plan_id=plan_id)
        except ValueError as exc:
            return self._apply_error_payload(plan_id=plan_id, exc=exc)
        self._audit(
            action="profile_pack.rolled_back",
            actor_id="admin",
            actor_role="admin",
            target_id=plan_id,
            status="rolled_back",
            detail={"continuity": continuity},
        )
        payload = {"plan_id": plan_id, "status": "rolled_back"}
        if continuity:
            payload["continuity"] = continuity
        return payload

    def admin_list_continuity(self, role: str, limit: int = 20) -> dict:
        if role != "admin":
            return {"error": "permission_denied"}
        continuity_service = self._continuity_service()
        if continuity_service is None:
            return {"error": "continuity_unavailable"}
        return {"entries": continuity_service.list_entries(limit=max(1, int(limit or 20)))}

    def admin_get_continuity(self, role: str, plan_id: str) -> dict:
        if role != "admin":
            return {"error": "permission_denied", "plan_id": plan_id}
        normalized_plan_id = str(plan_id or "").strip()
        if not normalized_plan_id:
            return {"error": "plan_id_required"}
        continuity_service = self._continuity_service()
        if continuity_service is None:
            return {"error": "continuity_unavailable", "plan_id": normalized_plan_id}
        entry = continuity_service.describe(normalized_plan_id)
        if entry is None:
            return {"error": "continuity_not_found", "plan_id": normalized_plan_id}
        return {"plan_id": normalized_plan_id, "entry": entry}

    def submit_profile_pack(
        self,
        user_id: str,
        artifact_id: str,
        submit_options: dict | None = None,
    ) -> dict:
        if self.profile_pack_service is None:
            return {"error": "profile_pack_service_unavailable"}
        normalized_artifact_id = str(artifact_id or "").strip()
        if not normalized_artifact_id:
            return {"error": "profile_pack_source_required"}
        normalized_submit_options = self._normalize_profile_pack_submit_options(submit_options)
        normalized_idempotency_key = self._normalize_idempotency_key(
            normalized_submit_options.get("idempotency_key"),
        )
        if normalized_idempotency_key:
            existing = self._find_any_profile_pack_submission_by_idempotency(
                user_id=user_id,
                idempotency_key=normalized_idempotency_key,
            )
            if existing is not None:
                existing_artifact_id = str(getattr(existing, "artifact_id", "") or "").strip()
                if existing_artifact_id != normalized_artifact_id:
                    self._audit(
                        action="profile_pack.submission.idempotency_conflict",
                        actor_id=user_id,
                        actor_role="member",
                        target_id=str(getattr(existing, "submission_id", "") or ""),
                        status="conflict",
                        detail={
                            "artifact_id": normalized_artifact_id,
                            "existing_artifact_id": existing_artifact_id,
                            "idempotency_key_fingerprint": self._idempotency_key_fingerprint(
                                normalized_idempotency_key,
                            ),
                        },
                    )
                    return {
                        "error": "idempotency_key_conflict",
                        "artifact_id": normalized_artifact_id,
                        "existing_submission_id": str(getattr(existing, "submission_id", "") or ""),
                    }
                self._audit(
                    action="profile_pack.submission.idempotency_replayed",
                    actor_id=user_id,
                    actor_role="member",
                    target_id=str(getattr(existing, "submission_id", "") or ""),
                    status=str(getattr(existing, "status", "pending") or "pending"),
                    detail={
                        "artifact_id": normalized_artifact_id,
                        "idempotency_key_fingerprint": self._idempotency_key_fingerprint(
                            normalized_idempotency_key,
                        ),
                    },
                )
                payload = self._profile_pack_submission_payload(existing)
                payload["idempotent_replay"] = True
                payload["replaced_submission_ids"] = []
                payload["replaced_submission_count"] = 0
                return payload
        try:
            submission = self.profile_pack_service.submit_export_artifact(
                user_id=user_id,
                artifact_id=normalized_artifact_id,
                submit_options=normalized_submit_options,
            )
        except ValueError as exc:
            return self._profile_pack_error_payload(exc=exc, fallback_id=normalized_artifact_id)
        replaced_submission_ids: list[str] = []
        if normalized_submit_options.get("replace_existing"):
            replaced_submission_ids = self.profile_pack_service.replace_pending_submissions(
                user_id=user_id,
                pack_id=submission.pack_id,
                exclude_submission_id=submission.submission_id,
            )
            if replaced_submission_ids:
                self._audit(
                    action="profile_pack.submission.pending_replaced",
                    actor_id=user_id,
                    actor_role="member",
                    target_id=submission.pack_id,
                    status="replaced",
                    detail={
                        "pack_id": submission.pack_id,
                        "replace_existing": True,
                        "replaced_submission_ids": list(replaced_submission_ids),
                    },
                )
        self._audit(
            action="profile_pack.submission_created",
            actor_id=user_id,
            actor_role="member",
            target_id=submission.submission_id,
            status=submission.status,
            detail={
                "pack_id": submission.pack_id,
                "version": submission.version,
                "submit_options": normalized_submit_options,
                "replaced_submission_ids": list(replaced_submission_ids),
                "replaced_submission_count": len(replaced_submission_ids),
            },
        )
        payload = self._profile_pack_submission_payload(submission)
        payload["submit_options"] = normalized_submit_options
        payload["replaced_submission_ids"] = list(replaced_submission_ids)
        payload["replaced_submission_count"] = len(replaced_submission_ids)
        return payload

    def admin_create_reviewer_invite(
        self,
        role: str,
        admin_id: str,
        expires_in_seconds: int = 3600,
    ) -> dict:
        if not self._is_admin_role(role):
            return {"error": "permission_denied"}
        if self.reviewer_auth_service is None:
            return {"error": "reviewer_auth_service_unavailable"}
        issued = self.reviewer_auth_service.create_invite(
            admin_id=admin_id or "admin",
            expires_in_seconds=expires_in_seconds,
        )
        if issued.get("error"):
            return issued
        self._audit(
            action="reviewer.invite_created",
            actor_id=str(admin_id or "admin"),
            actor_role="admin",
            target_id=str(issued.get("invite_code", "")),
            status=str(issued.get("status", "invite_issued")),
            detail={"expires_in_seconds": int(issued.get("expires_in_seconds", 0) or 0)},
        )
        return issued

    def admin_list_reviewer_invites(self, role: str, status: str = "") -> dict:
        if not self._is_admin_role(role):
            return {"error": "permission_denied"}
        if self.reviewer_auth_service is None:
            return {"error": "reviewer_auth_service_unavailable"}
        return {"invites": self.reviewer_auth_service.list_invites(status=status)}

    def admin_revoke_reviewer_invite(
        self,
        role: str,
        invite_code: str,
        admin_id: str,
    ) -> dict:
        if not self._is_admin_role(role):
            return {"error": "permission_denied"}
        if self.reviewer_auth_service is None:
            return {"error": "reviewer_auth_service_unavailable"}
        result = self.reviewer_auth_service.revoke_invite(
            invite_code=invite_code,
            admin_id=admin_id or "admin",
        )
        if result.get("error"):
            return result
        self._audit(
            action="reviewer.invite_revoked",
            actor_id=str(admin_id or "admin"),
            actor_role="admin",
            target_id=str(result.get("invite_code", "") or invite_code or ""),
            status=str(result.get("status", "revoked")),
            detail={
                "invite_code": str(result.get("invite_code", "") or invite_code or ""),
                "revoked_by": str(result.get("revoked_by", "") or admin_id or "admin"),
            },
        )
        return result

    def reviewer_redeem_invite(self, invite_code: str, reviewer_id: str) -> dict:
        if self.reviewer_auth_service is None:
            return {"error": "reviewer_auth_service_unavailable"}
        result = self.reviewer_auth_service.redeem_invite(
            invite_code=invite_code,
            reviewer_id=reviewer_id,
        )
        if result.get("error"):
            return result
        self._audit(
            action="reviewer.invite_redeemed",
            actor_id=str(reviewer_id or ""),
            actor_role="reviewer",
            target_id=str(result.get("reviewer_id", "") or reviewer_id or ""),
            status=str(result.get("status", "invite_redeemed")),
            detail={
                "reviewer_id": str(result.get("reviewer_id", "") or reviewer_id or ""),
                "invite_code": str(invite_code or ""),
                "created": bool(result.get("created")),
            },
        )
        return result

    def reviewer_register_device(self, reviewer_id: str, label: str = "") -> dict:
        if self.reviewer_auth_service is None:
            return {"error": "reviewer_auth_service_unavailable"}
        result = self.reviewer_auth_service.register_device(user_id=reviewer_id, label=label)
        if result.get("error"):
            return result
        self._audit(
            action="reviewer.device_registered",
            actor_id=str(reviewer_id or ""),
            actor_role="reviewer",
            target_id=str(result.get("device_id", "")),
            status=str(result.get("status", "registered")),
            detail={
                "reviewer_id": str(result.get("reviewer_id", "") or reviewer_id or ""),
                "device_id": str(result.get("device_id", "") or ""),
                "label": str(result.get("label", "") or label or ""),
                "max_devices": int(result.get("max_devices", 0) or 0),
            },
        )
        return result

    def reviewer_list_devices(self, reviewer_id: str) -> dict:
        if self.reviewer_auth_service is None:
            return {"error": "reviewer_auth_service_unavailable"}
        return {
            "reviewer_id": reviewer_id,
            "max_devices": int(self.reviewer_auth_service.max_devices),
            "devices": self.reviewer_auth_service.list_devices(user_id=reviewer_id),
        }

    def reviewer_revoke_device(self, reviewer_id: str, device_id: str) -> dict:
        if self.reviewer_auth_service is None:
            return {"error": "reviewer_auth_service_unavailable"}
        revoked = self.reviewer_auth_service.revoke_device(user_id=reviewer_id, device_id=device_id)
        if not revoked:
            return {
                "error": "device_not_found",
                "reviewer_id": reviewer_id,
                "device_id": device_id,
            }
        self._audit(
            action="reviewer.device_revoked",
            actor_id=str(reviewer_id or ""),
            actor_role="reviewer",
            target_id=str(device_id or ""),
            status="revoked",
            detail={
                "reviewer_id": str(reviewer_id or ""),
                "device_id": str(device_id or ""),
            },
        )
        return {
            "status": "revoked",
            "reviewer_id": reviewer_id,
            "device_id": device_id,
        }

    def admin_list_reviewers(self, role: str) -> dict:
        if not self._is_admin_role(role):
            return {"error": "permission_denied"}
        if self.reviewer_auth_service is None:
            return {"error": "reviewer_auth_service_unavailable"}
        return {
            "reviewers": self.reviewer_auth_service.list_reviewers(),
            "max_devices": int(self.reviewer_auth_service.max_devices),
        }

    def admin_force_reset_reviewer_devices(
        self,
        role: str,
        reviewer_id: str,
        admin_id: str,
    ) -> dict:
        if not self._is_admin_role(role):
            return {"error": "permission_denied"}
        if self.reviewer_auth_service is None:
            return {"error": "reviewer_auth_service_unavailable"}
        uid = str(reviewer_id or "").strip()
        if not uid:
            return {"error": "reviewer_id_required"}
        revoked = self.reviewer_auth_service.revoke_all_devices(user_id=uid)
        self._audit(
            action="reviewer.device_force_reset",
            actor_id=str(admin_id or "admin"),
            actor_role="admin",
            target_id=uid,
            status="revoked",
            detail={
                "reviewer_id": uid,
                "revoked_devices": revoked,
            },
        )
        return {
            "status": "reset",
            "reviewer_id": uid,
            "revoked_devices": revoked,
        }

    def admin_record_reviewer_session_revoke(
        self,
        role: str,
        reviewer_id: str,
        admin_id: str,
        revoked_sessions: int,
        device_id: str = "",
        session_id: str = "",
    ) -> dict:
        if not self._is_admin_role(role):
            return {"error": "permission_denied"}
        uid = str(reviewer_id or "").strip()
        if not uid:
            return {"error": "reviewer_id_required"}
        normalized_device_id = str(device_id or "").strip()
        normalized_session_id = str(session_id or "").strip()
        count = max(0, int(revoked_sessions or 0))
        detail: dict[str, Any] = {
            "reviewer_id": uid,
            "revoked_sessions": count,
        }
        if normalized_device_id:
            detail["device_id"] = normalized_device_id
        if normalized_session_id:
            detail["session_id"] = normalized_session_id
        self._audit(
            action="reviewer.session_force_revoke",
            actor_id=str(admin_id or "admin"),
            actor_role="admin",
            target_id=uid,
            status="revoked" if count else "noop",
            detail=detail,
        )
        return {
            "status": "revoked" if count else "noop",
            "reviewer_id": uid,
            "device_id": normalized_device_id,
            "session_id": normalized_session_id,
            "revoked_sessions": count,
        }

    def admin_list_profile_pack_submissions(
        self,
        role: str,
        status: str = "",
        pack_query: str = "",
        pack_type: str = "",
        risk_level: str = "",
        review_label: str = "",
        warning_flag: str = "",
    ) -> dict:
        if not self._is_reviewer_role(role):
            return {"error": "permission_denied"}
        if self.profile_pack_service is None:
            return {"error": "profile_pack_service_unavailable"}

        query = str(pack_query or "").strip().lower()
        normalized_pack_type = str(pack_type or "").strip().lower()
        normalized_risk = str(risk_level or "").strip().lower()
        normalized_review_label = str(review_label or "").strip().lower()
        normalized_warning_flag = str(warning_flag or "").strip().lower()

        rows = []
        for item in self.profile_pack_service.list_submissions(status=status):
            if query and query not in item.pack_id.lower():
                continue
            if normalized_pack_type and item.pack_type.lower() != normalized_pack_type:
                continue
            if normalized_risk and item.risk_level.lower() != normalized_risk:
                continue
            if not self._matches_metadata_filters(
                review_labels=item.review_labels,
                warning_flags=item.warning_flags,
                review_label=normalized_review_label,
                warning_flag=normalized_warning_flag,
            ):
                continue
            rows.append(self._profile_pack_submission_payload(item))
        return {"submissions": rows}

    def member_list_profile_pack_submissions(
        self,
        user_id: str,
        status: str = "",
        pack_query: str = "",
        pack_type: str = "",
        risk_level: str = "",
        review_label: str = "",
        warning_flag: str = "",
    ) -> dict:
        if self.profile_pack_service is None:
            return {"error": "profile_pack_service_unavailable"}
        normalized_user_id = str(user_id or "").strip() or "webui-user"
        query = str(pack_query or "").strip().lower()
        normalized_pack_type = str(pack_type or "").strip().lower()
        normalized_risk = str(risk_level or "").strip().lower()
        normalized_review_label = str(review_label or "").strip().lower()
        normalized_warning_flag = str(warning_flag or "").strip().lower()

        rows = []
        for item in self.profile_pack_service.list_submissions(status=status):
            if str(item.user_id or "").strip() != normalized_user_id:
                continue
            if query and query not in item.pack_id.lower():
                continue
            if normalized_pack_type and item.pack_type.lower() != normalized_pack_type:
                continue
            if normalized_risk and item.risk_level.lower() != normalized_risk:
                continue
            if not self._matches_metadata_filters(
                review_labels=item.review_labels,
                warning_flags=item.warning_flags,
                review_label=normalized_review_label,
                warning_flag=normalized_warning_flag,
            ):
                continue
            rows.append(self._profile_pack_submission_payload(item))
        return {"user_id": normalized_user_id, "submissions": rows}

    def member_withdraw_profile_pack_submission(
        self,
        user_id: str,
        submission_id: str,
    ) -> dict:
        if self.profile_pack_service is None:
            return {"error": "profile_pack_service_unavailable", "submission_id": submission_id}
        normalized_user_id = str(user_id or "").strip() or "webui-user"
        normalized_submission_id = str(submission_id or "").strip()
        if not normalized_submission_id:
            return {"error": "submission_id_required"}
        try:
            submission = self.profile_pack_service.withdraw_submission(
                user_id=normalized_user_id,
                submission_id=normalized_submission_id,
            )
        except ValueError as exc:
            return self._profile_pack_error_payload(exc=exc, fallback_id=normalized_submission_id)
        self._audit(
            action="profile_pack.submission_withdrawn",
            actor_id=normalized_user_id,
            actor_role="member",
            target_id=submission.submission_id,
            status=submission.status,
            detail={
                "pack_id": submission.pack_id,
                "version": submission.version,
            },
        )
        return self._profile_pack_submission_payload(submission)

    def member_get_profile_pack_submission_detail(
        self,
        user_id: str,
        submission_id: str,
    ) -> dict:
        if self.profile_pack_service is None:
            return {"error": "profile_pack_service_unavailable", "submission_id": submission_id}
        normalized_user_id = str(user_id or "").strip() or "webui-user"
        normalized_submission_id = str(submission_id or "").strip()
        if not normalized_submission_id:
            return {"error": "submission_id_required"}
        try:
            submission = self.profile_pack_service.get_submission(submission_id=normalized_submission_id)
        except ValueError:
            return {"error": "profile_pack_submission_not_found", "submission_id": normalized_submission_id}
        if str(submission.user_id or "").strip() != normalized_user_id:
            return {"error": "permission_denied", "submission_id": normalized_submission_id}
        return self._profile_pack_submission_payload(submission)

    def member_get_profile_pack_submission_export(
        self,
        user_id: str,
        submission_id: str,
    ) -> dict:
        if self.profile_pack_service is None:
            return {"error": "profile_pack_service_unavailable", "submission_id": submission_id}
        normalized_user_id = str(user_id or "").strip() or "webui-user"
        normalized_submission_id = str(submission_id or "").strip()
        if not normalized_submission_id:
            return {"error": "submission_id_required"}
        try:
            submission = self.profile_pack_service.get_submission(submission_id=normalized_submission_id)
        except ValueError:
            return {"error": "profile_pack_submission_not_found", "submission_id": normalized_submission_id}
        if str(submission.user_id or "").strip() != normalized_user_id:
            return {"error": "permission_denied", "submission_id": normalized_submission_id}
        artifact_id = str(submission.artifact_id or "").strip()
        if not artifact_id:
            return {"error": "profile_pack_not_found", "artifact_id": normalized_submission_id}
        try:
            artifact = self.profile_pack_service.get_export_artifact(artifact_id=artifact_id)
        except ValueError as exc:
            return self._profile_pack_error_payload(exc=exc, fallback_id=artifact_id)
        return {
            "submission_id": normalized_submission_id,
            "artifact_id": artifact.artifact_id,
            "pack_type": artifact.manifest.pack_type,
            "pack_id": artifact.pack_id,
            "version": artifact.version,
            "exported_at": artifact.exported_at,
            "path": str(artifact.path),
            "filename": artifact.filename,
            "sha256": artifact.sha256,
            "size_bytes": artifact.size_bytes,
        }

    def admin_decide_profile_pack_submission(
        self,
        role: str,
        submission_id: str,
        decision: str,
        review_note: str = "",
        review_labels: list[str] | None = None,
        reviewer_id: str = "",
    ) -> dict:
        if not self._is_reviewer_role(role):
            return {"error": "permission_denied", "submission_id": submission_id}
        if self.profile_pack_service is None:
            return {"error": "profile_pack_service_unavailable", "submission_id": submission_id}
        actor_id, actor_role = self._reviewer_actor(role=role, reviewer_id=reviewer_id)
        try:
            submission = self.profile_pack_service.decide_submission(
                submission_id=submission_id,
                reviewer_id=actor_id,
                decision=decision,
                review_note=review_note,
                review_labels=review_labels,
            )
        except ValueError as exc:
            return self._profile_pack_error_payload(exc=exc, fallback_id=submission_id)
        self._audit(
            action="profile_pack.submission_decided",
            actor_id=actor_id,
            actor_role=actor_role,
            target_id=submission.submission_id,
            status=submission.status,
            detail={"pack_id": submission.pack_id, "version": submission.version},
        )
        payload = self._profile_pack_submission_payload(submission)
        publish_result = self._auto_publish_profile_pack_submission(
            submission=submission,
            actor_id=actor_id,
            actor_role=actor_role,
        )
        if publish_result:
            payload["public_market_publish"] = publish_result
        return payload

    def admin_set_profile_pack_featured(
        self,
        role: str,
        pack_id: str,
        featured: bool,
        note: str = "",
    ) -> dict:
        if role != "admin":
            return {"error": "permission_denied", "pack_id": pack_id}
        if self.profile_pack_service is None:
            return {"error": "profile_pack_service_unavailable", "pack_id": pack_id}
        try:
            published = self.profile_pack_service.set_published_featured(
                pack_id=pack_id,
                reviewer_id="admin",
                featured=bool(featured),
                note=note,
            )
        except ValueError as exc:
            return self._profile_pack_error_payload(exc=exc, fallback_id=pack_id)
        self._audit(
            action="profile_pack.featured_updated",
            actor_id="admin",
            actor_role="admin",
            target_id=published.pack_id,
            status="featured" if published.featured else "normal",
            detail={"featured": published.featured, "featured_note": published.featured_note},
        )
        return self._profile_pack_published_payload(published, detail=True)

    def list_profile_pack_catalog(
        self,
        pack_query: str = "",
        pack_type: str = "",
        risk_level: str = "",
        review_label: str = "",
        warning_flag: str = "",
        featured: str = "",
    ) -> dict:
        if self.profile_pack_service is None:
            return {"error": "profile_pack_service_unavailable"}
        rows = self._filtered_profile_pack_catalog_rows(
            pack_query=pack_query,
            pack_type=pack_type,
            risk_level=risk_level,
            review_label=review_label,
            warning_flag=warning_flag,
            featured=featured,
        )
        return {"packs": rows}

    def list_profile_pack_catalog_insights(
        self,
        pack_query: str = "",
        pack_type: str = "",
        risk_level: str = "",
        review_label: str = "",
        warning_flag: str = "",
        featured: str = "",
    ) -> dict:
        if self.profile_pack_service is None:
            return {"error": "profile_pack_service_unavailable"}

        rows = self._filtered_profile_pack_catalog_rows(
            pack_query=pack_query,
            pack_type=pack_type,
            risk_level=risk_level,
            review_label=review_label,
            warning_flag=warning_flag,
            featured=featured,
        )
        ranked = self._rank_profile_pack_catalog_rows(rows)
        featured_row = next((item for item in ranked if bool(item.get("featured"))), None)
        if featured_row is None and ranked:
            featured_row = ranked[0]
        metrics = self._profile_pack_catalog_metrics(rows)
        return {
            "metrics": metrics,
            "featured": dict(featured_row) if featured_row is not None else None,
            "trending": [dict(item) for item in ranked[:6]],
            "total": int(metrics.get("total", 0) or 0),
        }

    def get_profile_pack_catalog_detail(self, pack_id: str) -> dict:
        if self.profile_pack_service is None:
            return {"error": "profile_pack_service_unavailable", "pack_id": pack_id}
        normalized_pack_id = str(pack_id or "").strip()
        if not normalized_pack_id:
            return {"error": "pack_id_required"}
        published = self.profile_pack_service.get_published_pack(pack_id=normalized_pack_id)
        if published is None:
            return {"error": "profile_pack_not_published", "pack_id": normalized_pack_id}
        return self._profile_pack_published_payload(published, detail=True)

    def compare_profile_pack_catalog(
        self,
        *,
        pack_id: str,
        selected_sections: list[str] | None = None,
    ) -> dict:
        if self.profile_pack_service is None:
            return {"error": "profile_pack_service_unavailable", "pack_id": pack_id}
        normalized_pack_id = str(pack_id or "").strip()
        if not normalized_pack_id:
            return {"error": "pack_id_required"}
        try:
            return self.profile_pack_service.preview_published_pack_compare(
                pack_id=normalized_pack_id,
                selected_sections=selected_sections,
            )
        except ValueError as exc:
            return self._profile_pack_error_payload(exc=exc, fallback_id=normalized_pack_id)

    def admin_list_submissions(
        self,
        role: str,
        status: str = "",
        template_query: str = "",
        risk_level: str = "",
        review_label: str = "",
        warning_flag: str = "",
    ) -> dict:
        if not self._is_reviewer_role(role):
            return {"error": "permission_denied"}

        filter_status = status.strip().lower() or None
        query = template_query.strip().lower()
        normalized_risk = risk_level.strip().lower()
        normalized_review_label = review_label.strip().lower()
        normalized_warning_flag = warning_flag.strip().lower()
        submissions = []
        for item in self.market_service.list_submissions(status=filter_status):
            if query and query not in item.template_id.lower():
                continue
            if normalized_risk and item.risk_level.lower() != normalized_risk:
                continue
            if not self._matches_metadata_filters(
                review_labels=item.review_labels or [],
                warning_flags=item.warning_flags or [],
                review_label=normalized_review_label,
                warning_flag=normalized_warning_flag,
            ):
                continue
            submissions.append(self._submission_payload(item))
        return {"submissions": submissions}

    def member_list_submissions(
        self,
        user_id: str,
        status: str = "",
        template_query: str = "",
        risk_level: str = "",
        review_label: str = "",
        warning_flag: str = "",
    ) -> dict:
        normalized_user_id = str(user_id or "").strip() or "webui-user"
        filter_status = status.strip().lower() or None
        query = template_query.strip().lower()
        normalized_risk = risk_level.strip().lower()
        normalized_review_label = review_label.strip().lower()
        normalized_warning_flag = warning_flag.strip().lower()
        submissions = []
        for item in self.market_service.list_submissions(status=filter_status):
            if str(item.user_id or "").strip() != normalized_user_id:
                continue
            if query and query not in item.template_id.lower():
                continue
            if normalized_risk and item.risk_level.lower() != normalized_risk:
                continue
            if not self._matches_metadata_filters(
                review_labels=item.review_labels or [],
                warning_flags=item.warning_flags or [],
                review_label=normalized_review_label,
                warning_flag=normalized_warning_flag,
            ):
                continue
            submissions.append(self._submission_payload(item))
        return {"user_id": normalized_user_id, "submissions": submissions}

    def member_get_submission_detail(self, user_id: str, submission_id: str) -> dict:
        normalized_user_id = str(user_id or "").strip() or "webui-user"
        normalized_submission_id = str(submission_id or "").strip()
        if not normalized_submission_id:
            return {"error": "submission_id_required"}
        try:
            submission = self.market_service.get_submission(submission_id=normalized_submission_id)
        except KeyError:
            return {"error": "submission_not_found", "submission_id": normalized_submission_id}
        if str(submission.user_id or "").strip() != normalized_user_id:
            return {"error": "permission_denied", "submission_id": normalized_submission_id}
        return self._submission_detail_payload(submission)

    def member_get_submission_package(
        self,
        user_id: str,
        submission_id: str,
        idempotency_key: str = "",
    ) -> dict:
        normalized_user_id = str(user_id or "").strip() or "webui-user"
        normalized_submission_id = str(submission_id or "").strip()
        normalized_idempotency_key = self._normalize_idempotency_key(idempotency_key)
        transfer_claim = self._claim_transfer_job(
            direction="download",
            job_type="member_submission_package",
            actor_id=normalized_user_id,
            actor_role="member",
            user_id=normalized_user_id,
            logical_key=(
                f"download:{normalized_user_id}:submission:{normalized_submission_id}:{normalized_idempotency_key}"
                if normalized_idempotency_key
                else self._new_transfer_logical_key(
                    f"download:{normalized_user_id}:submission:{normalized_submission_id}"
                )
            ),
            submission_id=normalized_submission_id,
            idempotency_key=normalized_idempotency_key,
            max_attempts=2,
        )
        if transfer_claim is not None and transfer_claim.should_execute:
            self.transfer_job_service.mark_running(transfer_claim.job.job_id)
        if not normalized_submission_id:
            payload = {"error": "submission_id_required"}
            if transfer_claim is not None:
                self.transfer_job_service.mark_failed(
                    transfer_claim.job.job_id,
                    failure_reason="validation_failed",
                    failure_detail="submission_id is required",
                )
                self._attach_transfer_job(payload, self.transfer_job_service.get(transfer_claim.job.job_id))
            return payload
        if self.package_service is None:
            payload = {"error": "package_service_unavailable", "submission_id": normalized_submission_id}
            if transfer_claim is not None:
                self.transfer_job_service.mark_failed(
                    transfer_claim.job.job_id,
                    failure_reason="service_unavailable",
                    failure_detail="package service unavailable",
                    submission_id=normalized_submission_id,
                )
                self._attach_transfer_job(payload, self.transfer_job_service.get(transfer_claim.job.job_id))
            return payload
        try:
            submission = self.market_service.get_submission(submission_id=normalized_submission_id)
        except KeyError:
            payload = {"error": "submission_not_found", "submission_id": normalized_submission_id}
            if transfer_claim is not None:
                self.transfer_job_service.mark_failed(
                    transfer_claim.job.job_id,
                    failure_reason="not_found",
                    failure_detail="submission not found",
                    submission_id=normalized_submission_id,
                )
                self._attach_transfer_job(payload, self.transfer_job_service.get(transfer_claim.job.job_id))
            return payload
        if str(submission.user_id or "").strip() != normalized_user_id:
            payload = {"error": "permission_denied", "submission_id": normalized_submission_id}
            if transfer_claim is not None:
                self.transfer_job_service.mark_failed(
                    transfer_claim.job.job_id,
                    failure_reason="permission_denied",
                    failure_detail="submission does not belong to current member",
                    submission_id=normalized_submission_id,
                )
                self._attach_transfer_job(payload, self.transfer_job_service.get(transfer_claim.job.job_id))
            return payload
        try:
            artifact = self.package_service.get_submission_package_artifact(submission_id=normalized_submission_id)
        except ValueError:
            payload = {"error": "submission_package_not_available", "submission_id": normalized_submission_id}
            if transfer_claim is not None:
                self.transfer_job_service.mark_failed(
                    transfer_claim.job.job_id,
                    failure_reason="artifact_missing",
                    failure_detail="submission package missing",
                    submission_id=normalized_submission_id,
                )
                self._attach_transfer_job(payload, self.transfer_job_service.get(transfer_claim.job.job_id))
            return payload
        payload = {
            "submission_id": normalized_submission_id,
            "template_id": artifact.template_id,
            "version": artifact.version,
            "path": str(artifact.path),
            "sha256": artifact.sha256,
            "filename": artifact.filename,
            "source": artifact.source,
            "size_bytes": artifact.size_bytes,
        }
        if transfer_claim is not None:
            self.transfer_job_service.mark_done(
                transfer_claim.job.job_id,
                template_id=artifact.template_id,
                submission_id=normalized_submission_id,
                filename=artifact.filename,
                size_bytes=artifact.size_bytes,
                sha256=artifact.sha256,
            )
            self._attach_transfer_job(payload, self.transfer_job_service.get(transfer_claim.job.job_id))
        return payload

    def admin_get_submission_detail(self, role: str, submission_id: str) -> dict:
        if not self._is_reviewer_role(role):
            return {"error": "permission_denied"}
        try:
            submission = self.market_service.get_submission(submission_id=submission_id)
        except KeyError:
            return {"error": "submission_not_found", "submission_id": submission_id}
        return self._submission_detail_payload(submission)

    def admin_update_submission_review(
        self,
        role: str,
        submission_id: str,
        review_note: str = "",
        review_labels: list[str] | None = None,
        reviewer_id: str = "",
    ) -> dict:
        if not self._is_reviewer_role(role):
            return {"error": "permission_denied", "submission_id": submission_id}
        actor_id, actor_role = self._reviewer_actor(role=role, reviewer_id=reviewer_id)

        record = self.market_service.update_submission_review(
            submission_id=submission_id,
            reviewer_id=actor_id,
            review_note=review_note,
            review_labels=review_labels,
        )
        self._audit(
            action="submission.review_updated",
            actor_id=actor_id,
            actor_role=actor_role,
            target_id=submission_id,
            status=record.status,
            detail={"template_id": record.template_id, "review_labels": list(record.review_labels or [])},
        )
        return self._submission_payload(record)

    def admin_get_submission_package(self, role: str, submission_id: str) -> dict:
        if not self._is_reviewer_role(role):
            return {"error": "permission_denied", "submission_id": submission_id}
        if self.package_service is None:
            return {"error": "package_service_unavailable", "submission_id": submission_id}
        try:
            artifact = self.package_service.get_submission_package_artifact(submission_id=submission_id)
        except ValueError:
            return {"error": "submission_package_not_available", "submission_id": submission_id}
        return {
            "submission_id": submission_id,
            "template_id": artifact.template_id,
            "version": artifact.version,
            "path": str(artifact.path),
            "sha256": artifact.sha256,
            "filename": artifact.filename,
            "source": artifact.source,
            "size_bytes": artifact.size_bytes,
        }

    def admin_compare_submission(self, role: str, submission_id: str) -> dict:
        if not self._is_reviewer_role(role):
            return {"error": "permission_denied", "submission_id": submission_id}
        submission = self.market_service.get_submission(submission_id=submission_id)
        published = self.market_service.get_published_template(template_id=submission.template_id)

        submission_labels = list(submission.review_labels or [])
        published_labels = list(published.review_labels or []) if published else []
        return {
            "submission": self._submission_payload(submission),
            "published_template": self._published_payload(published) if published else None,
            "comparison": {
                "status": "baseline_available" if published else "no_baseline",
                "version_changed": bool(published and published.version != submission.version),
                "risk_level_changed": bool(published and published.risk_level != submission.risk_level),
                "review_labels_added": [item for item in submission_labels if item not in published_labels],
                "review_labels_removed": [item for item in published_labels if item not in submission_labels],
                "has_submission_package": bool(submission.package_artifact),
                "has_published_package": bool(published and published.package_artifact),
            },
            "details": {
                "version": self._compare_scalar(
                    submission.version,
                    published.version if published else None,
                ),
                "risk_level": self._compare_scalar(
                    submission.risk_level,
                    published.risk_level if published else None,
                ),
                "review_note": self._compare_scalar(
                    submission.review_note,
                    published.review_note if published else None,
                ),
                "prompt": self._compare_prompt(
                    submission.prompt_template,
                    published.prompt_template if published else None,
                ),
                "review_labels": self._compare_list(
                    submission.review_labels or [],
                    published.review_labels if published else [],
                ),
                "warning_flags": self._compare_list(
                    submission.warning_flags or [],
                    published.warning_flags if published else [],
                ),
                "package": self._compare_package(
                    submission.package_artifact,
                    published.package_artifact if published else None,
                ),
                "scan": self._compare_scan(
                    submission.scan_summary or {},
                    published.scan_summary if published else {},
                ),
            },
        }

    def admin_decide_submission(
        self,
        role: str,
        submission_id: str,
        decision: str,
        review_note: str = "",
        review_labels: list[str] | None = None,
        reviewer_id: str = "",
    ) -> dict:
        if not self._is_reviewer_role(role):
            return {"error": "permission_denied", "submission_id": submission_id}
        actor_id, actor_role = self._reviewer_actor(role=role, reviewer_id=reviewer_id)

        record = self.market_service.decide_submission(
            submission_id=submission_id,
            reviewer_id=actor_id,
            decision=decision,
            review_note=review_note,
            review_labels=review_labels,
        )
        self._audit(
            action="submission.decided",
            actor_id=actor_id,
            actor_role=actor_role,
            target_id=submission_id,
            status=record.status,
            detail={"template_id": record.template_id},
        )
        return {
            "submission_id": record.id,
            "status": record.status,
            "template_id": record.template_id,
            "risk_level": record.risk_level,
            "review_note": record.review_note,
            "review_labels": list(record.review_labels or []),
            "warning_flags": list(record.warning_flags or []),
            "scan_summary": record.scan_summary or {},
        }

    def admin_list_retry_requests(self, role: str) -> dict:
        if role != "admin":
            return {"error": "permission_denied"}
        requests = [asdict(item) for item in self.retry_queue_service.list_requests()]
        return {"requests": requests}

    def admin_acquire_retry_lock(
        self,
        role: str,
        request_id: str,
        admin_id: str,
        force: bool = False,
        reason: str = "",
    ) -> dict:
        if role != "admin":
            return {"error": "permission_denied", "request_id": request_id}
        try:
            lock = self.retry_queue_service.acquire_lock(
                request_id=request_id,
                admin_id=admin_id,
                force=force,
                reason=reason,
            )
        except PermissionError:
            return {"error": "review_lock_held", "request_id": request_id}
        except ValueError as exc:
            if "TAKEOVER_REASON_REQUIRED" in str(exc):
                return {"error": "takeover_reason_required", "request_id": request_id}
            raise
        self._audit(
            action="retry.lock_acquired",
            actor_id=admin_id,
            actor_role="admin",
            target_id=request_id,
            status="locked",
            detail={"lock_version": lock.lock_version, "force": force},
        )
        return {
            "request_id": lock.request_id,
            "holder_id": lock.holder_id,
            "lock_version": lock.lock_version,
            "expires_at": lock.expires_at.isoformat(),
        }

    def admin_decide_retry_request(
        self,
        role: str,
        request_id: str,
        decision: str,
        admin_id: str | None = None,
        request_version: int | None = None,
        lock_version: int | None = None,
    ) -> dict:
        if role != "admin":
            return {"error": "permission_denied", "request_id": request_id}
        try:
            req = self.retry_queue_service.decide(
                request_id=request_id,
                decision=decision,
                admin_id=admin_id,
                request_version=request_version,
                lock_version=lock_version,
            )
        except PermissionError as exc:
            code = str(exc)
            if "LOCK_VERSION_CONFLICT" in code:
                return {"error": "lock_version_conflict", "request_id": request_id}
            if "REVIEW_LOCK_NOT_OWNER" in code:
                return {"error": "review_lock_not_owner", "request_id": request_id}
            if "REVIEW_LOCK_REQUIRED" in code:
                return {"error": "review_lock_required", "request_id": request_id}
            raise
        except ValueError as exc:
            code = str(exc)
            if "REQUEST_VERSION_CONFLICT" in code:
                return {"error": "request_version_conflict", "request_id": request_id}
            if "INVALID_RETRY_DECISION" in code:
                return {"error": "invalid_retry_decision", "request_id": request_id}
            raise
        self._audit(
            action="retry.decided",
            actor_id=admin_id or "admin",
            actor_role="admin",
            target_id=request_id,
            status=req.state,
            detail={"template_id": req.template_id},
        )
        return {"request_id": req.id, "state": req.state, "template_id": req.template_id}

    def admin_dryrun(self, role: str, plan_id: str, patch: dict) -> dict:
        if role != "admin":
            return {"error": "permission_denied", "plan_id": plan_id}
        selected_sections = sorted({str(key or "").strip() for key in patch.keys() if str(key or "").strip()})
        plan = self.apply_service.register_plan(
            plan_id=plan_id,
            patch=patch,
            metadata={
                "actor_id": "admin",
                "actor_role": "admin",
                "source_id": plan_id,
                "source_kind": "manual_patch",
                "selected_sections": selected_sections,
                "recovery_class": "config_snapshot_restore",
            },
        )
        self._audit(
            action="apply.dryrun_prepared",
            actor_id="admin",
            actor_role="admin",
            target_id=plan_id,
            status="dryrun_ready",
            detail={"patch": plan.patch},
        )
        return {"plan_id": plan.plan_id, "status": "dryrun_ready", "patch": plan.patch}

    def admin_apply(self, role: str, plan_id: str) -> dict:
        if role != "admin":
            return {"error": "permission_denied", "plan_id": plan_id}
        try:
            continuity = self.apply_service.apply(plan_id=plan_id)
        except ValueError as exc:
            return self._apply_error_payload(plan_id=plan_id, exc=exc)
        self._audit(
            action="apply.executed",
            actor_id="admin",
            actor_role="admin",
            target_id=plan_id,
            status="applied",
            detail={"continuity": continuity},
        )
        payload = {"plan_id": plan_id, "status": "applied"}
        if continuity:
            payload["continuity"] = continuity
        return payload

    def admin_rollback(self, role: str, plan_id: str) -> dict:
        if role != "admin":
            return {"error": "permission_denied", "plan_id": plan_id}
        try:
            continuity = self.apply_service.rollback(plan_id=plan_id)
        except ValueError as exc:
            return self._apply_error_payload(plan_id=plan_id, exc=exc)
        self._audit(
            action="apply.rolled_back",
            actor_id="admin",
            actor_role="admin",
            target_id=plan_id,
            status="rolled_back",
            detail={"continuity": continuity},
        )
        payload = {"plan_id": plan_id, "status": "rolled_back"}
        if continuity:
            payload["continuity"] = continuity
        return payload

    def admin_run_pipeline(
        self,
        role: str,
        contract: dict,
        input_payload: object,
        actor_id: str = "admin",
        run_id: str = "",
    ) -> dict:
        if role != "admin":
            return {"error": "permission_denied", "run_id": run_id}
        if self.pipeline_orchestrator is None:
            return {"error": "pipeline_service_unavailable", "run_id": run_id}
        if not isinstance(contract, dict):
            return {"error": "invalid_pipeline_contract", "run_id": run_id}

        result = self.pipeline_orchestrator.execute(
            contract=contract,
            input_payload=input_payload,
            actor_id=actor_id or "admin",
            actor_role=role,
            run_id=run_id,
        )
        status = str(result.get("status", "") or "")
        if status == "invalid_contract":
            return {"error": "invalid_pipeline_contract", "run_id": run_id, "detail": result}
        if status == "failed":
            self._audit(
                action="pipeline.run",
                actor_id=actor_id or "admin",
                actor_role=role,
                target_id=run_id or "pipeline-run",
                status="failed",
                detail={
                    "steps_failed": result.get("steps_failed"),
                    "steps_total": result.get("steps_total"),
                    "trace": result.get("trace"),
                },
            )
            return {"error": "pipeline_execution_failed", "run_id": run_id, "detail": result}

        self._audit(
            action="pipeline.run",
            actor_id=actor_id or "admin",
            actor_role=role,
            target_id=run_id or "pipeline-run",
            status="completed",
            detail={
                "steps_executed": result.get("steps_executed"),
                "steps_total": result.get("steps_total"),
            },
        )
        return result

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
    ) -> dict:
        if role != "admin":
            return {"error": "permission_denied"}
        normalized_limit = max(1, min(int(limit or 100), 200))
        normalized_action_prefix = str(action_prefix or "").strip()
        normalized_reviewer_id = str(reviewer_id or "").strip()
        normalized_device_id = str(device_id or "").strip()
        normalized_lifecycle_only = bool(lifecycle_only)
        normalized_inspect_limit = max(
            normalized_limit,
            min(max(int(inspect_limit or 1000), normalized_limit), 2000),
        )

        inspected_events = self.audit_service.list_events(limit=normalized_inspect_limit)
        filtered_events = self._filter_audit_events(
            inspected_events,
            action_prefix=normalized_action_prefix,
            reviewer_id=normalized_reviewer_id,
            device_id=normalized_device_id,
            lifecycle_only=normalized_lifecycle_only,
        )
        selected_events = filtered_events[-normalized_limit:]
        events = [
            {
                "id": item.id,
                "action": item.action,
                "actor_id": item.actor_id,
                "actor_role": item.actor_role,
                "target_id": item.target_id,
                "status": item.status,
                "detail": item.detail,
                "created_at": item.created_at.isoformat(),
            }
            for item in selected_events
        ]
        return {
            "events": events,
            "summary": self.audit_service.summarize_rows(selected_events),
            "filters": {
                "action_prefix": normalized_action_prefix,
                "reviewer_id": normalized_reviewer_id,
                "device_id": normalized_device_id,
                "lifecycle_only": normalized_lifecycle_only,
                "inspect_limit": normalized_inspect_limit,
            },
        }

    def _request_trial_with_preference(
        self,
        user_id: str,
        session_id: str,
        template_id: str,
    ) -> dict[str, object]:
        pref = self.preference_service.get(user_id=user_id)
        if pref.execution_mode == "inline_execution":
            status = self.trial_request_service.trial_service.get_status(
                user_id=user_id,
                session_id=session_id,
                template_id=template_id,
            )
            if status.get("status") == "active":
                payload: dict[str, object] = {
                    "status": "trial_already_active",
                    "trial_id": status.get("trial_id"),
                    "retry_request_id": None,
                }
            else:
                started = self.trial_request_service.request_trial(
                    user_id=user_id,
                    session_id=session_id,
                    template_id=template_id,
                )
                payload = {
                    "status": started.status,
                    "trial_id": started.trial_id,
                    "retry_request_id": started.retry_request_id,
                }
        else:
            started = self.trial_request_service.request_trial(
                user_id=user_id,
                session_id=session_id,
                template_id=template_id,
            )
            payload = {
                "status": started.status,
                "trial_id": started.trial_id,
                "retry_request_id": started.retry_request_id,
            }
        payload["execution_mode"] = pref.execution_mode
        payload["observe_task_details"] = pref.observe_task_details
        if pref.observe_task_details:
            payload["task_details"] = {
                "event": "trial.request",
                "template_id": template_id,
                "session_id": session_id,
                "execution_mode": pref.execution_mode,
                "status": payload.get("status", "unknown"),
            }
        return payload

    def _audit(
        self,
        action: str,
        actor_id: str,
        actor_role: str,
        target_id: str,
        status: str,
        detail: dict | None,
    ) -> None:
        self.audit_service.record(
            action=action,
            actor_id=actor_id,
            actor_role=actor_role,
            target_id=target_id,
            status=status,
            detail=detail or {},
        )

    @staticmethod
    def _audit_event_detail(event: Any) -> dict[str, Any]:
        detail = getattr(event, "detail", {})
        return detail if isinstance(detail, dict) else {}

    @classmethod
    def _audit_event_reviewer_id(cls, event: Any) -> str:
        detail = cls._audit_event_detail(event)
        reviewer_id = str(detail.get("reviewer_id", "") or "").strip()
        if reviewer_id:
            return reviewer_id
        if cls._normalize_role(str(getattr(event, "actor_role", "") or "")) == "reviewer":
            return str(getattr(event, "actor_id", "") or "").strip()
        return ""

    @classmethod
    def _audit_event_device_id(cls, event: Any) -> str:
        detail = cls._audit_event_detail(event)
        device_id = str(detail.get("device_id", "") or "").strip()
        if device_id:
            return device_id
        action = str(getattr(event, "action", "") or "").strip()
        if action in {"reviewer.device_registered", "reviewer.device_revoked"}:
            return str(getattr(event, "target_id", "") or "").strip()
        return ""

    @classmethod
    def _filter_audit_events(
        cls,
        events: list[Any],
        *,
        action_prefix: str = "",
        reviewer_id: str = "",
        device_id: str = "",
        lifecycle_only: bool = False,
    ) -> list[Any]:
        normalized_prefix = str(action_prefix or "").strip()
        normalized_reviewer_id = str(reviewer_id or "").strip()
        normalized_device_id = str(device_id or "").strip()
        filtered: list[Any] = []
        for event in events:
            action = str(getattr(event, "action", "") or "").strip()
            if normalized_prefix and not action.startswith(normalized_prefix):
                continue
            if lifecycle_only and action not in cls._REVIEWER_LIFECYCLE_ACTIONS:
                continue
            if normalized_reviewer_id and cls._audit_event_reviewer_id(event) != normalized_reviewer_id:
                continue
            if normalized_device_id and cls._audit_event_device_id(event) != normalized_device_id:
                continue
            filtered.append(event)
        return filtered

    @classmethod
    def _normalize_install_options(cls, install_options: dict | None) -> dict:
        return normalize_install_option_contract(install_options)

    @classmethod
    def _normalize_upload_options(cls, upload_options: dict | None) -> dict:
        return normalize_upload_option_contract(
            upload_options,
            normalize_idempotency_key=cls._normalize_idempotency_key,
        )

    @classmethod
    def _normalize_profile_pack_submit_options(cls, submit_options: dict | None) -> dict:
        return normalize_profile_pack_submit_option_contract(
            submit_options,
            normalize_idempotency_key=cls._normalize_idempotency_key,
        )

    def _member_installations_payload(self, user_id: str, limit: int) -> list[dict]:
        normalized_user_id = str(user_id or "").strip() or "webui-user"
        inspected_limit = max(200, limit * 20)
        latest_by_template: dict[str, tuple[str, Any]] = {}
        for event in self.audit_service.list_events(limit=inspected_limit):
            action = str(event.action or "").strip()
            if action not in {"template.installed", "template.uninstalled"}:
                continue
            if str(event.actor_id or "") != normalized_user_id:
                continue
            template_id = str(event.target_id or "").strip()
            if not template_id:
                continue
            previous = latest_by_template.get(template_id)
            if previous is not None and previous[1].created_at > event.created_at:
                continue
            latest_by_template[template_id] = (action, event)
        rows = []
        for template_id, (action, event) in latest_by_template.items():
            if action != "template.installed":
                continue
            published = self.market_service.get_published_template(template_id=template_id)
            detail = event.detail if isinstance(event.detail, dict) else {}
            row = {
                "template_id": template_id,
                "status": str(event.status or "unknown"),
                "installed_at": event.created_at.isoformat(),
                "execution_mode": str(detail.get("execution_mode", "") or ""),
                "observe_task_details": bool(detail.get("observe_task_details", False)),
                "install_options": self._normalize_install_options(
                    detail.get("install_options") if isinstance(detail.get("install_options"), dict) else None
                ),
                "version": str(getattr(published, "version", "") or ""),
                "risk_level": str(getattr(published, "risk_level", "") or ""),
                "review_labels": list(getattr(published, "review_labels", []) or []),
                "warning_flags": list(getattr(published, "warning_flags", []) or []),
                "source_channel": str(getattr(published, "source_channel", "") or ""),
                "maintainer": str(getattr(published, "maintainer", "") or ""),
                "engagement": self._engagement_payload(published, self.market_service) if published else {},
            }
            rows.append(row)
        rows = sorted(
            rows,
            key=lambda item: str(item.get("installed_at", "")),
            reverse=True,
        )
        return rows[:limit]

    @classmethod
    def _member_task_display_name(cls, action: str) -> str:
        value = str(action or "").strip()
        if not value:
            return "operation"
        if value == "trial.requested":
            return "trial"
        if value in {"template.installed", "template.uninstalled"}:
            return "install"
        if value in {"submission.created", "submission.package_uploaded", "submission.pending_replaced"}:
            return "submit_template"
        if value.startswith("submission.idempotency_"):
            return "submit_template"
        if value.startswith("member.installations."):
            return "member_installations_refresh"
        if value.startswith("profile_pack.submission"):
            return "profile_pack_submit"
        if value.startswith("profile_pack."):
            return "profile_pack_operation"
        return value.replace(".", "_")

    def _member_tasks_payload(self, user_id: str, limit: int) -> list[dict]:
        normalized_user_id = str(user_id or "").strip() or "webui-user"
        inspected_limit = max(200, limit * 40)
        rows: list[dict] = []
        for event in reversed(self.audit_service.list_events(limit=inspected_limit)):
            action = str(event.action or "").strip()
            if action not in self._MEMBER_TASK_ACTIONS:
                continue
            if str(event.actor_id or "").strip() != normalized_user_id:
                continue
            if self._normalize_role(str(event.actor_role or "")) != "member":
                continue
            detail = event.detail if isinstance(event.detail, dict) else {}
            template_id = str(detail.get("template_id", "") or "").strip()
            if not template_id and action.startswith("template."):
                template_id = str(event.target_id or "").strip()
            pack_id = str(detail.get("pack_id", "") or "").strip()
            normalized_status = str(event.status or "").strip().lower()
            ok = (
                normalized_status not in self._MEMBER_TASK_ERROR_STATUSES
                and not action.endswith("idempotency_conflict")
            )
            summary = str(detail.get("message", "") or "").strip()
            if not summary:
                if template_id:
                    summary = f"{action}: {template_id}"
                elif pack_id:
                    summary = f"{action}: {pack_id}"
                else:
                    summary = action
            rows.append(
                {
                    "task_id": str(event.id or "").strip(),
                    "name": self._member_task_display_name(action),
                    "action": action,
                    "ok": ok,
                    "status": str(event.status or "").strip(),
                    "message": summary,
                    "at": event.created_at.isoformat(),
                    "target_id": str(event.target_id or "").strip(),
                    "template_id": template_id,
                    "pack_id": pack_id,
                }
            )
            if len(rows) >= limit:
                break
        return rows

    @staticmethod
    def _apply_error_payload(plan_id: str, exc: Exception) -> dict:
        code = str(exc)
        if "PLAN_NOT_FOUND" in code:
            return {"error": "plan_not_found", "plan_id": plan_id}
        if "PLAN_NOT_APPLIED" in code:
            return {"error": "plan_not_applied", "plan_id": plan_id}
        raise exc

    @staticmethod
    def _profile_pack_error_payload(exc: Exception, fallback_id: str = "") -> dict:
        code = str(exc)
        if "PROFILE_PACK_NOT_PUBLISHED" in code:
            return {"error": "profile_pack_not_published", "pack_id": fallback_id}
        if "PROFILE_PACK_ARTIFACT_NOT_FOUND" in code:
            return {"error": "profile_pack_not_found", "artifact_id": fallback_id}
        if "PROFILE_PACK_ARTIFACT_PERMISSION_DENIED" in code:
            return {"error": "permission_denied", "artifact_id": fallback_id}
        if "PROFILE_PACK_SUBMISSION_PERMISSION_DENIED" in code:
            return {"error": "permission_denied", "submission_id": fallback_id}
        if "PROFILE_PACK_SUBMISSION_NOT_FOUND" in code:
            return {"error": "profile_pack_submission_not_found", "submission_id": fallback_id}
        if "PROFILE_PACK_SUBMISSION_STATE_INVALID" in code:
            return {"error": "profile_pack_submission_state_invalid", "submission_id": fallback_id}
        if "PROFILE_PACK_BYTES_REQUIRED" in code:
            return {"error": "invalid_profile_pack_payload"}
        if "PROFILE_PACK_INVALID_ARCHIVE" in code:
            return {"error": "invalid_profile_pack_payload"}
        if "PROFILE_PACK_MANIFEST_MISSING" in code:
            return {"error": "invalid_profile_pack_payload"}
        if "PROFILE_PACK_MANIFEST_INVALID" in code:
            return {"error": "invalid_profile_pack_payload"}
        if "PROFILE_PACK_SECTION_MISSING" in code:
            return {"error": "invalid_profile_pack_payload"}
        if "PROFILE_REDACTION_MODE_UNSUPPORTED" in code:
            return {"error": "invalid_redaction_mode"}
        if "PROFILE_PACK_TYPE_UNSUPPORTED" in code:
            return {"error": "invalid_pack_type"}
        if "PROFILE_PACK_ENCRYPTION_KEY_REQUIRED" in code:
            return {"error": "profile_pack_encryption_key_required"}
        if "PROFILE_PACK_SECTION_NOT_ALLOWED_FOR_TYPE" in code:
            return {"error": "invalid_profile_section"}
        if "PROFILE_SECTION_NOT_ALLOWED" in code or "unsupported profile section" in code:
            return {"error": "invalid_profile_section"}
        if "PROFILE_SECTION_SELECTION_EMPTY" in code:
            return {"error": "invalid_profile_section"}
        if "PROFILE_SECTION_ITEM_SELECTION_INVALID" in code:
            return {"error": "invalid_profile_section_path"}
        if "field path must include section prefix" in code:
            return {"error": "invalid_redaction_path"}
        if "PROFILE_IMPORT_NOT_FOUND" in code:
            return {"error": "profile_import_not_found", "import_id": fallback_id}
        if "PROFILE_IMPORT_IN_USE" in code:
            return {"error": "profile_import_in_use", "import_id": fallback_id}
        if "PROFILE_PACK_INCOMPATIBLE" in code:
            return {"error": "profile_pack_incompatible", "import_id": fallback_id}
        if "PROFILE_PACK_PLUGIN_INSTALL_CONFIRM_REQUIRED" in code:
            return {"error": "profile_pack_plugin_install_confirm_required", "import_id": fallback_id}
        if "PROFILE_PACK_PLUGIN_NOT_IN_INSTALL_PLAN" in code:
            return {"error": "profile_pack_plugin_not_in_plan", "import_id": fallback_id}
        if "PROFILE_PACK_PLUGIN_ID_REQUIRED" in code:
            return {"error": "profile_pack_plugin_id_required", "import_id": fallback_id}
        if "PROFILE_PACK_PLUGIN_INSTALL_EXEC_DISABLED" in code:
            return {"error": "profile_pack_plugin_install_exec_disabled", "import_id": fallback_id}
        if "PROFILE_PACK_PLUGIN_INSTALL_EXEC_REQUIRED" in code:
            return {"error": "profile_pack_plugin_install_exec_required", "import_id": fallback_id}
        if "PROFILE_PACK_PLUGIN_INSTALL_EXEC_FAILED" in code:
            return {"error": "profile_pack_plugin_install_exec_failed", "import_id": fallback_id}
        if "INVALID_PROFILE_PACK_SUBMISSION_DECISION" in code:
            return {"error": "invalid_submission_decision", "submission_id": fallback_id}
        raise exc

    def _profile_pack_import_payload(self, imported) -> dict:
        meta = imported.sections.get("sharelife_meta") if isinstance(imported.sections, dict) else None
        astrbot_import = meta.get("astrbot_import") if isinstance(meta, dict) else None
        import_summary = astrbot_import.get("summary") if isinstance(astrbot_import, dict) else {}
        selection_tree = []
        if self.profile_pack_service is not None:
            selection_tree = self.profile_pack_service.build_import_selection_tree(imported)
        return {
            "import_id": imported.import_id,
            "imported_at": imported.imported_at,
            "user_id": imported.user_id,
            "filename": imported.filename,
            "pack_type": imported.manifest.pack_type,
            "pack_id": imported.manifest.pack_id,
            "version": imported.manifest.version,
            "sections": list(imported.manifest.sections),
            "capabilities": list(imported.manifest.capabilities),
            "scan_summary": imported.scan_summary,
            "compatibility": imported.compatibility,
            "compatibility_issues": list(imported.compatibility_issues),
            "source_artifact_id": imported.source_artifact_id,
            "import_origin": imported.import_origin,
            "source_fingerprint": imported.source_fingerprint,
            "import_summary": dict(import_summary) if isinstance(import_summary, dict) else {},
            "selection_tree": selection_tree,
        }

    @staticmethod
    def _profile_pack_submission_payload(submission) -> dict:
        return {
            "id": submission.submission_id,
            "submission_id": submission.submission_id,
            "status": submission.status,
            "user_id": submission.user_id,
            "artifact_id": submission.artifact_id,
            "import_id": submission.import_id,
            "pack_type": submission.pack_type,
            "pack_id": submission.pack_id,
            "version": submission.version,
            "filename": submission.filename,
            "sha256": submission.sha256,
            "size_bytes": submission.size_bytes,
            "sections": list(submission.sections),
            "redaction_mode": submission.redaction_mode,
            "capability_summary": dict(submission.capability_summary),
            "compatibility_matrix": dict(submission.compatibility_matrix),
            "review_evidence": dict(submission.review_evidence),
            "submit_options": dict(submission.submit_options),
            "reviewer_id": submission.reviewer_id,
            "review_note": submission.review_note,
            "review_labels": list(submission.review_labels),
            "warning_flags": list(submission.warning_flags),
            "risk_level": submission.risk_level,
            "scan_summary": submission.scan_summary,
            "compatibility": submission.compatibility,
            "compatibility_issues": list(submission.compatibility_issues),
            "created_at": submission.created_at,
            "updated_at": submission.updated_at,
        }

    @staticmethod
    def _safe_slug(value: str) -> str:
        slug = "".join(char if char.isalnum() else "-" for char in str(value or "").strip().lower())
        slug = "-".join(part for part in slug.split("-") if part)
        return slug or "profile-pack"

    @staticmethod
    def _file_sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def _auto_publish_profile_pack_submission(
        self,
        *,
        submission,
        actor_id: str,
        actor_role: str,
    ) -> dict[str, Any]:
        if not self.public_market_auto_publish_profile_pack_approve:
            return {}
        if self.profile_pack_service is None:
            return {"status": "failed", "error": "profile_pack_service_unavailable"}
        status = str(getattr(submission, "status", "") or "").strip().lower()
        if status != "approved":
            return {"status": "skipped", "reason": "submission_not_approved"}
        redaction_mode = str(getattr(submission, "redaction_mode", "") or "").strip().lower()
        if redaction_mode not in {"exclude_secrets", "masked_secrets"}:
            result = {"status": "failed", "error": "public_market_redaction_not_allowed"}
            self._audit(
                action="profile_pack.public_market.publish",
                actor_id=actor_id,
                actor_role=actor_role,
                target_id=str(getattr(submission, "submission_id", "") or ""),
                status=result["status"],
                detail={
                    "error": result["error"],
                    "pack_id": str(getattr(submission, "pack_id", "") or ""),
                    "version": str(getattr(submission, "version", "") or ""),
                    "redaction_mode": redaction_mode,
                },
            )
            return result
        try:
            artifact = self.profile_pack_service.get_export_artifact(
                artifact_id=str(getattr(submission, "artifact_id", "") or ""),
            )
        except ValueError:
            artifact = None
        if artifact is None or not artifact.path.exists():
            result = {"status": "failed", "error": "profile_pack_not_found"}
            self._audit(
                action="profile_pack.public_market.publish",
                actor_id=actor_id,
                actor_role=actor_role,
                target_id=str(getattr(submission, "submission_id", "") or ""),
                status=result["status"],
                detail={
                    "error": result["error"],
                    "pack_id": str(getattr(submission, "pack_id", "") or ""),
                    "version": str(getattr(submission, "version", "") or ""),
                },
            )
            return result

        pack_id = str(getattr(submission, "pack_id", "") or "").strip()
        version = str(getattr(submission, "version", "") or "").strip()
        package_filename = f"{self._safe_slug(pack_id)}-{self._safe_slug(version)}.zip"
        packages_dir = self.public_market_root / "market" / "packages" / "community"
        entries_dir = self.public_market_root / "market" / "entries"
        packages_dir.mkdir(parents=True, exist_ok=True)
        entries_dir.mkdir(parents=True, exist_ok=True)
        target_package = (packages_dir / package_filename).resolve()
        shutil.copyfile(artifact.path, target_package)
        package_sha256 = self._file_sha256(target_package)
        package_size = int(target_package.stat().st_size)

        risk_level = str(getattr(submission, "risk_level", "low") or "low").strip() or "low"
        review_labels = [str(item or "").strip() for item in list(getattr(submission, "review_labels", []) or []) if str(item or "").strip()]
        warning_flags = [str(item or "").strip() for item in list(getattr(submission, "warning_flags", []) or []) if str(item or "").strip()]
        compatibility_issues = [
            str(item or "").strip()
            for item in list(getattr(submission, "compatibility_issues", []) or [])
            if str(item or "").strip()
        ]
        scan_summary = dict(getattr(submission, "scan_summary", {}) or {})
        compatibility = str(getattr(submission, "compatibility", "") or "compatible").strip() or "compatible"
        review_note = str(getattr(submission, "review_note", "") or "").strip()
        published_at = str(getattr(submission, "updated_at", "") or "").strip()
        source_submission_id = str(getattr(submission, "submission_id", "") or "").strip()
        maintainer = "community"

        entry_payload = {
            "pack_id": pack_id,
            "template_id": pack_id,
            "title": pack_id,
            "description": review_note,
            "version": version,
            "pack_type": str(getattr(submission, "pack_type", "bot_profile_pack") or "bot_profile_pack").strip(),
            "artifact_id": str(getattr(submission, "artifact_id", "") or ""),
            "import_id": str(getattr(submission, "import_id", "") or ""),
            "source_submission_id": source_submission_id,
            "filename": target_package.name,
            "sha256": package_sha256,
            "size_bytes": package_size,
            "sections": [str(item or "").strip() for item in list(getattr(submission, "sections", []) or []) if str(item or "").strip()],
            "redaction_mode": redaction_mode,
            "capability_summary": dict(getattr(submission, "capability_summary", {}) or {}),
            "compatibility_matrix": dict(getattr(submission, "compatibility_matrix", {}) or {}),
            "review_evidence": dict(getattr(submission, "review_evidence", {}) or {}),
            "featured": False,
            "featured_note": "",
            "featured_by": "",
            "featured_at": "",
            "review_note": review_note,
            "review_labels": review_labels,
            "warning_flags": warning_flags,
            "risk_level": risk_level,
            "scan_summary": scan_summary,
            "compatibility": compatibility,
            "compatibility_issues": compatibility_issues,
            "source_channel": "community_submission",
            "maintainer": maintainer,
            "published_at": published_at,
            "engagement": {"installs": 0, "trial_requests": 0},
            "package_path": f"/market/packages/community/{target_package.name}",
            "catalog_origin": "public",
            "runtime_available": False,
        }
        entry_name = f"{self._safe_slug(pack_id)}-{self._safe_slug(version)}.json"
        entry_path = (entries_dir / entry_name).resolve()
        entry_path.write_text(
            json.dumps(entry_payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        snapshot_result: dict[str, Any] = {"status": "skipped", "reason": "snapshot_rebuild_disabled"}
        if self.public_market_rebuild_snapshot_on_publish:
            snapshot_result = self._rebuild_public_market_snapshot()

        result = {
            "status": "succeeded",
            "entry_path": str(entry_path),
            "package_path": str(target_package),
            "entry_id": entry_name,
            "snapshot": snapshot_result,
        }
        self._audit(
            action="profile_pack.public_market.publish",
            actor_id=actor_id,
            actor_role=actor_role,
            target_id=source_submission_id or pack_id,
            status=result["status"],
            detail={
                "pack_id": pack_id,
                "version": version,
                "entry_path": str(entry_path),
                "package_path": str(target_package),
                "snapshot": snapshot_result,
            },
        )
        return result

    def _rebuild_public_market_snapshot(self) -> dict[str, Any]:
        market_dir = self.public_market_root / "market"
        snapshot_path = market_dir / "catalog.snapshot.json"
        entries_dir = market_dir / "entries"
        rows_by_key: dict[tuple[str, str], dict[str, Any]] = {}
        try:
            if snapshot_path.exists():
                previous = json.loads(snapshot_path.read_text(encoding="utf-8"))
                previous_rows = previous.get("rows", []) if isinstance(previous, dict) else []
                if isinstance(previous_rows, list):
                    for item in previous_rows:
                        if not isinstance(item, dict):
                            continue
                        pack_id = str(item.get("pack_id", "") or "").strip()
                        version = str(item.get("version", "") or "").strip()
                        if not pack_id or not version:
                            continue
                        rows_by_key[(pack_id, version)] = dict(item)
            if entries_dir.exists():
                for entry_path in sorted(entries_dir.glob("*.json")):
                    payload = json.loads(entry_path.read_text(encoding="utf-8"))
                    if not isinstance(payload, dict):
                        continue
                    pack_id = str(payload.get("pack_id", "") or "").strip()
                    version = str(payload.get("version", "") or "").strip()
                    package_path = str(payload.get("package_path", "") or "").strip()
                    if not pack_id or not version or not package_path:
                        continue
                    package_file = self.public_market_root / package_path.lstrip("/")
                    if not package_file.exists():
                        continue
                    normalized = dict(payload)
                    normalized["template_id"] = pack_id
                    normalized["filename"] = package_file.name
                    normalized["sha256"] = self._file_sha256(package_file)
                    normalized["size_bytes"] = int(package_file.stat().st_size)
                    rows_by_key[(pack_id, version)] = normalized
            rows = list(rows_by_key.values())
            rows.sort(
                key=lambda item: (
                    0 if bool(item.get("featured")) else 1,
                    -int(item.get("engagement", {}).get("installs", 0) or 0),
                    str(item.get("pack_id") or ""),
                    str(item.get("version") or ""),
                ),
            )
            payload = {
                "schema_version": "v1",
                "generated_at": datetime.now(UTC).isoformat(),
                "rows": rows,
            }
            content = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
            previous_text = snapshot_path.read_text(encoding="utf-8") if snapshot_path.exists() else ""
            changed = content != previous_text
            snapshot_path.parent.mkdir(parents=True, exist_ok=True)
            snapshot_path.write_text(content, encoding="utf-8")
            return {"status": "succeeded", "changed": changed}
        except Exception as exc:  # pragma: no cover - runtime guard
            return {
                "status": "failed",
                "error": "snapshot_rebuild_failed",
                "reason": f"{type(exc).__name__}:{exc}",
            }

    def _filtered_profile_pack_catalog_rows(
        self,
        *,
        pack_query: str = "",
        pack_type: str = "",
        risk_level: str = "",
        review_label: str = "",
        warning_flag: str = "",
        featured: str = "",
    ) -> list[dict]:
        if self.profile_pack_service is None:
            return []

        query = str(pack_query or "").strip().lower()
        normalized_pack_type = str(pack_type or "").strip().lower()
        normalized_risk = str(risk_level or "").strip().lower()
        normalized_review_label = str(review_label or "").strip().lower()
        normalized_warning_flag = str(warning_flag or "").strip().lower()
        featured_filter = str(featured or "").strip().lower()
        rows: list[dict] = []
        for item in self.profile_pack_service.list_published_packs():
            if query and query not in item.pack_id.lower():
                continue
            if normalized_pack_type and item.pack_type.lower() != normalized_pack_type:
                continue
            if normalized_risk and item.risk_level.lower() != normalized_risk:
                continue
            if featured_filter in {"true", "1", "yes", "on"} and not item.featured:
                continue
            if featured_filter in {"false", "0", "no", "off"} and item.featured:
                continue
            if not self._matches_metadata_filters(
                review_labels=item.review_labels,
                warning_flags=item.warning_flags,
                review_label=normalized_review_label,
                warning_flag=normalized_warning_flag,
            ):
                continue
            rows.append(self._profile_pack_published_payload(item))
        return rows

    @staticmethod
    def _profile_pack_catalog_list_len(value) -> int:
        return len(value) if isinstance(value, list) else 0

    @staticmethod
    def _profile_pack_catalog_risk_score(risk_level: str) -> int:
        normalized = str(risk_level or "").strip().lower()
        if normalized == "low":
            return 20
        if normalized == "medium":
            return 12
        if normalized == "high":
            return 4
        return 8

    @staticmethod
    def _profile_pack_catalog_compatibility_score(compatibility: str) -> int:
        normalized = str(compatibility or "").strip().lower()
        if normalized in {"compatible", "ok"}:
            return 14
        if normalized == "degraded":
            return 8
        if normalized == "blocked":
            return 0
        return 6

    @staticmethod
    def _profile_pack_catalog_rank_time(row: dict) -> str:
        return str(row.get("featured_at") or row.get("published_at") or "")

    @classmethod
    def _profile_pack_catalog_rank_score(cls, row: dict) -> int:
        labels = cls._profile_pack_catalog_list_len(row.get("review_labels"))
        warnings = cls._profile_pack_catalog_list_len(row.get("warning_flags"))
        issues = cls._profile_pack_catalog_list_len(row.get("compatibility_issues"))
        featured = 30 if bool(row.get("featured")) else 0
        freshness = 4 if cls._profile_pack_catalog_rank_time(row) else 0
        score = (
            featured
            + cls._profile_pack_catalog_risk_score(str(row.get("risk_level") or ""))
            + cls._profile_pack_catalog_compatibility_score(str(row.get("compatibility") or ""))
            + labels * 3
            + freshness
            - warnings * 4
            - issues * 2
        )
        return max(0, int(score))

    @classmethod
    def _rank_profile_pack_catalog_rows(cls, rows: list[dict]) -> list[dict]:
        ranked = [dict(item) for item in rows]
        for item in ranked:
            item["trend_score"] = cls._profile_pack_catalog_rank_score(item)
        ranked.sort(
            key=lambda item: (
                int(item.get("trend_score", 0) or 0),
                cls._profile_pack_catalog_rank_time(item),
                str(item.get("pack_id") or ""),
            ),
            reverse=True,
        )
        return ranked

    @staticmethod
    def _profile_pack_catalog_metrics(rows: list[dict]) -> dict[str, int]:
        metrics = {
            "total": 0,
            "featured": 0,
            "high_risk": 0,
            "low_risk": 0,
            "extension_pack": 0,
            "bot_profile_pack": 0,
        }
        for item in rows:
            metrics["total"] += 1
            if bool(item.get("featured")):
                metrics["featured"] += 1
            risk_level = str(item.get("risk_level") or "").strip().lower()
            if risk_level == "high":
                metrics["high_risk"] += 1
            if risk_level == "low":
                metrics["low_risk"] += 1
            pack_type = str(item.get("pack_type") or "").strip().lower()
            if pack_type == "extension_pack":
                metrics["extension_pack"] += 1
            if pack_type == "bot_profile_pack":
                metrics["bot_profile_pack"] += 1
        return metrics

    @staticmethod
    def _profile_pack_published_payload(published, detail: bool = False) -> dict:
        payload = {
            "pack_type": published.pack_type,
            "pack_id": published.pack_id,
            "version": published.version,
            "source_submission_id": published.source_submission_id,
            "artifact_id": published.artifact_id,
            "import_id": published.import_id,
            "filename": published.filename,
            "sha256": published.sha256,
            "size_bytes": published.size_bytes,
            "sections": list(published.sections),
            "redaction_mode": published.redaction_mode,
            "capability_summary": dict(published.capability_summary),
            "compatibility_matrix": dict(published.compatibility_matrix),
            "review_evidence": dict(published.review_evidence),
            "featured": published.featured,
            "featured_note": published.featured_note,
            "featured_by": published.featured_by,
            "featured_at": published.featured_at,
            "review_note": published.review_note,
            "review_labels": list(published.review_labels),
            "warning_flags": list(published.warning_flags),
            "risk_level": published.risk_level,
            "scan_summary": published.scan_summary,
            "compatibility": published.compatibility,
            "compatibility_issues": list(published.compatibility_issues),
        }
        if detail:
            payload["published_at"] = published.published_at
        return payload

    def _package_artifact_payload(self, artifact: dict | None) -> dict | None:
        if not isinstance(artifact, dict) or not artifact:
            return None
        if self.package_service is None:
            return dict(artifact)
        return self.package_service.resolve_package_artifact_metadata(artifact)

    def _submission_payload(self, submission) -> dict:
        payload = {
            "id": submission.id,
            "submission_id": submission.id,
            "status": submission.status,
            "template_id": submission.template_id,
            "version": submission.version,
            "user_id": submission.user_id,
            "risk_level": submission.risk_level,
            "review_note": submission.review_note,
            "review_labels": list(submission.review_labels or []),
            "warning_flags": list(submission.warning_flags or []),
            "scan_summary": submission.scan_summary or {},
            "category": submission.category,
            "tags": list(submission.tags or []),
            "maintainer": submission.maintainer,
            "source_channel": submission.source_channel,
            "upload_options": dict(submission.upload_options or {}),
        }
        if submission.package_artifact:
            payload["package_artifact"] = self._package_artifact_payload(submission.package_artifact)
        return payload

    def _submission_detail_payload(self, submission) -> dict:
        payload = self._submission_payload(submission)
        payload["created_at"] = submission.created_at.isoformat()
        payload["updated_at"] = submission.updated_at.isoformat()
        payload["reviewer_id"] = submission.reviewer_id
        payload["prompt_preview"] = str(submission.prompt_template or "")[:240]
        payload["prompt_length"] = len(str(submission.prompt_template or ""))
        return payload

    def _published_payload(self, published, market_service: MarketService | None = None) -> dict:
        payload = {
            "template_id": published.template_id,
            "version": published.version,
            "source_submission_id": published.source_submission_id,
            "risk_level": published.risk_level,
            "review_note": published.review_note,
            "review_labels": list(published.review_labels or []),
            "warning_flags": list(published.warning_flags or []),
            "scan_summary": published.scan_summary or {},
            "category": published.category,
            "tags": list(published.tags or []),
            "maintainer": published.maintainer,
            "source_channel": published.source_channel,
            "engagement": SharelifeApiV1._engagement_payload(published, market_service),
        }
        if published.package_artifact:
            payload["package_artifact"] = self._package_artifact_payload(published.package_artifact)
        return payload

    def _published_detail_payload(self, published, market_service: MarketService | None = None) -> dict:
        payload = self._published_payload(published, market_service)
        payload["published_at"] = published.published_at.isoformat()
        payload["prompt_preview"] = str(published.prompt_template or "")[:240]
        payload["prompt_length"] = len(str(published.prompt_template or ""))
        return payload

    @staticmethod
    def _engagement_payload(published, market_service: MarketService | None = None) -> dict:
        payload = {
            "trial_requests": 0,
            "installs": 0,
            "prompt_generations": 0,
            "package_generations": 0,
            "community_submissions": 0,
            "last_activity_at": "",
        }
        engagement = getattr(published, "engagement", {})
        if isinstance(engagement, dict):
            for key in payload:
                if key in engagement and engagement[key] is not None:
                    payload[key] = engagement[key]
        if market_service is not None:
            payload["community_submissions"] = market_service._submission_count_for_template(  # type: ignore[attr-defined]
                published.template_id
            )
        for key in (
            "trial_requests",
            "installs",
            "prompt_generations",
            "package_generations",
            "community_submissions",
        ):
            payload[key] = int(payload.get(key, 0) or 0)
        payload["last_activity_at"] = str(payload.get("last_activity_at", "") or "")
        return payload

    @staticmethod
    def _sort_templates(templates, sort_by: str = "", sort_order: str = ""):
        normalized_sort = str(sort_by or "").strip().lower() or "template_id"
        if normalized_sort not in {"template_id", "recent_activity", "trial_requests", "installs"}:
            normalized_sort = "template_id"
        normalized_order = str(sort_order or "").strip().lower()
        if normalized_order not in {"asc", "desc"}:
            normalized_order = "asc" if normalized_sort == "template_id" else "desc"

        def key(item):
            engagement = SharelifeApiV1._engagement_payload(item)
            if normalized_sort == "recent_activity":
                return (engagement["last_activity_at"], item.template_id)
            if normalized_sort == "trial_requests":
                return (engagement["trial_requests"], item.template_id)
            if normalized_sort == "installs":
                return (engagement["installs"], item.template_id)
            return item.template_id

        return sorted(templates, key=key, reverse=normalized_order == "desc")

    @staticmethod
    def _matches_metadata_filters(
        review_labels: list[str],
        warning_flags: list[str],
        review_label: str = "",
        warning_flag: str = "",
    ) -> bool:
        if review_label and not any(str(item).strip().lower() == review_label for item in review_labels):
            return False
        if warning_flag and not any(str(item).strip().lower() == warning_flag for item in warning_flags):
            return False
        return True

    @staticmethod
    def _compare_scalar(submission_value, published_value) -> dict:
        return {
            "changed": published_value is not None and submission_value != published_value,
            "submission": submission_value,
            "published": published_value,
        }

    @staticmethod
    def _compare_list(submission_items, published_items) -> dict:
        submission_list = list(submission_items or [])
        published_list = list(published_items or [])
        return {
            "changed": submission_list != published_list,
            "submission": submission_list,
            "published": published_list,
            "added": [item for item in submission_list if item not in published_list],
            "removed": [item for item in published_list if item not in submission_list],
        }

    @staticmethod
    def _compare_prompt(submission_prompt: str | None, published_prompt: str | None) -> dict:
        submission_text = str(submission_prompt or "")
        published_text = str(published_prompt or "") if published_prompt is not None else None
        return {
            "changed": published_prompt is not None and submission_text != str(published_prompt or ""),
            "submission_preview": submission_text[:160],
            "published_preview": str(published_text or "")[:160] if published_text is not None else None,
            "submission_length": len(submission_text),
            "published_length": len(str(published_text or "")) if published_text is not None else None,
        }

    @staticmethod
    def _compare_package(submission_artifact, published_artifact) -> dict:
        submission = submission_artifact or {}
        published = published_artifact or {}
        return {
            "changed": bool(published_artifact) and submission != published,
            "submission_filename": submission.get("filename"),
            "published_filename": published.get("filename"),
            "filename_changed": bool(published_artifact) and submission.get("filename") != published.get("filename"),
            "submission_sha256": submission.get("sha256"),
            "published_sha256": published.get("sha256"),
            "sha256_changed": bool(published_artifact) and submission.get("sha256") != published.get("sha256"),
            "submission_size_bytes": submission.get("size_bytes"),
            "published_size_bytes": published.get("size_bytes"),
        }

    @staticmethod
    def _compare_scan(submission_scan, published_scan) -> dict:
        submission = submission_scan or {}
        published = published_scan or {}
        submission_injection = submission.get("prompt_injection", {}) if isinstance(submission, dict) else {}
        published_injection = published.get("prompt_injection", {}) if isinstance(published, dict) else {}
        submission_levels = list(submission.get("levels", []) or []) if isinstance(submission, dict) else []
        published_levels = list(published.get("levels", []) or []) if isinstance(published, dict) else []
        return {
            "changed": bool(published_scan) and submission != published,
            "submission_compatibility": submission.get("compatibility") if isinstance(submission, dict) else None,
            "published_compatibility": published.get("compatibility") if isinstance(published, dict) else None,
            "compatibility_changed": bool(published_scan) and submission.get("compatibility") != published.get("compatibility"),
            "submission_levels": submission_levels,
            "published_levels": published_levels,
            "levels_added": [item for item in submission_levels if item not in published_levels],
            "levels_removed": [item for item in published_levels if item not in submission_levels],
            "submission_prompt_injection_detected": bool(submission_injection.get("detected")),
            "published_prompt_injection_detected": bool(published_injection.get("detected")),
            "prompt_injection_detected_changed": bool(published_scan) and bool(submission_injection.get("detected")) != bool(published_injection.get("detected")),
        }
