#!/usr/bin/env python3
"""Publish an already-sanitized profile-pack artifact into docs/public market."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path
import zipfile


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

DOCS_PUBLIC_DIR = REPO_ROOT / "docs" / "public"
DOCS_MARKET_DIR = DOCS_PUBLIC_DIR / "market"
DOCS_MARKET_ENTRIES_DIR = DOCS_MARKET_DIR / "entries"
DOCS_MARKET_COMMUNITY_PACKAGES_DIR = DOCS_MARKET_DIR / "packages" / "community"

from scripts.build_market_snapshot import build as build_market_snapshot  # noqa: E402


def _safe_slug(value: str) -> str:
    slug = "".join(char if char.isalnum() else "-" for char in str(value or "").strip().lower())
    slug = "-".join(part for part in slug.split("-") if part)
    return slug or "profile-pack"


def _package_metadata(path: Path) -> tuple[str, int]:
    return hashlib.sha256(path.read_bytes()).hexdigest(), path.stat().st_size


def _read_manifest(artifact_path: Path) -> dict:
    with zipfile.ZipFile(artifact_path, "r") as archive:
        return json.loads(archive.read("manifest.json").decode("utf-8"))


def _validate_public_artifact(artifact_path: Path, manifest: dict) -> None:
    redaction_policy = manifest.get("redaction_policy")
    if not isinstance(redaction_policy, dict):
        raise SystemExit("artifact manifest missing redaction_policy")
    redaction_mode = str(redaction_policy.get("mode", "") or "").strip()
    if redaction_mode not in {"exclude_secrets", "masked_secrets"}:
        raise SystemExit(
            "artifact redaction_policy.mode must be exclude_secrets or masked_secrets for public publish",
        )
    with zipfile.ZipFile(artifact_path, "r") as archive:
        names = sorted(archive.namelist())
        if "manifest.json" not in names:
            raise SystemExit("artifact missing manifest.json")
        invalid = [
            name
            for name in names
            if name != "manifest.json" and not name.startswith("sections/") and not name.endswith("/")
        ]
        if invalid:
            raise SystemExit(f"artifact contains non-public entries: {', '.join(invalid)}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact", required=True, help="Path to sanitized profile-pack zip")
    parser.add_argument("--pack-id", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--title", default="")
    parser.add_argument("--description", default="")
    parser.add_argument("--maintainer", default="community")
    parser.add_argument("--source-channel", default="community_submission")
    parser.add_argument("--risk-level", default="low")
    parser.add_argument("--compatibility", default="compatible")
    parser.add_argument("--featured", action="store_true")
    parser.add_argument("--featured-note", default="")
    parser.add_argument("--review-note", default="")
    parser.add_argument("--review-label", action="append", default=[])
    parser.add_argument("--warning-flag", action="append", default=[])
    parser.add_argument("--compatibility-issue", action="append", default=[])
    parser.add_argument("--installs", type=int, default=0)
    parser.add_argument("--trials", type=int, default=0)
    parser.add_argument("--published-at", default="")
    parser.add_argument("--skip-rebuild-snapshot", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    artifact_path = Path(args.artifact).expanduser().resolve()
    if not artifact_path.exists():
        raise SystemExit(f"artifact not found: {artifact_path}")
    if artifact_path.suffix.lower() != ".zip":
        raise SystemExit("artifact must be a .zip profile-pack archive")

    manifest = _read_manifest(artifact_path)
    _validate_public_artifact(artifact_path, manifest)
    DOCS_MARKET_ENTRIES_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_MARKET_COMMUNITY_PACKAGES_DIR.mkdir(parents=True, exist_ok=True)

    package_filename = f"{_safe_slug(args.pack_id)}-{_safe_slug(args.version)}.zip"
    target_package = DOCS_MARKET_COMMUNITY_PACKAGES_DIR / package_filename
    shutil.copyfile(artifact_path, target_package)
    sha256, size_bytes = _package_metadata(target_package)

    entry = {
        "pack_id": str(args.pack_id).strip(),
        "template_id": str(args.pack_id).strip(),
        "title": str(args.title or args.pack_id).strip(),
        "description": str(args.description or "").strip(),
        "version": str(args.version).strip(),
        "pack_type": str(manifest.get("pack_type", "bot_profile_pack") or "bot_profile_pack").strip(),
        "artifact_id": f"public:community:{_safe_slug(args.pack_id)}-{_safe_slug(args.version)}",
        "import_id": f"public:community-import:{_safe_slug(args.pack_id)}-{_safe_slug(args.version)}",
        "source_submission_id": f"community:{_safe_slug(args.pack_id)}-{_safe_slug(args.version)}",
        "filename": target_package.name,
        "sha256": sha256,
        "size_bytes": size_bytes,
        "sections": list(manifest.get("sections", []) or []),
        "redaction_mode": str(
            (manifest.get("redaction_policy", {}) or {}).get("mode", "exclude_secrets") or "exclude_secrets"
        ).strip(),
        "capability_summary": {
            "declared": list(manifest.get("capabilities", []) or []),
            "derived": list(manifest.get("capabilities", []) or []),
            "high_risk_declared": [],
            "missing_declared": [],
            "high_risk_count": 0,
        },
        "compatibility_matrix": {
            "compatibility": str(args.compatibility).strip() or "compatible",
            "issues": [str(item).strip() for item in args.compatibility_issue if str(item).strip()],
        },
        "review_evidence": {
            "review_labels": [str(item).strip() for item in args.review_label if str(item).strip()],
            "warning_flags": [str(item).strip() for item in args.warning_flag if str(item).strip()],
            "risk_level": str(args.risk_level).strip() or "low",
            "redaction_mode": str(
                (manifest.get("redaction_policy", {}) or {}).get("mode", "exclude_secrets") or "exclude_secrets"
            ).strip(),
        },
        "featured": bool(args.featured),
        "featured_note": str(args.featured_note or "").strip(),
        "featured_by": "admin:public-market",
        "featured_at": str(args.published_at or "").strip() if args.featured else "",
        "review_note": str(args.review_note or "").strip(),
        "review_labels": [str(item).strip() for item in args.review_label if str(item).strip()],
        "warning_flags": [str(item).strip() for item in args.warning_flag if str(item).strip()],
        "risk_level": str(args.risk_level).strip() or "low",
        "scan_summary": {
            "risk_level": str(args.risk_level).strip() or "low",
            "review_labels": [str(item).strip() for item in args.review_label if str(item).strip()],
            "warning_flags": [str(item).strip() for item in args.warning_flag if str(item).strip()],
        },
        "compatibility": str(args.compatibility).strip() or "compatible",
        "compatibility_issues": [str(item).strip() for item in args.compatibility_issue if str(item).strip()],
        "source_channel": str(args.source_channel).strip() or "community_submission",
        "maintainer": str(args.maintainer).strip() or "community",
        "published_at": str(args.published_at or "").strip(),
        "engagement": {
            "installs": max(0, int(args.installs)),
            "trial_requests": max(0, int(args.trials)),
        },
        "package_path": f"/market/packages/community/{target_package.name}",
        "catalog_origin": "public",
        "runtime_available": False,
    }

    entry_path = DOCS_MARKET_ENTRIES_DIR / f"{_safe_slug(args.pack_id)}-{_safe_slug(args.version)}.json"
    entry_path.write_text(json.dumps(entry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if not args.skip_rebuild_snapshot:
        build_market_snapshot()
    print(entry_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
