"""Notification adapter for community-first workflows."""

from __future__ import annotations

from dataclasses import dataclass

from .json_state_store import JsonStateStore
from .notifier_repository import JsonNotifierRepository, NotifierRepository, SqliteNotifierRepository
from .sqlite_state_store import SqliteStateStore


@dataclass(slots=True)
class NotificationEvent:
    channel: str
    target: str
    message: str


class InMemoryNotifier:
    """Minimal notifier used by tests and local development."""

    def __init__(
        self,
        state_store: JsonStateStore | SqliteStateStore | None = None,
        repository: NotifierRepository | None = None,
    ):
        self.state_store = state_store
        self.repository = self._build_repository(state_store=state_store, repository=repository)
        self.events: list[NotificationEvent] = []
        self._load_state()

    @staticmethod
    def _build_repository(
        *,
        state_store: JsonStateStore | SqliteStateStore | None,
        repository: NotifierRepository | None,
    ) -> NotifierRepository | None:
        if repository is not None:
            return repository
        if state_store is None:
            return None
        if isinstance(state_store, SqliteStateStore):
            return SqliteNotifierRepository(state_store.db_path, legacy_state_store=state_store)
        return JsonNotifierRepository(state_store)

    def notify_user(self, user_id: str, message: str) -> None:
        self.events.append(
            NotificationEvent(channel="user_dm", target=user_id, message=message)
        )
        self._flush_state()

    def notify_admin(self, message: str) -> None:
        self.events.append(
            NotificationEvent(channel="admin_dm", target="admin", message=message)
        )
        self._flush_state()

    def list_events(self, limit: int = 100) -> list[NotificationEvent]:
        if limit <= 0:
            return []
        return list(self.events[-limit:])

    def _load_state(self) -> None:
        if self.repository is None:
            return
        payload = self.repository.load_state()
        for item in payload.get("events", []):
            self.events.append(
                NotificationEvent(
                    channel=item["channel"],
                    target=item["target"],
                    message=item["message"],
                )
            )

    def _flush_state(self) -> None:
        if self.repository is None:
            return
        payload = {
            "events": [
                {
                    "channel": item.channel,
                    "target": item.target,
                    "message": item.message,
                }
                for item in self.events
            ]
        }
        self.repository.save_state(payload)
