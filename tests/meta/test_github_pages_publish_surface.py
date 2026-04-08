from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]


def _workflow_on_section(workflow: dict) -> dict:
    on_section = workflow.get("on") or workflow.get(True)
    assert on_section is not None
    return on_section


def test_docs_config_uses_docs_base_with_project_site_default():
    text = (REPO_ROOT / "docs" / ".vitepress" / "config.ts").read_text(encoding="utf-8")
    assert "DOCS_BASE" in text
    assert "/astrbot_plugin_sharelife/" in text


def test_github_pages_workflow_exists_and_supports_git_ref():
    workflow_path = REPO_ROOT / ".github" / "workflows" / "deploy-docs-github-pages.yml"
    assert workflow_path.exists()
    workflow = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
    workflow_on = _workflow_on_section(workflow)
    assert "workflow_dispatch" in workflow_on
    assert "git_ref" in workflow_on["workflow_dispatch"]["inputs"]


def test_github_pages_workflow_uses_node24_compatible_actions():
    text = (REPO_ROOT / ".github" / "workflows" / "deploy-docs-github-pages.yml").read_text(
        encoding="utf-8"
    )
    assert "actions/checkout@v6" in text
    assert "actions/setup-node@v6" in text
    assert 'node-version: "24"' in text
    assert "actions/configure-pages@v6" in text
    assert "actions/upload-pages-artifact@v4" in text
    assert "actions/deploy-pages@v5" in text


def test_github_pages_workflow_push_paths_include_market_snapshot_sources():
    workflow_path = REPO_ROOT / ".github" / "workflows" / "deploy-docs-github-pages.yml"
    workflow = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
    workflow_on = _workflow_on_section(workflow)
    push_section = workflow_on.get("push", {})
    paths = push_section.get("paths", [])

    assert "docs/**" in paths
    assert "templates/**" in paths
    assert "scripts/build_market_snapshot.py" in paths


def test_public_navigation_omits_github_pages_publish_guides():
    config_text = (REPO_ROOT / "docs" / ".vitepress" / "config.ts").read_text(encoding="utf-8")
    assert "/zh/how-to/github-pages-publish" not in config_text
    assert "/en/how-to/github-pages-publish" not in config_text
    assert "/ja/how-to/github-pages-publish" not in config_text


def test_readme_names_the_github_pages_url():
    text = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    assert "https://jacobinwwey.github.io/astrbot_plugin_sharelife/" in text
    assert "EdgeOne Fallback Publishing" not in text


def test_public_publish_docs_no_longer_reference_edgeone():
    localized_pages = [
        REPO_ROOT / "docs" / "en" / "how-to" / "github-pages-publish.md",
        REPO_ROOT / "docs" / "zh" / "how-to" / "github-pages-publish.md",
        REPO_ROOT / "docs" / "ja" / "how-to" / "github-pages-publish.md",
    ]

    for page_path in localized_pages:
        if not page_path.exists():
            continue
        text = page_path.read_text(encoding="utf-8")
        assert "EdgeOne" not in text
        assert "edgeone" not in text
