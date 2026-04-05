"""Interface DTO models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class CommandResponse:
    message: str
    data: dict[str, Any]
