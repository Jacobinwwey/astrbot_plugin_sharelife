from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_profile_pack_selection_tree_depth_is_four_levels() -> None:
    text = (
        REPO_ROOT
        / "sharelife"
        / "application"
        / "services_profile_pack.py"
    ).read_text(encoding="utf-8")

    assert "SELECTION_TREE_MAX_DEPTH = 4" in text
    assert text.count("max_depth=SELECTION_TREE_MAX_DEPTH") >= 10
