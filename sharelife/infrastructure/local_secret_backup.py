"""Encrypted local secret backup helpers for off-site cold storage."""

from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path


@dataclass(frozen=True)
class LocalSecretBackupResult:
    source_path: Path
    remote_encrypted_path: str
    remote_manifest_path: str
    artifact_name: str
    manifest_name: str
    plaintext_sha256: str
    ciphertext_sha256: str


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 128), b""):
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _run_checked(command: list[str], *, timeout_seconds: int) -> None:
    subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
    )


def _rclone_rcat_file(
    local_path: Path,
    remote_path: str,
    *,
    rclone_binary: str,
    timeout_seconds: int,
) -> None:
    with local_path.open("rb") as handle:
        subprocess.run(
            [rclone_binary, "rcat", remote_path],
            check=True,
            stdin=handle,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )


def build_local_secret_backup_names(prefix: str, *, now: datetime | None = None) -> tuple[str, str]:
    current = now.astimezone(UTC) if now is not None else datetime.now(tz=UTC)
    stamp = current.strftime("%Y%m%dT%H%M%SZ")
    return (
        f"{prefix}-{stamp}.toml.enc",
        f"{prefix}-{stamp}.manifest.json",
    )


def backup_local_webui_auth(
    *,
    source_path: str | Path,
    passphrase_file: str | Path,
    remote_path: str,
    rclone_binary: str = "rclone",
    openssl_binary: str = "openssl",
    timeout_seconds: int = 120,
    now: datetime | None = None,
) -> LocalSecretBackupResult:
    source = Path(source_path).expanduser().resolve()
    passphrase = Path(passphrase_file).expanduser().resolve()
    remote = str(remote_path or "").strip().rstrip("/")
    if not source.is_file():
        raise FileNotFoundError(f"local auth file not found: {source}")
    if not passphrase.is_file():
        raise FileNotFoundError(f"backup passphrase file not found: {passphrase}")
    if ":" not in remote:
        raise ValueError("remote_path must be an rclone remote path like 'gdrive:/sharelife/secrets'")

    artifact_name, manifest_name = build_local_secret_backup_names("sharelife-webui-auth", now=now)
    plaintext_sha256 = _sha256_file(source)

    with tempfile.TemporaryDirectory(prefix="sharelife-auth-backup-") as temp_dir:
        temp_root = Path(temp_dir)
        encrypted_path = temp_root / artifact_name
        manifest_path = temp_root / manifest_name

        _run_checked(
            [
                openssl_binary,
                "enc",
                "-aes-256-cbc",
                "-pbkdf2",
                "-salt",
                "-in",
                str(source),
                "-out",
                str(encrypted_path),
                "-pass",
                f"file:{passphrase}",
            ],
            timeout_seconds=timeout_seconds,
        )
        ciphertext_sha256 = _sha256_file(encrypted_path)

        created_at = now.astimezone(UTC) if now is not None else datetime.now(tz=UTC)
        manifest_path.write_text(
            json.dumps(
                {
                    "kind": "sharelife_local_webui_auth_backup",
                    "created_at": created_at.isoformat(),
                    "source_name": source.name,
                    "artifact_name": artifact_name,
                    "plaintext_sha256": plaintext_sha256,
                    "ciphertext_sha256": ciphertext_sha256,
                    "encryption": {
                        "tool": "openssl",
                        "algorithm": "aes-256-cbc",
                        "kdf": "pbkdf2",
                        "salt": True,
                    },
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        remote_encrypted_path = f"{remote}/{artifact_name}"
        remote_manifest_path = f"{remote}/{manifest_name}"
        _rclone_rcat_file(
            encrypted_path,
            remote_encrypted_path,
            rclone_binary=rclone_binary,
            timeout_seconds=timeout_seconds,
        )
        _rclone_rcat_file(
            manifest_path,
            remote_manifest_path,
            rclone_binary=rclone_binary,
            timeout_seconds=timeout_seconds,
        )

    return LocalSecretBackupResult(
        source_path=source,
        remote_encrypted_path=remote_encrypted_path,
        remote_manifest_path=remote_manifest_path,
        artifact_name=artifact_name,
        manifest_name=manifest_name,
        plaintext_sha256=plaintext_sha256,
        ciphertext_sha256=ciphertext_sha256,
    )
