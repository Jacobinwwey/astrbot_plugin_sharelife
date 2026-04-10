from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]

# Guardrail budgets to stop monolith growth while decomposition is in progress.
LINE_BUDGETS = {
    "sharelife/webui/app.js": 9800,
    "sharelife/webui/market_page.js": 4550,
    "sharelife/interfaces/webui_server.py": 3900,
}


def _line_count(path: Path) -> int:
    return len(path.read_text(encoding="utf-8").splitlines())


def test_core_monolith_files_stay_within_decomposition_budgets() -> None:
    for relative_path, max_lines in LINE_BUDGETS.items():
        file_path = REPO_ROOT / relative_path
        assert file_path.exists(), f"missing guarded file: {relative_path}"
        count = _line_count(file_path)
        assert count <= max_lines, (
            f"decomposition budget exceeded for {relative_path}: {count} > {max_lines}"
        )
