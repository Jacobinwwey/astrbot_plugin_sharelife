"""Persistent config continuity ledger for apply and rollback workflows."""

from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime
import hashlib
import json
from typing import Any, Protocol
from uuid import uuid4

from ..infrastructure.system_clock import SystemClock


class StateStore(Protocol):
    def load(self, default: dict[str, Any]) -> dict[str, Any]: ...
    def save(self, payload: dict[str, Any]) -> None: ...


class Clock(Protocol):
    def utcnow(self) -> datetime: ...


class ConfigContinuityService:
    """Persists rollback-capable pre-apply snapshots plus lightweight audit projection."""

    _DEFAULT_STATE: dict[str, Any] = {
        "entries": [],
        "active_snapshots": {},
    }

    def __init__(
        self,
        *,
        state_store: StateStore,
        clock: Clock | None = None,
        max_entries: int = 50,
    ):
        self.state_store = state_store
        self.clock = clock or SystemClock()
        self.max_entries = max(1, int(max_entries or 1))

    def _load_state(self) -> dict[str, Any]:
        payload = self.state_store.load(default=self._DEFAULT_STATE)
        if not isinstance(payload, dict):
            return deepcopy(self._DEFAULT_STATE)
        entries = payload.get("entries", [])
        active = payload.get("active_snapshots", {})
        return {
            "entries": [dict(item) for item in entries if isinstance(item, dict)],
            "active_snapshots": {
                str(plan_id): dict(item)
                for plan_id, item in active.items()
                if isinstance(plan_id, str) and isinstance(item, dict)
            },
        }

    def _save_state(self, payload: dict[str, Any]) -> None:
        self.state_store.save(payload if isinstance(payload, dict) else deepcopy(self._DEFAULT_STATE))

    @staticmethod
    def _entry_plan_id(entry: dict[str, Any]) -> str:
        return str(entry.get("plan_id", "") or "").strip()

    @classmethod
    def _serialize_entry(cls, entry: dict[str, Any], *, has_active_snapshot: bool) -> dict[str, Any]:
        payload = dict(entry)
        payload["active_snapshot_available"] = bool(has_active_snapshot)
        return payload

    def _now_iso(self) -> str:
        return self.clock.utcnow().astimezone(UTC).isoformat()

    @staticmethod
    def _snapshot_digest(snapshot: Any) -> str:
        normalized = json.dumps(snapshot, ensure_ascii=False, sort_keys=True, default=str)
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    @staticmethod
    def _selected_sections(metadata: dict[str, Any]) -> list[str]:
        raw = metadata.get("selected_sections", [])
        values = raw if isinstance(raw, list) else []
        items = sorted({str(item or "").strip() for item in values if str(item or "").strip()})
        return items

    def _normalize_metadata(self, plan_id: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = metadata if isinstance(metadata, dict) else {}
        return {
            "actor_id": str(payload.get("actor_id", "system") or "system").strip() or "system",
            "actor_role": str(payload.get("actor_role", "system") or "system").strip() or "system",
            "source_id": str(payload.get("source_id", plan_id) or plan_id).strip() or plan_id,
            "source_kind": str(payload.get("source_kind", "manual_patch") or "manual_patch").strip() or "manual_patch",
            "selected_sections": self._selected_sections(payload),
            "recovery_class": str(
                payload.get("recovery_class", "config_snapshot_restore") or "config_snapshot_restore",
            ).strip()
            or "config_snapshot_restore",
        }

    def record_apply(
        self,
        *,
        plan_id: str,
        pre_snapshot: Any,
        post_snapshot: Any,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        normalized = self._normalize_metadata(plan_id, metadata)
        now = self._now_iso()
        pre_snapshot_id = f"{plan_id}:pre:{uuid4().hex[:12]}"
        post_snapshot_id = f"{plan_id}:post:{uuid4().hex[:12]}"
        entry = {
            "plan_id": plan_id,
            "status": "applied",
            "actor_id": normalized["actor_id"],
            "actor_role": normalized["actor_role"],
            "source_id": normalized["source_id"],
            "source_kind": normalized["source_kind"],
            "selected_sections": normalized["selected_sections"],
            "recovery_class": normalized["recovery_class"],
            "pre_snapshot_id": pre_snapshot_id,
            "post_snapshot_id": post_snapshot_id,
            "pre_snapshot_digest": self._snapshot_digest(pre_snapshot),
            "post_snapshot_digest": self._snapshot_digest(post_snapshot),
            "restore_verification": "pending",
            "applied_at": now,
            "rolled_back_at": "",
        }

        payload = self._load_state()
        entries = [item for item in payload["entries"] if str(item.get("plan_id", "") or "") != plan_id]
        entries.insert(0, entry)
        payload["entries"] = entries[: self.max_entries]
        payload["active_snapshots"][plan_id] = {
            "plan_id": plan_id,
            "snapshot_id": pre_snapshot_id,
            "snapshot_digest": entry["pre_snapshot_digest"],
            "snapshot": deepcopy(pre_snapshot),
            "created_at": now,
        }
        self._save_state(payload)
        return dict(entry)

    def get_active_snapshot(self, plan_id: str) -> Any | None:
        payload = self._load_state()
        active = payload["active_snapshots"].get(plan_id)
        if not isinstance(active, dict):
            return None
        if "snapshot" not in active:
            return None
        return deepcopy(active["snapshot"])

    def record_rollback(self, *, plan_id: str, restored_snapshot: Any) -> dict[str, Any]:
        payload = self._load_state()
        active = payload["active_snapshots"].get(plan_id)
        if not isinstance(active, dict):
            raise ValueError("PLAN_NOT_APPLIED")

        verification = "matched"
        if str(active.get("snapshot_digest", "") or "") != self._snapshot_digest(restored_snapshot):
            verification = "mismatch"

        now = self._now_iso()
        updated_entry: dict[str, Any] | None = None
        updated_entries: list[dict[str, Any]] = []
        for item in payload["entries"]:
            if str(item.get("plan_id", "") or "") != plan_id:
                updated_entries.append(item)
                continue
            next_item = dict(item)
            next_item["status"] = "rolled_back"
            next_item["restore_verification"] = verification
            next_item["rolled_back_at"] = now
            updated_entry = next_item
            updated_entries.append(next_item)

        if updated_entry is None:
            raise ValueError("PLAN_NOT_FOUND")

        payload["entries"] = updated_entries[: self.max_entries]
        payload["active_snapshots"].pop(plan_id, None)
        self._save_state(payload)
        return dict(updated_entry)

    def describe(self, plan_id: str) -> dict[str, Any] | None:
        payload = self._load_state()
        for item in payload["entries"]:
            if self._entry_plan_id(item) == plan_id:
                return self._serialize_entry(
                    item,
                    has_active_snapshot=plan_id in payload["active_snapshots"],
                )
        return None

    def list_entries(self, limit: int = 20) -> list[dict[str, Any]]:
        payload = self._load_state()
        rows = payload["entries"] if isinstance(payload.get("entries"), list) else []
        if limit <= 0:
            return []
        return [
            self._serialize_entry(
                item,
                has_active_snapshot=self._entry_plan_id(item) in payload["active_snapshots"],
            )
            for item in rows[:limit]
            if isinstance(item, dict)
        ]
