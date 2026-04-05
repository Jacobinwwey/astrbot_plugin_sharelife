#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCAN_ROOT = REPO_ROOT / "docs" / "superpowers"

PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("aws_access_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("google_api_key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    ("github_token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b")),
    ("openai_key", re.compile(r"\bsk-[A-Za-z0-9]{20,}\b")),
    ("bearer_token", re.compile(r"\bBearer\s+[A-Za-z0-9._-]{20,}\b")),
    ("private_key_block", re.compile(r"-----BEGIN [A-Z ]+PRIVATE KEY-----")),
    ("absolute_root_path", re.compile(r"(?<!\w)/(?:root|home|Users)/[^\s`\"'<>]+")),
    ("windows_user_path", re.compile(r"\b[A-Za-z]:\\Users\\[^\s`\"'<>]+")),
    ("suspicious_query_token", re.compile(r"[?&](?:token|access_token|api_key|apikey|password)=[^&\s]+")),
    ("inline_email", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")),
)

SAFE_EMAIL_DOMAINS = ("example.com", "example.org", "example.net", "test.local")
ALLOW_MARKERS = ("privacy:allow", "privacy-allow", "privacy_ok")


def _iter_markdown_files(scan_root: Path) -> list[Path]:
    return sorted(path for path in scan_root.rglob("*.md") if path.is_file())


def _is_allowed_match(line: str, token: str, kind: str) -> bool:
    lowered = line.lower()
    if any(marker in lowered for marker in ALLOW_MARKERS):
        return True
    if "***" in token or "<redacted>" in lowered or "[redacted]" in lowered:
        return True
    if kind == "inline_email":
        domain = token.split("@", 1)[1].lower()
        if domain.endswith(SAFE_EMAIL_DOMAINS):
            return True
    return False


def _scan_file(path: Path) -> list[str]:
    findings: list[str] = []
    text = path.read_text(encoding="utf-8")
    for line_no, line in enumerate(text.splitlines(), start=1):
        for kind, pattern in PATTERNS:
            for match in pattern.finditer(line):
                token = match.group(0)
                if _is_allowed_match(line, token, kind):
                    continue
                snippet = line.strip()
                findings.append(f"{path}:{line_no}: [{kind}] {snippet}")
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Scan docs/superpowers markdown files for likely private tokens, "
            "local absolute paths, and leaked credentials."
        )
    )
    parser.add_argument(
        "--scan-root",
        default=str(DEFAULT_SCAN_ROOT),
        help="Root directory to scan (default: docs/superpowers).",
    )
    args = parser.parse_args(argv)

    scan_root = Path(args.scan_root).resolve()
    if not scan_root.exists():
        print(f"[privacy-check] scan root not found: {scan_root}", file=sys.stderr)
        return 2

    files = _iter_markdown_files(scan_root)
    findings: list[str] = []
    for path in files:
        findings.extend(_scan_file(path))

    if findings:
        print("[privacy-check] potential sensitive content detected:")
        for finding in findings:
            print(f"  - {finding}")
        print(
            "\n[privacy-check] block pushed changes until sensitive fragments are removed "
            "or explicitly marked with `privacy:allow`."
        )
        return 1

    print(f"[privacy-check] passed: scanned {len(files)} markdown file(s) under {scan_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
