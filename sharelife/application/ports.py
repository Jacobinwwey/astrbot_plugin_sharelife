"""Application port contracts."""

from __future__ import annotations

from typing import Any, Protocol


class RuntimePort(Protocol):
    def snapshot(self) -> Any: ...

    def apply_patch(self, patch: dict[str, Any]) -> None: ...

    def restore_snapshot(self, snapshot: Any) -> None: ...


class NotifierPort(Protocol):
    def notify_user(self, user_id: str, message: str) -> None: ...

    def notify_admin(self, message: str) -> None: ...
