import sqlite3
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from sharelife.infrastructure.audit_repository import JsonAuditRepository, SqliteAuditRepository
from sharelife.infrastructure.json_state_store import JsonStateStore
from sharelife.infrastructure.notifier_repository import JsonNotifierRepository, SqliteNotifierRepository
from sharelife.infrastructure.preference_repository import (
    JsonPreferenceRepository,
    SqlitePreferenceRepository,
)
from sharelife.infrastructure.retry_queue_repository import (
    JsonRetryQueueRepository,
    SqliteRetryQueueRepository,
)
from sharelife.infrastructure.sqlite_state_store import SqliteStateStore
from sharelife.infrastructure.transfer_job_repository import (
    JsonTransferJobRepository,
    SqliteTransferJobRepository,
)
from sharelife.infrastructure.trial_repository import JsonTrialRepository, SqliteTrialRepository
from sharelife.infrastructure.trial_request_repository import (
    JsonTrialRequestRepository,
    SqliteTrialRequestRepository,
)


def test_preference_repositories_roundtrip(tmp_path: Path) -> None:
    payload = {
        "preferences": [
            {
                "user_id": "u1",
                "execution_mode": "inline_execution",
                "observe_task_details": True,
            }
        ]
    }

    json_repo = JsonPreferenceRepository(JsonStateStore(tmp_path / "preferences.json"))
    json_repo.save_state(payload)
    assert json_repo.load_state() == payload

    sqlite_repo = SqlitePreferenceRepository(tmp_path / "sharelife_state.sqlite3")
    sqlite_repo.save_state(payload)
    assert sqlite_repo.load_state() == payload


def test_trial_repositories_roundtrip(tmp_path: Path) -> None:
    payload = {
        "trials": [
            {
                "id": "trial-1",
                "user_id": "u1",
                "session_id": "s1",
                "template_id": "community/basic",
                "started_at": "2026-03-25T12:00:00+00:00",
                "expires_at": "2026-03-25T14:00:00+00:00",
                "ttl_seconds": 7200,
            }
        ]
    }

    json_repo = JsonTrialRepository(JsonStateStore(tmp_path / "trial.json"))
    json_repo.save_state(payload)
    assert json_repo.load_state() == payload

    sqlite_repo = SqliteTrialRepository(tmp_path / "sharelife_state.sqlite3")
    sqlite_repo.save_state(payload)
    assert sqlite_repo.load_state() == payload


def test_retry_repositories_roundtrip(tmp_path: Path) -> None:
    payload = {
        "requests": [
            {
                "id": "req-1",
                "user_id": "u1",
                "template_id": "community/basic",
                "state": "reviewing",
                "created_at": "2026-03-25T12:00:00+00:00",
                "updated_at": "2026-03-25T12:01:00+00:00",
                "version": 2,
            }
        ],
        "locks": [
            {
                "request_id": "req-1",
                "holder_id": "admin-1",
                "lock_version": 1,
                "acquired_at": "2026-03-25T12:01:00+00:00",
                "expires_at": "2026-03-25T12:11:00+00:00",
                "force_reason": "",
            }
        ],
    }

    json_repo = JsonRetryQueueRepository(JsonStateStore(tmp_path / "retry.json"))
    json_repo.save_state(payload)
    assert json_repo.load_state() == payload

    sqlite_repo = SqliteRetryQueueRepository(tmp_path / "sharelife_state.sqlite3")
    sqlite_repo.save_state(payload)
    assert sqlite_repo.load_state() == payload


def test_audit_repositories_roundtrip(tmp_path: Path) -> None:
    payload = {
        "events": [
            {
                "id": "event-1",
                "action": "submission.approved",
                "actor_id": "admin",
                "actor_role": "admin",
                "target_id": "sub-1",
                "status": "approved",
                "detail": {"template_id": "community/basic"},
                "created_at": "2026-03-25T12:00:00+00:00",
            }
        ]
    }

    json_repo = JsonAuditRepository(JsonStateStore(tmp_path / "audit.json"))
    json_repo.save_state(payload)
    assert json_repo.load_state() == payload

    sqlite_repo = SqliteAuditRepository(tmp_path / "sharelife_state.sqlite3")
    sqlite_repo.save_state(payload)
    assert sqlite_repo.load_state() == payload


def test_trial_request_repositories_roundtrip(tmp_path: Path) -> None:
    payload = {"first_notice_sent_users": ["u1", "u2"]}

    json_repo = JsonTrialRequestRepository(JsonStateStore(tmp_path / "trial-request.json"))
    json_repo.save_state(payload)
    assert json_repo.load_state() == payload

    sqlite_repo = SqliteTrialRequestRepository(tmp_path / "sharelife_state.sqlite3")
    sqlite_repo.save_state(payload)
    assert sqlite_repo.load_state() == payload


