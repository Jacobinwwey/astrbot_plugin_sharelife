from pathlib import Path

from sharelife.application.services_reviewer_auth import ReviewerAuthService
from sharelife.infrastructure.json_state_store import JsonStateStore
from sharelife.infrastructure.sqlite_state_store import SqliteStateStore


def test_reviewer_auth_bootstrap_password_is_hashed_and_sessions_persist(tmp_path: Path) -> None:
    identity_path = tmp_path / "identity_state.json"
    service = ReviewerAuthService(state_store=JsonStateStore(identity_path))

    synced = service.sync_bootstrap_password("admin", "admin-secret-123")
    assert synced["status"] in {"created", "rotated"}
    assert service.verify_bootstrap_password("admin", "admin-secret-123") is True
    assert service.verify_bootstrap_password("admin", "wrong-secret") is False

    issued = service.issue_session(role="admin", ttl_seconds=7200)
    token = issued["token"]
    resolved = service.resolve_session(token)
    assert resolved is not None
    assert resolved["role"] == "admin"

    reloaded = ReviewerAuthService(state_store=JsonStateStore(identity_path))
    assert reloaded.verify_bootstrap_password("admin", "admin-secret-123") is True
    persisted = reloaded.resolve_session(token)
    assert persisted is not None
    assert persisted["session_id"] == resolved["session_id"]

    text = identity_path.read_text(encoding="utf-8")
    assert "admin-secret-123" not in text
    assert "secret_hash" in text


def test_reviewer_auth_migrates_legacy_state_without_preserving_plaintext_keys(tmp_path: Path) -> None:
    identity_store = JsonStateStore(tmp_path / "identity_state.json")
    legacy_store = JsonStateStore(tmp_path / "reviewer_auth_state.json")
    legacy_store.save(
        {
            "reviewer_accounts": {
                "reviewer-1": {
                    "reviewer_id": "reviewer-1",
                    "created_at": 10.0,
                    "created_by": "admin-1",
                    "source_invite": "invite-1",
                }
            },
            "reviewer_device_keys": {
                "reviewer-1": [
                    {
                        "device_id": "device-1",
                        "key": "plain-device-key",
                        "label": "macbook",
                        "registered_at": 11.0,
                        "last_used_at": 12.0,
                    }
                ]
            },
            "reviewer_invites": {
                "invite-1": {
                    "code": "invite-1",
                    "issued_by": "admin-1",
                    "issued_at": 9.0,
                    "expires_at": 99.0,
                    "status": "redeemed",
                    "redeemed_by": "reviewer-1",
                    "redeemed_at": 10.0,
                    "revoked_by": "",
                    "revoked_at": 0.0,
                }
            },
        }
    )

    service = ReviewerAuthService(
        state_store=identity_store,
        legacy_state_store=legacy_store,
    )

    reviewers = service.list_reviewers()
    assert reviewers[0]["reviewer_id"] == "reviewer-1"
    assert reviewers[0]["device_count"] == 1

    resolved = service.resolve_device("reviewer-1", "plain-device-key")
    assert resolved is not None
    assert resolved["device_id"] == "device-1"

    text = (tmp_path / "identity_state.json").read_text(encoding="utf-8")
    assert "plain-device-key" not in text
    assert "reviewer_device_key" in text


def test_reviewer_auth_imports_identity_state_row_when_switching_to_sqlite(tmp_path: Path) -> None:
    sqlite_path = tmp_path / "sharelife_state.sqlite3"
    identity_row = SqliteStateStore(sqlite_path, store_key="identity_state")
    identity_row.save(
        {
            "users": [
                {
                    "user_id": "__bootstrap__:admin",
                    "role": "admin",
                    "created_at": 1.0,
                    "updated_at": 1.0,
                    "created_by": "system",
                    "source_invite": "",
                    "status": "active",
                }
            ],
            "credentials": [
                {
                    "credential_id": "cred-admin-1",
                    "user_id": "__bootstrap__:admin",
                    "role": "admin",
                    "credential_type": "bootstrap_password",
                    "device_id": "",
                    "algorithm": "pbkdf2_sha256",
                    "iterations": 310000,
                    "salt": "c2FsdA==",
                    "secret_hash": "aGFzaA==",
                    "created_at": 2.0,
                    "updated_at": 2.0,
                    "revoked_at": 0.0,
                    "status": "active",
                    "source": "local_webui_auth",
                }
            ],
            "sessions": [
                {
                    "session_id": "sess-admin-1",
                    "role": "admin",
                    "user_id": "",
                    "device_id": "",
                    "session_key": "admin",
                    "token_hash": "tok-hash-admin-1",
                    "issued_at": 3.0,
                    "expires_at": 9999999999.0,
                    "last_seen_at": 3.0,
                    "revoked_at": 0.0,
                    "revoke_reason": "",
                }
            ],
            "reviewer_devices": [],
            "reviewer_invites": [],
        }
    )

    service = ReviewerAuthService(state_store=identity_row)

    assert service.has_bootstrap_password("admin") is True
    state = service.repository.load_state()
    assert state["users"][0]["user_id"] == "__bootstrap__:admin"
    assert state["sessions"][0]["session_id"] == "sess-admin-1"
