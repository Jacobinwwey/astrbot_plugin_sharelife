import json
from pathlib import Path

from sharelife.infrastructure.identity_repository import JsonIdentityRepository, SqliteIdentityRepository
from sharelife.infrastructure.json_state_store import JsonStateStore


def _sample_payload() -> dict[str, list[dict[str, object]]]:
    return {
        "users": [
            {
                "user_id": "reviewer-1",
                "role": "reviewer",
                "created_at": 1.0,
                "updated_at": 1.0,
                "created_by": "admin-1",
                "source_invite": "invite-1",
                "status": "active",
            }
        ],
        "credentials": [
            {
                "credential_id": "cred-1",
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
                "session_id": "sess-1",
                "role": "reviewer",
                "user_id": "reviewer-1",
                "device_id": "device-1",
                "session_key": "reviewer:reviewer-1:device-1",
                "token_hash": "tok-hash-1",
                "issued_at": 3.0,
                "expires_at": 33.0,
                "last_seen_at": 4.0,
                "revoked_at": 0.0,
                "revoke_reason": "",
            }
        ],
        "reviewer_devices": [
            {
                "device_id": "device-1",
                "reviewer_id": "reviewer-1",
                "credential_id": "cred-device-1",
                "label": "macbook",
                "registered_at": 5.0,
                "last_used_at": 6.0,
                "revoked_at": 0.0,
            }
        ],
        "reviewer_invites": [
            {
                "code": "invite-1",
                "issued_by": "admin-1",
                "issued_at": 7.0,
                "expires_at": 67.0,
                "status": "issued",
                "redeemed_by": "",
                "redeemed_at": 0.0,
                "revoked_by": "",
                "revoked_at": 0.0,
            }
        ],
    }


def test_json_identity_repository_roundtrip(tmp_path: Path) -> None:
    repo = JsonIdentityRepository(JsonStateStore(tmp_path / "identity_state.json"))
    payload = _sample_payload()

    repo.save_state(payload)

    assert repo.load_state() == payload


def test_sqlite_identity_repository_roundtrip(tmp_path: Path) -> None:
    repo = SqliteIdentityRepository(tmp_path / "sharelife_state.sqlite3")
    payload = _sample_payload()

    repo.save_state(payload)

    assert repo.load_state() == payload


def test_json_identity_repository_writes_structured_state(tmp_path: Path) -> None:
    path = tmp_path / "identity_state.json"
    repo = JsonIdentityRepository(JsonStateStore(path))

    repo.save_state(_sample_payload())

    written = json.loads(path.read_text(encoding="utf-8"))
    assert sorted(written.keys()) == [
        "credentials",
        "reviewer_devices",
        "reviewer_invites",
        "sessions",
        "users",
    ]
