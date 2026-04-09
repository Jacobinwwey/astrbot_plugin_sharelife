from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_public_projection_script_and_manifest_exist() -> None:
    assert (REPO_ROOT / "scripts" / "promote_public_projection.py").exists()
    assert (REPO_ROOT / "ops" / "public_projection_manifest.json").exists()
