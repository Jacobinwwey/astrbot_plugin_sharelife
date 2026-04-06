"""Local-only WebUI auth override loading for private deployments."""

from __future__ import annotations

import copy
import os
from pathlib import Path
from typing import Any

import tomllib

LOCAL_WEBUI_AUTH_ENV = "SHARELIFE_LOCAL_WEBUI_AUTH_FILE"
ALLOW_CONFIG_ADMIN_PASSWORD_ENV = "SHARELIFE_ALLOW_CONFIG_ADMIN_PASSWORD"

_ALLOWED_AUTH_FIELDS = frozenset(
    {
        "password",
        "member_password",
        "reviewer_password",
        "admin_password",
        "token_ttl_seconds",
        "reviewer_token_ttl_seconds",
        "allow_query_token",
        "allow_anonymous_member",
        "anonymous_member_user_id",
        "anonymous_member_allowlist",
        "login_rate_limit_window_seconds",
        "login_rate_limit_max_attempts",
        "api_rate_limit_window_seconds",
        "api_rate_limit_max_requests",
    }
)

DEFAULT_LOCAL_WEBUI_AUTH_TEMPLATE = """# Sharelife local-only WebUI auth override.
# This file is intended for local/private use and should not be committed.

[webui.auth]
member_password = ""
reviewer_password = ""
admin_password = ""
token_ttl_seconds = 7200
reviewer_token_ttl_seconds = 604800
allow_query_token = false
allow_anonymous_member = false
anonymous_member_user_id = "webui-user"
anonymous_member_allowlist = [
  "POST /api/trial",
  "GET /api/trial/status",
  "POST /api/templates/install",
  "GET /api/member/installations",
  "POST /api/member/installations/refresh",
  "GET /api/preferences",
  "POST /api/preferences/mode",
  "POST /api/preferences/observe",
]
login_rate_limit_window_seconds = 60
login_rate_limit_max_attempts = 10
api_rate_limit_window_seconds = 60
api_rate_limit_max_requests = 600
"""


def resolve_local_webui_auth_path(data_root: str | Path) -> Path:
    return Path(data_root).expanduser().resolve() / "secrets" / "webui-auth.local.toml"


def _configured_override_path(
    *,
    data_root: str | Path,
    override_path: str | Path | None = None,
    env: dict[str, str] | None = None,
) -> Path:
    if override_path:
        return Path(override_path).expanduser().resolve()
    runtime_env = env if env is not None else os.environ
    env_path = str(runtime_env.get(LOCAL_WEBUI_AUTH_ENV, "") or "").strip()
    if env_path:
        return Path(env_path).expanduser().resolve()
    return resolve_local_webui_auth_path(data_root)


def resolve_configured_local_webui_auth_path(
    *,
    data_root: str | Path,
    override_path: str | Path | None = None,
    env: dict[str, str] | None = None,
) -> Path:
    return _configured_override_path(
        data_root=data_root,
        override_path=override_path,
        env=env,
    )


def ensure_local_webui_auth_template(path: str | Path) -> Path:
    resolved = Path(path).expanduser().resolve()
    if resolved.exists():
        return resolved
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(DEFAULT_LOCAL_WEBUI_AUTH_TEMPLATE, encoding="utf-8")
    try:
        resolved.chmod(0o600)
    except Exception:
        pass
    return resolved


def load_local_webui_auth_override(path: str | Path) -> dict[str, Any]:
    resolved = Path(path).expanduser().resolve()
    if not resolved.exists():
        return {}
    payload = tomllib.loads(resolved.read_text(encoding="utf-8"))
    auth: dict[str, Any] = {}
    if isinstance(payload.get("webui"), dict) and isinstance(payload["webui"].get("auth"), dict):
        auth = payload["webui"]["auth"]
    elif isinstance(payload.get("auth"), dict):
        auth = payload["auth"]
    if not isinstance(auth, dict):
        return {}
    sanitized = {
        key: value
        for key, value in auth.items()
        if key in _ALLOWED_AUTH_FIELDS
    }
    if not sanitized:
        return {}
    return {"webui": {"auth": sanitized}}


def merge_local_webui_auth_override(
    config: dict[str, Any] | None,
    *,
    data_root: str | Path,
    override_path: str | Path | None = None,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    merged: dict[str, Any] = copy.deepcopy(config) if isinstance(config, dict) else {}
    path = _configured_override_path(data_root=data_root, override_path=override_path, env=env)
    override = load_local_webui_auth_override(path)
    if not override:
        return merged
    webui = merged.setdefault("webui", {})
    if not isinstance(webui, dict):
        webui = {}
        merged["webui"] = webui
    auth = webui.setdefault("auth", {})
    if not isinstance(auth, dict):
        auth = {}
        webui["auth"] = auth
    auth.update(override["webui"]["auth"])
    return merged


def strip_untrusted_standalone_admin_password(
    config: dict[str, Any] | None,
    *,
    data_root: str | Path,
    override_path: str | Path | None = None,
    env: dict[str, str] | None = None,
    allow_config_admin_password: bool = False,
) -> dict[str, Any]:
    sanitized: dict[str, Any] = copy.deepcopy(config) if isinstance(config, dict) else {}
    runtime_env = env if env is not None else os.environ
    if allow_config_admin_password:
        return sanitized
    if str(runtime_env.get(ALLOW_CONFIG_ADMIN_PASSWORD_ENV, "") or "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }:
        return sanitized
    if str(runtime_env.get("SHARELIFE_ADMIN_PASSWORD", "") or "").strip():
        return sanitized

    webui = sanitized.get("webui", {})
    if not isinstance(webui, dict):
        return sanitized
    auth = webui.get("auth", {})
    if not isinstance(auth, dict):
        return sanitized
    admin_password = str(auth.get("admin_password", "") or "").strip()
    if not admin_password:
        return sanitized

    override = load_local_webui_auth_override(
        resolve_configured_local_webui_auth_path(
            data_root=data_root,
            override_path=override_path,
            env=runtime_env,
        )
    )
    override_auth = (
        override.get("webui", {}).get("auth", {})
        if isinstance(override.get("webui"), dict)
        else {}
    )
    if isinstance(override_auth, dict) and str(override_auth.get("admin_password", "") or "").strip():
        return sanitized

    auth.pop("admin_password", None)
    return sanitized
