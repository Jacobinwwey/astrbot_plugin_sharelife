from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def _anonymous_member_allowlist_entries() -> list[tuple[str, str]]:
    source = (REPO_ROOT / "sharelife" / "interfaces" / "webui_server.py").read_text(encoding="utf-8")
    match = re.search(
        r"def _anonymous_member_default_api_paths\(\) -> set\[tuple\[str, str\]\]:\n\s+return \{(?P<body>.*?)\n\s+\}",
        source,
        re.DOTALL,
    )
    assert match is not None
    body = match.group("body")
    entries = {
        (str(method).strip().upper(), str(path).strip())
        for method, path in re.findall(r'\("([A-Z]+)",\s*"([^"]+)"\)', body)
    }
    assert entries
    return sorted(entries)


def _assert_doc_route_line_with_role(doc_text: str, *, method: str, path: str, role_token: str) -> None:
    marker = f"`{method} {path}`"
    matched_lines = [line for line in doc_text.splitlines() if marker in line]
    assert matched_lines, f"missing auth-matrix row for {method} {path}"
    assert any(role_token in line for line in matched_lines), (
        f"missing anonymous role token for {method} {path}"
    )


def test_api_reference_docs_cover_anonymous_member_default_allowlist_routes():
    entries = _anonymous_member_allowlist_entries()
    locale_tokens = {
        "en": "anonymous allowlist",
        "zh": "匿名白名单",
        "ja": "anonymous allowlist",
    }
    for locale, role_token in locale_tokens.items():
        doc_text = (REPO_ROOT / "docs" / locale / "reference" / "api-v1.md").read_text(
            encoding="utf-8"
        )
        for method, path in entries:
            _assert_doc_route_line_with_role(
                doc_text,
                method=method,
                path=path,
                role_token=role_token,
            )
