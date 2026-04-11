from __future__ import annotations

import base64
import io
import json
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
import zipfile

from sharelife.application.services_apply import ApplyService
from sharelife.application.services_audit import AuditService
from sharelife.application.services_continuity import ConfigContinuityService
from sharelife.application.services_market import MarketService
from sharelife.application.services_package import PackageService
from sharelife.application.services_preferences import PreferenceService
from sharelife.application.services_profile_pack import ProfilePackService
from sharelife.application.services_queue import RetryQueueService
from sharelife.application.services_trial import TrialService
from sharelife.application.services_trial_request import TrialRequestService
from sharelife.infrastructure.json_state_store import JsonStateStore
from sharelife.infrastructure.notifier import InMemoryNotifier
from sharelife.infrastructure.runtime_bridge import InMemoryRuntimeBridge
from sharelife.interfaces.api_v1 import SharelifeApiV1
from sharelife.interfaces.web_api_v1 import SharelifeWebApiV1


class FrozenClock:
    def __init__(self, start: datetime):
        self.current = start

    def utcnow(self) -> datetime:
        return self.current

    def shift(self, **kwargs) -> None:
        self.current = self.current + timedelta(**kwargs)


def build_interfaces(
    tmp_path,
    *,
    auto_publish_profile_pack_approve: bool = False,
    public_market_root: Path | None = None,
    rebuild_snapshot_on_publish: bool = True,
):
    clock = FrozenClock(datetime(2026, 3, 30, 3, 0, tzinfo=UTC))
    runtime = InMemoryRuntimeBridge(
        initial_state={
            "astrbot_core": {"name": "sharelife-bot"},
            "providers": {"openai": {"api_key": "sk-live-secret", "model": "gpt-5"}},
            "plugins": {"sharelife": {"enabled": True}},
        }
    )
    preferences = PreferenceService()
    queue = RetryQueueService(clock=clock)
    trial = TrialService(clock=clock)
    notifier = InMemoryNotifier()
    trial_request = TrialRequestService(
        trial_service=trial,
        retry_queue_service=queue,
        notifier=notifier,
    )
    market = MarketService(clock=clock)
    package = PackageService(
        market_service=market,
        output_root=tmp_path / "packages",
        clock=clock,
        artifact_state_store=JsonStateStore(tmp_path / "artifact_state.json"),
    )
    continuity = ConfigContinuityService(
        state_store=JsonStateStore(tmp_path / "continuity_state.json"),
        clock=clock,
    )
    apply_service = ApplyService(runtime=runtime, continuity_service=continuity)
    audit = AuditService(clock=clock)
    profile_pack = ProfilePackService(
        runtime=runtime,
        apply_service=apply_service,
        output_root=tmp_path / "profile-packs",
        clock=clock,
        astrbot_version="4.16.0",
        plugin_version="0.1.0",
    )
    api = SharelifeApiV1(
        preference_service=preferences,
        retry_queue_service=queue,
        trial_request_service=trial_request,
        market_service=market,
        package_service=package,
        apply_service=apply_service,
        audit_service=audit,
        profile_pack_service=profile_pack,
        public_market_auto_publish_profile_pack_approve=auto_publish_profile_pack_approve,
        public_market_root=public_market_root,
        public_market_rebuild_snapshot_on_publish=rebuild_snapshot_on_publish,
    )
    web_api = SharelifeWebApiV1(api=api, notifier=notifier)
    return api, web_api


def test_api_admin_profile_pack_export_import_dryrun_apply_flow(tmp_path):
    api, _ = build_interfaces(tmp_path)

    exported = api.admin_export_profile_pack(
        role="admin",
        pack_id="profile/basic",
        version="1.0.0",
        redaction_mode="exclude_secrets",
        mask_paths=["providers.openai.model"],
        drop_paths=["sharelife_meta.owner"],
    )
    assert exported["pack_id"] == "profile/basic"
    assert Path(exported["path"]).exists()

    imported = api.admin_import_profile_pack(
        role="admin",
        filename=exported["filename"],
        content_base64=base64.b64encode(Path(exported["path"]).read_bytes()).decode("ascii"),
    )
    assert imported["compatibility"] in {"compatible", "degraded", "blocked"}
    assert imported["import_id"]

    dryrun = api.admin_profile_pack_dryrun(
        role="admin",
        import_id=imported["import_id"],
        plan_id="plan-profile-basic",
        selected_sections=["plugins"],
    )
    assert dryrun["status"] == "dryrun_ready"
    assert dryrun["selected_sections"] == ["plugins"]

    applied = api.admin_profile_pack_apply(role="admin", plan_id="plan-profile-basic")
    assert applied["status"] == "applied"
    assert applied["continuity"]["source_kind"] == "profile_pack"
    assert applied["continuity"]["selected_sections"] == ["plugins"]

    continuity = api.admin_get_continuity(role="admin", plan_id="plan-profile-basic")
    assert continuity["entry"]["source_kind"] == "profile_pack"
    assert continuity["entry"]["selected_sections"] == ["plugins"]

    listed_imports = api.admin_list_profile_pack_imports(role="admin", limit=20)
    assert len(listed_imports["imports"]) == 1
    assert listed_imports["imports"][0]["import_id"] == imported["import_id"]

    listed_exports = api.admin_list_profile_pack_exports(role="admin", limit=20)
    assert len(listed_exports["exports"]) == 1
    assert listed_exports["exports"][0]["artifact_id"] == exported["artifact_id"]
    assert listed_exports["exports"][0]["redaction_mode"] == "exclude_secrets"


def test_api_admin_profile_pack_import_and_dryrun_from_export(tmp_path):
    api, _ = build_interfaces(tmp_path)
    exported = api.admin_export_profile_pack(
        role="admin",
        pack_id="profile/basic",
        version="1.0.0",
        redaction_mode="exclude_secrets",
    )
    prepared = api.admin_import_profile_pack_and_dryrun(
        role="admin",
        artifact_id=exported["artifact_id"],
        plan_id="profile-plan-quick",
        selected_sections=["plugins"],
    )
    assert prepared["status"] == "imported_dryrun_ready"
    assert prepared["plan_id"] == "profile-plan-quick"
    assert prepared["dryrun"]["status"] == "dryrun_ready"


def test_api_profile_pack_rejects_non_admin(tmp_path):
    api, _ = build_interfaces(tmp_path)

    denied = api.admin_export_profile_pack(
        role="member",
        pack_id="profile/basic",
        version="1.0.0",
        redaction_mode="exclude_secrets",
    )
    assert denied["error"] == "permission_denied"


def test_api_supports_extension_pack_export_and_type_filtering(tmp_path):
    api, _ = build_interfaces(tmp_path)

    exported = api.admin_export_profile_pack(
        role="admin",
        pack_id="extension/community-tools",
        version="1.0.0",
        pack_type="extension_pack",
        redaction_mode="exclude_secrets",
    )
    assert exported["pack_type"] == "extension_pack"

    imported = api.admin_import_profile_pack_from_export(
        role="admin",
        artifact_id=exported["artifact_id"],
    )
    assert imported["pack_type"] == "extension_pack"

    submitted = api.submit_profile_pack(
        user_id="member-1",
        artifact_id=exported["artifact_id"],
    )
    assert submitted["pack_type"] == "extension_pack"

    decided = api.admin_decide_profile_pack_submission(
        role="admin",
        submission_id=submitted["submission_id"],
        decision="approve",
    )
    assert decided["pack_type"] == "extension_pack"

    extension_catalog = api.list_profile_pack_catalog(pack_type="extension_pack")
    assert len(extension_catalog["packs"]) == 1
    assert extension_catalog["packs"][0]["pack_type"] == "extension_pack"

    bot_catalog = api.list_profile_pack_catalog(pack_type="bot_profile_pack")
    assert bot_catalog["packs"] == []


def test_api_submit_profile_pack_returns_normalized_submit_options(tmp_path):
    api, _ = build_interfaces(tmp_path)
    exported = api.admin_export_profile_pack(
        role="admin",
        pack_id="profile/community-safe",
        version="1.0.0",
        redaction_mode="exclude_secrets",
    )

    submitted = api.submit_profile_pack(
        user_id="member-1",
        artifact_id=exported["artifact_id"],
        submit_options={
            "pack_type": "extension_pack",
            "selected_sections": "plugins,providers",
            "redaction_mode": "include_provider_no_key",
            "replace_existing": True,
        },
    )

    assert submitted["submit_options"] == {
        "pack_type": "extension_pack",
        "selected_sections": ["plugins", "providers"],
        "selected_item_paths": [],
        "redaction_mode": "include_provider_no_key",
        "replace_existing": True,
    }


