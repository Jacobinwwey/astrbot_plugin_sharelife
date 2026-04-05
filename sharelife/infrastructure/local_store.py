"""Local JSON file store utilities."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class LocalStore:
    def __init__(self, root: Path | str):
        self.root = Path(root)

    def save_json(self, relative_path: str, payload: dict[str, Any]) -> None:
        target = self.root / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def load_json(self, relative_path: str, default: dict[str, Any]) -> dict[str, Any]:
        target = self.root / relative_path
        if not target.exists():
            return default
        raw = target.read_text(encoding="utf-8")
        return json.loads(raw)
