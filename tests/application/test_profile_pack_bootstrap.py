from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sharelife.application.services_apply import ApplyService
from sharelife.application.services_profile_pack import ProfilePackService
from sharelife.application.services_profile_pack_bootstrap import ProfilePackBootstrapService
from sharelife.infrastructure.runtime_bridge import InMemoryRuntimeBridge


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


def build_service(tmp_path):
    runtime = InMemoryRuntimeBridge(initial_state=runtime_state_fixture())
    apply_service = ApplyService(runtime=runtime)
    service = ProfilePackService(
        runtime=runtime,
        apply_service=apply_service,
        output_root=tmp_path,
        clock=FrozenClock(datetime(2026, 3, 31, 9, 0, tzinfo=UTC)),
        astrbot_version="4.16.0",
        plugin_version="0.3.0",
    )
    return service


def test_profile_pack_bootstrap_seeds_official_reference_pack(tmp_path):
    service = build_service(tmp_path)
    bootstrap = ProfilePackBootstrapService(profile_pack_service=service)

    result = bootstrap.sync()

    assert result["seeded"] >= 2
    published = service.get_published_pack("profile/official-starter")
    assert published is not None
    assert published.version == "1.0.1"
    assert published.featured is True
    assert published.source_submission_id.startswith("official:")
    assert "official_profile_pack" in published.review_labels
    assert published.risk_level == "low"
    assert "risk_low" in published.review_labels
    safe_reference = service.get_published_pack("profile/official-safe-reference")
    assert safe_reference is not None
    assert safe_reference.source_submission_id.startswith("official:")
    assert safe_reference.risk_level == "low"
    assert "risk_low" in safe_reference.review_labels


def test_profile_pack_bootstrap_does_not_override_user_published_pack(tmp_path):
    service = build_service(tmp_path)
    bootstrap = ProfilePackBootstrapService(profile_pack_service=service)
    artifact = service.export_bot_profile_pack(
        pack_id="profile/official-starter",
        version="9.9.9",
        redaction_mode="exclude_secrets",
    )
    submitted = service.submit_export_artifact(
        user_id="member-1",
        artifact_id=artifact.artifact_id,
    )
    service.decide_submission(
        submission_id=submitted.submission_id,
        reviewer_id="admin-1",
        decision="approve",
    )

    result = bootstrap.sync()

    assert result["seeded"] >= 1
    assert result["skipped"] >= 1
    published = service.get_published_pack("profile/official-starter")
    assert published is not None
    assert published.version == "9.9.9"
    assert not str(published.source_submission_id).startswith("official:")
    safe_reference = service.get_published_pack("profile/official-safe-reference")
    assert safe_reference is not None
    assert str(safe_reference.source_submission_id).startswith("official:")


def test_profile_pack_bootstrap_repairs_official_pack_when_same_version_is_not_low_risk(tmp_path):
    service = build_service(tmp_path)
    bootstrap = ProfilePackBootstrapService(profile_pack_service=service)

    first = bootstrap.sync()
    assert first["seeded"] >= 2
    published = service.get_published_pack("profile/official-safe-reference")
    assert published is not None
    published.risk_level = "medium"
    published.review_labels = ["official_profile_pack", "risk_medium"]

    second = bootstrap.sync()
    assert second["seeded"] >= 1
    repaired = service.get_published_pack("profile/official-safe-reference")
    assert repaired is not None
    assert repaired.risk_level == "low"
    assert "risk_low" in repaired.review_labels
