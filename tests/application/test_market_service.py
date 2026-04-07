from datetime import UTC, datetime, timedelta

from sharelife.application.services_market import MarketService
from sharelife.infrastructure.json_state_store import JsonStateStore
from sharelife.infrastructure.sqlite_state_store import SqliteStateStore


class FrozenClock:
    def __init__(self, start: datetime):
        self.current = start

    def utcnow(self) -> datetime:
        return self.current

    def shift(self, **kwargs) -> None:
        self.current = self.current + timedelta(**kwargs)


def test_submission_starts_pending():
    service = MarketService(clock=FrozenClock(datetime(2026, 3, 25, 10, 0, tzinfo=UTC)))

    sub = service.submit_template(user_id="u1", template_id="community/basic", version="1.0.0")

    assert sub.status == "pending"
    assert sub.user_id == "u1"


def test_admin_approve_publishes_template():
    service = MarketService(clock=FrozenClock(datetime(2026, 3, 25, 10, 0, tzinfo=UTC)))
    sub = service.submit_template(user_id="u1", template_id="community/basic", version="1.0.0")

    service.decide_submission(
        submission_id=sub.id,
        reviewer_id="admin-1",
        decision="approve",
    )

    published = service.get_published_template(template_id="community/basic")
    assert published is not None
    assert published.version == "1.0.0"


def test_replace_pending_submissions_marks_previous_rows_as_replaced():
    service = MarketService(clock=FrozenClock(datetime(2026, 3, 25, 10, 0, tzinfo=UTC)))
    first = service.submit_template(user_id="u1", template_id="community/basic", version="1.0.0")
    service.submit_template(user_id="u2", template_id="community/basic", version="1.0.0")
    service.submit_template(user_id="u1", template_id="community/other", version="1.0.0")

    replaced = service.replace_pending_submissions(user_id="u1", template_id="community/basic")
    assert replaced == [first.id]
    assert service.get_submission(first.id).status == "replaced"

    # repeated replacement should be idempotent after status transition
    replaced_again = service.replace_pending_submissions(user_id="u1", template_id="community/basic")
    assert replaced_again == []


def test_prompt_bundle_is_generated_for_published_template():
    service = MarketService(clock=FrozenClock(datetime(2026, 3, 25, 10, 0, tzinfo=UTC)))
    sub = service.submit_template(user_id="u1", template_id="community/basic", version="1.0.0")
    service.decide_submission(
        submission_id=sub.id,
        reviewer_id="admin-1",
        decision="approve",
    )

    bundle = service.build_prompt_bundle(template_id="community/basic")

    assert bundle["template_id"] == "community/basic"
    assert "community/basic" in bundle["prompt"]


def test_market_state_persists_across_service_restart(tmp_path):
    state_file = tmp_path / "market-state.json"
    store = JsonStateStore(state_file)

    service_a = MarketService(
        clock=FrozenClock(datetime(2026, 3, 25, 10, 0, tzinfo=UTC)),
        state_store=store,
    )
    sub = service_a.submit_template(user_id="u1", template_id="community/basic", version="1.0.0")
    service_a.decide_submission(submission_id=sub.id, reviewer_id="admin-1", decision="approve")

    service_b = MarketService(
        clock=FrozenClock(datetime(2026, 3, 25, 11, 0, tzinfo=UTC)),
        state_store=store,
    )

    loaded = service_b.get_published_template("community/basic")
    assert loaded is not None
    assert loaded.version == "1.0.0"


def test_admin_can_update_submission_review_metadata_and_sync_published_template():
    service = MarketService(clock=FrozenClock(datetime(2026, 3, 25, 10, 0, tzinfo=UTC)))
    sub = service.submit_template(
        user_id="u1",
        template_id="community/basic",
        version="1.0.0",
        review_labels=["risk_high", "prompt_injection_detected"],
    )

    reviewed = service.update_submission_review(
        submission_id=sub.id,
        reviewer_id="admin-1",
        review_note="Needs manual sandbox review but can proceed.",
        review_labels=["risk_high", "manual_reviewed", "allow_with_notice"],
    )
    assert reviewed.review_note == "Needs manual sandbox review but can proceed."
    assert reviewed.review_labels == ["risk_high", "manual_reviewed", "allow_with_notice"]

    service.decide_submission(
        submission_id=sub.id,
        reviewer_id="admin-1",
        decision="approve",
    )
    service.update_submission_review(
        submission_id=sub.id,
        reviewer_id="admin-1",
        review_note="Approved with notice.",
        review_labels=["risk_high", "approved_with_notice"],
    )

    published = service.get_published_template("community/basic")
    assert published is not None
    assert published.review_note == "Approved with notice."
    assert published.review_labels == ["risk_high", "approved_with_notice"]


