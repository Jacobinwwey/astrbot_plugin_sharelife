from __future__ import annotations

import io
import json
import zipfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from sharelife.application.services_apply import ApplyService
from sharelife.application.services_plugin_install import PluginInstallService
from sharelife.application.services_profile_pack import ProfilePackService
from sharelife.infrastructure.json_state_store import JsonStateStore
from sharelife.infrastructure.runtime_bridge import InMemoryRuntimeBridge
from sharelife.infrastructure.sqlite_state_store import SqliteStateStore


class FrozenClock:
    def __init__(self, start: datetime):
        self.current = start

    def utcnow(self) -> datetime:
        return self.current

    def shift(self, **kwargs) -> None:
        self.current = self.current + timedelta(**kwargs)


def runtime_state_fixture() -> dict:
    return {
        "astrbot_core": {"name": "sharelife-bot", "language": "zh-CN"},
        "providers": {
            "openai": {
                "api_key": "sk-live-secret",
                "base_url": "https://api.openai.com/v1",
            }
        },
        "plugins": {"sharelife": {"enabled": True}},
        "skills": {"writing": {"enabled": True}},
        "personas": {"default": {"tone": "helpful"}},
        "mcp_servers": {"filesystem": {"endpoint": "http://127.0.0.1:9000"}},
        "sharelife_meta": {"owner": "u1"},
    }


def build_service(tmp_path, **service_kwargs):
    runtime = InMemoryRuntimeBridge(initial_state=runtime_state_fixture())
    apply_service = ApplyService(runtime=runtime)
    service = ProfilePackService(
        runtime=runtime,
        apply_service=apply_service,
        output_root=tmp_path,
        clock=FrozenClock(datetime(2026, 3, 30, 2, 0, tzinfo=UTC)),
        astrbot_version="4.16.0",
        plugin_version="0.1.0",
        **service_kwargs,
    )
    return service, apply_service, runtime


def astrbot_cmd_config_fixture(*, plugin_set: list[str] | None = None) -> dict:
    return {
        "config_version": 2,
        "provider": [
            {
                "id": "test-openai",
                "type": "openai_chat_completion",
                "provider": "openai",
                "model": "gpt-4o-mini",
                "key": ["test-key"],
                "base_url": "https://api.openai.com/v1",
            }
        ],
        "provider_settings": {
            "default_personality": "default",
            "prompt_prefix": "",
            "websearch_tavily_key": ["tvly-secret"],
            "identifier": True,
            "group_name_display": True,
        },
        "default_personality": "default",
        "dashboard": {
            "enable": True,
            "username": "astrbot",
            "password": "dashboard-secret",
            "jwt_secret": "jwt-secret",
            "port": 6185,
        },
        "admins_id": ["owner"],
        "platform": [],
        "timezone": "Asia/Shanghai",
        "plugin_set": list(plugin_set if plugin_set is not None else ["*"]),
    }


def build_astrbot_backup_zip(config_payload: dict, *, astrbot_version: str = "4.16.0") -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            "manifest.json",
            json.dumps(
                {
                    "manifest_version": 1,
                    "astrbot_version": astrbot_version,
                    "backup_time": "2026-04-07T12:00:00Z",
                },
                ensure_ascii=False,
                indent=2,
            ),
        )
        zf.writestr("config/cmd_config.json", json.dumps(config_payload, ensure_ascii=False, indent=2))
        zf.writestr("databases/main_db.json", json.dumps({"messages": []}, ensure_ascii=False))
        zf.writestr("directories/config/abconf_extra.json", json.dumps({"timezone": "UTC"}, ensure_ascii=False))
    return buffer.getvalue()


def test_export_profile_pack_generates_expected_zip_layout_and_redacts_provider_key(tmp_path):
    service, _, _ = build_service(tmp_path)

    artifact = service.export_bot_profile_pack(
        pack_id="profile/basic",
        version="1.0.0",
        redaction_mode="exclude_secrets",
    )

    assert artifact.path.exists()
    assert artifact.filename.endswith(".zip")

    with zipfile.ZipFile(artifact.path, "r") as zf:
        names = set(zf.namelist())
        assert "manifest.json" in names
        assert "sections/providers.json" in names

        manifest = json.loads(zf.read("manifest.json").decode("utf-8"))
        providers = json.loads(zf.read("sections/providers.json").decode("utf-8"))

        assert manifest["pack_type"] == "bot_profile_pack"
        assert providers["openai"]["api_key"] != "sk-live-secret"


def test_import_profile_pack_and_prepare_selective_apply_plan(tmp_path):
    service, apply_service, runtime = build_service(tmp_path)
    exported = service.export_bot_profile_pack(
        pack_id="profile/basic",
        version="1.0.0",
        redaction_mode="exclude_secrets",
    )
    runtime.state["plugins"] = {"legacy": {"enabled": False}}

    imported = service.import_bot_profile_pack(
        filename=exported.filename,
        content=exported.path.read_bytes(),
    )
    assert imported.import_id
    assert imported.manifest.pack_type == "bot_profile_pack"
    assert "plugins" in imported.sections
    evidence = imported.scan_summary.get("risk_evidence", [])
    assert any(item.get("file") == "sections/mcp_servers.json" for item in evidence)
    assert any(item.get("path", "").startswith("$.filesystem") for item in evidence)

    dryrun = service.prepare_apply_plan(
        import_id=imported.import_id,
        plan_id="plan-profile-basic",
        selected_sections=["plugins"],
    )
    assert dryrun["status"] == "dryrun_ready"
    assert dryrun["selected_sections"] == ["plugins"]
    assert "plugins" in dryrun["patch"]
    assert "providers" not in dryrun["patch"]

    apply_service.apply("plan-profile-basic")
    assert runtime.state["plugins"] == {"sharelife": {"enabled": True}}


def test_profile_pack_service_persists_export_and_import_records(tmp_path):
    runtime = InMemoryRuntimeBridge(initial_state=runtime_state_fixture())
    apply_service = ApplyService(runtime=runtime)
    state_store = JsonStateStore(tmp_path / "profile_pack_state.json")

    service = ProfilePackService(
        runtime=runtime,
        apply_service=apply_service,
        output_root=tmp_path / "packs",
        clock=FrozenClock(datetime(2026, 3, 30, 4, 0, tzinfo=UTC)),
        astrbot_version="4.16.0",
        plugin_version="0.1.0",
        state_store=state_store,
    )
    exported = service.export_bot_profile_pack(
        pack_id="profile/persistent",
        version="1.0.0",
        redaction_mode="exclude_secrets",
    )
    imported = service.import_bot_profile_pack(
        filename=exported.filename,
        content=exported.path.read_bytes(),
    )

    reloaded = ProfilePackService(
        runtime=runtime,
        apply_service=apply_service,
        output_root=tmp_path / "packs",
        clock=FrozenClock(datetime(2026, 3, 30, 5, 0, tzinfo=UTC)),
        astrbot_version="4.16.0",
        plugin_version="0.1.0",
        state_store=state_store,
    )

    exports = reloaded.list_exports(limit=10)
    imports = reloaded.list_imports(limit=10)

    assert len(exports) == 1
    assert exports[0]["artifact_id"] == exported.artifact_id
    assert len(imports) == 1
    assert imports[0]["import_id"] == imported.import_id


