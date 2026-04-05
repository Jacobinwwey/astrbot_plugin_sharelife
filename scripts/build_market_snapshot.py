#!/usr/bin/env python3
"""Generate sanitized public market artifacts and snapshot metadata."""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
import zipfile

REPO_ROOT = Path(__file__).resolve().parents[1]

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sharelife.official_profile_pack_examples import official_profile_pack_examples


DOCS_PUBLIC_DIR = REPO_ROOT / "docs" / "public"
DOCS_MARKET_DIR = DOCS_PUBLIC_DIR / "market"
DOCS_MARKET_PACKAGES_DIR = DOCS_MARKET_DIR / "packages"
DOCS_MARKET_OFFICIAL_PACKAGES_DIR = DOCS_MARKET_PACKAGES_DIR / "official"
DOCS_MARKET_COMMUNITY_PACKAGES_DIR = DOCS_MARKET_PACKAGES_DIR / "community"
DOCS_MARKET_ENTRIES_DIR = DOCS_MARKET_DIR / "entries"
DOCS_MARKET_SNAPSHOT = DOCS_MARKET_DIR / "catalog.snapshot.json"


def _json_dump(payload: Any, *, pretty: bool = True) -> str:
    if pretty:
        return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _write_if_changed(path: Path, content: str) -> bool:
    current = path.read_text(encoding="utf-8") if path.exists() else None
    if current == content:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def _safe_slug(value: str) -> str:
    slug = "".join(char if char.isalnum() else "-" for char in str(value or "").strip().lower())
    slug = "-".join(part for part in slug.split("-") if part)
    return slug or "profile-pack"


