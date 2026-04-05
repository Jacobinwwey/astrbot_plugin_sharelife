"""System clock adapter."""

from __future__ import annotations

from datetime import UTC, datetime


class SystemClock:
    def utcnow(self) -> datetime:
        return datetime.now(UTC)
