from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_member_page_auth_role_select_is_member_only() -> None:
    text = (REPO_ROOT / "sharelife" / "webui" / "member.html").read_text(encoding="utf-8")

    auth_role_match = re.search(
        r'<select id="authRole">(?P<body>.*?)</select>',
        text,
        flags=re.DOTALL,
    )
    assert auth_role_match is not None
    auth_role_body = auth_role_match.group("body")
    assert 'value="member"' in auth_role_body
    assert 'value="reviewer"' not in auth_role_body
    assert 'value="admin"' not in auth_role_body


def test_member_page_actor_role_select_is_member_only() -> None:
    text = (REPO_ROOT / "sharelife" / "webui" / "member.html").read_text(encoding="utf-8")

    role_match = re.search(
        r'<select id="role">(?P<body>.*?)</select>',
        text,
        flags=re.DOTALL,
    )
    if role_match is None:
        # Safe member surface can omit manual actor role selector entirely.
        assert 'id="role"' not in text
        return
    role_body = role_match.group("body")
    assert 'value="member"' in role_body
    assert 'value="reviewer"' not in role_body
    assert 'value="admin"' not in role_body


def test_member_runtime_prunes_admin_scoped_dom_after_auth_init() -> None:
    text = (REPO_ROOT / "sharelife" / "webui" / "app.js").read_text(encoding="utf-8")

    assert "function pruneMemberPrivilegedDom()" in text
    assert "document.querySelectorAll('[data-console-scope=\"admin\"]')" in text
    assert "document.body.setAttribute(\"data-member-surface\", \"minimal\")" in text
    assert "await initAuth()" in text
    assert "pruneMemberPrivilegedDom()" in text


def test_bind_buttons_delegates_admin_operation_binding_slice() -> None:
    text = (REPO_ROOT / "sharelife" / "webui" / "app.js").read_text(encoding="utf-8")

    assert "function bindAdminOperationsControls()" in text
    assert "bindAdminOperationsControls()" in text


def test_bind_buttons_delegates_member_import_binding_slice() -> None:
    text = (REPO_ROOT / "sharelife" / "webui" / "app.js").read_text(encoding="utf-8")

    assert "function bindMemberImportControls()" in text
    assert "bindMemberImportControls()" in text


def test_bind_buttons_delegates_reviewer_lifecycle_binding_slice() -> None:
    text = (REPO_ROOT / "sharelife" / "webui" / "app.js").read_text(encoding="utf-8")

    assert "function bindReviewerLifecycleControls()" in text
    assert "bindReviewerLifecycleControls()" in text


def test_bind_buttons_delegates_preference_binding_slice() -> None:
    text = (REPO_ROOT / "sharelife" / "webui" / "app.js").read_text(encoding="utf-8")

    assert "function bindPreferenceControls()" in text
    assert "bindPreferenceControls()" in text


def test_bind_buttons_delegates_member_market_binding_slice() -> None:
    text = (REPO_ROOT / "sharelife" / "webui" / "app.js").read_text(encoding="utf-8")

    assert "function bindMemberMarketControls()" in text
    assert "bindMemberMarketControls()" in text


def test_bind_buttons_delegates_template_drawer_wizard_slice() -> None:
    text = (REPO_ROOT / "sharelife" / "webui" / "app.js").read_text(encoding="utf-8")

    assert "function bindTemplateDrawerAndWizardControls()" in text
    assert "bindTemplateDrawerAndWizardControls()" in text


def test_bind_buttons_delegates_template_execution_slice() -> None:
    text = (REPO_ROOT / "sharelife" / "webui" / "app.js").read_text(encoding="utf-8")

    assert "function bindTemplateExecutionControls()" in text
    assert "bindTemplateExecutionControls()" in text


def test_bind_buttons_delegates_profile_pack_binding_slice() -> None:
    text = (REPO_ROOT / "sharelife" / "webui" / "app.js").read_text(encoding="utf-8")

    assert "function bindProfilePackControls()" in text
    assert "bindProfilePackControls()" in text


def test_bind_buttons_delegates_submission_review_binding_slice() -> None:
    text = (REPO_ROOT / "sharelife" / "webui" / "app.js").read_text(encoding="utf-8")

    assert "function bindSubmissionReviewControls()" in text
    assert "bindSubmissionReviewControls()" in text


def test_bind_buttons_delegates_sidebar_navigation_binding_slice() -> None:
    text = (REPO_ROOT / "sharelife" / "webui" / "app.js").read_text(encoding="utf-8")

    assert "function bindSidebarNavigationControls()" in text
    assert "bindSidebarNavigationControls()" in text


def test_bind_buttons_delegates_auth_panel_binding_slice() -> None:
    text = (REPO_ROOT / "sharelife" / "webui" / "app.js").read_text(encoding="utf-8")

    assert "function bindAuthPanelControls()" in text
    assert "bindAuthPanelControls()" in text


def test_bind_buttons_delegates_locale_and_developer_binding_slice() -> None:
    text = (REPO_ROOT / "sharelife" / "webui" / "app.js").read_text(encoding="utf-8")

    assert "function bindLocaleAndDeveloperControls()" in text
    assert "bindLocaleAndDeveloperControls()" in text


def test_bind_buttons_delegates_workspace_route_binding_slice() -> None:
    text = (REPO_ROOT / "sharelife" / "webui" / "app.js").read_text(encoding="utf-8")

    assert "function bindWorkspaceRouteControls()" in text
    assert "bindWorkspaceRouteControls()" in text


def test_bootstrap_delegates_ui_state_initialization_slice() -> None:
    text = (REPO_ROOT / "sharelife" / "webui" / "app.js").read_text(encoding="utf-8")

    assert "function initializeBootstrapUiState()" in text
    assert "initializeBootstrapUiState()" in text


def test_bootstrap_delegates_post_auth_member_data_slice() -> None:
    text = (REPO_ROOT / "sharelife" / "webui" / "app.js").read_text(encoding="utf-8")

    assert "async function loadPostAuthMemberData()" in text
    assert "await loadPostAuthMemberData()" in text


def test_member_source_template_excludes_privileged_admin_sections() -> None:
    text = (REPO_ROOT / "sharelife" / "webui" / "member.html").read_text(encoding="utf-8")

    assert 'data-console-scope="admin"' not in text
    assert 'id="section-admin-apply"' not in text
    assert 'id="section-continuity"' not in text
    assert 'id="section-profile-pack"' not in text
    assert 'id="section-admin-submissions"' not in text
    assert 'id="submissionWorkspaceSection"' not in text
    assert 'id="section-storage-backup"' not in text
    assert 'id="btnStorageRunBackup"' not in text
