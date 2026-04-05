from pathlib import Path
import subprocess


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_webui_e2e_runner_uses_playwright_with_no_sandbox():
    runner = REPO_ROOT / "scripts" / "run_webui_e2e.sh"
    script = REPO_ROOT / "tests" / "e2e" / "sharelife_webui_e2e.cjs"
    server = REPO_ROOT / "tests" / "e2e" / "serve_webui.py"

    assert runner.exists()
    assert script.exists()
    assert server.exists()

    runner_text = runner.read_text()
    script_text = script.read_text()

    assert "npx --yes --package=playwright" in runner_text
    assert "NODE_PATH" in runner_text
    assert "serve_webui.py" in runner_text
    assert "sharelife_webui_e2e.cjs" in runner_text
    assert "chromiumSandbox: false" in script_text
    assert "workspaceRoute" in script_text
    assert "uiLocale" in script_text
    assert "btnTemplates" in script_text
    assert "templateListState" in script_text
    assert "submissionListState" in script_text
    assert "btnProfilePackExport" in script_text
    assert "btnProfilePackImportFromExport" in script_text
    assert "btnProfilePackImportDryrun" in script_text
    assert "btnProfilePackSubmitCommunity" in script_text
    assert "btnProfilePackListPackSubmissions" in script_text
    assert "btnProfilePackDecideSubmission" in script_text
    assert "btnProfilePackListCatalog" in script_text
    assert "btnProfilePackCatalogDetail" in script_text
    assert "btnToggleDeveloperMode" in script_text
    assert "scanEvidenceList" in script_text
    assert "compare.evidence_focus" in script_text or "evidence" in script_text
    assert "/api/admin/profile-pack/import-and-dryrun" in script_text


def test_webui_seed_server_entrypoint_loads_from_repo_root():
    completed = subprocess.run(
        ["python3", "tests/e2e/serve_webui.py", "--help"],
        cwd=REPO_ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert completed.returncode == 0
    assert "usage:" in completed.stdout.lower()


def test_webui_seed_server_enables_profile_pack_service():
    server = REPO_ROOT / "tests" / "e2e" / "serve_webui.py"
    text = server.read_text()
    assert "ProfilePackService" in text
    assert "profile_pack_service=profile_pack" in text
