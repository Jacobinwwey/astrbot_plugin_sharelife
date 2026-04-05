from pathlib import Path

from sharelife.infrastructure.runtime_bridge import InMemoryRuntimeBridge, JsonFileRuntimeBridge


def test_inmemory_runtime_bridge_applies_nested_patch_without_clobbering_peers():
    bridge = InMemoryRuntimeBridge(
        initial_state={
            "providers": {
                "openai": {
                    "base_url": "https://api.openai.com",
                    "organization": "org-a",
                },
                "anthropic": {"base_url": "https://api.anthropic.com"},
            }
        },
        merge_mode="deep_merge",
    )

    bridge.apply_patch(
        {
            "providers": {
                "openai": {"organization": "org-b"},
            }
        }
    )

    snapshot = bridge.snapshot()
    assert snapshot["providers"]["openai"]["base_url"] == "https://api.openai.com"
    assert snapshot["providers"]["openai"]["organization"] == "org-b"
    assert snapshot["providers"]["anthropic"]["base_url"] == "https://api.anthropic.com"


def test_json_file_runtime_bridge_persists_patch_and_restore(tmp_path: Path):
    state_file = tmp_path / "runtime_state.json"
    bridge = JsonFileRuntimeBridge(
        state_path=state_file,
        initial_state={"plugins": {"sharelife": {"enabled": True}}},
        merge_mode="deep_merge",
    )

    bridge.apply_patch({"plugins": {"sharelife": {"enabled": False, "mode": "strict"}}})
    loaded = JsonFileRuntimeBridge(state_path=state_file)
    snapshot = loaded.snapshot()
    assert snapshot["plugins"]["sharelife"]["enabled"] is False
    assert snapshot["plugins"]["sharelife"]["mode"] == "strict"

    loaded.restore_snapshot({"plugins": {"sharelife": {"enabled": True}}})
    reloaded = JsonFileRuntimeBridge(state_path=state_file)
    assert reloaded.snapshot()["plugins"]["sharelife"]["enabled"] is True
