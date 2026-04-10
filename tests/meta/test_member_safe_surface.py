from __future__ import annotations

import runpy
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_member_route_prefers_safe_page_artifact() -> None:
    server_text = (REPO_ROOT / "sharelife" / "interfaces" / "webui_server.py").read_text(encoding="utf-8")

    assert 'member_path = self.web_root / "member.safe.html"' in server_text
    assert 'member_path = self.web_root / "member.html"' in server_text


def test_member_safe_page_excludes_admin_and_reviewer_console_surface() -> None:
    html = (REPO_ROOT / "sharelife" / "webui" / "member.safe.html").read_text(encoding="utf-8")

    assert 'data-console-scope="admin"' not in html
    assert 'id="section-admin-apply"' not in html
    assert 'id="section-continuity"' not in html
    assert 'id="section-profile-pack"' not in html
    assert 'id="section-admin-submissions"' not in html
    assert 'id="submissionWorkspaceSection"' not in html
    assert 'id="section-retry-queue"' not in html
    assert 'id="section-reliability"' not in html
    assert 'id="section-storage-backup"' not in html
    assert 'id="btnStorageRunBackup"' not in html
    assert 'id="btnRetryDecide"' not in html
    assert 'id="btnReviewerInviteCreate"' not in html
    assert 'href="/admin"' not in html
    assert 'href="/reviewer"' not in html


def test_member_safe_page_matches_generator_output() -> None:
    source_html = (REPO_ROOT / "sharelife" / "webui" / "member.html").read_text(encoding="utf-8")
    safe_html = (REPO_ROOT / "sharelife" / "webui" / "member.safe.html").read_text(encoding="utf-8")
    namespace = runpy.run_path(str(REPO_ROOT / "scripts" / "build_member_safe_html.py"))
    build_member_safe_html = namespace["build_member_safe_html"]

    assert safe_html == build_member_safe_html(source_html)
