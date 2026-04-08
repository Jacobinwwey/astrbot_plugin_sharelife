import base64
import re
from pathlib import Path
from typing import Any

from astrbot.api import logger, sp
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star, register

from .sharelife.application.services_apply import ApplyService
from .sharelife.application.services_audit import AuditService
from .sharelife.application.services_capability_gateway import CapabilityGateway
from .sharelife.application.services_continuity import ConfigContinuityService
from .sharelife.application.services_market import MarketService
from .sharelife.application.services_package import PackageService
from .sharelife.application.services_pipeline import PipelineOrchestrator, builtin_pipeline_plugins
from .sharelife.application.services_plugin_install import PluginInstallService
from .sharelife.application.services_preferences import PreferenceService
from .sharelife.application.services_protocol_contracts import ProtocolContractService
from .sharelife.application.services_profile_pack_bootstrap import ProfilePackBootstrapService
from .sharelife.application.services_profile_pack import ProfilePackService
from .sharelife.application.services_queue import RetryQueueService
from .sharelife.application.services_registry import RegistryService
from .sharelife.application.services_registry_bootstrap import RegistryBootstrapService
from .sharelife.application.services_reviewer_auth import ReviewerAuthService
from .sharelife.application.services_storage_backup import StorageBackupService
from .sharelife.application.services_trial import TrialService
from .sharelife.application.services_trial_request import TrialRequestService
from .sharelife.infrastructure.json_state_store import JsonStateStore
from .sharelife.infrastructure.local_webui_auth import merge_local_webui_auth_override
from .sharelife.infrastructure.local_store import LocalStore
from .sharelife.infrastructure.notifier import InMemoryNotifier
from .sharelife.infrastructure.official_registry_source import OfficialRegistrySource
from .sharelife.infrastructure.runtime_bridge import InMemoryRuntimeBridge, JsonFileRuntimeBridge
from .sharelife.infrastructure.sqlite_state_store import SqliteStateStore
from .sharelife.infrastructure.system_clock import SystemClock
from .sharelife.interfaces.api_v1 import SharelifeApiV1
from .sharelife.interfaces.web_api_v1 import SharelifeWebApiV1
from .sharelife.interfaces.webui_server import SharelifeWebUIServer