def test_notifier_repositories_roundtrip(tmp_path: Path) -> None:
    payload = {
        "events": [
            {"channel": "user_dm", "target": "u1", "message": "hello"},
            {"channel": "admin_dm", "target": "admin", "message": "queued"},
        ]
    }

    json_repo = JsonNotifierRepository(JsonStateStore(tmp_path / "notifier.json"))
    json_repo.save_state(payload)
    assert json_repo.load_state() == payload

    sqlite_repo = SqliteNotifierRepository(tmp_path / "sharelife_state.sqlite3")
    sqlite_repo.save_state(payload)
    assert sqlite_repo.load_state() == payload


def test_transfer_job_repositories_roundtrip(tmp_path: Path) -> None:
    payload = {
        "upload_jobs": [
            {
                "job_id": "upload-1",
                "direction": "upload",
                "job_type": "template_submission_package",
                "actor_id": "u1",
                "actor_role": "member",
                "user_id": "u1",
                "logical_key": "upload:u1:community/basic:1.0.0:key-1",
                "status": "done",
                "created_at": "2026-04-07T12:00:00+00:00",
                "updated_at": "2026-04-07T12:00:01+00:00",
                "template_id": "community/basic",
                "submission_id": "sub-1",
                "filename": "community-basic.zip",
                "size_bytes": 256,
                "sha256": "abc123",
                "attempt_count": 2,
                "retry_count": 1,
                "max_attempts": 3,
                "idempotency_key": "key-1",
                "started_at": "2026-04-07T12:00:00+00:00",
                "finished_at": "2026-04-07T12:00:01+00:00",
                "failure_reason": "",
                "failure_detail": "",
                "metadata": {"version": "1.0.0"},
            }
        ],
        "download_jobs": [
            {
                "job_id": "download-1",
                "direction": "download",
                "job_type": "member_submission_package",
                "actor_id": "u1",
                "actor_role": "member",
                "user_id": "u1",
                "logical_key": "download:u1:submission:sub-1:key-2",
                "status": "failed",
                "created_at": "2026-04-07T12:05:00+00:00",
                "updated_at": "2026-04-07T12:05:01+00:00",
                "template_id": "community/basic",
                "submission_id": "sub-1",
                "filename": "community-basic.zip",
                "size_bytes": 256,
                "sha256": "abc123",
                "attempt_count": 1,
                "retry_count": 0,
                "max_attempts": 2,
                "idempotency_key": "key-2",
                "started_at": "2026-04-07T12:05:00+00:00",
                "finished_at": "2026-04-07T12:05:01+00:00",
                "failure_reason": "artifact_missing",
                "failure_detail": "submission package missing",
                "metadata": {},
            }
        ],
    }

    json_repo = JsonTransferJobRepository(JsonStateStore(tmp_path / "transfer.json"))
    json_repo.save_state(payload)
    assert json_repo.load_state() == payload

    sqlite_repo = SqliteTransferJobRepository(tmp_path / "sharelife_state.sqlite3")
    sqlite_repo.save_state(payload)
    assert sqlite_repo.load_state() == payload


def test_operational_sqlite_repositories_import_legacy_key_value_once(tmp_path: Path) -> None:
    sqlite_file = tmp_path / "sharelife_state.sqlite3"

    pref_store = SqliteStateStore(sqlite_file, store_key="preference_state")
    pref_store.save(
        {
            "preferences": [
                {
                    "user_id": "u1",
                    "execution_mode": "inline_execution",
                    "observe_task_details": True,
                }
            ]
        }
    )

    trial_store = SqliteStateStore(sqlite_file, store_key="trial_state")
    trial_store.save(
        {
            "trials": [
                {
                    "id": "trial-1",
                    "user_id": "u1",
                    "session_id": "s1",
                    "template_id": "community/basic",
                    "started_at": "2026-03-25T12:00:00+00:00",
                    "expires_at": "2026-03-25T14:00:00+00:00",
                    "ttl_seconds": 7200,
                }
            ]
        }
    )

    retry_store = SqliteStateStore(sqlite_file, store_key="retry_state")
    retry_store.save(
        {
            "requests": [
                {
                    "id": "req-1",
                    "user_id": "u1",
                    "template_id": "community/basic",
                    "state": "queued",
                    "created_at": "2026-03-25T12:00:00+00:00",
                    "updated_at": "2026-03-25T12:00:00+00:00",
                    "version": 1,
                }
            ],
            "locks": [],
        }
    )

    audit_store = SqliteStateStore(sqlite_file, store_key="audit_state")
    audit_store.save(
        {
            "events": [
                {
                    "id": "event-1",
                    "action": "submission.approved",
                    "actor_id": "admin",
                    "actor_role": "admin",
                    "target_id": "sub-1",
                    "status": "approved",
                    "detail": {},
                    "created_at": "2026-03-25T12:00:00+00:00",
                }
            ]
        }
    )

    trial_request_store = SqliteStateStore(sqlite_file, store_key="trial_request_state")
    trial_request_store.save({"first_notice_sent_users": ["u1"]})

    notification_store = SqliteStateStore(sqlite_file, store_key="notification_state")
    notification_store.save(
        {"events": [{"channel": "user_dm", "target": "u1", "message": "hello"}]}
    )
    transfer_store = SqliteStateStore(sqlite_file, store_key="transfer_state")
    transfer_store.save(
        {
            "upload_jobs": [
                {
                    "job_id": "upload-1",
                    "direction": "upload",
                    "job_type": "template_submission_package",
                    "actor_id": "u1",
                    "actor_role": "member",
                    "user_id": "u1",
                    "logical_key": "upload:u1:key-1",
                    "status": "done",
                    "created_at": "2026-04-07T12:00:00+00:00",
                    "updated_at": "2026-04-07T12:00:01+00:00",
                }
            ],
            "download_jobs": [],
        }
    )

    assert SqlitePreferenceRepository(sqlite_file, legacy_state_store=pref_store).load_state()["preferences"][0][
        "user_id"
    ] == "u1"
    assert SqliteTrialRepository(sqlite_file, legacy_state_store=trial_store).load_state()["trials"][0][
        "id"
    ] == "trial-1"
    assert SqliteRetryQueueRepository(sqlite_file, legacy_state_store=retry_store).load_state()["requests"][0][
        "id"
    ] == "req-1"
    assert SqliteAuditRepository(sqlite_file, legacy_state_store=audit_store).load_state()["events"][0][
        "id"
    ] == "event-1"
    assert SqliteTrialRequestRepository(
        sqlite_file,
        legacy_state_store=trial_request_store,
    ).load_state()["first_notice_sent_users"] == ["u1"]
    assert SqliteNotifierRepository(
        sqlite_file,
        legacy_state_store=notification_store,
    ).load_state()["events"][0]["channel"] == "user_dm"
    assert SqliteTransferJobRepository(
        sqlite_file,
        legacy_state_store=transfer_store,
    ).load_state()["upload_jobs"][0]["job_id"] == "upload-1"