def test_profile_pack_service_persists_export_and_import_records_with_sqlite_store(tmp_path):
    runtime = InMemoryRuntimeBridge(initial_state=runtime_state_fixture())
    apply_service = ApplyService(runtime=runtime)
    state_store = SqliteStateStore(tmp_path / "sharelife_state.sqlite3", store_key="profile_pack_state")

    service = ProfilePackService(
        runtime=runtime,
        apply_service=apply_service,
        output_root=tmp_path / "packs",
        clock=FrozenClock(datetime(2026, 3, 30, 4, 0, tzinfo=UTC)),
        astrbot_version="4.16.0",
        plugin_version="0.1.0",
        state_store=state_store,
    )
    exported = service.export_bot_profile_pack(
        pack_id="profile/persistent-sqlite",
        version="1.0.0",
        redaction_mode="exclude_secrets",
    )
    imported = service.import_bot_profile_pack(
        filename=exported.filename,
        content=exported.path.read_bytes(),
    )

    reloaded = ProfilePackService(
        runtime=runtime,
        apply_service=apply_service,
        output_root=tmp_path / "packs",
        clock=FrozenClock(datetime(2026, 3, 30, 5, 0, tzinfo=UTC)),
        astrbot_version="4.16.0",
        plugin_version="0.1.0",
        state_store=state_store,
    )

    exports = reloaded.list_exports(limit=10)
    imports = reloaded.list_imports(limit=10)

    assert len(exports) == 1
    assert exports[0]["artifact_id"] == exported.artifact_id
    assert len(imports) == 1
    assert imports[0]["import_id"] == imported.import_id


def test_profile_pack_service_imports_legacy_state_store_payload_into_sqlite_repository(tmp_path):
    runtime = InMemoryRuntimeBridge(initial_state=runtime_state_fixture())
    apply_service = ApplyService(runtime=runtime)

    legacy_json_store = JsonStateStore(tmp_path / "legacy_profile_pack_state.json")
    legacy_service = ProfilePackService(
        runtime=runtime,
        apply_service=apply_service,
        output_root=tmp_path / "legacy-packs",
        clock=FrozenClock(datetime(2026, 3, 30, 2, 0, tzinfo=UTC)),
        astrbot_version="4.16.0",
        plugin_version="0.1.0",
        state_store=legacy_json_store,
    )
    exported = legacy_service.export_bot_profile_pack(
        pack_id="profile/legacy-migrate",
        version="1.0.0",
        redaction_mode="exclude_secrets",
    )
    imported = legacy_service.import_bot_profile_pack(
        filename=exported.filename,
        content=exported.path.read_bytes(),
    )

    legacy_payload = legacy_json_store.load(
        default={
            "exports": [],
            "imports": [],
            "submissions": [],
            "published": [],
            "plugin_install_confirmations": {},
            "plugin_install_executions": {},
        }
    )

    sqlite_store = SqliteStateStore(tmp_path / "sharelife_state.sqlite3", store_key="profile_pack_state")
    sqlite_store.save(legacy_payload)

    migrated_service = ProfilePackService(
        runtime=runtime,
        apply_service=apply_service,
        output_root=tmp_path / "legacy-packs",
        clock=FrozenClock(datetime(2026, 3, 30, 3, 0, tzinfo=UTC)),
        astrbot_version="4.16.0",
        plugin_version="0.1.0",
        state_store=sqlite_store,
    )

    exports = migrated_service.list_exports(limit=10)
    imports = migrated_service.list_imports(limit=10)
    assert len(exports) == 1
    assert len(imports) == 1
    assert exports[0]["artifact_id"] == exported.artifact_id
    assert imports[0]["import_id"] == imported.import_id


def test_profile_pack_service_converts_raw_astrbot_backup_zip_into_standard_member_artifact(tmp_path):
    service, _, _ = build_service(tmp_path)
    backup_bytes = build_astrbot_backup_zip(astrbot_cmd_config_fixture())

    imported = service.import_member_profile_pack(
        user_id="member-1",
        filename="astrbot_backup_20260407.zip",
        content=backup_bytes,
    )

    assert imported.user_id == "member-1"
    assert imported.source_artifact_id
    assert imported.filename.endswith(".zip")
    assert imported.compatibility == "degraded"
    assert "astrbot_raw_import_converted" in imported.compatibility_issues
    assert "astrbot_backup_runtime_payload_omitted" in imported.compatibility_issues
    assert "astrbot_operator_fields_omitted" in imported.compatibility_issues
    assert "astrbot_plugin_wildcard_unresolved" in imported.compatibility_issues
    imported_details = service.compatibility_issue_details(
        imported.compatibility_issues,
        sections=imported.sections,
        scan_summary=imported.scan_summary,
    )
    assert any(
        item["code"] == "astrbot_raw_import_converted" and "sharelife_meta" in item["sections"]
        for item in imported_details
    )
    assert any(
        item["code"] == "astrbot_operator_fields_omitted"
        and "astrbot_core.dashboard" in item["related_paths"]
        for item in imported_details
    )
    operator_issue = next(item for item in imported_details if item["code"] == "astrbot_operator_fields_omitted")
    assert operator_issue["evidence_refs"]
    assert operator_issue["evidence_refs"][0]["file"] == "sections/sharelife_meta.json"
    assert operator_issue["evidence_refs"][0]["path"] in {"astrbot_core.dashboard", "astrbot_core.admins_id"}
    summary = imported.sections["sharelife_meta"]["astrbot_import"]["summary"]
    assert summary["field_diagnostic_count"] >= 4
    assert isinstance(summary["field_diagnostics"], list)
    assert any(
        item.get("issue_code") == "astrbot_plugin_wildcard_unresolved"
        and item.get("source_path") == "plugin_set"
        for item in summary["field_diagnostics"]
    )
    assert imported.sections["sharelife_meta"]["astrbot_import"]["source_type"] == "astrbot_backup_zip"
    assert "dashboard" not in imported.sections["astrbot_core"]
    assert "admins_id" not in imported.sections["astrbot_core"]
    assert imported.sections["providers"]["test-openai"]["model"] == "gpt-4o-mini"
    assert "key" not in imported.sections["providers"]["test-openai"]

    artifact = service.get_export_artifact(imported.source_artifact_id)
    assert artifact.owner_user_id == "member-1"
    assert artifact.path.exists()
    with zipfile.ZipFile(artifact.path, "r") as zf:
        names = set(zf.namelist())
        assert "manifest.json" in names
        assert "sections/astrbot_core.json" in names
        assert "sections/providers.json" in names
        manifest = json.loads(zf.read("manifest.json").decode("utf-8"))
        meta = json.loads(zf.read("sections/sharelife_meta.json").decode("utf-8"))
    assert manifest["pack_type"] == "bot_profile_pack"
    assert meta["astrbot_import"]["source_filename"] == "astrbot_backup_20260407.zip"

    submission = service.submit_export_artifact(
        user_id="member-1",
        artifact_id=imported.source_artifact_id,
    )
    assert submission.status == "pending"
    assert submission.compatibility == "degraded"
    assert "astrbot_raw_import_converted" in submission.compatibility_issues
    assert submission.compatibility_matrix["runtime_issue_groups"]["conversion"]
    assert "astrbot_raw_import_converted" in submission.compatibility_matrix["runtime_issue_groups"]["conversion"]
    assert any(
        item["code"] == "astrbot_raw_import_converted"
        for item in submission.compatibility_matrix["runtime_issue_details"]
    )
    assert submission.review_evidence["compatibility_issue_groups"]["conversion"]
    assert any(
        item["code"] == "astrbot_raw_import_converted"
        for item in submission.review_evidence["compatibility_issue_details"]
    )