@register(
    "sharelife",
    "Jacobinwwey",
    "Sharelife community-first template governance plugin.",
    "0.3.13",
)
class SharelifePlugin(Star):
    def __init__(self, context: Context, config: dict | None = None):
        super().__init__(context, config=config)
        data_root = self._resolve_data_dir()
        self.config = merge_local_webui_auth_override(config or {}, data_root=data_root)
        state_stores = self._build_state_stores(data_root=data_root)
        preference_store = state_stores["preference_state"]
        retry_store = state_stores["retry_state"]
        trial_store = state_stores["trial_state"]
        trial_request_store = state_stores["trial_request_state"]
        notification_store = state_stores["notification_state"]
        market_store = state_stores["market_state"]
        audit_store = state_stores["audit_state"]
        profile_pack_store = state_stores["profile_pack_state"]
        reviewer_auth_store = state_stores["reviewer_auth_state"]
        storage_store = state_stores["storage_state"]
        continuity_store = state_stores["continuity_state"]
        package_root = data_root / "packages"
        registry_store = LocalStore(data_root)
        bundled_registry_path = Path(__file__).resolve().parent / "templates" / "index.json"
        configured_registry_url = str(self.config.get("official_registry_url", "") or "").strip()
        registry_index_url = configured_registry_url or str(bundled_registry_path)
        continuity_cfg = self._continuity_config()

        self.clock = SystemClock()
        self.preference_service = PreferenceService(state_store=preference_store)
        self.runtime_bridge = self._build_runtime_bridge(data_root=data_root)
        self.continuity_service = ConfigContinuityService(
            state_store=continuity_store,
            clock=self.clock,
            max_entries=self._to_int(continuity_cfg.get("max_entries"), default=50),
        )
        self.apply_service = ApplyService(
            runtime=self.runtime_bridge,
            continuity_service=self.continuity_service,
        )
        self.retry_queue_service = RetryQueueService(clock=self.clock, state_store=retry_store)
        self.trial_service = TrialService(clock=self.clock, state_store=trial_store)
        self.market_service = MarketService(clock=self.clock, state_store=market_store)
        self.package_service = PackageService(
            market_service=self.market_service,
            output_root=package_root,
            clock=self.clock,
        )
        profile_pack_cfg = self._profile_pack_config()
        plugin_install_cfg = (
            profile_pack_cfg.get("plugin_install", {})
            if isinstance(profile_pack_cfg.get("plugin_install"), dict)
            else {}
        )
        self.plugin_install_service = PluginInstallService(
            enabled=self._to_bool(plugin_install_cfg.get("enabled"), default=False),
            command_timeout_seconds=self._to_int(plugin_install_cfg.get("command_timeout_seconds"), default=180),
            allowed_command_prefixes=self._split_csv_or_list(
                plugin_install_cfg.get("allowed_command_prefixes"),
                default=["astrbot", "pip", "uv", "npm", "pnpm"],
            ),
            allow_http_source=self._to_bool(plugin_install_cfg.get("allow_http_source"), default=False),
            require_success_before_apply=self._to_bool(
                plugin_install_cfg.get("require_success_before_apply"),
                default=False,
            ),
        )
        self.profile_pack_service = ProfilePackService(
            runtime=self.runtime_bridge,
            apply_service=self.apply_service,
            output_root=data_root / "profile_packs",
            clock=self.clock,
            plugin_install_service=self.plugin_install_service,
            astrbot_version=str(self.config.get("astrbot_version", "") or ""),
            plugin_version="0.3.13",
            state_store=profile_pack_store,
            signing_key_id=str(profile_pack_cfg.get("signing_key_id", "") or ""),
            signing_secret=str(profile_pack_cfg.get("signing_secret", "") or ""),
            trusted_signing_keys=self._trusted_signing_keys(profile_pack_cfg.get("trusted_signing_keys")),
            secrets_encryption_key=str(profile_pack_cfg.get("secrets_encryption_key", "") or ""),
        )
        self.notifier = InMemoryNotifier(state_store=notification_store)
        self.audit_service = AuditService(clock=self.clock, state_store=audit_store)
        reviewer_auth_cfg = self._reviewer_device_key_config()
        self.reviewer_auth_service = ReviewerAuthService(
            state_store=reviewer_auth_store,
            max_devices=self._to_int(reviewer_auth_cfg.get("max_reviewer_devices"), default=3),
        )
        self.storage_backup_service = StorageBackupService(
            state_store=storage_store,
            data_root=data_root,
            clock=self.clock,
        )
        self.protocol_contract_service = ProtocolContractService()
        self.capability_gateway = CapabilityGateway(audit_service=self.audit_service)
        self.pipeline_orchestrator = PipelineOrchestrator(
            contract_service=self.protocol_contract_service,
            capability_gateway=self.capability_gateway,
        )
        for plugin_ref, runtime in builtin_pipeline_plugins().items():
            self.pipeline_orchestrator.register_plugin(
                plugin_ref=plugin_ref,
                handler=runtime.handler,
                required_capabilities=runtime.required_capabilities,
            )
        self.registry_service = RegistryService(
            source=OfficialRegistrySource(registry_index_url),
            store=registry_store,
        )
        self.registry_bootstrap_service = RegistryBootstrapService(
            registry_service=self.registry_service,
            market_service=self.market_service,
        )
        self.profile_pack_bootstrap_service = ProfilePackBootstrapService(
            profile_pack_service=self.profile_pack_service,
        )
        public_market_cfg = self._public_market_config()
        public_market_root = str(
            public_market_cfg.get(
                "root",
                str(Path(__file__).resolve().parent / "docs" / "public"),
            )
            or str(Path(__file__).resolve().parent / "docs" / "public")
        ).strip()
        self.trial_request_service = TrialRequestService(
            trial_service=self.trial_service,
            retry_queue_service=self.retry_queue_service,
            notifier=self.notifier,
            state_store=trial_request_store,
        )
        self.registry_bootstrap_service.sync()
        self.profile_pack_bootstrap_service.sync()
        self.api = SharelifeApiV1(
            preference_service=self.preference_service,
            retry_queue_service=self.retry_queue_service,
            trial_request_service=self.trial_request_service,
            market_service=self.market_service,
            package_service=self.package_service,
            apply_service=self.apply_service,
            audit_service=self.audit_service,
            profile_pack_service=self.profile_pack_service,
            pipeline_orchestrator=self.pipeline_orchestrator,
            reviewer_auth_service=self.reviewer_auth_service,
            storage_backup_service=self.storage_backup_service,
            public_market_auto_publish_profile_pack_approve=self._to_bool(
                public_market_cfg.get("auto_publish_profile_pack_approve"),
                default=False,
            ),
            public_market_root=public_market_root,
            public_market_rebuild_snapshot_on_publish=self._to_bool(
                public_market_cfg.get("rebuild_snapshot_on_publish"),
                default=True,
            ),
        )
        self.web_api = SharelifeWebApiV1(
            api=self.api,
            notifier=self.notifier,
        )
        web_root = Path(__file__).resolve().parent / "sharelife" / "webui"
        self.webui_server = SharelifeWebUIServer(
            api=self.web_api,
            config=self.config,
            web_root=web_root,
        )

    def _resolve_data_dir(self) -> Path:
        try:
            return sp.get_data_dir("sharelife")
        except Exception:
            fallback = Path.cwd() / ".sharelife_data"
            fallback.mkdir(parents=True, exist_ok=True)
            return fallback

    def _state_store_config(self) -> dict:
        raw = self.config.get("state_store", {}) if isinstance(self.config, dict) else {}
        if isinstance(raw, dict):
            return raw
        return {}

    @staticmethod
    def _state_store_filenames() -> dict[str, str]:
        return {
            "preference_state": "preference_state.json",
            "retry_state": "retry_state.json",
            "trial_state": "trial_state.json",
            "trial_request_state": "trial_request_state.json",
            "notification_state": "notification_state.json",
            "market_state": "market_state.json",
            "audit_state": "audit_state.json",
            "profile_pack_state": "profile_pack_state.json",
            "reviewer_auth_state": "reviewer_auth_state.json",
            "storage_state": "storage_state.json",
            "continuity_state": "continuity_state.json",
        }

    def _reviewer_device_key_config(self) -> dict:
        webui_cfg = self.config.get("webui", {}) if isinstance(self.config, dict) else {}
        if not isinstance(webui_cfg, dict):
            return {}
        raw = webui_cfg.get("device_keys", {})
        if isinstance(raw, dict):
            return raw
        return {}

    def _build_state_stores(self, *, data_root: Path) -> dict[str, Any]:
        mapping = self._state_store_filenames()
        cfg = self._state_store_config()
        backend = str(cfg.get("backend", "json") or "json").strip().lower()

        if backend in {"sqlite", "sqlite3"}:
            sqlite_file = str(cfg.get("sqlite_file", "") or "").strip()
            sqlite_path = Path(sqlite_file).expanduser() if sqlite_file else (data_root / "sharelife_state.sqlite3")
            stores = {
                store_key: SqliteStateStore(sqlite_path, store_key=store_key)
                for store_key in mapping
            }
            migrate_from_json = self._to_bool(cfg.get("migrate_from_json"), default=True)
            if migrate_from_json:
                for store_key, filename in mapping.items():
                    legacy_path = data_root / filename
                    stores[store_key].import_from_json_file(legacy_path)
            return stores

        if backend not in {"json", "json_file"}:
            logger.warning("[sharelife] unknown state_store backend '%s', fallback to json", backend)
        return {
            store_key: JsonStateStore(data_root / filename)
            for store_key, filename in mapping.items()
        }

    def _build_runtime_bridge(self, data_root: Path):
        runtime_cfg = self.config.get("runtime", {}) if isinstance(self.config, dict) else {}
        runtime_cfg = runtime_cfg if isinstance(runtime_cfg, dict) else {}
        adapter = str(runtime_cfg.get("adapter", "json_file") or "json_file").strip().lower()
        merge_mode = str(runtime_cfg.get("merge_mode", "replace") or "replace").strip().lower()
        initial_state = runtime_cfg.get("initial_state", {})
        if not isinstance(initial_state, dict):
            initial_state = {}

        if adapter == "in_memory":
            return InMemoryRuntimeBridge(initial_state=initial_state, merge_mode=merge_mode)

        state_file = str(runtime_cfg.get("state_file", "") or "").strip()
        state_path = Path(state_file).expanduser() if state_file else (data_root / "runtime_state.json")
        if adapter not in {"json_file", "in_memory"}:
            logger.warning("[sharelife] unknown runtime adapter '%s', fallback to json_file", adapter)
        return JsonFileRuntimeBridge(
            state_path=state_path,
            initial_state=initial_state,
            merge_mode=merge_mode,
        )

    def _profile_pack_config(self) -> dict:
        raw = self.config.get("profile_pack", {}) if isinstance(self.config, dict) else {}
        if isinstance(raw, dict):
            return raw
        return {}

    def _continuity_config(self) -> dict:
        raw = self.config.get("continuity", {}) if isinstance(self.config, dict) else {}
        if isinstance(raw, dict):
            return raw
        return {}

    def _public_market_config(self) -> dict:
        if not isinstance(self.config, dict):
            return {}
        webui_cfg = self.config.get("webui", {})
        if isinstance(webui_cfg, dict):
            public_market_cfg = webui_cfg.get("public_market", {})
            if isinstance(public_market_cfg, dict):
                return public_market_cfg
        fallback = self.config.get("public_market", {})
        if isinstance(fallback, dict):
            return fallback
        return {}

    @staticmethod
    def _to_bool(value, default: bool = False) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return bool(value)
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "yes", "on"}:
                return True
            if normalized in {"0", "false", "no", "off"}:
                return False
        return default

    @staticmethod
    def _to_int(value, default: int) -> int:
        try:
            return int(value)
        except Exception:
            return default

    @staticmethod
    def _split_csv_or_list(value, *, default: list[str] | None = None) -> list[str]:
        if isinstance(value, list):
            raw = value
        elif isinstance(value, str):
            raw = value.split(",")
        else:
            raw = default or []
        out: list[str] = []
        seen: set[str] = set()
        for item in raw:
            text = str(item or "").strip()
            if not text or text in seen:
                continue
            seen.add(text)
            out.append(text)
        return out

    @staticmethod
    def _trusted_signing_keys(raw: object) -> dict[str, str]:
        if not isinstance(raw, dict):
            return {}
        out: dict[str, str] = {}
        for key_id, secret in raw.items():
            normalized_key_id = str(key_id or "").strip()
            normalized_secret = str(secret or "").strip()
            if normalized_key_id and normalized_secret:
                out[normalized_key_id] = normalized_secret
        return out

    def _sender_id(self, event: AstrMessageEvent) -> str:
        getter = getattr(event, "get_sender_id", None)
        if callable(getter):
            return str(getter())
        return "unknown"

    def _session_id(self, event: AstrMessageEvent) -> str:
        getter = getattr(event, "get_session_id", None)
        if callable(getter):
            return str(getter())
        return "default"

    @staticmethod
    def _actor_role(event: AstrMessageEvent) -> str:
        return str(getattr(event, "role", "member") or "member")

    @staticmethod
    def _default_plan_id(template_id: str) -> str:
        normalized = re.sub(r"[^a-z0-9]+", "-", template_id.strip().lower()).strip("-")
        return f"plan-{normalized or 'template'}"

    @staticmethod
    def _apply_error_message(response: dict) -> str | None:
        code = str(response.get("error", "") or "")
        if code == "permission_denied":
            return "permission denied"
        if code == "plan_not_found":
            return "plan not found"
        if code == "plan_not_applied":
            return "plan has not been applied yet"
        return None

    @staticmethod
    def _format_trial_status(status: dict) -> str:
        summary = f"trial status: {status['status']} template_id={status['template_id']}"
        if status.get("status") != "not_started":
            summary += (
                f" ttl_seconds={status.get('ttl_seconds', 0)}"
                f" remaining_seconds={status.get('remaining_seconds', 0)}"
            )
        return summary

    @staticmethod
    def _safe_limit(value: int | str, default: int = 20) -> int:
        try:
            parsed = int(value)
        except Exception:
            parsed = default
        return max(1, min(parsed, 200))

    @staticmethod
    def _normalize_sections_csv(value: str) -> list[str]:
        out: list[str] = []
        seen: set[str] = set()
        for item in str(value or "").split(","):
            text = item.strip()
            if not text or text in seen:
                continue
            seen.add(text)
            out.append(text)
        return out

    @staticmethod
    def _parse_profile_import_options(tokens: tuple[str, ...]) -> tuple[bool, str, list[str] | None, str | None]:
        auto_dryrun = False
        plan_id = ""
        selected_sections: list[str] = []
        index = 0
        while index < len(tokens):
            token = str(tokens[index] or "").strip()
            if not token:
                index += 1
                continue
            if token in {"--dryrun", "--auto-dryrun"}:
                auto_dryrun = True
                index += 1
                continue
            if token.startswith("--plan-id="):
                plan_id = token.split("=", 1)[1].strip()
                if not plan_id:
                    return auto_dryrun, "", None, "plan-id value required"
                index += 1
                continue
            if token == "--plan-id":
                if index + 1 >= len(tokens):
                    return auto_dryrun, "", None, "plan-id value required"
                plan_id = str(tokens[index + 1] or "").strip()
                if not plan_id:
                    return auto_dryrun, "", None, "plan-id value required"
                index += 2
                continue
            if token.startswith("--sections="):
                selected_sections = SharelifePlugin._normalize_sections_csv(token.split("=", 1)[1])
                if not selected_sections:
                    return auto_dryrun, plan_id, None, "sections value required"
                index += 1
                continue
            if token == "--sections":
                if index + 1 >= len(tokens):
                    return auto_dryrun, plan_id, None, "sections value required"
                selected_sections = SharelifePlugin._normalize_sections_csv(tokens[index + 1])
                if not selected_sections:
                    return auto_dryrun, plan_id, None, "sections value required"
                index += 2
                continue
            return auto_dryrun, plan_id, None, f"unsupported option: {token}"
        return auto_dryrun, plan_id, (selected_sections or None), None

    async def initialize(self) -> None:
        await self.webui_server.start()

    async def terminate(self) -> None:
        await self.webui_server.stop()

    @filter.command("sharelife")
    async def sharelife(self, event: AstrMessageEvent):
        """Sharelife command entrypoint."""
        yield event.plain_result(
            "Sharelife ready. Use /sharelife_webui, /sharelife_pref, /sharelife_mode, /sharelife_observe, /sharelife_submit, /sharelife_market, /sharelife_install, /sharelife_prompt, /sharelife_package, /sharelife_submission_list, /sharelife_submission_decide, /sharelife_trial, /sharelife_trial_status, /sharelife_retry_list, /sharelife_retry_lock, /sharelife_retry_decide, /sharelife_dryrun, /sharelife_apply, /sharelife_rollback, /sharelife_audit, /sharelife_profile_export, /sharelife_profile_import, /sharelife_profile_import_dryrun, /sharelife_profile_import_dryrun_latest, /sharelife_profile_exports, /sharelife_profile_imports, /sharelife_profile_plugins, /sharelife_profile_plugins_confirm, /sharelife_profile_plugins_install."
        )

    @filter.command("sharelife_webui")
    async def sharelife_webui(self, event: AstrMessageEvent):
        """Show standalone Sharelife WebUI status and URL."""
        status = self.webui_server.status_payload()
        if not status.get("available"):
            yield event.plain_result(
                "sharelife webui unavailable: missing fastapi/uvicorn dependency"
            )
            return

        if status.get("enabled") and not status.get("running"):
            await self.webui_server.start()
            status = self.webui_server.status_payload()

        if not status.get("enabled"):
            yield event.plain_result("sharelife webui disabled by config: webui.enabled=false")
            return

        url = status.get("url") or "(starting...)"
        auth_required = "on" if status.get("auth_required") else "off"
        yield event.plain_result(f"sharelife webui: {url} (auth={auth_required})")

    @filter.command("sharelife_pref")
    async def sharelife_pref(self, event: AstrMessageEvent):
        """Show current preference values for execution mode and detail observability."""
        pref = self.api.get_preferences(user_id=self._sender_id(event))
        mode = pref["execution_mode"]
        observe = pref["observe_task_details"]
        observe_text = "on" if observe else "off"
        yield event.plain_result(
            f"execution_mode={mode}; observe_task_details={observe_text}"
        )

    @filter.command("sharelife_mode")
    async def sharelife_mode(self, event: AstrMessageEvent, mode: str = ""):
        """Switch execution mode: subagent_driven | inline_execution."""
        if mode not in {"subagent_driven", "inline_execution"}:
            yield event.plain_result(
                "Invalid mode. Use subagent_driven or inline_execution."
            )
            return

        self.api.set_preference_mode(user_id=self._sender_id(event), mode=mode)
        yield event.plain_result("execution mode updated")

    @filter.command("sharelife_observe")
    async def sharelife_observe(self, event: AstrMessageEvent, enabled: str = ""):
        """Toggle task detail observability: on/off."""
        normalized = enabled.strip().lower()
        if normalized not in {"on", "off", "true", "false", "1", "0", "yes", "no"}:
            yield event.plain_result("Invalid flag. Use on/off.")
            return

        is_enabled = normalized in {"on", "true", "1", "yes"}
        self.api.set_preference_observe(
            user_id=self._sender_id(event),
            enabled=is_enabled,
        )
        yield event.plain_result("task detail observability updated")

    @filter.command("sharelife_trial")
    async def sharelife_trial(self, event: AstrMessageEvent, template_id: str = ""):
        """Start first trial or enqueue retry request for repeated trial."""
        if not template_id:
            yield event.plain_result("template_id is required")
            return

        result = self.api.request_trial(
            user_id=self._sender_id(event),
            session_id=self._session_id(event),
            template_id=template_id,
        )
        if result["status"] == "trial_started":
            yield event.plain_result("trial started")
            return
        yield event.plain_result("retry request queued")

    @filter.command("sharelife_trial_status")
    async def sharelife_trial_status(self, event: AstrMessageEvent, template_id: str = ""):
        """Show trial status for the current user/session and template."""
        if not template_id:
            yield event.plain_result("template_id is required")
            return

        status = self.api.get_trial_status(
            user_id=self._sender_id(event),
            session_id=self._session_id(event),
            template_id=template_id,
        )
        yield event.plain_result(self._format_trial_status(status))

    @filter.command("sharelife_submit")
    async def sharelife_submit(
        self,
        event: AstrMessageEvent,
        template_id: str = "",
        version: str = "1.0.0",
    ):
        """User submits template metadata into community market queue."""
        if not template_id:
            yield event.plain_result("template_id is required")
            return

        response = self.api.submit_template(
            user_id=self._sender_id(event),
            template_id=template_id,
            version=version,
        )
        submission_id = response.get("submission_id", "")
        if submission_id:
            yield event.plain_result(f"template submitted: {submission_id}")
            return
        yield event.plain_result("template submitted")

    @filter.command("sharelife_market")
    async def sharelife_market(self, event: AstrMessageEvent):
        """List published templates available for install."""
        response = self.api.list_templates()
        templates = response.get("templates", [])
        if not templates:
            yield event.plain_result("no published templates")
            return

        lines = [
            (
                f"{item['template_id']}@{item['version']}"
                + (f" [{item.get('category')}]" if item.get("category") else "")
            )
            for item in templates
        ]
        yield event.plain_result("\n".join(lines))

    @filter.command("sharelife_install")
    async def sharelife_install(self, event: AstrMessageEvent, template_id: str = ""):
        """Install approved template and start trial/queue flow."""
        if not template_id:
            yield event.plain_result("template_id is required")
            return
        response = self.api.install_template(
            user_id=self._sender_id(event),
            session_id=self._session_id(event),
            template_id=template_id,
        )
        if response.get("status") == "not_installable":
            yield event.plain_result("template is not approved for install")
            return
        yield event.plain_result("template install processed")

    @filter.command("sharelife_prompt")
    async def sharelife_prompt(self, event: AstrMessageEvent, template_id: str = ""):
        """Generate prompt bundle for an approved template."""
        if not template_id:
            yield event.plain_result("template_id is required")
            return
        try:
            response = self.api.generate_prompt_bundle(template_id=template_id)
        except ValueError:
            yield event.plain_result("template is not approved for install")
            return
        prompt = response.get("prompt")
        if prompt:
            yield event.plain_result(prompt)
            return
        yield event.plain_result("prompt bundle generated")

    @filter.command("sharelife_package")
    async def sharelife_package(self, event: AstrMessageEvent, template_id: str = ""):
        """Generate downloadable package artifact for approved template."""
        if not template_id:
            yield event.plain_result("template_id is required")
            return

        response = self.api.generate_package(template_id=template_id)
        path = response.get("path")
        if path:
            yield event.plain_result(f"template package generated: {path}")
            return
        yield event.plain_result("template is not approved for install")

    @filter.command("sharelife_submission_list")
    async def sharelife_submission_list(self, event: AstrMessageEvent, status: str = ""):
        """Admin-only submission list."""
        role = str(getattr(event, "role", "member"))
        response = self.api.admin_list_submissions(role=role, status=status)
        if response.get("error") == "permission_denied":
            yield event.plain_result("permission denied")
            return
        submissions = response.get("submissions", [])
        if not submissions:
            yield event.plain_result("submissions listed")
            return
        lines = [
            f"{item['id']} {item['template_id']}@{item['version']} [{item['status']}]"
            for item in submissions
        ]
        yield event.plain_result("\n".join(lines))

    @filter.command("sharelife_submission_decide")
    async def sharelife_submission_decide(
        self,
        event: AstrMessageEvent,
        submission_id: str = "",
        decision: str = "",
    ):
        """Admin-only decision for user submitted templates."""
        if not submission_id:
            yield event.plain_result("submission_id is required")
            return
        if decision.strip().lower() not in {"approve", "reject", "approved", "rejected"}:
            yield event.plain_result("invalid decision. Use approve or reject.")
            return

        role = str(getattr(event, "role", "member"))
        response = self.api.admin_decide_submission(
            role=role,
            submission_id=submission_id,
            decision=decision,
        )
        if response.get("error") == "permission_denied":
            yield event.plain_result("permission denied")
            return
        yield event.plain_result("submission decided")

    @filter.command("sharelife_retry_list")
    async def sharelife_retry_list(self, event: AstrMessageEvent):
        """Admin-only retry request list."""
        role = str(getattr(event, "role", "member"))
        response = self.api.admin_list_retry_requests(role=role)
        if response.get("error") == "permission_denied":
            yield event.plain_result("permission denied")
            return
        requests = response.get("requests", [])
        if not requests:
            yield event.plain_result("retry requests listed")
            return
        lines = [
            f"{item['id']} {item['template_id']} [{item['state']}] v{item['version']}"
            for item in requests
        ]
        yield event.plain_result("\n".join(lines))

    @filter.command("sharelife_retry_decide")
    async def sharelife_retry_decide(
        self,
        event: AstrMessageEvent,
        request_id: str = "",
        decision: str = "",
        request_version: int = 0,
        lock_version: int = 0,
    ):
        """Admin-only retry decision with optimistic version guards."""
        if not request_id:
            yield event.plain_result("request_id is required")
            return
        if decision.strip().lower() not in {"approve", "reject", "approved", "rejected"}:
            yield event.plain_result("invalid decision. Use approve or reject.")
            return

        role = str(getattr(event, "role", "member"))
        response = self.api.admin_decide_retry_request(
            role=role,
            request_id=request_id,
            decision=decision,
            admin_id=self._sender_id(event),
            request_version=request_version or None,
            lock_version=lock_version or None,
        )
        if response.get("error") == "permission_denied":
            yield event.plain_result("permission denied")
            return
        if response.get("error") == "request_version_conflict":
            yield event.plain_result("request version conflict, refresh and retry")
            return
        if response.get("error") == "lock_version_conflict":
            yield event.plain_result("lock version conflict, refresh and retry")
            return
        if response.get("error") == "review_lock_required":
            yield event.plain_result("review lock required, call /sharelife_retry_lock first")
            return
        if response.get("error") == "review_lock_not_owner":
            yield event.plain_result("you are not lock owner for this request")
            return
        yield event.plain_result("retry request decided")

    @filter.command("sharelife_retry_lock")
    async def sharelife_retry_lock(
        self,
        event: AstrMessageEvent,
        request_id: str = "",
        force: str = "no",
        reason: str = "",
    ):
        """Admin-only lock acquire for retry request review."""
        if not request_id:
            yield event.plain_result("request_id is required")
            return
        normalized_force = force.strip().lower()
        is_force = normalized_force in {"yes", "true", "1", "force"}
        role = str(getattr(event, "role", "member"))
        response = self.api.admin_acquire_retry_lock(
            role=role,
            request_id=request_id,
            admin_id=self._sender_id(event),
            force=is_force,
            reason=reason,
        )
        if response.get("error") == "permission_denied":
            yield event.plain_result("permission denied")
            return
        if response.get("error") == "review_lock_held":
            yield event.plain_result("review lock already held by another admin")
            return
        if response.get("error") == "takeover_reason_required":
            yield event.plain_result("takeover reason required when force=true")
            return
        yield event.plain_result(
            f"lock acquired v{response['lock_version']} expires_at={response['expires_at']}"
        )

    @filter.command("sharelife_dryrun")
    async def sharelife_dryrun(
        self,
        event: AstrMessageEvent,
        template_id: str = "",
        version: str = "1.0.0",
        plan_id: str = "",
    ):
        """Admin-only dryrun entrypoint for a template patch plan."""
        if not template_id:
            yield event.plain_result("template_id is required")
            return

        resolved_plan_id = plan_id.strip() or self._default_plan_id(template_id)
        response = self.api.admin_dryrun(
            role=self._actor_role(event),
            plan_id=resolved_plan_id,
            patch={"template_id": template_id, "version": version or "1.0.0"},
        )
        error_message = self._apply_error_message(response)
        if error_message:
            yield event.plain_result(error_message)
            return
        yield event.plain_result(f"dryrun ready: {resolved_plan_id}")

    @filter.command("sharelife_apply")
    async def sharelife_apply(self, event: AstrMessageEvent, plan_id: str = ""):
        """Admin-only apply entrypoint."""
        if not plan_id:
            yield event.plain_result("plan_id is required")
            return

        response = self.api.admin_apply(role=self._actor_role(event), plan_id=plan_id)
        error_message = self._apply_error_message(response)
        if error_message == "permission denied":
            logger.info("sharelife_apply denied for non-admin user")
            yield event.plain_result(error_message)
            return
        if error_message:
            yield event.plain_result(error_message)
            return
        yield event.plain_result("plan applied")

    @filter.command("sharelife_rollback")
    async def sharelife_rollback(self, event: AstrMessageEvent, plan_id: str = ""):
        """Admin-only rollback entrypoint."""
        if not plan_id:
            yield event.plain_result("plan_id is required")
            return

        response = self.api.admin_rollback(role=self._actor_role(event), plan_id=plan_id)
        error_message = self._apply_error_message(response)
        if error_message:
            yield event.plain_result(error_message)
            return
        yield event.plain_result("plan rolled back")

    @filter.command("sharelife_audit")
    async def sharelife_audit(self, event: AstrMessageEvent, limit: int = 20):
        """Admin-only audit event listing."""
        response = self.api.admin_list_audit(role=self._actor_role(event), limit=self._safe_limit(limit))
        if response.get("error") == "permission_denied":
            yield event.plain_result("permission denied")
            return
        events = response.get("events", [])
        if not events:
            yield event.plain_result("no audit events")
            return
        lines = [
            f"{item['created_at']} {item['action']} {item['status']} target={item['target_id']}"
            for item in events
        ]
        yield event.plain_result("\n".join(lines))

    @filter.command("sharelife_profile_export")
    async def sharelife_profile_export(
        self,
        event: AstrMessageEvent,
        pack_id: str = "",
        version: str = "1.0.0",
        redaction_mode: str = "exclude_secrets",
        sections_csv: str = "",
        mask_paths_csv: str = "",
        drop_paths_csv: str = "",
        pack_type: str = "bot_profile_pack",
    ):
        """Admin-only export of current runtime state into bot_profile_pack artifact."""
        if not pack_id:
            yield event.plain_result("pack_id is required")
            return
        sections = self._normalize_sections_csv(sections_csv) if sections_csv else None
        mask_paths = self._normalize_sections_csv(mask_paths_csv) if mask_paths_csv else None
        drop_paths = self._normalize_sections_csv(drop_paths_csv) if drop_paths_csv else None
        response = self.api.admin_export_profile_pack(
            role=self._actor_role(event),
            pack_id=pack_id,
            version=version or "1.0.0",
            pack_type=pack_type or "bot_profile_pack",
            redaction_mode=redaction_mode or "exclude_secrets",
            sections=sections,
            mask_paths=mask_paths,
            drop_paths=drop_paths,
        )
        error_code = str(response.get("error", "") or "")
        if error_code == "permission_denied":
            yield event.plain_result("permission denied")
            return
        if error_code == "invalid_redaction_mode":
            yield event.plain_result("invalid redaction mode")
            return
        if error_code == "invalid_pack_type":
            yield event.plain_result("invalid profile pack type")
            return
        if error_code:
            yield event.plain_result(error_code)
            return
        yield event.plain_result(f"profile pack exported: {response.get('artifact_id', '')}")

    @filter.command("sharelife_profile_exports")
    async def sharelife_profile_exports(self, event: AstrMessageEvent, limit: int | str = 20):
        """Admin-only list of exported bot_profile_pack artifacts."""
        response = self.api.admin_list_profile_pack_exports(
            role=self._actor_role(event),
            limit=self._safe_limit(limit),
        )
        if response.get("error") == "permission_denied":
            yield event.plain_result("permission denied")
            return
        rows = response.get("exports", [])
        if not rows:
            yield event.plain_result("no exported profile packs")
            return
        lines = [
            f"{item.get('artifact_id', '')} {item.get('pack_id', '')}@{item.get('version', '')} {item.get('filename', '')}"
            for item in rows
        ]
        yield event.plain_result("\n".join(lines))

    @filter.command("sharelife_profile_import")
    async def sharelife_profile_import(self, event: AstrMessageEvent, source: str = "", *extra: str):
        """Admin-only import of bot_profile_pack from exported artifact id or local zip path."""
        source_text = str(source or "").strip()
        if not source_text:
            yield event.plain_result("source is required")
            return

        role = self._actor_role(event)
        auto_dryrun, plan_id_opt, selected_sections, parse_error = self._parse_profile_import_options(extra)
        if parse_error:
            yield event.plain_result(parse_error)
            return

        resolved_path: Path | None = None
        filename = ""

        artifact = self.api.admin_get_profile_pack_export(role=role, artifact_id=source_text)
        artifact_error = str(artifact.get("error", "") or "")
        if artifact_error == "permission_denied":
            yield event.plain_result("permission denied")
            return
        if not artifact.get("error"):
            candidate = Path(str(artifact.get("path", "") or "")).expanduser()
            if candidate.exists():
                resolved_path = candidate
                filename = str(artifact.get("filename", "") or candidate.name)

        if resolved_path is None:
            candidate = Path(source_text).expanduser()
            if not candidate.exists() or not candidate.is_file():
                yield event.plain_result("artifact or file not found")
                return
            resolved_path = candidate
            filename = candidate.name

        try:
            encoded = base64.b64encode(resolved_path.read_bytes()).decode("ascii")
        except Exception:
            yield event.plain_result("failed to read profile pack file")
            return

        response = self.api.admin_import_profile_pack(
            role=role,
            filename=filename,
            content_base64=encoded,
        )
        error = str(response.get("error", "") or "")
        if error == "permission_denied":
            yield event.plain_result("permission denied")
            return
        if error:
            yield event.plain_result(error)
            return
        import_id = str(response.get("import_id", "") or "")
        message = f"profile pack imported: {import_id}"
        if not auto_dryrun:
            yield event.plain_result(message)
            return

        resolved_plan_id = plan_id_opt or self._default_plan_id(str(response.get("pack_id", "") or "profile-pack"))
        dryrun = self.api.admin_profile_pack_dryrun(
            role=role,
            import_id=import_id,
            plan_id=resolved_plan_id,
            selected_sections=selected_sections,
        )
        dryrun_error = str(dryrun.get("error", "") or "")
        if dryrun_error:
            yield event.plain_result(f"{message} | dryrun failed: {dryrun_error}")
            return
        yield event.plain_result(f"{message} | dryrun ready: {resolved_plan_id}")

    @filter.command("sharelife_profile_import_dryrun")
    async def sharelife_profile_import_dryrun(
        self,
        event: AstrMessageEvent,
        source: str = "",
        plan_id: str = "",
        sections_csv: str = "",
    ):
        """Admin-only one-shot import + dryrun for bot_profile_pack."""
        source_text = str(source or "").strip()
        if not source_text:
            yield event.plain_result("source is required")
            return

        args: list[str] = ["--dryrun"]
        normalized_plan_id = str(plan_id or "").strip()
        if normalized_plan_id:
            args.extend(["--plan-id", normalized_plan_id])
        normalized_sections = str(sections_csv or "").strip()
        if normalized_sections:
            args.extend(["--sections", normalized_sections])

        response_text = ""
        async for item in self.sharelife_profile_import(event, source_text, *args):
            response_text = str(item or "")
        if not response_text:
            yield event.plain_result("profile pack import+dryrun failed")
            return
        marker = "dryrun ready:"
        if marker in response_text:
            ready_plan_id = response_text.split(marker, 1)[1].strip()
            yield event.plain_result(f"profile pack import+dryrun ready: {ready_plan_id}")
            return
        if "| dryrun failed:" in response_text:
            reason = response_text.split("| dryrun failed:", 1)[1].strip()
            yield event.plain_result(f"profile pack import+dryrun failed: {reason}")
            return
        yield event.plain_result(response_text)

    @filter.command("sharelife_profile_import_dryrun_latest")
    async def sharelife_profile_import_dryrun_latest(
        self,
        event: AstrMessageEvent,
        plan_id: str = "",
        sections_csv: str = "",
    ):
        """Admin-only import+dryrun from latest exported bot_profile_pack artifact."""
        response = self.api.admin_list_profile_pack_exports(
            role=self._actor_role(event),
            limit=1,
        )
        error = str(response.get("error", "") or "")
        if error == "permission_denied":
            yield event.plain_result("permission denied")
            return
        rows = response.get("exports", [])
        if not rows:
            yield event.plain_result("no exported profile packs")
            return
        latest_artifact = str(rows[0].get("artifact_id", "") or "")
        if not latest_artifact:
            yield event.plain_result("latest export artifact unavailable")
            return
        async for item in self.sharelife_profile_import_dryrun(
            event,
            latest_artifact,
            plan_id,
            sections_csv,
        ):
            yield item

    @filter.command("sharelife_profile_imports")
    async def sharelife_profile_imports(self, event: AstrMessageEvent, limit: int | str = 20):
        """Admin-only list of imported bot_profile_pack records."""
        response = self.api.admin_list_profile_pack_imports(
            role=self._actor_role(event),
            limit=self._safe_limit(limit),
        )
        if response.get("error") == "permission_denied":
            yield event.plain_result("permission denied")
            return
        rows = [
            item
            for item in response.get("imports", [])
            if not str(item.get("import_id", "") or "").startswith("official-import:")
        ]
        if not rows:
            yield event.plain_result("no imported profile packs")
            return
        lines = [
            f"{item.get('import_id', '')} {item.get('pack_id', '')}@{item.get('version', '')} {item.get('filename', '')} [{item.get('compatibility', 'unknown')}]"
            for item in rows
        ]
        yield event.plain_result("\n".join(lines))

    @filter.command("sharelife_profile_plugins")
    async def sharelife_profile_plugins(self, event: AstrMessageEvent, import_id: str = ""):
        """Admin-only view of plugin install plan for imported profile pack."""
        normalized_import_id = str(import_id or "").strip()
        if not normalized_import_id:
            yield event.plain_result("import_id is required")
            return

        response = self.api.admin_profile_pack_plugin_install_plan(
            role=self._actor_role(event),
            import_id=normalized_import_id,
        )
        error = str(response.get("error", "") or "")
        if error == "permission_denied":
            yield event.plain_result("permission denied")
            return
        if error:
            yield event.plain_result(error)
            return

        required = list(response.get("required_plugins", []) or [])
        missing = list(response.get("missing_plugins", []) or [])
        confirmed = list(response.get("confirmed_plugins", []) or [])
        status = str(response.get("status", "unknown") or "unknown")
        if not required:
            yield event.plain_result("plugin install plan: not required")
            return
        lines = [
            f"plugin install plan: {status}",
            f"required={','.join(required) or '-'}",
            f"missing={','.join(missing) or '-'}",
            f"confirmed={','.join(confirmed) or '-'}",
        ]
        yield event.plain_result("\n".join(lines))

    @filter.command("sharelife_profile_plugins_confirm")
    async def sharelife_profile_plugins_confirm(
        self,
        event: AstrMessageEvent,
        import_id: str = "",
        plugins_csv: str = "",
    ):
        """Admin-only confirmation for plugin install metadata in imported profile pack."""
        normalized_import_id = str(import_id or "").strip()
        if not normalized_import_id:
            yield event.plain_result("import_id is required")
            return
        plugin_ids = self._normalize_sections_csv(plugins_csv) if str(plugins_csv or "").strip() else None

        response = self.api.admin_profile_pack_confirm_plugin_install(
            role=self._actor_role(event),
            import_id=normalized_import_id,
            plugin_ids=plugin_ids,
        )
        error = str(response.get("error", "") or "")
        if error == "permission_denied":
            yield event.plain_result("permission denied")
            return
        if error == "profile_pack_plugin_not_in_plan":
            yield event.plain_result("plugin id not in install plan")
            return
        if error == "profile_pack_plugin_id_required":
            yield event.plain_result("plugin_ids is required")
            return
        if error:
            yield event.plain_result(error)
            return

        status = str(response.get("status", "unknown") or "unknown")
        missing = list(response.get("missing_plugins", []) or [])
        if missing:
            yield event.plain_result(f"plugin install confirmation updated: {status} missing={','.join(missing)}")
            return
        yield event.plain_result(f"plugin install confirmation updated: {status}")

    @filter.command("sharelife_profile_plugins_install")
    async def sharelife_profile_plugins_install(
        self,
        event: AstrMessageEvent,
        import_id: str = "",
        plugins_csv: str = "",
        dry_run: str = "",
    ):
        """Admin-only execute plugin install commands for imported profile pack metadata."""
        normalized_import_id = str(import_id or "").strip()
        if not normalized_import_id:
            yield event.plain_result("import_id is required")
            return
        plugin_ids = self._normalize_sections_csv(plugins_csv) if str(plugins_csv or "").strip() else None
        dry_run_enabled = self._to_bool(dry_run, default=False)

        response = self.api.admin_profile_pack_execute_plugin_install(
            role=self._actor_role(event),
            import_id=normalized_import_id,
            plugin_ids=plugin_ids,
            dry_run=dry_run_enabled,
        )
        error = str(response.get("error", "") or "")
        if error == "permission_denied":
            yield event.plain_result("permission denied")
            return
        if error == "profile_pack_plugin_not_in_plan":
            yield event.plain_result("plugin id not in install plan")
            return
        if error == "profile_pack_plugin_id_required":
            yield event.plain_result("plugin_ids is required")
            return
        if error == "profile_pack_plugin_install_confirm_required":
            yield event.plain_result("plugin install confirmation required")
            return
        if error == "profile_pack_plugin_install_exec_disabled":
            yield event.plain_result(
                "plugin install execution is disabled; set profile_pack.plugin_install.enabled=true"
            )
            return
        if error:
            yield event.plain_result(error)
            return

        status = str(response.get("status", "unknown") or "unknown")
        execution = response.get("execution", {}) if isinstance(response.get("execution"), dict) else {}
        output = execution.get("result", {}) if isinstance(execution.get("result"), dict) else {}
        installed_count = int(output.get("installed_count", 0) or 0)
        failed_count = int(output.get("failed_count", 0) or 0)
        blocked_count = int(output.get("blocked_count", 0) or 0)
        yield event.plain_result(
            f"plugin install execution: {status} installed={installed_count} failed={failed_count} blocked={blocked_count}"
        )
