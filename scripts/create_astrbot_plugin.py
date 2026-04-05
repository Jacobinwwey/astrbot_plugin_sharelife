#!/usr/bin/env python3
"""Scaffold a minimal AstrBot plugin project for fast local iteration."""

from __future__ import annotations

import argparse
from pathlib import Path


def _safe_name(value: str) -> str:
    text = "".join(ch for ch in str(value or "").strip() if ch.isalnum() or ch in {"_", "-"})
    return text.replace("-", "_")


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_scaffold(*, root: Path, plugin_name: str, author: str, description: str, force: bool) -> Path:
    normalized_name = _safe_name(plugin_name)
    if not normalized_name:
        raise ValueError("plugin name is required")
    target = root / normalized_name
    if target.exists() and not force:
        raise FileExistsError(f"target already exists: {target}")
    target.mkdir(parents=True, exist_ok=True)

    package_name = normalized_name
    register_name = normalized_name
    human_name = normalized_name.replace("_", " ").title()
    version = "0.1.0"
    short_desc = (description or f"{human_name} plugin scaffold").strip()

    _write(
        target / "main.py",
        f"""from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star, register


@register(
    "{register_name}",
    "{author}",
    "{short_desc}",
    "{version}",
)
class {human_name.replace(" ", "")}Plugin(Star):
    def __init__(self, context: Context, config: dict | None = None):
        super().__init__(context, config=config)
        self.config = config or {{}}

    @filter.command("{register_name}")
    async def {package_name}_entry(self, event: AstrMessageEvent):
        yield event.plain_result("{human_name} ready")
""",
    )
    _write(
        target / "metadata.yaml",
        f"""name: {register_name}
author: {author}
desc: {short_desc}
version: v{version}
""",
    )
    _write(
        target / "README.md",
        f"""# {human_name}

## Quick Start

1. Drop this folder into AstrBot plugin directory.
2. Enable plugin in AstrBot.
3. Run `/{register_name}` in chat to verify command registration.
""",
    )
    _write(
        target / "tests" / "test_smoke.py",
        f"""from pathlib import Path


def test_scaffold_files_exist():
    root = Path(__file__).resolve().parents[1]
    assert (root / "main.py").exists()
    assert (root / "metadata.yaml").exists()
""",
    )
    return target


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a minimal AstrBot plugin scaffold.")
    parser.add_argument("--name", required=True, help="plugin folder/name, e.g. astrbot_plugin_demo")
    parser.add_argument("--author", default="sharelife", help="plugin author")
    parser.add_argument("--description", default="", help="short plugin description")
    parser.add_argument("--output", default=".", help="output directory")
    parser.add_argument("--force", action="store_true", help="overwrite existing target directory")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    target = build_scaffold(
        root=Path(args.output).expanduser().resolve(),
        plugin_name=args.name,
        author=str(args.author or "sharelife"),
        description=str(args.description or ""),
        force=bool(args.force),
    )
    print(f"scaffold created: {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
