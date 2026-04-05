"""Redaction service for bot_profile_pack exports."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import re
from typing import Any, Callable

from ..domain.profile_pack_models import PROFILE_REDACTION_MODES


REDACTED_VALUE = "***REDACTED***"
_KEY_SPLIT_RE = re.compile(r"[^a-z0-9]+")


@dataclass(slots=True)
class RedactionResult:
    section_name: str
    payload: Any
    redacted_paths: list[str]
    dropped: bool = False


class ProfileRedactionService:
    def redact_section(
        self,
        section_name: str,
        payload: Any,
        mode: str,
        *,
        mask_paths: list[str] | None = None,
        drop_paths: list[str] | None = None,
        secret_transformer: Callable[[Any, str], Any] | None = None,
    ) -> RedactionResult:
        normalized_mode = str(mode or "").strip() or "exclude_secrets"
        if normalized_mode not in PROFILE_REDACTION_MODES:
            raise ValueError("PROFILE_REDACTION_MODE_UNSUPPORTED")

        if normalized_mode == "exclude_provider" and section_name == "providers":
            return RedactionResult(
                section_name=section_name,
                payload={},
                redacted_paths=[section_name],
                dropped=True,
            )

        redacted_paths: list[str] = []
        mask_set = self._normalize_override_paths(mask_paths or [], section_name=section_name)
        drop_set = self._normalize_override_paths(drop_paths or [], section_name=section_name)
        redacted_payload = self._redact_recursive(
            value=deepcopy(payload),
            path=section_name,
            redacted_paths=redacted_paths,
                mode=normalized_mode,
                mask_paths=mask_set,
                drop_paths=drop_set,
                secret_transformer=secret_transformer,
            )
        return RedactionResult(
            section_name=section_name,
            payload=redacted_payload,
            redacted_paths=redacted_paths,
            dropped=False,
        )

    def _redact_recursive(
        self,
        value: Any,
        path: str,
        redacted_paths: list[str],
        mode: str,
        mask_paths: set[str],
        drop_paths: set[str],
        secret_transformer: Callable[[Any, str], Any] | None,
    ) -> Any:
        if isinstance(value, dict):
            out: dict[str, Any] = {}
            for key, item in value.items():
                child_path = f"{path}.{key}" if path else str(key)
                if child_path in drop_paths:
                    redacted_paths.append(f"{child_path}:dropped")
                    continue
                if child_path in mask_paths:
                    out[key] = REDACTED_VALUE
                    redacted_paths.append(child_path)
                    continue
                if self._is_sensitive_key(key):
                    if mode == "include_encrypted_secrets" and secret_transformer is not None:
                        out[key] = secret_transformer(item, child_path)
                    else:
                        out[key] = REDACTED_VALUE
                    redacted_paths.append(child_path)
                    continue
                out[key] = self._redact_recursive(
                    item,
                    child_path,
                    redacted_paths,
                    mode,
                    mask_paths,
                    drop_paths,
                    secret_transformer,
                )
            return out

        if isinstance(value, list):
            out_list: list[Any] = []
            for index, item in enumerate(value):
                child_path = f"{path}[{index}]"
                out_list.append(
                    self._redact_recursive(
                        item,
                        child_path,
                        redacted_paths,
                        mode,
                        mask_paths,
                        drop_paths,
                        secret_transformer,
                    )
                )
            return out_list

        return value

    @staticmethod
    def _normalize_override_paths(paths: list[str], *, section_name: str) -> set[str]:
        out: set[str] = set()
        for path in paths:
            text = str(path or "").strip()
            if not text:
                continue
            if text == section_name or text.startswith(f"{section_name}."):
                out.add(text)
        return out

    @staticmethod
    def _is_sensitive_key(key: Any) -> bool:
        text = str(key or "").strip().lower()
        if not text:
            return False

        direct = {
            "api_key",
            "access_key",
            "secret_key",
            "private_key",
            "token",
            "secret",
            "password",
            "passphrase",
            "credential",
            "credentials",
        }
        if text in direct:
            return True
        if text.endswith("_token") or text.endswith("_secret") or text.endswith("_password"):
            return True
        if text.startswith("token_") or text.startswith("secret_") or text.startswith("password_"):
            return True
        parts = [part for part in _KEY_SPLIT_RE.split(text) if part]
        has_security_word = bool(set(parts) & {"token", "secret", "password", "credential", "credentials"})
        if has_security_word:
            return True
        return bool(
            {"api", "access", "secret", "private"} & set(parts)
            and "key" in parts
        )
