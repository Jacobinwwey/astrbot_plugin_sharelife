from __future__ import annotations

from sharelife.domain.option_contracts import (
    normalize_install_options,
    normalize_profile_pack_submit_options,
    normalize_upload_options,
)


def test_option_contract_install_normalization_preserves_selected_sections():
    normalized = normalize_install_options(
        {
            "preflight": "true",
            "force_reinstall": 1,
            "source_preference": "GENERATED",
            "selected_sections": "memory_store,conversation_history,memory_store",
        },
    )
    assert normalized == {
        "preflight": True,
        "force_reinstall": True,
        "source_preference": "generated",
        "selected_sections": ["memory_store", "conversation_history"],
    }


def test_option_contract_upload_normalization_with_idempotency_callback():
    normalized = normalize_upload_options(
        {
            "scan_mode": "UNKNOWN",
            "visibility": "PRIVATE",
            "replace_existing": "yes",
            "idempotency_key": "  key-1  ",
        },
        normalize_idempotency_key=lambda value: str(value or "").strip(),
    )
    assert normalized == {
        "scan_mode": "balanced",
        "visibility": "private",
        "replace_existing": True,
        "idempotency_key": "key-1",
    }


def test_option_contract_profile_pack_submit_deduplicates_and_normalizes():
    normalized = normalize_profile_pack_submit_options(
        {
            "pack_type": "Extension_Pack",
            "selected_sections": ["plugins", "plugins", "providers"],
            "selected_item_paths": "plugins.enabled,plugins.enabled,providers.openai.model",
            "redaction_mode": "INVALID",
            "replace_existing": "1",
            "idempotency_key": "submit-k1",
        },
        normalize_idempotency_key=lambda value: str(value or "").strip(),
    )
    assert normalized == {
        "pack_type": "extension_pack",
        "selected_sections": ["plugins", "providers"],
        "selected_item_paths": ["plugins.enabled", "providers.openai.model"],
        "redaction_mode": "exclude_secrets",
        "replace_existing": True,
        "idempotency_key": "submit-k1",
    }
