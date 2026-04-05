from sharelife.sdk import AstrAgentContract, PluginManifestV2


def test_sdk_contract_exports_are_available():
    assert isinstance(PluginManifestV2.__name__, str)
    assert isinstance(AstrAgentContract.__name__, str)
