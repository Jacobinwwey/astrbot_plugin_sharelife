from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_trilingual_execution_plan_docs_exist_and_are_wired_in_navigation():
    config_text = (REPO_ROOT / "docs" / ".vitepress" / "config.ts").read_text(encoding="utf-8")
    en_index = (REPO_ROOT / "docs" / "en" / "index.md").read_text(encoding="utf-8")
    zh_index = (REPO_ROOT / "docs" / "zh" / "index.md").read_text(encoding="utf-8")
    ja_index = (REPO_ROOT / "docs" / "ja" / "index.md").read_text(encoding="utf-8")

    paths = {
        "en": [
            "/en/reference/user-panel-stitch-execution-plan",
            "/en/reference/storage-cold-backup-execution-plan",
            "/en/reference/integrated-execution-playbook",
        ],
        "zh": [
            "/zh/reference/user-panel-stitch-execution-plan",
            "/zh/reference/storage-cold-backup-execution-plan",
            "/zh/reference/integrated-execution-playbook",
        ],
        "ja": [
            "/ja/reference/user-panel-stitch-execution-plan",
            "/ja/reference/storage-cold-backup-execution-plan",
            "/ja/reference/integrated-execution-playbook",
        ],
    }

    for locale, links in paths.items():
        for link in links:
            assert (REPO_ROOT / "docs" / locale / "reference" / f"{Path(link).name}.md").exists()
            assert link in config_text

    for link in paths["en"]:
        assert link in en_index
    for link in paths["zh"]:
        assert link in zh_index
    for link in paths["ja"]:
        assert link in ja_index
