#!/usr/bin/env python3
from __future__ import annotations

import shutil
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_ROOT = REPO_ROOT / "docs"

TARGETS = (
    DOCS_ROOT / ".vitepress" / ".temp",
    DOCS_ROOT / ".vitepress" / "cache",
    DOCS_ROOT / ".vitepress" / "dist",
)


def main() -> int:
    for target in TARGETS:
        if target.exists():
            shutil.rmtree(target, ignore_errors=True)
            print(f"[docs-clean] removed: {target}")
        else:
            print(f"[docs-clean] skip (not found): {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
