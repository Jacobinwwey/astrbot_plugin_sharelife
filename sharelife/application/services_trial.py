"""Session trial lifecycle service."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import uuid4

from ..infrastructure.json_state_store import JsonStateStore
from ..infrastructure.sqlite_state_store import SqliteStateStore
from ..infrastructure.system_clock import SystemClock
from ..infrastructure.trial_repository import (
    JsonTrialRepository,
    SqliteTrialRepository,
    TrialRepository,
)


@dataclass(slots=True)
class TrialRecord:
    id: str
    user_id: str
    session_id: str
    template_id: str
    started_at: datetime
    expires_at: datetime
    ttl_seconds: int


class TrialService:
    DEFAULT_TTL_SECONDS = 7200

    def __init__(
        self,
        clock: SystemClock,
        state_store: JsonStateStore | SqliteStateStore | None = None,
        repository: TrialRepository | None = None,
    ):
        self.clock = clock
        self.state_store = state_store
        self.repository = self._build_repository(state_store=state_store, repository=repository)
        self._trials: dict[str, TrialRecord] = {}
        self._load_state()

    @staticmethod
    def _build_repository(
        *,
        state_store: JsonStateStore | SqliteStateStore | None,
        repository: TrialRepository | None,
    ) -> TrialRepository | None:
        if repository is not None:
            return repository
        if state_store is None:
            return None
        if isinstance(state_store, SqliteStateStore):
            return SqliteTrialRepository(state_store.db_path, legacy_state_store=state_store)
        return JsonTrialRepository(state_store)

    def start_trial(self, user_id: str, session_id: str, template_id: str) -> TrialRecord:
        now = self.clock.utcnow()
        trial = TrialRecord(
            id=str(uuid4()),
            user_id=user_id,
            session_id=session_id,
            template_id=template_id,
            started_at=now,
            expires_at=now + timedelta(seconds=self.DEFAULT_TTL_SECONDS),
            ttl_seconds=self.DEFAULT_TTL_SECONDS,
        )
        self._trials[trial.id] = trial
        self._flush_state()
        return trial

    def renew_trial(self, trial_id: str) -> None:
        raise PermissionError("TRIAL_RENEW_FORBIDDEN")

    def has_trial_history(self, user_id: str, template_id: str) -> bool:
        for trial in self._trials.values():
            if trial.user_id == user_id and trial.template_id == template_id:
                return True
        return False

    def get_status(self, user_id: str, session_id: str, template_id: str) -> dict:
        trial = self._find_latest_trial(
            user_id=user_id,
            session_id=session_id,
            template_id=template_id,
        )
        if trial is None:
            return {
                "status": "not_started",
                "user_id": user_id,
                "session_id": session_id,
                "template_id": template_id,
            }

        now = self.clock.utcnow()
        remaining_seconds = max(0, int((trial.expires_at - now).total_seconds()))
        return {
            "status": "active" if trial.expires_at > now else "expired",
            "trial_id": trial.id,
            "user_id": trial.user_id,
            "session_id": trial.session_id,
            "template_id": trial.template_id,
            "started_at": trial.started_at.isoformat(),
            "expires_at": trial.expires_at.isoformat(),
            "ttl_seconds": trial.ttl_seconds,
            "remaining_seconds": remaining_seconds,
        }

    def _find_latest_trial(self, user_id: str, session_id: str, template_id: str) -> TrialRecord | None:
        exact_matches = [
            item
            for item in self._trials.values()
            if item.user_id == user_id
            and item.session_id == session_id
            and item.template_id == template_id
        ]
        if exact_matches:
            return max(exact_matches, key=lambda item: item.started_at)

        fallback_matches = [
            item
            for item in self._trials.values()
            if item.user_id == user_id and item.template_id == template_id
        ]
        if not fallback_matches:
            return None
        return max(fallback_matches, key=lambda item: item.started_at)

    def _load_state(self) -> None:
        if self.repository is None:
            return
        payload = self.repository.load_state()
        for item in payload.get("trials", []):
            trial = TrialRecord(
                id=item["id"],
                user_id=item["user_id"],
                session_id=item["session_id"],
                template_id=item["template_id"],
                started_at=datetime.fromisoformat(item["started_at"]),
                expires_at=datetime.fromisoformat(item["expires_at"]),
                ttl_seconds=int(item.get("ttl_seconds", self.DEFAULT_TTL_SECONDS)),
            )
            self._trials[trial.id] = trial

    def _flush_state(self) -> None:
        if self.repository is None:
            return
        payload = {
            "trials": [
                {
                    "id": item.id,
                    "user_id": item.user_id,
                    "session_id": item.session_id,
                    "template_id": item.template_id,
                    "started_at": item.started_at.isoformat(),
                    "expires_at": item.expires_at.isoformat(),
                    "ttl_seconds": item.ttl_seconds,
                }
                for item in self._trials.values()
            ]
        }
        self.repository.save_state(payload)
