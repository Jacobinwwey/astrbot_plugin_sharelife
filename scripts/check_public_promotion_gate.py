#!/usr/bin/env python3
from __future__ import annotations

import argparse
import fnmatch
import json
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath


REPO_ROOT = Path(__file__).resolve().parents[1]
ALLOW_MARKERS = ("promotion:allow", "privacy:allow", "privacy-allow", "privacy_ok")

PATH_RULES: tuple[tuple[str, str], ...] = (
    ("private_docs_root", "docs/private/**"),
    ("private_docs_locales", "docs/*/private/**"),
    ("private_docs_workspace", "docs-private/**"),
    ("local_secret_store", "output/standalone-data/secrets/**"),
    ("local_toml_secret", "**/*.local.toml"),
    ("private_key_file", "**/*.pem"),
    ("private_key_file", "**/*.key"),
    ("private_key_file", "**/*.p12"),
    ("ssh_private_key_file", "**/id_rsa"),
)

CONTENT_RULES: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("private_key_block", re.compile(r"-----BEGIN [A-Z ]+PRIVATE KEY-----")),
    ("openai_key", re.compile(r"\bsk-[A-Za-z0-9]{20,}\b")),
    ("github_token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b")),
    ("google_api_key", re.compile(r"\bAIza[0-9A-Za-z_-]{20,}\b")),
    ("bearer_header", re.compile(r"\bAuthorization\s*:\s*Bearer\s+\S{10,}\b", re.IGNORECASE)),
    (
        "inline_auth_secret",
        re.compile(r"\b(?:admin_password|reviewer_password|passphrase)\s*[:=]\s*['\"]?[^'\"#\s]{4,}", re.IGNORECASE),
    ),
    (
        "query_secret",
        re.compile(r"[?&](?:token|access_token|api_key|apikey|password)=[^&\s]+", re.IGNORECASE),
    ),
)

HUNK_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")


class GateError(RuntimeError):
    pass


