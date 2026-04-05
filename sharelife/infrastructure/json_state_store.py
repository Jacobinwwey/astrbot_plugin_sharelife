"""JSON-backed state store for plugin services."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any


class JsonStateStore:
    def __init__(self, path: Path | str):
        self.path = Path(path)

    def load(self, default: dict[str, Any]) -> dict[str, Any]:
        if not self.path.exists():
            return deepcopy(default)

        raw = self.path.read_text(encoding="utf-8").strip()
        if not raw:
            return deepcopy(default)

        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            return deepcopy(default)

        if not isinstance(payload, dict):
            return deepcopy(default)
        return payload

    def save(self, payload: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        tmp.replace(self.path)
