"""Identity-backed reviewer lifecycle, credential hashing, and WebUI sessions."""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import time
from typing import Any, Protocol

from ..infrastructure.identity_repository import (
    IdentityRepository,
    JsonIdentityRepository,
    SqliteIdentityRepository,
)
from ..infrastructure.sqlite_state_store import SqliteStateStore


class StateStore(Protocol):
    def load(self, default: dict[str, Any]) -> dict[str, Any]: ...
    def save(self, payload: dict[str, Any]) -> None: ...


class _MemoryStateStore:
    def __init__(self):
        self.payload: dict[str, Any] = {}

    def load(self, default: dict[str, Any]) -> dict[str, Any]:
        if not self.payload:
            return dict(default)
        return dict(self.payload)

    def save(self, payload: dict[str, Any]) -> None:
        self.payload = dict(payload)


class ReviewerAuthService:
    """Manages reviewer identities, hashed credentials, device keys, and WebUI sessions."""

    DEFAULT_INVITE_TTL_SECONDS = 3600
    DEFAULT_PBKDF2_ITERATIONS = 310_000
    PASSWORD_CREDENTIAL_TYPE = "bootstrap_password"
    DEVICE_CREDENTIAL_TYPE = "reviewer_device_key"
    PASSWORD_SOURCE = "local_webui_auth"
    SESSION_REVOKE_REASON_EXPIRED = "expired"

    def __init__(
        self,
        state_store: StateStore | None = None,
        *,
        repository: IdentityRepository | None = None,
        legacy_state_store: StateStore | None = None,
        max_devices: int = 3,
    ):
        self.max_devices = max(1, int(max_devices or 1))
        self.repository = self._build_repository(state_store=state_store, repository=repository)
        self._users: dict[str, dict[str, Any]] = {}
        self._credentials: dict[str, dict[str, Any]] = {}
        self._sessions: dict[str, dict[str, Any]] = {}
        self._reviewer_devices: dict[str, dict[str, Any]] = {}
        self._reviewer_invites: dict[str, dict[str, Any]] = {}
        self._session_ids_by_token_hash: dict[str, str] = {}
        self._session_ids_by_key: dict[str, str] = {}
        self._load_state()
        self._import_legacy_state_if_needed(state_store)
        self._import_legacy_state_if_needed(legacy_state_store)

    @staticmethod
    def _build_repository(
        *,
        state_store: StateStore | None,
        repository: IdentityRepository | None,
    ) -> IdentityRepository:
        if repository is not None:
            return repository
        if state_store is None:
            return JsonIdentityRepository(_MemoryStateStore())
        if isinstance(state_store, SqliteStateStore):
            return SqliteIdentityRepository(state_store.db_path)
        return JsonIdentityRepository(state_store)  # type: ignore[arg-type]

    @staticmethod
    def _normalize_role(role: str) -> str:
        text = str(role or "").strip().lower()
        if text in {"member", "user"}:
            return "member"
        if text in {"reviewer", "admin"}:
            return text
        return "member"

    @staticmethod
    def _normalize_user_id(value: str) -> str:
        return str(value or "").strip()

    @classmethod
    def _bootstrap_user_id(cls, role: str) -> str:
        return f"__bootstrap__:{cls._normalize_role(role)}"

    @staticmethod
    def _token_hash(token: str) -> str:
        return hashlib.sha256(str(token or "").encode("utf-8")).hexdigest()

    @classmethod
    def _session_key(cls, role: str, *, subject: str = "", device_id: str = "") -> str:
        normalized_role = cls._normalize_role(role)
        if normalized_role == "reviewer":
            reviewer_id = str(subject or "").strip()
            reviewer_device_id = str(device_id or "").strip()
            return f"reviewer:{reviewer_id}:{reviewer_device_id or 'default-device'}"
        if normalized_role == "member":
            member_id = str(subject or "").strip()
            if member_id:
                return f"member:{member_id}"
        return normalized_role

    @classmethod
    def _hash_secret(
        cls,
        secret: str,
        *,
        salt: str = "",
        iterations: int | None = None,
    ) -> dict[str, Any]:
        normalized_secret = str(secret or "")
        rounds = max(120_000, int(iterations or cls.DEFAULT_PBKDF2_ITERATIONS))
        if salt:
            salt_bytes = base64.b64decode(salt.encode("ascii"))
        else:
            salt_bytes = secrets.token_bytes(16)
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            normalized_secret.encode("utf-8"),
            salt_bytes,
            rounds,
        )
        return {
            "algorithm": "pbkdf2_sha256",
            "iterations": rounds,
            "salt": base64.b64encode(salt_bytes).decode("ascii"),
            "secret_hash": base64.b64encode(digest).decode("ascii"),
        }

    @classmethod
    def _verify_secret(cls, secret: str, credential: dict[str, Any]) -> bool:
        if str(credential.get("algorithm", "pbkdf2_sha256") or "pbkdf2_sha256").strip().lower() != "pbkdf2_sha256":
            return False
        stored_hash = str(credential.get("secret_hash", "") or "").strip()
        stored_salt = str(credential.get("salt", "") or "").strip()
        if not stored_hash or not stored_salt:
            return False
        try:
            probe = cls._hash_secret(
                secret,
                salt=stored_salt,
                iterations=int(credential.get("iterations", cls.DEFAULT_PBKDF2_ITERATIONS) or cls.DEFAULT_PBKDF2_ITERATIONS),
            )
        except Exception:
            return False
        return hmac.compare_digest(probe["secret_hash"], stored_hash)

    def _load_state(self) -> None:
        payload = self.repository.load_state()
        self._users = {}
        self._credentials = {}
        self._sessions = {}
        self._reviewer_devices = {}
        self._reviewer_invites = {}

        for item in payload.get("users", []):
            if not isinstance(item, dict):
                continue
            user_id = self._normalize_user_id(str(item.get("user_id", "") or ""))
            if not user_id:
                continue
            self._users[user_id] = {
                "user_id": user_id,
                "role": self._normalize_role(str(item.get("role", "member") or "member")),
                "created_at": float(item.get("created_at", 0.0) or 0.0),
                "updated_at": float(item.get("updated_at", item.get("created_at", 0.0)) or 0.0),
                "created_by": str(item.get("created_by", "") or "").strip(),
                "source_invite": str(item.get("source_invite", "") or "").strip(),
                "status": str(item.get("status", "active") or "active").strip().lower() or "active",
            }

        for item in payload.get("credentials", []):
            if not isinstance(item, dict):
                continue
            credential_id = str(item.get("credential_id", "") or "").strip()
            if not credential_id:
                continue
            self._credentials[credential_id] = {
                "credential_id": credential_id,
                "user_id": self._normalize_user_id(str(item.get("user_id", "") or "")),
                "role": self._normalize_role(str(item.get("role", "member") or "member")),
                "credential_type": str(item.get("credential_type", "") or "").strip(),
                "device_id": str(item.get("device_id", "") or "").strip(),
                "algorithm": str(item.get("algorithm", "pbkdf2_sha256") or "pbkdf2_sha256").strip(),
                "iterations": int(item.get("iterations", self.DEFAULT_PBKDF2_ITERATIONS) or self.DEFAULT_PBKDF2_ITERATIONS),
                "salt": str(item.get("salt", "") or "").strip(),
                "secret_hash": str(item.get("secret_hash", "") or "").strip(),
                "created_at": float(item.get("created_at", 0.0) or 0.0),
                "updated_at": float(item.get("updated_at", item.get("created_at", 0.0)) or 0.0),
                "revoked_at": float(item.get("revoked_at", 0.0) or 0.0),
                "status": str(item.get("status", "active") or "active").strip().lower() or "active",
                "source": str(item.get("source", "") or "").strip(),
            }

        for item in payload.get("sessions", []):
            if not isinstance(item, dict):
                continue
            session_id = str(item.get("session_id", "") or "").strip()
            token_hash = str(item.get("token_hash", "") or "").strip()
            if not session_id or not token_hash:
                continue
            self._sessions[session_id] = {
                "session_id": session_id,
                "role": self._normalize_role(str(item.get("role", "member") or "member")),
                "user_id": self._normalize_user_id(str(item.get("user_id", "") or "")),
                "device_id": str(item.get("device_id", "") or "").strip(),
                "session_key": str(item.get("session_key", "") or "").strip(),
                "token_hash": token_hash,
                "issued_at": float(item.get("issued_at", 0.0) or 0.0),
                "expires_at": float(item.get("expires_at", 0.0) or 0.0),
                "last_seen_at": float(item.get("last_seen_at", item.get("issued_at", 0.0)) or 0.0),
                "revoked_at": float(item.get("revoked_at", 0.0) or 0.0),
                "revoke_reason": str(item.get("revoke_reason", "") or "").strip(),
            }

        for item in payload.get("reviewer_devices", []):
            if not isinstance(item, dict):
                continue
            device_id = str(item.get("device_id", "") or "").strip()
            if not device_id:
                continue
            self._reviewer_devices[device_id] = {
                "device_id": device_id,
                "reviewer_id": self._normalize_user_id(str(item.get("reviewer_id", "") or "")),
                "credential_id": str(item.get("credential_id", "") or "").strip(),
                "label": str(item.get("label", "") or "").strip(),
                "registered_at": float(item.get("registered_at", 0.0) or 0.0),
                "last_used_at": float(item.get("last_used_at", 0.0) or 0.0),
                "revoked_at": float(item.get("revoked_at", 0.0) or 0.0),
            }

        for item in payload.get("reviewer_invites", []):
            if not isinstance(item, dict):
                continue
            code = str(item.get("code", "") or "").strip()
            if not code:
                continue
            self._reviewer_invites[code] = {
                "code": code,
                "issued_by": str(item.get("issued_by", "") or "").strip(),
                "issued_at": float(item.get("issued_at", 0.0) or 0.0),
                "expires_at": float(item.get("expires_at", 0.0) or 0.0),
                "status": str(item.get("status", "issued") or "issued").strip().lower(),
                "redeemed_by": str(item.get("redeemed_by", "") or "").strip(),
                "redeemed_at": float(item.get("redeemed_at", 0.0) or 0.0),
                "revoked_by": str(item.get("revoked_by", "") or "").strip(),
                "revoked_at": float(item.get("revoked_at", 0.0) or 0.0),
            }

        self._rebuild_session_indexes()

    def _flush_state(self) -> None:
        self.repository.save_state(
            {
                "users": sorted(
                    self._users.values(),
                    key=lambda item: (
                        float(item.get("created_at", 0.0) or 0.0),
                        str(item.get("user_id", "") or ""),
                    ),
                ),
                "credentials": sorted(
                    self._credentials.values(),
                    key=lambda item: (
                        float(item.get("created_at", 0.0) or 0.0),
                        str(item.get("credential_id", "") or ""),
                    ),
                ),
                "sessions": sorted(
                    self._sessions.values(),
                    key=lambda item: (
                        float(item.get("issued_at", 0.0) or 0.0),
                        str(item.get("session_id", "") or ""),
                    ),
                ),
                "reviewer_devices": sorted(
                    self._reviewer_devices.values(),
                    key=lambda item: (
                        float(item.get("registered_at", 0.0) or 0.0),
                        str(item.get("device_id", "") or ""),
                    ),
                ),
                "reviewer_invites": sorted(
                    self._reviewer_invites.values(),
                    key=lambda item: (
                        float(item.get("issued_at", 0.0) or 0.0),
                        str(item.get("code", "") or ""),
                    ),
                ),
            }
        )
        self._rebuild_session_indexes()

    def _rebuild_session_indexes(self) -> None:
        self._session_ids_by_token_hash = {}
        self._session_ids_by_key = {}
        for session_id, session in self._sessions.items():
            token_hash = str(session.get("token_hash", "") or "").strip()
            if token_hash:
                self._session_ids_by_token_hash[token_hash] = session_id
            if self._session_active(session, now=time.time()):
                session_key = str(session.get("session_key", "") or "").strip()
                if session_key:
                    self._session_ids_by_key[session_key] = session_id

    def _session_active(self, session: dict[str, Any], *, now: float) -> bool:
        return (
            float(session.get("revoked_at", 0.0) or 0.0) <= 0
            and float(session.get("expires_at", 0.0) or 0.0) > now
        )

    def _prune_expired_sessions(self) -> bool:
        changed = False
        now = float(time.time())
        for session in self._sessions.values():
            if float(session.get("revoked_at", 0.0) or 0.0) > 0:
                continue
            expires_at = float(session.get("expires_at", 0.0) or 0.0)
            if expires_at > 0 and now >= expires_at:
                session["revoked_at"] = now
                session["revoke_reason"] = self.SESSION_REVOKE_REASON_EXPIRED
                changed = True
        if changed:
            self._flush_state()
        return changed

    def _ensure_user(
        self,
        *,
        user_id: str,
        role: str,
        created_by: str = "",
        source_invite: str = "",
    ) -> dict[str, Any]:
        uid = self._normalize_user_id(user_id)
        if not uid:
            raise ValueError("user_id_required")
        row = self._users.get(uid)
        now = float(time.time())
        if row is None:
            row = {
                "user_id": uid,
                "role": self._normalize_role(role),
                "created_at": now,
                "updated_at": now,
                "created_by": str(created_by or "").strip(),
                "source_invite": str(source_invite or "").strip(),
                "status": "active",
            }
            self._users[uid] = row
            return row
        row["role"] = self._normalize_role(role)
        row["updated_at"] = now
        if created_by and not str(row.get("created_by", "") or "").strip():
            row["created_by"] = str(created_by or "").strip()
        if source_invite and not str(row.get("source_invite", "") or "").strip():
            row["source_invite"] = str(source_invite or "").strip()
        if str(row.get("status", "active") or "active").strip().lower() != "active":
            row["status"] = "active"
        return row

    def _active_credentials(
        self,
        *,
        user_id: str,
        credential_type: str,
        role: str = "",
        device_id: str = "",
    ) -> list[dict[str, Any]]:
        uid = self._normalize_user_id(user_id)
        normalized_role = self._normalize_role(role) if role else ""
        target_device_id = str(device_id or "").strip()
        rows: list[dict[str, Any]] = []
        for item in self._credentials.values():
            if str(item.get("status", "active") or "active").strip().lower() != "active":
                continue
            if float(item.get("revoked_at", 0.0) or 0.0) > 0:
                continue
            if self._normalize_user_id(str(item.get("user_id", "") or "")) != uid:
                continue
            if str(item.get("credential_type", "") or "").strip() != credential_type:
                continue
            if normalized_role and self._normalize_role(str(item.get("role", "") or "")) != normalized_role:
                continue
            if target_device_id and str(item.get("device_id", "") or "").strip() != target_device_id:
                continue
            rows.append(item)
        rows.sort(
            key=lambda item: (
                float(item.get("created_at", 0.0) or 0.0),
                str(item.get("credential_id", "") or ""),
            ),
            reverse=True,
        )
        return rows

    def _revoke_credential(self, credential: dict[str, Any], *, reason: str = "") -> None:
        if float(credential.get("revoked_at", 0.0) or 0.0) > 0:
            return
        now = float(time.time())
        credential["revoked_at"] = now
        credential["updated_at"] = now
        credential["status"] = "revoked"
        if reason:
            credential["source"] = str(reason or "").strip()

    def _create_credential(
        self,
        *,
        user_id: str,
        role: str,
        credential_type: str,
        secret: str,
        device_id: str = "",
        source: str = "",
    ) -> dict[str, Any]:
        now = float(time.time())
        credential_id = secrets.token_hex(16)
        hashed = self._hash_secret(secret)
        row = {
            "credential_id": credential_id,
            "user_id": self._normalize_user_id(user_id),
            "role": self._normalize_role(role),
            "credential_type": str(credential_type or "").strip(),
            "device_id": str(device_id or "").strip(),
            "algorithm": hashed["algorithm"],
            "iterations": int(hashed["iterations"] or self.DEFAULT_PBKDF2_ITERATIONS),
            "salt": str(hashed["salt"] or ""),
            "secret_hash": str(hashed["secret_hash"] or ""),
            "created_at": now,
            "updated_at": now,
            "revoked_at": 0.0,
            "status": "active",
            "source": str(source or "").strip(),
        }
        self._credentials[credential_id] = row
        return row

    def _import_legacy_state_if_needed(self, legacy_state_store: StateStore | None) -> None:
        if legacy_state_store is None:
            return
        if self._users or self._credentials or self._reviewer_devices or self._reviewer_invites:
            return
        payload = legacy_state_store.load(default={})
        if not isinstance(payload, dict):
            return
        changed = False

        if any(
            isinstance(payload.get(key), list)
            for key in ("users", "credentials", "sessions", "reviewer_devices", "reviewer_invites")
        ):
            identity_users = payload.get("users", [])
            if isinstance(identity_users, list):
                for item in identity_users:
                    if not isinstance(item, dict):
                        continue
                    user_id = self._normalize_user_id(str(item.get("user_id", "") or ""))
                    if not user_id:
                        continue
                    self._users[user_id] = {
                        "user_id": user_id,
                        "role": self._normalize_role(str(item.get("role", "member") or "member")),
                        "created_at": float(item.get("created_at", 0.0) or 0.0),
                        "updated_at": float(item.get("updated_at", item.get("created_at", 0.0)) or 0.0),
                        "created_by": str(item.get("created_by", "") or "").strip(),
                        "source_invite": str(item.get("source_invite", "") or "").strip(),
                        "status": str(item.get("status", "active") or "active").strip().lower() or "active",
                    }
                    changed = True

            identity_credentials = payload.get("credentials", [])
            if isinstance(identity_credentials, list):
                for item in identity_credentials:
                    if not isinstance(item, dict):
                        continue
                    credential_id = str(item.get("credential_id", "") or "").strip()
                    if not credential_id:
                        continue
                    self._credentials[credential_id] = {
                        "credential_id": credential_id,
                        "user_id": self._normalize_user_id(str(item.get("user_id", "") or "")),
                        "role": self._normalize_role(str(item.get("role", "member") or "member")),
                        "credential_type": str(item.get("credential_type", "") or "").strip(),
                        "device_id": str(item.get("device_id", "") or "").strip(),
                        "algorithm": str(item.get("algorithm", "pbkdf2_sha256") or "pbkdf2_sha256").strip(),
                        "iterations": int(item.get("iterations", self.DEFAULT_PBKDF2_ITERATIONS) or self.DEFAULT_PBKDF2_ITERATIONS),
                        "salt": str(item.get("salt", "") or "").strip(),
                        "secret_hash": str(item.get("secret_hash", "") or "").strip(),
                        "created_at": float(item.get("created_at", 0.0) or 0.0),
                        "updated_at": float(item.get("updated_at", item.get("created_at", 0.0)) or 0.0),
                        "revoked_at": float(item.get("revoked_at", 0.0) or 0.0),
                        "status": str(item.get("status", "active") or "active").strip().lower() or "active",
                        "source": str(item.get("source", "") or "").strip(),
                    }
                    changed = True

            identity_sessions = payload.get("sessions", [])
            if isinstance(identity_sessions, list):
                for item in identity_sessions:
                    if not isinstance(item, dict):
                        continue
                    session_id = str(item.get("session_id", "") or "").strip()
                    token_hash = str(item.get("token_hash", "") or "").strip()
                    if not session_id or not token_hash:
                        continue
                    self._sessions[session_id] = {
                        "session_id": session_id,
                        "role": self._normalize_role(str(item.get("role", "member") or "member")),
                        "user_id": self._normalize_user_id(str(item.get("user_id", "") or "")),
                        "device_id": str(item.get("device_id", "") or "").strip(),
                        "session_key": str(item.get("session_key", "") or "").strip(),
                        "token_hash": token_hash,
                        "issued_at": float(item.get("issued_at", 0.0) or 0.0),
                        "expires_at": float(item.get("expires_at", 0.0) or 0.0),
                        "last_seen_at": float(item.get("last_seen_at", item.get("issued_at", 0.0)) or 0.0),
                        "revoked_at": float(item.get("revoked_at", 0.0) or 0.0),
                        "revoke_reason": str(item.get("revoke_reason", "") or "").strip(),
                    }
                    changed = True

            identity_devices = payload.get("reviewer_devices", [])
            if isinstance(identity_devices, list):
                for item in identity_devices:
                    if not isinstance(item, dict):
                        continue
                    device_id = str(item.get("device_id", "") or "").strip()
                    if not device_id:
                        continue
                    self._reviewer_devices[device_id] = {
                        "device_id": device_id,
                        "reviewer_id": self._normalize_user_id(str(item.get("reviewer_id", "") or "")),
                        "credential_id": str(item.get("credential_id", "") or "").strip(),
                        "label": str(item.get("label", "") or "").strip(),
                        "registered_at": float(item.get("registered_at", 0.0) or 0.0),
                        "last_used_at": float(item.get("last_used_at", 0.0) or 0.0),
                        "revoked_at": float(item.get("revoked_at", 0.0) or 0.0),
                    }
                    changed = True

            identity_invites = payload.get("reviewer_invites", [])
            if isinstance(identity_invites, list):
                for item in identity_invites:
                    if not isinstance(item, dict):
                        continue
                    code = str(item.get("code", "") or "").strip()
                    if not code:
                        continue
                    self._reviewer_invites[code] = {
                        "code": code,
                        "issued_by": str(item.get("issued_by", "") or "").strip(),
                        "issued_at": float(item.get("issued_at", 0.0) or 0.0),
                        "expires_at": float(item.get("expires_at", 0.0) or 0.0),
                        "status": str(item.get("status", "issued") or "issued").strip().lower(),
                        "redeemed_by": str(item.get("redeemed_by", "") or "").strip(),
                        "redeemed_at": float(item.get("redeemed_at", 0.0) or 0.0),
                        "revoked_by": str(item.get("revoked_by", "") or "").strip(),
                        "revoked_at": float(item.get("revoked_at", 0.0) or 0.0),
                    }
                    changed = True

            if changed:
                self._flush_state()
            return

        raw_accounts = payload.get("reviewer_accounts", {})
        if isinstance(raw_accounts, dict):
            for user_id, account in raw_accounts.items():
                uid = self._normalize_user_id(str(user_id))
                if not uid:
                    continue
                row = account if isinstance(account, dict) else {}
                created_at = float(row.get("created_at", 0.0) or 0.0)
                self._users[uid] = {
                    "user_id": uid,
                    "role": "reviewer",
                    "created_at": created_at,
                    "updated_at": created_at,
                    "created_by": str(row.get("created_by", "") or "").strip(),
                    "source_invite": str(row.get("source_invite", "") or "").strip(),
                    "status": "active",
                }
                changed = True

        raw_invites = payload.get("reviewer_invites", {})
        if isinstance(raw_invites, dict):
            for code, item in raw_invites.items():
                invite_code = str(code or "").strip()
                if not invite_code or not isinstance(item, dict):
                    continue
                self._reviewer_invites[invite_code] = {
                    "code": invite_code,
                    "issued_by": str(item.get("issued_by", "") or "").strip(),
                    "issued_at": float(item.get("issued_at", 0.0) or 0.0),
                    "expires_at": float(item.get("expires_at", 0.0) or 0.0),
                    "status": str(item.get("status", "issued") or "issued").strip().lower(),
                    "redeemed_by": str(item.get("redeemed_by", "") or "").strip(),
                    "redeemed_at": float(item.get("redeemed_at", 0.0) or 0.0),
                    "revoked_by": str(item.get("revoked_by", "") or "").strip(),
                    "revoked_at": float(item.get("revoked_at", 0.0) or 0.0),
                }
                changed = True

        raw_keys = payload.get("reviewer_device_keys", {})
        if isinstance(raw_keys, dict):
            for user_id, devices in raw_keys.items():
                uid = self._normalize_user_id(str(user_id))
                if not uid or not isinstance(devices, list):
                    continue
                if uid not in self._users:
                    self._users[uid] = {
                        "user_id": uid,
                        "role": "reviewer",
                        "created_at": 0.0,
                        "updated_at": 0.0,
                        "created_by": "",
                        "source_invite": "",
                        "status": "active",
                    }
                for item in devices:
                    if not isinstance(item, dict):
                        continue
                    device_id = str(item.get("device_id", "") or "").strip()
                    key = str(item.get("key", "") or "").strip()
                    if not device_id or not key:
                        continue
                    credential = self._create_credential(
                        user_id=uid,
                        role="reviewer",
                        credential_type=self.DEVICE_CREDENTIAL_TYPE,
                        secret=key,
                        device_id=device_id,
                        source="legacy_reviewer_auth_state",
                    )
                    self._reviewer_devices[device_id] = {
                        "device_id": device_id,
                        "reviewer_id": uid,
                        "credential_id": credential["credential_id"],
                        "label": str(item.get("label", "") or "").strip(),
                        "registered_at": float(item.get("registered_at", 0.0) or 0.0),
                        "last_used_at": float(item.get("last_used_at", 0.0) or 0.0),
                        "revoked_at": 0.0,
                    }
                    changed = True

        if changed:
            self._flush_state()

    def sync_bootstrap_password(self, role: str, password: str) -> dict[str, Any]:
        normalized_role = self._normalize_role(role)
        secret = str(password or "")
        if not secret:
            return {"status": "skipped", "role": normalized_role}
        user_id = self._bootstrap_user_id(normalized_role)
        self._ensure_user(user_id=user_id, role=normalized_role, created_by="system")
        active = self._active_credentials(
            user_id=user_id,
            credential_type=self.PASSWORD_CREDENTIAL_TYPE,
            role=normalized_role,
        )
        for credential in active:
            if self._verify_secret(secret, credential):
                return {
                    "status": "unchanged",
                    "role": normalized_role,
                    "credential_id": str(credential.get("credential_id", "") or ""),
                }
        for credential in active:
            self._revoke_credential(credential, reason=f"{self.PASSWORD_SOURCE}:rotated")
        created = self._create_credential(
            user_id=user_id,
            role=normalized_role,
            credential_type=self.PASSWORD_CREDENTIAL_TYPE,
            secret=secret,
            source=self.PASSWORD_SOURCE,
        )
        self._flush_state()
        return {
            "status": "rotated" if active else "created",
            "role": normalized_role,
            "credential_id": str(created.get("credential_id", "") or ""),
        }

    def verify_bootstrap_password(self, role: str, password: str) -> bool:
        normalized_role = self._normalize_role(role)
        user_id = self._bootstrap_user_id(normalized_role)
        for credential in self._active_credentials(
            user_id=user_id,
            credential_type=self.PASSWORD_CREDENTIAL_TYPE,
            role=normalized_role,
        ):
            if self._verify_secret(password, credential):
                return True
        return False

    def has_bootstrap_password(self, role: str) -> bool:
        normalized_role = self._normalize_role(role)
        user_id = self._bootstrap_user_id(normalized_role)
        return bool(
            self._active_credentials(
                user_id=user_id,
                credential_type=self.PASSWORD_CREDENTIAL_TYPE,
                role=normalized_role,
            )
        )

    def issue_session(
        self,
        *,
        role: str,
        subject: str = "",
        device_id: str = "",
        ttl_seconds: int,
    ) -> dict[str, Any]:
        normalized_role = self._normalize_role(role)
        normalized_subject = self._normalize_user_id(subject)
        normalized_device_id = str(device_id or "").strip()
        if normalized_role == "reviewer" and (not normalized_subject or not normalized_device_id):
            raise ValueError("reviewer_session_requires_device")
        session_key = self._session_key(
            normalized_role,
            subject=normalized_subject,
            device_id=normalized_device_id,
        )
        now = float(time.time())
        current_session_id = self._session_ids_by_key.get(session_key)
        if current_session_id:
            row = self._sessions.get(current_session_id)
            if isinstance(row, dict):
                row["revoked_at"] = now
                row["revoke_reason"] = "superseded"
        token = secrets.token_hex(24)
        session_id = secrets.token_hex(12)
        self._sessions[session_id] = {
            "session_id": session_id,
            "role": normalized_role,
            "user_id": normalized_subject,
            "device_id": normalized_device_id,
            "session_key": session_key,
            "token_hash": self._token_hash(token),
            "issued_at": now,
            "expires_at": now + float(max(1, int(ttl_seconds or 1))),
            "last_seen_at": now,
            "revoked_at": 0.0,
            "revoke_reason": "",
        }
        self._flush_state()
        return {
            "token": token,
            "session_id": session_id,
            "role": normalized_role,
            "user_id": normalized_subject,
            "device_id": normalized_device_id,
            "issued_at": now,
            "expires_at": now + float(max(1, int(ttl_seconds or 1))),
        }

    def resolve_session(self, token: str, *, touch: bool = False) -> dict[str, Any] | None:
        text = str(token or "").strip()
        if not text:
            return None
        self._prune_expired_sessions()
        session_id = self._session_ids_by_token_hash.get(self._token_hash(text))
        if not session_id:
            return None
        session = self._sessions.get(session_id)
        if not isinstance(session, dict):
            return None
        now = float(time.time())
        if not self._session_active(session, now=now):
            return None
        if touch:
            last_seen_at = float(session.get("last_seen_at", 0.0) or 0.0)
            if now - last_seen_at >= 30.0:
                session["last_seen_at"] = now
                self._flush_state()
        return dict(session)

    def revoke_session_token(self, token: str, *, reason: str = "logout") -> bool:
        text = str(token or "").strip()
        if not text:
            return False
        session_id = self._session_ids_by_token_hash.get(self._token_hash(text))
        if not session_id:
            return False
        return self.revoke_session(session_id=session_id, reason=reason)

    def revoke_session(self, *, session_id: str, reason: str = "manual") -> bool:
        sid = str(session_id or "").strip()
        if not sid:
            return False
        session = self._sessions.get(sid)
        if not isinstance(session, dict):
            return False
        if float(session.get("revoked_at", 0.0) or 0.0) > 0:
            return False
        session["revoked_at"] = float(time.time())
        session["revoke_reason"] = str(reason or "manual").strip()
        self._flush_state()
        return True

    def list_reviewer_sessions(self, reviewer_id: str, *, device_id: str = "") -> list[dict[str, Any]]:
        self._prune_expired_sessions()
        uid = self._normalize_user_id(reviewer_id)
        target_device_id = str(device_id or "").strip()
        rows: list[dict[str, Any]] = []
        now = float(time.time())
        for item in self._sessions.values():
            if self._normalize_role(str(item.get("role", "") or "")) != "reviewer":
                continue
            if self._normalize_user_id(str(item.get("user_id", "") or "")) != uid:
                continue
            if not self._session_active(item, now=now):
                continue
            session_device_id = str(item.get("device_id", "") or "").strip()
            if target_device_id and session_device_id != target_device_id:
                continue
            rows.append(
                {
                    "session_id": str(item.get("session_id", "") or ""),
                    "reviewer_id": uid,
                    "device_id": session_device_id,
                    "issued_at": float(item.get("issued_at", 0.0) or 0.0),
                    "expires_at": float(item.get("expires_at", 0.0) or 0.0),
                    "last_seen_at": float(item.get("last_seen_at", 0.0) or 0.0),
                    "remaining_seconds": max(0, int(float(item.get("expires_at", 0.0) or 0.0) - now)),
                }
            )
        rows.sort(
            key=lambda item: (
                float(item.get("issued_at", 0.0) or 0.0),
                str(item.get("session_id", "") or ""),
            ),
            reverse=True,
        )
        return rows

    def revoke_reviewer_sessions(
        self,
        reviewer_id: str,
        *,
        device_id: str = "",
        session_id: str = "",
        exclude_session_id: str = "",
    ) -> dict[str, Any]:
        self._prune_expired_sessions()
        uid = self._normalize_user_id(reviewer_id)
        target_device_id = str(device_id or "").strip()
        target_session_id = str(session_id or "").strip()
        excluded = str(exclude_session_id or "").strip()
        revoked_sessions = 0
        revoked_device_ids: set[str] = set()
        revoked_session_ids: set[str] = set()
        if not uid:
            return {
                "reviewer_id": "",
                "device_id": target_device_id,
                "session_id": target_session_id,
                "revoked_sessions": 0,
                "revoked_device_ids": [],
                "revoked_session_ids": [],
            }
        for item in self._sessions.values():
            if self._normalize_role(str(item.get("role", "") or "")) != "reviewer":
                continue
            if self._normalize_user_id(str(item.get("user_id", "") or "")) != uid:
                continue
            current_session_id = str(item.get("session_id", "") or "").strip()
            if excluded and current_session_id == excluded:
                continue
            if target_session_id and current_session_id != target_session_id:
                continue
            current_device_id = str(item.get("device_id", "") or "").strip()
            if target_device_id and current_device_id != target_device_id:
                continue
            if float(item.get("revoked_at", 0.0) or 0.0) > 0:
                continue
            item["revoked_at"] = float(time.time())
            item["revoke_reason"] = "admin_revoke"
            revoked_sessions += 1
            if current_device_id:
                revoked_device_ids.add(current_device_id)
            if current_session_id:
                revoked_session_ids.add(current_session_id)
        if revoked_sessions:
            self._flush_state()
        return {
            "reviewer_id": uid,
            "device_id": target_device_id,
            "session_id": target_session_id,
            "revoked_sessions": revoked_sessions,
            "revoked_device_ids": sorted(revoked_device_ids),
            "revoked_session_ids": sorted(revoked_session_ids),
        }

    def create_invite(self, admin_id: str, expires_in_seconds: int | None = None) -> dict[str, Any]:
        issuer = self._normalize_user_id(admin_id)
        if not issuer:
            return {"error": "admin_id_required"}
        ttl = max(60, int(expires_in_seconds or self.DEFAULT_INVITE_TTL_SECONDS))
        now = float(time.time())
        code = secrets.token_urlsafe(24)
        self._reviewer_invites[code] = {
            "code": code,
            "issued_by": issuer,
            "issued_at": now,
            "expires_at": now + float(ttl),
            "status": "issued",
            "redeemed_by": "",
            "redeemed_at": 0.0,
            "revoked_by": "",
            "revoked_at": 0.0,
        }
        self._flush_state()
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
        changed = False
        rows: list[dict[str, Any]] = []
        for code, invite in self._reviewer_invites.items():
            row = dict(invite)
            if row.get("status") == "issued" and float(row.get("expires_at", 0.0) or 0.0) > 0 and now >= float(
                row.get("expires_at", 0.0) or 0.0
            ):
                row["status"] = "expired"
                self._reviewer_invites[code] = row
                changed = True
            if requested and row.get("status") != requested:
                continue
            rows.append(row)
        if changed:
            self._flush_state()
        rows.sort(key=lambda item: float(item.get("issued_at", 0.0) or 0.0), reverse=True)
        return rows

    def redeem_invite(self, invite_code: str, reviewer_id: str) -> dict[str, Any]:
        code = str(invite_code or "").strip()
        uid = self._normalize_user_id(reviewer_id)
        if not code:
            return {"error": "invite_code_required"}
        if not uid:
            return {"error": "reviewer_id_required"}
        invite = self._reviewer_invites.get(code)
        if not isinstance(invite, dict):
            return {"error": "invite_not_found"}
        now = float(time.time())
        status = str(invite.get("status", "issued") or "issued").strip().lower()
        expires_at = float(invite.get("expires_at", 0.0) or 0.0)
        if status == "redeemed":
            return {"error": "invite_already_redeemed", "reviewer_id": str(invite.get("redeemed_by", "") or "")}
        if status == "revoked":
            return {"error": "invite_revoked"}
        if expires_at > 0 and now >= expires_at:
            invite["status"] = "expired"
            self._reviewer_invites[code] = invite
            self._flush_state()
            return {"error": "invite_expired"}

        created = uid not in self._users
        self._ensure_user(
            user_id=uid,
            role="reviewer",
            created_by=str(invite.get("issued_by", "") or "").strip(),
            source_invite=code,
        )
        invite["status"] = "redeemed"
        invite["redeemed_by"] = uid
        invite["redeemed_at"] = now
        self._reviewer_invites[code] = invite
        self._flush_state()
        return {
            "status": "invite_redeemed",
            "reviewer_id": uid,
            "created": created,
        }

    def revoke_invite(self, invite_code: str, admin_id: str) -> dict[str, Any]:
        code = str(invite_code or "").strip()
        issuer = self._normalize_user_id(admin_id)
        if not code:
            return {"error": "invite_code_required"}
        if not issuer:
            return {"error": "admin_id_required"}
        invite = self._reviewer_invites.get(code)
        if not isinstance(invite, dict):
            return {"error": "invite_not_found"}
        status = str(invite.get("status", "issued") or "issued").strip().lower()
        if status == "redeemed":
            return {"error": "invite_already_redeemed", "reviewer_id": str(invite.get("redeemed_by", "") or "").strip()}
        now = float(time.time())
        invite["status"] = "revoked"
        invite["revoked_by"] = issuer
        invite["revoked_at"] = now
        self._reviewer_invites[code] = invite
        self._flush_state()
        return {
            "status": "revoked",
            "invite_code": code,
            "revoked_by": issuer,
            "revoked_at": now,
        }

    def is_reviewer(self, user_id: str) -> bool:
        uid = self._normalize_user_id(user_id)
        row = self._users.get(uid)
        return isinstance(row, dict) and row.get("role") == "reviewer" and row.get("status") == "active"

    def list_reviewers(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for uid, account in self._users.items():
            if str(account.get("role", "") or "") != "reviewer":
                continue
            if str(account.get("status", "active") or "active").strip().lower() != "active":
                continue
            rows.append(
                {
                    "reviewer_id": uid,
                    "created_at": float(account.get("created_at", 0.0) or 0.0),
                    "created_by": str(account.get("created_by", "") or "").strip(),
                    "source_invite": str(account.get("source_invite", "") or "").strip(),
                    "device_count": len(self.list_devices(user_id=uid)),
                }
            )
        rows.sort(
            key=lambda item: (
                float(item.get("created_at", 0.0) or 0.0),
                str(item.get("reviewer_id", "") or ""),
            ),
            reverse=True,
        )
        return rows

    def register_device(self, user_id: str, label: str = "") -> dict[str, Any]:
        uid = self._normalize_user_id(user_id)
        if not uid:
            return {"error": "reviewer_id_required"}
        if not self.is_reviewer(uid):
            return {"error": "reviewer_not_registered", "reviewer_id": uid}
        active_devices = self.list_devices(user_id=uid)
        if len(active_devices) >= self.max_devices:
            return {"error": "device_limit_exceeded", "max_devices": self.max_devices}
        now = float(time.time())
        device_id = secrets.token_hex(8)
        device_key = secrets.token_urlsafe(32)
        credential = self._create_credential(
            user_id=uid,
            role="reviewer",
            credential_type=self.DEVICE_CREDENTIAL_TYPE,
            secret=device_key,
            device_id=device_id,
            source="reviewer_device_register",
        )
        self._reviewer_devices[device_id] = {
            "device_id": device_id,
            "reviewer_id": uid,
            "credential_id": str(credential.get("credential_id", "") or ""),
            "label": str(label or "").strip(),
            "registered_at": now,
            "last_used_at": 0.0,
            "revoked_at": 0.0,
        }
        self._flush_state()
        return {
            "status": "registered",
            "reviewer_id": uid,
            "device_id": device_id,
            "device_key": device_key,
            "label": str(label or "").strip(),
            "max_devices": self.max_devices,
        }

    def list_devices(self, user_id: str) -> list[dict[str, Any]]:
        uid = self._normalize_user_id(user_id)
        rows: list[dict[str, Any]] = []
        for item in self._reviewer_devices.values():
            if self._normalize_user_id(str(item.get("reviewer_id", "") or "")) != uid:
                continue
            if float(item.get("revoked_at", 0.0) or 0.0) > 0:
                continue
            rows.append(
                {
                    "device_id": str(item.get("device_id", "") or "").strip(),
                    "label": str(item.get("label", "") or "").strip(),
                    "registered_at": float(item.get("registered_at", 0.0) or 0.0),
                    "last_used_at": float(item.get("last_used_at", 0.0) or 0.0),
                }
            )
        rows.sort(
            key=lambda item: (
                float(item.get("registered_at", 0.0) or 0.0),
                str(item.get("device_id", "") or ""),
            ),
            reverse=True,
        )
        return rows

    def revoke_device(self, user_id: str, device_id: str) -> bool:
        uid = self._normalize_user_id(user_id)
        did = str(device_id or "").strip()
        if not uid or not did:
            return False
        device = self._reviewer_devices.get(did)
        if not isinstance(device, dict):
            return False
        if self._normalize_user_id(str(device.get("reviewer_id", "") or "")) != uid:
            return False
        if float(device.get("revoked_at", 0.0) or 0.0) > 0:
            return False
        now = float(time.time())
        device["revoked_at"] = now
        credential_id = str(device.get("credential_id", "") or "").strip()
        if credential_id and credential_id in self._credentials:
            self._revoke_credential(self._credentials[credential_id], reason="reviewer_device_revoked")
        self._flush_state()
        return True

    def revoke_all_devices(self, user_id: str) -> int:
        uid = self._normalize_user_id(user_id)
        if not uid:
            return 0
        revoked = 0
        for did, device in self._reviewer_devices.items():
            if self._normalize_user_id(str(device.get("reviewer_id", "") or "")) != uid:
                continue
            if float(device.get("revoked_at", 0.0) or 0.0) > 0:
                continue
            if self.revoke_device(uid, did):
                revoked += 1
        return revoked

    def resolve_device(self, user_id: str, key: str) -> dict[str, Any] | None:
        uid = self._normalize_user_id(user_id)
        provided = str(key or "").strip()
        if not uid or not provided:
            return None
        for device in self._reviewer_devices.values():
            if self._normalize_user_id(str(device.get("reviewer_id", "") or "")) != uid:
                continue
            if float(device.get("revoked_at", 0.0) or 0.0) > 0:
                continue
            credential_id = str(device.get("credential_id", "") or "").strip()
            credential = self._credentials.get(credential_id)
            if not isinstance(credential, dict):
                continue
            if not self._verify_secret(provided, credential):
                continue
            return {
                "device_id": str(device.get("device_id", "") or "").strip(),
                "label": str(device.get("label", "") or "").strip(),
                "registered_at": float(device.get("registered_at", 0.0) or 0.0),
                "last_used_at": float(device.get("last_used_at", 0.0) or 0.0),
            }
        return None

    def validate_device(self, user_id: str, key: str) -> bool:
        return self.resolve_device(user_id=user_id, key=key) is not None

    def mark_device_used(self, user_id: str, device_id: str) -> None:
        uid = self._normalize_user_id(user_id)
        did = str(device_id or "").strip()
        if not uid or not did:
            return
        device = self._reviewer_devices.get(did)
        if not isinstance(device, dict):
            return
        if self._normalize_user_id(str(device.get("reviewer_id", "") or "")) != uid:
            return
        device["last_used_at"] = float(time.time())
        self._flush_state()
