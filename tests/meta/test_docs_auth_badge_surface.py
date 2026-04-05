from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_api_reference_docs_include_auth_badge_matrix_and_reviewer_routes():
    for locale in ("zh", "en", "ja"):
        text = (REPO_ROOT / "docs" / locale / "reference" / "api-v1.md").read_text(
            encoding="utf-8"
        )

        assert "Auth Badge Matrix (HTTP)" in text
        assert "GET /api/profile-pack/catalog/insights" in text
        assert "GET /api/reviewer/submissions" in text
        assert "POST /api/reviewer/submissions/decide" in text
        assert "POST /api/admin/profile-pack/apply" in text
        assert "POST /api/admin/pipeline/run" in text
        assert "permission_denied" in text