def test_api_profile_pack_submit_option_normalizer_deduplicates_selected_sections_and_item_paths():
    normalized = SharelifeApiV1._normalize_profile_pack_submit_options(
        {
            "selected_sections": ["plugins", "plugins", "providers"],
            "selected_item_paths": (
                "plugins.enabled,"
                "plugins.enabled,"
                "providers.openai.model"
            ),
        },
    )
    assert normalized["selected_sections"] == [
        "plugins",
        "providers",
    ]
    assert normalized["selected_item_paths"] == [
        "plugins.enabled",
        "providers.openai.model",
    ]


def test_api_submit_profile_pack_preserves_selected_item_paths_and_materializes_filtered_submission(tmp_path):
    api, _ = build_interfaces(tmp_path)
    raw_bytes = json.dumps(
        {
            "config_version": 2,
            "provider": [
                {
                    "id": "test-openai",
                    "type": "openai_chat_completion",
                    "model": "gpt-4o-mini",
                    "key": ["test-key"],
                }
            ],
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

    imported = api.member_import_profile_pack(
        user_id="member-1",
        filename="cmd_config.json",
        content_base64=base64.b64encode(raw_bytes).decode("ascii"),
    )
    source_artifact_id = imported["source_artifact_id"]

    submitted = api.submit_profile_pack(
        user_id="member-1",
        artifact_id=source_artifact_id,
        submit_options={
            "selected_sections": ["personas", "environment_manifest"],
            "selected_item_paths": [
                "personas.runtime.default_personality",
                "personas.entries.analyst",
                "environment_manifest.subagent_orchestrator.agents[0]",
            ],
        },
    )

    assert submitted["submit_options"]["selected_sections"] == ["personas", "environment_manifest"]
    assert submitted["submit_options"]["selected_item_paths"] == [
        "personas.runtime.default_personality",
        "personas.entries.analyst",
        "environment_manifest.subagent_orchestrator.agents[0]",
    ]
    assert submitted["artifact_id"] != source_artifact_id
    assert submitted["sections"] == ["personas", "environment_manifest"]

    detail = api.member_get_profile_pack_submission_detail(
        user_id="member-1",
        submission_id=submitted["submission_id"],
    )
    assert detail["submit_options"]["selected_item_paths"] == submitted["submit_options"]["selected_item_paths"]
    assert detail["sections"] == ["personas", "environment_manifest"]


def test_api_submit_profile_pack_replace_existing_retires_previous_pending_submission(tmp_path):
    api, _ = build_interfaces(tmp_path)
    exported = api.admin_export_profile_pack(
        role="admin",
        pack_id="profile/community-safe-replace",
        version="1.0.0",
        redaction_mode="exclude_secrets",
    )

    first = api.submit_profile_pack(
        user_id="member-1",
        artifact_id=exported["artifact_id"],
    )
    assert first["status"] == "pending"

    second = api.submit_profile_pack(
        user_id="member-1",
        artifact_id=exported["artifact_id"],
        submit_options={"replace_existing": True},
    )
    assert second["status"] == "pending"
    assert second["replaced_submission_count"] == 1
    assert second["replaced_submission_ids"] == [first["submission_id"]]

    first_detail = api.member_get_profile_pack_submission_detail(
        user_id="member-1",
        submission_id=first["submission_id"],
    )
    assert first_detail["status"] == "replaced"

    pending_rows = api.member_list_profile_pack_submissions(
        user_id="member-1",
        status="pending",
    )
    assert [item["submission_id"] for item in pending_rows["submissions"]] == [second["submission_id"]]

    replaced_rows = api.member_list_profile_pack_submissions(
        user_id="member-1",
        status="replaced",
    )
    assert [item["submission_id"] for item in replaced_rows["submissions"]] == [first["submission_id"]]

    audit = api.admin_list_audit(role="admin", limit=20)
    assert any(item["action"] == "profile_pack.submission.pending_replaced" for item in audit["events"])


def test_api_submit_profile_pack_idempotency_key_replays_existing_submission(tmp_path):
    api, _ = build_interfaces(tmp_path)
    exported = api.admin_export_profile_pack(
        role="admin",
        pack_id="profile/community-safe-idempotent",
        version="1.0.0",
        redaction_mode="exclude_secrets",
    )

    first = api.submit_profile_pack(
        user_id="member-1",
        artifact_id=exported["artifact_id"],
        submit_options={"idempotency_key": "profile-pack-key-1"},
    )
    assert first["status"] == "pending"

    second = api.submit_profile_pack(
        user_id="member-1",
        artifact_id=exported["artifact_id"],
        submit_options={"idempotency_key": "profile-pack-key-1"},
    )
    assert second["submission_id"] == first["submission_id"]
    assert second["idempotent_replay"] is True

    rows = api.member_list_profile_pack_submissions(user_id="member-1")
    assert len(rows["submissions"]) == 1
    events = api.admin_list_audit(role="admin", limit=30)
    assert any(item["action"] == "profile_pack.submission.idempotency_replayed" for item in events["events"])


def test_api_submit_profile_pack_idempotency_key_conflict_is_rejected(tmp_path):
    api, _ = build_interfaces(tmp_path)
    exported_first = api.admin_export_profile_pack(
        role="admin",
        pack_id="profile/community-safe-idempotent-a",
        version="1.0.0",
        redaction_mode="exclude_secrets",
    )
    exported_second = api.admin_export_profile_pack(
        role="admin",
        pack_id="profile/community-safe-idempotent-b",
        version="1.0.0",
        redaction_mode="exclude_secrets",
    )

    first = api.submit_profile_pack(
        user_id="member-1",
        artifact_id=exported_first["artifact_id"],
        submit_options={"idempotency_key": "profile-pack-key-2"},
    )
    assert first["status"] == "pending"

    conflict = api.submit_profile_pack(
        user_id="member-1",
        artifact_id=exported_second["artifact_id"],
        submit_options={"idempotency_key": "profile-pack-key-2"},
    )
    assert conflict["error"] == "idempotency_key_conflict"
    assert conflict["existing_submission_id"] == first["submission_id"]

    rows = api.member_list_profile_pack_submissions(user_id="member-1")
    assert len(rows["submissions"]) == 1
    events = api.admin_list_audit(role="admin", limit=30)
    assert any(item["action"] == "profile_pack.submission.idempotency_conflict" for item in events["events"])


def test_api_profile_pack_plugin_install_confirmation_flow(tmp_path):
    export_api, _ = build_interfaces(tmp_path / "exporter")
    import_api, _ = build_interfaces(tmp_path / "importer")

    export_api.profile_pack_service.runtime.state["plugins"]["community_tools"] = {
        "enabled": True,
        "version": "1.2.3",
        "source": "https://github.com/acme/community-tools",
        "sha256": "abc123",
        "install_cmd": "pip install astrbot-plugin-community-tools==1.2.3",
    }
    exported = export_api.admin_export_profile_pack(
        role="admin",
        pack_id="extension/community-tools",
        version="1.0.0",
        pack_type="extension_pack",
        redaction_mode="exclude_secrets",
    )
    assert exported["artifact_id"]

    imported = import_api.admin_import_profile_pack(
        role="admin",
        filename=exported["filename"],
        content_base64=base64.b64encode(Path(exported["path"]).read_bytes()).decode("ascii"),
    )
    import_id = imported["import_id"]

    install_plan = import_api.admin_profile_pack_plugin_install_plan(
        role="admin",
        import_id=import_id,
    )
    assert install_plan["status"] == "confirmation_required"
    assert install_plan["required_plugins"] == ["community_tools"]

    blocked = import_api.admin_profile_pack_dryrun(
        role="admin",
        import_id=import_id,
        plan_id="plan-extension-community-tools",
        selected_sections=["plugins"],
    )
    assert blocked["error"] == "profile_pack_plugin_install_confirm_required"

    confirmed = import_api.admin_profile_pack_confirm_plugin_install(
        role="admin",
        import_id=import_id,
        plugin_ids=["community_tools"],
    )
    assert confirmed["status"] == "confirmed"
    assert confirmed["missing_plugins"] == []

    disabled_execute = import_api.admin_profile_pack_execute_plugin_install(
        role="admin",
        import_id=import_id,
        plugin_ids=["community_tools"],
    )
    assert disabled_execute["error"] == "profile_pack_plugin_install_exec_disabled"

    plugin_install_service = import_api.profile_pack_service.plugin_install_service
    plugin_install_service.enabled = True
    plugin_install_service.command_runner = lambda command, timeout_seconds: {
        "returncode": 0,
        "stdout": "ok",
        "stderr": "",
        "timed_out": False,
    }

    executed = import_api.admin_profile_pack_execute_plugin_install(
        role="admin",
        import_id=import_id,
        plugin_ids=["community_tools"],
    )
    assert executed["status"] == "executed"
    assert executed["execution"]["result"]["installed_count"] == 1
    attempt = executed["execution"]["result"]["attempts"][0]
    assert attempt["status"] == "installed"
    assert attempt["plugin_id"] == "community_tools"

    refreshed_plan = import_api.admin_profile_pack_plugin_install_plan(
        role="admin",
        import_id=import_id,
    )
    assert refreshed_plan["latest_execution"]["status"] == "executed"

    dryrun = import_api.admin_profile_pack_dryrun(
        role="admin",
        import_id=import_id,
        plan_id="plan-extension-community-tools",
        selected_sections=["plugins"],
    )
    assert dryrun["status"] == "dryrun_ready"
    assert dryrun["plugin_install"]["status"] == "confirmed"


def test_web_api_profile_pack_validates_payload(tmp_path):
    _, web_api = build_interfaces(tmp_path)

    invalid = web_api.admin_import_profile_pack(
        role="admin",
        filename="",
        content_base64="",
    )
    assert invalid.ok is False
    assert invalid.status_code == 400
    assert invalid.error_code == "profile_pack_payload_required"


def test_web_api_profile_pack_list_routes(tmp_path):
    _, web_api = build_interfaces(tmp_path)
    exported = web_api.admin_export_profile_pack(
        role="admin",
        pack_id="profile/basic",
        version="1.0.0",
        redaction_mode="exclude_secrets",
    )
    imported = web_api.admin_import_profile_pack(
        role="admin",
        filename=exported.data["filename"],
        content_base64=base64.b64encode(Path(exported.data["path"]).read_bytes()).decode("ascii"),
    )
    assert imported.ok is True

    imports_rows = web_api.admin_list_profile_pack_imports(role="admin", limit=10)
    assert imports_rows.ok is True
    assert len(imports_rows.data["imports"]) == 1

    exports_rows = web_api.admin_list_profile_pack_exports(role="admin", limit=10)
    assert exports_rows.ok is True
    assert len(exports_rows.data["exports"]) == 1


def test_web_api_profile_pack_import_from_export_artifact(tmp_path):
    _, web_api = build_interfaces(tmp_path)
    exported = web_api.admin_export_profile_pack(
        role="admin",
        pack_id="profile/basic",
        version="1.0.0",
        redaction_mode="exclude_secrets",
    )
    assert exported.ok is True

    imported = web_api.admin_import_profile_pack_from_export(
        role="admin",
        artifact_id=exported.data["artifact_id"],
    )
    assert imported.ok is True
    assert imported.data["import_id"]
    assert imported.data["source_artifact_id"] == exported.data["artifact_id"]


def test_web_api_profile_pack_import_and_dryrun_from_export(tmp_path):
    _, web_api = build_interfaces(tmp_path)
    exported = web_api.admin_export_profile_pack(
        role="admin",
        pack_id="profile/basic",
        version="1.0.0",
        redaction_mode="exclude_secrets",
    )
    assert exported.ok is True

    prepared = web_api.admin_import_profile_pack_and_dryrun(
        role="admin",
        artifact_id=exported.data["artifact_id"],
        plan_id="profile-plan-quick",
        selected_sections=["plugins"],
    )
    assert prepared.ok is True
    assert prepared.data["status"] == "imported_dryrun_ready"
    assert prepared.data["plan_id"] == "profile-plan-quick"
    assert prepared.data["source_artifact_id"] == exported.data["artifact_id"]
    assert prepared.data["dryrun"]["status"] == "dryrun_ready"


def test_web_api_profile_pack_import_and_dryrun_requires_source(tmp_path):
    _, web_api = build_interfaces(tmp_path)
    invalid = web_api.admin_import_profile_pack_and_dryrun(
        role="admin",
        artifact_id="",
        filename="",
        content_base64="",
        plan_id="profile-plan-quick",
    )
    assert invalid.ok is False
    assert invalid.status_code == 400
    assert invalid.error_code == "profile_pack_import_source_required"


def test_api_profile_pack_submission_review_publish_flow(tmp_path):
    api, _ = build_interfaces(tmp_path)
    exported = api.admin_export_profile_pack(
        role="admin",
        pack_id="profile/community-basic",
        version="1.0.0",
        redaction_mode="exclude_secrets",
    )
    assert exported["artifact_id"]

    submitted = api.submit_profile_pack(
        user_id="member-1",
        artifact_id=exported["artifact_id"],
    )
    assert submitted["status"] == "pending"
    assert submitted["pack_id"] == "profile/community-basic"

    queue_rows = api.admin_list_profile_pack_submissions(role="admin", status="pending")
    assert len(queue_rows["submissions"]) == 1
    assert queue_rows["submissions"][0]["submission_id"] == submitted["submission_id"]

    decided = api.admin_decide_profile_pack_submission(
        role="admin",
        submission_id=submitted["submission_id"],
        decision="approve",
        review_note="Approved with notice.",
        review_labels=["risk_medium", "approved_with_notice"],
    )
    assert decided["status"] == "approved"
    assert decided["review_labels"] == ["risk_medium", "approved_with_notice"]

    listed = api.list_profile_pack_catalog(pack_query="community-basic")
    assert len(listed["packs"]) == 1
    assert listed["packs"][0]["pack_id"] == "profile/community-basic"
    assert listed["packs"][0]["source_submission_id"] == submitted["submission_id"]

    detail = api.get_profile_pack_catalog_detail(pack_id="profile/community-basic")
    assert detail["pack_id"] == "profile/community-basic"
    assert detail["source_submission_id"] == submitted["submission_id"]

    compared = api.compare_profile_pack_catalog(
        pack_id="profile/community-basic",
        selected_sections=["plugins"],
    )
    assert compared["status"] == "compare_ready"
    assert compared["pack_id"] == "profile/community-basic"
    assert compared["selected_sections"] == ["plugins"]
    assert "diff" in compared
    row = compared["diff"]["sections"][0]
    assert row["file_path"] == "sections/plugins.json"
    assert isinstance(row["before_preview"], list)
    assert isinstance(row["after_preview"], list)
    assert isinstance(row["diff_preview"], list)


def test_api_member_profile_pack_submission_views_are_owner_scoped(tmp_path):
    api, _ = build_interfaces(tmp_path)
    exported = api.admin_export_profile_pack(
        role="admin",
        pack_id="profile/community-owner-scope",
        version="1.0.0",
        redaction_mode="exclude_secrets",
    )
    own = api.submit_profile_pack(
        user_id="member-1",
        artifact_id=exported["artifact_id"],
    )
    other = api.submit_profile_pack(
        user_id="member-2",
        artifact_id=exported["artifact_id"],
    )

    listed = api.member_list_profile_pack_submissions(user_id="member-1")
    assert listed["user_id"] == "member-1"
    assert len(listed["submissions"]) == 1
    assert listed["submissions"][0]["submission_id"] == own["submission_id"]

    own_detail = api.member_get_profile_pack_submission_detail(
        user_id="member-1",
        submission_id=own["submission_id"],
    )
    assert own_detail["submission_id"] == own["submission_id"]
    assert own_detail["user_id"] == "member-1"

    own_export = api.member_get_profile_pack_submission_export(
        user_id="member-1",
        submission_id=own["submission_id"],
    )
    assert own_export["submission_id"] == own["submission_id"]
    assert own_export["artifact_id"] == own_detail["artifact_id"]
    assert Path(own_export["path"]).exists()

    denied = api.member_get_profile_pack_submission_detail(
        user_id="member-1",
        submission_id=other["submission_id"],
    )
    assert denied["error"] == "permission_denied"

    denied_export = api.member_get_profile_pack_submission_export(
        user_id="member-1",
        submission_id=other["submission_id"],
    )
    assert denied_export["error"] == "permission_denied"

    missing_export = api.member_get_profile_pack_submission_export(
        user_id="member-1",
        submission_id="",
    )
    assert missing_export["error"] == "submission_id_required"


def test_api_profile_pack_catalog_exposes_governance_evidence_and_featured_toggle(tmp_path):
    api, _ = build_interfaces(tmp_path)
    exported = api.admin_export_profile_pack(
        role="admin",
        pack_id="profile/community-governed",
        version="1.0.0",
        redaction_mode="exclude_secrets",
    )
    submitted = api.submit_profile_pack(user_id="member-1", artifact_id=exported["artifact_id"])
    api.admin_decide_profile_pack_submission(
        role="admin",
        submission_id=submitted["submission_id"],
        decision="approve",
        review_note="governance baseline",
        review_labels=["risk_low", "approved"],
    )

    catalog = api.list_profile_pack_catalog(pack_query="community-governed")
    assert len(catalog["packs"]) == 1
    row = catalog["packs"][0]
    assert "capability_summary" in row
    assert "compatibility_matrix" in row
    assert "review_evidence" in row
    assert row["featured"] is False

    featured = api.admin_set_profile_pack_featured(
        role="admin",
        pack_id="profile/community-governed",
        featured=True,
        note="featured for reproducibility and safety guardrails",
    )
    assert featured["featured"] is True
    assert featured["featured_note"].startswith("featured for")

    featured_only = api.list_profile_pack_catalog(featured="true")
    assert any(item["pack_id"] == "profile/community-governed" for item in featured_only["packs"])


def test_api_profile_pack_approval_auto_publishes_to_public_market(tmp_path):
    public_market_root = tmp_path / "public-root"
    api, _ = build_interfaces(
        tmp_path / "workspace",
        auto_publish_profile_pack_approve=True,
        public_market_root=public_market_root,
    )
    exported = api.admin_export_profile_pack(
        role="admin",
        pack_id="profile/community-autopublish",
        version="1.0.0",
        redaction_mode="exclude_secrets",
    )
    submitted = api.submit_profile_pack(user_id="member-1", artifact_id=exported["artifact_id"])
    decided = api.admin_decide_profile_pack_submission(
        role="admin",
        submission_id=submitted["submission_id"],
        decision="approve",
        review_note="publish this to public market",
        review_labels=["risk_low", "approved"],
    )

    publish = decided.get("public_market_publish", {})
    assert publish.get("status") == "succeeded"
    pipeline = publish.get("pipeline", {})
    assert pipeline.get("trace_id")
    assert pipeline.get("events", {}).get("decision")
    assert pipeline.get("events", {}).get("publish")
    assert pipeline.get("events", {}).get("snapshot")
    assert pipeline.get("events", {}).get("backup")
    entry_path = Path(str(publish["entry_path"]))
    package_path = Path(str(publish["package_path"]))
    assert entry_path.exists()
    assert package_path.exists()
    assert entry_path.parent == public_market_root / "market" / "entries"
    assert package_path.parent == public_market_root / "market" / "packages" / "community"

    entry_payload = json.loads(entry_path.read_text(encoding="utf-8"))
    assert entry_payload["pack_id"] == "profile/community-autopublish"
    assert entry_payload["source_submission_id"] == submitted["submission_id"]
    assert entry_payload["redaction_mode"] == "exclude_secrets"
    assert entry_payload["pipeline_trace_id"] == pipeline["trace_id"]
    assert entry_payload["pipeline_events"]["publish"] == pipeline["events"]["publish"]

    snapshot = public_market_root / "market" / "catalog.snapshot.json"
    assert snapshot.exists()
    snapshot_rows = json.loads(snapshot.read_text(encoding="utf-8"))["rows"]
    assert any(item.get("pack_id") == "profile/community-autopublish" for item in snapshot_rows)
    assert publish["snapshot"]["pipeline_event_id"] == pipeline["events"]["snapshot"]
    assert publish["backup"]["pipeline_event_id"] == pipeline["events"]["backup"]

    audit = api.admin_list_audit(role="admin", limit=60)
    events = audit.get("events", [])
    assert any(
        item.get("action") == "profile_pack.submission_decided"
        and (item.get("detail") or {}).get("pipeline_event_id") == pipeline["events"]["decision"]
        for item in events
    )
    assert any(
        item.get("action") == "profile_pack.public_market.publish"
        and (item.get("detail") or {}).get("pipeline_event_id") == pipeline["events"]["publish"]
        for item in events
    )
    assert any(
        item.get("action") == "profile_pack.public_market.snapshot_rebuilt"
        and (item.get("detail") or {}).get("pipeline_event_id") == pipeline["events"]["snapshot"]
        for item in events
    )
    assert any(
        item.get("action") == "profile_pack.public_market.backup_handoff"
        and (item.get("detail") or {}).get("pipeline_event_id") == pipeline["events"]["backup"]
        for item in events
    )


def test_api_profile_pack_approval_does_not_publish_when_flag_disabled(tmp_path):
    public_market_root = tmp_path / "public-root"
    api, _ = build_interfaces(
        tmp_path / "workspace",
        auto_publish_profile_pack_approve=False,
        public_market_root=public_market_root,
    )
    exported = api.admin_export_profile_pack(
        role="admin",
        pack_id="profile/community-not-published",
        version="1.0.0",
        redaction_mode="exclude_secrets",
    )
    submitted = api.submit_profile_pack(user_id="member-1", artifact_id=exported["artifact_id"])
    decided = api.admin_decide_profile_pack_submission(
        role="admin",
        submission_id=submitted["submission_id"],
        decision="approve",
    )

    assert decided["status"] == "approved"
    assert "public_market_publish" not in decided
    assert not (public_market_root / "market" / "entries").exists()
    assert not (public_market_root / "market" / "catalog.snapshot.json").exists()


def test_api_profile_pack_approval_keeps_decision_when_public_redaction_not_allowed(tmp_path):
    public_market_root = tmp_path / "public-root"
    api, _ = build_interfaces(
        tmp_path / "workspace",
        auto_publish_profile_pack_approve=True,
        public_market_root=public_market_root,
    )
    exported = api.admin_export_profile_pack(
        role="admin",
        pack_id="profile/community-redaction-blocked",
        version="1.0.0",
        redaction_mode="include_provider_no_key",
    )
    submitted = api.submit_profile_pack(user_id="member-1", artifact_id=exported["artifact_id"])
    decided = api.admin_decide_profile_pack_submission(
        role="admin",
        submission_id=submitted["submission_id"],
        decision="approve",
    )

    assert decided["status"] == "approved"
    publish = decided.get("public_market_publish", {})
    assert publish.get("status") == "failed"
    assert publish.get("error") == "public_market_redaction_not_allowed"
    assert not (public_market_root / "market" / "entries").exists()


def test_api_profile_pack_catalog_insights_returns_metrics_and_ranked_rows(tmp_path):
    api, _ = build_interfaces(tmp_path)

    exported_member = api.admin_export_profile_pack(
        role="admin",
        pack_id="profile/community-insights",
        version="1.0.0",
        pack_type="bot_profile_pack",
        redaction_mode="exclude_secrets",
    )
    submitted_member = api.submit_profile_pack(
        user_id="member-1",
        artifact_id=exported_member["artifact_id"],
    )
    api.admin_decide_profile_pack_submission(
        role="admin",
        submission_id=submitted_member["submission_id"],
        decision="approve",
        review_labels=["risk_low", "approved"],
    )
    api.admin_set_profile_pack_featured(
        role="admin",
        pack_id="profile/community-insights",
        featured=True,
        note="featured insights test",
    )

    exported_extension = api.admin_export_profile_pack(
        role="admin",
        pack_id="extension/community-insights-tools",
        version="1.0.0",
        pack_type="extension_pack",
        redaction_mode="exclude_secrets",
    )
    submitted_extension = api.submit_profile_pack(
        user_id="member-2",
        artifact_id=exported_extension["artifact_id"],
    )
    api.admin_decide_profile_pack_submission(
        role="admin",
        submission_id=submitted_extension["submission_id"],
        decision="approve",
        review_labels=["risk_low", "approved"],
    )

    insights = api.list_profile_pack_catalog_insights(pack_query="community-insights")
    assert insights["metrics"]["total"] == 2
    assert insights["metrics"]["featured"] == 1
    assert insights["metrics"]["bot_profile_pack"] == 1
    assert insights["metrics"]["extension_pack"] == 1
    assert insights["featured"]["pack_id"] == "profile/community-insights"
    assert len(insights["trending"]) == 2
    assert insights["trending"][0]["trend_score"] >= insights["trending"][1]["trend_score"]

    extension_only = api.list_profile_pack_catalog_insights(
        pack_query="community-insights",
        pack_type="extension_pack",
    )
    assert extension_only["metrics"]["total"] == 1
    assert extension_only["metrics"]["extension_pack"] == 1
    assert extension_only["trending"][0]["pack_type"] == "extension_pack"


def test_web_api_profile_pack_submission_review_publish_routes(tmp_path):
    _, web_api = build_interfaces(tmp_path)
    exported = web_api.admin_export_profile_pack(
        role="admin",
        pack_id="profile/community-safe",
        version="1.0.0",
        redaction_mode="exclude_secrets",
    )
    assert exported.ok is True

    submitted = web_api.submit_profile_pack(
        user_id="member-1",
        artifact_id=exported.data["artifact_id"],
    )
    assert submitted.ok is True
    assert submitted.data["status"] == "pending"

    queue_rows = web_api.admin_list_profile_pack_submissions(role="admin", status="pending")
    assert queue_rows.ok is True
    assert len(queue_rows.data["submissions"]) == 1

    decided = web_api.admin_decide_profile_pack_submission(
        role="admin",
        submission_id=submitted.data["submission_id"],
        decision="approve",
        review_note="Approved for community use.",
        review_labels=["risk_low", "approved"],
    )
    assert decided.ok is True
    assert decided.data["status"] == "approved"

    catalog = web_api.list_profile_pack_catalog(pack_query="community-safe")
    assert catalog.ok is True
    assert len(catalog.data["packs"]) == 1

    detail = web_api.get_profile_pack_catalog_detail(pack_id="profile/community-safe")
    assert detail.ok is True
    assert detail.data["pack_id"] == "profile/community-safe"

    compared = web_api.compare_profile_pack_catalog(
        pack_id="profile/community-safe",
        selected_sections=["plugins"],
    )
    assert compared.ok is True
    assert compared.data["status"] == "compare_ready"
    assert compared.data["pack_id"] == "profile/community-safe"
    row = compared.data["diff"]["sections"][0]
    assert row["file_path"] == "sections/plugins.json"
    assert isinstance(row["before_preview"], list)
    assert isinstance(row["after_preview"], list)
    assert isinstance(row["diff_preview"], list)


def test_web_api_submit_profile_pack_replace_existing_retires_previous_pending_submission(tmp_path):
    _, web_api = build_interfaces(tmp_path)
    exported = web_api.admin_export_profile_pack(
        role="admin",
        pack_id="profile/community-web-replace",
        version="1.0.0",
        redaction_mode="exclude_secrets",
    )
    assert exported.ok is True

    first = web_api.submit_profile_pack(
        user_id="member-1",
        artifact_id=exported.data["artifact_id"],
    )
    assert first.ok is True
    assert first.data["status"] == "pending"

    second = web_api.submit_profile_pack(
        user_id="member-1",
        artifact_id=exported.data["artifact_id"],
        submit_options={"replace_existing": True},
    )
    assert second.ok is True
    assert second.data["status"] == "pending"
    assert second.data["replaced_submission_count"] == 1
    assert second.data["replaced_submission_ids"] == [first.data["submission_id"]]

    replaced = web_api.member_get_profile_pack_submission_detail(
        user_id="member-1",
        submission_id=first.data["submission_id"],
    )
    assert replaced.ok is True
    assert replaced.data["status"] == "replaced"


def test_web_api_submit_profile_pack_idempotency_key_conflict_maps_to_409(tmp_path):
    _, web_api = build_interfaces(tmp_path)
    exported_first = web_api.admin_export_profile_pack(
        role="admin",
        pack_id="profile/community-web-idempotent-a",
        version="1.0.0",
        redaction_mode="exclude_secrets",
    )
    exported_second = web_api.admin_export_profile_pack(
        role="admin",
        pack_id="profile/community-web-idempotent-b",
        version="1.0.0",
        redaction_mode="exclude_secrets",
    )
    assert exported_first.ok is True
    assert exported_second.ok is True

    first = web_api.submit_profile_pack(
        user_id="member-1",
        artifact_id=exported_first.data["artifact_id"],
        submit_options={"idempotency_key": "profile-pack-web-key-1"},
    )
    assert first.ok is True

    conflict = web_api.submit_profile_pack(
        user_id="member-1",
        artifact_id=exported_second.data["artifact_id"],
        submit_options={"idempotency_key": "profile-pack-web-key-1"},
    )
    assert conflict.ok is False
    assert conflict.status_code == 409
    assert conflict.error_code == "idempotency_key_conflict"


def test_web_api_member_profile_pack_submission_views_are_owner_scoped(tmp_path):
    _, web_api = build_interfaces(tmp_path)
    exported = web_api.admin_export_profile_pack(
        role="admin",
        pack_id="profile/community-web-owner-scope",
        version="1.0.0",
        redaction_mode="exclude_secrets",
    )
    assert exported.ok is True

    own = web_api.submit_profile_pack(
        user_id="member-1",
        artifact_id=exported.data["artifact_id"],
    )
    other = web_api.submit_profile_pack(
        user_id="member-2",
        artifact_id=exported.data["artifact_id"],
    )
    assert own.ok is True
    assert other.ok is True

    listed = web_api.member_list_profile_pack_submissions(user_id="member-1")
    assert listed.ok is True
    assert listed.data["user_id"] == "member-1"
    assert len(listed.data["submissions"]) == 1
    assert listed.data["submissions"][0]["submission_id"] == own.data["submission_id"]

    own_detail = web_api.member_get_profile_pack_submission_detail(
        user_id="member-1",
        submission_id=own.data["submission_id"],
    )
    assert own_detail.ok is True
    assert own_detail.data["submission_id"] == own.data["submission_id"]

    own_export = web_api.member_get_profile_pack_submission_export(
        user_id="member-1",
        submission_id=own.data["submission_id"],
    )
    assert own_export.ok is True
    assert own_export.data["submission_id"] == own.data["submission_id"]
    assert own_export.data["artifact_id"] == own_detail.data["artifact_id"]

    denied = web_api.member_get_profile_pack_submission_detail(
        user_id="member-1",
        submission_id=other.data["submission_id"],
    )
    assert denied.ok is False
    assert denied.status_code == 403
    assert denied.error_code == "permission_denied"

    denied_export = web_api.member_get_profile_pack_submission_export(
        user_id="member-1",
        submission_id=other.data["submission_id"],
    )
    assert denied_export.ok is False
    assert denied_export.status_code == 403
    assert denied_export.error_code == "permission_denied"

    missing_export = web_api.member_get_profile_pack_submission_export(
        user_id="member-1",
        submission_id="",
    )
    assert missing_export.ok is False
    assert missing_export.status_code == 400
    assert missing_export.error_code == "submission_id_required"


def test_api_member_profile_pack_import_drafts_are_owner_scoped(tmp_path):
    api, web_api = build_interfaces(tmp_path)
    exported = api.admin_export_profile_pack(
        role="admin",
        pack_id="profile/member-import-draft",
        version="1.0.0",
        redaction_mode="exclude_secrets",
    )
    assert exported["artifact_id"]
    archive_bytes = Path(exported["path"]).read_bytes()
    archive_b64 = base64.b64encode(archive_bytes).decode("ascii")

    imported = api.member_import_profile_pack(
        user_id="member-1",
        filename=exported["filename"],
        content_base64=archive_b64,
    )
    assert imported["user_id"] == "member-1"
    assert imported["source_artifact_id"]

    listed = api.member_list_profile_pack_imports(user_id="member-1", limit=20)
    assert listed["user_id"] == "member-1"
    assert len(listed["imports"]) == 1
    assert listed["imports"][0]["import_id"] == imported["import_id"]

    denied_submit = api.submit_profile_pack(
        user_id="member-2",
        artifact_id=imported["source_artifact_id"],
    )
    assert denied_submit["error"] == "permission_denied"

    web_imported = web_api.member_import_profile_pack(
        user_id="member-2",
        filename=exported["filename"],
        content_base64=archive_b64,
    )
    assert web_imported.ok is True
    assert web_imported.data["user_id"] == "member-2"

    web_listed = web_api.member_list_profile_pack_imports(user_id="member-2", limit=20)
    assert web_listed.ok is True
    assert web_listed.data["user_id"] == "member-2"
    assert len(web_listed.data["imports"]) == 1
    assert web_listed.data["imports"][0]["import_id"] == web_imported.data["import_id"]

    web_denied = web_api.submit_profile_pack(
        user_id="member-1",
        artifact_id=web_imported.data["source_artifact_id"],
    )
    assert web_denied.ok is False
    assert web_denied.status_code == 403
    assert web_denied.error_code == "permission_denied"


def test_api_member_profile_pack_submission_withdraw_is_owner_scoped_and_pending_only(tmp_path):
    api, web_api = build_interfaces(tmp_path)
    exported = api.admin_export_profile_pack(
        role="admin",
        pack_id="profile/member-withdraw",
        version="1.0.0",
        redaction_mode="exclude_secrets",
    )

    submitted = api.submit_profile_pack(
        user_id="member-1",
        artifact_id=exported["artifact_id"],
    )
    submission_id = submitted["submission_id"]
    assert submitted["status"] == "pending"

    denied = api.member_withdraw_profile_pack_submission(
        user_id="member-2",
        submission_id=submission_id,
    )
    assert denied["error"] == "permission_denied"

    withdrawn = api.member_withdraw_profile_pack_submission(
        user_id="member-1",
        submission_id=submission_id,
    )
    assert withdrawn["status"] == "withdrawn"

    withdrawn_again = api.member_withdraw_profile_pack_submission(
        user_id="member-1",
        submission_id=submission_id,
    )
    assert withdrawn_again["status"] == "withdrawn"

    pending_rows = api.member_list_profile_pack_submissions(
        user_id="member-1",
        status="pending",
    )
    assert pending_rows["submissions"] == []

    withdrawn_rows = api.member_list_profile_pack_submissions(
        user_id="member-1",
        status="withdrawn",
    )
    assert [item["submission_id"] for item in withdrawn_rows["submissions"]] == [submission_id]

    exported_approved = api.admin_export_profile_pack(
        role="admin",
        pack_id="profile/member-withdraw-approved",
        version="1.0.0",
        redaction_mode="exclude_secrets",
    )
    approved = api.submit_profile_pack(
        user_id="member-1",
        artifact_id=exported_approved["artifact_id"],
    )
    decided = api.admin_decide_profile_pack_submission(
        role="admin",
        reviewer_id="admin",
        submission_id=approved["submission_id"],
        decision="approve",
        review_labels=["approved"],
    )
    assert decided["status"] == "approved"

    invalid_state = web_api.member_withdraw_profile_pack_submission(
        user_id="member-1",
        submission_id=approved["submission_id"],
    )
    assert invalid_state.ok is False
    assert invalid_state.status_code == 409
    assert invalid_state.error_code == "profile_pack_submission_state_invalid"

    audit = api.admin_list_audit(role="admin", limit=20)
    assert any(item["action"] == "profile_pack.submission_withdrawn" for item in audit["events"])


def test_api_member_profile_pack_import_rejects_non_sharelife_archive(tmp_path):
    api, web_api = build_interfaces(tmp_path)
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("astrbot-config.json", json.dumps({"provider": "openai"}))
    archive_b64 = base64.b64encode(archive.getvalue()).decode("ascii")

    imported = api.member_import_profile_pack(
        user_id="member-1",
        filename="astrbot-export.zip",
        content_base64=archive_b64,
    )
    assert imported["error"] == "invalid_profile_pack_payload"

    web_imported = web_api.member_import_profile_pack(
        user_id="member-1",
        filename="astrbot-export.zip",
        content_base64=archive_b64,
    )
    assert web_imported.ok is False
    assert web_imported.status_code == 400
    assert web_imported.error_code == "invalid_profile_pack_payload"


def test_api_member_profile_pack_import_converts_astrbot_backup_zip(tmp_path):
    api, web_api = build_interfaces(tmp_path)
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            "manifest.json",
            json.dumps(
                {
                    "manifest_version": 1,
                    "astrbot_version": "4.16.0",
                    "backup_time": "2026-04-07T12:00:00Z",
                },
                ensure_ascii=False,
                indent=2,
            ),
        )
        zf.writestr(
            "config/cmd_config.json",
            json.dumps(
                {
                    "provider": [
                        {
                            "id": "test-openai",
                            "type": "openai_chat_completion",
                            "model": "gpt-4o-mini",
                            "key": ["test-key"],
                        }
                    ],
                    "provider_settings": {"websearch_tavily_key": ["tvly-secret"]},
                    "dashboard": {"password": "dashboard-secret", "jwt_secret": "jwt-secret"},
                    "admins_id": ["owner"],
                    "plugin_set": ["*"],
                    "timezone": "Asia/Shanghai",
                },
                ensure_ascii=False,
                indent=2,
            ),
        )
    archive_b64 = base64.b64encode(archive.getvalue()).decode("ascii")

    imported = api.member_import_profile_pack(
        user_id="member-1",
        filename="astrbot-backup.zip",
        content_base64=archive_b64,
    )
    assert imported["compatibility"] == "degraded"
    assert "astrbot_raw_import_converted" in imported["compatibility_issues"]
    assert imported["source_artifact_id"]

    submission = api.submit_profile_pack(
        user_id="member-1",
        artifact_id=imported["source_artifact_id"],
    )
    assert submission["status"] == "pending"
    assert submission["compatibility"] == "degraded"

    web_imported = web_api.member_import_profile_pack(
        user_id="member-1",
        filename="astrbot-backup.zip",
        content_base64=archive_b64,
    )
    assert web_imported.ok is True
    assert web_imported.data["compatibility"] == "degraded"
    assert "astrbot_raw_import_converted" in web_imported.data["compatibility_issues"]


def test_api_member_profile_pack_import_detects_local_astrbot_config(tmp_path, monkeypatch):
    api, web_api = build_interfaces(tmp_path)
    local_config = tmp_path / "astrbot-data" / "cmd_config.json"
    local_config.parent.mkdir(parents=True, exist_ok=True)
    local_config.write_text(
        json.dumps(
            {
                "provider": [
                    {
                        "id": "test-openai",
                        "type": "openai_chat_completion",
                        "model": "gpt-4o-mini",
                        "key": ["test-key"],
                    }
                ],
                "provider_settings": {"websearch_tavily_key": ["tvly-secret"]},
                "dashboard": {"password": "dashboard-secret"},
                "admins_id": ["owner"],
                "plugin_set": ["sharelife"],
                "timezone": "Asia/Shanghai",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("SHARELIFE_ASTRBOT_CONFIG_PATH", str(local_config))

    imported = api.member_import_local_astrbot_config(user_id="member-1")
    assert imported["compatibility"] == "degraded"
    assert "astrbot_raw_import_converted" in imported["compatibility_issues"]
    assert "astrbot_raw_import_converted" in imported["compatibility_issue_groups"]["conversion"]
    assert any(
        item["code"] == "astrbot_raw_import_converted"
        for item in imported["compatibility_issue_details"]
    )
    assert imported["source_artifact_id"]
    assert imported["refresh_replaced_count"] == 0
    assert imported["refresh_replaced_import_ids"] == []

    web_imported = web_api.member_import_local_astrbot_config(user_id="member-1")
    assert web_imported.ok is True
    assert web_imported.data["compatibility"] == "degraded"
    assert "astrbot_raw_import_converted" in web_imported.data["compatibility_issues"]
    assert "astrbot_raw_import_converted" in web_imported.data["compatibility_issue_groups"]["conversion"]
    assert any(
        item["code"] == "astrbot_raw_import_converted"
        for item in web_imported.data["compatibility_issue_details"]
    )
    assert web_imported.data["probe"]["detected"] is True
    assert web_imported.data["probe"]["matched_source"] == "config_path_file"
    assert web_imported.data["refresh_replaced_count"] == 1
    assert web_imported.data["refresh_replaced_import_ids"] == [imported["import_id"]]


def test_api_member_local_astrbot_probe_returns_safe_detection_metadata(tmp_path, monkeypatch):
    api, web_api = build_interfaces(tmp_path)
    local_config = tmp_path / "astrbot-data" / "cmd_config.json"
    local_config.parent.mkdir(parents=True, exist_ok=True)
    local_config.write_text("{}", encoding="utf-8")
    monkeypatch.setenv("SHARELIFE_ASTRBOT_CONFIG_PATH", str(local_config))
    monkeypatch.delenv("SHARELIFE_ASTRBOT_SEARCH_ROOTS", raising=False)
    monkeypatch.delenv("SHARELIFE_ASTRBOT_HOME", raising=False)

    probe = api.member_probe_local_astrbot_config(user_id="member-1")
    assert probe["detected"] is True
    assert probe["filename"] == "cmd_config.json"
    assert probe["matched_source"] == "config_path_file"
    assert probe["checked_candidate_count"] >= 1
    assert probe["path_list_separator"] == os.pathsep
    assert "SHARELIFE_ASTRBOT_CONFIG_PATH" in probe["hint_env_keys"]
    assert str(local_config) not in json.dumps(probe, ensure_ascii=False)

    web_probe = web_api.member_probe_local_astrbot_config(user_id="member-1")
    assert web_probe.ok is True
    assert web_probe.data["detected"] is True
    assert web_probe.data["matched_source"] == "config_path_file"


def test_api_member_local_astrbot_import_not_found_returns_probe_payload(tmp_path, monkeypatch):
    api, web_api = build_interfaces(tmp_path)
    probe_payload = {
        "detected": False,
        "filename": "",
        "matched_source": "",
        "checked_candidate_count": 7,
        "hint_env_keys": [
            "SHARELIFE_ASTRBOT_CONFIG_PATH",
            "SHARELIFE_ASTRBOT_SEARCH_ROOTS",
            "SHARELIFE_ASTRBOT_HOME",
        ],
        "path_list_separator": os.pathsep,
        "default_root_count": 16,
    }
    monkeypatch.setattr(
        SharelifeApiV1,
        "_probe_local_astrbot_config_path",
        classmethod(lambda cls: (None, dict(probe_payload))),
    )

    imported = api.member_import_local_astrbot_config(user_id="member-1")
    assert imported["error"] == "astrbot_local_config_not_found"
    assert imported["probe"]["detected"] is False
    assert imported["probe"]["filename"] == ""
    assert imported["probe"]["checked_candidate_count"] == 7
    assert imported["probe"]["path_list_separator"] == os.pathsep

    web_imported = web_api.member_import_local_astrbot_config(user_id="member-1")
    assert web_imported.ok is False
    assert web_imported.error_code == "astrbot_local_config_not_found"
    assert web_imported.data["probe"]["detected"] is False


def test_api_detect_local_astrbot_config_path_accepts_directory_hint(tmp_path, monkeypatch):
    local_root = tmp_path / "astrbot-home"
    local_config = local_root / "data" / "cmd_config.json"
    local_config.parent.mkdir(parents=True, exist_ok=True)
    local_config.write_text("{}", encoding="utf-8")

    monkeypatch.setenv("SHARELIFE_ASTRBOT_CONFIG_PATH", str(local_root))
    monkeypatch.delenv("SHARELIFE_ASTRBOT_SEARCH_ROOTS", raising=False)
    monkeypatch.delenv("SHARELIFE_ASTRBOT_HOME", raising=False)

    detected = SharelifeApiV1._detect_local_astrbot_config_path()
    assert detected == local_config.resolve()


def test_api_detect_local_astrbot_config_path_supports_path_list_hint(tmp_path, monkeypatch):
    local_root = tmp_path / "astrbot-home"
    local_config = local_root / "config" / "cmd_config.json"
    local_config.parent.mkdir(parents=True, exist_ok=True)
    local_config.write_text("{}", encoding="utf-8")

    missing_file = tmp_path / "missing" / "cmd_config.json"
    monkeypatch.setenv(
        "SHARELIFE_ASTRBOT_CONFIG_PATH",
        f"{missing_file}{os.pathsep}{local_root}",
    )
    monkeypatch.delenv("SHARELIFE_ASTRBOT_SEARCH_ROOTS", raising=False)
    monkeypatch.delenv("SHARELIFE_ASTRBOT_HOME", raising=False)

    detected = SharelifeApiV1._detect_local_astrbot_config_path()
    assert detected == local_config.resolve()


def test_api_detect_local_astrbot_config_path_honors_search_roots_env(tmp_path, monkeypatch):
    missing_root = tmp_path / "root-a"
    found_root = tmp_path / "root-b"
    local_config = found_root / "data" / "cmd_config.json"
    local_config.parent.mkdir(parents=True, exist_ok=True)
    local_config.write_text("{}", encoding="utf-8")

    monkeypatch.delenv("SHARELIFE_ASTRBOT_CONFIG_PATH", raising=False)
    monkeypatch.setenv(
        "SHARELIFE_ASTRBOT_SEARCH_ROOTS",
        f"{missing_root}{os.pathsep}{found_root}",
    )
    monkeypatch.delenv("SHARELIFE_ASTRBOT_HOME", raising=False)

    detected = SharelifeApiV1._detect_local_astrbot_config_path()
    assert detected == local_config.resolve()


def test_api_member_local_astrbot_import_refreshes_existing_draft_and_supports_delete(tmp_path, monkeypatch):
    api, web_api = build_interfaces(tmp_path)
    local_config = tmp_path / "astrbot-data" / "cmd_config.json"
    local_config.parent.mkdir(parents=True, exist_ok=True)
    local_config.write_text(
        json.dumps(
            {
                "provider": [
                    {
                        "id": "test-openai",
                        "type": "openai_chat_completion",
                        "model": "gpt-4o-mini",
                        "key": ["test-key"],
                    }
                ],
                "provider_settings": {"default_personality": "alpha"},
                "plugin_set": ["sharelife"],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("SHARELIFE_ASTRBOT_CONFIG_PATH", str(local_config))

    first = api.member_import_local_astrbot_config(user_id="member-1")
    assert first["refresh_replaced_count"] == 0
    assert first["refresh_replaced_import_ids"] == []
    listed_first = api.member_list_profile_pack_imports(user_id="member-1", limit=10)
    assert len(listed_first["imports"]) == 1
    assert listed_first["imports"][0]["import_id"] == first["import_id"]
    assert listed_first["imports"][0]["import_origin"] == "local_astrbot_detected"
    assert listed_first["imports"][0]["delete_allowed"] is True
    assert listed_first["imports"][0]["import_summary"]["default_personality"] == "alpha"
    assert "astrbot_raw_import_converted" in listed_first["imports"][0]["compatibility_issue_groups"]["conversion"]
    assert any(
        item["code"] == "astrbot_raw_import_converted"
        for item in listed_first["imports"][0]["compatibility_issue_details"]
    )
    if api.profile_pack_service is not None and hasattr(api.profile_pack_service.clock, "shift"):
        api.profile_pack_service.clock.shift(seconds=1)

    local_config.write_text(
        json.dumps(
            {
                "provider": [
                    {
                        "id": "test-openai",
                        "type": "openai_chat_completion",
                        "model": "gpt-4o-mini",
                        "key": ["test-key"],
                    }
                ],
                "provider_settings": {"default_personality": "beta"},
                "plugin_set": ["sharelife", "community_tools"],
                "subagent_orchestrator": {
                    "agents": [{"name": "planner_prometheus", "enabled": True}],
                },
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    second = api.member_import_local_astrbot_config(user_id="member-1")
    assert second["refresh_replaced_count"] == 1
    assert second["refresh_replaced_import_ids"] == [first["import_id"]]
    listed_second = api.member_list_profile_pack_imports(user_id="member-1", limit=10)
    assert len(listed_second["imports"]) == 1
    assert listed_second["imports"][0]["import_id"] == second["import_id"]
    assert listed_second["imports"][0]["import_summary"]["default_personality"] == "beta"
    assert listed_second["imports"][0]["import_summary"]["subagent_count"] == 1
    assert "astrbot_raw_import_converted" in listed_second["imports"][0]["compatibility_issue_groups"]["conversion"]
    assert any(
        item["code"] == "astrbot_raw_import_converted"
        for item in listed_second["imports"][0]["compatibility_issue_details"]
    )

    deleted = api.member_delete_profile_pack_import(
        user_id="member-1",
        import_id=second["import_id"],
    )
    assert deleted["deleted"] is True
    assert deleted["import_id"] == second["import_id"]
    assert api.member_list_profile_pack_imports(user_id="member-1", limit=10)["imports"] == []

    web_deleted = web_api.member_delete_profile_pack_import(
        user_id="member-1",
        import_id=second["import_id"],
    )
    assert web_deleted.ok is False
    assert web_deleted.status_code == 404
    assert web_deleted.error_code == "profile_import_not_found"


def test_api_member_profile_pack_import_detects_local_astrbot_config_with_utf8_bom(tmp_path, monkeypatch):
    api, _web_api = build_interfaces(tmp_path)
    local_config = tmp_path / "astrbot-data" / "cmd_config.json"
    local_config.parent.mkdir(parents=True, exist_ok=True)
    local_config.write_text(
        json.dumps(
            {
                "provider": [
                    {
                        "id": "test-openai",
                        "type": "openai_chat_completion",
                        "model": "gpt-4o-mini",
                        "key": ["test-key"],
                    }
                ],
                "provider_settings": {"websearch_tavily_key": ["tvly-secret"]},
                "dashboard": {"password": "dashboard-secret"},
                "admins_id": ["owner"],
                "plugin_set": ["sharelife"],
                "timezone": "Asia/Shanghai",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8-sig",
    )
    monkeypatch.setenv("SHARELIFE_ASTRBOT_CONFIG_PATH", str(local_config))

    imported = api.member_import_local_astrbot_config(user_id="member-1")
    assert imported["compatibility"] == "degraded"
    assert "astrbot_raw_import_converted" in imported["compatibility_issues"]
    assert imported["source_artifact_id"]


def test_web_api_profile_pack_decision_exposes_public_market_publish_payload(tmp_path):
    public_market_root = tmp_path / "public-root"
    _, web_api = build_interfaces(
        tmp_path / "workspace",
        auto_publish_profile_pack_approve=True,
        public_market_root=public_market_root,
    )
    exported = web_api.admin_export_profile_pack(
        role="admin",
        pack_id="profile/community-webapi-autopublish",
        version="1.0.0",
        redaction_mode="exclude_secrets",
    )
    assert exported.ok is True

    submitted = web_api.submit_profile_pack(
        user_id="member-1",
        artifact_id=exported.data["artifact_id"],
    )
    assert submitted.ok is True

    decided = web_api.admin_decide_profile_pack_submission(
        role="admin",
        submission_id=submitted.data["submission_id"],
        decision="approve",
        review_labels=["risk_low", "approved"],
    )
    assert decided.ok is True
    publish = decided.data.get("public_market_publish", {})
    assert publish.get("status") == "succeeded"
    assert publish.get("pipeline", {}).get("trace_id")
    assert publish.get("backup", {}).get("status") == "queued"
    assert Path(str(publish.get("entry_path", ""))).exists()
    assert Path(str(publish.get("package_path", ""))).exists()


def test_web_api_profile_pack_featured_route(tmp_path):
    _, web_api = build_interfaces(tmp_path)
    exported = web_api.admin_export_profile_pack(
        role="admin",
        pack_id="profile/community-featured",
        version="1.0.0",
        redaction_mode="exclude_secrets",
    )
    submitted = web_api.submit_profile_pack(
        user_id="member-1",
        artifact_id=exported.data["artifact_id"],
    )
    web_api.admin_decide_profile_pack_submission(
        role="admin",
        submission_id=submitted.data["submission_id"],
        decision="approve",
    )

    updated = web_api.admin_set_profile_pack_featured(
        role="admin",
        pack_id="profile/community-featured",
        featured=True,
        note="featured test note",
    )
    assert updated.ok is True
    assert updated.data["featured"] is True
    assert updated.data["featured_note"] == "featured test note"

    filtered = web_api.list_profile_pack_catalog(pack_query="community-featured", featured="true")
    assert filtered.ok is True
    assert len(filtered.data["packs"]) == 1


def test_web_api_profile_pack_catalog_insights_route(tmp_path):
    _, web_api = build_interfaces(tmp_path)
    exported = web_api.admin_export_profile_pack(
        role="admin",
        pack_id="profile/community-featured-insights",
        version="1.0.0",
        redaction_mode="exclude_secrets",
    )
    submitted = web_api.submit_profile_pack(
        user_id="member-1",
        artifact_id=exported.data["artifact_id"],
    )
    web_api.admin_decide_profile_pack_submission(
        role="admin",
        submission_id=submitted.data["submission_id"],
        decision="approve",
        review_labels=["risk_low", "approved"],
    )
    web_api.admin_set_profile_pack_featured(
        role="admin",
        pack_id="profile/community-featured-insights",
        featured=True,
        note="featured for insights route",
    )

    insights = web_api.list_profile_pack_catalog_insights(pack_query="community-featured-insights")
    assert insights.ok is True
    assert insights.data["metrics"]["total"] == 1
    assert insights.data["metrics"]["featured"] == 1
    assert insights.data["featured"]["pack_id"] == "profile/community-featured-insights"
    assert len(insights.data["trending"]) == 1
    assert insights.data["trending"][0]["trend_score"] >= 0


def test_web_api_profile_pack_plugin_install_confirmation_flow(tmp_path):
    _, export_web_api = build_interfaces(tmp_path / "exporter")
    _, import_web_api = build_interfaces(tmp_path / "importer")

    export_web_api.api.profile_pack_service.runtime.state["plugins"]["community_tools"] = {
        "enabled": True,
        "version": "1.2.3",
        "source": "https://github.com/acme/community-tools",
        "install_cmd": "pip install astrbot-plugin-community-tools==1.2.3",
    }
    exported = export_web_api.admin_export_profile_pack(
        role="admin",
        pack_id="extension/community-tools",
        version="1.0.0",
        pack_type="extension_pack",
        redaction_mode="exclude_secrets",
    )
    assert exported.ok is True

    imported = import_web_api.admin_import_profile_pack(
        role="admin",
        filename=exported.data["filename"],
        content_base64=base64.b64encode(Path(exported.data["path"]).read_bytes()).decode("ascii"),
    )
    assert imported.ok is True
    import_id = imported.data["import_id"]

    install_plan = import_web_api.admin_profile_pack_plugin_install_plan(
        role="admin",
        import_id=import_id,
    )
    assert install_plan.ok is True
    assert install_plan.data["status"] == "confirmation_required"
    assert install_plan.data["required_plugins"] == ["community_tools"]

    blocked = import_web_api.admin_profile_pack_dryrun(
        role="admin",
        import_id=import_id,
        plan_id="plan-extension-community-tools",
        selected_sections=["plugins"],
    )
    assert blocked.ok is False
    assert blocked.error_code == "profile_pack_plugin_install_confirm_required"

    confirmed = import_web_api.admin_profile_pack_confirm_plugin_install(
        role="admin",
        import_id=import_id,
        plugin_ids=["community_tools"],
    )
    assert confirmed.ok is True
    assert confirmed.data["status"] == "confirmed"

    disabled_execute = import_web_api.admin_profile_pack_execute_plugin_install(
        role="admin",
        import_id=import_id,
        plugin_ids=["community_tools"],
    )
    assert disabled_execute.ok is False
    assert disabled_execute.error_code == "profile_pack_plugin_install_exec_disabled"

    plugin_install_service = import_web_api.api.profile_pack_service.plugin_install_service
    plugin_install_service.enabled = True
    plugin_install_service.command_runner = lambda command, timeout_seconds: {
        "returncode": 0,
        "stdout": "ok",
        "stderr": "",
        "timed_out": False,
    }

    executed = import_web_api.admin_profile_pack_execute_plugin_install(
        role="admin",
        import_id=import_id,
        plugin_ids=["community_tools"],
    )
    assert executed.ok is True
    assert executed.data["status"] == "executed"
    assert executed.data["execution"]["result"]["installed_count"] == 1

    refreshed_plan = import_web_api.admin_profile_pack_plugin_install_plan(
        role="admin",
        import_id=import_id,
    )
    assert refreshed_plan.ok is True
    assert refreshed_plan.data["latest_execution"]["status"] == "executed"

    dryrun = import_web_api.admin_profile_pack_dryrun(
        role="admin",
        import_id=import_id,
        plan_id="plan-extension-community-tools",
        selected_sections=["plugins"],
    )
    assert dryrun.ok is True
    assert dryrun.data["status"] == "dryrun_ready"
