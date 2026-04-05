from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_superpowers_privacy_guard_is_wired_in_ci():
    workflow = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert "scripts/check_superpowers_privacy.py" in workflow


def test_superpowers_privacy_policy_and_checker_exist():
    checker = REPO_ROOT / "scripts" / "check_superpowers_privacy.py"
    policy = REPO_ROOT / "docs" / "superpowers" / "PRIVACY_POLICY.md"
    assert checker.exists()
    assert policy.exists()
