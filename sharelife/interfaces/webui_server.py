"""Embedded standalone WebUI server for Sharelife."""

from __future__ import annotations

import asyncio
import secrets
import time
from pathlib import Path
from typing import Any

from astrbot.api import logger

from ..application.services_profile_pack_bootstrap import ProfilePackBootstrapService
from .web_api_v1 import SharelifeWebApiV1, WebApiResult

try:
    import uvicorn
    from fastapi import FastAPI, Request
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse, RedirectResponse
    from fastapi.staticfiles import StaticFiles

    FASTAPI_AVAILABLE = True
except Exception:
    FASTAPI_AVAILABLE = False
    logger.warning(
        "[sharelife] fastapi/uvicorn unavailable; standalone WebUI disabled.",
    )


def _to_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        norm = value.strip().lower()
        if norm in {"1", "true", "yes", "on"}:
            return True
        if norm in {"0", "false", "no", "off"}:
            return False
    return default


def _to_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _to_string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        items = value
    elif isinstance(value, str):
        items = value.split(",")
    else:
        return []
    out: list[str] = []
    seen: set[str] = set()
    for item in items:
        text = str(item or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        out.append(text)
    return out


def _optional_string_list(payload: dict[str, Any], key: str) -> list[str] | None:
    if key not in payload:
        return None
    return _to_string_list(payload.get(key))


def _auth_secret_requested(value: Any) -> bool:
    text = str(value or "")
    return text != ""


def _normalize_auth_secret(
    value: Any,
    *,
    min_length: int = 1,
    allow_whitespace: bool = False,
) -> str:
    raw = str(value or "")
    text = raw.strip()
    if not text:
        return ""
    if len(text) < max(1, int(min_length or 1)):
        return ""
    if not allow_whitespace and any(ch.isspace() for ch in text):
        return ""
    return text


class SharelifeWebUIServer:
    """Provides a standalone page and HTTP APIs for Sharelife management."""

    _DEFAULT_SECURITY_HEADERS: dict[str, str] = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Referrer-Policy": "no-referrer",
        "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
        "Content-Security-Policy": (
            "default-src 'self'; "
            "base-uri 'self'; "
            "frame-ancestors 'none'; "
            "object-src 'none'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "connect-src 'self'; "
            "form-action 'self'"
        ),
    }

    _PUBLIC_UI_OPERATIONS: set[str] = {
        "auth.info.read",
        "auth.login",
        "health.read",
        "ui.capabilities.read",
    }
    _ANONYMOUS_MEMBER_UI_OPERATIONS: set[str] = {
        "member.installations.read",
        "member.installations.refresh",
        "member.installations.uninstall",
        "member.tasks.read",
        "member.tasks.refresh",
        "notifications.read",
        "preferences.read",
        "preferences.write",
        "profile_pack.catalog.read",
        "templates.detail",
        "templates.install",
        "templates.list",
        "templates.package.download",
        "templates.trial.request",
        "templates.trial.status",
    }
    _MEMBER_UI_OPERATIONS: set[str] = {
        "member.installations.read",
        "member.installations.refresh",
        "member.installations.uninstall",
        "member.profile_pack.imports.delete",
        "member.profile_pack.imports.local_astrbot",
        "member.profile_pack.imports.package_upload",
        "member.tasks.read",
        "member.tasks.refresh",
        "member.profile_pack.imports.read",
        "member.profile_pack.imports.write",
        "member.submissions.read",
        "member.submissions.detail.read",
        "member.submissions.package.download",
        "member.profile_pack.submissions.read",
        "member.profile_pack.submissions.detail.read",
        "member.profile_pack.submissions.withdraw",
        "member.profile_pack.submissions.export.download",
        "notifications.read",
        "preferences.read",
        "preferences.write",
        "profile_pack.catalog.read",
        "profile_pack.community.submit",
        "templates.detail",
        "templates.install",
        "templates.list",
        "templates.package.download",
        "templates.package.generate",
        "templates.prompt.generate",
        "templates.submit",
        "templates.trial.request",
        "templates.trial.status",
    }
    _REVIEWER_UI_OPERATIONS: set[str] = {
        "admin.profile_pack.market.review",
        "admin.submissions.compare",
        "admin.submissions.decide",
        "admin.submissions.package.download",
        "admin.submissions.read",
        "admin.submissions.review",
    }
    _ADMIN_UI_OPERATIONS: set[str] = {
        "admin.apply.workflow",
        "admin.audit.read",
        "admin.reviewer.lifecycle.manage",
        "admin.storage.jobs.read",
        "admin.storage.jobs.run",
        "admin.storage.local_summary.read",
        "admin.storage.policies.read",
        "admin.storage.policies.write",
        "admin.storage.restore.cancel",
        "admin.storage.restore.commit",
        "admin.storage.restore.prepare",
        "admin.storage.restore.read",
        "admin.pipeline.run",
        "admin.profile_pack.featured.write",
        "admin.profile_pack.manage",
        "admin.profile_pack.market.review",
        "admin.retry.manage",
        "admin.submissions.compare",
        "admin.submissions.decide",
        "admin.submissions.package.download",
        "admin.submissions.read",
        "admin.submissions.review",
    }
    _ANONYMOUS_MEMBER_COOKIE_NAME = "sharelife_anon_member"

    def __init__(
        self,
        api: SharelifeWebApiV1,
        config: dict[str, Any] | None,
        web_root: Path,
    ):
        self.api = api
        self.config = config or {}
        self.web_root = web_root
        self.public_market_root = web_root.parents[1] / "docs" / "public"
        self.private_docs_root = web_root.parents[1] / "docs-private"

        self.app: Any = None
        self.server: Any = None
        self._server_task: asyncio.Task | None = None
        self.public_url: str = ""

        self._auth_enabled = False
        self._active_auth_roles: set[str] = set()
        self._invalid_auth_roles: set[str] = set()
        self._auth_token_ttl_seconds = 7200
        self._reviewer_token_ttl_seconds = 7 * 24 * 3600
        self._auth_allow_query_token = False
        self._auth_allow_anonymous_member = False
        self._auth_anonymous_member_user_id = "webui-user"
        self._auth_anonymous_member_allowlist = self._anonymous_member_default_api_paths()
        self._feature_local_astrbot_import = True
        self._feature_allow_anonymous_local_astrbot_import = False
        self._login_rate_limit_window_seconds = 60
        self._login_rate_limit_max_attempts = 10
        self._login_attempts: dict[str, list[float]] = {}
        self._api_rate_limit_window_seconds = 60
        self._api_rate_limit_max_requests = 600
        self._metrics_max_paths = 128
        self._metrics_overflow_path_label = "/__other__"
        self._metrics_known_paths: set[str] = set()
        self._api_requests: dict[str, list[float]] = {}
        self._http_request_counts: dict[str, int] = {}
        self._http_request_durations_ms_sum: dict[str, float] = {}
        self._http_request_durations_ms_count: dict[str, int] = {}
        self._http_error_counts: dict[str, int] = {}
        self._auth_event_counts: dict[str, int] = {}
        self._rate_limit_counts: dict[str, int] = {}
        self._security_alert_counts: dict[str, int] = {}
        self._security_alert_windows: dict[str, list[float]] = {}
        self._security_alert_last_sent_at: dict[str, float] = {}
        self._security_alert_window_seconds = 300
        self._security_alert_threshold = 3
        self._security_alert_cooldown_seconds = 300
        self._security_headers_enabled = True
        self._security_headers: dict[str, str] = dict(self._DEFAULT_SECURITY_HEADERS)
        self._refresh_auth()
        self._ensure_profile_pack_catalog_seeded()

        if FASTAPI_AVAILABLE:
            self._setup_app()

    def _ensure_profile_pack_catalog_seeded(self) -> None:
        inner_api = getattr(self.api, "api", None)
        profile_pack_service = getattr(inner_api, "profile_pack_service", None)
        if profile_pack_service is None:
            return
        try:
            result = ProfilePackBootstrapService(profile_pack_service=profile_pack_service).sync()
            seeded = int(result.get("seeded", 0) or 0)
            skipped = int(result.get("skipped", 0) or 0)
            logger.info(
                "[sharelife] webui profile-pack bootstrap synced seeded=%s skipped=%s",
                seeded,
                skipped,
            )
        except Exception as exc:  # pragma: no cover - defensive bootstrap guard
            logger.warning(
                "[sharelife] webui profile-pack bootstrap failed: %s",
                exc,
            )

    def _submission_package_limit_bytes(self) -> int:
        inner_api = getattr(self.api, "api", None)
        package_service = getattr(inner_api, "package_service", None)
        value = getattr(package_service, "max_submission_package_bytes", 20 * 1024 * 1024)
        return max(1, int(value or 20 * 1024 * 1024))

    def _submission_request_limit_bytes(self) -> int:
        limit = self._submission_package_limit_bytes()
        return (((limit + 2) // 3) * 4) + (1024 * 1024)

    def _private_docs_allowed_roles(self) -> set[str]:
        cfg = self._webui_config()
        private_docs = (
            cfg.get("private_docs", {})
            if isinstance(cfg.get("private_docs"), dict)
            else {}
        )
        roles = {
            self._normalize_role(item)
            for item in _to_string_list(private_docs.get("allowed_roles", ["admin"]))
        }
        roles.discard("member")
        roles.discard("public")
        return roles or {"admin"}

    def _list_private_docs(self) -> list[dict[str, Any]]:
        if not self.private_docs_root.exists():
            return []
        rows: list[dict[str, Any]] = []
        for path in sorted(self.private_docs_root.rglob("*")):
            if not path.is_file():
                continue
            relative = path.relative_to(self.private_docs_root)
            if any(part.startswith(".") for part in relative.parts):
                continue
            rows.append(
                {
                    "path": relative.as_posix(),
                    "size_bytes": int(path.stat().st_size),
                }
            )
        return rows

    def _resolve_private_doc_path(self, relative_path: str) -> Path | None:
        text = str(relative_path or "").strip().replace("\\", "/")
        if not text:
            return None
        candidate = (self.private_docs_root / text).resolve()
        try:
            candidate.relative_to(self.private_docs_root.resolve())
        except Exception:
            return None
        if not candidate.exists() or not candidate.is_file():
            return None
        return candidate

    def _webui_config(self) -> dict[str, Any]:
        raw = self.config.get("webui", {}) if isinstance(self.config, dict) else {}
        return raw if isinstance(raw, dict) else {}

    def _refresh_auth(self) -> None:
        cfg = self._webui_config()
        auth = cfg.get("auth", {}) if isinstance(cfg.get("auth"), dict) else {}
        features = cfg.get("features", {}) if isinstance(cfg.get("features"), dict) else {}
        member_import_features = (
            features.get("member_import", {})
            if isinstance(features.get("member_import"), dict)
            else {}
        )
        security_headers = (
            cfg.get("security_headers", {})
            if isinstance(cfg.get("security_headers"), dict)
            else {}
        )
        observability = (
            cfg.get("observability", {})
            if isinstance(cfg.get("observability"), dict)
            else {}
        )
        legacy_password_raw = str(auth.get("password", "") or "")
        member_password_raw = str(auth.get("member_password", "") or legacy_password_raw)
        admin_password_raw = str(auth.get("admin_password", "") or "")
        reviewer_password_raw = str(auth.get("reviewer_password", "") or "")
        member_password = _normalize_auth_secret(member_password_raw)
        reviewer_password = _normalize_auth_secret(reviewer_password_raw)
        admin_password = _normalize_auth_secret(admin_password_raw, min_length=12)
        self._auth_token_ttl_seconds = max(1, _to_int(auth.get("token_ttl_seconds"), 7200))
        self._reviewer_token_ttl_seconds = max(
            3600,
            _to_int(auth.get("reviewer_token_ttl_seconds"), 7 * 24 * 3600),
        )
        self._auth_allow_query_token = _to_bool(auth.get("allow_query_token"), default=False)
        self._auth_allow_anonymous_member = _to_bool(
            auth.get("allow_anonymous_member"),
            default=False,
        )
        self._auth_anonymous_member_user_id = (
            str(auth.get("anonymous_member_user_id", "webui-user") or "webui-user").strip()
            or "webui-user"
        )
        raw_anonymous_member_allowlist = auth.get("anonymous_member_allowlist")
        if raw_anonymous_member_allowlist is None:
            self._auth_anonymous_member_allowlist = self._anonymous_member_default_api_paths()
        else:
            self._auth_anonymous_member_allowlist = self._parse_anonymous_member_allowlist(
                raw_anonymous_member_allowlist,
            )
        local_astrbot_import_raw = member_import_features.get(
            "local_astrbot_import",
            features.get("local_astrbot_import"),
        )
        self._feature_local_astrbot_import = _to_bool(
            local_astrbot_import_raw,
            default=True,
        )
        allow_anonymous_local_import_raw = member_import_features.get(
            "allow_anonymous_local_astrbot_import",
            features.get("allow_anonymous_local_astrbot_import"),
        )
        if allow_anonymous_local_import_raw is None:
            allow_anonymous_local_import = self._auth_allow_anonymous_member
        else:
            allow_anonymous_local_import = _to_bool(
                allow_anonymous_local_import_raw,
                default=False,
            )
        self._feature_allow_anonymous_local_astrbot_import = (
            self._feature_local_astrbot_import
            and allow_anonymous_local_import
        )
        self._login_rate_limit_window_seconds = max(
            1,
            _to_int(auth.get("login_rate_limit_window_seconds"), 60),
        )
        self._login_rate_limit_max_attempts = max(
            1,
            _to_int(auth.get("login_rate_limit_max_attempts"), 10),
        )
        self._api_rate_limit_window_seconds = max(
            1,
            _to_int(auth.get("api_rate_limit_window_seconds"), 60),
        )
        self._api_rate_limit_max_requests = max(
            1,
            _to_int(auth.get("api_rate_limit_max_requests"), 600),
        )
        self._metrics_max_paths = max(
            8,
            _to_int(observability.get("metrics_max_paths"), 128),
        )
        self._security_alert_window_seconds = max(
            30,
            _to_int(observability.get("security_alert_window_seconds"), 300),
        )
        self._security_alert_threshold = max(
            1,
            _to_int(observability.get("security_alert_threshold"), 3),
        )
        self._security_alert_cooldown_seconds = max(
            30,
            _to_int(observability.get("security_alert_cooldown_seconds"), 300),
        )
        overflow_label = str(
            observability.get("metrics_overflow_path_label", "/__other__") or "/__other__"
        ).strip()
        if not overflow_label.startswith("/"):
            overflow_label = f"/{overflow_label}"
        self._metrics_overflow_path_label = overflow_label or "/__other__"
        self._security_headers_enabled = _to_bool(
            security_headers.get("enabled"),
            default=True,
        )
        self._security_headers = {}
        for header_name, default_value in self._DEFAULT_SECURITY_HEADERS.items():
            raw_value = security_headers.get(header_name, default_value)
            if raw_value is None:
                continue
            value = str(raw_value).replace("\r", "").replace("\n", " ").strip()
            if not value:
                continue
            self._security_headers[header_name] = value

        auth_service = self._reviewer_auth_service()
        self._active_auth_roles = set()
        self._invalid_auth_roles = set()
        if _auth_secret_requested(member_password_raw) and not member_password:
            self._invalid_auth_roles.add("member")
        if _auth_secret_requested(reviewer_password_raw) and not reviewer_password:
            self._invalid_auth_roles.add("reviewer")
        if _auth_secret_requested(admin_password_raw) and not admin_password:
            self._invalid_auth_roles.add("admin")
        if auth_service is not None:
            if member_password:
                auth_service.sync_bootstrap_password("member", member_password)
                self._active_auth_roles.add("member")
            if reviewer_password:
                auth_service.sync_bootstrap_password("reviewer", reviewer_password)
                self._active_auth_roles.add("reviewer")
            if admin_password:
                auth_service.sync_bootstrap_password("admin", admin_password)
                self._active_auth_roles.add("admin")

        self._auth_enabled = bool(self._active_auth_roles) or bool(self._invalid_auth_roles)
        self._login_attempts = {}
        self._api_requests = {}
        self._metrics_known_paths = set()
        self._security_alert_counts = {}
        self._security_alert_windows = {}
        self._security_alert_last_sent_at = {}
        if self._invalid_auth_roles:
            logger.warning(
                "[sharelife] webui auth ignored invalid credentials for roles=%s",
                ",".join(sorted(self._invalid_auth_roles)),
            )

    def _available_auth_roles(self) -> list[str]:
        return [role for role in ("member", "reviewer", "admin") if role in self._active_auth_roles]

    def _token_from_request(self, request: Request) -> str:
        auth_header = str(request.headers.get("Authorization", "") or "").strip()
        if auth_header.startswith("Bearer "):
            return str(auth_header[7:] or "").strip()
        if self._auth_allow_query_token:
            return str(request.query_params.get("token", "") or "").strip()
        return ""

    @classmethod
    def _operations_for_role(cls, role: str) -> list[str]:
        normalized_role = cls._normalize_role(role)
        operations = set(cls._PUBLIC_UI_OPERATIONS)
        if normalized_role in {"member", "reviewer", "admin"}:
            operations.update(cls._MEMBER_UI_OPERATIONS)
        if normalized_role in {"reviewer", "admin"}:
            operations.update(cls._REVIEWER_UI_OPERATIONS)
        if normalized_role == "admin":
            operations.update(cls._ADMIN_UI_OPERATIONS)
        return sorted(operations)

    def _runtime_feature_payload(self) -> dict[str, Any]:
        allow_anonymous_local_astrbot_import = (
            self._feature_local_astrbot_import
            and self._feature_allow_anonymous_local_astrbot_import
            and self._auth_allow_anonymous_member
        )
        return {
            "supports_local_astrbot_import": self._feature_local_astrbot_import,
            "allow_anonymous_local_astrbot_import": allow_anonymous_local_astrbot_import,
        }

    def _effective_operations_for_role(self, role: str) -> list[str]:
        operations = set(self._operations_for_role(role))
        if not self._feature_local_astrbot_import:
            operations.discard("member.profile_pack.imports.local_astrbot")
        return sorted(operations)

    def _anonymous_member_import_operations(self) -> set[str]:
        if not self._runtime_feature_payload()["allow_anonymous_local_astrbot_import"]:
            return set()
        return {
            "member.profile_pack.imports.delete",
            "member.profile_pack.imports.local_astrbot",
            "member.profile_pack.imports.read",
        }

    def _anonymous_member_operations(self) -> list[str]:
        operations = set(self._PUBLIC_UI_OPERATIONS) | set(self._ANONYMOUS_MEMBER_UI_OPERATIONS)
        operations.update(self._anonymous_member_import_operations())
        return sorted(operations)

    def _issue_anonymous_member_subject(self) -> str:
        base = str(self._auth_anonymous_member_user_id or "webui-user").strip() or "webui-user"
        return f"{base}-{secrets.token_hex(8)}"

    def _anonymous_member_subject_from_request(self, request: Request) -> str:
        cookie_value = str(
            request.cookies.get(self._ANONYMOUS_MEMBER_COOKIE_NAME, "") or "",
        ).strip()
        base = str(self._auth_anonymous_member_user_id or "webui-user").strip() or "webui-user"
        if cookie_value.startswith(f"{base}-") and len(cookie_value) > len(base) + 1:
            return cookie_value
        return ""

    @staticmethod
    def _console_scopes_for_role(page_mode: str, role: str) -> list[str]:
        normalized_page_mode = str(page_mode or "").strip().lower()
        if normalized_page_mode == "user":
            normalized_page_mode = "member"
        if normalized_page_mode in {"member", "reviewer", "admin"}:
            return [normalized_page_mode]
        normalized_role = SharelifeWebUIServer._normalize_role(role)
        if normalized_role in {"member", "reviewer", "admin"}:
            return [normalized_role]
        return ["member"]

    def _request_ui_capability_role(self, request: Request) -> str:
        if self._auth_enabled:
            role = self._role_from_token(self._token_from_request(request))
            if role in {"member", "reviewer", "admin"}:
                return role
            return "public"
        role = self._request_role(request)
        if role in {"member", "reviewer", "admin"}:
            return role
        return "member"

    @staticmethod
    def _normalize_role(role: str) -> str:
        text = str(role or "").strip().lower()
        if text in {"member", "user"}:
            return "member"
        if text in {"reviewer", "admin", "public"}:
            return text
        return "member"

    def _reviewer_auth_service(self):
        inner_api = getattr(self.api, "api", None)
        return getattr(inner_api, "reviewer_auth_service", None)

    def _session_from_token(self, token: str) -> dict[str, Any] | None:
        service = self._reviewer_auth_service()
        if service is None:
            return None
        session = service.resolve_session(str(token or "").strip())
        if not isinstance(session, dict):
            return None
        role = self._normalize_role(str(session.get("role", "") or ""))
        if role not in self._active_auth_roles:
            return None
        if role == "reviewer":
            reviewer_id = str(session.get("user_id", "") or "").strip()
            device_id = str(session.get("device_id", "") or "").strip()
            if not reviewer_id or not device_id or service is None:
                self._revoke_token(str(token or "").strip(), role=role, subject=reviewer_id)
                return None
            devices = service.list_devices(user_id=reviewer_id)
            device_exists = any(
                str(item.get("device_id", "") or "").strip() == device_id
                for item in devices
                if isinstance(item, dict)
            )
            if not device_exists:
                self._revoke_token(str(token or "").strip(), role=role, subject=reviewer_id)
                return None
        return {
            "session_id": str(session.get("session_id", "") or "").strip(),
            "role": role,
            "subject": str(session.get("user_id", "") or "").strip(),
            "device_id": str(session.get("device_id", "") or "").strip(),
            "issued_at": float(session.get("issued_at", 0.0) or 0.0),
            "expires_at": float(session.get("expires_at", 0.0) or 0.0),
            "last_seen_at": float(session.get("last_seen_at", 0.0) or 0.0),
        }

    def _role_from_token(self, token: str) -> str | None:
        session = self._session_from_token(token)
        if session is None:
            return None
        return self._normalize_role(str(session.get("role", "") or ""))

    @staticmethod
    def _normalize_page_mode(page_mode: str) -> str:
        text = str(page_mode or "").strip().lower()
        if text == "user":
            return "member"
        if text in {"member", "reviewer", "admin"}:
            return text
        return ""

    def _ui_capability_payload(self, request: Request, *, page_mode: str = "") -> dict[str, Any]:
        normalized_page_mode = self._normalize_page_mode(page_mode)
        feature_payload = self._runtime_feature_payload()
        if not self._auth_enabled:
            role = self._request_role(request)
            if role not in {"member", "reviewer", "admin"}:
                role = "member"
            operations = self._effective_operations_for_role(role)
            return {
                "ok": True,
                "auth_required": False,
                "authenticated": True,
                "anonymous_member": False,
                "role": role,
                "available_roles": ["member", "reviewer", "admin"],
                "operations": operations,
                **feature_payload,
                "console_scopes": self._console_scopes_for_role(
                    page_mode=normalized_page_mode,
                    role=role,
                ),
            }

        token = self._token_from_request(request)
        role = self._role_from_token(token)
        if role in {"member", "reviewer", "admin"}:
            operations = self._effective_operations_for_role(role)
            return {
                "ok": True,
                "auth_required": True,
                "authenticated": True,
                "anonymous_member": False,
                "role": role,
                "available_roles": self._available_auth_roles(),
                "operations": operations,
                **feature_payload,
                "console_scopes": self._console_scopes_for_role(
                    page_mode=normalized_page_mode,
                    role=role,
                ),
            }

        anonymous_member = (
            self._auth_allow_anonymous_member
            and normalized_page_mode not in {"reviewer", "admin"}
        )
        if anonymous_member:
            role = "member"
            operations = self._anonymous_member_operations()
        else:
            role = "public"
            operations = sorted(self._PUBLIC_UI_OPERATIONS)
        return {
            "ok": True,
            "auth_required": True,
            "authenticated": False,
            "anonymous_member": anonymous_member,
            "role": role,
            "available_roles": self._available_auth_roles(),
            "operations": operations,
            **feature_payload,
            "console_scopes": self._console_scopes_for_role(
                page_mode=normalized_page_mode,
                role=role,
            ),
        }

    def _issue_token(self, role: str, *, subject: str = "", device_id: str = "") -> str:
        normalized_role = self._normalize_role(role)
        if normalized_role not in self._active_auth_roles:
            raise ValueError("PROFILE_WEBUI_AUTH_ROLE_UNAVAILABLE")
        service = self._reviewer_auth_service()
        if service is None:
            raise ValueError("PROFILE_WEBUI_AUTH_SERVICE_UNAVAILABLE")
        normalized_subject = str(subject or "").strip()
        normalized_device_id = str(device_id or "").strip()
        if normalized_role == "reviewer" and not normalized_subject:
            raise ValueError("PROFILE_WEBUI_REVIEWER_ID_REQUIRED")
        ttl_seconds = self._auth_token_ttl_seconds
        if normalized_role == "reviewer":
            ttl_seconds = self._reviewer_token_ttl_seconds
        session = service.issue_session(
            role=normalized_role,
            subject=normalized_subject,
            device_id=normalized_device_id,
            ttl_seconds=ttl_seconds,
        )
        return str(session.get("token", "") or "")

    def _revoke_token(
        self,
        token: str,
        *,
        role: str = "",
        subject: str = "",
        device_id: str = "",
    ) -> None:
        text = str(token or "").strip()
        if not text:
            return
        service = self._reviewer_auth_service()
        if service is None:
            return
        service.revoke_session_token(text)

    def _client_key(self, request: Request, role: str) -> str:
        host = "unknown"
        if request.client is not None:
            host = str(request.client.host or "unknown")
        return f"{host}:{role}"

    @staticmethod
    def _normalize_rate_limit_path(path: str) -> str:
        text = str(path or "").strip()
        if not text:
            return "/"
        if "?" in text:
            return text.split("?", 1)[0]
        return text

    def _login_rate_limit_allowed(self, request: Request, role: str) -> bool:
        now = time.time()
        key = self._client_key(request, role)
        window_start = now - float(self._login_rate_limit_window_seconds)
        rows = [item for item in self._login_attempts.get(key, []) if item >= window_start]
        self._login_attempts[key] = rows
        return len(rows) < self._login_rate_limit_max_attempts

    def _record_login_failure(self, request: Request, role: str) -> None:
        key = self._client_key(request, role)
        rows = self._login_attempts.get(key, [])
        rows.append(time.time())
        self._login_attempts[key] = rows

    def _clear_login_failures(self, request: Request, role: str) -> None:
        key = self._client_key(request, role)
        self._login_attempts.pop(key, None)

    def _api_rate_limit_key(self, request: Request, role: str, path: str) -> str:
        host = "unknown"
        if request.client is not None:
            host = str(request.client.host or "unknown")
        normalized_role = str(role or "public").strip().lower() or "public"
        normalized_path = self._normalize_rate_limit_path(path)
        return f"{host}:{normalized_role}:{normalized_path}"

    def _api_rate_limit_status(
        self,
        request: Request,
        role: str,
        path: str,
    ) -> tuple[bool, int]:
        now = time.time()
        key = self._api_rate_limit_key(request, role, path)
        window_start = now - float(self._api_rate_limit_window_seconds)
        rows = [item for item in self._api_requests.get(key, []) if item >= window_start]
        self._api_requests[key] = rows
        if len(rows) >= self._api_rate_limit_max_requests:
            earliest = rows[0]
            retry_after = max(1, int((earliest + float(self._api_rate_limit_window_seconds)) - now))
            return False, retry_after
        rows.append(now)
        self._api_requests[key] = rows
        return True, 0

    @staticmethod
    def _prometheus_label(value: Any) -> str:
        text = str(value or "")
        escaped = text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
        return escaped

    def _normalize_metrics_path(self, path: str) -> str:
        normalized = self._normalize_rate_limit_path(path)
        if normalized in self._metrics_known_paths:
            return normalized
        if len(self._metrics_known_paths) < self._metrics_max_paths:
            self._metrics_known_paths.add(normalized)
            return normalized
        return self._metrics_overflow_path_label

    def _record_http_metrics(
        self,
        *,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        role: str,
        error_code: str = "",
    ) -> None:
        normalized_method = str(method or "GET").upper()
        normalized_path = self._normalize_metrics_path(path)
        normalized_status = str(int(status_code))
        normalized_role = str(role or "public").strip().lower() or "public"
        counter_key = "|".join((normalized_method, normalized_path, normalized_status, normalized_role))
        self._http_request_counts[counter_key] = self._http_request_counts.get(counter_key, 0) + 1

        duration_key = "|".join((normalized_method, normalized_path, normalized_role))
        self._http_request_durations_ms_sum[duration_key] = (
            self._http_request_durations_ms_sum.get(duration_key, 0.0) + max(0.0, float(duration_ms))
        )
        self._http_request_durations_ms_count[duration_key] = (
            self._http_request_durations_ms_count.get(duration_key, 0) + 1
        )

        code = str(error_code or "").strip().lower()
        if code:
            error_key = "|".join((code, normalized_path, normalized_role))
            self._http_error_counts[error_key] = self._http_error_counts.get(error_key, 0) + 1

    def _record_auth_event(self, *, event: str, role: str) -> None:
        normalized_event = str(event or "unknown").strip().lower() or "unknown"
        normalized_role = str(role or "public").strip().lower() or "public"
        key = "|".join((normalized_event, normalized_role))
        self._auth_event_counts[key] = self._auth_event_counts.get(key, 0) + 1

    def _record_rate_limit_event(self, *, scope: str, role: str, path: str) -> None:
        normalized_scope = str(scope or "api").strip().lower() or "api"
        normalized_role = str(role or "public").strip().lower() or "public"
        normalized_path = self._normalize_metrics_path(path)
        key = "|".join((normalized_scope, normalized_role, normalized_path))
        self._rate_limit_counts[key] = self._rate_limit_counts.get(key, 0) + 1

    def _record_security_alert_metric(self, *, event: str, role: str, path: str) -> None:
        normalized_event = str(event or "unknown").strip().lower() or "unknown"
        normalized_role = str(role or "public").strip().lower() or "public"
        normalized_path = self._normalize_metrics_path(path)
        key = "|".join((normalized_event, normalized_role, normalized_path))
        self._security_alert_counts[key] = self._security_alert_counts.get(key, 0) + 1

    def _notifier(self):
        return getattr(self.api, "notifier", None)

    @staticmethod
    def _client_host(request: Request) -> str:
        if request.client is None:
            return "unknown"
        return str(request.client.host or "unknown")

    @staticmethod
    def _is_sensitive_anomaly_path(path: str) -> bool:
        normalized = str(path or "").strip().lower()
        return (
            normalized == "/api/login"
            or normalized.startswith("/api/admin")
            or normalized.startswith("/api/reviewer")
        )

    def _emit_security_alert(
        self,
        *,
        event: str,
        role: str,
        path: str,
        client_host: str,
        count: int,
        reason: str = "",
    ) -> None:
        notifier = self._notifier()
        if notifier is None or not hasattr(notifier, "notify_admin"):
            return
        normalized_event = str(event or "unknown").strip().lower() or "unknown"
        normalized_role = str(role or "public").strip().lower() or "public"
        normalized_path = self._normalize_rate_limit_path(path)
        message = (
            "[security-anomaly] "
            f"event={normalized_event} role={normalized_role} path={normalized_path} "
            f"client={client_host or 'unknown'} count={int(count or 0)}"
        )
        if reason:
            message += f" reason={str(reason).strip()}"
        notifier.notify_admin(message)
        self._record_security_alert_metric(
            event=normalized_event,
            role=normalized_role,
            path=normalized_path,
        )

    def _security_anomaly_threshold_reached(
        self,
        *,
        request: Request,
        event: str,
        role: str,
        path: str,
        threshold: int | None = None,
    ) -> tuple[bool, int]:
        now = time.time()
        normalized_event = str(event or "unknown").strip().lower() or "unknown"
        normalized_role = str(role or "public").strip().lower() or "public"
        normalized_path = self._normalize_rate_limit_path(path)
        client_host = self._client_host(request)
        key = "|".join((client_host, normalized_event, normalized_role, normalized_path))
        window_start = now - float(self._security_alert_window_seconds)
        rows = [item for item in self._security_alert_windows.get(key, []) if item >= window_start]
        rows.append(now)
        self._security_alert_windows[key] = rows
        required = max(1, int(threshold or self._security_alert_threshold))
        return len(rows) >= required, len(rows)

    def _maybe_emit_security_alert(
        self,
        *,
        request: Request,
        event: str,
        role: str,
        path: str,
        reason: str = "",
        threshold: int | None = None,
    ) -> None:
        normalized_event = str(event or "unknown").strip().lower() or "unknown"
        normalized_role = str(role or "public").strip().lower() or "public"
        normalized_path = self._normalize_rate_limit_path(path)
        if not self._is_sensitive_anomaly_path(normalized_path):
            return
        reached, count = self._security_anomaly_threshold_reached(
            request=request,
            event=normalized_event,
            role=normalized_role,
            path=normalized_path,
            threshold=threshold,
        )
        if not reached:
            return
        client_host = self._client_host(request)
        cooldown_key = "|".join((client_host, normalized_event, normalized_role, normalized_path))
        now = time.time()
        last_sent = float(self._security_alert_last_sent_at.get(cooldown_key, 0.0) or 0.0)
        if now - last_sent < float(self._security_alert_cooldown_seconds):
            return
        self._security_alert_last_sent_at[cooldown_key] = now
        self._emit_security_alert(
            event=normalized_event,
            role=normalized_role,
            path=normalized_path,
            client_host=client_host,
            count=count,
            reason=reason,
        )

    def _prometheus_metrics_text(self) -> str:
        lines = [
            "# HELP sharelife_webui_http_requests_total Total HTTP requests served by Sharelife WebUI.",
            "# TYPE sharelife_webui_http_requests_total counter",
        ]
        for key in sorted(self._http_request_counts):
            method, path, status, role = key.split("|", 3)
            value = self._http_request_counts[key]
            lines.append(
                "sharelife_webui_http_requests_total"
                f'{{method="{self._prometheus_label(method)}",'
                f'path="{self._prometheus_label(path)}",'
                f'status="{self._prometheus_label(status)}",'
                f'role="{self._prometheus_label(role)}"}} {value}'
            )

        lines.extend(
            [
                "# HELP sharelife_webui_http_request_duration_ms_sum Sum of HTTP request duration in milliseconds.",
                "# TYPE sharelife_webui_http_request_duration_ms_sum counter",
            ]
        )
        for key in sorted(self._http_request_durations_ms_sum):
            method, path, role = key.split("|", 2)
            value = self._http_request_durations_ms_sum[key]
            lines.append(
                "sharelife_webui_http_request_duration_ms_sum"
                f'{{method="{self._prometheus_label(method)}",'
                f'path="{self._prometheus_label(path)}",'
                f'role="{self._prometheus_label(role)}"}} {value:.3f}'
            )

        lines.extend(
            [
                "# HELP sharelife_webui_http_request_duration_ms_count Count of HTTP requests in duration metric.",
                "# TYPE sharelife_webui_http_request_duration_ms_count counter",
            ]
        )
        for key in sorted(self._http_request_durations_ms_count):
            method, path, role = key.split("|", 2)
            value = self._http_request_durations_ms_count[key]
            lines.append(
                "sharelife_webui_http_request_duration_ms_count"
                f'{{method="{self._prometheus_label(method)}",'
                f'path="{self._prometheus_label(path)}",'
                f'role="{self._prometheus_label(role)}"}} {value}'
            )

        lines.extend(
            [
                "# HELP sharelife_webui_http_error_total Total API errors grouped by error_code/path/role.",
                "# TYPE sharelife_webui_http_error_total counter",
            ]
        )
        for key in sorted(self._http_error_counts):
            code, path, role = key.split("|", 2)
            value = self._http_error_counts[key]
            lines.append(
                "sharelife_webui_http_error_total"
                f'{{error_code="{self._prometheus_label(code)}",'
                f'path="{self._prometheus_label(path)}",'
                f'role="{self._prometheus_label(role)}"}} {value}'
            )

        lines.extend(
            [
                "# HELP sharelife_webui_auth_events_total Authentication and authorization events grouped by event/role.",
                "# TYPE sharelife_webui_auth_events_total counter",
            ]
        )
        for key in sorted(self._auth_event_counts):
            event, role = key.split("|", 1)
            value = self._auth_event_counts[key]
            lines.append(
                "sharelife_webui_auth_events_total"
                f'{{event="{self._prometheus_label(event)}",'
                f'role="{self._prometheus_label(role)}"}} {value}'
            )

        lines.extend(
            [
                "# HELP sharelife_webui_rate_limit_total Rate-limit triggers grouped by scope/role/path.",
                "# TYPE sharelife_webui_rate_limit_total counter",
            ]
        )
        for key in sorted(self._rate_limit_counts):
            scope, role, path = key.split("|", 2)
            value = self._rate_limit_counts[key]
            lines.append(
                "sharelife_webui_rate_limit_total"
                f'{{scope="{self._prometheus_label(scope)}",'
                f'role="{self._prometheus_label(role)}",'
                f'path="{self._prometheus_label(path)}"}} {value}'
            )

        lines.extend(
            [
                "# HELP sharelife_webui_security_alert_total Sensitive-route anomaly alerts emitted to admin notifications.",
                "# TYPE sharelife_webui_security_alert_total counter",
            ]
        )
        for key in sorted(self._security_alert_counts):
            event, role, path = key.split("|", 2)
            value = self._security_alert_counts[key]
            lines.append(
                "sharelife_webui_security_alert_total"
                f'{{event="{self._prometheus_label(event)}",'
                f'role="{self._prometheus_label(role)}",'
                f'path="{self._prometheus_label(path)}"}} {value}'
            )

        lines.append("")
        return "\n".join(lines)

    def _cors_allow_origins(self) -> list[str]:
        cfg = self._webui_config()
        cors = cfg.get("cors", {}) if isinstance(cfg.get("cors"), dict) else {}
        explicit = _to_string_list(cors.get("allow_origins"))
        if explicit:
            return explicit

        if self._auth_enabled:
            host = str(cfg.get("host", "127.0.0.1") or "127.0.0.1").strip()
            port = max(1, _to_int(cfg.get("port", 8106), 8106))
            candidates = {"127.0.0.1", "localhost", self._display_host(host)}
            origins: list[str] = []
            for item in candidates:
                text = str(item or "").strip()
                if not text:
                    continue
                origins.append(f"http://{text}:{port}")
            return origins

        return ["*"]

    def _setup_app(self) -> None:
        self.app = FastAPI(
            title="Sharelife WebUI",
            description="Sharelife community-first governance console",
            version="0.3.13",
        )
        allow_origins = self._cors_allow_origins()
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=allow_origins,
            allow_credentials="*" not in allow_origins,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        @self.app.middleware("http")
        async def auth_middleware(request: Request, call_next):
            request_id = secrets.token_hex(12)
            started = time.perf_counter()
            path = request.url.path
            method = request.method
            normalized_path = self._normalize_api_path(path)

            def finalize(response, *, error_code: str = "", role: str = ""):
                out = self._apply_security_headers(response)
                anonymous_cookie_subject = str(
                    getattr(request.state, "sharelife_auth_anonymous_subject", "") or "",
                ).strip()
                if anonymous_cookie_subject:
                    out.set_cookie(
                        self._ANONYMOUS_MEMBER_COOKIE_NAME,
                        anonymous_cookie_subject,
                        httponly=True,
                        samesite="lax",
                        path="/",
                    )
                out.headers.setdefault("X-Request-ID", request_id)
                elapsed_ms = (time.perf_counter() - started) * 1000.0
                request_role = str(role or "").strip().lower()
                if not request_role:
                    request_role = str(getattr(request.state, "sharelife_auth_role", "public") or "public").strip().lower()
                if not request_role:
                    request_role = "public"
                self._record_http_metrics(
                    method=method,
                    path=path,
                    status_code=int(getattr(out, "status_code", 0) or 0),
                    duration_ms=elapsed_ms,
                    role=request_role,
                    error_code=error_code,
                )
                logger.info(
                    (
                        "[sharelife] webui_request "
                        f"request_id={request_id} method={method} path={path} "
                        f"status={getattr(out, 'status_code', 0)} role={request_role} "
                        f"duration_ms={elapsed_ms:.2f} error_code={error_code or '-'}"
                    )
                )
                return out

            async def invoke_next(*, role: str) -> Any:
                try:
                    return finalize(await call_next(request), role=role)
                except Exception as exc:
                    logger.warning(
                        (
                            "[sharelife] webui_unhandled_exception "
                            f"request_id={request_id} method={method} path={path} "
                            f"role={role or 'public'} error={type(exc).__name__}: {exc}"
                        )
                    )
                    response = self._error_response(
                        code="internal_server_error",
                        message="internal server error",
                        status_code=500,
                    )
                    return finalize(
                        response,
                        error_code="internal_server_error",
                        role=role or "public",
                    )

            if normalized_path.startswith("/api") and normalized_path != "/api/health":
                rate_limit_role = "public"
                if self._auth_enabled:
                    auth_header = request.headers.get("Authorization", "")
                    token = ""
                    if auth_header.startswith("Bearer "):
                        token = auth_header[7:]
                    elif self._auth_allow_query_token:
                        token = request.query_params.get("token", "")
                    role = self._role_from_token(token)
                    if role in {"member", "reviewer", "admin"}:
                        rate_limit_role = role
                allowed, retry_after = self._api_rate_limit_status(
                    request,
                    rate_limit_role,
                    normalized_path,
                )
                if not allowed:
                    self._record_rate_limit_event(
                        scope="api",
                        role=rate_limit_role,
                        path=normalized_path,
                    )
                    self._maybe_emit_security_alert(
                        request=request,
                        event="api_rate_limited",
                        role=rate_limit_role,
                        path=normalized_path,
                        reason="sensitive_api_rate_limit",
                        threshold=1,
                    )
                    response = self._error_response(
                        code="rate_limited",
                        message="Too many API requests.",
                        status_code=429,
                    )
                    response.headers["Retry-After"] = str(retry_after)
                    return finalize(response, error_code="rate_limited", role=rate_limit_role)

            if not self._auth_enabled:
                return await invoke_next(role="public")

            if self._is_public_api_request(path=normalized_path, method=method):
                return await invoke_next(role="public")
            if not normalized_path.startswith("/api"):
                return await invoke_next(role="public")

            token = self._token_from_request(request)
            session = self._session_from_token(token)
            role = self._normalize_role(str(session.get("role", "") or "")) if isinstance(session, dict) else None
            if role is None:
                if self._is_anonymous_member_api_request(path=normalized_path, method=method):
                    anonymous_subject = self._anonymous_member_subject_from_request(request)
                    if not anonymous_subject:
                        anonymous_subject = self._issue_anonymous_member_subject()
                    request.state.sharelife_auth_role = "member"
                    request.state.sharelife_auth_subject = anonymous_subject
                    request.state.sharelife_auth_device_id = ""
                    request.state.sharelife_auth_anonymous = True
                    request.state.sharelife_auth_anonymous_subject = anonymous_subject
                    self._record_auth_event(event="anonymous_member_session", role="member")
                    return await invoke_next(role="member")
                self._record_auth_event(event="unauthorized", role="public")
                self._maybe_emit_security_alert(
                    request=request,
                    event="unauthorized_privileged_route",
                    role="public",
                    path=normalized_path,
                    reason="missing_or_expired_token",
                    threshold=1,
                )
                return finalize(
                    self._error_response(
                        code="unauthorized",
                        message="Unauthorized. Please login first.",
                        status_code=401,
                    ),
                    error_code="unauthorized",
                    role="public",
                )
            request.state.sharelife_auth_role = role
            request.state.sharelife_auth_subject = str(session.get("subject", "") or "") if isinstance(session, dict) else ""
            request.state.sharelife_auth_device_id = str(session.get("device_id", "") or "") if isinstance(session, dict) else ""
            if normalized_path.startswith("/api/admin") and role != "admin":
                if role == "reviewer" and self._reviewer_admin_path_allowed(normalized_path):
                    return await invoke_next(role=role)
                self._record_auth_event(event="forbidden", role=role)
                self._maybe_emit_security_alert(
                    request=request,
                    event="forbidden_admin_route",
                    role=role,
                    path=normalized_path,
                    reason="admin_route_denied",
                    threshold=1,
                )
                return finalize(
                    self._error_response(
                        code="permission_denied",
                        message="permission denied",
                        status_code=403,
                        data={"error": "permission_denied"},
                    ),
                    error_code="permission_denied",
                    role=role,
                )
            if normalized_path.startswith("/api/reviewer") and role not in {"reviewer", "admin"}:
                self._record_auth_event(event="forbidden", role=role)
                self._maybe_emit_security_alert(
                    request=request,
                    event="forbidden_reviewer_route",
                    role=role,
                    path=normalized_path,
                    reason="reviewer_route_denied",
                    threshold=1,
                )
                return finalize(
                    self._error_response(
                        code="permission_denied",
                        message="permission denied",
                        status_code=403,
                        data={"error": "permission_denied"},
                    ),
                    error_code="permission_denied",
                    role=role,
                )
            return await invoke_next(role=role)

        self._register_routes()
        if self.public_market_root.exists():
            self.app.mount(
                "/public-market",
                StaticFiles(directory=str(self.public_market_root), html=False),
                name="sharelife-public-market",
            )
        if self.web_root.exists():
            self.app.mount("/", StaticFiles(directory=str(self.web_root), html=True), name="sharelife-webui")

    @staticmethod
    def _display_host(host: str) -> str:
        normalized = str(host or "").strip()
        if normalized in {"0.0.0.0", "::", "[::]"}:
            return "127.0.0.1"
        return normalized or "127.0.0.1"

    @staticmethod
    def _actor_role(payload: dict[str, Any]) -> str:
        role = str(payload.get("role", "member") or "member").strip().lower()
        if role == "user":
            role = "member"
        if role not in {"member", "reviewer", "admin"}:
            return "member"
        return role

    @staticmethod
    def _user_id(payload: dict[str, Any]) -> str:
        user_id = str(payload.get("user_id", "webui-user") or "webui-user").strip()
        return user_id or "webui-user"

    @staticmethod
    def _session_id(payload: dict[str, Any]) -> str:
        session_id = str(payload.get("session_id", "webui-session") or "webui-session").strip()
        return session_id or "webui-session"

    @staticmethod
    def _request_idempotency_key(request: Request) -> str:
        return str(
            request.headers.get("idempotency-key")
            or request.headers.get("x-idempotency-key")
            or "",
        ).strip()

    @staticmethod
    def _payload_options(payload: dict[str, Any], *, key: str) -> dict[str, Any] | None:
        value = payload.get(key)
        if isinstance(value, dict):
            return value
        return None

    @staticmethod
    def _options_with_idempotency_key(
        options: dict[str, Any] | None,
        *,
        idempotency_key: str,
    ) -> dict[str, Any] | None:
        key = str(idempotency_key or "").strip()
        if not key:
            return options
        merged = dict(options or {})
        merged.setdefault("idempotency_key", key)
        return merged

    def _request_payload_options_with_idempotency(
        self,
        request: Request,
        *,
        payload: dict[str, Any],
        key: str,
    ) -> dict[str, Any] | None:
        return self._options_with_idempotency_key(
            self._payload_options(payload, key=key),
            idempotency_key=self._request_idempotency_key(request),
        )

    @staticmethod
    def _admin_id(payload: dict[str, Any]) -> str:
        admin_id = str(payload.get("admin_id", "webui-admin") or "webui-admin").strip()
        return admin_id or "webui-admin"

    @staticmethod
    def _reviewer_id(payload: dict[str, Any]) -> str:
        reviewer_id = str(payload.get("reviewer_id", "") or "").strip()
        if reviewer_id:
            return reviewer_id
        return str(payload.get("user_id", "webui-reviewer") or "webui-reviewer").strip() or "webui-reviewer"

    @staticmethod
    def _response(result: WebApiResult) -> JSONResponse:
        return JSONResponse(result.to_dict(), status_code=result.status_code)

    @staticmethod
    def _error_response(
        *,
        code: str,
        message: str,
        status_code: int,
        data: dict[str, Any] | None = None,
    ) -> JSONResponse:
        payload: dict[str, Any] = {
            "ok": False,
            "message": message,
            "error": {
                "code": str(code or "request_failed"),
                "message": message,
            },
        }
        if isinstance(data, dict) and data:
            payload["data"] = data
        return JSONResponse(payload, status_code=int(status_code))

    def _apply_security_headers(self, response):
        if not self._security_headers_enabled:
            return response
        for header_name, header_value in self._security_headers.items():
            response.headers.setdefault(header_name, header_value)
        return response

    @staticmethod
    def _public_api_paths() -> set[str]:
        return {
            "/api/auth-info",
            "/api/login",
            "/api/health",
            "/api/ui/capabilities",
            "/api/reviewer/redeem",
            "/api/reviewer/devices/register",
        }

    @staticmethod
    def _public_read_api_paths() -> set[str]:
        return {
            "/api/templates",
            "/api/templates/detail",
            "/api/profile-pack/catalog",
            "/api/profile-pack/catalog/insights",
            "/api/profile-pack/catalog/detail",
            "/api/profile-pack/catalog/compare",
        }

    @staticmethod
    def _anonymous_member_default_api_paths() -> set[tuple[str, str]]:
        return {
            ("POST", "/api/trial"),
            ("GET", "/api/trial/status"),
            ("POST", "/api/templates/install"),
            ("GET", "/api/templates/package/download"),
            ("GET", "/api/member/installations"),
            ("POST", "/api/member/installations/refresh"),
            ("POST", "/api/member/installations/uninstall"),
            ("GET", "/api/member/tasks"),
            ("POST", "/api/member/tasks/refresh"),
            ("GET", "/api/notifications"),
            ("GET", "/api/preferences"),
            ("POST", "/api/preferences/mode"),
            ("POST", "/api/preferences/observe"),
        }

    @classmethod
    def _parse_anonymous_member_allowlist(cls, value: Any) -> set[tuple[str, str]]:
        out: set[tuple[str, str]] = set()
        allowed_methods = {
            "GET",
            "HEAD",
            "POST",
            "PUT",
            "PATCH",
            "DELETE",
            "OPTIONS",
        }
        for item in _to_string_list(value):
            parts = str(item or "").strip().split(None, 1)
            if len(parts) != 2:
                continue
            method = str(parts[0] or "").strip().upper()
            path = cls._normalize_api_path(parts[1])
            if method not in allowed_methods:
                continue
            if not path.startswith("/api/"):
                continue
            out.add((method, path))
        return out

    @staticmethod
    def _normalize_api_path(path: str) -> str:
        text = str(path or "").strip() or "/"
        if not text.startswith("/"):
            text = f"/{text}"
        if len(text) > 1 and text.endswith("/"):
            text = text[:-1]
        return text

    @classmethod
    def _is_public_api_request(cls, *, path: str, method: str) -> bool:
        normalized_path = cls._normalize_api_path(path)
        if normalized_path in cls._public_api_paths():
            return True
        normalized_method = str(method or "GET").strip().upper() or "GET"
        if normalized_method in {"GET", "HEAD"} and normalized_path in cls._public_read_api_paths():
            return True
        return False

    def _is_anonymous_member_api_request(self, *, path: str, method: str) -> bool:
        if not self._auth_allow_anonymous_member:
            return False
        normalized_path = self._normalize_api_path(path)
        normalized_method = str(method or "GET").strip().upper() or "GET"
        if self._runtime_feature_payload()["allow_anonymous_local_astrbot_import"]:
            if (
                normalized_method == "GET"
                and normalized_path == "/api/member/profile-pack/imports/local-astrbot/probe"
            ):
                return True
            if (
                normalized_method == "POST"
                and normalized_path == "/api/member/profile-pack/imports/local-astrbot"
            ):
                return True
            if normalized_method == "GET" and normalized_path == "/api/member/profile-pack/imports":
                return True
            if (
                normalized_method == "DELETE"
                and normalized_path.startswith("/api/member/profile-pack/imports/")
            ):
                return True
        return (normalized_method, normalized_path) in self._auth_anonymous_member_allowlist

    def _local_astrbot_import_enabled(self) -> bool:
        return self._feature_local_astrbot_import

    @staticmethod
    def _reviewer_admin_path_allowed(path: str) -> bool:
        normalized = str(path or "").strip().lower()
        if not normalized.startswith("/api/admin"):
            return False
        allowed_prefixes = (
            "/api/admin/submissions",
            "/api/admin/profile-pack/submissions",
        )
        return any(normalized.startswith(prefix) for prefix in allowed_prefixes)

    def _revoke_reviewer_tokens(self, reviewer_id: str, *, exclude_token: str = "") -> None:
        uid = str(reviewer_id or "").strip()
        if not uid:
            return
        service = self._reviewer_auth_service()
        if service is None:
            return
        excluded_session_id = ""
        keep = str(exclude_token or "").strip()
        if keep:
            session = service.resolve_session(keep)
            if isinstance(session, dict):
                excluded_session_id = str(session.get("session_id", "") or "").strip()
        service.revoke_reviewer_sessions(
            uid,
            exclude_session_id=excluded_session_id,
        )

    def _revoke_reviewer_sessions(
        self,
        reviewer_id: str,
        *,
        device_id: str = "",
        session_id: str = "",
        exclude_token: str = "",
    ) -> dict[str, Any]:
        service = self._reviewer_auth_service()
        uid = str(reviewer_id or "").strip()
        target_device_id = str(device_id or "").strip()
        target_session_id = str(session_id or "").strip()
        if service is None:
            return {
                "reviewer_id": uid,
                "device_id": target_device_id,
                "session_id": target_session_id,
                "revoked_sessions": 0,
                "revoked_device_ids": [],
                "revoked_session_ids": [],
            }
        excluded_session_id = ""
        keep = str(exclude_token or "").strip()
        if keep:
            session = service.resolve_session(keep)
            if isinstance(session, dict):
                excluded_session_id = str(session.get("session_id", "") or "").strip()
        return service.revoke_reviewer_sessions(
            uid,
            device_id=target_device_id,
            session_id=target_session_id,
            exclude_session_id=excluded_session_id,
        )

    def _list_reviewer_sessions(
        self,
        reviewer_id: str,
        *,
        device_id: str = "",
    ) -> list[dict[str, Any]]:
        service = self._reviewer_auth_service()
        if service is None:
            return []
        return service.list_reviewer_sessions(
            str(reviewer_id or "").strip(),
            device_id=str(device_id or "").strip(),
        )

    def _request_role(self, request: Request, payload: dict[str, Any] | None = None) -> str:
        if self._auth_enabled:
            role = str(getattr(request.state, "sharelife_auth_role", "member") or "member").strip().lower()
            if role in {"member", "reviewer", "admin"}:
                return role
            return "member"
        if payload is not None:
            return self._actor_role(payload)
        return self._actor_role({"role": request.query_params.get("role", "member")})

    def _request_reviewer_id(self, request: Request, payload: dict[str, Any] | None = None) -> str:
        if self._auth_enabled:
            role = self._request_role(request, payload)
            if role == "reviewer":
                reviewer_id = str(getattr(request.state, "sharelife_auth_subject", "") or "").strip()
                if reviewer_id:
                    return reviewer_id
            if role == "admin" and payload is not None:
                return str(payload.get("reviewer_id", "") or "").strip()
            return ""
        if payload is not None:
            return self._reviewer_id(payload)
        return str(request.query_params.get("reviewer_id", "webui-reviewer") or "webui-reviewer").strip() or "webui-reviewer"

    def _request_member_user_id(
        self,
        request: Request,
        *,
        payload: dict[str, Any] | None = None,
        query_user_id: str = "",
        enforce_owner_binding: bool = True,
    ) -> tuple[str | None, JSONResponse | None]:
        requested_user_id = ""
        if isinstance(payload, dict):
            requested_user_id = str(payload.get("user_id", "") or "").strip()
        elif query_user_id:
            requested_user_id = str(query_user_id or "").strip()
        fallback_user_id = requested_user_id or "webui-user"
        if not self._auth_enabled:
            return fallback_user_id, None
        role = self._request_role(request, payload)
        if role != "member":
            return fallback_user_id, None
        member_subject = str(getattr(request.state, "sharelife_auth_subject", "") or "").strip()
        is_anonymous_member = False
        if self._auth_allow_anonymous_member and _to_bool(
            getattr(request.state, "sharelife_auth_anonymous", False),
            default=False,
        ):
            is_anonymous_member = True
            if not member_subject:
                member_subject = self._auth_anonymous_member_user_id
        if not member_subject:
            return None, self._error_response(
                code="unauthorized",
                message="Unauthorized. Please login first.",
                status_code=401,
            )
        allow_legacy_anonymous_alias = (
            is_anonymous_member
            and requested_user_id
            and requested_user_id == self._auth_anonymous_member_user_id
        )
        if (
            (enforce_owner_binding or is_anonymous_member)
            and requested_user_id
            and requested_user_id != member_subject
            and not allow_legacy_anonymous_alias
        ):
            self._record_auth_event(event="owner_scope_denied", role="member")
            return None, self._error_response(
                code="permission_denied",
                message="permission denied",
                status_code=403,
                data={"error": "permission_denied"},
            )
        if enforce_owner_binding or is_anonymous_member:
            return member_subject, None
        return (requested_user_id or member_subject), None

    def _page_request_role(self, request: Request) -> str | None:
        if not self._auth_enabled:
            return None
        token = self._token_from_request(request)
        session = self._session_from_token(token)
        role = self._normalize_role(str(session.get("role", "") or "")) if isinstance(session, dict) else None
        if role is None:
            return None
        request.state.sharelife_auth_role = role
        request.state.sharelife_auth_subject = str(session.get("subject", "") or "")
        request.state.sharelife_auth_device_id = str(session.get("device_id", "") or "")
        return role

    def _authorize_console_page(
        self,
        request: Request,
        *,
        allowed_roles: set[str],
        denied_event: str,
    ) -> JSONResponse | None:
        if not self._auth_enabled:
            return self._error_response(
                code="permission_denied",
                message="permission denied",
                status_code=403,
                data={"error": "permission_denied"},
            )
        role = self._page_request_role(request)
        path = self._normalize_api_path(request.url.path)
        if role is None:
            self._record_auth_event(event="unauthorized", role="public")
            self._maybe_emit_security_alert(
                request=request,
                event="unauthorized_privileged_route",
                role="public",
                path=path,
                reason="missing_or_expired_token",
                threshold=1,
            )
            return self._error_response(
                code="unauthorized",
                message="Unauthorized. Please login first.",
                status_code=401,
            )
        if role not in allowed_roles:
            self._record_auth_event(event="forbidden", role=role)
            self._maybe_emit_security_alert(
                request=request,
                event=denied_event,
                role=role,
                path=path,
                reason="console_route_denied",
                threshold=1,
            )
            return self._error_response(
                code="permission_denied",
                message="permission denied",
                status_code=403,
                data={"error": "permission_denied"},
            )
        return None

    def _register_routes(self) -> None:
        @self.app.get("/")
        @self.app.get("/index.html")
        async def console_page():
            return RedirectResponse(url="/member", status_code=307)

        @self.app.get("/member.html")
        async def member_console_page_legacy():
            return RedirectResponse(url="/member", status_code=307)

        @self.app.get("/member")
        @self.app.get("/member/")
        @self.app.get("/user")
        @self.app.get("/user/")
        async def member_console_page():
            member_path = self.web_root / "member.safe.html"
            if not member_path.exists():
                member_path = self.web_root / "member.html"
            if not member_path.exists():
                member_path = self.web_root / "index.html"
            if not member_path.exists():
                return JSONResponse(
                    {
                        "ok": False,
                        "message": "member console page not found",
                        "error": {
                            "code": "webui_page_not_found",
                            "message": "member console page not found",
                        },
                    },
                    status_code=404,
                )
            return FileResponse(path=member_path, media_type="text/html")

        @self.app.get("/admin.html")
        async def admin_console_page_legacy():
            return RedirectResponse(url="/admin", status_code=307)

        @self.app.get("/admin")
        @self.app.get("/admin/")
        async def admin_console_page(request: Request):
            denied = self._authorize_console_page(
                request,
                allowed_roles={"admin"},
                denied_event="forbidden_admin_route",
            )
            if denied is not None:
                return denied
            admin_path = self.web_root / "admin.html"
            if not admin_path.exists():
                admin_path = self.web_root / "index.html"
            if not admin_path.exists():
                return JSONResponse(
                    {
                        "ok": False,
                        "message": "admin console page not found",
                        "error": {
                            "code": "webui_page_not_found",
                            "message": "admin console page not found",
                        },
                    },
                    status_code=404,
                )
            return FileResponse(path=admin_path, media_type="text/html")

        @self.app.get("/reviewer.html")
        async def reviewer_console_page_legacy():
            return RedirectResponse(url="/reviewer", status_code=307)

        @self.app.get("/reviewer")
        @self.app.get("/reviewer/")
        async def reviewer_console_page(request: Request):
            denied = self._authorize_console_page(
                request,
                allowed_roles={"reviewer", "admin"},
                denied_event="forbidden_reviewer_route",
            )
            if denied is not None:
                return denied
            reviewer_path = self.web_root / "reviewer.html"
            if not reviewer_path.exists():
                reviewer_path = self.web_root / "index.html"
            if not reviewer_path.exists():
                return JSONResponse(
                    {
                        "ok": False,
                        "message": "reviewer console page not found",
                        "error": {
                            "code": "webui_page_not_found",
                            "message": "reviewer console page not found",
                        },
                    },
                    status_code=404,
                )
            return FileResponse(path=reviewer_path, media_type="text/html")

        @self.app.get("/market")
        @self.app.get("/market/")
        async def market_page():
            market_path = self.web_root / "market.html"
            if not market_path.exists():
                return JSONResponse(
                    {
                        "ok": False,
                        "message": "market page not found",
                        "error": {
                            "code": "webui_page_not_found",
                            "message": "market page not found",
                        },
                    },
                    status_code=404,
                )
            return FileResponse(path=market_path, media_type="text/html")

        @self.app.get("/market/packs/{pack_id:path}")
        async def market_detail_page(pack_id: str):
            market_detail_path = self.web_root / "market_detail.html"
            if not market_detail_path.exists():
                return JSONResponse(
                    {
                        "ok": False,
                        "message": "market detail page not found",
                        "error": {
                            "code": "webui_page_not_found",
                            "message": "market detail page not found",
                        },
                    },
                    status_code=404,
                )
            return FileResponse(path=market_detail_path, media_type="text/html")

        @self.app.get("/api/auth-info")
        async def auth_info():
            return {
                "ok": True,
                "auth_required": self._auth_enabled,
                "available_roles": self._available_auth_roles(),
                "invalid_roles": sorted(self._invalid_auth_roles),
                "token_ttl_seconds": self._auth_token_ttl_seconds,
                "reviewer_token_ttl_seconds": self._reviewer_token_ttl_seconds,
                "allow_query_token": self._auth_allow_query_token,
                "allow_anonymous_member": self._auth_allow_anonymous_member,
                "anonymous_member_user_id": self._auth_anonymous_member_user_id,
                "anonymous_member_allowlist": sorted(
                    f"{method} {path}"
                    for method, path in self._auth_anonymous_member_allowlist
                ),
                **self._runtime_feature_payload(),
            }

        @self.app.get("/api/ui/capabilities")
        async def ui_capabilities(request: Request, page_mode: str = ""):
            return self._ui_capability_payload(request, page_mode=page_mode)

        @self.app.post("/api/login")
        async def login(request: Request, payload: dict[str, Any]):
            if not self._auth_enabled:
                return {
                    "ok": True,
                    "auth_required": False,
                    "token": "no-auth",
                    "role": "member",
                    "available_roles": [],
                }
            role = self._actor_role(payload)
            if not self._login_rate_limit_allowed(request, role):
                self._record_rate_limit_event(
                    scope="login",
                    role=role,
                    path="/api/login",
                )
                self._record_auth_event(event="login_blocked", role=role)
                self._maybe_emit_security_alert(
                    request=request,
                    event="login_rate_limited",
                    role=role,
                    path="/api/login",
                    reason="login_rate_limit_triggered",
                    threshold=1,
                )
                return self._error_response(
                    code="rate_limited",
                    message="Too many login attempts.",
                    status_code=429,
                )
            provided = str(payload.get("password", "") or "")
            reviewer_auth_service = self._reviewer_auth_service()
            if reviewer_auth_service is None:
                return self._error_response(
                    code="reviewer_auth_service_unavailable",
                    message="reviewer auth service unavailable",
                    status_code=503,
                )
            member_user_id = ""
            reviewer_id = ""
            reviewer_device_id = ""
            if role == "member":
                member_user_id = self._user_id(payload)
            if role == "reviewer":
                reviewer_id = self._reviewer_id(payload)
                reviewer_device_key = str(payload.get("reviewer_device_key", "") or "").strip()
                if not reviewer_id:
                    return self._error_response(
                        code="reviewer_id_required",
                        message="reviewer_id is required",
                        status_code=400,
                    )
                device = reviewer_auth_service.resolve_device(user_id=reviewer_id, key=reviewer_device_key)
                if device is None:
                    self._record_auth_event(event="invalid_reviewer_device", role=role)
                    self._maybe_emit_security_alert(
                        request=request,
                        event="invalid_reviewer_device",
                        role=role,
                        path="/api/login",
                        reason="reviewer_device_key_invalid",
                        threshold=1,
                    )
                    return self._error_response(
                        code="invalid_reviewer_device",
                        message="reviewer device key is invalid",
                        status_code=401,
                    )
                reviewer_device_id = str(device.get("device_id", "") or "").strip()
            if role not in self._active_auth_roles:
                self._record_login_failure(request, role)
                return self._error_response(
                    code="invalid_credentials",
                    message="Password is incorrect.",
                    status_code=401,
                )
            if reviewer_auth_service.verify_bootstrap_password(role, provided):
                self._clear_login_failures(request, role)
                self._record_auth_event(event="login_success", role=role)
                if role == "reviewer":
                    reviewer_auth_service.mark_device_used(
                        user_id=reviewer_id,
                        device_id=reviewer_device_id,
                    )
                return {
                    "ok": True,
                    "auth_required": True,
                    "token": self._issue_token(
                        role,
                        subject=(
                            reviewer_id
                            if role == "reviewer"
                            else member_user_id if role == "member" else ""
                        ),
                        device_id=reviewer_device_id if role == "reviewer" else "",
                    ),
                    "role": role,
                    "user_id": member_user_id if role == "member" else "",
                    "reviewer_id": reviewer_id if role == "reviewer" else "",
                    "reviewer_device_id": reviewer_device_id if role == "reviewer" else "",
                    "available_roles": self._available_auth_roles(),
                }
            self._record_login_failure(request, role)
            self._record_auth_event(event="login_invalid_credentials", role=role)
            self._maybe_emit_security_alert(
                request=request,
                event="login_invalid_credentials",
                role=role,
                path="/api/login",
                reason="invalid_password",
            )
            return self._error_response(
                code="invalid_credentials",
                message="Password is incorrect.",
                status_code=401,
            )

        @self.app.get("/api/health")
        async def health():
            return {
                "ok": True,
                "webui_url": self.public_url,
                "auth_required": self._auth_enabled,
                "available_roles": self._available_auth_roles(),
                "invalid_roles": sorted(self._invalid_auth_roles),
                "running": self.is_running(),
            }

        @self.app.get("/api/private-docs")
        async def list_private_docs(request: Request):
            role = str(getattr(request.state, "sharelife_auth_role", "") or "").strip().lower()
            if not self._auth_enabled or role not in self._private_docs_allowed_roles():
                return self._error_response(
                    code="permission_denied",
                    message="permission denied",
                    status_code=403,
                    data={"error": "permission_denied"},
                )
            return {
                "ok": True,
                "available": self.private_docs_root.exists(),
                "allowed_roles": sorted(self._private_docs_allowed_roles()),
                "documents": self._list_private_docs(),
            }

        @self.app.get("/api/private-docs/content")
        async def get_private_doc_content(request: Request, path: str = ""):
            role = str(getattr(request.state, "sharelife_auth_role", "") or "").strip().lower()
            if not self._auth_enabled or role not in self._private_docs_allowed_roles():
                return self._error_response(
                    code="permission_denied",
                    message="permission denied",
                    status_code=403,
                    data={"error": "permission_denied"},
                )
            resolved = self._resolve_private_doc_path(path)
            if resolved is None:
                return self._error_response(
                    code="private_doc_not_found",
                    message="private doc not found",
                    status_code=404,
                )
            return {
                "ok": True,
                "path": str(resolved.relative_to(self.private_docs_root.resolve()).as_posix()),
                "size_bytes": int(resolved.stat().st_size),
                "content": resolved.read_text(encoding="utf-8"),
            }

        @self.app.post("/api/reviewer/invites")
        async def reviewer_invites_create(request: Request, payload: dict[str, Any]):
            return self._response(
                self.api.admin_create_reviewer_invite(
                    role=self._request_role(request, payload),
                    admin_id=self._admin_id(payload),
                    expires_in_seconds=_to_int(payload.get("expires_in_seconds"), 3600),
                )
            )

        @self.app.get("/api/reviewer/invites")
        async def reviewer_invites_list(request: Request, status: str = ""):
            return self._response(
                self.api.admin_list_reviewer_invites(
                    role=self._request_role(request),
                    status=status,
                )
            )

        @self.app.post("/api/reviewer/invites/revoke")
        async def reviewer_invites_revoke(request: Request, payload: dict[str, Any]):
            return self._response(
                self.api.admin_revoke_reviewer_invite(
                    role=self._request_role(request, payload),
                    invite_code=str(payload.get("invite_code", "") or ""),
                    admin_id=self._admin_id(payload),
                )
            )

        @self.app.post("/api/reviewer/redeem")
        async def reviewer_redeem(payload: dict[str, Any]):
            return self._response(
                self.api.reviewer_redeem_invite(
                    invite_code=str(payload.get("invite_code", "") or ""),
                    reviewer_id=self._reviewer_id(payload),
                )
            )

        @self.app.post("/api/reviewer/devices/register")
        async def reviewer_device_register(request: Request, payload: dict[str, Any]):
            role = self._request_role(request, payload)
            reviewer_id = self._request_reviewer_id(request, payload)
            if self._auth_enabled and role not in {"reviewer", "admin"}:
                provided = str(payload.get("password", "") or "")
                reviewer_auth_service = self._reviewer_auth_service()
                if reviewer_auth_service is None or not reviewer_auth_service.verify_bootstrap_password(
                    "reviewer",
                    provided,
                ):
                    return self._error_response(
                        code="invalid_credentials",
                        message="Password is incorrect.",
                        status_code=401,
                    )
                reviewer_id = self._reviewer_id(payload)
            return self._response(
                self.api.reviewer_register_device(
                    reviewer_id=reviewer_id,
                    label=str(payload.get("label", "") or ""),
                )
            )

        @self.app.get("/api/reviewer/devices")
        async def reviewer_devices(request: Request, reviewer_id: str = ""):
            role = self._request_role(request)
            resolved_reviewer_id = reviewer_id.strip()
            if role == "reviewer":
                resolved_reviewer_id = self._request_reviewer_id(request)
            if not resolved_reviewer_id:
                resolved_reviewer_id = self._request_reviewer_id(request)
            return self._response(
                self.api.reviewer_list_devices(
                    reviewer_id=resolved_reviewer_id,
                )
            )

        @self.app.delete("/api/reviewer/devices/{device_id}")
        async def reviewer_revoke_device(request: Request, device_id: str, reviewer_id: str = ""):
            role = self._request_role(request)
            resolved_reviewer_id = reviewer_id.strip()
            if role == "reviewer":
                resolved_reviewer_id = self._request_reviewer_id(request)
            if not resolved_reviewer_id:
                resolved_reviewer_id = self._request_reviewer_id(request)
            result = self.api.reviewer_revoke_device(
                reviewer_id=resolved_reviewer_id,
                device_id=device_id,
            )
            token = self._token_from_request(request)
            if result.ok and role == "reviewer":
                token_session = self._session_from_token(token)
                session_device_id = str(token_session.get("device_id", "") or "").strip() if isinstance(token_session, dict) else ""
                if session_device_id and session_device_id == str(device_id or "").strip():
                    self._revoke_token(
                        token,
                        role="reviewer",
                        subject=resolved_reviewer_id,
                        device_id=session_device_id,
                    )
            return self._response(result)

        @self.app.get("/api/reviewer/accounts")
        async def reviewer_accounts(request: Request):
            return self._response(
                self.api.admin_list_reviewers(
                    role=self._request_role(request),
                )
            )

        @self.app.post("/api/reviewer/accounts/reset-devices")
        async def reviewer_reset_devices(request: Request, payload: dict[str, Any]):
            reviewer_id = self._reviewer_id(payload)
            result = self.api.admin_force_reset_reviewer_devices(
                role=self._request_role(request, payload),
                reviewer_id=reviewer_id,
                admin_id=self._admin_id(payload),
            )
            if result.ok:
                self._revoke_reviewer_tokens(reviewer_id=reviewer_id)
            return self._response(result)

        @self.app.post("/api/admin/reviewer/sessions/revoke")
        async def admin_reviewer_sessions_revoke(request: Request, payload: dict[str, Any]):
            reviewer_id = str(payload.get("reviewer_id", "") or "").strip()
            if not reviewer_id:
                return self._error_response(
                    code="reviewer_id_required",
                    message="reviewer_id is required",
                    status_code=400,
                )
            device_id = str(payload.get("device_id", "") or "").strip()
            session_id = str(payload.get("session_id", "") or "").strip()
            summary = self._revoke_reviewer_sessions(
                reviewer_id=reviewer_id,
                device_id=device_id,
                session_id=session_id,
            )
            result = self.api.admin_record_reviewer_session_revoke(
                role=self._request_role(request, payload),
                reviewer_id=reviewer_id,
                admin_id=self._admin_id(payload),
                revoked_sessions=int(summary.get("revoked_sessions", 0) or 0),
                device_id=device_id,
                session_id=session_id,
            )
            if isinstance(result.data, dict):
                result.data["revoked_device_ids"] = list(summary.get("revoked_device_ids", []))
                result.data["revoked_session_ids"] = list(summary.get("revoked_session_ids", []))
            return self._response(result)

        @self.app.get("/api/admin/reviewer/sessions")
        async def admin_reviewer_sessions(request: Request, reviewer_id: str = "", device_id: str = ""):
            role = self._request_role(request)
            if role != "admin":
                return self._error_response(
                    code="permission_denied",
                    message="permission denied",
                    status_code=403,
                    data={"error": "permission_denied"},
                )
            normalized_reviewer_id = str(reviewer_id or "").strip()
            if not normalized_reviewer_id:
                return self._error_response(
                    code="reviewer_id_required",
                    message="reviewer_id is required",
                    status_code=400,
                )
            normalized_device_id = str(device_id or "").strip()
            sessions = self._list_reviewer_sessions(
                normalized_reviewer_id,
                device_id=normalized_device_id,
            )
            return self._response(
                WebApiResult(
                    ok=True,
                    message="reviewer sessions listed",
                    data={
                        "reviewer_id": normalized_reviewer_id,
                        "device_id": normalized_device_id,
                        "sessions": sessions,
                        "count": len(sessions),
                    },
                )
            )

        @self.app.get("/api/reviewer/session")
        async def reviewer_session(request: Request):
            role = self._request_role(request)
            if role not in {"reviewer", "admin"}:
                return self._error_response(
                    code="permission_denied",
                    message="permission denied",
                    status_code=403,
                    data={"error": "permission_denied"},
                )
            return {
                "ok": True,
                "role": role,
                "reviewer_id": str(getattr(request.state, "sharelife_auth_subject", "") or ""),
                "device_id": str(getattr(request.state, "sharelife_auth_device_id", "") or ""),
            }

        @self.app.post("/api/reviewer/session/logout")
        async def reviewer_session_logout(request: Request):
            token = self._token_from_request(request)
            session = self._session_from_token(token)
            if isinstance(session, dict):
                self._revoke_token(
                    token,
                    role=str(session.get("role", "") or ""),
                    subject=str(session.get("subject", "") or ""),
                )
            return {"ok": True, "message": "logged out"}

        @self.app.get("/api/metrics")
        async def metrics():
            return PlainTextResponse(
                self._prometheus_metrics_text(),
                media_type="text/plain; version=0.0.4; charset=utf-8",
            )

        @self.app.get("/api/preferences")
        async def get_preferences(request: Request, user_id: str = ""):
            normalized_user_id, denied = self._request_member_user_id(
                request,
                query_user_id=user_id,
                enforce_owner_binding=False,
            )
            if denied is not None or normalized_user_id is None:
                return denied
            return self._response(self.api.get_preferences(user_id=normalized_user_id))

        @self.app.post("/api/preferences/mode")
        async def set_preference_mode(request: Request, payload: dict[str, Any]):
            normalized_user_id, denied = self._request_member_user_id(
                request,
                payload=payload,
                enforce_owner_binding=False,
            )
            if denied is not None or normalized_user_id is None:
                return denied
            return self._response(
                self.api.set_preference_mode(
                    user_id=normalized_user_id,
                    mode=str(payload.get("mode", "") or ""),
                )
            )

        @self.app.post("/api/preferences/observe")
        async def set_preference_observe(request: Request, payload: dict[str, Any]):
            normalized_user_id, denied = self._request_member_user_id(
                request,
                payload=payload,
                enforce_owner_binding=False,
            )
            if denied is not None or normalized_user_id is None:
                return denied
            return self._response(
                self.api.set_preference_observe(
                    user_id=normalized_user_id,
                    enabled=_to_bool(payload.get("enabled"), default=False),
                )
            )

        @self.app.get("/api/templates")
        async def list_templates(
            template_id: str = "",
            risk_level: str = "",
            review_label: str = "",
            warning_flag: str = "",
            category: str = "",
            tag: str = "",
            source_channel: str = "",
            sort_by: str = "",
            sort_order: str = "",
        ):
            return self._response(
                self.api.list_templates(
                    template_query=template_id,
                    risk_level=risk_level,
                    review_label=review_label,
                    warning_flag=warning_flag,
                    category=category,
                    tag=tag,
                    source_channel=source_channel,
                    sort_by=sort_by,
                    sort_order=sort_order,
                )
            )

        @self.app.get("/api/templates/detail")
        async def template_detail(template_id: str = ""):
            return self._response(self.api.get_template_detail(template_id=template_id))

        @self.app.post("/api/templates/submit")
        async def submit_template(request: Request):
            raw_content_length = str(request.headers.get("content-length", "") or "").strip()
            if raw_content_length:
                try:
                    if int(raw_content_length) > self._submission_request_limit_bytes():
                        return self._error_response(
                            code="package_too_large",
                            message="package exceeds 20 MiB limit",
                            status_code=413,
                            data={"max_size_bytes": self._submission_package_limit_bytes()},
                        )
                except Exception:
                    pass
            try:
                payload = await request.json()
            except Exception:
                return self._error_response(
                    code="invalid_json",
                    message="invalid json payload",
                    status_code=400,
                )
            if not isinstance(payload, dict):
                return self._error_response(
                    code="invalid_json",
                    message="invalid json payload",
                    status_code=400,
                )
            package_name = str(payload.get("package_name", "") or "").strip()
            package_base64 = str(payload.get("package_base64", "") or "").strip()
            upload_options = self._request_payload_options_with_idempotency(
                request,
                payload=payload,
                key="upload_options",
            )
            user_id, denied = self._request_member_user_id(request, payload=payload)
            if denied is not None or user_id is None:
                return denied
            if package_name and package_base64:
                return self._response(
                    self.api.submit_template_package(
                        user_id=user_id,
                        template_id=str(payload.get("template_id", "") or ""),
                        version=str(payload.get("version", "1.0.0") or "1.0.0"),
                        filename=package_name,
                        content_base64=package_base64,
                        upload_options=upload_options,
                    )
                )
            return self._response(
                self.api.submit_template(
                    user_id=user_id,
                    template_id=str(payload.get("template_id", "") or ""),
                    version=str(payload.get("version", "1.0.0") or "1.0.0"),
                    upload_options=upload_options,
                )
            )

        @self.app.post("/api/trial")
        async def request_trial(request: Request, payload: dict[str, Any]):
            normalized_user_id, denied = self._request_member_user_id(
                request,
                payload=payload,
            )
            if denied is not None or normalized_user_id is None:
                return denied
            return self._response(
                self.api.request_trial(
                    user_id=normalized_user_id,
                    session_id=self._session_id(payload),
                    template_id=str(payload.get("template_id", "") or ""),
                )
            )

        @self.app.get("/api/trial/status")
        async def trial_status(
            request: Request,
            user_id: str = "",
            session_id: str = "webui-session",
            template_id: str = "",
        ):
            normalized_user_id, denied = self._request_member_user_id(
                request,
                query_user_id=user_id,
            )
            if denied is not None or normalized_user_id is None:
                return denied
            return self._response(
                self.api.get_trial_status(
                    user_id=normalized_user_id,
                    session_id=session_id,
                    template_id=template_id,
                )
            )

        @self.app.get("/api/member/installations")
        async def member_installations(
            request: Request,
            user_id: str = "",
            limit: int = 50,
        ):
            normalized_user_id, denied = self._request_member_user_id(
                request,
                query_user_id=user_id,
            )
            if denied is not None or normalized_user_id is None:
                return denied
            return self._response(
                self.api.list_member_installations(
                    user_id=normalized_user_id,
                    limit=limit,
                )
            )

        @self.app.post("/api/member/installations/refresh")
        async def member_installations_refresh(request: Request, payload: dict[str, Any]):
            normalized_user_id, denied = self._request_member_user_id(
                request,
                payload=payload,
            )
            if denied is not None or normalized_user_id is None:
                return denied
            return self._response(
                self.api.refresh_member_installations(
                    user_id=normalized_user_id,
                    limit=_to_int(payload.get("limit"), 50),
                )
            )

        @self.app.get("/api/member/tasks")
        async def member_tasks(
            request: Request,
            user_id: str = "",
            limit: int = 50,
        ):
            normalized_user_id, denied = self._request_member_user_id(
                request,
                query_user_id=user_id,
            )
            if denied is not None or normalized_user_id is None:
                return denied
            return self._response(
                self.api.list_member_tasks(
                    user_id=normalized_user_id,
                    limit=limit,
                )
            )

        @self.app.post("/api/member/tasks/refresh")
        async def member_tasks_refresh(request: Request, payload: dict[str, Any]):
            normalized_user_id, denied = self._request_member_user_id(
                request,
                payload=payload,
            )
            if denied is not None or normalized_user_id is None:
                return denied
            return self._response(
                self.api.refresh_member_tasks(
                    user_id=normalized_user_id,
                    limit=_to_int(payload.get("limit"), 50),
                )
            )

        @self.app.get("/api/member/transfers")
        async def member_transfers(
            request: Request,
            user_id: str = "",
            direction: str = "",
            status: str = "",
            limit: int = 50,
        ):
            normalized_user_id, denied = self._request_member_user_id(
                request,
                query_user_id=user_id,
            )
            if denied is not None or normalized_user_id is None:
                return denied
            return self._response(
                self.api.list_member_transfer_jobs(
                    user_id=normalized_user_id,
                    direction=direction,
                    status=status,
                    limit=limit,
                )
            )

        @self.app.post("/api/member/transfers/refresh")
        async def member_transfers_refresh(request: Request, payload: dict[str, Any]):
            normalized_user_id, denied = self._request_member_user_id(
                request,
                payload=payload,
            )
            if denied is not None or normalized_user_id is None:
                return denied
            return self._response(
                self.api.refresh_member_transfer_jobs(
                    user_id=normalized_user_id,
                    direction=str(payload.get("direction", "") or ""),
                    status=str(payload.get("status", "") or ""),
                    limit=_to_int(payload.get("limit"), 50),
                )
            )

        @self.app.post("/api/member/installations/uninstall")
        async def member_installations_uninstall(request: Request, payload: dict[str, Any]):
            normalized_user_id, denied = self._request_member_user_id(
                request,
                payload=payload,
            )
            if denied is not None or normalized_user_id is None:
                return denied
            return self._response(
                self.api.uninstall_member_installation(
                    user_id=normalized_user_id,
                    template_id=str(payload.get("template_id", "") or ""),
                )
            )

        @self.app.get("/api/member/submissions")
        async def member_submissions(
            request: Request,
            user_id: str = "",
            status: str = "",
            template_id: str = "",
            risk_level: str = "",
            review_label: str = "",
            warning_flag: str = "",
        ):
            normalized_user_id, denied = self._request_member_user_id(
                request,
                query_user_id=user_id,
            )
            if denied is not None or normalized_user_id is None:
                return denied
            return self._response(
                self.api.member_list_submissions(
                    user_id=normalized_user_id,
                    status=status,
                    template_query=template_id,
                    risk_level=risk_level,
                    review_label=review_label,
                    warning_flag=warning_flag,
                )
            )

        @self.app.get("/api/member/submissions/detail")
        async def member_submission_detail(
            request: Request,
            submission_id: str = "",
            user_id: str = "",
        ):
            normalized_user_id, denied = self._request_member_user_id(
                request,
                query_user_id=user_id,
            )
            if denied is not None or normalized_user_id is None:
                return denied
            return self._response(
                self.api.member_get_submission_detail(
                    user_id=normalized_user_id,
                    submission_id=submission_id,
                )
            )

        @self.app.get("/api/member/submissions/package/download")
        async def member_download_submission_package(
            request: Request,
            submission_id: str = "",
            user_id: str = "",
        ):
            normalized_user_id, denied = self._request_member_user_id(
                request,
                query_user_id=user_id,
            )
            if denied is not None or normalized_user_id is None:
                return denied
            result = self.api.member_get_submission_package(
                user_id=normalized_user_id,
                submission_id=submission_id,
                idempotency_key=self._request_idempotency_key(request),
            )
            if not result.ok:
                return self._response(result)
            artifact = result.data
            path = Path(str(artifact.get("path", "") or ""))
            if not path.exists():
                return JSONResponse(
                    {
                        "ok": False,
                        "message": "submission package missing",
                        "error": {
                            "code": "submission_package_not_available",
                            "message": "submission package missing",
                        },
                    },
                    status_code=404,
                )
            response = FileResponse(
                path=path,
                media_type="application/zip",
                filename=str(artifact.get("filename", "") or path.name),
            )
            transfer_job = artifact.get("transfer_job", {}) if isinstance(artifact, dict) else {}
            if isinstance(transfer_job, dict):
                job_id = str(transfer_job.get("job_id", "") or "").strip()
                if job_id:
                    response.headers["X-Sharelife-Transfer-Job-Id"] = job_id
                status_value = str(transfer_job.get("status", "") or "").strip()
                if status_value:
                    response.headers["X-Sharelife-Transfer-Status"] = status_value
            return response

        @self.app.post("/api/templates/install")
        async def install_template(request: Request, payload: dict[str, Any]):
            install_options = (
                payload.get("install_options")
                if isinstance(payload.get("install_options"), dict)
                else None
            )
            normalized_user_id, denied = self._request_member_user_id(
                request,
                payload=payload,
            )
            if denied is not None or normalized_user_id is None:
                return denied
            return self._response(
                self.api.install_template(
                    user_id=normalized_user_id,
                    session_id=self._session_id(payload),
                    template_id=str(payload.get("template_id", "") or ""),
                    install_options=install_options,
                )
            )

        @self.app.post("/api/templates/prompt")
        async def prompt_bundle(payload: dict[str, Any]):
            return self._response(
                self.api.generate_prompt_bundle(
                    template_id=str(payload.get("template_id", "") or "")
                )
            )

        @self.app.post("/api/templates/package")
        async def package_bundle(payload: dict[str, Any]):
            return self._response(
                self.api.generate_package(
                    template_id=str(payload.get("template_id", "") or "")
                )
            )

        @self.app.post("/api/profile-pack/submit")
        async def submit_profile_pack(request: Request, payload: dict[str, Any]):
            submit_options = self._request_payload_options_with_idempotency(
                request,
                payload=payload,
                key="submit_options",
            )
            user_id, denied = self._request_member_user_id(request, payload=payload)
            if denied is not None or user_id is None:
                return denied
            return self._response(
                self.api.submit_profile_pack(
                    user_id=user_id,
                    artifact_id=str(payload.get("artifact_id", "") or ""),
                    submit_options=submit_options,
                )
            )

        @self.app.post("/api/member/profile-pack/imports")
        async def member_profile_pack_imports_create(request: Request, payload: dict[str, Any]):
            user_id, denied = self._request_member_user_id(request, payload=payload)
            if denied is not None or user_id is None:
                return denied
            return self._response(
                self.api.member_import_profile_pack(
                    user_id=user_id,
                    filename=str(payload.get("filename", "") or ""),
                    content_base64=str(payload.get("content_base64", "") or ""),
                )
            )

        @self.app.post("/api/member/profile-pack/imports/local-astrbot")
        async def member_profile_pack_imports_local_astrbot_create(
            request: Request,
            payload: dict[str, Any],
        ):
            if not self._local_astrbot_import_enabled():
                return self._error_response(
                    code="feature_disabled",
                    message="local AstrBot import is disabled",
                    status_code=404,
                )
            user_id, denied = self._request_member_user_id(request, payload=payload)
            if denied is not None or user_id is None:
                return denied
            return self._response(
                self.api.member_import_local_astrbot_config(user_id=user_id)
            )

        @self.app.get("/api/member/profile-pack/imports/local-astrbot/probe")
        async def member_profile_pack_imports_local_astrbot_probe(
            request: Request,
            user_id: str = "",
        ):
            if not self._local_astrbot_import_enabled():
                return self._error_response(
                    code="feature_disabled",
                    message="local AstrBot import is disabled",
                    status_code=404,
                )
            normalized_user_id, denied = self._request_member_user_id(
                request,
                query_user_id=user_id,
            )
            if denied is not None or normalized_user_id is None:
                return denied
            return self._response(
                self.api.member_probe_local_astrbot_config(user_id=normalized_user_id)
            )

        @self.app.get("/api/member/profile-pack/imports")
        async def member_profile_pack_imports_list(
            request: Request,
            user_id: str = "",
            limit: int = 50,
        ):
            normalized_user_id, denied = self._request_member_user_id(
                request,
                query_user_id=user_id,
            )
            if denied is not None or normalized_user_id is None:
                return denied
            return self._response(
                self.api.member_list_profile_pack_imports(
                    user_id=normalized_user_id,
                    limit=limit,
                )
            )

        @self.app.delete("/api/member/profile-pack/imports/{import_id}")
        async def member_profile_pack_import_delete(
            request: Request,
            import_id: str,
            user_id: str = "",
        ):
            normalized_user_id, denied = self._request_member_user_id(
                request,
                query_user_id=user_id,
            )
            if denied is not None or normalized_user_id is None:
                return denied
            return self._response(
                self.api.member_delete_profile_pack_import(
                    user_id=normalized_user_id,
                    import_id=import_id,
                )
            )

        @self.app.get("/api/member/profile-pack/submissions")
        async def member_profile_pack_submissions(
            request: Request,
            user_id: str = "",
            status: str = "",
            pack_id: str = "",
            pack_type: str = "",
            risk_level: str = "",
            review_label: str = "",
            warning_flag: str = "",
        ):
            normalized_user_id, denied = self._request_member_user_id(
                request,
                query_user_id=user_id,
            )
            if denied is not None or normalized_user_id is None:
                return denied
            return self._response(
                self.api.member_list_profile_pack_submissions(
                    user_id=normalized_user_id,
                    status=status,
                    pack_query=pack_id,
                    pack_type=pack_type,
                    risk_level=risk_level,
                    review_label=review_label,
                    warning_flag=warning_flag,
                )
            )

        @self.app.get("/api/member/profile-pack/submissions/detail")
        async def member_profile_pack_submission_detail(
            request: Request,
            submission_id: str = "",
            user_id: str = "",
        ):
            normalized_user_id, denied = self._request_member_user_id(
                request,
                query_user_id=user_id,
            )
            if denied is not None or normalized_user_id is None:
                return denied
            return self._response(
                self.api.member_get_profile_pack_submission_detail(
                    user_id=normalized_user_id,
                    submission_id=submission_id,
                )
            )

        @self.app.post("/api/member/profile-pack/submissions/withdraw")
        async def member_profile_pack_submission_withdraw(request: Request, payload: dict[str, Any]):
            user_id, denied = self._request_member_user_id(request, payload=payload)
            if denied is not None or user_id is None:
                return denied
            return self._response(
                self.api.member_withdraw_profile_pack_submission(
                    user_id=user_id,
                    submission_id=str(payload.get("submission_id", "") or ""),
                )
            )

        @self.app.get("/api/member/profile-pack/submissions/export/download")
        async def member_profile_pack_submission_export_download(
            request: Request,
            submission_id: str = "",
            user_id: str = "",
        ):
            normalized_user_id, denied = self._request_member_user_id(
                request,
                query_user_id=user_id,
            )
            if denied is not None or normalized_user_id is None:
                return denied
            result = self.api.member_get_profile_pack_submission_export(
                user_id=normalized_user_id,
                submission_id=submission_id,
            )
            if not result.ok:
                return self._response(result)
            artifact = result.data
            path = Path(str(artifact.get("path", "") or ""))
            if not path.exists():
                return JSONResponse(
                    {
                        "ok": False,
                        "message": "profile pack artifact missing",
                        "error": {
                            "code": "profile_pack_not_found",
                            "message": "profile pack artifact missing",
                        },
                    },
                    status_code=404,
                )
            return FileResponse(
                path=path,
                media_type="application/zip",
                filename=str(artifact.get("filename", "") or path.name),
            )

        @self.app.get("/api/profile-pack/catalog")
        async def list_profile_pack_catalog(
            pack_id: str = "",
            pack_type: str = "",
            risk_level: str = "",
            review_label: str = "",
            warning_flag: str = "",
            featured: str = "",
        ):
            return self._response(
                self.api.list_profile_pack_catalog(
                    pack_query=pack_id,
                    pack_type=pack_type,
                    risk_level=risk_level,
                    review_label=review_label,
                    warning_flag=warning_flag,
                    featured=featured,
                )
            )

        @self.app.get("/api/profile-pack/catalog/insights")
        async def list_profile_pack_catalog_insights(
            pack_id: str = "",
            pack_type: str = "",
            risk_level: str = "",
            review_label: str = "",
            warning_flag: str = "",
            featured: str = "",
        ):
            return self._response(
                self.api.list_profile_pack_catalog_insights(
                    pack_query=pack_id,
                    pack_type=pack_type,
                    risk_level=risk_level,
                    review_label=review_label,
                    warning_flag=warning_flag,
                    featured=featured,
                )
            )

        @self.app.get("/api/profile-pack/catalog/detail")
        async def profile_pack_catalog_detail(pack_id: str = ""):
            return self._response(self.api.get_profile_pack_catalog_detail(pack_id=pack_id))

        @self.app.get("/api/profile-pack/catalog/compare")
        async def profile_pack_catalog_compare(
            pack_id: str = "",
            selected_sections: str = "",
        ):
            sections = _to_string_list(selected_sections)
            return self._response(
                self.api.compare_profile_pack_catalog(
                    pack_id=pack_id,
                    selected_sections=sections or None,
                )
            )

        @self.app.get("/api/templates/package/download")
        async def package_download(template_id: str):
            result = self.api.generate_package(template_id=template_id)
            if not result.ok:
                return self._response(result)
            artifact = result.data
            path = Path(str(artifact.get("path", "") or ""))
            if not path.exists():
                return JSONResponse(
                    {
                        "ok": False,
                        "message": "package artifact missing",
                        "error": {
                            "code": "package_artifact_missing",
                            "message": "package artifact missing",
                        },
                    },
                    status_code=404,
                )
            return FileResponse(
                path=path,
                media_type="application/zip",
                filename=str(artifact.get("filename", "") or path.name),
            )

        @self.app.get("/api/admin/submissions")
        async def admin_submissions(
            request: Request,
            role: str = "member",
            status: str = "",
            template_id: str = "",
            risk_level: str = "",
            review_label: str = "",
            warning_flag: str = "",
        ):
            return self._response(
                self.api.admin_list_submissions(
                    role=self._request_role(request),
                    status=status,
                    template_query=template_id,
                    risk_level=risk_level,
                    review_label=review_label,
                    warning_flag=warning_flag,
                )
            )

        @self.app.post("/api/admin/dryrun")
        async def admin_dryrun(request: Request, payload: dict[str, Any]):
            patch = payload.get("patch", {})
            return self._response(
                self.api.admin_dryrun(
                    role=self._request_role(request, payload),
                    plan_id=str(payload.get("plan_id", "") or ""),
                    patch=patch if isinstance(patch, dict) else {},
                )
            )

        @self.app.post("/api/admin/apply")
        async def admin_apply(request: Request, payload: dict[str, Any]):
            return self._response(
                self.api.admin_apply(
                    role=self._request_role(request, payload),
                    plan_id=str(payload.get("plan_id", "") or ""),
                )
            )

        @self.app.post("/api/admin/rollback")
        async def admin_rollback(request: Request, payload: dict[str, Any]):
            return self._response(
                self.api.admin_rollback(
                    role=self._request_role(request, payload),
                    plan_id=str(payload.get("plan_id", "") or ""),
                )
            )

        @self.app.get("/api/admin/continuity")
        async def admin_continuity(request: Request, role: str = "member", limit: int = 20):
            return self._response(
                self.api.admin_list_continuity(
                    role=self._request_role(request),
                    limit=limit,
                )
            )

        @self.app.get("/api/admin/continuity/detail")
        async def admin_continuity_detail(request: Request, role: str = "member", plan_id: str = ""):
            return self._response(
                self.api.admin_get_continuity(
                    role=self._request_role(request),
                    plan_id=plan_id,
                )
            )

        @self.app.post("/api/admin/pipeline/run")
        async def admin_pipeline_run(request: Request, payload: dict[str, Any]):
            contract = payload.get("contract", {})
            input_payload = payload.get("input", None)
            return self._response(
                self.api.admin_run_pipeline(
                    role=self._request_role(request, payload),
                    contract=contract if isinstance(contract, dict) else {},
                    input_payload=input_payload,
                    actor_id=self._admin_id(payload),
                    run_id=str(payload.get("run_id", "") or ""),
                )
            )

        @self.app.post("/api/admin/profile-pack/export")
        async def admin_profile_pack_export(request: Request, payload: dict[str, Any]):
            return self._response(
                self.api.admin_export_profile_pack(
                    role=self._request_role(request, payload),
                    pack_id=str(payload.get("pack_id", "") or ""),
                    version=str(payload.get("version", "1.0.0") or "1.0.0"),
                    pack_type=str(payload.get("pack_type", "bot_profile_pack") or "bot_profile_pack"),
                    redaction_mode=str(payload.get("redaction_mode", "exclude_secrets") or "exclude_secrets"),
                    sections=_optional_string_list(payload, "sections"),
                    mask_paths=_optional_string_list(payload, "mask_paths"),
                    drop_paths=_optional_string_list(payload, "drop_paths"),
                )
            )

        @self.app.get("/api/admin/profile-pack/export/download")
        async def admin_profile_pack_export_download(request: Request, artifact_id: str):
            result = self.api.admin_get_profile_pack_export(
                role=self._request_role(request),
                artifact_id=artifact_id,
            )
            if not result.ok:
                return self._response(result)
            artifact = result.data
            path = Path(str(artifact.get("path", "") or ""))
            if not path.exists():
                return JSONResponse(
                    {
                        "ok": False,
                        "message": "profile pack artifact missing",
                        "error": {
                            "code": "profile_pack_not_found",
                            "message": "profile pack artifact missing",
                        },
                    },
                    status_code=404,
                )
            return FileResponse(
                path=path,
                media_type="application/zip",
                filename=str(artifact.get("filename", "") or path.name),
            )

        @self.app.get("/api/admin/profile-pack/exports")
        async def admin_profile_pack_exports(request: Request, role: str = "member", limit: int = 20):
            return self._response(
                self.api.admin_list_profile_pack_exports(
                    role=self._request_role(request),
                    limit=limit,
                )
            )

        @self.app.post("/api/admin/profile-pack/import")
        async def admin_profile_pack_import(request: Request, payload: dict[str, Any]):
            return self._response(
                self.api.admin_import_profile_pack(
                    role=self._request_role(request, payload),
                    filename=str(payload.get("filename", "") or ""),
                    content_base64=str(payload.get("content_base64", "") or ""),
                )
            )

        @self.app.post("/api/admin/profile-pack/import/from-export")
        async def admin_profile_pack_import_from_export(request: Request, payload: dict[str, Any]):
            return self._response(
                self.api.admin_import_profile_pack_from_export(
                    role=self._request_role(request, payload),
                    artifact_id=str(payload.get("artifact_id", "") or ""),
                )
            )

        @self.app.post("/api/admin/profile-pack/import-and-dryrun")
        async def admin_profile_pack_import_and_dryrun(request: Request, payload: dict[str, Any]):
            return self._response(
                self.api.admin_import_profile_pack_and_dryrun(
                    role=self._request_role(request, payload),
                    plan_id=str(payload.get("plan_id", "") or ""),
                    selected_sections=_optional_string_list(payload, "selected_sections"),
                    filename=str(payload.get("filename", "") or ""),
                    content_base64=str(payload.get("content_base64", "") or ""),
                    artifact_id=str(payload.get("artifact_id", "") or ""),
                )
            )

        @self.app.get("/api/admin/profile-pack/imports")
        async def admin_profile_pack_imports(request: Request, role: str = "member", limit: int = 20):
            return self._response(
                self.api.admin_list_profile_pack_imports(
                    role=self._request_role(request),
                    limit=limit,
                )
            )

        @self.app.post("/api/admin/profile-pack/dryrun")
        async def admin_profile_pack_dryrun(request: Request, payload: dict[str, Any]):
            return self._response(
                self.api.admin_profile_pack_dryrun(
                    role=self._request_role(request, payload),
                    import_id=str(payload.get("import_id", "") or ""),
                    plan_id=str(payload.get("plan_id", "") or ""),
                    selected_sections=_optional_string_list(payload, "selected_sections"),
                )
            )

        @self.app.get("/api/admin/profile-pack/plugin-install-plan")
        async def admin_profile_pack_plugin_install_plan(request: Request, import_id: str):
            return self._response(
                self.api.admin_profile_pack_plugin_install_plan(
                    role=self._request_role(request),
                    import_id=import_id,
                )
            )

        @self.app.post("/api/admin/profile-pack/plugin-install-confirm")
        async def admin_profile_pack_plugin_install_confirm(request: Request, payload: dict[str, Any]):
            return self._response(
                self.api.admin_profile_pack_confirm_plugin_install(
                    role=self._request_role(request, payload),
                    import_id=str(payload.get("import_id", "") or ""),
                    plugin_ids=_optional_string_list(payload, "plugin_ids"),
                )
            )

        @self.app.post("/api/admin/profile-pack/plugin-install-execute")
        async def admin_profile_pack_plugin_install_execute(request: Request, payload: dict[str, Any]):
            return self._response(
                self.api.admin_profile_pack_execute_plugin_install(
                    role=self._request_role(request, payload),
                    import_id=str(payload.get("import_id", "") or ""),
                    plugin_ids=_optional_string_list(payload, "plugin_ids"),
                    dry_run=_to_bool(payload.get("dry_run"), default=False),
                )
            )

        @self.app.post("/api/admin/profile-pack/apply")
        async def admin_profile_pack_apply(request: Request, payload: dict[str, Any]):
            return self._response(
                self.api.admin_profile_pack_apply(
                    role=self._request_role(request, payload),
                    plan_id=str(payload.get("plan_id", "") or ""),
                )
            )

        @self.app.post("/api/admin/profile-pack/rollback")
        async def admin_profile_pack_rollback(request: Request, payload: dict[str, Any]):
            return self._response(
                self.api.admin_profile_pack_rollback(
                    role=self._request_role(request, payload),
                    plan_id=str(payload.get("plan_id", "") or ""),
                )
            )

        @self.app.get("/api/admin/profile-pack/submissions")
        async def admin_profile_pack_submissions(
            request: Request,
            role: str = "member",
            status: str = "",
            pack_id: str = "",
            pack_type: str = "",
            risk_level: str = "",
            review_label: str = "",
            warning_flag: str = "",
        ):
            return self._response(
                self.api.admin_list_profile_pack_submissions(
                    role=self._request_role(request),
                    status=status,
                    pack_query=pack_id,
                    pack_type=pack_type,
                    risk_level=risk_level,
                    review_label=review_label,
                    warning_flag=warning_flag,
                )
            )

        @self.app.post("/api/admin/profile-pack/submissions/decide")
        async def admin_decide_profile_pack_submission(request: Request, payload: dict[str, Any]):
            return self._response(
                self.api.admin_decide_profile_pack_submission(
                    role=self._request_role(request, payload),
                    submission_id=str(payload.get("submission_id", "") or ""),
                    decision=str(payload.get("decision", "") or ""),
                    review_note=str(payload.get("review_note", "") or ""),
                    review_labels=_optional_string_list(payload, "review_labels"),
                    reviewer_id=self._request_reviewer_id(request, payload),
                )
            )

        @self.app.post("/api/admin/profile-pack/catalog/featured")
        async def admin_set_profile_pack_catalog_featured(request: Request, payload: dict[str, Any]):
            return self._response(
                self.api.admin_set_profile_pack_featured(
                    role=self._request_role(request, payload),
                    pack_id=str(payload.get("pack_id", "") or ""),
                    featured=_to_bool(payload.get("featured"), default=False),
                    note=str(payload.get("note", "") or ""),
                )
            )

        @self.app.post("/api/admin/submissions/decide")
        async def admin_decide_submission(request: Request, payload: dict[str, Any]):
            return self._response(
                self.api.admin_decide_submission(
                    role=self._request_role(request, payload),
                    submission_id=str(payload.get("submission_id", "") or ""),
                    decision=str(payload.get("decision", "") or ""),
                    review_note=str(payload.get("review_note", "") or ""),
                    review_labels=_optional_string_list(payload, "review_labels"),
                    reviewer_id=self._request_reviewer_id(request, payload),
                )
            )

        @self.app.post("/api/admin/submissions/review")
        async def admin_review_submission(request: Request, payload: dict[str, Any]):
            return self._response(
                self.api.admin_update_submission_review(
                    role=self._request_role(request, payload),
                    submission_id=str(payload.get("submission_id", "") or ""),
                    review_note=str(payload.get("review_note", "") or ""),
                    review_labels=_optional_string_list(payload, "review_labels"),
                    reviewer_id=self._request_reviewer_id(request, payload),
                )
            )

        @self.app.get("/api/admin/submissions/compare")
        async def admin_compare_submission(request: Request, submission_id: str):
            return self._response(
                self.api.admin_compare_submission(
                    role=self._request_role(request),
                    submission_id=submission_id,
                )
            )

        @self.app.get("/api/admin/submissions/detail")
        async def admin_submission_detail(request: Request, submission_id: str):
            return self._response(
                self.api.admin_get_submission_detail(
                    role=self._request_role(request),
                    submission_id=submission_id,
                )
            )

        @self.app.get("/api/admin/submissions/package/download")
        async def admin_download_submission_package(request: Request, submission_id: str):
            result = self.api.admin_get_submission_package(
                role=self._request_role(request),
                submission_id=submission_id,
            )
            if not result.ok:
                return self._response(result)
            artifact = result.data
            path = Path(str(artifact.get("path", "") or ""))
            if not path.exists():
                return JSONResponse(
                    {
                        "ok": False,
                        "message": "submission package missing",
                        "error": {
                            "code": "submission_package_not_available",
                            "message": "submission package missing",
                        },
                    },
                    status_code=404,
                )
            return FileResponse(
                path=path,
                media_type="application/zip",
                filename=str(artifact.get("filename", "") or path.name),
            )

        @self.app.get("/api/reviewer/submissions")
        async def reviewer_submissions(
            request: Request,
            status: str = "",
            template_id: str = "",
            risk_level: str = "",
            review_label: str = "",
            warning_flag: str = "",
        ):
            return self._response(
                self.api.admin_list_submissions(
                    role=self._request_role(request),
                    status=status,
                    template_query=template_id,
                    risk_level=risk_level,
                    review_label=review_label,
                    warning_flag=warning_flag,
                )
            )

        @self.app.post("/api/reviewer/submissions/review")
        async def reviewer_submission_review(request: Request, payload: dict[str, Any]):
            return self._response(
                self.api.admin_update_submission_review(
                    role=self._request_role(request, payload),
                    submission_id=str(payload.get("submission_id", "") or ""),
                    review_note=str(payload.get("review_note", "") or ""),
                    review_labels=_optional_string_list(payload, "review_labels"),
                    reviewer_id=self._request_reviewer_id(request, payload),
                )
            )

        @self.app.post("/api/reviewer/submissions/decide")
        async def reviewer_submission_decide(request: Request, payload: dict[str, Any]):
            return self._response(
                self.api.admin_decide_submission(
                    role=self._request_role(request, payload),
                    submission_id=str(payload.get("submission_id", "") or ""),
                    decision=str(payload.get("decision", "") or ""),
                    review_note=str(payload.get("review_note", "") or ""),
                    review_labels=_optional_string_list(payload, "review_labels"),
                    reviewer_id=self._request_reviewer_id(request, payload),
                )
            )

        @self.app.get("/api/reviewer/submissions/detail")
        async def reviewer_submission_detail(request: Request, submission_id: str):
            return self._response(
                self.api.admin_get_submission_detail(
                    role=self._request_role(request),
                    submission_id=submission_id,
                )
            )

        @self.app.get("/api/reviewer/submissions/compare")
        async def reviewer_submission_compare(request: Request, submission_id: str):
            return self._response(
                self.api.admin_compare_submission(
                    role=self._request_role(request),
                    submission_id=submission_id,
                )
            )

        @self.app.get("/api/reviewer/submissions/package/download")
        async def reviewer_submission_package_download(request: Request, submission_id: str):
            result = self.api.admin_get_submission_package(
                role=self._request_role(request),
                submission_id=submission_id,
            )
            if not result.ok:
                return self._response(result)
            artifact = result.data
            path = Path(str(artifact.get("path", "") or ""))
            if not path.exists():
                return JSONResponse(
                    {
                        "ok": False,
                        "message": "submission package missing",
                        "error": {
                            "code": "submission_package_not_available",
                            "message": "submission package missing",
                        },
                    },
                    status_code=404,
                )
            return FileResponse(
                path=path,
                media_type="application/zip",
                filename=str(artifact.get("filename", "") or path.name),
            )

        @self.app.get("/api/reviewer/profile-pack/submissions")
        async def reviewer_profile_pack_submissions(
            request: Request,
            status: str = "",
            pack_id: str = "",
            pack_type: str = "",
            risk_level: str = "",
            review_label: str = "",
            warning_flag: str = "",
        ):
            return self._response(
                self.api.admin_list_profile_pack_submissions(
                    role=self._request_role(request),
                    status=status,
                    pack_query=pack_id,
                    pack_type=pack_type,
                    risk_level=risk_level,
                    review_label=review_label,
                    warning_flag=warning_flag,
                )
            )

        @self.app.post("/api/reviewer/profile-pack/submissions/decide")
        async def reviewer_profile_pack_decide(request: Request, payload: dict[str, Any]):
            return self._response(
                self.api.admin_decide_profile_pack_submission(
                    role=self._request_role(request, payload),
                    submission_id=str(payload.get("submission_id", "") or ""),
                    decision=str(payload.get("decision", "") or ""),
                    review_note=str(payload.get("review_note", "") or ""),
                    review_labels=_optional_string_list(payload, "review_labels"),
                    reviewer_id=self._request_reviewer_id(request, payload),
                )
            )

        @self.app.get("/api/admin/retry-requests")
        async def admin_retry_requests(request: Request, role: str = "member"):
            return self._response(self.api.admin_list_retry_requests(role=self._request_role(request)))

        @self.app.post("/api/admin/retry-requests/lock")
        async def admin_retry_lock(request: Request, payload: dict[str, Any]):
            return self._response(
                self.api.admin_acquire_retry_lock(
                    role=self._request_role(request, payload),
                    request_id=str(payload.get("request_id", "") or ""),
                    admin_id=self._admin_id(payload),
                    force=_to_bool(payload.get("force"), default=False),
                    reason=str(payload.get("reason", "") or ""),
                )
            )

        @self.app.post("/api/admin/retry-requests/decide")
        async def admin_retry_decide(request: Request, payload: dict[str, Any]):
            return self._response(
                self.api.admin_decide_retry_request(
                    role=self._request_role(request, payload),
                    request_id=str(payload.get("request_id", "") or ""),
                    decision=str(payload.get("decision", "") or ""),
                    admin_id=self._admin_id(payload),
                    request_version=_to_int(payload.get("request_version"), 0) or None,
                    lock_version=_to_int(payload.get("lock_version"), 0) or None,
                )
            )

        @self.app.get("/api/admin/audit")
        async def admin_audit(
            request: Request,
            role: str = "member",
            limit: int = 50,
            action_prefix: str = "",
            reviewer_id: str = "",
            device_id: str = "",
            lifecycle_only: bool = False,
            inspect_limit: int = 1000,
        ):
            return self._response(
                self.api.admin_list_audit(
                    role=self._request_role(request),
                    limit=limit,
                    action_prefix=action_prefix,
                    reviewer_id=reviewer_id,
                    device_id=device_id,
                    lifecycle_only=lifecycle_only,
                    inspect_limit=inspect_limit,
                )
            )

        @self.app.get("/api/admin/storage/local-summary")
        async def admin_storage_local_summary(request: Request):
            return self._response(
                self.api.admin_storage_local_summary(
                    role=self._request_role(request),
                )
            )

        @self.app.get("/api/admin/artifacts")
        async def admin_artifacts_list(request: Request, artifact_kind: str = "", limit: int = 50):
            return self._response(
                self.api.admin_list_artifacts(
                    role=self._request_role(request),
                    artifact_kind=artifact_kind,
                    limit=limit,
                )
            )

        @self.app.post("/api/admin/artifacts/mirror")
        async def admin_artifact_mirror(request: Request, payload: dict[str, Any]):
            return self._response(
                self.api.admin_mirror_artifact(
                    role=self._request_role(request, payload),
                    artifact_id=str(payload.get("artifact_id", "") or ""),
                    admin_id=self._admin_id(payload),
                    remote_path=str(payload.get("remote_path", "") or ""),
                    rclone_binary=str(payload.get("rclone_binary", "") or "rclone"),
                    timeout_seconds=_to_int(payload.get("timeout_seconds"), 300),
                    bwlimit=str(payload.get("bwlimit", "") or ""),
                    encryption_required=_to_bool(payload.get("encryption_required"), True),
                    remote_encryption_verified=_to_bool(payload.get("remote_encryption_verified"), False),
                )
            )

        @self.app.get("/api/admin/storage/policies")
        async def admin_storage_policies_get(request: Request):
            return self._response(
                self.api.admin_storage_get_policies(
                    role=self._request_role(request),
                )
            )

        @self.app.post("/api/admin/storage/policies")
        async def admin_storage_policies_set(request: Request, payload: dict[str, Any]):
            policy_patch = payload.get("policy_patch")
            if not isinstance(policy_patch, dict):
                policy_patch = {
                    key: value
                    for key, value in payload.items()
                    if key not in {"role", "admin_id"}
                }
            return self._response(
                self.api.admin_storage_set_policies(
                    role=self._request_role(request, payload),
                    patch=policy_patch,
                    admin_id=self._admin_id(payload),
                )
            )

        @self.app.post("/api/admin/storage/jobs/run")
        async def admin_storage_jobs_run(request: Request, payload: dict[str, Any]):
            return self._response(
                self.api.admin_storage_run_job(
                    role=self._request_role(request, payload),
                    admin_id=self._admin_id(payload),
                    trigger=str(payload.get("trigger", "") or "manual"),
                    note=str(payload.get("note", "") or ""),
                )
            )

        @self.app.get("/api/admin/storage/jobs")
        async def admin_storage_jobs_list(request: Request, status: str = "", limit: int = 50):
            return self._response(
                self.api.admin_storage_list_jobs(
                    role=self._request_role(request),
                    status=status,
                    limit=limit,
                )
            )

        @self.app.get("/api/admin/storage/jobs/{job_id}")
        async def admin_storage_job_get(request: Request, job_id: str):
            return self._response(
                self.api.admin_storage_get_job(
                    role=self._request_role(request),
                    job_id=job_id,
                )
            )

        @self.app.post("/api/admin/storage/restore/prepare")
        async def admin_storage_restore_prepare(request: Request, payload: dict[str, Any]):
            artifact_ref = str(payload.get("artifact_ref", "") or "").strip()
            if not artifact_ref:
                artifact_ref = str(payload.get("artifact_id", "") or "").strip()
            return self._response(
                self.api.admin_storage_restore_prepare(
                    role=self._request_role(request, payload),
                    artifact_ref=artifact_ref,
                    admin_id=self._admin_id(payload),
                    note=str(payload.get("note", "") or ""),
                )
            )

        @self.app.post("/api/admin/storage/restore/commit")
        async def admin_storage_restore_commit(request: Request, payload: dict[str, Any]):
            return self._response(
                self.api.admin_storage_restore_commit(
                    role=self._request_role(request, payload),
                    restore_id=str(payload.get("restore_id", "") or ""),
                    admin_id=self._admin_id(payload),
                )
            )

        @self.app.post("/api/admin/storage/restore/cancel")
        async def admin_storage_restore_cancel(request: Request, payload: dict[str, Any]):
            return self._response(
                self.api.admin_storage_restore_cancel(
                    role=self._request_role(request, payload),
                    restore_id=str(payload.get("restore_id", "") or ""),
                    admin_id=self._admin_id(payload),
                )
            )

        @self.app.get("/api/admin/storage/restore/jobs")
        async def admin_storage_restore_jobs_list(request: Request, state: str = "", limit: int = 50):
            return self._response(
                self.api.admin_storage_list_restore_jobs(
                    role=self._request_role(request),
                    state=state,
                    limit=limit,
                )
            )

        @self.app.get("/api/admin/storage/restore/jobs/{restore_id}")
        async def admin_storage_restore_job_get(request: Request, restore_id: str):
            return self._response(
                self.api.admin_storage_get_restore_job(
                    role=self._request_role(request),
                    restore_id=restore_id,
                )
            )

        @self.app.get("/api/notifications")
        async def list_notifications(limit: int = 100):
            return self._response(self.api.list_notifications(limit=limit))

    async def start(self) -> bool:
        if not FASTAPI_AVAILABLE or self.app is None:
            return False

        enabled = _to_bool(self._webui_config().get("enabled", True), default=True)
        if not enabled:
            logger.info("[sharelife] webui disabled by config")
            return False

        if self._server_task and not self._server_task.done():
            return True

        cfg = self._webui_config()
        host = str(cfg.get("host", "127.0.0.1") or "127.0.0.1").strip() or "127.0.0.1"
        port = _to_int(cfg.get("port", 8106), default=8106)
        if port < 1 or port > 65535:
            port = 8106

        self._refresh_auth()
        uv_config = uvicorn.Config(
            self.app,
            host=host,
            port=port,
            log_level="warning",
            access_log=False,
        )
        self.server = uvicorn.Server(uv_config)
        self._server_task = asyncio.create_task(
            self.server.serve(),
            name="sharelife-webui-server",
        )
        self.public_url = f"http://{self._display_host(host)}:{port}"
        logger.info(
            "[sharelife] webui started: bind=%s:%s url=%s auth_enabled=%s",
            host,
            port,
            self.public_url,
            self._auth_enabled,
        )
        return True

    def is_running(self) -> bool:
        return bool(self._server_task and not self._server_task.done())

    def status_payload(self) -> dict[str, Any]:
        enabled = _to_bool(self._webui_config().get("enabled", True), default=True)
        return {
            "available": FASTAPI_AVAILABLE,
            "enabled": enabled,
            "running": self.is_running(),
            "url": self.public_url,
            "auth_required": self._auth_enabled,
            "available_roles": self._available_auth_roles(),
        }

    async def stop(self) -> None:
        if self.server is not None:
            self.server.should_exit = True

        if self._server_task is not None:
            try:
                await asyncio.wait_for(self._server_task, timeout=8)
            except asyncio.TimeoutError:
                self._server_task.cancel()
                try:
                    await self._server_task
                except asyncio.CancelledError:
                    pass
            except asyncio.CancelledError:
                pass
            except Exception as exc:
                logger.warning("[sharelife] webui stop failed: %s", exc)

        self.server = None
        self._server_task = None
        self.public_url = ""
