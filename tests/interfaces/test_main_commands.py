from __future__ import annotations

import asyncio
import importlib
import os
import sys
from pathlib import Path

from scripts.migrate_state_to_sqlite import state_store_filenames as migrate_state_store_filenames
from scripts.run_sharelife_webui_standalone import (
    apply_standalone_feature_defaults,
    build_server as standalone_build_server,
    state_store_filenames as standalone_state_store_filenames,
)


class FakeEvent:
    def __init__(self, sender_id: str = "u1", session_id: str = "s1", role: str = "member"):
        self._sender_id = sender_id
        self._session_id = session_id
        self.role = role

    def get_sender_id(self) -> str:
        return self._sender_id

    def get_session_id(self) -> str:
        return self._session_id

    def plain_result(self, text: str) -> str:
        return text


async def _collect(async_gen) -> list[str]:
    return [item async for item in async_gen]


def _load_plugin_module(tmp_path: Path):
    repo_root = Path(__file__).resolve().parents[2]
    package_root = tmp_path / "data" / "plugins"
    package_root.mkdir(parents=True)
    (tmp_path / "data" / "__init__.py").write_text("", encoding="utf-8")
    (package_root / "__init__.py").write_text("", encoding="utf-8")
    os.symlink(repo_root, package_root / "astrbot_plugin_sharelife", target_is_directory=True)

    astrbot_api = tmp_path / "astrbot" / "api"
    astrbot_api.mkdir(parents=True)
    (tmp_path / "astrbot" / "__init__.py").write_text("", encoding="utf-8")
    (astrbot_api / "__init__.py").write_text(
        "\n".join(
            [
                "from pathlib import Path",
                "",
                "class _Logger:",
                "    def info(self, *args, **kwargs):",
                "        return None",
                "    def warning(self, *args, **kwargs):",
                "        return None",
                "logger = _Logger()",
                "",
                "class sp:",
                "    @staticmethod",
                "    def get_data_dir(name):",
                f"        path = Path({str(tmp_path / 'plugin_data')!r}) / name",
                "        path.mkdir(parents=True, exist_ok=True)",
                "        return path",
            ]
        ),
        encoding="utf-8",
    )
    (astrbot_api / "event.py").write_text(
        "\n".join(
            [
                "class AstrMessageEvent:",
                "    pass",
                "",
                "class _Filter:",
                "    @staticmethod",
                "    def command(name):",
                "        def decorator(func):",
                "            return func",
                "        return decorator",
                "",
                "filter = _Filter()",
            ]
        ),
        encoding="utf-8",
    )
    (astrbot_api / "star.py").write_text(
        "\n".join(
            [
                "class Context:",
                "    pass",
                "",
                "class Star:",
                "    def __init__(self, context, config=None):",
                "        self.context = context",
                "        self.config = config",
                "",
                "def register(*args, **kwargs):",
                "    def decorator(cls):",
                "        return cls",
                "    return decorator",
            ]
        ),
        encoding="utf-8",
    )

    sys.path.insert(0, str(tmp_path))
    for name in list(sys.modules):
        if name == "astrbot" or name.startswith("astrbot.") or name.startswith("data.plugins.astrbot_plugin_sharelife"):
            del sys.modules[name]
    return importlib.import_module("data.plugins.astrbot_plugin_sharelife.main")


def test_sharelife_help_mentions_new_command_entries(tmp_path: Path) -> None:
    module = _load_plugin_module(tmp_path)
    plugin = module.SharelifePlugin(module.Context(), config={"webui": {"enabled": False}})

    output = asyncio.run(_collect(plugin.sharelife(FakeEvent())))[0]

    assert "/sharelife_trial_status" in output
    assert "/sharelife_dryrun" in output
    assert "/sharelife_rollback" in output
    assert "/sharelife_profile_export" in output
    assert "/sharelife_profile_import" in output
    assert "/sharelife_profile_import_dryrun" in output
    assert "/sharelife_profile_import_dryrun_latest" in output
    assert "/sharelife_profile_exports" in output
    assert "/sharelife_profile_imports" in output
    assert "/sharelife_profile_plugins" in output
    assert "/sharelife_profile_plugins_confirm" in output
    assert "/sharelife_profile_plugins_install" in output


