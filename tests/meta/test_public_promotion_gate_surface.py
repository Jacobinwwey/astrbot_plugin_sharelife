from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_public_promotion_gate_checker_exists() -> None:
    checker = REPO_ROOT / "scripts" / "check_public_promotion_gate.py"
    assert checker.exists()


def test_public_promotion_gate_is_wired_in_ci() -> None:
    workflow = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert "scripts/check_public_promotion_gate.py" in workflow
    assert "Fetch origin/main for promotion gate" in workflow
