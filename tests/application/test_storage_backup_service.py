from datetime import UTC, datetime

from sharelife.application.services_storage_backup import StorageBackupService


class FrozenClock:
    def __init__(self, start: datetime):
        self.current = start

    def utcnow(self) -> datetime:
        return self.current


class InMemoryStateStore:
    def __init__(self):
        self.payload = {}

    def load(self, default):
        if not self.payload:
            return dict(default)
        return dict(self.payload)

    def save(self, payload):
        self.payload = dict(payload)


def test_storage_service_summary_and_policy_update(tmp_path):
    (tmp_path / "a.txt").write_text("abc", encoding="utf-8")
    (tmp_path / "nested").mkdir(parents=True, exist_ok=True)
    (tmp_path / "nested" / "b.txt").write_text("defg", encoding="utf-8")

    service = StorageBackupService(
        state_store=InMemoryStateStore(),
        data_root=tmp_path,
        clock=FrozenClock(datetime(2026, 4, 4, 12, 0, tzinfo=UTC)),
    )

    summary = service.get_local_summary()
    assert summary["root_exists"] is True
    assert summary["scanned_file_count"] >= 2
    assert summary["estimated_size_bytes"] >= 7

    updated = service.set_policies(
        {
            "rpo_hours": 12,
            "daily_upload_budget_gb": 650,
            "rclone_remote_path": "gdrive-crypt:/sharelife-backup",
        },
        actor_id="admin-1",
    )
    assert "error" not in updated
    assert updated["policies"]["rpo_hours"] == 12
    assert updated["policies"]["daily_upload_budget_gb"] == 650
    assert updated["policies"]["rclone_remote_path"] == "gdrive-crypt:/sharelife-backup"
    assert updated["policies"]["last_updated_by"] == "admin-1"


def test_storage_service_backup_job_lock_guard(tmp_path):
    store = InMemoryStateStore()
    store.save(
        {
            "policies": {"single_active_backup_lock": True},
            "backup_jobs": [
                {"job_id": "backup-1", "status": "running", "created_at": "2026-04-04T10:00:00+00:00"}
            ],
        }
    )
    service = StorageBackupService(
        state_store=store,
        data_root=tmp_path,
        clock=FrozenClock(datetime(2026, 4, 4, 12, 0, tzinfo=UTC)),
    )

    started = service.run_backup_job(actor_id="admin-1")
    assert started["error"] == "backup_job_in_progress"


def test_storage_service_restore_prepare_commit_cancel(tmp_path):
    service = StorageBackupService(
        state_store=InMemoryStateStore(),
        data_root=tmp_path,
        clock=FrozenClock(datetime(2026, 4, 4, 12, 0, tzinfo=UTC)),
    )
    started = service.run_backup_job(actor_id="admin-1")
    assert "job" in started
    artifact_id = started["job"]["artifact_id"]

    prepared = service.restore_prepare(
        artifact_ref=artifact_id,
        actor_id="admin-1",
        note="canary restore",
    )
    assert "error" not in prepared
    restore_id = prepared["restore"]["restore_id"]
    assert prepared["restore"]["restore_state"] == "prepared"

    committed = service.restore_commit(restore_id=restore_id, actor_id="admin-1")
    assert "error" not in committed
    assert committed["restore"]["restore_state"] == "committed"

    cancelled_after_commit = service.restore_cancel(restore_id=restore_id, actor_id="admin-1")
    assert cancelled_after_commit["error"] == "restore_state_invalid"


def test_storage_service_remote_sync_reports_missing_rclone_binary(tmp_path):
    service = StorageBackupService(
        state_store=InMemoryStateStore(),
        data_root=tmp_path,
        clock=FrozenClock(datetime(2026, 4, 4, 12, 0, tzinfo=UTC)),
    )
    service.set_policies(
        {
            "sync_remote_enabled": True,
            "remote_required": True,
            "rclone_binary": "definitely-not-existing-rclone-binary",
            "rclone_remote_path": "gdrive:/sharelife-backup",
        },
        actor_id="admin-1",
    )
    started = service.run_backup_job(actor_id="admin-1")
    assert "job" in started
    assert started["job"]["status"] == "failed"
    assert started["job"]["reason"] == "remote_sync_command_not_found"