def test_profile_pack_service_compatibility_issue_groups_bucket_known_codes():
    grouped = ProfilePackService.compatibility_issue_groups(
        [
            "section_hash_mismatch:providers",
            "signature_invalid",
            "encrypted_secret_payload_invalid",
            "astrbot_version_mismatch",
            "plugin_compat_mismatch",
            "astrbot_raw_import_converted",
            "environment_plugin_binary_reconfigure_required",
            "knowledge_base_storage_sync_required",
            "custom_future_issue",
        ],
    )
    assert grouped["integrity"] == [
        "section_hash_mismatch:providers",
        "signature_invalid",
    ]
    assert grouped["security"] == ["encrypted_secret_payload_invalid"]
    assert grouped["version"] == ["astrbot_version_mismatch", "plugin_compat_mismatch"]
    assert grouped["conversion"] == ["astrbot_raw_import_converted"]
    assert grouped["environment"] == [
        "environment_plugin_binary_reconfigure_required",
        "knowledge_base_storage_sync_required",
    ]
    assert grouped["unknown"] == ["custom_future_issue"]


def test_profile_pack_service_compatibility_issue_details_attach_related_paths_and_evidence():
    details = ProfilePackService.compatibility_issue_details(
        ["environment_plugin_binary_reconfigure_required", "unknown_future_issue"],
        sections={
            "environment_manifest": {
                "plugin_binaries": [
                    {"id": "bot-a"},
                ]
            }
        },
        scan_summary={
            "risk_evidence": [
                {
                    "file": "sections/environment_manifest.json",
                    "path": "$.environment_manifest.plugin_binaries[0].id",
                    "line": 8,
                    "column": 3,
                    "rule": "plugin_binary_untrusted",
                }
            ]
        },
    )
    env_issue = next(item for item in details if item["code"] == "environment_plugin_binary_reconfigure_required")
    assert env_issue["group"] == "environment"
    assert "environment_manifest" in env_issue["sections"]
    assert "environment_manifest.plugin_binaries" in env_issue["related_paths"]
    assert env_issue["evidence_refs"]
    assert env_issue["evidence_refs"][0]["file"].endswith("sections/environment_manifest.json")

    unknown_issue = next(item for item in details if item["code"] == "unknown_future_issue")
    assert unknown_issue["group"] == "unknown"
    assert unknown_issue["evidence_refs"] == []


def test_profile_pack_service_compatibility_issue_details_use_conversion_fallback_evidence():
    details = ProfilePackService.compatibility_issue_details(
        ["astrbot_plugin_wildcard_unresolved"],
        sections={
            "sharelife_meta": {
                "astrbot_import": {
                    "summary": {
                        "field_diagnostics": [
                            {
                                "source_path": "plugin_set",
                                "target_path": "plugins",
                                "outcome": "requires_manual_resolution",
                                "issue_code": "astrbot_plugin_wildcard_unresolved",
                                "note": "plugin wildcard cannot be resolved",
                            }
                        ]
                    }
                }
            }
        },
        scan_summary={},
    )
    issue = details[0]
    assert issue["code"] == "astrbot_plugin_wildcard_unresolved"
    assert issue["evidence_refs"]
    assert issue["evidence_refs"][0]["file"] == "sections/sharelife_meta.json"
    assert issue["evidence_refs"][0]["path"] == "plugins"
    assert issue["evidence_refs"][0]["rule"] == "conversion_requires_manual_resolution"


def test_profile_pack_service_converts_raw_astrbot_cmd_config_json(tmp_path):
    service, _, _ = build_service(tmp_path)
    raw_bytes = json.dumps(
        astrbot_cmd_config_fixture(plugin_set=["sharelife", "community_tools"]),
        ensure_ascii=False,
        indent=2,
    ).encode("utf-8")

    imported = service.import_member_profile_pack(
        user_id="member-1",
        filename="cmd_config.json",
        content=raw_bytes,
    )

    assert imported.compatibility == "degraded"
    assert "astrbot_raw_import_converted" in imported.compatibility_issues
    assert "astrbot_operator_fields_omitted" in imported.compatibility_issues
    assert "astrbot_plugin_wildcard_unresolved" not in imported.compatibility_issues
    assert imported.sections["sharelife_meta"]["astrbot_import"]["source_type"] == "astrbot_cmd_config_json"
    assert sorted(imported.sections["plugins"].keys()) == ["community_tools", "sharelife"]
    assert imported.sections["providers"]["test-openai"]["base_url"] == "https://api.openai.com/v1"
    assert "key" not in imported.sections["providers"]["test-openai"]
    assert imported.sections["astrbot_core"]["provider_settings"]["websearch_tavily_key"] == ["***REDACTED***"]


def test_profile_pack_service_extracts_persona_and_subagent_sections_from_astrbot_config(tmp_path):
    service, _, _ = build_service(tmp_path)
    raw_bytes = json.dumps(
        {
            **astrbot_cmd_config_fixture(plugin_set=["sharelife", "community_tools"]),
            "provider_settings": {
                "default_personality": "zeroclaw_migrated",
                "persona_pool": ["*", "analyst"],
                "websearch_tavily_key": ["tvly-secret"],
            },
            "persona": [
                {
                    "name": "analyst",
                    "system_prompt": "Analyze before acting.",
                }
            ],
            "subagent_orchestrator": {
                "main_enable": True,
                "agents": [
                    {
                        "name": "planner_prometheus",
                        "enabled": True,
                        "runtime": {
                            "limits": {
                                "token_budget": 2048,
                                "completion": {
                                    "max_tokens": 1024,
                                },
                            },
                        },
                    },
                    {"name": "reviewer_oracle", "enabled": False},
                ],
            },
            "platform": [
                {
                    "type": "slack",
                    "enabled": True,
                    "app_id": "slack-app",
                }
            ],
            "provider_sources": [{"id": "builtin-default", "enabled": True}],
        },
        ensure_ascii=False,
        indent=2,
    ).encode("utf-8")

    imported = service.import_member_profile_pack(
        user_id="member-1",
        filename="cmd_config.json",
        content=raw_bytes,
    )

    assert "personas" in imported.sections
    assert imported.sections["personas"]["runtime"]["default_personality"] == "zeroclaw_migrated"
    assert imported.sections["personas"]["runtime"]["persona_pool"] == ["*", "analyst"]
    assert imported.sections["personas"]["entries"]["analyst"]["system_prompt"] == "Analyze before acting."
    assert "environment_manifest" in imported.sections
    assert imported.sections["environment_manifest"]["subagent_orchestrator"]["agents"][0]["name"] == "planner_prometheus"
    assert imported.sections["environment_manifest"]["subagent_orchestrator"]["enabled_agents"] == [
        "planner_prometheus"
    ]
    summary = imported.sections["sharelife_meta"]["astrbot_import"]["summary"]
    assert summary["default_personality"] == "zeroclaw_migrated"
    assert summary["persona_count"] == 1
    assert summary["subagent_count"] == 1
    assert summary["platform_count"] == 1