def test_sharelife_trial_status_and_apply_workflow_commands(tmp_path: Path) -> None:
    module = _load_plugin_module(tmp_path)
    plugin = module.SharelifePlugin(module.Context(), config={"webui": {"enabled": False}})

    member = FakeEvent(role="member")
    admin = FakeEvent(sender_id="admin-1", role="admin")

    missing = asyncio.run(_collect(plugin.sharelife_trial_status(member, "community/basic")))[0]
    assert missing == "trial status: not_started template_id=community/basic"

    started = asyncio.run(_collect(plugin.sharelife_trial(member, "community/basic")))[0]
    assert started == "trial started"

    active = asyncio.run(_collect(plugin.sharelife_trial_status(member, "community/basic")))[0]
    assert active.startswith("trial status: active template_id=community/basic")

    dryrun = asyncio.run(_collect(plugin.sharelife_dryrun(admin, "community/basic", "1.0.0")))[0]
    assert dryrun == "dryrun ready: plan-community-basic"

    applied = asyncio.run(_collect(plugin.sharelife_apply(admin, "plan-community-basic")))[0]
    assert applied == "plan applied"

    rolled_back = asyncio.run(_collect(plugin.sharelife_rollback(admin, "plan-community-basic")))[0]
    assert rolled_back == "plan rolled back"


def test_sharelife_state_store_sqlite_persists_preferences_across_reloads(tmp_path: Path) -> None:
    module = _load_plugin_module(tmp_path)
    sqlite_file = tmp_path / "sharelife_state.sqlite3"
    config = {
        "webui": {"enabled": False},
        "state_store": {"backend": "sqlite", "sqlite_file": str(sqlite_file)},
    }

    plugin = module.SharelifePlugin(module.Context(), config=config)
    event = FakeEvent(sender_id="sqlite-user", role="member")

    before = asyncio.run(_collect(plugin.sharelife_pref(event)))[0]
    assert "execution_mode=subagent_driven" in before

    updated = asyncio.run(_collect(plugin.sharelife_mode(event, "inline_execution")))[0]
    assert updated == "execution mode updated"

    reloaded_plugin = module.SharelifePlugin(module.Context(), config=config)
    after = asyncio.run(_collect(reloaded_plugin.sharelife_pref(event)))[0]
    assert "execution_mode=inline_execution" in after


def test_sharelife_state_store_sqlite_persists_profile_pack_exports_across_reloads(tmp_path: Path) -> None:
    module = _load_plugin_module(tmp_path)
    sqlite_file = tmp_path / "sharelife_state.sqlite3"
    config = {
        "webui": {"enabled": False},
        "state_store": {"backend": "sqlite", "sqlite_file": str(sqlite_file)},
    }
    admin = FakeEvent(sender_id="admin-1", role="admin")

    plugin = module.SharelifePlugin(module.Context(), config=config)
    exported = asyncio.run(
        _collect(plugin.sharelife_profile_export(admin, "profile/sqlite", "1.0.0"))
    )[0]
    assert exported.startswith("profile pack exported:")

    reloaded_plugin = module.SharelifePlugin(module.Context(), config=config)
    exports = asyncio.run(_collect(reloaded_plugin.sharelife_profile_exports(admin, "10")))[0]
    assert "profile/sqlite@1.0.0" in exports


def test_sharelife_state_store_mappings_include_artifact_and_continuity_state(tmp_path: Path) -> None:
    module = _load_plugin_module(tmp_path)

    assert "artifact_state" in module.SharelifePlugin._state_store_filenames()
    assert "continuity_state" in module.SharelifePlugin._state_store_filenames()
    assert "artifact_state" in standalone_state_store_filenames()
    assert "continuity_state" in standalone_state_store_filenames()
    assert "artifact_state" in migrate_state_store_filenames()
    assert "continuity_state" in migrate_state_store_filenames()


