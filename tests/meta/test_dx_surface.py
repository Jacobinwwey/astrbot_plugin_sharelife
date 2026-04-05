import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_dx_scripts_exist_and_are_referenced():
    makefile = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    assert (REPO_ROOT / "scripts" / "create-astrbot-plugin").exists()
    assert (REPO_ROOT / "scripts" / "sharelife-hot-reload").exists()
    assert (REPO_ROOT / "scripts" / "sharelife-init-wizard").exists()
    assert "dx-scaffold:" in makefile
    assert "dx-hot-reload:" in makefile
    assert "dx-init-wizard:" in makefile


def test_create_astrbot_plugin_scaffold_command_generates_minimal_plugin(tmp_path):
    output_dir = tmp_path / "out"
    output_dir.mkdir()

    completed = subprocess.run(
        [
            "bash",
            "scripts/create-astrbot-plugin",
            "--name",
            "astrbot_plugin_demo",
            "--author",
            "tester",
            "--output",
            str(output_dir),
        ],
        cwd=REPO_ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    assert completed.returncode == 0, completed.stderr
    plugin_root = output_dir / "astrbot_plugin_demo"
    assert (plugin_root / "main.py").exists()
    assert (plugin_root / "metadata.yaml").exists()
    assert (plugin_root / "README.md").exists()
    assert (plugin_root / "tests" / "test_smoke.py").exists()


def test_sharelife_hot_reload_supports_dry_run(tmp_path):
    watch_dir = tmp_path / "watch"
    watch_dir.mkdir()
    (watch_dir / "main.py").write_text("print('ok')\n", encoding="utf-8")

    env = os.environ.copy()
    completed = subprocess.run(
        [
            "bash",
            "scripts/sharelife-hot-reload",
            "--watch",
            str(watch_dir),
            "--cmd",
            "python3 -c pass",
            "--dry-run",
        ],
        cwd=REPO_ROOT,
        env=env,
        check=False,
        text=True,
        capture_output=True,
    )
    assert completed.returncode == 0
    assert "mode=dry-run" in completed.stdout


def test_sharelife_init_wizard_supports_non_interactive_generation(tmp_path):
    output = tmp_path / "config.generated.yaml"
    completed = subprocess.run(
        [
            "bash",
            "scripts/sharelife-init-wizard",
            "--yes",
            "--provider",
            "openai",
            "--api-key",
            "sk-test",
            "--preset",
            "sharelife_companion",
            "--webui-auth",
            "true",
            "--member-password",
            "member-pass",
            "--admin-password",
            "admin-pass",
            "--enable-plugin-install-exec",
            "false",
            "--output",
            str(output),
        ],
        cwd=REPO_ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    assert completed.returncode == 0, completed.stderr
    assert output.exists()
    text = output.read_text(encoding="utf-8")
    assert 'provider: "openai"' in text
    assert 'startup_template_id: "community/support-care"' in text
    assert 'member_password: "member-pass"' in text
    assert 'admin_password: "admin-pass"' in text
    assert "enabled: false" in text