def test_profile_pack_service_exposes_selection_tree_for_astrbot_import(tmp_path):
    service, _, _ = build_service(tmp_path)
    raw_bytes = json.dumps(
        {
            **astrbot_cmd_config_fixture(plugin_set=["sharelife", "community_tools"]),
            "provider_settings": {
                "default_personality": "analyst",
                "persona_pool": ["analyst", "helper"],
                "websearch_tavily_key": ["tvly-secret"],
            },
            "persona": [
                {"name": "analyst", "system_prompt": "Analyze before acting."},
                {"name": "helper", "system_prompt": "Help with rollout tasks."},
            ],
            "subagent_orchestrator": {
                "main_enable": True,
                "agents": [
                    {
                        "name": "planner_prometheus",
                        "enabled": True,
                        "runtime": {
                            "limits": {
                                "token_budget": 2048,
                                "completion": {
                                    "max_tokens": 1024,
                                },
                            },
                        },
                    },
                    {"name": "reviewer_oracle", "enabled": False},
                ],
            },
            "platform": [
                {"id": "slack-main", "type": "slack", "enabled": True},
                {"type": "telegram", "enabled": True},
            ],
            "provider_sources": [
                {"id": "builtin-default", "enabled": True},
                {"id": "community-mirror", "enabled": False},
            ],
        },
        ensure_ascii=False,
        indent=2,
    ).encode("utf-8")

    service.import_member_profile_pack(
        user_id="member-1",
        filename="cmd_config.json",
        content=raw_bytes,
    )
    imports = service.list_imports(limit=10)
    selection_tree = imports[0]["selection_tree"]
    section_names = [item["name"] for item in selection_tree]

    assert "personas" in section_names
    assert "environment_manifest" in section_names
    assert "astrbot_core" in section_names

    personas_section = next(item for item in selection_tree if item["name"] == "personas")
    persona_paths = {
        node["path"]
        for node in personas_section["items"]
        if isinstance(node, dict) and isinstance(node.get("path"), str)
    }
    assert "personas.runtime" in persona_paths
    assert "personas.entries" in persona_paths

    runtime_node = next(item for item in personas_section["items"] if item["path"] == "personas.runtime")
    runtime_paths = {child["path"] for child in runtime_node["children"]}
    assert "personas.runtime.default_personality" in runtime_paths
    assert "personas.runtime.persona_pool" in runtime_paths
    assert runtime_node["preview_lines"]
    persona_pool_node = next(
        item for item in runtime_node["children"] if item["path"] == "personas.runtime.persona_pool"
    )
    persona_pool_paths = {child["path"] for child in persona_pool_node["children"]}
    assert "personas.runtime.persona_pool[0]" in persona_pool_paths
    assert "personas.runtime.persona_pool[1]" in persona_pool_paths
    persona_pool_labels = {child["label"] for child in persona_pool_node["children"]}
    assert "analyst" in persona_pool_labels
    assert "helper" in persona_pool_labels

    entries_node = next(item for item in personas_section["items"] if item["path"] == "personas.entries")
    entry_paths = {child["path"] for child in entries_node["children"]}
    assert "personas.entries.analyst" in entry_paths
    assert "personas.entries.helper" in entry_paths
    analyst_node = next(item for item in entries_node["children"] if item["path"] == "personas.entries.analyst")
    analyst_paths = {child["path"] for child in analyst_node["children"]}
    assert "personas.entries.analyst.system_prompt" in analyst_paths
    assert "Analyze before acting." in "\n".join(analyst_node["preview_lines"])
    system_prompt_node = next(
        item for item in analyst_node["children"] if item["path"] == "personas.entries.analyst.system_prompt"
    )
    assert system_prompt_node["preview_lines"] == ["Analyze before acting."]

    env_section = next(item for item in selection_tree if item["name"] == "environment_manifest")
    env_paths = {
        node["path"]
        for node in env_section["items"]
        if isinstance(node, dict) and isinstance(node.get("path"), str)
    }
    assert "environment_manifest.subagent_orchestrator" in env_paths
    assert "environment_manifest.platform" in env_paths
    assert "environment_manifest.provider_sources" in env_paths

    subagent_node = next(
        item for item in env_section["items"] if item["path"] == "environment_manifest.subagent_orchestrator"
    )
    subagent_paths = {child["path"] for child in subagent_node["children"]}
    assert "environment_manifest.subagent_orchestrator.agents[0]" in subagent_paths
    assert "environment_manifest.subagent_orchestrator.agents[1]" in subagent_paths
    first_agent_node = next(
        item for item in subagent_node["children"] if item["path"] == "environment_manifest.subagent_orchestrator.agents[0]"
    )
    first_agent_paths = {child["path"] for child in first_agent_node["children"]}
    assert "environment_manifest.subagent_orchestrator.agents[0].name" in first_agent_paths
    assert "environment_manifest.subagent_orchestrator.agents[0].enabled" in first_agent_paths
    assert "environment_manifest.subagent_orchestrator.agents[0].runtime" in first_agent_paths
    runtime_node = next(
        item
        for item in first_agent_node["children"]
        if item["path"] == "environment_manifest.subagent_orchestrator.agents[0].runtime"
    )
    runtime_paths = {child["path"] for child in runtime_node["children"]}
    assert "environment_manifest.subagent_orchestrator.agents[0].runtime.limits" in runtime_paths
    limits_node = next(
        item
        for item in runtime_node["children"]
        if item["path"] == "environment_manifest.subagent_orchestrator.agents[0].runtime.limits"
    )
    limits_paths = {child["path"] for child in limits_node["children"]}
    assert "environment_manifest.subagent_orchestrator.agents[0].runtime.limits.token_budget" in limits_paths
    assert "environment_manifest.subagent_orchestrator.agents[0].runtime.limits.completion" in limits_paths
    completion_node = next(
        item
        for item in limits_node["children"]
        if item["path"] == "environment_manifest.subagent_orchestrator.agents[0].runtime.limits.completion"
    )
    completion_paths = {child["path"] for child in completion_node["children"]}
    assert "environment_manifest.subagent_orchestrator.agents[0].runtime.limits.completion.max_tokens" in completion_paths

    platform_node = next(item for item in env_section["items"] if item["path"] == "environment_manifest.platform")
    platform_paths = {child["path"] for child in platform_node["children"]}
    assert "environment_manifest.platform[0]" in platform_paths
    assert "environment_manifest.platform[1]" in platform_paths
    first_platform_node = next(
        item for item in platform_node["children"] if item["path"] == "environment_manifest.platform[0]"
    )
    first_platform_paths = {child["path"] for child in first_platform_node["children"]}
    assert "environment_manifest.platform[0].id" in first_platform_paths
    assert "environment_manifest.platform[0].type" in first_platform_paths
    assert "slack-main" in "\n".join(first_platform_node["preview_lines"])

    astrbot_core_section = next(item for item in selection_tree if item["name"] == "astrbot_core")
    provider_settings_node = next(
        item for item in astrbot_core_section["items"] if item["path"] == "astrbot_core.provider_settings"
    )
    provider_settings_paths = {child["path"] for child in provider_settings_node["children"]}
    assert "astrbot_core.provider_settings.websearch_tavily_key" in provider_settings_paths
    tavily_node = next(
        item
        for item in provider_settings_node["children"]
        if item["path"] == "astrbot_core.provider_settings.websearch_tavily_key"
    )
    tavily_paths = {child["path"] for child in tavily_node["children"]}
    assert "astrbot_core.provider_settings.websearch_tavily_key[0]" in tavily_paths

    plugins_section = next(item for item in selection_tree if item["name"] == "plugins")
    plugin_labels = {node["label"] for node in plugins_section["items"]}
    assert "sharelife" in plugin_labels
    assert "community_tools" in plugin_labels


