#!/usr/bin/env python3
"""Archive the sanitized public market and optionally sync it to an rclone remote."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sharelife.infrastructure.public_market_backup import backup_public_market_directory  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Archive docs/public/market and optionally upload the sanitized backup via rclone",
    )
    parser.add_argument(
        "--source",
        default=str(REPO_ROOT / "docs" / "public" / "market"),
        help="Directory containing sanitized public market artifacts",
    )
    parser.add_argument(
        "--archive-output-dir",
        default=str(REPO_ROOT / "output" / "public-market-backups"),
        help="Local directory for generated archive + manifest",
    )
    parser.add_argument(
        "--remote",
        default="",
        help="Optional rclone remote path, for example gdrive:/sharelife/public-market",
    )
    parser.add_argument("--rclone-binary", default="rclone")
    parser.add_argument("--rclone-bwlimit", default="")
    parser.add_argument("--timeout-seconds", type=int, default=300)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = backup_public_market_directory(
        source_dir=args.source,
        archive_output_dir=args.archive_output_dir,
        remote_path=args.remote,
        rclone_binary=args.rclone_binary,
        rclone_bwlimit=args.rclone_bwlimit,
        timeout_seconds=int(args.timeout_seconds),
    )
    print(result.archive_path)
    print(result.manifest_path)
    if result.remote_archive_path:
        print(result.remote_archive_path)
    if result.remote_manifest_path:
        print(result.remote_manifest_path)


if __name__ == "__main__":
    main()
