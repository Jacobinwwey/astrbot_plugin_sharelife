"""User preference service for execution mode and observability."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from ..infrastructure.json_state_store import JsonStateStore
from ..infrastructure.preference_repository import (
    JsonPreferenceRepository,
    PreferenceRepository,
    SqlitePreferenceRepository,
)
from ..infrastructure.sqlite_state_store import SqliteStateStore


ExecutionMode = Literal["subagent_driven", "inline_execution"]


@dataclass(slots=True)
class UserPreference:
    user_id: str
    execution_mode: ExecutionMode = "subagent_driven"
    observe_task_details: bool = False


class PreferenceService:
    def __init__(
        self,
        state_store: JsonStateStore | SqliteStateStore | None = None,
        repository: PreferenceRepository | None = None,
    ):
        self.state_store = state_store
        self.repository = self._build_repository(state_store=state_store, repository=repository)
        self._prefs: dict[str, UserPreference] = {}
        self._load_state()

    @staticmethod
    def _build_repository(
        *,
        state_store: JsonStateStore | SqliteStateStore | None,
        repository: PreferenceRepository | None,
    ) -> PreferenceRepository | None:
        if repository is not None:
            return repository
        if state_store is None:
            return None
        if isinstance(state_store, SqliteStateStore):
            return SqlitePreferenceRepository(state_store.db_path, legacy_state_store=state_store)
        return JsonPreferenceRepository(state_store)

    def get(self, user_id: str) -> UserPreference:
        pref = self._prefs.get(user_id)
        if pref:
            return pref
        pref = UserPreference(user_id=user_id)
        self._prefs[user_id] = pref
        self._flush_state()
        return pref

    def set_execution_mode(self, user_id: str, mode: ExecutionMode) -> UserPreference:
        if mode not in {"subagent_driven", "inline_execution"}:
            raise ValueError("INVALID_EXECUTION_MODE")
        pref = self.get(user_id)
        pref.execution_mode = mode
        self._flush_state()
        return pref

    def set_observe_details(self, user_id: str, enabled: bool) -> UserPreference:
        pref = self.get(user_id)
        pref.observe_task_details = bool(enabled)
        self._flush_state()
        return pref

    def _load_state(self) -> None:
        if self.repository is None:
            return
        payload = self.repository.load_state()
        for item in payload.get("preferences", []):
            pref = UserPreference(
                user_id=item["user_id"],
                execution_mode=item.get("execution_mode", "subagent_driven"),
                observe_task_details=bool(item.get("observe_task_details", False)),
            )
            self._prefs[pref.user_id] = pref

    def _flush_state(self) -> None:
        if self.repository is None:
            return
        payload = {
            "preferences": [
                {
                    "user_id": item.user_id,
                    "execution_mode": item.execution_mode,
                    "observe_task_details": item.observe_task_details,
                }
                for item in self._prefs.values()
            ]
        }
        self.repository.save_state(payload)