def _hash_json(payload: Any) -> str:
    encoded = _json_dump(payload, pretty=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _package_hash_key(section_name: str) -> str:
    return f"sections/{section_name}.json"


def _infer_capabilities(sections: dict[str, Any], pack_type: str) -> list[str]:
    inferred: set[str] = set()
    if pack_type in {"bot_profile_pack", "extension_pack"}:
        inferred.update({"file.read", "file.write"})
    if "providers" in sections:
        inferred.add("provider.access")
    if "mcp_servers" in sections:
        inferred.add("mcp.invoke")
    if "memory_store" in sections:
        inferred.add("memory.export")
    if "conversation_history" in sections:
        inferred.add("conversation.export")
    if "knowledge_base" in sections:
        inferred.add("knowledge.export")
    if "environment_manifest" in sections:
        inferred.add("environment.reconfigure")
    return sorted(inferred)


def _official_title(pack_id: str) -> str:
    if pack_id == "profile/official-starter":
        return "Official Starter"
    if pack_id == "profile/official-safe-reference":
        return "Official Safe Reference"
    return pack_id


def _official_description(pack_id: str) -> str:
    if pack_id == "profile/official-starter":
        return "Starter baseline profile-pack for first import, compare, and apply walkthrough."
    if pack_id == "profile/official-safe-reference":
        return "Safety-first reference profile-pack for strict apply, rollback, and audit review."
    return "Official Sharelife profile-pack."


def _official_engagement(pack_id: str) -> dict[str, int]:
    if pack_id == "profile/official-starter":
        return {"installs": 248, "trial_requests": 61}
    if pack_id == "profile/official-safe-reference":
        return {"installs": 179, "trial_requests": 47}
    return {"installs": 0, "trial_requests": 0}


def _build_manifest(
    *,
    pack_id: str,
    version: str,
    pack_type: str,
    sections: dict[str, Any],
    created_at: str,
) -> dict[str, Any]:
    return {
        "pack_type": pack_type,
        "pack_id": pack_id,
        "version": version,
        "created_at": created_at,
        "astrbot_version": "any",
        "plugin_compat": "any",
        "sections": list(sections.keys()),
        "capabilities": _infer_capabilities(sections=sections, pack_type=pack_type),
        "redaction_policy": {
            "mode": "exclude_secrets",
            "include_sections": list(sections.keys()),
            "mask_paths": [],
            "drop_paths": [],
        },
        "hashes": {
            _package_hash_key(section_name): _hash_json(section_payload)
            for section_name, section_payload in sections.items()
        },
    }


def _write_profile_pack_archive(
    *,
    package_dir: Path,
    package_name: str,
    manifest: dict[str, Any],
    sections: dict[str, Any],
) -> tuple[bool, Path]:
    package_dir.mkdir(parents=True, exist_ok=True)
    path = package_dir / package_name
    serialized = {
        "manifest.json": _json_dump(manifest),
    }
    for section_name, section_payload in sections.items():
        serialized[_package_hash_key(section_name)] = _json_dump(section_payload)

    previous: dict[str, str] = {}
    if path.exists():
        with zipfile.ZipFile(path, "r") as archive:
            previous = {
                name: archive.read(name).decode("utf-8")
                for name in archive.namelist()
            }
    if previous == serialized:
        return False, path

    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, content in serialized.items():
            archive.writestr(name, content)
    return True, path


def _package_metadata(path: Path) -> tuple[str, int]:
    return hashlib.sha256(path.read_bytes()).hexdigest(), path.stat().st_size


def _official_examples() -> list[dict[str, Any]]:
    return official_profile_pack_examples()


def _official_row(example: dict[str, Any], *, generated_at: str) -> tuple[bool, dict[str, Any]]:
    pack_id = str(example.get("pack_id", "") or "").strip()
    version = str(example.get("version", "") or "").strip()
    pack_type = str(example.get("pack_type", "bot_profile_pack") or "bot_profile_pack").strip()
    sections = dict(example.get("sections", {}) or {})
    if not pack_id or not version or not sections:
        raise ValueError("invalid official market example")

    created_at = str(example.get("created_at", "") or "").strip() or generated_at
    published_at = str(example.get("published_at", "") or "").strip() or created_at
    manifest = _build_manifest(
        pack_id=pack_id,
        version=version,
        pack_type=pack_type,
        sections=sections,
        created_at=created_at,
    )
    package_name = f"{_safe_slug(pack_id)}-{_safe_slug(version)}.zip"
    changed, package_path = _write_profile_pack_archive(
        package_dir=DOCS_MARKET_OFFICIAL_PACKAGES_DIR,
        package_name=package_name,
        manifest=manifest,
        sections=sections,
    )
    sha256, size_bytes = _package_metadata(package_path)
    review_labels = ["approved", "official_profile_pack", "risk_low"]
    row = {
        "pack_id": pack_id,
        "template_id": pack_id,
        "title": _official_title(pack_id),
        "description": _official_description(pack_id),
        "version": version,
        "pack_type": pack_type,
        "artifact_id": f"public:official:{_safe_slug(pack_id)}-{_safe_slug(version)}",
        "import_id": f"public:official-import:{_safe_slug(pack_id)}-{_safe_slug(version)}",
        "source_submission_id": f"official:{_safe_slug(pack_id)}-{_safe_slug(version)}",
        "filename": package_path.name,
        "sha256": sha256,
        "size_bytes": size_bytes,
        "sections": list(manifest.get("sections", [])),
        "redaction_mode": "exclude_secrets",
        "capability_summary": {
            "declared": list(manifest.get("capabilities", [])),
            "derived": list(manifest.get("capabilities", [])),
            "high_risk_declared": [],
            "missing_declared": [],
            "high_risk_count": 0,
        },
        "compatibility_matrix": {
            "compatibility": "compatible",
            "issues": [],
        },
        "review_evidence": {
            "review_labels": list(review_labels),
            "warning_flags": [],
            "risk_level": "low",
            "redaction_mode": "exclude_secrets",
        },
        "featured": bool(example.get("featured", True)),
        "featured_note": str(example.get("featured_note", "") or "").strip(),
        "featured_by": "official:sharelife",
        "featured_at": published_at,
        "review_note": str(example.get("review_note", "") or "").strip(),
        "review_labels": review_labels,
        "warning_flags": [],
        "risk_level": "low",
        "scan_summary": {
            "risk_level": "low",
            "review_labels": list(review_labels),
            "warning_flags": [],
        },
        "compatibility": "compatible",
        "compatibility_issues": [],
        "source_channel": "bundled_official",
        "maintainer": "Sharelife",
        "published_at": published_at,
        "engagement": _official_engagement(pack_id),
        "package_path": f"/market/packages/official/{package_path.name}",
        "catalog_origin": "public",
        "runtime_available": False,
    }
    return changed, row


def _normalized_public_row(entry: dict[str, Any]) -> dict[str, Any]:
    pack_id = str(entry.get("pack_id", entry.get("template_id", "")) or "").strip()
    version = str(entry.get("version", "") or "").strip()
    package_path = str(entry.get("package_path", "") or "").strip()
    if not pack_id or not version or not package_path:
        raise ValueError("public market entry requires pack_id, version, and package_path")

    resolved_package = DOCS_PUBLIC_DIR / package_path.lstrip("/")
    if not resolved_package.exists():
        raise ValueError(f"missing public package for entry: {package_path}")
    sha256, size_bytes = _package_metadata(resolved_package)
    engagement = entry.get("engagement") if isinstance(entry.get("engagement"), dict) else {}
    sections = entry.get("sections") if isinstance(entry.get("sections"), list) else []
    review_labels = entry.get("review_labels") if isinstance(entry.get("review_labels"), list) else []
    warning_flags = entry.get("warning_flags") if isinstance(entry.get("warning_flags"), list) else []
    compatibility_issues = (
        entry.get("compatibility_issues")
        if isinstance(entry.get("compatibility_issues"), list)
        else []
    )
    normalized = dict(entry)
    normalized.update(
        {
            "pack_id": pack_id,
            "template_id": pack_id,
            "version": version,
            "filename": resolved_package.name,
            "sha256": sha256,
            "size_bytes": size_bytes,
            "package_path": package_path,
            "engagement": {
                "installs": int(engagement.get("installs", 0) or 0),
                "trial_requests": int(engagement.get("trial_requests", 0) or 0),
            },
            "sections": [str(item or "").strip() for item in sections if str(item or "").strip()],
            "review_labels": [str(item or "").strip() for item in review_labels if str(item or "").strip()],
            "warning_flags": [str(item or "").strip() for item in warning_flags if str(item or "").strip()],
            "compatibility_issues": [
                str(item or "").strip()
                for item in compatibility_issues
                if str(item or "").strip()
            ],
            "catalog_origin": "public",
            "runtime_available": False,
        }
    )
    return normalized


def _load_entry_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not DOCS_MARKET_ENTRIES_DIR.exists():
        return rows
    for path in sorted(DOCS_MARKET_ENTRIES_DIR.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            rows.append(_normalized_public_row(payload))
    return rows


def _cleanup_official_packages(expected_filenames: set[str]) -> bool:
    changed = False
    DOCS_MARKET_OFFICIAL_PACKAGES_DIR.mkdir(parents=True, exist_ok=True)
    for path in DOCS_MARKET_OFFICIAL_PACKAGES_DIR.glob("*.zip"):
        if path.name in expected_filenames:
            continue
        path.unlink()
        changed = True
    return changed


def build() -> bool:
    DOCS_MARKET_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_MARKET_ENTRIES_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_MARKET_COMMUNITY_PACKAGES_DIR.mkdir(parents=True, exist_ok=True)

    changed = False
    generated_at = datetime.now(UTC).isoformat()
    official_rows: list[dict[str, Any]] = []
    official_filenames: set[str] = set()
    for example in _official_examples():
        row_changed, row = _official_row(example, generated_at=generated_at)
        official_rows.append(row)
        official_filenames.add(Path(str(row["package_path"]).strip()).name)
        changed = row_changed or changed
    changed = _cleanup_official_packages(official_filenames) or changed

    merged_by_key: dict[tuple[str, str], dict[str, Any]] = {}
    for row in official_rows:
        merged_by_key[(str(row["pack_id"]), str(row["version"]))] = row
    for row in _load_entry_rows():
        merged_by_key[(str(row["pack_id"]), str(row["version"]))] = row

    rows = list(merged_by_key.values())
    rows.sort(
        key=lambda item: (
            0 if bool(item.get("featured")) else 1,
            -int(item.get("engagement", {}).get("installs", 0) or 0),
            str(item.get("pack_id") or ""),
            str(item.get("version") or ""),
        ),
    )

    if DOCS_MARKET_SNAPSHOT.exists():
        try:
            previous = json.loads(DOCS_MARKET_SNAPSHOT.read_text(encoding="utf-8"))
        except Exception:
            previous = {}
        if isinstance(previous, dict) and previous.get("rows") == rows:
            previous_generated_at = str(previous.get("generated_at", "") or "").strip()
            if previous_generated_at:
                generated_at = previous_generated_at

    snapshot = {
        "schema_version": "v1",
        "generated_at": generated_at,
        "rows": rows,
    }
    changed = _write_if_changed(DOCS_MARKET_SNAPSHOT, _json_dump(snapshot)) or changed
    return changed


if __name__ == "__main__":
    build()
