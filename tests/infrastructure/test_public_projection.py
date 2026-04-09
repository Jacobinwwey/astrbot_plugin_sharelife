from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "promote_public_projection.py"
MANIFEST_PATH = REPO_ROOT / "ops" / "public_projection_manifest.json"


def _load_module():
    spec = importlib.util.spec_from_file_location("public_projection", SCRIPT_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_projection_manifest_filters_private_docs_and_local_secrets(tmp_path: Path) -> None:
    module = _load_module()
    source_root = tmp_path / "source"
    source_root.mkdir(parents=True, exist_ok=True)
    (source_root / "README.md").write_text("public", encoding="utf-8")
    (source_root / "docs" / "en" / "how-to").mkdir(parents=True)
    (source_root / "docs" / "en" / "how-to" / "guide.md").write_text("guide", encoding="utf-8")
    (source_root / "docs" / ".vitepress").mkdir(parents=True)
    (source_root / "docs" / ".vitepress" / "config.ts").write_text("export default {}", encoding="utf-8")
    (source_root / "docs" / ".vitepress" / "private-sidebar.json").write_text("{}", encoding="utf-8")
    (source_root / "docs" / ".vitepress" / "dist" / "assets").mkdir(parents=True)
    (source_root / "docs" / ".vitepress" / "dist" / "assets" / "en_private_index.js").write_text(
        "private build output",
        encoding="utf-8",
    )
    (source_root / "scripts").mkdir(parents=True)
    (source_root / "scripts" / "sync_local_private_docs.py").write_text("print('private helper')", encoding="utf-8")
    (source_root / "tests" / "meta" / "__pycache__").mkdir(parents=True)
    (source_root / "tests" / "meta" / "test_private_docs_portal_surface.py").write_text(
        "def test_private(): pass",
        encoding="utf-8",
    )
    (source_root / "tests" / "meta" / "__pycache__" / "test_private_docs_portal_surface.cpython-312.pyc").write_bytes(
        b"pyc",
    )
    (source_root / "docs" / "en" / "private").mkdir(parents=True)
    (source_root / "docs" / "en" / "private" / "secret.md").write_text("secret", encoding="utf-8")
    (source_root / "output" / "standalone-data" / "secrets").mkdir(parents=True)
    (source_root / "output" / "standalone-data" / "secrets" / "webui-auth.local.toml").write_text(
        "admin_password = 'secret'",
        encoding="utf-8",
    )

    manifest = module.load_manifest(MANIFEST_PATH)
    projected = module.resolve_projection_files(source_root=source_root, manifest=manifest)

    assert "README.md" in projected
    assert "docs/en/how-to/guide.md" in projected
    assert "docs/.vitepress/config.ts" in projected
    assert "docs/.vitepress/private-sidebar.json" not in projected
    assert "docs/.vitepress/dist/assets/en_private_index.js" not in projected
    assert "docs/en/private/secret.md" not in projected
    assert "scripts/sync_local_private_docs.py" not in projected
    assert "tests/meta/test_private_docs_portal_surface.py" not in projected
    assert "tests/meta/__pycache__/test_private_docs_portal_surface.cpython-312.pyc" not in projected
    assert "output/standalone-data/secrets/webui-auth.local.toml" not in projected


def test_projection_plan_copies_allowed_files_and_prunes_managed_stale_files(tmp_path: Path) -> None:
    module = _load_module()
    source_root = tmp_path / "source"
    dest_root = tmp_path / "dest"
    source_root.mkdir(parents=True, exist_ok=True)
    dest_root.mkdir(parents=True, exist_ok=True)
    (source_root / "README.md").write_text("new readme", encoding="utf-8")
    (source_root / "docs" / "en" / "how-to").mkdir(parents=True)
    (source_root / "docs" / "en" / "how-to" / "guide.md").write_text("fresh guide", encoding="utf-8")
    (source_root / "docs" / "en" / "private").mkdir(parents=True)
    (source_root / "docs" / "en" / "private" / "secret.md").write_text("private", encoding="utf-8")

    (dest_root / "README.md").write_text("old readme", encoding="utf-8")
    (dest_root / "docs" / "en" / "how-to").mkdir(parents=True)
    (dest_root / "docs" / "en" / "how-to" / "stale.md").write_text("stale", encoding="utf-8")
    (dest_root / "docs" / "en" / "private").mkdir(parents=True)
    (dest_root / "docs" / "en" / "private" / "secret.md").write_text("should be removed", encoding="utf-8")
    (dest_root / "scripts").mkdir(parents=True)
    (dest_root / "scripts" / "keep.sh").write_text("outside managed roots for this test", encoding="utf-8")

    manifest = {
        "managed_roots": ["README.md", "docs"],
        "include": ["README.md", "docs/**"],
        "exclude": ["docs/*/private/**"],
    }
    plan = module.build_projection_plan(
        source_root=source_root,
        dest_root=dest_root,
        manifest=manifest,
    )

    assert "README.md" in plan["update_paths"]
    assert "docs/en/how-to/guide.md" in plan["copy_paths"]
    assert "docs/en/how-to/stale.md" in plan["remove_paths"]
    assert "docs/en/private/secret.md" in plan["remove_paths"]

    result = module.apply_projection_plan(
        source_root=source_root,
        dest_root=dest_root,
        plan=plan,
        delete=True,
    )

    assert result["copied"] == 1
    assert result["updated"] == 1
    assert result["removed"] == 2
    assert (dest_root / "README.md").read_text(encoding="utf-8") == "new readme"
    assert (dest_root / "docs" / "en" / "how-to" / "guide.md").read_text(encoding="utf-8") == "fresh guide"
    assert not (dest_root / "docs" / "en" / "how-to" / "stale.md").exists()
    assert not (dest_root / "docs" / "en" / "private" / "secret.md").exists()
    assert (dest_root / "scripts" / "keep.sh").exists()


def test_projection_cli_dry_run_writes_json_summary(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    dest_root = tmp_path / "dest"
    manifest_path = tmp_path / "manifest.json"
    output_path = tmp_path / "projection-report.json"

    source_root.mkdir(parents=True, exist_ok=True)
    (source_root / "README.md").write_text("public", encoding="utf-8")
    manifest_path.write_text(
        json.dumps(
            {
                "managed_roots": ["README.md"],
                "include": ["README.md"],
                "exclude": [],
            }
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--source-root",
            str(source_root),
            "--dest-root",
            str(dest_root),
            "--manifest",
            str(manifest_path),
            "--dry-run",
            "--json-output",
            str(output_path),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    report = json.loads(output_path.read_text(encoding="utf-8"))
    assert report["projected_files_count"] == 1
    assert report["copy_paths"] == ["README.md"]
    assert report["dry_run"] is True
