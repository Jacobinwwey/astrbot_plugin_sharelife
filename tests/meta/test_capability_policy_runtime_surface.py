from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
WEBUI_ROOT = REPO_ROOT / "sharelife" / "webui"


def test_role_pages_load_capability_policy_runtime_before_app() -> None:
    for page_name in ("index.html", "member.html", "reviewer.html", "admin.html"):
        text = (WEBUI_ROOT / page_name).read_text(encoding="utf-8")
        policy_pos = text.find('src="/capability_policy_runtime.js"')
        app_pos = text.find('src="/app.js"')
        assert policy_pos >= 0, f"{page_name} missing capability_policy_runtime.js"
        assert app_pos >= 0, f"{page_name} missing app.js"
        assert policy_pos < app_pos, f"{page_name} loads app.js before capability_policy_runtime.js"


def test_app_runtime_reads_capability_policy_runtime_bundle() -> None:
    text = (WEBUI_ROOT / "app.js").read_text(encoding="utf-8")
    assert "SharelifeCapabilityPolicyRuntime" in text
    assert "anonymousMemberFallbackOperations" in text
