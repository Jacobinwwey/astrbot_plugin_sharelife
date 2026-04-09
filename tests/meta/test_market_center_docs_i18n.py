from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def test_market_center_superpowers_docs_are_split_by_locale():
    spec_en = _read("docs/superpowers/specs/2026-04-05-market-center-redesign-design.md")
    spec_zh = _read("docs/superpowers/specs/2026-04-05-market-center-redesign-design.zh-CN.md")
    spec_ja = _read("docs/superpowers/specs/2026-04-05-market-center-redesign-design.ja-JP.md")

    plan_en = _read("docs/superpowers/plans/2026-04-05-sharelife-market-center-redesign-implementation.md")
    plan_zh = _read("docs/superpowers/plans/2026-04-05-sharelife-market-center-redesign-implementation.zh-CN.md")
    plan_ja = _read("docs/superpowers/plans/2026-04-05-sharelife-market-center-redesign-implementation.ja-JP.md")

    assert "## 中文文档" not in spec_en
    assert "## 日本語文書" not in spec_en
    assert "## English Document" not in spec_en
    assert "当前语言：简体中文" in spec_zh
    assert "現在の言語: 日本語" in spec_ja

    assert "## 中文文档" not in plan_en
    assert "## 日本語文書" not in plan_en
    assert "**Canonical language:** English" in plan_en
    assert "**当前语言：** 简体中文" in plan_zh
    assert "**現在の言語:** 日本語" in plan_ja
