"""Domain models for Sharelife bot profile pack manifests."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

PROFILE_CAPABILITY_OPTIONS = (
    "network.outbound",
    "file.read",
    "file.write",
    "command.exec",
    "provider.access",
    "mcp.invoke",
    "memory.export",
    "conversation.export",
    "knowledge.export",
    "environment.reconfigure",
)


PROFILE_PACK_TYPE = "bot_profile_pack"
EXTENSION_PACK_TYPE = "extension_pack"
PROFILE_PACK_TYPES = (
    PROFILE_PACK_TYPE,
    EXTENSION_PACK_TYPE,
)
PROFILE_ALLOWED_SECTIONS = (
    "astrbot_core",
    "providers",
    "plugins",
    "skills",
    "personas",
    "mcp_servers",
    "sharelife_meta",
    "memory_store",
    "conversation_history",
    "knowledge_base",
    "environment_manifest",
)
EXTENSION_ALLOWED_SECTIONS = (
    "plugins",
    "skills",
    "personas",
    "mcp_servers",
)
PROFILE_REDACTION_MODES = (
    "exclude_secrets",
    "exclude_provider",
    "include_provider_no_key",
    "include_encrypted_secrets",
)


def profile_allowed_sections_for_pack(pack_type: str) -> tuple[str, ...]:
    normalized = str(pack_type or PROFILE_PACK_TYPE).strip()
    if normalized == EXTENSION_PACK_TYPE:
        return EXTENSION_ALLOWED_SECTIONS
    return PROFILE_ALLOWED_SECTIONS


class RedactionPolicy(BaseModel):
    mode: Literal[
        "exclude_secrets",
        "exclude_provider",
        "include_provider_no_key",
        "include_encrypted_secrets",
    ] = "exclude_secrets"
    include_sections: list[str] = Field(default_factory=list)
    mask_paths: list[str] = Field(default_factory=list)
    drop_paths: list[str] = Field(default_factory=list)

    @field_validator("include_sections")
    @classmethod
    def _normalize_sections(cls, value: list[str]) -> list[str]:
        out: list[str] = []
        seen: set[str] = set()
        for section in value:
            item = str(section or "").strip()
            if not item:
                continue
            if item not in PROFILE_ALLOWED_SECTIONS:
                raise ValueError(f"unsupported profile section: {item}")
            if item in seen:
                continue
            seen.add(item)
            out.append(item)
        return out

    @field_validator("mask_paths", "drop_paths")
    @classmethod
    def _normalize_paths(cls, value: list[str]) -> list[str]:
        out: list[str] = []
        seen: set[str] = set()
        for entry in value:
            item = str(entry or "").strip()
            if not item:
                continue
            if "." not in item:
                raise ValueError("field path must include section prefix")
            section = item.split(".", 1)[0]
            if section not in PROFILE_ALLOWED_SECTIONS:
                raise ValueError(f"unsupported profile section: {section}")
            if item in seen:
                continue
            seen.add(item)
            out.append(item)
        return out


class ManifestSignature(BaseModel):
    algorithm: Literal["hmac-sha256"] = "hmac-sha256"
    key_id: str
    value: str

    @field_validator("key_id", "value")
    @classmethod
    def _required_text(cls, value: str) -> str:
        text = str(value or "").strip()
        if not text:
            raise ValueError("signature fields are required")
        return text


class BotProfilePackManifest(BaseModel):
    pack_type: Literal["bot_profile_pack", "extension_pack"] = PROFILE_PACK_TYPE
    pack_id: str
    version: str
    created_at: str
    astrbot_version: str = ""
    plugin_compat: str = ""
    sections: list[str]
    capabilities: list[str] = Field(default_factory=list)
    redaction_policy: RedactionPolicy = Field(default_factory=RedactionPolicy)
    hashes: dict[str, str]
    signature: ManifestSignature | None = None

    @field_validator("pack_id")
    @classmethod
    def _pack_id_required(cls, value: str) -> str:
        text = str(value or "").strip()
        if not text:
            raise ValueError("pack_id is required")
        return text

    @field_validator("version")
    @classmethod
    def _version_required(cls, value: str) -> str:
        text = str(value or "").strip()
        if not text:
            raise ValueError("version is required")
        return text

    @field_validator("sections")
    @classmethod
    def _validate_sections(cls, value: list[str]) -> list[str]:
        out: list[str] = []
        seen: set[str] = set()
        for section in value:
            item = str(section or "").strip()
            if not item:
                continue
            if item not in PROFILE_ALLOWED_SECTIONS:
                raise ValueError(f"unsupported profile section: {item}")
            if item in seen:
                continue
            seen.add(item)
            out.append(item)
        if not out:
            raise ValueError("sections must not be empty")
        return out

    @field_validator("capabilities")
    @classmethod
    def _validate_capabilities(cls, value: list[str]) -> list[str]:
        out: list[str] = []
        seen: set[str] = set()
        for capability in value:
            item = str(capability or "").strip()
            if not item:
                continue
            if item not in PROFILE_CAPABILITY_OPTIONS:
                raise ValueError(f"unsupported capability: {item}")
            if item in seen:
                continue
            seen.add(item)
            out.append(item)
        return out

    @model_validator(mode="after")
    def _ensure_hashes_match_sections(self) -> "BotProfilePackManifest":
        allowed_sections = set(profile_allowed_sections_for_pack(self.pack_type))
        invalid_sections = [item for item in self.sections if item not in allowed_sections]
        if invalid_sections:
            raise ValueError(
                f"unsupported sections for pack_type {self.pack_type}: {sorted(invalid_sections)}"
            )

        expected_keys = {self.hash_key(section) for section in self.sections}
        present_keys = set(self.hashes.keys())
        if expected_keys != present_keys:
            missing = sorted(expected_keys - present_keys)
            extra = sorted(present_keys - expected_keys)
            detail = []
            if missing:
                detail.append(f"missing={missing}")
            if extra:
                detail.append(f"extra={extra}")
            raise ValueError(f"manifest hashes mismatch: {'; '.join(detail) or 'unexpected keys'}")
        return self

    @staticmethod
    def hash_key(section_name: str) -> str:
        return f"sections/{section_name}.json"
