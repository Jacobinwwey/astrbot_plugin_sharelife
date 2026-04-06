from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_public_permission_boundary_roadmap_is_revised_and_sanitized():
    english = (REPO_ROOT / "docs" / "en" / "reference" / "permission-boundary-roadmap.md").read_text(
        encoding="utf-8"
    )
    chinese = (REPO_ROOT / "docs" / "zh" / "reference" / "permission-boundary-roadmap.md").read_text(
        encoding="utf-8"
    )
    japanese = (REPO_ROOT / "docs" / "ja" / "reference" / "permission-boundary-roadmap.md").read_text(
        encoding="utf-8"
    )

    assert "owner-aware" in english
    assert "admin-to-reviewer" in english
    assert "single active reviewer session" not in english.lower()
    assert "owner-aware" in chinese
    assert "owner-aware" in japanese
