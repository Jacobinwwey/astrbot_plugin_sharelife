#!/usr/bin/env python3
"""Run Sharelife standalone WebUI without requiring AstrBot runtime."""

from __future__ import annotations

import argparse
import base64
import io
import json
import os
import sys
import types
import zipfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def ensure_astrbot_logger_stub() -> None:
    try:
        import astrbot.api  # noqa: F401

        return
    except Exception:
        pass

    astrbot_module = types.ModuleType("astrbot")
    astrbot_api_module = types.ModuleType("astrbot.api")

    class _Logger:
        @staticmethod
        def warning(*args, **kwargs):
            print(*args)

        @staticmethod
        def info(*args, **kwargs):
            print(*args)

    astrbot_api_module.logger = _Logger()
    astrbot_module.api = astrbot_api_module
    sys.modules.setdefault("astrbot", astrbot_module)
    sys.modules.setdefault("astrbot.api", astrbot_api_module)


ensure_astrbot_logger_stub()

from sharelife.application.services_apply import ApplyService
from sharelife.application.services_audit import AuditService
from sharelife.application.services_artifact_mirror import ArtifactMirrorService
from sharelife.application.services_continuity import ConfigContinuityService
from sharelife.application.services_market import MarketService
from sharelife.application.services_package import PackageService
from sharelife.application.services_preferences import PreferenceService
from sharelife.application.services_profile_pack import ProfilePackService
from sharelife.application.services_profile_pack_bootstrap import ProfilePackBootstrapService
from sharelife.application.services_queue import RetryQueueService
from sharelife.application.services_reviewer_auth import ReviewerAuthService
from sharelife.application.services_transfer_jobs import TransferJobService
from sharelife.application.services_trial import TrialService
from sharelife.application.services_trial_request import TrialRequestService
from sharelife.infrastructure.json_state_store import JsonStateStore
from sharelife.infrastructure.local_webui_auth import (
    strip_untrusted_standalone_admin_password,
    merge_local_webui_auth_override,
)
from sharelife.infrastructure.notifier import InMemoryNotifier
from sharelife.infrastructure.runtime_bridge import InMemoryRuntimeBridge
from sharelife.infrastructure.sqlite_state_store import SqliteStateStore
from sharelife.interfaces.api_v1 import SharelifeApiV1
from sharelife.interfaces.web_api_v1 import SharelifeWebApiV1
from sharelife.interfaces.webui_server import SharelifeWebUIServer


class FrozenClock:
    def __init__(self, start: datetime):
        self.current = start

    def utcnow(self) -> datetime:
        return self.current

    def shift(self, **kwargs) -> None:
        self.current = self.current + timedelta(**kwargs)


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    norm = str(value).strip().lower()
    if norm in {"1", "true", "yes", "on"}:
        return True
    if norm in {"0", "false", "no", "off"}:
        return False
    return default


def _as_int(value: Any, default: int) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(value.strip())
        except ValueError:
            return default
    return default


