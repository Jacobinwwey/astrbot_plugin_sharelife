from __future__ import annotations

import pytest
from pydantic import ValidationError

from sharelife.domain.profile_pack_models import BotProfilePackManifest, RedactionPolicy


def test_redaction_policy_defaults_to_exclude_secrets():
    policy = RedactionPolicy.model_validate({})

    assert policy.mode == "exclude_secrets"
    assert policy.include_sections == []
    assert policy.mask_paths == []
    assert policy.drop_paths == []


def test_redaction_policy_rejects_unknown_mode():
    with pytest.raises(ValidationError):
        RedactionPolicy.model_validate({"mode": "include_plaintext_secrets"})


def test_manifest_requires_hash_for_each_section():
    with pytest.raises(ValidationError):
        BotProfilePackManifest.model_validate(
            {
                "pack_type": "bot_profile_pack",
                "pack_id": "profile/basic",
                "version": "1.0.0",
                "created_at": "2026-03-30T00:00:00+00:00",
                "astrbot_version": "4.16.0",
                "plugin_compat": ">=0.1.0",
                "sections": ["astrbot_core", "providers"],
                "redaction_policy": {"mode": "exclude_secrets"},
                "hashes": {
                    "sections/astrbot_core.json": "hash-only-one-section",
                },
            }
        )


def test_manifest_accepts_valid_profile_pack_payload():
    manifest = BotProfilePackManifest.model_validate(
        {
            "pack_type": "bot_profile_pack",
            "pack_id": "profile/basic",
            "version": "1.0.0",
            "created_at": "2026-03-30T00:00:00+00:00",
            "astrbot_version": "4.16.0",
            "plugin_compat": ">=0.1.0",
            "sections": ["astrbot_core", "providers"],
            "redaction_policy": {"mode": "exclude_secrets"},
            "hashes": {
                "sections/astrbot_core.json": "hash-astrbot",
                "sections/providers.json": "hash-providers",
            },
        }
    )

    assert manifest.pack_type == "bot_profile_pack"
    assert manifest.sections == ["astrbot_core", "providers"]


def test_redaction_policy_accepts_mask_and_drop_paths():
    policy = RedactionPolicy.model_validate(
        {
            "mode": "exclude_secrets",
            "mask_paths": [
                "providers.openai.organization",
                "providers.openai.organization",
            ],
            "drop_paths": [
                "sharelife_meta.notes",
            ],
        }
    )

    assert policy.mask_paths == ["providers.openai.organization"]
    assert policy.drop_paths == ["sharelife_meta.notes"]


def test_redaction_policy_accepts_include_encrypted_secrets_mode():
    policy = RedactionPolicy.model_validate({"mode": "include_encrypted_secrets"})
    assert policy.mode == "include_encrypted_secrets"


def test_manifest_accepts_optional_signature_payload():
    manifest = BotProfilePackManifest.model_validate(
        {
            "pack_type": "bot_profile_pack",
            "pack_id": "profile/signed-basic",
            "version": "1.0.0",
            "created_at": "2026-03-30T00:00:00+00:00",
            "astrbot_version": "4.16.0",
            "plugin_compat": ">=0.1.0",
            "sections": ["astrbot_core"],
            "redaction_policy": {"mode": "exclude_secrets"},
            "hashes": {
                "sections/astrbot_core.json": "hash-astrbot",
            },
            "signature": {
                "algorithm": "hmac-sha256",
                "key_id": "team-default",
                "value": "abc123",
            },
        }
    )
    assert manifest.signature is not None
    assert manifest.signature.key_id == "team-default"


def test_manifest_accepts_extension_pack_payload():
    manifest = BotProfilePackManifest.model_validate(
        {
            "pack_type": "extension_pack",
            "pack_id": "extension/community-basic",
            "version": "1.0.0",
            "created_at": "2026-03-30T00:00:00+00:00",
            "astrbot_version": "4.16.0",
            "plugin_compat": ">=0.1.0",
            "sections": ["plugins", "skills", "personas", "mcp_servers"],
            "redaction_policy": {"mode": "exclude_secrets"},
            "hashes": {
                "sections/plugins.json": "hash-plugins",
                "sections/skills.json": "hash-skills",
                "sections/personas.json": "hash-personas",
                "sections/mcp_servers.json": "hash-mcp",
            },
        }
    )
    assert manifest.pack_type == "extension_pack"


def test_manifest_rejects_extension_pack_with_disallowed_sections():
    with pytest.raises(ValidationError):
        BotProfilePackManifest.model_validate(
            {
                "pack_type": "extension_pack",
                "pack_id": "extension/community-invalid",
                "version": "1.0.0",
                "created_at": "2026-03-30T00:00:00+00:00",
                "astrbot_version": "4.16.0",
                "plugin_compat": ">=0.1.0",
                "sections": ["providers", "plugins"],
                "redaction_policy": {"mode": "exclude_secrets"},
                "hashes": {
                    "sections/providers.json": "hash-providers",
                    "sections/plugins.json": "hash-plugins",
                },
            }
        )


def test_manifest_accepts_stateful_sections_for_bot_profile_pack():
    manifest = BotProfilePackManifest.model_validate(
        {
            "pack_type": "bot_profile_pack",
            "pack_id": "profile/stateful-pack",
            "version": "1.0.0",
            "created_at": "2026-04-02T00:00:00+00:00",
            "astrbot_version": "4.16.0",
            "plugin_compat": ">=0.1.0",
            "sections": [
                "memory_store",
                "conversation_history",
                "knowledge_base",
                "environment_manifest",
            ],
            "capabilities": [
                "memory.export",
                "conversation.export",
                "knowledge.export",
                "environment.reconfigure",
            ],
            "redaction_policy": {"mode": "exclude_secrets"},
            "hashes": {
                "sections/memory_store.json": "hash-memory",
                "sections/conversation_history.json": "hash-conversation",
                "sections/knowledge_base.json": "hash-kb",
                "sections/environment_manifest.json": "hash-env",
            },
        }
    )

    assert manifest.sections == [
        "memory_store",
        "conversation_history",
        "knowledge_base",
        "environment_manifest",
    ]
    assert "environment.reconfigure" in manifest.capabilities


def test_manifest_rejects_stateful_sections_for_extension_pack():
    with pytest.raises(ValidationError):
        BotProfilePackManifest.model_validate(
            {
                "pack_type": "extension_pack",
                "pack_id": "extension/invalid-stateful",
                "version": "1.0.0",
                "created_at": "2026-04-02T00:00:00+00:00",
                "astrbot_version": "4.16.0",
                "plugin_compat": ">=0.1.0",
                "sections": ["plugins", "memory_store"],
                "redaction_policy": {"mode": "exclude_secrets"},
                "hashes": {
                    "sections/plugins.json": "hash-plugins",
                    "sections/memory_store.json": "hash-memory",
                },
            }
        )
