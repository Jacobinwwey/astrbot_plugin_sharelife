#!/usr/bin/env python3
"""Build a member-safe WebUI artifact without privileged admin/reviewer sections."""

from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = REPO_ROOT / "sharelife" / "webui" / "member.html"
TARGET_PATH = REPO_ROOT / "sharelife" / "webui" / "member.safe.html"

SECTION_IDS_TO_REMOVE = (
    "section-admin-apply",
    "section-continuity",
    "section-profile-pack",
    "section-admin-submissions",
    "submissionWorkspaceSection",
    "section-retry-queue",
    "section-reliability",
    "section-storage-backup",
    "section-risk-glossary",
    "section-actor-context",
    "section-preferences",
)


def _strip_section_by_id(html: str, section_id: str) -> str:
    pattern = re.compile(
        rf"<section\b(?=[^>]*\bid=\"{re.escape(section_id)}\")[^>]*>.*?</section>",
        re.IGNORECASE | re.DOTALL,
    )
    return pattern.sub("", html)


def _strip_sections_by_pattern(html: str, pattern: re.Pattern[str]) -> str:
    return pattern.sub("", html)


def build_member_safe_html(source: str) -> str:
    html = source
    for section_id in SECTION_IDS_TO_REMOVE:
        html = _strip_section_by_id(html, section_id)
    html = _strip_sections_by_pattern(
        html,
        re.compile(
            r"<section\b[^>]*\bdata-console-scope=\"admin\"[^>]*>.*?</section>",
            re.IGNORECASE | re.DOTALL,
        ),
    )
    html = _strip_sections_by_pattern(
        html,
        re.compile(
            r"<section\b[^>]*\bclass=\"[^\"]*developer-only-card[^\"]*\"[^>]*>.*?</section>",
            re.IGNORECASE | re.DOTALL,
        ),
    )
    return html


def main() -> int:
    source = SOURCE_PATH.read_text(encoding="utf-8")
    safe_html = build_member_safe_html(source)
    TARGET_PATH.write_text(safe_html, encoding="utf-8")
    print(f"[member-safe] generated: {TARGET_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
