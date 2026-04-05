from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_edgeone_workflow_and_scripts_are_removed():
    assert (REPO_ROOT / ".github" / "workflows" / "deploy-docs-edgeone.yml").exists() is False
    assert (REPO_ROOT / "scripts" / "deploy_edgeone_docs.sh").exists() is False
    assert (REPO_ROOT / "docs" / "scripts" / "publish-edgeone.mjs").exists() is False


def test_makefile_no_longer_exposes_edgeone_publish_target():
    text = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    assert "docs-publish-edgeone" not in text
    assert "deploy_edgeone_docs.sh" not in text


def test_docs_package_scripts_remove_edgeone_publish_entry():
    package_json = json.loads((REPO_ROOT / "docs" / "package.json").read_text(encoding="utf-8"))
    scripts = package_json.get("scripts", {})
    dev_dependencies = package_json.get("devDependencies", {})

    assert "docs:publish:edgeone" not in scripts
    assert "edgeone-pages-mcp-fullstack" not in dev_dependencies


def test_docs_lockfile_no_longer_contains_edgeone_mcp_dependency():
    text = (REPO_ROOT / "docs" / "package-lock.json").read_text(encoding="utf-8")
    assert "edgeone-pages-mcp-fullstack" not in text


def test_public_docs_and_readme_do_not_reference_edgeone_publish_path():
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    assert "EdgeOne" not in readme
    assert "edgeone" not in readme

    localized_pages = [
        REPO_ROOT / "docs" / "zh" / "how-to" / "edgeone-publish.md",
        REPO_ROOT / "docs" / "en" / "how-to" / "edgeone-publish.md",
        REPO_ROOT / "docs" / "ja" / "how-to" / "edgeone-publish.md",
    ]
    for page_path in localized_pages:
        assert page_path.exists() is False