def test_profile_pack_service_refreshes_local_astrbot_import_without_duplicate_drafts(tmp_path):
    service, _, _ = build_service(tmp_path)
    initial_bytes = json.dumps(
        {
            **astrbot_cmd_config_fixture(plugin_set=["sharelife"]),
            "provider_settings": {"default_personality": "alpha"},
        },
        ensure_ascii=False,
        indent=2,
    ).encode("utf-8")
    refreshed_bytes = json.dumps(
        {
            **astrbot_cmd_config_fixture(plugin_set=["sharelife", "community_tools"]),
            "provider_settings": {"default_personality": "beta"},
            "subagent_orchestrator": {
                "agents": [{"name": "planner_prometheus", "enabled": True}],
            },
        },
        ensure_ascii=False,
        indent=2,
    ).encode("utf-8")

    first = service.import_member_profile_pack(
        user_id="member-1",
        filename="cmd_config.json",
        content=initial_bytes,
        import_origin="local_astrbot_detected",
        source_fingerprint="local-config-1",
        refresh_existing=True,
    )
    if hasattr(service.clock, "shift"):
        service.clock.shift(seconds=1)
    first_artifact_path = service.get_export_artifact(first.source_artifact_id).path
    assert first_artifact_path.exists()

    refresh_result: dict[str, object] = {}
    second = service.import_member_profile_pack(
        user_id="member-1",
        filename="cmd_config.json",
        content=refreshed_bytes,
        import_origin="local_astrbot_detected",
        source_fingerprint="local-config-1",
        refresh_existing=True,
        refresh_result=refresh_result,
    )

    imports = service.list_imports(limit=10, user_id="member-1")
    assert [item["import_id"] for item in imports] == [second.import_id]
    assert imports[0]["import_origin"] == "local_astrbot_detected"
    assert imports[0]["import_summary"]["default_personality"] == "beta"
    assert imports[0]["import_summary"]["subagent_count"] == 1
    assert refresh_result["replaced_count"] == 1
    assert refresh_result["replaced_import_ids"] == [first.import_id]
    assert not first_artifact_path.exists()
    with pytest.raises(ValueError, match="PROFILE_IMPORT_NOT_FOUND"):
        service.get_import_record(first.import_id)


def test_profile_pack_service_list_imports_hides_stale_local_draft_after_submission(tmp_path):
    service, _, _ = build_service(tmp_path)
    initial_bytes = json.dumps(
        {
            **astrbot_cmd_config_fixture(plugin_set=["sharelife"]),
            "provider_settings": {"default_personality": "alpha"},
        },
        ensure_ascii=False,
        indent=2,
    ).encode("utf-8")
    refreshed_bytes = json.dumps(
        {
            **astrbot_cmd_config_fixture(plugin_set=["sharelife", "community_tools"]),
            "provider_settings": {"default_personality": "beta"},
        },
        ensure_ascii=False,
        indent=2,
    ).encode("utf-8")

    first = service.import_member_profile_pack(
        user_id="member-1",
        filename="cmd_config.json",
        content=initial_bytes,
        import_origin="local_astrbot_detected",
        source_fingerprint="local-config-2",
        refresh_existing=True,
    )
    first_submission = service.submit_export_artifact(
        user_id="member-1",
        artifact_id=first.source_artifact_id,
    )
    assert first_submission.import_id
    if hasattr(service.clock, "shift"):
        service.clock.shift(seconds=1)

    refresh_result: dict[str, object] = {}
    second = service.import_member_profile_pack(
        user_id="member-1",
        filename="cmd_config.json",
        content=refreshed_bytes,
        import_origin="local_astrbot_detected",
        source_fingerprint="local-config-2",
        refresh_existing=True,
        refresh_result=refresh_result,
    )
    assert second.import_id != first.import_id

    # Older import draft remains for audit/submission linkage, but user listing should show only latest local draft.
    assert service.get_import_record(first.import_id).import_id == first.import_id
    assert refresh_result["replaced_count"] == 0
    assert refresh_result["replaced_import_ids"] == []
    rows = service.list_imports(limit=10, user_id="member-1")
    assert [item["import_id"] for item in rows] == [second.import_id]
    assert rows[0]["import_summary"]["default_personality"] == "beta"

def test_profile_pack_service_collapse_local_import_prefers_latest_timestamp_under_order_drift(tmp_path):
    service, _, _ = build_service(tmp_path)
    payload = json.dumps(
        astrbot_cmd_config_fixture(plugin_set=["sharelife"]),
        ensure_ascii=False,
        indent=2,
    ).encode("utf-8")
    first = service.import_member_profile_pack(
        user_id="member-1",
        filename="cmd_config.json",
        content=payload,
        import_origin="local_astrbot_detected",
        source_fingerprint="local-config-order-drift",
        refresh_existing=False,
    )
    if hasattr(service.clock, "shift"):
        service.clock.shift(seconds=1)
    second = service.import_member_profile_pack(
        user_id="member-1",
        filename="cmd_config.json",
        content=payload,
        import_origin="local_astrbot_detected",
        source_fingerprint="local-config-order-drift",
        refresh_existing=False,
    )
    # Simulate storage reload order drift where older imports may appear later in dictionary iteration.
    service._imports = {
        second.import_id: service._imports[second.import_id],
        first.import_id: service._imports[first.import_id],
    }
    rows = service.list_imports(limit=10, user_id="member-1")
    assert [item["import_id"] for item in rows] == [second.import_id]


def test_profile_pack_service_deletes_unsubmitted_member_import_draft(tmp_path):
    service, _, _ = build_service(tmp_path)
    imported = service.import_member_profile_pack(
        user_id="member-1",
        filename="cmd_config.json",
        content=json.dumps(astrbot_cmd_config_fixture(), ensure_ascii=False, indent=2).encode("utf-8"),
    )
    artifact_path = service.get_export_artifact(imported.source_artifact_id).path

    deleted = service.delete_import(
        user_id="member-1",
        import_id=imported.import_id,
    )

    assert deleted.import_id == imported.import_id
    assert service.list_imports(limit=10, user_id="member-1") == []
    assert not artifact_path.exists()
    with pytest.raises(ValueError, match="PROFILE_IMPORT_NOT_FOUND"):
        service.get_import_record(imported.import_id)


def test_profile_pack_service_rejects_deleting_import_draft_once_submission_exists(tmp_path):
    service, _, _ = build_service(tmp_path)
    imported = service.import_member_profile_pack(
        user_id="member-1",
        filename="cmd_config.json",
        content=json.dumps(astrbot_cmd_config_fixture(), ensure_ascii=False, indent=2).encode("utf-8"),
    )
    service.submit_export_artifact(
        user_id="member-1",
        artifact_id=imported.source_artifact_id,
    )

    with pytest.raises(ValueError, match="PROFILE_IMPORT_IN_USE"):
        service.delete_import(
            user_id="member-1",
            import_id=imported.import_id,
        )


