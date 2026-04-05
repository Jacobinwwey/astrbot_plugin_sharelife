#!/usr/bin/env python3
"""Migrate legacy JSON service state files into a single SQLite state store."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sharelife.infrastructure.sqlite_state_store import SqliteStateStore


def state_store_filenames() -> dict[str, str]:
    return {
        "preference_state": "preference_state.json",
        "retry_state": "retry_state.json",
        "trial_state": "trial_state.json",
        "trial_request_state": "trial_request_state.json",
        "notification_state": "notification_state.json",
        "market_state": "market_state.json",
        "audit_state": "audit_state.json",
        "profile_pack_state": "profile_pack_state.json",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Migrate Sharelife JSON state to SQLite")
    parser.add_argument(
        "--data-root",
        default=str(Path.cwd() / ".sharelife_data" / "sharelife"),
        help="Root directory containing legacy *_state.json files",
    )
    parser.add_argument(
        "--sqlite-file",
        default="",
        help="Target sqlite file path. Empty => {data-root}/sharelife_state.sqlite3",
    )
    parser.add_argument(
        "--overwrite-existing",
        action="store_true",
        help="Overwrite existing sqlite keys with JSON file contents",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    data_root = Path(str(args.data_root)).expanduser().resolve()
    sqlite_file = str(args.sqlite_file or "").strip()
    sqlite_path = Path(sqlite_file).expanduser().resolve() if sqlite_file else (data_root / "sharelife_state.sqlite3")

    mapping = state_store_filenames()
    migrated = 0
    skipped = 0
    missing = 0

    print(f"[sharelife] migrate state root={data_root}")
    print(f"[sharelife] target sqlite={sqlite_path}")
    for store_key, filename in mapping.items():
        source_path = data_root / filename
        store = SqliteStateStore(sqlite_path, store_key=store_key)
        if not source_path.exists():
            missing += 1
            print(f"- {store_key}: source missing ({source_path.name})")
            continue

        if args.overwrite_existing:
            imported = store.import_from_json_file(source_path)
            if not imported and store.has_state():
                import json

                payload = json.loads(source_path.read_text(encoding="utf-8"))
                if isinstance(payload, dict):
                    store.save(payload)
                    imported = True
            if imported:
                migrated += 1
                print(f"- {store_key}: migrated (overwrite mode)")
            else:
                skipped += 1
                print(f"- {store_key}: skipped (invalid json)")
            continue

        imported = store.import_from_json_file(source_path)
        if imported:
            migrated += 1
            print(f"- {store_key}: migrated")
        else:
            skipped += 1
            print(f"- {store_key}: skipped (already exists or invalid source)")

    print(
        f"[sharelife] done migrated={migrated} skipped={skipped} missing={missing} sqlite={sqlite_path}",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
