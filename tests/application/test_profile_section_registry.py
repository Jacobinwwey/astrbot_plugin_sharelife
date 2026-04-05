from __future__ import annotations

import pytest

from sharelife.application.services_profile_redaction import REDACTED_VALUE, ProfileRedactionService
from sharelife.application.services_profile_section_registry import ProfileSectionAdapterRegistry


def test_section_registry_captures_selected_whitelisted_sections():
    registry = ProfileSectionAdapterRegistry.default_registry()
    snapshot = {
        "astrbot_core": {"name": "demo-bot", "timezone": "UTC"},
        "providers": {"openai": {"api_key": "sk-demo", "model": "gpt-5"}},
        "plugins": {"sharelife": {"enabled": True}},
    }

    captured = registry.capture(snapshot=snapshot, selected_sections=["astrbot_core", "providers"])

    assert captured["astrbot_core"]["name"] == "demo-bot"
    assert captured["providers"]["openai"]["model"] == "gpt-5"


def test_section_registry_rejects_unknown_sections():
    registry = ProfileSectionAdapterRegistry.default_registry()

    with pytest.raises(ValueError):
        registry.capture(snapshot={}, selected_sections=["unknown_section"])


def test_section_registry_supports_stateful_migration_sections():
    registry = ProfileSectionAdapterRegistry.default_registry()
    snapshot = {
        "memory_store": {"thread": {"summary": "stable context"}},
        "conversation_history": [{"role": "user", "content": "hi"}],
        "knowledge_base": {"default": {"collection": "docs"}},
        "environment_manifest": {"container_runtime": "docker"},
    }
    captured = registry.capture(
        snapshot=snapshot,
        selected_sections=[
            "memory_store",
            "conversation_history",
            "knowledge_base",
            "environment_manifest",
        ],
    )
    assert captured["memory_store"]["thread"]["summary"] == "stable context"
    assert captured["conversation_history"][0]["role"] == "user"
    assert captured["knowledge_base"]["default"]["collection"] == "docs"
    assert captured["environment_manifest"]["container_runtime"] == "docker"


def test_profile_redaction_masks_sensitive_keys_recursively():
    service = ProfileRedactionService()
    payload = {
        "api_key": "sk-live-secret",
        "nested": {
            "token": "demo-token",
            "normal_key": "safe",
        },
    }

    result = service.redact_section(
        section_name="providers",
        payload=payload,
        mode="exclude_secrets",
    )

    assert result.payload["api_key"] == REDACTED_VALUE
    assert result.payload["nested"]["token"] == REDACTED_VALUE
    assert result.payload["nested"]["normal_key"] == "safe"
    assert "providers.api_key" in result.redacted_paths


def test_profile_redaction_can_drop_provider_section():
    service = ProfileRedactionService()
    payload = {"openai": {"api_key": "sk-live-secret", "model": "gpt-5"}}

    result = service.redact_section(
        section_name="providers",
        payload=payload,
        mode="exclude_provider",
    )

    assert result.dropped is True
    assert result.payload == {}


def test_profile_redaction_supports_field_level_mask_and_drop_paths():
    service = ProfileRedactionService()
    payload = {
        "openai": {
            "model": "gpt-5",
            "organization": "org-123",
            "endpoint": "https://api.openai.com/v1",
        }
    }
    result = service.redact_section(
        section_name="providers",
        payload=payload,
        mode="include_provider_no_key",
        mask_paths=["providers.openai.organization"],
        drop_paths=["providers.openai.endpoint"],
    )

    assert result.payload["openai"]["organization"] == REDACTED_VALUE
    assert "endpoint" not in result.payload["openai"]
    assert "providers.openai.organization" in result.redacted_paths
    assert "providers.openai.endpoint:dropped" in result.redacted_paths
