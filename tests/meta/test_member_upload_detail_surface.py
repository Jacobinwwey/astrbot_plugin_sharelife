from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_member_upload_detail_modal_uses_master_detail_layout() -> None:
    html = (REPO_ROOT / "sharelife" / "webui" / "member.html").read_text(encoding="utf-8")
    css = (REPO_ROOT / "sharelife" / "webui" / "style.css").read_text(encoding="utf-8")

    assert 'id="memberUploadDetailTreePane"' in html
    assert 'id="memberUploadDetailInspector"' in html
    assert 'id="memberUploadDetailInspectorHeading"' in html
    assert 'id="memberUploadDetailInspectorPreview"' in html
    assert 'id="memberUploadDetailInspectorChildren"' in html

    assert ".member-upload-detail-workbench" in css
    assert ".member-upload-tree-pane" in css
    assert ".member-upload-inspector-pane" in css
    assert ".member-upload-inspector-preview" in css
    assert ".modal-shell" in css
    assert ".modal-panel-glass" in css
    assert "overflow: auto;" in css
    assert "overscroll-behavior: contain;" in css
    assert "grid-template-rows: auto minmax(0, 1fr) auto;" in css
    assert ".member-upload-review-shell" in css
    assert "height: 100%;" in css
    assert "overflow: hidden;" in css
    assert "grid-template-rows: auto auto minmax(0, 1fr);" in css
    assert "body.modal-scroll-locked" in css
    assert ".profile-pack-section-title" in css
    assert ".profile-pack-section-description" in css
    assert "overflow-wrap: anywhere;" in css

    app_js = (REPO_ROOT / "sharelife" / "webui" / "app.js").read_text(encoding="utf-8")
    assert "SharelifeDialogScrollLock" in app_js
