from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
WEBUI_ROOT = REPO_ROOT / "sharelife" / "webui"


def test_role_pages_load_binding_slices_before_app_runtime() -> None:
    pages = ("index.html", "member.html", "admin.html", "reviewer.html")
    for page in pages:
        text = (WEBUI_ROOT / page).read_text(encoding="utf-8")
        assert 'src="/app_binding_slices.js"' in text
        assert 'src="/app.js"' in text
        assert text.index('src="/app_binding_slices.js"') < text.index('src="/app.js"')


def test_binding_slices_registry_exposes_expected_slice_functions() -> None:
    text = (WEBUI_ROOT / "app_binding_slices.js").read_text(encoding="utf-8")
    assert "globalScope.SharelifeAppBindingSlices" in text
    assert "bindAdminOperationsControls" in text
    assert "bindMemberImportControls" in text
    assert "bindReviewerLifecycleControls" in text
    assert "bindSidebarNavigationControls" in text
    assert "bindAuthPanelControls" in text
    assert "bindLocaleAndDeveloperControls" in text
    assert "bindWorkspaceRouteControls" in text
    assert "bindPreferenceControls" in text
    assert "bindMemberMarketControls" in text
    assert "bindTemplateDrawerAndWizardControls" in text
    assert "bindTemplateExecutionControls" in text
    assert "bindProfilePackControls" in text
    assert "bindSubmissionReviewControls" in text
