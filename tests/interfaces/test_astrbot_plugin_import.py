from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def test_plugin_main_imports_under_astrbot_package_layout(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    package_root = tmp_path / "data" / "plugins"
    package_root.mkdir(parents=True)
    (tmp_path / "data" / "__init__.py").write_text("", encoding="utf-8")
    (package_root / "__init__.py").write_text("", encoding="utf-8")
    os.symlink(repo_root, package_root / "astrbot_plugin_sharelife", target_is_directory=True)

    astrbot_api = tmp_path / "astrbot" / "api"
    astrbot_api.mkdir(parents=True)
    (tmp_path / "astrbot" / "__init__.py").write_text("", encoding="utf-8")
    (astrbot_api / "__init__.py").write_text(
        "\n".join(
            [
                "class _Logger:",
                "    def warning(self, *args, **kwargs):",
                "        return None",
                "logger = _Logger()",
                "",
                "class sp:",
                "    @staticmethod",
                "    def get_data_dir(name):",
                "        raise RuntimeError('stub')",
            ]
        ),
        encoding="utf-8",
    )
    (astrbot_api / "event.py").write_text(
        "\n".join(
            [
                "class AstrMessageEvent:",
                "    pass",
                "",
                "class _Filter:",
                "    @staticmethod",
                "    def command(name):",
                "        def decorator(func):",
                "            return func",
                "        return decorator",
                "",
                "filter = _Filter()",
            ]
        ),
        encoding="utf-8",
    )
    (astrbot_api / "star.py").write_text(
        "\n".join(
            [
                "class Context:",
                "    pass",
                "",
                "class Star:",
                "    def __init__(self, context, config=None):",
                "        self.context = context",
                "        self.config = config",
                "",
                "def register(*args, **kwargs):",
                "    def decorator(cls):",
                "        return cls",
                "    return decorator",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "-c", "import data.plugins.astrbot_plugin_sharelife.main"],
        cwd=tmp_path,
        env={**os.environ, "PYTHONPATH": str(tmp_path)},
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