def test_standalone_feature_defaults_disable_host_local_astrbot_import_by_default() -> None:
    defaulted = apply_standalone_feature_defaults({"webui": {}})
    assert defaulted["webui"]["features"]["local_astrbot_import"] is False
    assert defaulted["webui"]["features"]["allow_anonymous_local_astrbot_import"] is False

    explicit = apply_standalone_feature_defaults(
        {
            "webui": {
                "features": {
                    "local_astrbot_import": True,
                    "allow_anonymous_local_astrbot_import": True,
                }
            }
        }
    )
    assert explicit["webui"]["features"]["local_astrbot_import"] is True
    assert explicit["webui"]["features"]["allow_anonymous_local_astrbot_import"] is True

    inherited = apply_standalone_feature_defaults(
        {
            "webui": {
                "auth": {
                    "allow_anonymous_member": True,
                },
                "features": {
                    "local_astrbot_import": True,
                },
            }
        }
    )
    assert inherited["webui"]["features"]["local_astrbot_import"] is True
    assert inherited["webui"]["features"]["allow_anonymous_local_astrbot_import"] is True

    override_enabled = apply_standalone_feature_defaults(
        {"webui": {}},
        enable_local_astrbot_import=True,
    )
    assert override_enabled["webui"]["features"]["local_astrbot_import"] is True
    assert override_enabled["webui"]["features"]["allow_anonymous_local_astrbot_import"] is False

    override_enabled_over_config = apply_standalone_feature_defaults(
        {"webui": {"features": {"local_astrbot_import": False}}},
        enable_local_astrbot_import=True,
    )
    assert override_enabled_over_config["webui"]["features"]["local_astrbot_import"] is True
    assert (
        override_enabled_over_config["webui"]["features"]["allow_anonymous_local_astrbot_import"]
        is False
    )

    override_anonymous = apply_standalone_feature_defaults(
        {"webui": {}},
        allow_anonymous_local_astrbot_import=True,
    )
    assert override_anonymous["webui"]["features"]["local_astrbot_import"] is True
    assert override_anonymous["webui"]["features"]["allow_anonymous_local_astrbot_import"] is True


def test_sharelife_continuity_retention_is_configurable_from_plugin_config(tmp_path: Path) -> None:
    module = _load_plugin_module(tmp_path)
    plugin = module.SharelifePlugin(
        module.Context(),
        config={
            "webui": {"enabled": False},
            "continuity": {"max_entries": 7},
        },
    )

    assert plugin.continuity_service.max_entries == 7


def test_sharelife_continuity_retention_is_configurable_in_standalone_runner(tmp_path: Path) -> None:
    server, api = standalone_build_server(
        tmp_path,
        config={
            "continuity": {"max_entries": 9},
        },
    )

    assert server is not None
    assert api.apply_service.continuity_service is not None
    assert api.apply_service.continuity_service.max_entries == 9


def test_sharelife_state_store_sqlite_persists_template_artifacts_across_reloads(tmp_path: Path) -> None:
    module = _load_plugin_module(tmp_path)
    sqlite_file = tmp_path / "sharelife_state.sqlite3"
    config = {
        "webui": {"enabled": False},
        "state_store": {"backend": "sqlite", "sqlite_file": str(sqlite_file)},
    }

    plugin = module.SharelifePlugin(module.Context(), config=config)
    artifact = plugin.package_service.export_template_package("community/basic")

    reloaded_plugin = module.SharelifePlugin(module.Context(), config=config)
    resolved = reloaded_plugin.package_service.resolve_package_artifact_metadata(
        {"artifact_id": artifact.artifact_id}
    )

    assert resolved["artifact_id"] == artifact.artifact_id
    assert Path(resolved["path"]).exists()


def test_sharelife_market_lists_bundled_official_template(tmp_path: Path) -> None:
    module = _load_plugin_module(tmp_path)
    plugin = module.SharelifePlugin(module.Context(), config={"webui": {"enabled": False}})

    output = asyncio.run(_collect(plugin.sharelife_market(FakeEvent())))[0]

    assert "community/basic@1.0.0" in output
    assert "community/writing-polish@1.0.0" in output
    assert "community/coding-review@1.0.0" in output


def test_sharelife_prompt_and_package_work_for_bundled_official_template(tmp_path: Path) -> None:
    module = _load_plugin_module(tmp_path)
    plugin = module.SharelifePlugin(module.Context(), config={"webui": {"enabled": False}})

    prompt = asyncio.run(_collect(plugin.sharelife_prompt(FakeEvent(), "community/basic")))[0]
    package = asyncio.run(_collect(plugin.sharelife_package(FakeEvent(), "community/basic")))[0]

    assert "Sharelife Community Basic" in prompt
    assert package.startswith("template package generated: ")


