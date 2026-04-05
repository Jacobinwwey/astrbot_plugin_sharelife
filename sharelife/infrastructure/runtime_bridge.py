"""Runtime bridge implementations for Sharelife apply/profile-pack workflows."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any


def _deep_merge_dict(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(base)
    for key, value in patch.items():
        current = merged.get(key)
        if isinstance(current, dict) and isinstance(value, dict):
            merged[key] = _deep_merge_dict(current, value)
            continue
        merged[key] = deepcopy(value)
    return merged


def _replace_merge_dict(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(base)
    for key, value in patch.items():
        merged[key] = deepcopy(value)
    return merged


def _apply_merge_mode(base: dict[str, Any], patch: dict[str, Any], merge_mode: str) -> dict[str, Any]:
    if merge_mode == "deep_merge":
        return _deep_merge_dict(base, patch)
    return _replace_merge_dict(base, patch)


class InMemoryRuntimeBridge:
    """In-memory runtime bridge for tests and lightweight local development."""

    def __init__(self, initial_state: dict[str, Any] | None = None, merge_mode: str = "replace"):
        self.state = deepcopy(initial_state or {})
        self.merge_mode = str(merge_mode or "replace").strip().lower()

    def snapshot(self) -> dict[str, Any]:
        return deepcopy(self.state)

    def apply_patch(self, patch: dict[str, Any]) -> None:
        self.state = _apply_merge_mode(self.state, patch, self.merge_mode)

    def restore_snapshot(self, snapshot: dict[str, Any]) -> None:
        self.state = deepcopy(snapshot)


class JsonFileRuntimeBridge:
    """File-backed runtime bridge that persists runtime state as JSON."""

    def __init__(
        self,
        state_path: Path | str,
        initial_state: dict[str, Any] | None = None,
        merge_mode: str = "replace",
    ):
        self.state_path = Path(state_path)
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.merge_mode = str(merge_mode or "replace").strip().lower()
        if not self.state_path.exists():
            self._write_state(initial_state or {})

    def snapshot(self) -> dict[str, Any]:
        return self._read_state()

    def apply_patch(self, patch: dict[str, Any]) -> None:
        current = self._read_state()
        merged = _apply_merge_mode(current, patch, self.merge_mode)
        self._write_state(merged)

    def restore_snapshot(self, snapshot: dict[str, Any]) -> None:
        self._write_state(snapshot)

    def _read_state(self) -> dict[str, Any]:
        try:
            payload = json.loads(self.state_path.read_text(encoding="utf-8"))
        except Exception:
            return {}
        if isinstance(payload, dict):
            return payload
        return {}

    def _write_state(self, payload: dict[str, Any]) -> None:
        text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
        self.state_path.write_text(text, encoding="utf-8")