def _run_git(args: list[str]) -> str:
    completed = subprocess.run(
        ["git", "-C", str(REPO_ROOT), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise GateError(f"git {' '.join(args)} failed: {completed.stderr.strip()}")
    return completed.stdout


def resolve_diff_mode(from_ref: str, to_ref: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "merge-base", from_ref, to_ref],
        capture_output=True,
        text=True,
        check=False,
    )
    return "merge-base" if completed.returncode == 0 else "direct"


def _build_diff_args(
    from_ref: str,
    to_ref: str,
    *,
    mode: str,
    name_only: bool = False,
    unified_zero: bool = False,
    path: str | None = None,
) -> list[str]:
    args: list[str] = ["diff"]
    if name_only:
        args.extend(["--name-only", "--diff-filter=ACMR"])
    if unified_zero:
        args.extend(["--unified=0", "--no-color"])
    if mode == "merge-base":
        args.append(f"{from_ref}...{to_ref}")
    else:
        args.extend([from_ref, to_ref])
    if path is not None:
        args.extend(["--", path])
    return args


def _path_matches(path: str, pattern: str) -> bool:
    normalized = path.replace("\\", "/")
    pure = PurePosixPath(normalized)
    return pure.match(pattern) or fnmatch.fnmatch(normalized, pattern)


def list_changed_paths(from_ref: str, to_ref: str, *, mode: str) -> list[str]:
    output = _run_git(_build_diff_args(from_ref, to_ref, mode=mode, name_only=True))
    return [line.strip().replace("\\", "/") for line in output.splitlines() if line.strip()]


def collect_added_lines(from_ref: str, to_ref: str, path: str, *, mode: str) -> list[tuple[int, str]]:
    output = _run_git(
        _build_diff_args(from_ref, to_ref, mode=mode, unified_zero=True, path=path)
    )
    added: list[tuple[int, str]] = []
    new_line = 0
    for line in output.splitlines():
        hunk = HUNK_RE.match(line)
        if hunk:
            new_line = int(hunk.group(1))
            continue
        if line.startswith("+++") or line.startswith("---"):
            continue
        if line.startswith("+"):
            added.append((new_line, line[1:]))
            new_line += 1
            continue
        if line.startswith("-"):
            continue
        if line.startswith("\\ No newline"):
            continue
    return added


def _is_allowed_line(line: str, token: str, rule: str) -> bool:
    lowered = line.lower()
    if any(marker in lowered for marker in ALLOW_MARKERS):
        return True
    if "<redacted>" in lowered or "[redacted]" in lowered or "***" in token:
        return True
    if rule in {"openai_key", "github_token", "google_api_key"} and "placeholder" in lowered:
        return True
    return False


def evaluate_change_set(
    changed_paths: list[str],
    added_lines_by_path: dict[str, list[tuple[int, str]]],
) -> dict[str, object]:
    blocked_paths: list[dict[str, str]] = []
    blocked_content: list[dict[str, object]] = []

    for path in changed_paths:
        for rule, pattern in PATH_RULES:
            if _path_matches(path, pattern):
                blocked_paths.append({"path": path, "rule": rule, "pattern": pattern})
                break

    for path, rows in added_lines_by_path.items():
        for line_no, line in rows:
            for rule, pattern in CONTENT_RULES:
                for match in pattern.finditer(line):
                    token = match.group(0)
                    if _is_allowed_line(line, token, rule):
                        continue
                    blocked_content.append(
                        {
                            "path": path,
                            "line_no": line_no,
                            "rule": rule,
                            "snippet": line.strip()[:200],
                        }
                    )

    promotable = not blocked_paths and not blocked_content
    return {
        "promotable": promotable,
        "changed_files_count": len(changed_paths),
        "blocked_paths": blocked_paths,
        "blocked_content": blocked_content,
    }


def build_report(from_ref: str, to_ref: str) -> dict[str, object]:
    mode = resolve_diff_mode(from_ref, to_ref)
    changed_paths = list_changed_paths(from_ref, to_ref, mode=mode)
    added_lines_by_path = {
        path: collect_added_lines(from_ref, to_ref, path, mode=mode) for path in changed_paths
    }
    result = evaluate_change_set(changed_paths, added_lines_by_path)
    return {
        "from_ref": from_ref,
        "to_ref": to_ref,
        "comparison_mode": mode,
        "status": "PASS" if result["promotable"] else "BLOCK",
        **result,
    }


def _print_summary(report: dict[str, object]) -> None:
    status = report["status"]
    print(
        f"[promotion-gate] {status} ({report['comparison_mode']}): changed={report['changed_files_count']}, "
        f"blocked_paths={len(report['blocked_paths'])}, blocked_content={len(report['blocked_content'])}"
    )
    if report["blocked_paths"]:
        print("[promotion-gate] blocked paths:")
        for item in report["blocked_paths"][:50]:
            print(f"  - {item['path']} ({item['rule']}:{item['pattern']})")
    if report["blocked_content"]:
        print("[promotion-gate] blocked content:")
        for item in report["blocked_content"][:50]:
            print(f"  - {item['path']}:{item['line_no']} [{item['rule']}] {item['snippet']}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Gate private->public promotion by scanning changed paths and added content "
            "for private docs and likely sensitive secrets."
        )
    )
    parser.add_argument("--from-ref", default="origin/main", help="Baseline ref (default: origin/main)")
    parser.add_argument("--to-ref", default="HEAD", help="Target ref to evaluate (default: HEAD)")
    parser.add_argument("--json-output", default="", help="Optional JSON report output path")
    args = parser.parse_args(argv)

    try:
        report = build_report(args.from_ref, args.to_ref)
    except GateError as exc:
        print(f"[promotion-gate] error: {exc}", file=sys.stderr)
        return 3

    _print_summary(report)
    if args.json_output:
        output_path = Path(args.json_output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"[promotion-gate] wrote report: {output_path}")

    return 0 if report["promotable"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
