"""Community template submission and installation service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4

from ..infrastructure.json_state_store import JsonStateStore
from ..infrastructure.market_repository import JsonMarketRepository, MarketRepository, SqliteMarketRepository
from ..infrastructure.sqlite_state_store import SqliteStateStore
from ..infrastructure.system_clock import SystemClock


SUBMISSION_PENDING = "pending"
SUBMISSION_APPROVED = "approved"
SUBMISSION_REJECTED = "rejected"


def _default_engagement() -> dict[str, int | str]:
    return {
        "trial_requests": 0,
        "installs": 0,
        "prompt_generations": 0,
        "package_generations": 0,
        "community_submissions": 0,
        "last_activity_at": "",
    }


@dataclass(slots=True)
class CommunitySubmission:
    id: str
    user_id: str
    template_id: str
    version: str
    status: str
    created_at: datetime
    updated_at: datetime
    reviewer_id: str | None = None
    review_note: str = ""
    prompt_template: str = ""
    package_artifact: dict | None = None
    scan_summary: dict | None = None
    upload_options: dict | None = None
    review_labels: list[str] | None = None
    warning_flags: list[str] | None = None
    risk_level: str = "low"
    category: str = ""
    tags: list[str] | None = None
    maintainer: str = ""
    source_channel: str = ""


@dataclass(slots=True)
class PublishedTemplate:
    template_id: str
    version: str
    source_submission_id: str
    prompt_template: str
    published_at: datetime
    review_note: str = ""
    package_artifact: dict | None = None
    scan_summary: dict | None = None
    review_labels: list[str] | None = None
    warning_flags: list[str] | None = None
    risk_level: str = "low"
    category: str = ""
    tags: list[str] | None = None
    maintainer: str = ""
    source_channel: str = ""
    engagement: dict[str, int | str] = field(default_factory=_default_engagement)


class MarketService:
    """Handles user submissions and admin moderation for template publishing."""

    def __init__(
        self,
        clock: SystemClock,
        state_store: JsonStateStore | SqliteStateStore | None = None,
        repository: MarketRepository | None = None,
    ):
        self.clock = clock
        self.state_store = state_store
        self.repository = self._build_repository(state_store=state_store, repository=repository)
        self._submissions: dict[str, CommunitySubmission] = {}
        self._published: dict[str, PublishedTemplate] = {}
        self._load_state()

    @staticmethod
    def _build_repository(
        *,
        state_store: JsonStateStore | SqliteStateStore | None,
        repository: MarketRepository | None,
    ) -> MarketRepository | None:
        if repository is not None:
            return repository
        if state_store is None:
            return None
        if isinstance(state_store, SqliteStateStore):
            return SqliteMarketRepository(
                state_store.db_path,
                legacy_state_store=state_store,
            )
        return JsonMarketRepository(state_store)

    def submit_template(
        self,
        user_id: str,
        template_id: str,
        version: str,
        *,
        prompt_template: str = "",
        package_artifact: dict | None = None,
        scan_summary: dict | None = None,
        upload_options: dict | None = None,
        review_labels: list[str] | None = None,
        warning_flags: list[str] | None = None,
        risk_level: str = "low",
        category: str = "",
        tags: list[str] | None = None,
        maintainer: str = "",
        source_channel: str = "",
    ) -> CommunitySubmission:
        now = self.clock.utcnow()
        submission = CommunitySubmission(
            id=str(uuid4()),
            user_id=user_id,
            template_id=template_id,
            version=version,
            status=SUBMISSION_PENDING,
            created_at=now,
            updated_at=now,
            prompt_template=prompt_template,
            package_artifact=package_artifact,
            scan_summary=scan_summary,
            upload_options=upload_options,
            review_labels=list(review_labels or []),
            warning_flags=list(warning_flags or []),
            risk_level=risk_level,
            category=category,
            tags=list(tags or []),
            maintainer=maintainer,
            source_channel=source_channel,
        )
        self._submissions[submission.id] = submission
        self._refresh_submission_counts(template_id)
        self._flush_state()
        return submission

    def get_submission(self, submission_id: str) -> CommunitySubmission:
        return self._submissions[submission_id]

    def list_submissions(self, status: str | None = None) -> list[CommunitySubmission]:
        values = list(self._submissions.values())
        if status:
            status = status.strip().lower()
            values = [item for item in values if item.status == status]
        return sorted(values, key=lambda item: item.created_at)

    def decide_submission(
        self,
        submission_id: str,
        reviewer_id: str,
        decision: str,
        review_note: str = "",
        review_labels: list[str] | None = None,
    ) -> CommunitySubmission:
        submission = self.get_submission(submission_id)
        normalized = decision.strip().lower()
        if normalized not in {"approve", "approved", "reject", "rejected"}:
            raise ValueError("INVALID_SUBMISSION_DECISION")

        if review_note:
            submission.review_note = review_note
        if review_labels is not None:
            submission.review_labels = list(review_labels)
        submission.status = (
            SUBMISSION_APPROVED if normalized.startswith("approve") else SUBMISSION_REJECTED
        )
        submission.reviewer_id = reviewer_id
        submission.updated_at = self.clock.utcnow()

        if submission.status == SUBMISSION_APPROVED:
            existing = self._published.get(submission.template_id)
            self._published[submission.template_id] = PublishedTemplate(
                template_id=submission.template_id,
                version=submission.version,
                source_submission_id=submission.id,
                prompt_template=(
                    submission.prompt_template
                    or (
                        "You are running template "
                        f"{submission.template_id} (version {submission.version}). "
                        "Follow strict-mode safety boundaries and avoid privilege escalation."
                    )
                ),
                published_at=submission.updated_at,
                review_note=submission.review_note,
                package_artifact=submission.package_artifact,
                scan_summary=submission.scan_summary,
                review_labels=list(submission.review_labels or []),
                warning_flags=list(submission.warning_flags or []),
                risk_level=submission.risk_level,
                category=submission.category,
                tags=list(submission.tags or []),
                maintainer=submission.maintainer,
                source_channel=submission.source_channel or "community_submission",
                engagement=self._copy_engagement(existing.engagement if existing else None),
            )
        else:
            self._published.pop(submission.template_id, None)

        self._refresh_submission_counts(submission.template_id)
        self._flush_state()

        return submission

    def update_submission_review(
        self,
        submission_id: str,
        reviewer_id: str,
        review_note: str = "",
        review_labels: list[str] | None = None,
    ) -> CommunitySubmission:
        submission = self.get_submission(submission_id)
        submission.reviewer_id = reviewer_id
        submission.review_note = review_note
        if review_labels is not None:
            submission.review_labels = list(review_labels)
        submission.updated_at = self.clock.utcnow()

        published = self._published.get(submission.template_id)
        if published is not None and published.source_submission_id == submission.id:
            published.review_note = submission.review_note
            published.review_labels = list(submission.review_labels or [])
            published.published_at = submission.updated_at

        self._flush_state()
        return submission

    def list_published_templates(self) -> list[PublishedTemplate]:
        return sorted(self._published.values(), key=lambda item: item.template_id)

    def get_published_template(self, template_id: str) -> PublishedTemplate | None:
        return self._published.get(template_id)

    def publish_official_template(
        self,
        *,
        template_id: str,
        version: str,
        prompt_template: str,
        review_note: str = "",
        package_artifact: dict | None = None,
        scan_summary: dict | None = None,
        review_labels: list[str] | None = None,
        warning_flags: list[str] | None = None,
        risk_level: str = "low",
        category: str = "",
        tags: list[str] | None = None,
        maintainer: str = "",
        source_channel: str = "bundled_official",
    ) -> PublishedTemplate:
        existing = self._published.get(template_id)
        published = PublishedTemplate(
            template_id=template_id,
            version=version,
            source_submission_id=f"official:{template_id}@{version}",
            prompt_template=prompt_template,
            published_at=self.clock.utcnow(),
            review_note=review_note,
            package_artifact=package_artifact,
            scan_summary=scan_summary,
            review_labels=list(review_labels or []),
            warning_flags=list(warning_flags or []),
            risk_level=risk_level,
            category=category,
            tags=list(tags or []),
            maintainer=maintainer,
            source_channel=source_channel,
            engagement=self._copy_engagement(existing.engagement if existing else None),
        )
        self._published[template_id] = published
        self._refresh_submission_counts(template_id)
        self._flush_state()
        return published

    def build_prompt_bundle(self, template_id: str) -> dict[str, str]:
        published = self.get_published_template(template_id=template_id)
        if not published:
            raise ValueError("TEMPLATE_NOT_PUBLISHED")
        return {
            "template_id": published.template_id,
            "version": published.version,
            "prompt": published.prompt_template,
        }

    def record_template_event(self, template_id: str, event: str) -> None:
        published = self.get_published_template(template_id=template_id)
        if published is None:
            return

        event_map = {
            "trial_request": "trial_requests",
            "install": "installs",
            "prompt_generation": "prompt_generations",
            "package_generation": "package_generations",
        }
        key = event_map.get(str(event or "").strip().lower())
        if not key:
            return

        engagement = self._copy_engagement(published.engagement)
        engagement[key] = int(engagement.get(key, 0) or 0) + 1
        engagement["community_submissions"] = self._submission_count_for_template(template_id)
        engagement["last_activity_at"] = self.clock.utcnow().isoformat()
        published.engagement = engagement
        self._flush_state()

    def _submission_count_for_template(self, template_id: str) -> int:
        return sum(1 for item in self._submissions.values() if item.template_id == template_id)

    def _refresh_submission_counts(self, template_id: str) -> None:
        published = self._published.get(template_id)
        if published is None:
            return
        engagement = self._copy_engagement(published.engagement)
        engagement["community_submissions"] = self._submission_count_for_template(template_id)
        published.engagement = engagement

    @staticmethod
    def _copy_engagement(engagement: dict | None) -> dict[str, int | str]:
        out = _default_engagement()
        if isinstance(engagement, dict):
            for key in out:
                if key in engagement and engagement[key] is not None:
                    out[key] = engagement[key]
        for key in ("trial_requests", "installs", "prompt_generations", "package_generations", "community_submissions"):
            out[key] = int(out.get(key, 0) or 0)
        out["last_activity_at"] = str(out.get("last_activity_at", "") or "")
        return out

    def _load_state(self) -> None:
        if self.repository is None:
            return

        payload = self.repository.load_state()
        for item in payload.get("submissions", []):
            submission = CommunitySubmission(
                id=item["id"],
                user_id=item["user_id"],
                template_id=item["template_id"],
                version=item["version"],
                status=item["status"],
                created_at=datetime.fromisoformat(item["created_at"]),
                updated_at=datetime.fromisoformat(item["updated_at"]),
                reviewer_id=item.get("reviewer_id"),
                review_note=item.get("review_note", ""),
                prompt_template=item.get("prompt_template", ""),
                package_artifact=item.get("package_artifact"),
                scan_summary=item.get("scan_summary"),
                upload_options=item.get("upload_options"),
                review_labels=list(item.get("review_labels", []) or []),
                warning_flags=list(item.get("warning_flags", []) or []),
                risk_level=item.get("risk_level", "low"),
                category=item.get("category", ""),
                tags=list(item.get("tags", []) or []),
                maintainer=item.get("maintainer", ""),
                source_channel=item.get("source_channel", ""),
            )
            self._submissions[submission.id] = submission

        for item in payload.get("published", []):
            published = PublishedTemplate(
                template_id=item["template_id"],
                version=item["version"],
                source_submission_id=item["source_submission_id"],
                prompt_template=item["prompt_template"],
                published_at=datetime.fromisoformat(item["published_at"]),
                review_note=item.get("review_note", ""),
                package_artifact=item.get("package_artifact"),
                scan_summary=item.get("scan_summary"),
                review_labels=list(item.get("review_labels", []) or []),
                warning_flags=list(item.get("warning_flags", []) or []),
                risk_level=item.get("risk_level", "low"),
                category=item.get("category", ""),
                tags=list(item.get("tags", []) or []),
                maintainer=item.get("maintainer", ""),
                source_channel=item.get("source_channel", ""),
                engagement=self._copy_engagement(item.get("engagement")),
            )
            self._published[published.template_id] = published

        for template_id in list(self._published):
            self._refresh_submission_counts(template_id)

    def _flush_state(self) -> None:
        if self.repository is None:
            return

        payload = {
            "submissions": [
                {
                    "id": item.id,
                    "user_id": item.user_id,
                    "template_id": item.template_id,
                    "version": item.version,
                    "status": item.status,
                    "created_at": item.created_at.isoformat(),
                    "updated_at": item.updated_at.isoformat(),
                    "reviewer_id": item.reviewer_id,
                    "review_note": item.review_note,
                    "prompt_template": item.prompt_template,
                    "package_artifact": item.package_artifact,
                    "scan_summary": item.scan_summary,
                    "upload_options": item.upload_options,
                    "review_labels": list(item.review_labels or []),
                    "warning_flags": list(item.warning_flags or []),
                    "risk_level": item.risk_level,
                    "category": item.category,
                    "tags": list(item.tags or []),
                    "maintainer": item.maintainer,
                    "source_channel": item.source_channel,
                }
                for item in self._submissions.values()
            ],
            "published": [
                {
                    "template_id": item.template_id,
                    "version": item.version,
                    "source_submission_id": item.source_submission_id,
                    "prompt_template": item.prompt_template,
                    "published_at": item.published_at.isoformat(),
                    "review_note": item.review_note,
                    "package_artifact": item.package_artifact,
                    "scan_summary": item.scan_summary,
                    "review_labels": list(item.review_labels or []),
                    "warning_flags": list(item.warning_flags or []),
                    "risk_level": item.risk_level,
                    "category": item.category,
                    "tags": list(item.tags or []),
                    "maintainer": item.maintainer,
                    "source_channel": item.source_channel,
                    "engagement": self._copy_engagement(item.engagement),
                }
                for item in self._published.values()
            ],
        }
        self.repository.save_state(payload)