def test_sharelife_profile_pack_export_and_list_commands(tmp_path: Path) -> None:
    module = _load_plugin_module(tmp_path)
    plugin = module.SharelifePlugin(module.Context(), config={"webui": {"enabled": False}})
    admin = FakeEvent(sender_id="admin-1", role="admin")

    exported = asyncio.run(_collect(plugin.sharelife_profile_export(admin, "profile/basic", "1.0.0")))[0]
    assert exported.startswith("profile pack exported:")

    exports = asyncio.run(_collect(plugin.sharelife_profile_exports(admin, "10")))[0]
    assert "profile/basic@1.0.0" in exports

    imports = asyncio.run(_collect(plugin.sharelife_profile_imports(admin, "10")))[0]
    assert imports == "no imported profile packs"


def test_sharelife_profile_pack_export_command_accepts_sections_mask_and_drop(tmp_path: Path) -> None:
    module = _load_plugin_module(tmp_path)
    plugin = module.SharelifePlugin(module.Context(), config={"webui": {"enabled": False}})
    admin = FakeEvent(sender_id="admin-1", role="admin")

    exported = asyncio.run(
        _collect(
            plugin.sharelife_profile_export(
                admin,
                "profile/scoped",
                "1.0.0",
                "include_provider_no_key",
                "providers,plugins,providers",
                "providers.openai.base_url",
                "sharelife_meta.owner",
            )
        )
    )[0]
    assert exported.startswith("profile pack exported:")

    artifact_id = exported.split(":", 1)[1].strip()
    artifact = plugin.profile_pack_service.get_export_artifact(artifact_id)
    assert artifact.manifest.redaction_policy.include_sections == ["providers", "plugins"]
    assert artifact.manifest.redaction_policy.mask_paths == ["providers.openai.base_url"]
    assert artifact.manifest.redaction_policy.drop_paths == ["sharelife_meta.owner"]


def test_sharelife_profile_pack_export_command_supports_extension_pack_type(tmp_path: Path) -> None:
    module = _load_plugin_module(tmp_path)
    plugin = module.SharelifePlugin(module.Context(), config={"webui": {"enabled": False}})
    admin = FakeEvent(sender_id="admin-1", role="admin")

    exported = asyncio.run(
        _collect(
            plugin.sharelife_profile_export(
                admin,
                "extension/community-tools",
                "1.0.0",
                "exclude_secrets",
                "",
                "",
                "",
                "extension_pack",
            )
        )
    )[0]
    assert exported.startswith("profile pack exported:")

    artifact_id = exported.split(":", 1)[1].strip()
    artifact = plugin.profile_pack_service.get_export_artifact(artifact_id)
    assert artifact.manifest.pack_type == "extension_pack"
    assert artifact.manifest.sections == ["plugins", "skills", "personas", "mcp_servers"]


def test_sharelife_profile_pack_import_command_accepts_export_artifact_id(tmp_path: Path) -> None:
    module = _load_plugin_module(tmp_path)
    plugin = module.SharelifePlugin(module.Context(), config={"webui": {"enabled": False}})
    admin = FakeEvent(sender_id="admin-1", role="admin")

    exported = asyncio.run(_collect(plugin.sharelife_profile_export(admin, "profile/restore", "1.0.0")))[0]
    artifact_id = exported.split(":", 1)[1].strip()
    assert artifact_id

    imported = asyncio.run(
        _collect(
            plugin.sharelife_profile_import(
                admin,
                artifact_id,
                "--dryrun",
                "--plan-id",
                "profile-restore-plan",
                "--sections",
                "plugins,providers",
            )
        )
    )[0]
    assert imported.startswith("profile pack imported:")
    assert "dryrun ready: profile-restore-plan" in imported

    imports = asyncio.run(_collect(plugin.sharelife_profile_imports(admin, "10")))[0]
    assert "profile/restore@1.0.0" in imports


