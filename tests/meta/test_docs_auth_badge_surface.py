from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_api_reference_docs_include_public_member_auth_badges_without_private_routes():
    for locale in ("zh", "en", "ja"):
        text = (REPO_ROOT / "docs" / locale / "reference" / "api-v1.md").read_text(
            encoding="utf-8"
        )

        assert "Auth Badge Matrix (HTTP)" in text
        assert "GET /api/profile-pack/catalog/insights" in text
        assert "POST /api/templates/submit" in text
        assert "POST /api/profile-pack/submit" in text
        assert "GET /api/member/installations" in text
        assert "POST /api/member/installations/uninstall" in text
        assert "GET /api/templates/package/download" in text
        assert "GET /api/notifications" in text
        assert "permission_denied" in text
        assert "/api/reviewer/" not in text
        assert "/api/admin/" not in text