def test_market_service_records_template_engagement_and_persists(tmp_path):
    state_file = tmp_path / "market-state.json"
    store = JsonStateStore(state_file)
    clock = FrozenClock(datetime(2026, 3, 25, 10, 0, tzinfo=UTC))

    service_a = MarketService(clock=clock, state_store=store)
    sub = service_a.submit_template(user_id="u1", template_id="community/basic", version="1.0.0")
    service_a.decide_submission(submission_id=sub.id, reviewer_id="admin-1", decision="approve")

    service_a.record_template_event(template_id="community/basic", event="trial_request")
    clock.shift(minutes=15)
    service_a.record_template_event(template_id="community/basic", event="install")
    clock.shift(minutes=5)
    service_a.record_template_event(template_id="community/basic", event="prompt_generation")

    published = service_a.get_published_template("community/basic")
    assert published is not None
    assert published.engagement["trial_requests"] == 1
    assert published.engagement["installs"] == 1
    assert published.engagement["prompt_generations"] == 1
    assert published.engagement["package_generations"] == 0
    assert published.engagement["community_submissions"] == 1
    assert published.engagement["last_activity_at"] == "2026-03-25T10:20:00+00:00"

    service_b = MarketService(
        clock=FrozenClock(datetime(2026, 3, 25, 11, 0, tzinfo=UTC)),
        state_store=store,
    )
    loaded = service_b.get_published_template("community/basic")
    assert loaded is not None
    assert loaded.engagement["installs"] == 1
    assert loaded.engagement["prompt_generations"] == 1


def test_market_state_persists_across_service_restart_with_sqlite_store(tmp_path):
    sqlite_file = tmp_path / "sharelife_state.sqlite3"
    store = SqliteStateStore(sqlite_file, store_key="market_state")

    service_a = MarketService(
        clock=FrozenClock(datetime(2026, 3, 25, 10, 0, tzinfo=UTC)),
        state_store=store,
    )
    sub = service_a.submit_template(user_id="u1", template_id="community/basic", version="1.0.0")
    service_a.decide_submission(submission_id=sub.id, reviewer_id="admin-1", decision="approve")
    service_a.record_template_event(template_id="community/basic", event="install")

    service_b = MarketService(
        clock=FrozenClock(datetime(2026, 3, 25, 11, 0, tzinfo=UTC)),
        state_store=store,
    )
    loaded = service_b.get_published_template("community/basic")
    assert loaded is not None
    assert loaded.version == "1.0.0"
    assert loaded.engagement["installs"] == 1


def test_market_service_migrates_legacy_sqlite_key_value_payload_once(tmp_path):
    sqlite_file = tmp_path / "sharelife_state.sqlite3"
    legacy_store = SqliteStateStore(sqlite_file, store_key="market_state")
    legacy_store.save(
        {
            "submissions": [
                {
                    "id": "s1",
                    "user_id": "u1",
                    "template_id": "community/basic",
                    "version": "1.0.0",
                    "status": "approved",
                    "created_at": "2026-03-25T10:00:00+00:00",
                    "updated_at": "2026-03-25T10:05:00+00:00",
                    "reviewer_id": "admin-1",
                    "review_note": "ok",
                    "prompt_template": "legacy prompt",
                    "package_artifact": None,
                    "scan_summary": None,
                    "review_labels": [],
                    "warning_flags": [],
                    "risk_level": "low",
                    "category": "starter",
                    "tags": ["legacy"],
                    "maintainer": "legacy",
                    "source_channel": "legacy_state_store",
                }
            ],
            "published": [
                {
                    "template_id": "community/basic",
                    "version": "1.0.0",
                    "source_submission_id": "s1",
                    "prompt_template": "legacy prompt",
                    "published_at": "2026-03-25T10:05:00+00:00",
                    "review_note": "ok",
                    "package_artifact": None,
                    "scan_summary": None,
                    "review_labels": [],
                    "warning_flags": [],
                    "risk_level": "low",
                    "category": "starter",
                    "tags": ["legacy"],
                    "maintainer": "legacy",
                    "source_channel": "legacy_state_store",
                    "engagement": {
                        "trial_requests": 0,
                        "installs": 0,
                        "prompt_generations": 0,
                        "package_generations": 0,
                        "community_submissions": 1,
                        "last_activity_at": "",
                    },
                }
            ],
        }
    )

    service = MarketService(
        clock=FrozenClock(datetime(2026, 3, 25, 11, 0, tzinfo=UTC)),
        state_store=legacy_store,
    )
    published = service.get_published_template("community/basic")
    assert published is not None
    assert published.prompt_template == "legacy prompt"

    # After migration, new writes should keep using repository tables in the same DB.
    service.record_template_event(template_id="community/basic", event="trial_request")
    reloaded = MarketService(
        clock=FrozenClock(datetime(2026, 3, 25, 12, 0, tzinfo=UTC)),
        state_store=legacy_store,
    )
    again = reloaded.get_published_template("community/basic")
    assert again is not None
    assert again.engagement["trial_requests"] == 1
