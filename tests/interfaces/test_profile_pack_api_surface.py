from __future__ import annotations

import base64
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from sharelife.application.services_apply import ApplyService
from sharelife.application.services_audit import AuditService
from sharelife.application.services_market import MarketService
from sharelife.application.services_package import PackageService
from sharelife.application.services_preferences import PreferenceService
from sharelife.application.services_profile_pack import ProfilePackService
from sharelife.application.services_queue import RetryQueueService
from sharelife.application.services_trial import TrialService
from sharelife.application.services_trial_request import TrialRequestService
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
    package = PackageService(market_service=market, output_root=tmp_path / "packages", clock=clock)
    apply_service = ApplyService(runtime=runtime)
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
        },
    )

    assert submitted["submit_options"] == {
        "pack_type": "extension_pack",
        "selected_sections": ["plugins", "providers"],
        "redaction_mode": "include_provider_no_key",
    }


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

    snapshot = public_market_root / "market" / "catalog.snapshot.json"
    assert snapshot.exists()
    snapshot_rows = json.loads(snapshot.read_text(encoding="utf-8"))["rows"]
    assert any(item.get("pack_id") == "profile/community-autopublish" for item in snapshot_rows)


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
