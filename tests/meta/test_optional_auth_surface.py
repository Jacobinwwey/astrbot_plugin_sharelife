from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_member_surface_exposes_optional_auth_entrypoints() -> None:
    app_js = (REPO_ROOT / 'sharelife' / 'webui' / 'app.js').read_text(encoding='utf-8')
    member_html = (REPO_ROOT / 'sharelife' / 'webui' / 'member.html').read_text(encoding='utf-8')
    index_html = (REPO_ROOT / 'sharelife' / 'webui' / 'index.html').read_text(encoding='utf-8')

    assert 'authPromptRequested' in app_js
    assert 'auth.status.optional' in app_js
    assert 'btnAuthOpenLoginPanel' in app_js
    assert 'id="btnAuthOpenLoginPanel"' in member_html
    assert 'id="authGuidance"' in member_html
    assert 'id="btnAuthOpenLoginPanel"' in index_html
    assert 'id="authGuidance"' in index_html
