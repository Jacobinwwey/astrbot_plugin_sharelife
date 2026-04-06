from pathlib import Path
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_superpowers_privacy_guard_is_wired_in_ci():
    workflow = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert "scripts/check_superpowers_privacy.py" in workflow


def test_superpowers_privacy_policy_and_checker_exist():
    checker = REPO_ROOT / "scripts" / "check_superpowers_privacy.py"
    assert checker.exists()
    scan_root = REPO_ROOT / "docs" / "superpowers"
    if scan_root.exists():
        policy = scan_root / "PRIVACY_POLICY.md"
        assert policy.exists()


def test_superpowers_privacy_checker_skips_missing_scan_root():
    checker = REPO_ROOT / "scripts" / "check_superpowers_privacy.py"
    missing_root = REPO_ROOT / "docs" / "superpowers"
    result = subprocess.run(
        [sys.executable, str(checker), "--scan-root", str(missing_root)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    output = f"{result.stdout}\n{result.stderr}"
    if not missing_root.exists():
        assert "skipped: scan root not found" in output