def test_profile_pack_service_submit_export_artifact_materializes_partial_selection(tmp_path):
    service, _, _ = build_service(tmp_path)
    raw_bytes = json.dumps(
        {
            **astrbot_cmd_config_fixture(plugin_set=["sharelife", "community_tools"]),
            "provider_settings": {
                "default_personality": "analyst",
                "persona_pool": ["analyst", "helper"],
            },
            "persona": [
                {"name": "analyst", "system_prompt": "Analyze before acting."},
                {"name": "helper", "system_prompt": "Help with rollout tasks."},
            ],
            "subagent_orchestrator": {
                "main_enable": True,
                "agents": [
                    {"name": "planner_prometheus", "enabled": True},
                    {"name": "reviewer_oracle", "enabled": False},
                ],
            },
        },
        ensure_ascii=False,
        indent=2,
    ).encode("utf-8")

    imported = service.import_member_profile_pack(
        user_id="member-1",
        filename="cmd_config.json",
        content=raw_bytes,
    )

    submission = service.submit_export_artifact(
        user_id="member-1",
        artifact_id=imported.source_artifact_id,
        submit_options={
            "pack_type": "bot_profile_pack",
            "selected_sections": ["personas", "environment_manifest"],
            "selected_item_paths": [
                "personas.runtime.default_personality",
                "personas.entries.analyst.system_prompt",
                "environment_manifest.subagent_orchestrator.agents[0].name",
            ],
        },
    )

    assert submission.status == "pending"
    assert submission.sections == ["personas", "environment_manifest"]
    assert submission.import_id != imported.import_id
    assert submission.artifact_id != imported.source_artifact_id
    assert submission.submit_options["selected_item_paths"] == [
        "personas.runtime.default_personality",
        "personas.entries.analyst.system_prompt",
        "environment_manifest.subagent_orchestrator.agents[0].name",
    ]

    materialized_import = service.get_import_record(submission.import_id)
    assert materialized_import.sections["personas"]["runtime"] == {"default_personality": "analyst"}
    assert list(materialized_import.sections["personas"]["entries"].keys()) == ["analyst"]
    assert materialized_import.sections["personas"]["entries"]["analyst"] == {
        "system_prompt": "Analyze before acting."
    }
    assert materialized_import.sections["environment_manifest"]["subagent_orchestrator"]["agents"] == [
        {"name": "planner_prometheus"}
    ]
    assert "enabled_agents" not in materialized_import.sections["environment_manifest"]["subagent_orchestrator"]

    artifact = service.get_export_artifact(submission.artifact_id)
    with zipfile.ZipFile(artifact.path, "r") as zf:
        manifest = json.loads(zf.read("manifest.json").decode("utf-8"))
        personas = json.loads(zf.read("sections/personas.json").decode("utf-8"))
        environment = json.loads(zf.read("sections/environment_manifest.json").decode("utf-8"))

    assert manifest["sections"] == ["personas", "environment_manifest"]
    assert personas["runtime"] == {"default_personality": "analyst"}
    assert list(personas["entries"].keys()) == ["analyst"]
    assert personas["entries"]["analyst"] == {"system_prompt": "Analyze before acting."}
    assert environment["subagent_orchestrator"]["agents"] == [{"name": "planner_prometheus"}]


def test_profile_pack_service_converts_raw_astrbot_abconf_json(tmp_path):
    service, _, _ = build_service(tmp_path)
    raw_bytes = json.dumps(
        {
            "provider_settings": {
                "default_personality": "work",
                "websearch_bocha_key": ["bocha-secret"],
            },
            "timezone": "UTC",
            "plugin_set": ["community_tools"],
        },
        ensure_ascii=False,
        indent=2,
    ).encode("utf-8")

    imported = service.import_member_profile_pack(
        user_id="member-1",
        filename="abconf_team.json",
        content=raw_bytes,
    )

    assert imported.compatibility == "degraded"
    assert "astrbot_raw_import_converted" in imported.compatibility_issues
    assert imported.sections["sharelife_meta"]["astrbot_import"]["source_type"] == "astrbot_abconf_json"
    assert imported.sections["plugins"] == {"community_tools": {"enabled": True}}
    assert imported.sections["astrbot_core"]["provider_settings"]["websearch_bocha_key"] == ["***REDACTED***"]


def test_profile_pack_export_applies_field_level_redaction_policy(tmp_path):
    service, _, _ = build_service(tmp_path)

    artifact = service.export_bot_profile_pack(
        pack_id="profile/field-redaction",
        version="1.0.0",
        redaction_mode="include_provider_no_key",
        mask_paths=["providers.openai.base_url"],
        drop_paths=["sharelife_meta.owner"],
    )
    with zipfile.ZipFile(artifact.path, "r") as zf:
        providers = json.loads(zf.read("sections/providers.json").decode("utf-8"))
        meta = json.loads(zf.read("sections/sharelife_meta.json").decode("utf-8"))

    assert providers["openai"]["base_url"] != "https://api.openai.com/v1"
    assert "owner" not in meta


def test_profile_pack_export_supports_signature_and_import_verification(tmp_path):
    service, _, _ = build_service(
        tmp_path,
        signing_key_id="team-default",
        signing_secret="super-secret-signing-key",
        trusted_signing_keys={"team-default": "super-secret-signing-key"},
    )
    artifact = service.export_bot_profile_pack(
        pack_id="profile/signed",
        version="1.0.0",
        redaction_mode="exclude_secrets",
    )
    assert artifact.manifest.signature is not None
    assert artifact.manifest.signature.key_id == "team-default"

    imported = service.import_bot_profile_pack(
        filename=artifact.filename,
        content=artifact.path.read_bytes(),
    )
    assert imported.compatibility == "compatible"
    assert not any("signature_" in issue for issue in imported.compatibility_issues)


def test_profile_pack_import_blocks_invalid_signature(tmp_path):
    service, _, _ = build_service(
        tmp_path,
        signing_key_id="team-default",
        signing_secret="super-secret-signing-key",
        trusted_signing_keys={"team-default": "different-key"},
    )
    artifact = service.export_bot_profile_pack(
        pack_id="profile/signed-invalid",
        version="1.0.0",
        redaction_mode="exclude_secrets",
    )
    imported = service.import_bot_profile_pack(
        filename=artifact.filename,
        content=artifact.path.read_bytes(),
    )
    assert imported.compatibility == "blocked"
    assert "signature_invalid" in imported.compatibility_issues


def test_profile_pack_export_include_encrypted_secrets_mode_obfuscates_sensitive_values(tmp_path):
    service, _, _ = build_service(
        tmp_path,
        secrets_encryption_key="encryption-secret-v1",
    )
    artifact = service.export_bot_profile_pack(
        pack_id="profile/encrypted-secrets",
        version="1.0.0",
        redaction_mode="include_encrypted_secrets",
    )
    with zipfile.ZipFile(artifact.path, "r") as zf:
        providers = json.loads(zf.read("sections/providers.json").decode("utf-8"))
    encrypted_value = providers["openai"]["api_key"]
    assert encrypted_value != "sk-live-secret"
    assert encrypted_value != "***REDACTED***"
    assert str(encrypted_value).startswith("enc-v1:")


def test_profile_pack_import_include_encrypted_secrets_mode_restores_secret_on_apply(tmp_path):
    service, apply_service, runtime = build_service(
        tmp_path,
        secrets_encryption_key="encryption-secret-v1",
    )
    artifact = service.export_bot_profile_pack(
        pack_id="profile/encrypted-restore",
        version="1.0.0",
        redaction_mode="include_encrypted_secrets",
    )
    runtime.state["providers"]["openai"]["api_key"] = "sk-overwritten"

    imported = service.import_bot_profile_pack(
        filename=artifact.filename,
        content=artifact.path.read_bytes(),
    )
    assert imported.compatibility == "compatible"

    dryrun = service.prepare_apply_plan(
        import_id=imported.import_id,
        plan_id="plan-profile-encrypted-restore",
        selected_sections=["providers"],
    )
    restored_value = dryrun["patch"]["providers"]["openai"]["api_key"]
    assert restored_value == "sk-live-secret"
    assert not str(restored_value).startswith("enc-v1:")

    apply_service.apply("plan-profile-encrypted-restore")
    assert runtime.state["providers"]["openai"]["api_key"] == "sk-live-secret"


def test_profile_pack_import_blocks_encrypted_secrets_without_decryption_key(tmp_path):
    exporter, _, _ = build_service(
        tmp_path / "exporter",
        secrets_encryption_key="encryption-secret-v1",
    )
    artifact = exporter.export_bot_profile_pack(
        pack_id="profile/encrypted-no-key",
        version="1.0.0",
        redaction_mode="include_encrypted_secrets",
    )

    importer, _, _ = build_service(tmp_path / "importer")
    imported = importer.import_bot_profile_pack(
        filename=artifact.filename,
        content=artifact.path.read_bytes(),
    )
    assert imported.compatibility == "blocked"
    assert "encrypted_secrets_key_unavailable" in imported.compatibility_issues

    with pytest.raises(ValueError, match="PROFILE_PACK_INCOMPATIBLE"):
        importer.prepare_apply_plan(
            import_id=imported.import_id,
            plan_id="plan-profile-encrypted-no-key",
            selected_sections=["providers"],
        )


