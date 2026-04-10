from datetime import UTC, datetime
from pathlib import Path
import subprocess

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


def test_storage_service_restore_prepare_rehydrates_from_remote_when_local_artifact_missing(tmp_path, monkeypatch):
    transferred: list[list[str]] = []
    source_bytes = {"value": b""}

    def _fake_run(command, **kwargs):
        transferred.append(list(command))
        if len(transferred) == 1:
            return subprocess.CompletedProcess(args=command, returncode=0, stdout="backup sync ok", stderr="")
        if len(transferred) == 2:
            return subprocess.CompletedProcess(args=command, returncode=0, stdout="retention ok", stderr="")
        target_path = command[3]
        with open(target_path, "wb") as handle:
            handle.write(source_bytes["value"])
        return subprocess.CompletedProcess(args=command, returncode=0, stdout="restore sync ok", stderr="")

    monkeypatch.setattr(subprocess, "run", _fake_run)
    service = StorageBackupService(
        state_store=InMemoryStateStore(),
        data_root=tmp_path,
        clock=FrozenClock(datetime(2026, 4, 4, 12, 0, tzinfo=UTC)),
    )
    service.set_policies(
        {
            "sync_remote_enabled": True,
            "remote_required": True,
            "encryption_required": False,
            "rclone_binary": "rclone",
            "rclone_remote_path": "gdrive:/sharelife-backup",
        },
        actor_id="admin-1",
    )

    started = service.run_backup_job(actor_id="admin-1")
    assert "job" in started
    artifact_path = started["job"]["artifact_path"]
    with open(artifact_path, "rb") as handle:
        source_bytes["value"] = handle.read()
    assert source_bytes["value"]
    Path(artifact_path).unlink()

    prepared = service.restore_prepare(
        artifact_ref=started["job"]["artifact_id"],
        actor_id="admin-1",
        note="remote restore fallback",
    )
    assert "error" not in prepared
    assert prepared["restore"]["rehydrated_from_remote"] is True
    assert prepared["restore"]["remote_restore"]["status"] == "succeeded"
    assert Path(prepared["restore"]["artifact_path"]).exists()
    assert any(cmd[0:2] == ["rclone", "copyto"] for cmd in transferred)


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
            "encryption_required": False,
            "rclone_binary": "definitely-not-existing-rclone-binary",
            "rclone_remote_path": "gdrive:/sharelife-backup",
        },
        actor_id="admin-1",
    )
    started = service.run_backup_job(actor_id="admin-1")
    assert "job" in started
    assert started["job"]["status"] == "failed"
    assert started["job"]["reason"] == "remote_sync_command_not_found"


def test_storage_service_remote_sync_enforces_encrypted_remote_when_required(tmp_path):
    service = StorageBackupService(
        state_store=InMemoryStateStore(),
        data_root=tmp_path,
        clock=FrozenClock(datetime(2026, 4, 4, 12, 0, tzinfo=UTC)),
    )
    service.set_policies(
        {
            "sync_remote_enabled": True,
            "remote_required": True,
            "encryption_required": True,
            "rclone_remote_path": "gdrive:/sharelife-backup",
        },
        actor_id="admin-1",
    )
    started = service.run_backup_job(actor_id="admin-1")
    assert "job" in started
    assert started["job"]["status"] == "failed"
    assert started["job"]["reason"] == "remote_encryption_required"


def test_storage_service_remote_retention_executes_rclone_delete_after_sync(tmp_path, monkeypatch):
    calls: list[list[str]] = []

    def _fake_run(command, **kwargs):
        calls.append(list(command))
        return subprocess.CompletedProcess(args=command, returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr(subprocess, "run", _fake_run)
    service = StorageBackupService(
        state_store=InMemoryStateStore(),
        data_root=tmp_path,
        clock=FrozenClock(datetime(2026, 4, 4, 12, 0, tzinfo=UTC)),
    )
    service.set_policies(
        {
            "sync_remote_enabled": True,
            "remote_required": True,
            "encryption_required": False,
            "remote_retention_days": 7,
            "rclone_binary": "rclone",
            "rclone_remote_path": "gdrive:/sharelife-backup",
        },
        actor_id="admin-1",
    )
    started = service.run_backup_job(actor_id="admin-1")
    assert started["job"]["status"] == "succeeded"
    assert started["job"]["remote_retention"]["status"] == "succeeded"
    assert len(calls) >= 2
    assert calls[0][0:2] == ["rclone", "copyto"]
    assert calls[1][0:2] == ["rclone", "delete"]
    assert "--min-age" in calls[1]
    assert "7d" in calls[1]


def test_storage_service_remote_retention_failure_does_not_fail_backup_job(tmp_path, monkeypatch):
    call_index = {"value": 0}

    def _fake_run(command, **kwargs):
        call_index["value"] += 1
        if call_index["value"] == 1:
            return subprocess.CompletedProcess(args=command, returncode=0, stdout="copy ok", stderr="")
        return subprocess.CompletedProcess(args=command, returncode=11, stdout="", stderr="retention failed")

    monkeypatch.setattr(subprocess, "run", _fake_run)
    service = StorageBackupService(
        state_store=InMemoryStateStore(),
        data_root=tmp_path,
        clock=FrozenClock(datetime(2026, 4, 4, 12, 0, tzinfo=UTC)),
    )
    service.set_policies(
        {
            "sync_remote_enabled": True,
            "remote_required": True,
            "encryption_required": False,
            "remote_retention_days": 7,
            "rclone_binary": "rclone",
            "rclone_remote_path": "gdrive:/sharelife-backup",
        },
        actor_id="admin-1",
    )
    started = service.run_backup_job(actor_id="admin-1")
    assert started["job"]["status"] == "succeeded"
    assert started["job"]["remote_retention"]["status"] == "failed"
    assert started["job"]["remote_retention"]["error"] == "remote_retention_failed"
