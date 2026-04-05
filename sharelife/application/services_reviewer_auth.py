"""Reviewer auth primitives: invite redemption + device key management."""

from __future__ import annotations

import secrets
import time
from typing import Any, Protocol


class StateStore(Protocol):
    def load(self, default: dict[str, Any]) -> dict[str, Any]: ...
    def save(self, payload: dict[str, Any]) -> None: ...


class ReviewerAuthService:
    """Manages reviewer identities, invite codes, and device key limits."""

    DEFAULT_INVITE_TTL_SECONDS = 3600

    def __init__(self, state_store: StateStore, max_devices: int = 3):
        self.store = state_store
        self.max_devices = max(1, int(max_devices or 1))

    @staticmethod
    def _normalize_user_id(value: str) -> str:
        return str(value or "").strip()

    def _load_payload(self) -> dict[str, Any]:
        payload = self.store.load({})
        if isinstance(payload, dict):
            return payload
        return {}

    def _save_payload(self, payload: dict[str, Any]) -> None:
        self.store.save(payload if isinstance(payload, dict) else {})

    def _load_accounts(self) -> dict[str, dict[str, Any]]:
        payload = self._load_payload()
        raw = payload.get("reviewer_accounts", {})
        if not isinstance(raw, dict):
            return {}
        out: dict[str, dict[str, Any]] = {}
        for user_id, account in raw.items():
            uid = self._normalize_user_id(str(user_id))
            if not uid:
                continue
            if not isinstance(account, dict):
                out[uid] = {
                    "reviewer_id": uid,
                    "created_at": 0.0,
                    "created_by": "",
                    "source_invite": "",
                }
                continue
            out[uid] = {
                "reviewer_id": uid,
                "created_at": float(account.get("created_at", 0.0) or 0.0),
                "created_by": str(account.get("created_by", "") or "").strip(),
                "source_invite": str(account.get("source_invite", "") or "").strip(),
            }
        return out

    def _save_accounts(self, accounts: dict[str, dict[str, Any]]) -> None:
        payload = self._load_payload()
        payload["reviewer_accounts"] = accounts
        self._save_payload(payload)

    def _load_keys(self) -> dict[str, list[dict[str, Any]]]:
        payload = self._load_payload()
        raw = payload.get("reviewer_device_keys", {})
        if not isinstance(raw, dict):
            return {}
        out: dict[str, list[dict[str, Any]]] = {}
        for uid, devices in raw.items():
            user_id = self._normalize_user_id(str(uid))
            if not user_id:
                continue
            normalized_devices: list[dict[str, Any]] = []
            if isinstance(devices, list):
                for item in devices:
                    if not isinstance(item, dict):
                        continue
                    device_id = str(item.get("device_id", "") or "").strip()
                    key = str(item.get("key", "") or "").strip()
                    if not device_id or not key:
                        continue
                    normalized_devices.append(
                        {
                            "device_id": device_id,
                            "key": key,
                            "label": str(item.get("label", "") or "").strip(),
                            "registered_at": float(item.get("registered_at", 0.0) or 0.0),
                            "last_used_at": float(item.get("last_used_at", 0.0) or 0.0),
                        }
                    )
            out[user_id] = normalized_devices
        return out

    def _save_keys(self, keys: dict[str, list[dict[str, Any]]]) -> None:
        payload = self._load_payload()
        payload["reviewer_device_keys"] = keys
        self._save_payload(payload)

    def _load_invites(self) -> dict[str, dict[str, Any]]:
        payload = self._load_payload()
        raw = payload.get("reviewer_invites", {})
        if not isinstance(raw, dict):
            return {}
        out: dict[str, dict[str, Any]] = {}
        for code, row in raw.items():
            invite_code = str(code or "").strip()
            if not invite_code or not isinstance(row, dict):
                continue
            out[invite_code] = {
                "code": invite_code,
                "issued_by": str(row.get("issued_by", "") or "").strip(),
                "issued_at": float(row.get("issued_at", 0.0) or 0.0),
                "expires_at": float(row.get("expires_at", 0.0) or 0.0),
                "status": str(row.get("status", "issued") or "issued").strip().lower(),
                "redeemed_by": str(row.get("redeemed_by", "") or "").strip(),
                "redeemed_at": float(row.get("redeemed_at", 0.0) or 0.0),
            }
        return out

    def _save_invites(self, invites: dict[str, dict[str, Any]]) -> None:
        payload = self._load_payload()
        payload["reviewer_invites"] = invites
        self._save_payload(payload)

    def create_invite(self, admin_id: str, expires_in_seconds: int | None = None) -> dict[str, Any]:
        issuer = self._normalize_user_id(admin_id)
        if not issuer:
            return {"error": "admin_id_required"}
        ttl = int(expires_in_seconds or self.DEFAULT_INVITE_TTL_SECONDS)
        ttl = max(60, ttl)
        now = float(time.time())
        code = secrets.token_urlsafe(24)
        invites = self._load_invites()
        invites[code] = {
            "code": code,
            "issued_by": issuer,
            "issued_at": now,
            "expires_at": now + float(ttl),
            "status": "issued",
            "redeemed_by": "",
            "redeemed_at": 0.0,
        }
        self._save_invites(invites)
        return {
            "status": "invite_issued",
            "invite_code": code,
            "issued_by": issuer,
            "expires_in_seconds": ttl,
            "expires_at": now + float(ttl),
        }

    def list_invites(self, status: str = "") -> list[dict[str, Any]]:
        now = float(time.time())
        requested = str(status or "").strip().lower()
        rows: list[dict[str, Any]] = []
        invites = self._load_invites()
        changed = False
        for code, invite in invites.items():
            row = dict(invite)
            if row.get("status") == "issued" and float(row.get("expires_at", 0.0) or 0.0) > 0 and now >= float(
                row.get("expires_at", 0.0) or 0.0
            ):
                row["status"] = "expired"
                invites[code] = row
                changed = True
            if requested and row.get("status") != requested:
                continue
            rows.append(row)
        if changed:
            self._save_invites(invites)
        rows.sort(key=lambda item: float(item.get("issued_at", 0.0) or 0.0), reverse=True)
        return rows

    def redeem_invite(self, invite_code: str, reviewer_id: str) -> dict[str, Any]:
        code = str(invite_code or "").strip()
        uid = self._normalize_user_id(reviewer_id)
        if not code:
            return {"error": "invite_code_required"}
        if not uid:
            return {"error": "reviewer_id_required"}

        invites = self._load_invites()
        invite = invites.get(code)
        if not isinstance(invite, dict):
            return {"error": "invite_not_found"}

        now = float(time.time())
        status = str(invite.get("status", "issued") or "issued").strip().lower()
        expires_at = float(invite.get("expires_at", 0.0) or 0.0)
        if status == "redeemed":
            return {"error": "invite_already_redeemed", "reviewer_id": str(invite.get("redeemed_by", "") or "")}
        if expires_at > 0 and now >= expires_at:
            invite["status"] = "expired"
            invites[code] = invite
            self._save_invites(invites)
            return {"error": "invite_expired"}

        accounts = self._load_accounts()
        created = uid not in accounts
        if created:
            accounts[uid] = {
                "reviewer_id": uid,
                "created_at": now,
                "created_by": str(invite.get("issued_by", "") or "").strip(),
                "source_invite": code,
            }
            self._save_accounts(accounts)

        invite["status"] = "redeemed"
        invite["redeemed_by"] = uid
        invite["redeemed_at"] = now
        invites[code] = invite
        self._save_invites(invites)

        return {
            "status": "invite_redeemed",
            "reviewer_id": uid,
            "created": created,
        }

    def is_reviewer(self, user_id: str) -> bool:
        uid = self._normalize_user_id(user_id)
        if not uid:
            return False
        accounts = self._load_accounts()
        return uid in accounts

    def list_reviewers(self) -> list[dict[str, Any]]:
        accounts = self._load_accounts()
        keys = self._load_keys()
        rows: list[dict[str, Any]] = []
        for uid, account in accounts.items():
            rows.append(
                {
                    "reviewer_id": uid,
                    "created_at": float(account.get("created_at", 0.0) or 0.0),
                    "created_by": str(account.get("created_by", "") or "").strip(),
                    "source_invite": str(account.get("source_invite", "") or "").strip(),
                    "device_count": len(keys.get(uid, [])),
                }
            )
        rows.sort(key=lambda item: (float(item.get("created_at", 0.0) or 0.0), str(item.get("reviewer_id", ""))), reverse=True)
        return rows

    def register_device(self, user_id: str, label: str = "") -> dict[str, Any]:
        """Register a new device for a reviewer account under the configured limit."""
        uid = self._normalize_user_id(user_id)
        if not uid:
            return {"error": "reviewer_id_required"}
        if not self.is_reviewer(uid):
            return {"error": "reviewer_not_registered", "reviewer_id": uid}

        all_keys = self._load_keys()
        user_devices = all_keys.get(uid, [])
        if len(user_devices) >= self.max_devices:
            return {"error": "device_limit_exceeded", "max_devices": self.max_devices}

        now = float(time.time())
        device_id = secrets.token_hex(8)
        key = secrets.token_urlsafe(32)
        device = {
            "device_id": device_id,
            "key": key,
            "label": str(label or "").strip(),
            "registered_at": now,
            "last_used_at": 0.0,
        }
        user_devices.append(device)
        all_keys[uid] = user_devices
        self._save_keys(all_keys)

        return {
            "status": "registered",
            "reviewer_id": uid,
            "device_id": device_id,
            "device_key": key,
            "label": str(device.get("label", "") or "").strip(),
            "max_devices": self.max_devices,
        }

    def list_devices(self, user_id: str) -> list[dict[str, Any]]:
        """List active devices for a reviewer (without sensitive key values)."""
        uid = self._normalize_user_id(user_id)
        if not uid:
            return []

        all_keys = self._load_keys()
        user_devices = all_keys.get(uid, [])
        return [
            {
                "device_id": str(item.get("device_id", "") or "").strip(),
                "label": str(item.get("label", "") or "").strip(),
                "registered_at": float(item.get("registered_at", 0.0) or 0.0),
                "last_used_at": float(item.get("last_used_at", 0.0) or 0.0),
            }
            for item in user_devices
            if str(item.get("device_id", "") or "").strip()
        ]

    def revoke_device(self, user_id: str, device_id: str) -> bool:
        """Revoke a specific reviewer device key."""
        uid = self._normalize_user_id(user_id)
        did = str(device_id or "").strip()
        if not uid or not did:
            return False

        all_keys = self._load_keys()
        user_devices = all_keys.get(uid, [])
        initial_len = len(user_devices)
        filtered_devices = [item for item in user_devices if str(item.get("device_id", "")) != did]
        if len(filtered_devices) >= initial_len:
            return False
        all_keys[uid] = filtered_devices
        self._save_keys(all_keys)
        return True

    def revoke_all_devices(self, user_id: str) -> int:
        uid = self._normalize_user_id(user_id)
        if not uid:
            return 0
        all_keys = self._load_keys()
        count = len(all_keys.get(uid, []))
        all_keys[uid] = []
        self._save_keys(all_keys)
        return count

    def resolve_device(self, user_id: str, key: str) -> dict[str, Any] | None:
        uid = self._normalize_user_id(user_id)
        k = str(key or "").strip()
        if not uid or not k:
            return None
        all_keys = self._load_keys()
        user_devices = all_keys.get(uid, [])
        for item in user_devices:
            item_key = str(item.get("key", "") or "").strip()
            if item_key and secrets.compare_digest(item_key, k):
                return dict(item)
        return None

    def validate_device(self, user_id: str, key: str) -> bool:
        """Check whether the given device key is currently valid for this reviewer."""
        return self.resolve_device(user_id=user_id, key=key) is not None

    def mark_device_used(self, user_id: str, device_id: str) -> None:
        uid = self._normalize_user_id(user_id)
        did = str(device_id or "").strip()
        if not uid or not did:
            return
        all_keys = self._load_keys()
        user_devices = all_keys.get(uid, [])
        changed = False
        now = float(time.time())
        for item in user_devices:
            if str(item.get("device_id", "") or "").strip() == did:
                item["last_used_at"] = now
                changed = True
                break
        if changed:
            all_keys[uid] = user_devices
            self._save_keys(all_keys)
