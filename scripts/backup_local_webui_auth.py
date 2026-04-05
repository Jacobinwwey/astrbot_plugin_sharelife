#!/usr/bin/env python3
"""Encrypt and back up the local-only WebUI auth TOML file via rclone."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sharelife.infrastructure.local_secret_backup import backup_local_webui_auth  # noqa: E402
from sharelife.infrastructure.local_webui_auth import resolve_local_webui_auth_path  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Encrypt and upload Sharelife local WebUI auth TOML to an rclone remote")
    parser.add_argument(
        "--data-root",
        default=str(REPO_ROOT / "output" / "standalone-data"),
        help="Sharelife data root used when resolving the default source path",
    )
    parser.add_argument(
        "--source",
        default="",
        help="Explicit source path. Defaults to <data-root>/secrets/webui-auth.local.toml",
    )
    parser.add_argument(
        "--passphrase-file",
        required=True,
        help="Path to a local file containing the backup encryption passphrase",
    )
    parser.add_argument(
        "--remote",
        required=True,
        help="Destination rclone remote path, for example gdrive:/sharelife/secrets",
    )
    parser.add_argument("--rclone-binary", default="rclone")
    parser.add_argument("--openssl-binary", default="openssl")
    parser.add_argument("--timeout-seconds", type=int, default=120)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    source = Path(str(args.source)).expanduser().resolve() if str(args.source or "").strip() else resolve_local_webui_auth_path(args.data_root)
    result = backup_local_webui_auth(
        source_path=source,
        passphrase_file=args.passphrase_file,
        remote_path=args.remote,
        rclone_binary=args.rclone_binary,
        openssl_binary=args.openssl_binary,
        timeout_seconds=int(args.timeout_seconds),
    )
    print(result.remote_encrypted_path)
    print(result.remote_manifest_path)


if __name__ == "__main__":
    main()
