from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_protocol_schema_files_and_examples_exist():
    root = REPO_ROOT / "sharelife" / "contracts"
    assert (root / "plugin.manifest.v2.schema.json").exists()
    assert (root / "astr-agent.v1.schema.json").exists()
    assert (root / "examples" / "plugin.manifest.v2.example.json").exists()
    assert (root / "examples" / "astr-agent.example.yaml").exists()


def test_ci_workflow_runs_protocol_validation_script():
    workflow = yaml.safe_load((REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8"))
    jobs = workflow.get("jobs", {})
    test_job = jobs.get("test", {})
    steps = test_job.get("steps", [])
    run_values = [str(step.get("run", "") or "") for step in steps if isinstance(step, dict)]
    assert any("scripts/validate_protocol_examples.py" in run for run in run_values)


def test_makefile_exposes_protocol_validate_target():
    makefile = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    assert "protocol-validate:" in makefile
    assert "scripts/validate_protocol_examples.py" in makefile
