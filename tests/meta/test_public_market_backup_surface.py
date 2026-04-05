from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]


def _workflow_on_section(workflow: dict) -> dict:
    on_section = workflow.get("on") or workflow.get(True)
    assert on_section is not None
    return on_section


def test_public_market_backup_workflow_exists_and_is_scheduled():
    workflow_path = REPO_ROOT / ".github" / "workflows" / "public-market-backup.yml"
    assert workflow_path.exists()
    workflow = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
    workflow_on = _workflow_on_section(workflow)
    assert "workflow_dispatch" in workflow_on
    assert "schedule" in workflow_on


def test_public_market_backup_workflow_targets_sanitized_market_paths_only():
    workflow_path = REPO_ROOT / ".github" / "workflows" / "public-market-backup.yml"
    workflow = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
    paths = _workflow_on_section(workflow).get("push", {}).get("paths", [])

    assert "docs/public/market/**" in paths
    assert "scripts/backup_public_market.py" in paths
    assert "sharelife/infrastructure/public_market_backup.py" in paths


def test_readme_mentions_public_market_backup_and_reviewer_contact():
    text = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    assert "public market" in text.lower()
    assert "Jacobinwwey" in text
