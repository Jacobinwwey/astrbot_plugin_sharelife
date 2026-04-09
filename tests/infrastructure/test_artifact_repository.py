from pathlib import Path

from sharelife.infrastructure.artifact_repository import (
    JsonArtifactRepository,
    SqliteArtifactRepository,
)
from sharelife.infrastructure.json_state_store import JsonStateStore
from sharelife.infrastructure.sqlite_state_store import SqliteStateStore


def _sample_payload() -> dict:
    return {
        "artifacts": [
            {
                "artifact_id": "artifact-1",
                "artifact_kind": "template_submission_package",
                "storage_backend": "local",
                "file_key": "uploads/community-basic.zip",
                "filename": "community-basic.zip",
                "sha256": "abc123",
                "size_bytes": 512,
                "created_at": "2026-04-07T12:00:00+00:00",
                "updated_at": "2026-04-07T12:00:01+00:00",
                "metadata": {
                    "template_id": "community/basic",
                    "version": "1.0.0",
                    "source": "uploaded_submission",
                },
            }
        ]
    }


def test_json_artifact_repository_roundtrip(tmp_path: Path) -> None:
    repo = JsonArtifactRepository(JsonStateStore(tmp_path / "artifact_state.json"))

    payload = _sample_payload()
    repo.save_state(payload)

    assert repo.load_state() == payload


def test_sqlite_artifact_repository_roundtrip(tmp_path: Path) -> None:
    repo = SqliteArtifactRepository(tmp_path / "sharelife_state.sqlite3")

    payload = _sample_payload()
    repo.save_state(payload)

    assert repo.load_state() == payload


def test_sqlite_artifact_repository_imports_legacy_payload_once(tmp_path: Path) -> None:
    sqlite_file = tmp_path / "sharelife_state.sqlite3"
    legacy_store = SqliteStateStore(sqlite_file, store_key="artifact_state")
    legacy_store.save(_sample_payload())

    repo = SqliteArtifactRepository(sqlite_file, legacy_state_store=legacy_store)
    loaded = repo.load_state()
    assert loaded["artifacts"][0]["artifact_id"] == "artifact-1"

    payload = _sample_payload()
    payload["artifacts"][0]["artifact_id"] = "artifact-2"
    payload["artifacts"][0]["file_key"] = "uploads/community-basic-v2.zip"
    repo.save_state(payload)

    repo_again = SqliteArtifactRepository(sqlite_file, legacy_state_store=legacy_store)
    loaded_again = repo_again.load_state()
    assert loaded_again["artifacts"][0]["artifact_id"] == "artifact-2"