def test_sharelife_profile_pack_import_dryrun_command_accepts_export_artifact_id(tmp_path: Path) -> None:
    module = _load_plugin_module(tmp_path)
    plugin = module.SharelifePlugin(module.Context(), config={"webui": {"enabled": False}})
    admin = FakeEvent(sender_id="admin-1", role="admin")

    exported = asyncio.run(_collect(plugin.sharelife_profile_export(admin, "profile/quick", "1.0.0")))[0]
    artifact_id = exported.split(":", 1)[1].strip()
    assert artifact_id

    response = asyncio.run(
        _collect(
            plugin.sharelife_profile_import_dryrun(
                admin,
                artifact_id,
                "profile-plan-quick",
                "plugins,providers",
            )
        )
    )[0]
    assert response == "profile pack import+dryrun ready: profile-plan-quick"


def test_sharelife_profile_pack_import_dryrun_latest_uses_most_recent_export(tmp_path: Path) -> None:
    module = _load_plugin_module(tmp_path)
    plugin = module.SharelifePlugin(module.Context(), config={"webui": {"enabled": False}})
    admin = FakeEvent(sender_id="admin-1", role="admin")

    old_export = asyncio.run(_collect(plugin.sharelife_profile_export(admin, "profile/old", "1.0.0")))[0]
    assert old_export.startswith("profile pack exported:")
    new_export = asyncio.run(_collect(plugin.sharelife_profile_export(admin, "profile/new", "1.0.0")))[0]
    assert new_export.startswith("profile pack exported:")

    response = asyncio.run(
        _collect(
            plugin.sharelife_profile_import_dryrun_latest(
                admin,
                "profile-plan-latest",
                "plugins",
            )
        )
    )[0]
    assert response == "profile pack import+dryrun ready: profile-plan-latest"

    imports = asyncio.run(_collect(plugin.sharelife_profile_imports(admin, "10")))[0]
    assert "profile/new@1.0.0" in imports


def test_sharelife_profile_plugin_install_confirmation_commands(tmp_path: Path) -> None:
    module = _load_plugin_module(tmp_path)
    plugin = module.SharelifePlugin(module.Context(), config={"webui": {"enabled": False}})
    admin = FakeEvent(sender_id="admin-1", role="admin")

    plugin.runtime_bridge.apply_patch(
        {
            "plugins": {
                "sharelife": {"enabled": True},
                "community_tools": {
                    "enabled": True,
                    "version": "1.2.3",
                    "source": "https://github.com/acme/community-tools",
                    "install_cmd": "pip install astrbot-plugin-community-tools==1.2.3",
                },
            }
        }
    )
    exported = asyncio.run(
        _collect(
            plugin.sharelife_profile_export(
                admin,
                "extension/community-tools",
                "1.0.0",
                "exclude_secrets",
                "",
                "",
                "",
                "extension_pack",
            )
        )
    )[0]
    artifact_id = exported.split(":", 1)[1].strip()
    assert artifact_id

    plugin.runtime_bridge.apply_patch(
        {
            "plugins": {
                "sharelife": {"enabled": True},
            }
        }
    )
    imported_response = asyncio.run(
        _collect(
            plugin.sharelife_profile_import(
                admin,
                artifact_id,
            )
        )
    )[0]
    import_id = imported_response.split(":", 1)[1].strip()
    assert import_id

    plan = asyncio.run(_collect(plugin.sharelife_profile_plugins(admin, import_id)))[0]
    assert "confirmation_required" in plan
    assert "community_tools" in plan

    confirmed = asyncio.run(
        _collect(
            plugin.sharelife_profile_plugins_confirm(
                admin,
                import_id,
                "community_tools",
            )
        )
    )[0]
    assert confirmed == "plugin install confirmation updated: confirmed"

    disabled = asyncio.run(
        _collect(
            plugin.sharelife_profile_plugins_install(
                admin,
                import_id,
            )
        )
    )[0]
    assert (
        disabled
        == "plugin install execution is disabled; set profile_pack.plugin_install.enabled=true"
    )

    plugin.profile_pack_service.plugin_install_service.enabled = True
    plugin.profile_pack_service.plugin_install_service.command_runner = lambda command, timeout_seconds: {
        "returncode": 0,
        "stdout": "ok",
        "stderr": "",
        "timed_out": False,
    }
    executed = asyncio.run(
        _collect(
            plugin.sharelife_profile_plugins_install(
                admin,
                import_id,
                "community_tools",
            )
        )
    )[0]
    assert executed == "plugin install execution: executed installed=1 failed=0 blocked=0"


