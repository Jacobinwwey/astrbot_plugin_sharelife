"""Trial request orchestration for community-first workflow."""

from __future__ import annotations

from dataclasses import dataclass

from .ports import NotifierPort
from .services_queue import RetryQueueService
from .services_trial import TrialService
from ..infrastructure.json_state_store import JsonStateStore
from ..infrastructure.sqlite_state_store import SqliteStateStore
from ..infrastructure.trial_request_repository import (
    JsonTrialRequestRepository,
    SqliteTrialRequestRepository,
    TrialRequestRepository,
)


@dataclass(slots=True)
class TrialRequestResult:
    status: str
    trial_id: str | None = None
    retry_request_id: str | None = None


class TrialRequestService:
    """Coordinates first trial and subsequent retry queue behavior."""

    def __init__(
        self,
        trial_service: TrialService,
        retry_queue_service: RetryQueueService,
        notifier: NotifierPort,
        state_store: JsonStateStore | SqliteStateStore | None = None,
        repository: TrialRequestRepository | None = None,
    ):
        self.trial_service = trial_service
        self.retry_queue_service = retry_queue_service
        self.notifier = notifier
        self.state_store = state_store
        self.repository = self._build_repository(state_store=state_store, repository=repository)
        self._first_notice_sent_users: set[str] = set()
        self._load_state()

    @staticmethod
    def _build_repository(
        *,
        state_store: JsonStateStore | SqliteStateStore | None,
        repository: TrialRequestRepository | None,
    ) -> TrialRequestRepository | None:
        if repository is not None:
            return repository
        if state_store is None:
            return None
        if isinstance(state_store, SqliteStateStore):
            return SqliteTrialRequestRepository(state_store.db_path, legacy_state_store=state_store)
        return JsonTrialRequestRepository(state_store)

    def request_trial(self, user_id: str, session_id: str, template_id: str) -> TrialRequestResult:
        if not self.trial_service.has_trial_history(user_id=user_id, template_id=template_id):
            trial = self.trial_service.start_trial(
                user_id=user_id,
                session_id=session_id,
                template_id=template_id,
            )
            self._send_first_notice_if_needed(user_id=user_id, template_id=template_id)
            return TrialRequestResult(status="trial_started", trial_id=trial.id)

        queued = self.retry_queue_service.enqueue(user_id=user_id, template_id=template_id)
        self.notifier.notify_admin(
            f"retry request queued: request_id={queued.id} user_id={user_id} template_id={template_id}"
        )
        return TrialRequestResult(status="retry_queued", retry_request_id=queued.id)

    def _send_first_notice_if_needed(self, user_id: str, template_id: str) -> None:
        if user_id in self._first_notice_sent_users:
            return

        self._first_notice_sent_users.add(user_id)
        self._flush_state()
        self.notifier.notify_user(
            user_id=user_id,
            message=(
                "first trial started (2h). renewal is forbidden; "
                "further attempts require admin review."
            ),
        )
        self.notifier.notify_admin(
            f"first trial started: user_id={user_id} template_id={template_id}"
        )

    def _load_state(self) -> None:
        if self.repository is None:
            return
        payload = self.repository.load_state()
        users = payload.get("first_notice_sent_users", [])
        self._first_notice_sent_users = {str(item) for item in users}

    def _flush_state(self) -> None:
        if self.repository is None:
            return
        payload = {
            "first_notice_sent_users": sorted(self._first_notice_sent_users),
        }
        self.repository.save_state(payload)
