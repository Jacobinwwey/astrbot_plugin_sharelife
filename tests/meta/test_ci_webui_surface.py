from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_ci_workflow_runs_webui_node_tests_and_keeps_e2e_temporarily_skipped():
    workflow_path = REPO_ROOT / ".github" / "workflows" / "ci.yml"
    assert workflow_path.exists()

    text = workflow_path.read_text()

    assert "actions/setup-node@v6" in text
    assert "node-version: '24'" in text
    assert "node --test tests/webui/*.js" in text
    assert "bash scripts/run_webui_e2e.sh" in text
    assert "SHARELIFE_SKIP_WEBUI_E2E" in text
    assert "google-chrome" in text or "chrome" in text