def test_sharelife_profile_pack_import_command_rejects_invalid_options(tmp_path: Path) -> None:
    module = _load_plugin_module(tmp_path)
    plugin = module.SharelifePlugin(module.Context(), config={"webui": {"enabled": False}})
    admin = FakeEvent(sender_id="admin-1", role="admin")

    exported = asyncio.run(_collect(plugin.sharelife_profile_export(admin, "profile/restore", "1.0.0")))[0]
    artifact_id = exported.split(":", 1)[1].strip()
    assert artifact_id

    parse_error = asyncio.run(
        _collect(
            plugin.sharelife_profile_import(
                admin,
                artifact_id,
                "--unsupported",
            )
        )
    )[0]
    assert parse_error == "unsupported option: --unsupported"


def test_plugin_uses_json_file_runtime_bridge_by_default(tmp_path: Path) -> None:
    module = _load_plugin_module(tmp_path)
    plugin = module.SharelifePlugin(module.Context(), config={"webui": {"enabled": False}})

    plugin.runtime_bridge.apply_patch({"providers": {"openai": {"organization": "org-sharelife"}}})
    runtime_file = tmp_path / "plugin_data" / "sharelife" / "runtime_state.json"
    assert runtime_file.exists()

    plugin_reloaded = module.SharelifePlugin(module.Context(), config={"webui": {"enabled": False}})
    snapshot = plugin_reloaded.runtime_bridge.snapshot()
    assert snapshot["providers"]["openai"]["organization"] == "org-sharelife"


def test_plugin_profile_pack_security_config_is_wired(tmp_path: Path) -> None:
    module = _load_plugin_module(tmp_path)
    plugin = module.SharelifePlugin(
        module.Context(),
        config={
            "webui": {"enabled": False},
            "profile_pack": {
                "signing_key_id": "team-default",
                "signing_secret": "profile-pack-signing-secret",
                "trusted_signing_keys": {
                    "team-default": "profile-pack-signing-secret",
                    "legacy": "legacy-secret",
                },
                "secrets_encryption_key": "profile-pack-encryption-secret",
                "plugin_install": {
                    "enabled": True,
                    "command_timeout_seconds": 120,
                    "allowed_command_prefixes": "pip,uv",
                    "allow_http_source": True,
                    "require_success_before_apply": True,
                },
            },
        },
    )

    assert plugin.profile_pack_service.signing_key_id == "team-default"
    assert plugin.profile_pack_service.signing_secret == "profile-pack-signing-secret"
    assert plugin.profile_pack_service.secrets_encryption_key == "profile-pack-encryption-secret"
    assert plugin.profile_pack_service.trusted_signing_keys["team-default"] == "profile-pack-signing-secret"
    assert plugin.profile_pack_service.trusted_signing_keys["legacy"] == "legacy-secret"
    assert plugin.profile_pack_service.plugin_install_service.enabled is True
    assert plugin.profile_pack_service.plugin_install_service.command_timeout_seconds == 120
    assert plugin.profile_pack_service.plugin_install_service.allow_http_source is True
    assert plugin.profile_pack_service.plugin_install_service.require_success_before_apply is True
    assert plugin.profile_pack_service.plugin_install_service.allowed_command_prefixes == {"pip", "uv"}


def test_plugin_public_market_auto_publish_config_is_wired(tmp_path: Path) -> None:
    module = _load_plugin_module(tmp_path)
    public_market_root = tmp_path / "public-market-root"
    plugin = module.SharelifePlugin(
        module.Context(),
        config={
            "webui": {
                "enabled": False,
                "public_market": {
                    "auto_publish_profile_pack_approve": True,
                    "root": str(public_market_root),
                    "rebuild_snapshot_on_publish": False,
                },
            },
        },
    )

    assert plugin.api.public_market_auto_publish_profile_pack_approve is True
    assert plugin.api.public_market_root == public_market_root.resolve()
    assert plugin.api.public_market_rebuild_snapshot_on_publish is False
