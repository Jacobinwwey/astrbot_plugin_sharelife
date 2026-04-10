"""Shared option-contract normalization helpers.

These helpers provide a single backend normalization surface for member-facing
install/upload/submit option payloads.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

_UPLOAD_SCAN_MODES = {"strict", "balanced"}
_UPLOAD_VISIBILITY = {"community", "private"}
_INSTALL_SOURCE_PREFERENCES = {"auto", "uploaded_submission", "generated"}
_PROFILE_PACK_TYPES = {"bot_profile_pack", "extension_pack"}
_PROFILE_PACK_REDACTION_MODES = {
    "exclude_secrets",
    "exclude_provider",
    "include_provider_no_key",
    "include_encrypted_secrets",
}


def as_bool(value: object, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
    return default


def normalize_string_list(value: object, *, max_items: int = 256) -> list[str]:
    raw_items: list[object]
    if isinstance(value, str):
        raw_items = [item for item in value.split(",")]
    elif isinstance(value, (list, tuple, set)):
        raw_items = list(value)
    else:
        raw_items = []
    out: list[str] = []
    seen: set[str] = set()
    for item in raw_items:
        normalized = str(item or "").strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        out.append(normalized)
        if len(out) >= max_items:
            break
    return out


def normalize_install_options(install_options: Mapping[str, Any] | None) -> dict[str, Any]:
    payload = install_options if isinstance(install_options, Mapping) else {}
    source_preference = str(payload.get("source_preference", "auto") or "auto").strip().lower()
    if source_preference not in _INSTALL_SOURCE_PREFERENCES:
        source_preference = "auto"
    return {
        "preflight": as_bool(payload.get("preflight"), default=False),
        "force_reinstall": as_bool(payload.get("force_reinstall"), default=False),
        "source_preference": source_preference,
        "selected_sections": normalize_string_list(payload.get("selected_sections")),
    }


def normalize_upload_options(
    upload_options: Mapping[str, Any] | None,
    *,
    normalize_idempotency_key: Callable[[object], str] | None = None,
) -> dict[str, Any]:
    payload = upload_options if isinstance(upload_options, Mapping) else {}
    scan_mode = str(payload.get("scan_mode", "balanced") or "balanced").strip().lower()
    if scan_mode not in _UPLOAD_SCAN_MODES:
        scan_mode = "balanced"
    visibility = str(payload.get("visibility", "community") or "community").strip().lower()
    if visibility not in _UPLOAD_VISIBILITY:
        visibility = "community"
    normalized = {
        "scan_mode": scan_mode,
        "visibility": visibility,
        "replace_existing": as_bool(payload.get("replace_existing"), default=False),
    }
    if normalize_idempotency_key is not None:
        idempotency_key = normalize_idempotency_key(payload.get("idempotency_key"))
        if idempotency_key:
            normalized["idempotency_key"] = idempotency_key
    return normalized


def normalize_profile_pack_submit_options(
    submit_options: Mapping[str, Any] | None,
    *,
    normalize_idempotency_key: Callable[[object], str] | None = None,
) -> dict[str, Any]:
    payload = submit_options if isinstance(submit_options, Mapping) else {}
    pack_type = str(payload.get("pack_type", "bot_profile_pack") or "bot_profile_pack").strip().lower()
    if pack_type not in _PROFILE_PACK_TYPES:
        pack_type = "bot_profile_pack"
    redaction_mode = str(payload.get("redaction_mode", "exclude_secrets") or "exclude_secrets").strip().lower()
    if redaction_mode not in _PROFILE_PACK_REDACTION_MODES:
        redaction_mode = "exclude_secrets"
    normalized = {
        "pack_type": pack_type,
        "selected_sections": normalize_string_list(payload.get("selected_sections")),
        "selected_item_paths": normalize_string_list(payload.get("selected_item_paths")),
        "redaction_mode": redaction_mode,
        "replace_existing": as_bool(payload.get("replace_existing"), default=False),
    }
    if normalize_idempotency_key is not None:
        idempotency_key = normalize_idempotency_key(payload.get("idempotency_key"))
        if idempotency_key:
            normalized["idempotency_key"] = idempotency_key
    return normalized
