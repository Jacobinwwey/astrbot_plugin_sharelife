from __future__ import annotations

import io
import json
import zipfile
from datetime import UTC, datetime, timedelta

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
    assert submission.review_evidence["redaction_mode"] == "exclude_secrets"

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
