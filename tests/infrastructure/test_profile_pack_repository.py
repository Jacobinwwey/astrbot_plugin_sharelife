import sqlite3
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from sharelife.infrastructure.json_state_store import JsonStateStore
from sharelife.infrastructure.profile_pack_repository import (
    JsonProfilePackRepository,
    SqliteProfilePackRepository,
)
from sharelife.infrastructure.sqlite_state_store import SqliteStateStore


def _sample_payload() -> dict:
    return {
        "exports": [
            {
                "artifact_id": "artifact-1",
                "pack_id": "profile/basic",
                "version": "1.0.0",
                "exported_at": "2026-03-30T04:00:00+00:00",
                "path": "/tmp/profile-basic.zip",
                "filename": "profile-basic.zip",
                "sha256": "abc",
                "size_bytes": 123,
                "manifest": {
                    "pack_type": "bot_profile_pack",
                    "pack_id": "profile/basic",
                    "version": "1.0.0",
                },
                "redaction_notes": [],
            }
        ],
        "imports": [
            {
                "import_id": "import-1",
                "imported_at": "2026-03-30T04:05:00+00:00",
                "filename": "profile-basic.zip",
                "manifest": {
                    "pack_type": "bot_profile_pack",
                    "pack_id": "profile/basic",
                    "version": "1.0.0",
                },
                "sections": {"plugins": {"sharelife": {"enabled": True}}},
                "scan_summary": {"risk_level": "low"},
                "compatibility": "compatible",
                "compatibility_issues": [],
            }
        ],
        "submissions": [
            {
                "submission_id": "submission-1",
                "user_id": "u1",
                "artifact_id": "artifact-1",
                "import_id": "import-1",
                "pack_type": "bot_profile_pack",
                "pack_id": "profile/basic",
                "version": "1.0.0",
                "status": "pending",
                "created_at": "2026-03-30T04:06:00+00:00",
                "updated_at": "2026-03-30T04:06:00+00:00",
                "risk_level": "low",
                "review_labels": [],
                "warning_flags": [],
                "scan_summary": {},
            }
        ],
        "published": [
            {
                "pack_type": "bot_profile_pack",
                "pack_id": "profile/basic",
                "version": "1.0.0",
                "source_submission_id": "submission-1",
                "artifact_id": "artifact-1",
                "import_id": "import-1",
                "published_at": "2026-03-30T04:08:00+00:00",
                "risk_level": "low",
                "review_labels": [],
                "warning_flags": [],
                "scan_summary": {},
            }
        ],
        "plugin_install_confirmations": {
            "import-1": ["community_tools"],
        },
        "plugin_install_executions": {
            "import-1": [
                {
                    "executed_at": "2026-03-30T04:09:00+00:00",
                    "status": "executed",
                    "result": {"installed_count": 1},
                }
            ]
        },
    }


def test_json_profile_pack_repository_roundtrip(tmp_path: Path) -> None:
    repo = JsonProfilePackRepository(JsonStateStore(tmp_path / "profile_pack_state.json"))
    payload = _sample_payload()
    repo.save_state(payload)
    assert repo.load_state() == payload


def test_sqlite_profile_pack_repository_roundtrip(tmp_path: Path) -> None:
    repo = SqliteProfilePackRepository(tmp_path / "sharelife_state.sqlite3")
    payload = _sample_payload()
    repo.save_state(payload)
    assert repo.load_state() == payload


def test_sqlite_profile_pack_repository_imports_legacy_payload_once(tmp_path: Path) -> None:
    sqlite_file = tmp_path / "sharelife_state.sqlite3"
    legacy_store = SqliteStateStore(sqlite_file, store_key="profile_pack_state")
    legacy_store.save(_sample_payload())

    repo = SqliteProfilePackRepository(sqlite_file, legacy_state_store=legacy_store)
    loaded = repo.load_state()
    assert loaded["submissions"][0]["submission_id"] == "submission-1"

    payload = _sample_payload()
    payload["submissions"][0]["submission_id"] = "submission-2"
    payload["published"][0]["source_submission_id"] = "submission-2"
    repo.save_state(payload)
    repo_again = SqliteProfilePackRepository(sqlite_file, legacy_state_store=legacy_store)
    loaded_again = repo_again.load_state()
    assert loaded_again["submissions"][0]["submission_id"] == "submission-2"


def test_sqlite_profile_pack_repository_creates_required_indexes(tmp_path: Path) -> None:
    sqlite_file = tmp_path / "sharelife_state.sqlite3"
    SqliteProfilePackRepository(sqlite_file)

    with sqlite3.connect(str(sqlite_file)) as conn:
        rows = conn.execute("PRAGMA index_list('sharelife_profile_pack_submissions')").fetchall()
        index_names = {str(row[1]) for row in rows}

    assert "idx_profile_pack_submissions_pack_id" in index_names
    assert "idx_profile_pack_submissions_status" in index_names
    assert "idx_profile_pack_submissions_risk_level" in index_names
    assert "idx_profile_pack_submissions_created_at" in index_names


def test_sqlite_profile_pack_repository_concurrent_writes_keep_valid_state(tmp_path: Path) -> None:
    sqlite_file = tmp_path / "sharelife_state.sqlite3"
    submission_ids = [f"submission-{idx}" for idx in range(10)]

    def _write_state(submission_id: str) -> None:
        repo = SqliteProfilePackRepository(sqlite_file)
        payload = _sample_payload()
        payload["submissions"][0]["submission_id"] = submission_id
        payload["published"][0]["source_submission_id"] = submission_id
        repo.save_state(payload)

    with ThreadPoolExecutor(max_workers=5) as pool:
        list(pool.map(_write_state, submission_ids))

    final_state = SqliteProfilePackRepository(sqlite_file).load_state()
    assert len(final_state["submissions"]) == 1
    assert len(final_state["published"]) == 1
    assert final_state["submissions"][0]["submission_id"] in set(submission_ids)
    assert final_state["published"][0]["source_submission_id"] in set(submission_ids)
