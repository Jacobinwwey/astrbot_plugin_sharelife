from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_market_pages_load_shared_capability_runtime_helpers_before_market_page() -> None:
    for page_name in ("market.html", "market_detail.html"):
        text = (REPO_ROOT / "sharelife" / "webui" / page_name).read_text(encoding="utf-8")
        runtime_pos = text.find('/capability_guard_runtime.js')
        dom_runtime_pos = text.find('/capability_guard_dom_runtime.js')
        market_page_pos = text.find('/market_page.js')
        assert runtime_pos >= 0, f"{page_name} missing capability_guard_runtime.js"
        assert dom_runtime_pos >= 0, f"{page_name} missing capability_guard_dom_runtime.js"
        assert market_page_pos >= 0, f"{page_name} missing market_page.js"
        assert runtime_pos < market_page_pos, f"{page_name} loads market_page.js before capability runtime"
        assert dom_runtime_pos < market_page_pos, f"{page_name} loads market_page.js before capability DOM runtime"


def test_market_page_uses_shared_capability_helper_paths() -> None:
    text = (REPO_ROOT / "sharelife" / "webui" / "market_page.js").read_text(encoding="utf-8")
    assert "function capabilityGuardHelpers()" in text
    assert "SharelifeCapabilityGuardRuntime" in text
    assert "function capabilityGuardDomHelpers()" in text
    assert "SharelifeCapabilityGuardDomRuntime" in text
    assert "helper.fallbackCapabilityOperations" in text
    assert "helper.hasCapability" in text