def test_profile_pack_import_blocks_malformed_encrypted_secret_payload(tmp_path):
    service, _, _ = build_service(
        tmp_path,
        secrets_encryption_key="encryption-secret-v1",
    )
    artifact = service.export_bot_profile_pack(
        pack_id="profile/encrypted-invalid",
        version="1.0.0",
        redaction_mode="include_encrypted_secrets",
    )

    source = io.BytesIO(artifact.path.read_bytes())
    target = io.BytesIO()
    with zipfile.ZipFile(source, "r") as src, zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as dst:
        for name in src.namelist():
            payload = src.read(name)
            if name == "sections/providers.json":
                providers = json.loads(payload.decode("utf-8"))
                providers["openai"]["api_key"] = "enc-v1:broken"
                payload = json.dumps(providers, ensure_ascii=False, indent=2).encode("utf-8")
            dst.writestr(name, payload)

    imported = service.import_bot_profile_pack(
        filename=artifact.filename,
        content=target.getvalue(),
    )
    assert imported.compatibility == "blocked"
    assert "encrypted_secret_payload_invalid" in imported.compatibility_issues


def test_profile_pack_export_supports_extension_pack_defaults(tmp_path):
    service, _, _ = build_service(tmp_path)
    artifact = service.export_bot_profile_pack(
        pack_id="extension/community-basic",
        version="1.0.0",
        pack_type="extension_pack",
        redaction_mode="exclude_secrets",
    )

    with zipfile.ZipFile(artifact.path, "r") as zf:
        names = set(zf.namelist())
        manifest = json.loads(zf.read("manifest.json").decode("utf-8"))

    assert manifest["pack_type"] == "extension_pack"
    assert manifest["sections"] == ["plugins", "skills", "personas", "mcp_servers"]
    assert "sections/providers.json" not in names
    assert "sections/plugins.json" in names


def test_profile_pack_export_rejects_disallowed_section_for_extension_pack(tmp_path):
    service, _, _ = build_service(tmp_path)
    with pytest.raises(ValueError, match="PROFILE_PACK_SECTION_NOT_ALLOWED_FOR_TYPE"):
        service.export_bot_profile_pack(
            pack_id="extension/community-invalid",
            version="1.0.0",
            pack_type="extension_pack",
            redaction_mode="exclude_secrets",
            sections=["providers", "plugins"],
        )


def test_profile_pack_export_supports_stateful_sections_and_capabilities(tmp_path):
    service, _, runtime = build_service(tmp_path)
    runtime.state["memory_store"] = {
        "thread_default": {
            "summary": "user prefers concise answers",
        }
    }
    runtime.state["conversation_history"] = [
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "hi"},
    ]
    runtime.state["knowledge_base"] = {
        "default": {
            "collection": "project_docs",
            "storage_path": "/data/knowledge/base",
        }
    }
    runtime.state["environment_manifest"] = {
        "container_runtime": "docker",
        "system_dependencies": ["ffmpeg"],
        "plugin_binaries": ["plugin_sharelife_core.so"],
    }

    artifact = service.export_bot_profile_pack(
        pack_id="profile/stateful-sample",
        version="1.0.0",
        pack_type="bot_profile_pack",
        redaction_mode="exclude_secrets",
        sections=[
            "memory_store",
            "conversation_history",
            "knowledge_base",
            "environment_manifest",
        ],
    )

    manifest = artifact.manifest.model_dump()
    assert manifest["sections"] == [
        "memory_store",
        "conversation_history",
        "knowledge_base",
        "environment_manifest",
    ]
    assert "memory.export" in manifest["capabilities"]
    assert "conversation.export" in manifest["capabilities"]
    assert "knowledge.export" in manifest["capabilities"]
    assert "environment.reconfigure" in manifest["capabilities"]


def test_profile_pack_import_marks_environment_reconfigure_issues_as_degraded(tmp_path):
    exporter, _, runtime = build_service(tmp_path / "exporter")
    runtime.state["knowledge_base"] = {
        "default": {
            "storage_path": "/data/knowledge/base",
        }
    }
    runtime.state["environment_manifest"] = {
        "container_runtime": "docker",
        "system_dependencies": ["ffmpeg", "tesseract"],
        "plugin_binaries": ["plugin_sharelife_core.so"],
    }
    artifact = exporter.export_bot_profile_pack(
        pack_id="profile/stateful-reconfigure",
        version="1.0.0",
        redaction_mode="exclude_secrets",
        sections=["knowledge_base", "environment_manifest"],
    )

    importer, _, _ = build_service(tmp_path / "importer")
    imported = importer.import_bot_profile_pack(
        filename=artifact.filename,
        content=artifact.path.read_bytes(),
    )
    assert imported.compatibility == "degraded"
    assert "environment_container_reconfigure_required" in imported.compatibility_issues
    assert "environment_system_dependencies_reconfigure_required" in imported.compatibility_issues
    assert "environment_plugin_binary_reconfigure_required" in imported.compatibility_issues
    assert "knowledge_base_storage_sync_required" in imported.compatibility_issues


def test_profile_pack_plugin_install_confirmation_gate_blocks_dryrun_until_confirmed(tmp_path):
    exporter, _, _ = build_service(tmp_path / "exporter")
    exporter.runtime.state["plugins"]["community_tools"] = {
        "enabled": True,
        "version": "1.2.3",
        "source": "https://github.com/acme/community-tools",
        "sha256": "abc123",
    }
    artifact = exporter.export_bot_profile_pack(
        pack_id="extension/community-tools",
        version="1.0.0",
        pack_type="extension_pack",
        redaction_mode="exclude_secrets",
    )

    importer, _, _ = build_service(tmp_path / "importer")
    imported = importer.import_bot_profile_pack(
        filename=artifact.filename,
        content=artifact.path.read_bytes(),
    )

    install_plan = importer.profile_pack_plugin_install_plan(import_id=imported.import_id)
    assert install_plan["status"] == "confirmation_required"
    assert install_plan["confirmation_required"] is True
    assert install_plan["required_plugins"] == ["community_tools"]
    assert install_plan["missing_plugins"] == ["community_tools"]

    with pytest.raises(ValueError, match="PROFILE_PACK_PLUGIN_INSTALL_CONFIRM_REQUIRED"):
        importer.prepare_apply_plan(
            import_id=imported.import_id,
            plan_id="plan-extension-community-tools",
            selected_sections=["plugins"],
        )

    confirmed = importer.confirm_profile_pack_plugin_install(
        import_id=imported.import_id,
        plugin_ids=["community_tools"],
    )
    assert confirmed["status"] == "confirmed"
    assert confirmed["confirmed_plugins"] == ["community_tools"]

    dryrun = importer.prepare_apply_plan(
        import_id=imported.import_id,
        plan_id="plan-extension-community-tools",
        selected_sections=["plugins"],
    )
    assert dryrun["status"] == "dryrun_ready"
    assert dryrun["plugin_install"]["status"] == "confirmed"


