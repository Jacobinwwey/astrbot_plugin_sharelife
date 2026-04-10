"""Cold-backup helpers for sanitized public market artifacts."""

from __future__ import annotations

import hashlib
import json
import subprocess
import tarfile
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path


@dataclass(frozen=True)
class PublicMarketBackupResult:
    source_dir: Path
    archive_path: Path
    manifest_path: Path
    archive_name: str
    manifest_name: str
    archive_sha256: str
    source_manifest_sha256: str
    file_count: int
    remote_archive_path: str
    remote_manifest_path: str


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 128), b""):
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _normalize_remote_path(remote_path: str) -> str:
    remote = str(remote_path or "").strip().rstrip("/")
    if not remote:
        return ""
    if ":" not in remote:
        raise ValueError("remote_path must be an rclone remote path like 'gdrive:/sharelife/public-market'")
    return remote


def build_public_market_backup_names(
    prefix: str = "sharelife-public-market",
    *,
    now: datetime | None = None,
) -> tuple[str, str]:
    current = now.astimezone(UTC) if now is not None else datetime.now(tz=UTC)
    stamp = current.strftime("%Y%m%dT%H%M%SZ")
    return (
        f"{prefix}-{stamp}.tar.gz",
        f"{prefix}-{stamp}.manifest.json",
    )


def _source_entries(source_dir: Path) -> list[dict[str, object]]:
    entries: list[dict[str, object]] = []
    for path in sorted(source_dir.rglob("*")):
        if not path.is_file():
            continue
        entries.append(
            {
                "path": str(path.relative_to(source_dir)),
                "size_bytes": int(path.stat().st_size),
                "sha256": _sha256_file(path),
            }
        )
    return entries


def _source_manifest_sha(entries: list[dict[str, object]]) -> str:
    encoded = json.dumps(entries, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _snapshot_summary(source_dir: Path) -> dict[str, object]:
    snapshot_path = source_dir / "catalog.snapshot.json"
    if not snapshot_path.exists():
        return {
            "exists": False,
            "schema_version": "",
            "row_count": 0,
            "pipeline_trace_count": 0,
            "latest_pipeline_trace_id": "",
            "latest_pipeline_events": {},
        }
    try:
        payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
    except Exception:
        return {
            "exists": True,
            "schema_version": "",
            "row_count": 0,
            "pipeline_trace_count": 0,
            "latest_pipeline_trace_id": "",
            "latest_pipeline_events": {},
        }
    rows = payload.get("rows", [])
    normalized_rows = rows if isinstance(rows, list) else []
    pipeline_trace_ids: set[str] = set()
    latest_trace_id = ""
    latest_events: dict[str, object] = {}
    latest_at = ""
    for item in normalized_rows:
        if not isinstance(item, dict):
            continue
        trace_id = str(item.get("pipeline_trace_id", "") or "").strip()
        if trace_id:
            pipeline_trace_ids.add(trace_id)
        published_at = str(item.get("published_at", "") or "").strip()
        if not published_at:
            continue
        if published_at >= latest_at:
            latest_at = published_at
            latest_trace_id = trace_id
            events = item.get("pipeline_events")
            latest_events = dict(events) if isinstance(events, dict) else {}
    return {
        "exists": True,
        "schema_version": str(payload.get("schema_version", "") or ""),
        "row_count": len(normalized_rows),
        "pipeline_trace_count": len(pipeline_trace_ids),
        "latest_pipeline_trace_id": latest_trace_id,
        "latest_pipeline_events": latest_events,
    }


def _create_archive(source_dir: Path, archive_path: Path) -> None:
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive_path, "w:gz") as archive:
        archive.add(source_dir, arcname=source_dir.name, recursive=True)


def _rclone_copyto(
    local_path: Path,
    remote_path: str,
    *,
    rclone_binary: str,
    bwlimit: str,
    timeout_seconds: int,
) -> None:
    command = [rclone_binary]
    if str(bwlimit or "").strip():
        command.extend(["--bwlimit", str(bwlimit).strip()])
    command.extend(["copyto", str(local_path), remote_path])
    subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
    )


def backup_public_market_directory(
    *,
    source_dir: str | Path,
    archive_output_dir: str | Path,
    remote_path: str = "",
    rclone_binary: str = "rclone",
    rclone_bwlimit: str = "",
    timeout_seconds: int = 300,
    prefix: str = "sharelife-public-market",
    now: datetime | None = None,
) -> PublicMarketBackupResult:
    source = Path(source_dir).expanduser().resolve()
    output_dir = Path(archive_output_dir).expanduser().resolve()
    remote = _normalize_remote_path(remote_path)
    if not source.is_dir():
        raise FileNotFoundError(f"public market directory not found: {source}")

    archive_name, manifest_name = build_public_market_backup_names(prefix=prefix, now=now)
    archive_path = output_dir / archive_name
    manifest_path = output_dir / manifest_name
    output_dir.mkdir(parents=True, exist_ok=True)

    entries = _source_entries(source)
    source_manifest_sha256 = _source_manifest_sha(entries)
    _create_archive(source, archive_path)
    archive_sha256 = _sha256_file(archive_path)

    created_at = now.astimezone(UTC) if now is not None else datetime.now(tz=UTC)
    manifest = {
        "kind": "sharelife_public_market_backup",
        "created_at": created_at.isoformat(),
        "source_dir": str(source),
        "source_name": source.name,
        "archive_name": archive_name,
        "archive_sha256": archive_sha256,
        "file_count": len(entries),
        "source_manifest_sha256": source_manifest_sha256,
        "snapshot": _snapshot_summary(source),
        "entries": entries,
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    remote_archive_path = ""
    remote_manifest_path = ""
    if remote:
        remote_archive_path = f"{remote}/{archive_name}"
        remote_manifest_path = f"{remote}/{manifest_name}"
        _rclone_copyto(
            archive_path,
            remote_archive_path,
            rclone_binary=rclone_binary,
            bwlimit=rclone_bwlimit,
            timeout_seconds=timeout_seconds,
        )
        _rclone_copyto(
            manifest_path,
            remote_manifest_path,
            rclone_binary=rclone_binary,
            bwlimit=rclone_bwlimit,
            timeout_seconds=timeout_seconds,
        )

    return PublicMarketBackupResult(
        source_dir=source,
        archive_path=archive_path,
        manifest_path=manifest_path,
        archive_name=archive_name,
        manifest_name=manifest_name,
        archive_sha256=archive_sha256,
        source_manifest_sha256=source_manifest_sha256,
        file_count=len(entries),
        remote_archive_path=remote_archive_path,
        remote_manifest_path=remote_manifest_path,
    )
