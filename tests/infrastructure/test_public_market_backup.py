import json
import subprocess
import tarfile
from datetime import UTC, datetime
from pathlib import Path

from sharelife.infrastructure.public_market_backup import (
    backup_public_market_directory,
    build_public_market_backup_names,
)


def test_build_public_market_backup_names_uses_utc_timestamp():
    archive_name, manifest_name = build_public_market_backup_names(
        now=datetime(2026, 4, 5, 8, 15, 30, tzinfo=UTC),
    )

    assert archive_name == "sharelife-public-market-20260405T081530Z.tar.gz"
    assert manifest_name == "sharelife-public-market-20260405T081530Z.manifest.json"


def test_backup_public_market_directory_creates_local_archive_and_manifest(tmp_path):
    source_dir = tmp_path / "market"
    (source_dir / "packages" / "official").mkdir(parents=True, exist_ok=True)
    (source_dir / "packages" / "official" / "pack.zip").write_bytes(b"zip-bytes")
    (source_dir / "catalog.snapshot.json").write_text(
        json.dumps(
            {
                "schema_version": "v1",
                "rows": [
                    {
                        "pack_id": "profile/example",
                        "version": "1.0.0",
                        "published_at": "2026-04-05T08:00:00+00:00",
                        "pipeline_trace_id": "trace-1",
                        "pipeline_events": {
                            "decision": "pm-trace-1-decision",
                            "publish": "pm-trace-1-publish",
                            "snapshot": "pm-trace-1-snapshot",
                            "backup": "pm-trace-1-backup",
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    result = backup_public_market_directory(
        source_dir=source_dir,
        archive_output_dir=tmp_path / "backups",
        now=datetime(2026, 4, 5, 8, 15, 30, tzinfo=UTC),
    )

    assert result.archive_path.exists()
    assert result.manifest_path.exists()
    assert result.file_count == 2
    assert result.remote_archive_path == ""
    assert result.remote_manifest_path == ""

    with tarfile.open(result.archive_path, "r:gz") as archive:
      names = archive.getnames()
    assert "market/catalog.snapshot.json" in names
    assert "market/packages/official/pack.zip" in names

    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert manifest["kind"] == "sharelife_public_market_backup"
    assert manifest["snapshot"]["schema_version"] == "v1"
    assert manifest["snapshot"]["row_count"] == 1
    assert manifest["snapshot"]["pipeline_trace_count"] == 1
    assert manifest["snapshot"]["latest_pipeline_trace_id"] == "trace-1"
    assert manifest["snapshot"]["latest_pipeline_events"]["backup"] == "pm-trace-1-backup"


def test_backup_public_market_directory_syncs_archive_and_manifest_via_rclone(tmp_path, monkeypatch):
    source_dir = tmp_path / "market"
    source_dir.mkdir(parents=True, exist_ok=True)
    (source_dir / "catalog.snapshot.json").write_text(
        json.dumps({"schema_version": "v1", "rows": []}),
        encoding="utf-8",
    )
    calls = []

    def fake_run(cmd, check, capture_output, text, timeout):
        calls.append(list(cmd))
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr("sharelife.infrastructure.public_market_backup.subprocess.run", fake_run)

    result = backup_public_market_directory(
        source_dir=source_dir,
        archive_output_dir=tmp_path / "backups",
        remote_path="gdrive:/sharelife/public-market",
        rclone_bwlimit="8M",
        now=datetime(2026, 4, 5, 8, 15, 30, tzinfo=UTC),
    )

    assert result.remote_archive_path.endswith(".tar.gz")
    assert result.remote_manifest_path.endswith(".manifest.json")
    assert calls[0][:4] == ["rclone", "--bwlimit", "8M", "copyto"]
    assert calls[1][:4] == ["rclone", "--bwlimit", "8M", "copyto"]
