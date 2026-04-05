#!/usr/bin/env python3
"""Minimal hot-reload runner for local plugin development."""

from __future__ import annotations

import argparse
import shlex
import subprocess
import time
from pathlib import Path


def snapshot_mtime(root: Path, patterns: tuple[str, ...]) -> dict[str, float]:
    rows: dict[str, float] = {}
    for pattern in patterns:
        for path in root.rglob(pattern):
            if not path.is_file():
                continue
            rows[str(path)] = path.stat().st_mtime
    return rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run command and restart when source files change.")
    parser.add_argument("--watch", default=".", help="directory to watch recursively")
    parser.add_argument("--cmd", required=True, help="command to run")
    parser.add_argument("--interval", type=float, default=1.0, help="poll interval in seconds")
    parser.add_argument(
        "--patterns",
        default="*.py,*.yaml,*.yml,*.json,*.md",
        help="comma-separated glob patterns",
    )
    parser.add_argument("--dry-run", action="store_true", help="print config and exit")
    parser.add_argument(
        "--max-restarts",
        type=int,
        default=0,
        help="optional max restarts for test environments (0 means unlimited)",
    )
    return parser.parse_args()


def run() -> int:
    args = parse_args()
    watch_root = Path(args.watch).expanduser().resolve()
    patterns = tuple(item.strip() for item in str(args.patterns or "").split(",") if item.strip())
    cmd = shlex.split(str(args.cmd))

    if args.dry_run:
        print(f"watch={watch_root}")
        print(f"patterns={','.join(patterns)}")
        print(f"cmd={' '.join(cmd)}")
        print("mode=dry-run")
        return 0

    previous = snapshot_mtime(watch_root, patterns)
    process = subprocess.Popen(cmd)
    restarts = 0
    print(f"[hot-reload] started pid={process.pid} cmd={' '.join(cmd)}")
    try:
        while True:
            time.sleep(max(0.2, float(args.interval)))
            current = snapshot_mtime(watch_root, patterns)
            if current != previous:
                previous = current
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
                restarts += 1
                if args.max_restarts > 0 and restarts > args.max_restarts:
                    print("[hot-reload] max-restarts reached, exiting")
                    return 0
                process = subprocess.Popen(cmd)
                print(f"[hot-reload] restarted pid={process.pid} count={restarts}")

            if process.poll() is not None:
                print(f"[hot-reload] process exited with code={process.returncode}")
                return int(process.returncode or 0)
    except KeyboardInterrupt:
        process.terminate()
        return 130


if __name__ == "__main__":
    raise SystemExit(run())
