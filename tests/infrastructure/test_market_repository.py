import sqlite3
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from sharelife.infrastructure.json_state_store import JsonStateStore
from sharelife.infrastructure.market_repository import JsonMarketRepository, SqliteMarketRepository
from sharelife.infrastructure.sqlite_state_store import SqliteStateStore


def _sample_payload() -> dict:
    return {
        "submissions": [
            {
                "id": "s-1",
                "user_id": "u-1",
                "template_id": "community/basic",
                "version": "1.0.0",
                "status": "pending",
                "created_at": "2026-03-25T10:00:00+00:00",
                "updated_at": "2026-03-25T10:00:00+00:00",
                "reviewer_id": None,
                "review_note": "",
                "prompt_template": "prompt",
                "package_artifact": {"path": "bundle.zip"},
                "scan_summary": {"risk": "low"},
                "upload_options": {
                    "scan_mode": "strict",
                    "visibility": "private",
                    "replace_existing": True,
                },
                "review_labels": ["manual_reviewed"],
                "warning_flags": [],
                "risk_level": "low",
                "category": "starter",
                "tags": ["basic"],
                "maintainer": "demo",
                "source_channel": "community_submission",
            }
        ],
        "published": [
            {
                "template_id": "community/basic",
                "version": "1.0.0",
                "source_submission_id": "s-1",
                "prompt_template": "prompt",
                "published_at": "2026-03-25T10:05:00+00:00",
                "review_note": "approved",
                "package_artifact": {"path": "bundle.zip"},
                "scan_summary": {"risk": "low"},
                "review_labels": ["manual_reviewed"],
                "warning_flags": [],
                "risk_level": "low",
                "category": "starter",
                "tags": ["basic"],
                "maintainer": "demo",
                "source_channel": "community_submission",
                "engagement": {
                    "trial_requests": 1,
                    "installs": 2,
                    "prompt_generations": 3,
                    "package_generations": 4,
                    "community_submissions": 1,
                    "last_activity_at": "2026-03-25T10:10:00+00:00",
                },
            }
        ],
    }


def test_json_market_repository_roundtrip(tmp_path: Path) -> None:
    store = JsonStateStore(tmp_path / "market_state.json")
    repo = JsonMarketRepository(store)

    payload = _sample_payload()
    repo.save_state(payload)

    loaded = repo.load_state()
    assert loaded == payload


def test_sqlite_market_repository_roundtrip(tmp_path: Path) -> None:
    repo = SqliteMarketRepository(tmp_path / "sharelife_state.sqlite3")

    payload = _sample_payload()
    repo.save_state(payload)

    loaded = repo.load_state()
    assert loaded == payload


def test_sqlite_market_repository_imports_legacy_payload_once(tmp_path: Path) -> None:
    sqlite_file = tmp_path / "sharelife_state.sqlite3"
    legacy_store = SqliteStateStore(sqlite_file, store_key="market_state")
    legacy_store.save(_sample_payload())

    repo = SqliteMarketRepository(sqlite_file, legacy_state_store=legacy_store)
    loaded = repo.load_state()
    assert loaded["submissions"][0]["id"] == "s-1"

    # Existing normalized rows must not be replaced by legacy data on re-init.
    payload = _sample_payload()
    payload["submissions"][0]["id"] = "s-2"
    repo.save_state(payload)
    repo_again = SqliteMarketRepository(sqlite_file, legacy_state_store=legacy_store)
    loaded_again = repo_again.load_state()
    assert loaded_again["submissions"][0]["id"] == "s-2"


def test_sqlite_market_repository_creates_required_indexes(tmp_path: Path) -> None:
    sqlite_file = tmp_path / "sharelife_state.sqlite3"
    SqliteMarketRepository(sqlite_file)

    with sqlite3.connect(str(sqlite_file)) as conn:
        rows = conn.execute("PRAGMA index_list('sharelife_market_submissions')").fetchall()
        index_names = {str(row[1]) for row in rows}

    assert "idx_market_submissions_template_id" in index_names
    assert "idx_market_submissions_status" in index_names
    assert "idx_market_submissions_risk_level" in index_names
    assert "idx_market_submissions_created_at" in index_names


def test_sqlite_market_repository_migrates_missing_upload_options_column(tmp_path: Path) -> None:
    sqlite_file = tmp_path / "sharelife_state.sqlite3"
    with sqlite3.connect(str(sqlite_file)) as conn:
        conn.execute(
            """
            CREATE TABLE sharelife_market_submissions (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                template_id TEXT NOT NULL,
                version TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                reviewer_id TEXT,
                review_note TEXT NOT NULL,
                prompt_template TEXT NOT NULL,
                package_artifact_json TEXT,
                scan_summary_json TEXT,
                review_labels_json TEXT NOT NULL,
                warning_flags_json TEXT NOT NULL,
                risk_level TEXT NOT NULL,
                category TEXT NOT NULL,
                tags_json TEXT NOT NULL,
                maintainer TEXT NOT NULL,
                source_channel TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE sharelife_market_published (
                template_id TEXT PRIMARY KEY,
                version TEXT NOT NULL,
                source_submission_id TEXT NOT NULL,
                prompt_template TEXT NOT NULL,
                published_at TEXT NOT NULL,
                review_note TEXT NOT NULL,
                package_artifact_json TEXT,
                scan_summary_json TEXT,
                review_labels_json TEXT NOT NULL,
                warning_flags_json TEXT NOT NULL,
                risk_level TEXT NOT NULL,
                category TEXT NOT NULL,
                tags_json TEXT NOT NULL,
                maintainer TEXT NOT NULL,
                source_channel TEXT NOT NULL,
                engagement_json TEXT NOT NULL
            )
            """
        )
        conn.commit()

    repo = SqliteMarketRepository(sqlite_file)
    repo.save_state(_sample_payload())
    loaded = repo.load_state()
    assert loaded == _sample_payload()

    with sqlite3.connect(str(sqlite_file)) as conn:
        rows = conn.execute("PRAGMA table_info('sharelife_market_submissions')").fetchall()
    assert any(str(row[1]) == "upload_options_json" for row in rows)


def test_sqlite_market_repository_concurrent_writes_keep_valid_state(tmp_path: Path) -> None:
    sqlite_file = tmp_path / "sharelife_state.sqlite3"
    writer_ids = [f"s-{idx}" for idx in range(10)]

    def _write_state(writer_id: str) -> None:
        repo = SqliteMarketRepository(sqlite_file)
        payload = _sample_payload()
        payload["submissions"][0]["id"] = writer_id
        payload["published"][0]["source_submission_id"] = writer_id
        repo.save_state(payload)

    with ThreadPoolExecutor(max_workers=5) as pool:
        list(pool.map(_write_state, writer_ids))

    final_state = SqliteMarketRepository(sqlite_file).load_state()
    assert len(final_state["submissions"]) == 1
    assert len(final_state["published"]) == 1
    assert final_state["submissions"][0]["id"] in set(writer_ids)
    assert final_state["published"][0]["source_submission_id"] in set(writer_ids)