def _build_bundle_zip(payload: dict[str, Any]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("bundle.json", json.dumps(payload, ensure_ascii=False, indent=2))
        zf.writestr("README.txt", "Sharelife standalone demo package")
    return buffer.getvalue()


def _bundle_base64(payload: dict[str, Any]) -> str:
    return base64.b64encode(_build_bundle_zip(payload)).decode("ascii")


def load_config(config_path: Path | None) -> dict[str, Any]:
    if config_path is None:
        return {}
    if not config_path.exists():
        raise FileNotFoundError(f"config file not found: {config_path}")
    text = config_path.read_text(encoding="utf-8")
    if config_path.suffix.lower() == ".json":
        data = json.loads(text)
    else:
        data = yaml.safe_load(text) or {}
    if not isinstance(data, dict):
        raise ValueError("config root must be a JSON/YAML object")
    return data


def merge_env_auth(config: dict[str, Any]) -> dict[str, Any]:
    webui = config.setdefault("webui", {})
    if not isinstance(webui, dict):
        config["webui"] = {}
        webui = config["webui"]
    auth = webui.setdefault("auth", {})
    if not isinstance(auth, dict):
        webui["auth"] = {}
        auth = webui["auth"]

    member_password = str(os.getenv("SHARELIFE_MEMBER_PASSWORD", "") or "").strip()
    admin_password = str(os.getenv("SHARELIFE_ADMIN_PASSWORD", "") or "").strip()
    if member_password:
        auth["member_password"] = member_password
    if admin_password:
        auth["admin_password"] = admin_password
    return config


def apply_standalone_auth_defaults(config: dict[str, Any]) -> dict[str, Any]:
    webui = config.setdefault("webui", {})
    if not isinstance(webui, dict):
        config["webui"] = {}
        webui = config["webui"]
    auth = webui.setdefault("auth", {})
    if not isinstance(auth, dict):
        webui["auth"] = {}
        auth = webui["auth"]

    has_any_auth_secret = any(
        str(auth.get(key, "") or "").strip()
        for key in ("member_password", "reviewer_password", "admin_password", "password")
    )
    if has_any_auth_secret and "allow_anonymous_member" not in auth:
        auth["allow_anonymous_member"] = True
    return config


def apply_standalone_feature_defaults(config: dict[str, Any]) -> dict[str, Any]:
    webui = config.setdefault("webui", {})
    if not isinstance(webui, dict):
        config["webui"] = {}
        webui = config["webui"]
    features = webui.setdefault("features", {})
    if not isinstance(features, dict):
        webui["features"] = {}
        features = webui["features"]

    if "local_astrbot_import" not in features:
        features["local_astrbot_import"] = False
    if not _as_bool(str(features.get("local_astrbot_import", "false")), default=False):
        features["local_astrbot_import"] = False
        features["allow_anonymous_local_astrbot_import"] = False
        return config
    if "allow_anonymous_local_astrbot_import" not in features:
        features["allow_anonymous_local_astrbot_import"] = False
    return config


def merge_env_state_store(config: dict[str, Any]) -> dict[str, Any]:
    raw = config.setdefault("state_store", {})
    state_store = raw if isinstance(raw, dict) else {}
    if not isinstance(raw, dict):
        config["state_store"] = state_store

    backend = str(os.getenv("SHARELIFE_STATE_BACKEND", "") or "").strip()
    sqlite_file = str(os.getenv("SHARELIFE_STATE_SQLITE_FILE", "") or "").strip()
    migrate = os.getenv("SHARELIFE_STATE_MIGRATE_FROM_JSON", None)

    if backend:
        state_store["backend"] = backend
    if sqlite_file:
        state_store["sqlite_file"] = sqlite_file
    if migrate is not None:
        state_store["migrate_from_json"] = _as_bool(migrate, default=True)
    return config


def state_store_filenames() -> dict[str, str]:
    return {
        "preference_state": "preference_state.json",
        "retry_state": "retry_state.json",
        "trial_state": "trial_state.json",
        "trial_request_state": "trial_request_state.json",
        "notification_state": "notification_state.json",
        "market_state": "market_state.json",
        "audit_state": "audit_state.json",
        "profile_pack_state": "profile_pack_state.json",
        "identity_state": "identity_state.json",
        "reviewer_auth_state": "reviewer_auth_state.json",
        "transfer_state": "transfer_state.json",
        "artifact_state": "artifact_state.json",
        "continuity_state": "continuity_state.json",
    }


def build_state_stores(data_root: Path, config: dict[str, Any]) -> dict[str, Any]:
    mapping = state_store_filenames()
    raw = config.get("state_store", {})
    cfg = raw if isinstance(raw, dict) else {}
    backend = str(cfg.get("backend", "json") or "json").strip().lower()
    if backend in {"sqlite", "sqlite3"}:
        sqlite_file = str(cfg.get("sqlite_file", "") or "").strip()
        sqlite_path = Path(sqlite_file).expanduser() if sqlite_file else (data_root / "sharelife_state.sqlite3")
        stores = {
            store_key: SqliteStateStore(sqlite_path, store_key=store_key)
            for store_key in mapping
        }
        migrate_from_json = _as_bool(str(cfg.get("migrate_from_json", "true")), default=True)
        if migrate_from_json:
            for store_key, filename in mapping.items():
                stores[store_key].import_from_json_file(data_root / filename)
        return stores

    return {
        store_key: JsonStateStore(data_root / filename)
        for store_key, filename in mapping.items()
    }


def build_server(output_root: Path, config: dict[str, Any]) -> tuple[SharelifeWebUIServer, SharelifeApiV1]:
    clock = FrozenClock(datetime.now(UTC))
    state_stores = build_state_stores(output_root, config=config)
    continuity_cfg = config.get("continuity", {}) if isinstance(config.get("continuity"), dict) else {}
    preferences = PreferenceService(state_store=state_stores["preference_state"])
    queue = RetryQueueService(clock=clock, state_store=state_stores["retry_state"])
    trial = TrialService(clock=clock, state_store=state_stores["trial_state"])
    notifier = InMemoryNotifier(state_store=state_stores["notification_state"])
    trial_request = TrialRequestService(
        trial_service=trial,
        retry_queue_service=queue,
        notifier=notifier,
        state_store=state_stores["trial_request_state"],
    )
    market = MarketService(clock=clock, state_store=state_stores["market_state"])
    package = PackageService(
        market_service=market,
        output_root=output_root,
        clock=clock,
        artifact_state_store=state_stores["artifact_state"],
    )
    artifact_mirror = ArtifactMirrorService(
        artifact_store=package.artifact_store,
        clock=clock,
    )
    runtime = InMemoryRuntimeBridge(
        initial_state={
            "astrbot_core": {"name": "sharelife-standalone"},
            "providers": {"openai": {"model": "gpt-5", "api_key": "sk-standalone-redacted"}},
            "plugins": {"sharelife": {"enabled": True}},
        }
    )
    continuity = ConfigContinuityService(
        state_store=state_stores["continuity_state"],
        clock=clock,
        max_entries=max(1, _as_int(continuity_cfg.get("max_entries"), 50)),
    )
    apply = ApplyService(runtime=runtime, continuity_service=continuity)
    profile_pack = ProfilePackService(
        runtime=runtime,
        apply_service=apply,
        output_root=output_root / "profile-packs",
        clock=clock,
        astrbot_version="4.16.0",
        plugin_version="0.3.12",
        state_store=state_stores["profile_pack_state"],
    )
    webui_cfg = config.get("webui", {}) if isinstance(config.get("webui"), dict) else {}
    public_market_cfg = (
        webui_cfg.get("public_market", {})
        if isinstance(webui_cfg.get("public_market"), dict)
        else {}
    )
    public_market_root = str(
        public_market_cfg.get("root", str(REPO_ROOT / "docs" / "public"))
        or str(REPO_ROOT / "docs" / "public")
    ).strip()
    device_keys_cfg = (
        webui_cfg.get("device_keys", {})
        if isinstance(webui_cfg.get("device_keys"), dict)
        else {}
    )
    # Keep standalone market useful on first launch: always seed bundled official pack baseline.
    ProfilePackBootstrapService(profile_pack_service=profile_pack).sync()
    audit = AuditService(clock=clock, state_store=state_stores["audit_state"])
    reviewer_auth = ReviewerAuthService(
        state_store=state_stores["identity_state"],
        legacy_state_store=state_stores["reviewer_auth_state"],
        max_devices=int(device_keys_cfg.get("max_reviewer_devices", 3) or 3),
    )
    transfer_jobs = TransferJobService(
        clock=clock,
        state_store=state_stores["transfer_state"],
    )
    api = SharelifeApiV1(
        preference_service=preferences,
        retry_queue_service=queue,
        trial_request_service=trial_request,
        market_service=market,
        package_service=package,
        apply_service=apply,
        audit_service=audit,
        artifact_mirror_service=artifact_mirror,
        profile_pack_service=profile_pack,
        reviewer_auth_service=reviewer_auth,
        transfer_job_service=transfer_jobs,
        public_market_auto_publish_profile_pack_approve=_as_bool(
            str(public_market_cfg.get("auto_publish_profile_pack_approve", "false")),
            default=False,
        ),
        public_market_root=public_market_root,
        public_market_rebuild_snapshot_on_publish=_as_bool(
            str(public_market_cfg.get("rebuild_snapshot_on_publish", "true")),
            default=True,
        ),
    )
    web_api = SharelifeWebApiV1(api=api, notifier=notifier)
    web_root = REPO_ROOT / "sharelife" / "webui"
    server = SharelifeWebUIServer(api=web_api, config=config, web_root=web_root)
    return server, api


def seed_demo_market(api: SharelifeApiV1) -> None:
    baseline = api.submit_template_package(
        user_id="demo-seed",
        template_id="community/basic",
        version="1.0.0",
        filename="community-basic-v1_0.zip",
        content_base64=_bundle_base64(
            {
                "template_id": "community/basic",
                "version": "1.0.0",
                "prompt": "You are a careful community helper. Follow platform policy.",
                "provider_settings": {"provider": "openai"},
            }
        ),
    )
    api.admin_decide_submission(
        role="admin",
        submission_id=baseline["submission_id"],
        decision="approve",
        review_note="seed baseline",
        review_labels=["manual_reviewed"],
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Sharelife standalone WebUI server")
    parser.add_argument("--host", default=os.getenv("SHARELIFE_HOST", "0.0.0.0"))
    parser.add_argument("--port", type=int, default=int(os.getenv("SHARELIFE_PORT", "8106")))
    parser.add_argument(
        "--data-root",
        default=os.getenv("SHARELIFE_DATA_ROOT", str(REPO_ROOT / "output" / "standalone-data")),
        help="Data root for generated package/profile-pack artifacts",
    )
    parser.add_argument(
        "--config",
        default=os.getenv("SHARELIFE_CONFIG", ""),
        help="Optional JSON/YAML config path (same structure as plugin config)",
    )
    parser.add_argument(
        "--seed-demo",
        action="store_true",
        default=_as_bool(os.getenv("SHARELIFE_SEED_DEMO", "0"), default=False),
        help="Seed a minimal demo template into market on startup",
    )
    parser.add_argument(
        "--allow-config-admin-password",
        action="store_true",
        default=_as_bool(os.getenv("SHARELIFE_ALLOW_CONFIG_ADMIN_PASSWORD", "0"), default=False),
        help="Allow standalone WebUI to honor admin_password from the regular config file. Disabled by default for safer public deployments.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data_root = Path(str(args.data_root)).resolve()
    data_root.mkdir(parents=True, exist_ok=True)

    config_path = Path(str(args.config)).resolve() if str(args.config or "").strip() else None
    config = load_config(config_path)
    config = merge_local_webui_auth_override(config, data_root=data_root)
    config = merge_env_auth(config)
    config = apply_standalone_auth_defaults(config)
    config = apply_standalone_feature_defaults(config)
    config = merge_env_state_store(config)
    pre_strip_auth = (
        config.get("webui", {}).get("auth", {})
        if isinstance(config.get("webui"), dict) and isinstance(config.get("webui", {}).get("auth"), dict)
        else {}
    )
    pre_strip_admin_password = (
        str(pre_strip_auth.get("admin_password", "") or "").strip()
        if isinstance(pre_strip_auth, dict)
        else ""
    )
    config = strip_untrusted_standalone_admin_password(
        config,
        data_root=data_root,
        allow_config_admin_password=bool(args.allow_config_admin_password),
    )
    webui_cfg = config.setdefault("webui", {})
    if isinstance(webui_cfg, dict):
        webui_cfg.setdefault("enabled", True)
        webui_cfg.setdefault("host", args.host)
        webui_cfg.setdefault("port", int(args.port))

    effective_auth = (
        webui_cfg.get("auth", {})
        if isinstance(webui_cfg, dict) and isinstance(webui_cfg.get("auth"), dict)
        else {}
    )
    if isinstance(effective_auth, dict):
        admin_password = str(effective_auth.get("admin_password", "") or "").strip()
        if pre_strip_admin_password and not admin_password and not args.allow_config_admin_password:
            print(
                "[sharelife] standalone admin login only accepts admin_password from local secrets TOML or SHARELIFE_ADMIN_PASSWORD; config-file admin_password is ignored by default.",
                file=sys.stderr,
            )

    server, api = build_server(data_root, config=config)
    if args.seed_demo:
        seed_demo_market(api)

    import uvicorn

    uvicorn.run(server.app, host=args.host, port=int(args.port), log_level="warning")


if __name__ == "__main__":
    main()
