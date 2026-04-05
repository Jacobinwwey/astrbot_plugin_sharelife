#!/usr/bin/env python3
"""Create a local-only WebUI auth TOML template outside tracked config."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sharelife.infrastructure.local_webui_auth import (  # noqa: E402
    ensure_local_webui_auth_template,
    resolve_local_webui_auth_path,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scaffold a local-only Sharelife WebUI auth TOML file")
    parser.add_argument(
        "--data-root",
        default=str(REPO_ROOT / "output" / "standalone-data"),
        help="Sharelife data root used to place the local secret file under data_root/secrets/",
    )
    parser.add_argument(
        "--path",
        default="",
        help="Explicit file path override. Defaults to <data-root>/secrets/webui-auth.local.toml",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    path = Path(str(args.path)).expanduser().resolve() if str(args.path or "").strip() else resolve_local_webui_auth_path(args.data_root)
    created = ensure_local_webui_auth_template(path)
    print(created)


if __name__ == "__main__":
    main()