def test_retry_repository_concurrent_writes_keep_valid_state(tmp_path: Path) -> None:
    sqlite_file = tmp_path / "sharelife_state.sqlite3"
    request_ids = [f"req-{idx}" for idx in range(10)]

    def _write(request_id: str) -> None:
        repo = SqliteRetryQueueRepository(sqlite_file)
        repo.save_state(
            {
                "requests": [
                    {
                        "id": request_id,
                        "user_id": "u1",
                        "template_id": "community/basic",
                        "state": "queued",
                        "created_at": "2026-03-25T12:00:00+00:00",
                        "updated_at": "2026-03-25T12:00:00+00:00",
                        "version": 1,
                    }
                ],
                "locks": [],
            }
        )

    with ThreadPoolExecutor(max_workers=5) as pool:
        list(pool.map(_write, request_ids))

    state = SqliteRetryQueueRepository(sqlite_file).load_state()
    assert len(state["requests"]) == 1
    assert state["requests"][0]["id"] in set(request_ids)


def test_operational_repositories_create_indexes(tmp_path: Path) -> None:
    sqlite_file = tmp_path / "sharelife_state.sqlite3"
    SqlitePreferenceRepository(sqlite_file)
    SqliteTrialRepository(sqlite_file)
    SqliteRetryQueueRepository(sqlite_file)
    SqliteAuditRepository(sqlite_file)
    SqliteTrialRequestRepository(sqlite_file)
    SqliteNotifierRepository(sqlite_file)
    SqliteTransferJobRepository(sqlite_file)

    with sqlite3.connect(str(sqlite_file)) as conn:
        pref_indexes = {row[1] for row in conn.execute("PRAGMA index_list('sharelife_preferences')")}
        trial_indexes = {row[1] for row in conn.execute("PRAGMA index_list('sharelife_trials')")}
        retry_indexes = {row[1] for row in conn.execute("PRAGMA index_list('sharelife_retry_requests')")}
        audit_indexes = {row[1] for row in conn.execute("PRAGMA index_list('sharelife_audit_events')")}
        trial_request_indexes = {
            row[1] for row in conn.execute("PRAGMA index_list('sharelife_trial_request_notices')")
        }
        notification_indexes = {
            row[1] for row in conn.execute("PRAGMA index_list('sharelife_notification_events')")
        }
        upload_job_indexes = {row[1] for row in conn.execute("PRAGMA index_list('sharelife_upload_jobs')")}
        download_job_indexes = {row[1] for row in conn.execute("PRAGMA index_list('sharelife_download_jobs')")}

    assert "idx_preferences_execution_mode" in pref_indexes
    assert "idx_trials_user_template" in trial_indexes
    assert "idx_retry_requests_state" in retry_indexes
    assert "idx_audit_events_action" in audit_indexes
    assert "idx_trial_request_notices_user_id" in trial_request_indexes
    assert "idx_notification_events_channel" in notification_indexes
    assert "idx_upload_jobs_logical_key" in upload_job_indexes
    assert "idx_download_jobs_logical_key" in download_job_indexes
