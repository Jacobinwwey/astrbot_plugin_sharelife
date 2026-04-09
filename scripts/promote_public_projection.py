#!/usr/bin/env python3
from __future__ import annotations

import argparse
import fnmatch
import glob
import json
import shutil
import sys
from pathlib import Path, PurePosixPath
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST_PATH = REPO_ROOT / "ops" / "public_projection_manifest.json"


def _normalize_patterns(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    out: list[str] = []
    seen: set[str] = set()
    for item in value:
        text = str(item or "").strip().replace("\\", "/")
        if not text or text in seen:
            continue
        seen.add(text)
        out.append(text)
    return out


def load_manifest(path: str | Path = DEFAULT_MANIFEST_PATH) -> dict[str, list[str]]:
    resolved = Path(path).expanduser().resolve()
    payload = json.loads(resolved.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("projection manifest root must be a JSON object")
    return {
        "managed_roots": _normalize_patterns(payload.get("managed_roots", [])),
        "include": _normalize_patterns(payload.get("include", [])),
        "exclude": _normalize_patterns(payload.get("exclude", [])),
    }


def _path_matches(path: str, pattern: str) -> bool:
    normalized = path.replace("\\", "/")
    pure = PurePosixPath(normalized)
    return pure.match(pattern) or fnmatch.fnmatch(normalized, pattern)


def _expand_file_matches(root: Path, patterns: list[str]) -> set[str]:
    files: set[str] = set()
    for pattern in patterns:
        if not pattern:
            continue
        matches = glob.glob(str(root / pattern), recursive=True)
        for raw in matches:
            path = Path(raw)
            if path.is_file():
                files.add(path.relative_to(root).as_posix())
                continue
            if path.is_dir():
                for child in path.rglob("*"):
                    if child.is_file():
                        files.add(child.relative_to(root).as_posix())
    return files


def resolve_projection_files(source_root: str | Path, manifest: dict[str, list[str]]) -> list[str]:
    root = Path(source_root).expanduser().resolve()
    include = _normalize_patterns(manifest.get("include", []))
    exclude = _normalize_patterns(manifest.get("exclude", []))
    files = _expand_file_matches(root, include)
    projected = [
        path for path in sorted(files)
        if not any(_path_matches(path, pattern) for pattern in exclude)
    ]
    return projected


def _list_managed_destination_files(dest_root: Path, managed_roots: list[str]) -> set[str]:
    return _expand_file_matches(dest_root, managed_roots)


def build_projection_plan(
    *,
    source_root: str | Path,
    dest_root: str | Path,
    manifest: dict[str, list[str]],
) -> dict[str, Any]:
    normalized_source_root = Path(source_root).expanduser().resolve()
    normalized_dest_root = Path(dest_root).expanduser().resolve()
    projected_files = resolve_projection_files(normalized_source_root, manifest)
    projected_set = set(projected_files)

    copy_paths: list[str] = []
    update_paths: list[str] = []
    for relative_path in projected_files:
        source_path = normalized_source_root / relative_path
        dest_path = normalized_dest_root / relative_path
        if not dest_path.exists():
            copy_paths.append(relative_path)
            continue
        if source_path.read_bytes() != dest_path.read_bytes():
            update_paths.append(relative_path)

    managed_roots = _normalize_patterns(manifest.get("managed_roots", []))
    dest_managed_files = _list_managed_destination_files(normalized_dest_root, managed_roots)
    remove_paths = sorted(dest_managed_files - projected_set)
    return {
        "source_root": str(normalized_source_root),
        "dest_root": str(normalized_dest_root),
        "projected_files_count": len(projected_files),
        "projected_paths": projected_files,
        "copy_paths": sorted(copy_paths),
        "update_paths": sorted(update_paths),
        "remove_paths": remove_paths,
        "managed_roots": managed_roots,
    }


def _prune_empty_dirs(start: Path, stop: Path) -> None:
    current = start
    while current != stop and current.exists():
        try:
            current.rmdir()
        except OSError:
            break
        current = current.parent


def apply_projection_plan(
    *,
    source_root: str | Path,
    dest_root: str | Path,
    plan: dict[str, Any],
    delete: bool = True,
) -> dict[str, Any]:
    normalized_source_root = Path(source_root).expanduser().resolve()
    normalized_dest_root = Path(dest_root).expanduser().resolve()
    copied = 0
    updated = 0
    removed = 0

    for relative_path in plan.get("copy_paths", []):
        source_path = normalized_source_root / relative_path
        dest_path = normalized_dest_root / relative_path
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, dest_path)
        copied += 1

    for relative_path in plan.get("update_paths", []):
        source_path = normalized_source_root / relative_path
        dest_path = normalized_dest_root / relative_path
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, dest_path)
        updated += 1

    if delete:
        for relative_path in plan.get("remove_paths", []):
            dest_path = normalized_dest_root / relative_path
            if not dest_path.exists():
                continue
            dest_path.unlink()
            removed += 1
            _prune_empty_dirs(dest_path.parent, normalized_dest_root)

    return {
        **plan,
        "copied": copied,
        "updated": updated,
        "removed": removed,
        "delete": delete,
    }


def _print_summary(report: dict[str, Any]) -> None:
    print(
        "[public-projection] "
        f"projected={report['projected_files_count']} "
        f"copy={len(report['copy_paths'])} "
        f"update={len(report['update_paths'])} "
        f"remove={len(report['remove_paths'])}"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Project the private repository into a sanitized public mirror using an allowlist manifest."
    )
    parser.add_argument("--source-root", default=str(REPO_ROOT), help="Private repo root")
    parser.add_argument("--dest-root", required=True, help="Public mirror repo root")
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST_PATH), help="Projection manifest path")
    parser.add_argument("--dry-run", action="store_true", help="Calculate projection without writing files")
    parser.add_argument("--no-delete", action="store_true", help="Do not remove stale managed files from destination")
    parser.add_argument("--json-output", default="", help="Optional JSON report output path")
    args = parser.parse_args(argv)

    manifest = load_manifest(args.manifest)
    plan = build_projection_plan(
        source_root=args.source_root,
        dest_root=args.dest_root,
        manifest=manifest,
    )
    delete = not args.no_delete
    if args.dry_run:
        report = {
            **plan,
            "copied": 0,
            "updated": 0,
            "removed": 0,
            "dry_run": True,
            "delete": delete,
        }
    else:
        report = apply_projection_plan(
            source_root=args.source_root,
            dest_root=args.dest_root,
            plan=plan,
            delete=delete,
        )
        report["dry_run"] = False

    _print_summary(report)
    if args.json_output:
        output_path = Path(args.json_output).expanduser().resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"[public-projection] wrote report: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
