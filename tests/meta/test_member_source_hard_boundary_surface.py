from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_member_source_template_enforces_hard_boundary_markers() -> None:
    html = (REPO_ROOT / "sharelife" / "webui" / "member.html").read_text(encoding="utf-8")

    assert 'data-console-scope="admin"' not in html
    assert 'data-console-scope="reviewer"' not in html
    assert 'href="/admin"' not in html
    assert 'href="/reviewer"' not in html
    assert 'id="section-admin-apply"' not in html
    assert 'id="section-admin-submissions"' not in html
    assert 'id="section-storage-backup"' not in html