def test_profile_pack_plugin_install_execute_runs_commands_after_confirmation(tmp_path):
    exporter, _, _ = build_service(tmp_path / "exporter")
    exporter.runtime.state["plugins"]["community_tools"] = {
        "enabled": True,
        "version": "1.2.3",
        "source": "https://github.com/acme/community-tools",
        "install_cmd": "pip install astrbot-plugin-community-tools==1.2.3",
    }
    artifact = exporter.export_bot_profile_pack(
        pack_id="extension/community-tools",
        version="1.0.0",
        pack_type="extension_pack",
        redaction_mode="exclude_secrets",
    )

    executed_commands: list[list[str]] = []

    def runner(command: list[str], timeout_seconds: int) -> dict:
        executed_commands.append(list(command))
        return {"returncode": 0, "stdout": "ok", "stderr": "", "timed_out": False}

    importer, _, _ = build_service(
        tmp_path / "importer",
        plugin_install_service=PluginInstallService(
            enabled=True,
            command_runner=runner,
        ),
    )
    imported = importer.import_bot_profile_pack(
        filename=artifact.filename,
        content=artifact.path.read_bytes(),
    )

    importer.confirm_profile_pack_plugin_install(
        import_id=imported.import_id,
        plugin_ids=["community_tools"],
    )
    executed = importer.execute_profile_pack_plugin_install(
        import_id=imported.import_id,
        plugin_ids=["community_tools"],
    )
    assert executed["status"] == "executed"
    output = executed["execution"]["result"]
    assert output["installed_count"] == 1
    assert output["failed_count"] == 0
    assert output["attempts"][0]["status"] == "installed"
    assert executed_commands == [["pip", "install", "astrbot-plugin-community-tools==1.2.3"]]


def test_profile_pack_plugin_install_execute_respects_require_success_before_apply(tmp_path):
    exporter, _, _ = build_service(tmp_path / "exporter")
    exporter.runtime.state["plugins"]["community_tools"] = {
        "enabled": True,
        "version": "1.2.3",
        "source": "https://github.com/acme/community-tools",
        "install_cmd": "pip install astrbot-plugin-community-tools==1.2.3",
    }
    artifact = exporter.export_bot_profile_pack(
        pack_id="extension/community-tools",
        version="1.0.0",
        pack_type="extension_pack",
        redaction_mode="exclude_secrets",
    )

    importer, _, _ = build_service(
        tmp_path / "importer",
        plugin_install_service=PluginInstallService(
            enabled=True,
            require_success_before_apply=True,
            command_runner=lambda command, timeout_seconds: {
                "returncode": 0,
                "stdout": "",
                "stderr": "",
                "timed_out": False,
            },
        ),
    )
    imported = importer.import_bot_profile_pack(
        filename=artifact.filename,
        content=artifact.path.read_bytes(),
    )
    importer.confirm_profile_pack_plugin_install(
        import_id=imported.import_id,
        plugin_ids=["community_tools"],
    )

    with pytest.raises(ValueError, match="PROFILE_PACK_PLUGIN_INSTALL_EXEC_REQUIRED"):
        importer.prepare_apply_plan(
            import_id=imported.import_id,
            plan_id="plan-extension-community-tools",
            selected_sections=["plugins"],
        )

    importer.execute_profile_pack_plugin_install(import_id=imported.import_id)
    dryrun = importer.prepare_apply_plan(
        import_id=imported.import_id,
        plan_id="plan-extension-community-tools",
        selected_sections=["plugins"],
    )
    assert dryrun["status"] == "dryrun_ready"


def test_profile_pack_plugin_install_execute_disabled_by_default(tmp_path):
    exporter, _, _ = build_service(tmp_path / "exporter")
    exporter.runtime.state["plugins"]["community_tools"] = {
        "enabled": True,
        "version": "1.2.3",
        "source": "https://github.com/acme/community-tools",
        "install_cmd": "pip install astrbot-plugin-community-tools==1.2.3",
    }
    artifact = exporter.export_bot_profile_pack(
        pack_id="extension/community-tools",
        version="1.0.0",
        pack_type="extension_pack",
        redaction_mode="exclude_secrets",
    )

    importer, _, _ = build_service(tmp_path / "importer")
    imported = importer.import_bot_profile_pack(
        filename=artifact.filename,
        content=artifact.path.read_bytes(),
    )
    importer.confirm_profile_pack_plugin_install(
        import_id=imported.import_id,
        plugin_ids=["community_tools"],
    )

    with pytest.raises(ValueError, match="PROFILE_PACK_PLUGIN_INSTALL_EXEC_DISABLED"):
        importer.execute_profile_pack_plugin_install(import_id=imported.import_id)


def test_profile_pack_preview_published_compare_returns_runtime_diff(tmp_path):
    service, _, runtime = build_service(tmp_path)

    artifact = service.export_bot_profile_pack(
        pack_id="profile/community-compare",
        version="1.0.0",
        redaction_mode="exclude_secrets",
    )
    submission = service.submit_export_artifact(
        user_id="member-1",
        artifact_id=artifact.artifact_id,
    )
    service.decide_submission(
        submission_id=submission.submission_id,
        reviewer_id="admin",
        decision="approve",
    )
    runtime.state["plugins"] = {"legacy": {"enabled": False}}

    compared = service.preview_published_pack_compare(
        pack_id="profile/community-compare",
        selected_sections=["plugins"],
    )
    assert compared["status"] == "compare_ready"
    assert compared["pack_id"] == "profile/community-compare"
    assert compared["selected_sections"] == ["plugins"]
    assert compared["changed_sections"] == ["plugins"]
    assert compared["changed_sections_count"] == 1
    assert "diff" in compared
    sections = compared["diff"]["sections"]
    assert len(sections) == 1
    plugins = sections[0]
    assert plugins["file_path"] == "sections/plugins.json"
    assert isinstance(plugins["before_preview"], list)
    assert isinstance(plugins["after_preview"], list)
    assert isinstance(plugins["diff_preview"], list)
    assert plugins["before_preview"]
    assert plugins["after_preview"]
    assert plugins["diff_preview"]


def test_profile_pack_governance_metadata_and_featured_toggle(tmp_path):
    service, _, _ = build_service(tmp_path)
    artifact = service.export_bot_profile_pack(
        pack_id="profile/community-governance",
        version="1.0.0",
        redaction_mode="exclude_secrets",
    )
    assert "file.write" in artifact.manifest.capabilities

    submission = service.submit_export_artifact(
        user_id="member-1",
        artifact_id=artifact.artifact_id,
    )
    assert "declared" in submission.capability_summary
    assert "runtime_result" in submission.compatibility_matrix
    assert "runtime_issue_details" in submission.compatibility_matrix
    assert submission.review_evidence["redaction_mode"] == "exclude_secrets"
    assert "compatibility_issue_details" in submission.review_evidence

    service.decide_submission(
        submission_id=submission.submission_id,
        reviewer_id="admin",
        decision="approve",
    )
    featured = service.set_published_featured(
        pack_id="profile/community-governance",
        reviewer_id="admin",
        featured=True,
        note="featured for deterministic restore",
    )
    assert featured.featured is True
    assert featured.featured_note.startswith("featured")


def test_profile_pack_replace_pending_submissions_marks_previous_rows_as_replaced(tmp_path):
    service, _, _ = build_service(tmp_path)
    artifact = service.export_bot_profile_pack(
        pack_id="profile/community-replace",
        version="1.0.0",
        redaction_mode="exclude_secrets",
    )
    first = service.submit_export_artifact(
        user_id="member-1",
        artifact_id=artifact.artifact_id,
    )
    service.submit_export_artifact(
        user_id="member-2",
        artifact_id=artifact.artifact_id,
    )
    latest = service.submit_export_artifact(
        user_id="member-1",
        artifact_id=artifact.artifact_id,
    )

    replaced = service.replace_pending_submissions(
        user_id="member-1",
        pack_id="profile/community-replace",
        exclude_submission_id=latest.submission_id,
    )
    assert replaced == [first.submission_id]
    assert service.get_submission(first.submission_id).status == "replaced"

    replaced_again = service.replace_pending_submissions(
        user_id="member-1",
        pack_id="profile/community-replace",
        exclude_submission_id=latest.submission_id,
    )
    assert replaced_again == []
