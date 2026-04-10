"""Audit service for governance events."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import uuid4

from ..infrastructure.json_state_store import JsonStateStore
from ..infrastructure.audit_repository import (
    AuditRepository,
    JsonAuditRepository,
    SqliteAuditRepository,
)
from ..infrastructure.sqlite_state_store import SqliteStateStore
from ..infrastructure.system_clock import SystemClock


@dataclass(slots=True)
class AuditEvent:
    id: str
    action: str
    actor_id: str
    actor_role: str
    target_id: str
    status: str
    detail: dict
    created_at: datetime


class AuditService:
    def __init__(
        self,
        clock: SystemClock,
        state_store: JsonStateStore | SqliteStateStore | None = None,
        repository: AuditRepository | None = None,
    ):
        self.clock = clock
        self.state_store = state_store
        self.repository = self._build_repository(state_store=state_store, repository=repository)
        self._events: list[AuditEvent] = []
        self._load_state()

    @staticmethod
    def _build_repository(
        *,
        state_store: JsonStateStore | SqliteStateStore | None,
        repository: AuditRepository | None,
    ) -> AuditRepository | None:
        if repository is not None:
            return repository
        if state_store is None:
            return None
        if isinstance(state_store, SqliteStateStore):
            return SqliteAuditRepository(state_store.db_path, legacy_state_store=state_store)
        return JsonAuditRepository(state_store)

    def record(
        self,
        action: str,
        actor_id: str,
        actor_role: str,
        target_id: str,
        status: str,
        detail: dict | None = None,
    ) -> AuditEvent:
        event = AuditEvent(
            id=str(uuid4()),
            action=action,
            actor_id=actor_id,
            actor_role=actor_role,
            target_id=target_id,
            status=status,
            detail=detail or {},
            created_at=self.clock.utcnow(),
        )
        self._events.append(event)
        self._flush_state()
        return event

    def list_events(self, limit: int = 100) -> list[AuditEvent]:
        if limit <= 0:
            return []
        return list(self._events[-limit:])

    def summarize_events(self, limit: int = 100) -> dict[str, Any]:
        return self.summarize_rows(self.list_events(limit=limit))

    @classmethod
    def summarize_rows(cls, events: list[AuditEvent]) -> dict[str, Any]:
        summary: dict[str, Any] = {
            "total": len(events),
            "first_event_at": "",
            "last_event_at": "",
            "actor_roles": [],
            "actors": [],
            "actions": [],
            "reviewers": [],
            "devices": [],
        }
        if not events:
            return summary

        summary["first_event_at"] = events[0].created_at.isoformat()
        summary["last_event_at"] = events[-1].created_at.isoformat()

        actor_role_buckets: dict[str, dict[str, Any]] = {}
        actor_buckets: dict[tuple[str, str], dict[str, Any]] = {}
        action_buckets: dict[str, dict[str, Any]] = {}
        reviewer_buckets: dict[str, dict[str, Any]] = {}
        device_buckets: dict[tuple[str, str], dict[str, Any]] = {}

        for event in events:
            cls._update_simple_bucket(
                actor_role_buckets,
                key=str(event.actor_role or "unknown").strip() or "unknown",
                label_key="actor_role",
                label_value=str(event.actor_role or "unknown").strip() or "unknown",
                event=event,
            )
            cls._update_simple_bucket(
                actor_buckets,
                key=(str(event.actor_role or "unknown").strip() or "unknown", str(event.actor_id or "").strip() or "-"),
                label_key="actor_key",
                label_value={
                    "actor_role": str(event.actor_role or "unknown").strip() or "unknown",
                    "actor_id": str(event.actor_id or "").strip() or "-",
                },
                event=event,
            )
            cls._update_simple_bucket(
                action_buckets,
                key=str(event.action or "unknown").strip() or "unknown",
                label_key="action",
                label_value=str(event.action or "unknown").strip() or "unknown",
                event=event,
            )

            reviewer_id = cls._event_reviewer_id(event)
            device_id = cls._event_device_id(event)

            if reviewer_id:
                reviewer_bucket = reviewer_buckets.setdefault(
                    reviewer_id,
                    {
                        "reviewer_id": reviewer_id,
                        "count": 0,
                        "last_event_at": event.created_at,
                        "actions": {},
                        "actor_roles": set(),
                        "device_ids": set(),
                    },
                )
                reviewer_bucket["count"] += 1
                reviewer_bucket["last_event_at"] = max(reviewer_bucket["last_event_at"], event.created_at)
                reviewer_bucket["actions"][event.action] = int(reviewer_bucket["actions"].get(event.action, 0) or 0) + 1
                reviewer_bucket["actor_roles"].add(str(event.actor_role or "unknown").strip() or "unknown")
                if device_id:
                    reviewer_bucket["device_ids"].add(device_id)

            if device_id:
                reviewer_for_device = reviewer_id
                device_bucket = device_buckets.setdefault(
                    (reviewer_for_device, device_id),
                    {
                        "reviewer_id": reviewer_for_device,
                        "device_id": device_id,
                        "count": 0,
                        "last_event_at": event.created_at,
                        "actions": {},
                    },
                )
                device_bucket["count"] += 1
                device_bucket["last_event_at"] = max(device_bucket["last_event_at"], event.created_at)
                device_bucket["actions"][event.action] = int(device_bucket["actions"].get(event.action, 0) or 0) + 1

        summary["actor_roles"] = cls._serialize_simple_buckets(actor_role_buckets)
        summary["actors"] = cls._serialize_actor_buckets(actor_buckets)
        summary["actions"] = cls._serialize_simple_buckets(action_buckets)
        summary["reviewers"] = cls._serialize_reviewer_buckets(reviewer_buckets)
        summary["devices"] = cls._serialize_device_buckets(device_buckets)
        return summary

    @staticmethod
    def _event_detail(event: AuditEvent) -> dict[str, Any]:
        return event.detail if isinstance(event.detail, dict) else {}

    @classmethod
    def _event_reviewer_id(cls, event: AuditEvent) -> str:
        detail = cls._event_detail(event)
        reviewer_id = str(detail.get("reviewer_id", "") or "").strip()
        if reviewer_id:
            return reviewer_id
        if str(event.actor_role or "").strip().lower() == "reviewer":
            return str(event.actor_id or "").strip()
        return ""

    @classmethod
    def _event_device_id(cls, event: AuditEvent) -> str:
        detail = cls._event_detail(event)
        device_id = str(detail.get("device_id", "") or "").strip()
        if device_id:
            return device_id
        action = str(event.action or "").strip()
        if action in {"reviewer.device_registered", "reviewer.device_revoked"}:
            return str(event.target_id or "").strip()
        return ""

    @staticmethod
    def _update_simple_bucket(
        buckets: dict[Any, dict[str, Any]],
        *,
        key: Any,
        label_key: str,
        label_value: Any,
        event: AuditEvent,
    ) -> None:
        bucket = buckets.setdefault(
            key,
            {
                label_key: label_value,
                "count": 0,
                "last_event_at": event.created_at,
            },
        )
        bucket["count"] += 1
        bucket["last_event_at"] = max(bucket["last_event_at"], event.created_at)

    @staticmethod
    def _serialize_simple_buckets(buckets: dict[Any, dict[str, Any]]) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for item in buckets.values():
            row = {key: value for key, value in item.items() if key != "last_event_at"}
            row["last_event_at"] = item["last_event_at"].isoformat()
            rows.append(row)
        return sorted(
            rows,
            key=lambda item: (
                -int(item.get("count", 0) or 0),
                str(item.get("last_event_at", "") or ""),
                str(item.get("action", item.get("actor_role", "")) or ""),
            ),
        )

    @staticmethod
    def _serialize_actor_buckets(buckets: dict[tuple[str, str], dict[str, Any]]) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for item in buckets.values():
            actor_key = item.get("actor_key", {})
            row = {
                "actor_role": str(actor_key.get("actor_role", "unknown") or "unknown"),
                "actor_id": str(actor_key.get("actor_id", "-") or "-"),
                "count": int(item.get("count", 0) or 0),
                "last_event_at": item["last_event_at"].isoformat(),
            }
            rows.append(row)
        return sorted(
            rows,
            key=lambda item: (
                -int(item.get("count", 0) or 0),
                str(item.get("last_event_at", "") or ""),
                str(item.get("actor_role", "") or ""),
                str(item.get("actor_id", "") or ""),
            ),
        )

    @classmethod
    def _serialize_reviewer_buckets(cls, buckets: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for item in buckets.values():
            rows.append(
                {
                    "reviewer_id": str(item.get("reviewer_id", "") or ""),
                    "count": int(item.get("count", 0) or 0),
                    "last_event_at": item["last_event_at"].isoformat(),
                    "actor_roles": sorted(str(role) for role in item.get("actor_roles", set()) if str(role).strip()),
                    "device_ids": sorted(str(device_id) for device_id in item.get("device_ids", set()) if str(device_id).strip()),
                    "actions": cls._serialize_action_counts(item.get("actions", {})),
                }
            )
        return sorted(
            rows,
            key=lambda item: (
                -int(item.get("count", 0) or 0),
                str(item.get("last_event_at", "") or ""),
                str(item.get("reviewer_id", "") or ""),
            ),
        )

    @classmethod
    def _serialize_device_buckets(cls, buckets: dict[tuple[str, str], dict[str, Any]]) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for item in buckets.values():
            rows.append(
                {
                    "reviewer_id": str(item.get("reviewer_id", "") or ""),
                    "device_id": str(item.get("device_id", "") or ""),
                    "count": int(item.get("count", 0) or 0),
                    "last_event_at": item["last_event_at"].isoformat(),
                    "actions": cls._serialize_action_counts(item.get("actions", {})),
                }
            )
        return sorted(
            rows,
            key=lambda item: (
                -int(item.get("count", 0) or 0),
                str(item.get("last_event_at", "") or ""),
                str(item.get("reviewer_id", "") or ""),
                str(item.get("device_id", "") or ""),
            ),
        )

    @staticmethod
    def _serialize_action_counts(action_counts: dict[str, Any]) -> list[dict[str, Any]]:
        rows = [
            {"action": str(action or "unknown"), "count": int(count or 0)}
            for action, count in action_counts.items()
        ]
        return sorted(rows, key=lambda item: (-int(item.get("count", 0) or 0), str(item.get("action", "") or "")))

    def _load_state(self) -> None:
        if self.repository is None:
            return

        payload = self.repository.load_state()
        for item in payload.get("events", []):
            event = AuditEvent(
                id=item["id"],
                action=item["action"],
                actor_id=item["actor_id"],
                actor_role=item["actor_role"],
                target_id=item["target_id"],
                status=item["status"],
                detail=item.get("detail", {}),
                created_at=datetime.fromisoformat(item["created_at"]),
            )
            self._events.append(event)

    def _flush_state(self) -> None:
        if self.repository is None:
            return

        payload = {
            "events": [
                {
                    "id": item.id,
                    "action": item.action,
                    "actor_id": item.actor_id,
                    "actor_role": item.actor_role,
                    "target_id": item.target_id,
                    "status": item.status,
                    "detail": item.detail,
                    "created_at": item.created_at.isoformat(),
                }
                for item in self._events
            ]
        }
        self.repository.save_state(payload)
