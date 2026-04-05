#!/usr/bin/env python3
"""Redact sensitive tokens/paths from ops-smoke diagnostic artifacts."""

from __future__ import annotations

import argparse
import os
import re
from pathlib import Path


_URL_CREDENTIAL_RE = re.compile(r"([a-zA-Z][a-zA-Z0-9+\-.]*://)([^/\s:@]+):([^/@\s]+)@")
_BEARER_RE = re.compile(r"(?i)\b(Bearer)\s+([A-Za-z0-9._~+/=-]+)")
_AUTH_HEADER_RE = re.compile(r"(?im)^(\s*Authorization\s*:\s*)(.+)$")
_QUERY_SECRET_RE = re.compile(r"(?i)([?&](?:token|api[_-]?key|password|secret)=)([^&\s]+)")
_KV_SECRET_RE = re.compile(
    r"(?im)(\b(?:api[_-]?key|token|password|pass|secret|signing[_-]?key|encryption[_-]?key)\b\s*[:=]\s*)([^\s,;\"']+)"
)
_JSON_SECRET_RE = re.compile(
    r'(?i)("(?:api[_-]?key|token|password|pass|secret|signing[_-]?key|encryption[_-]?key)"\s*:\s*")([^"]*)(")'
)
_IP_RE = re.compile(r"\b((?:\d{1,3}\.){3}\d{1,3})\b")
_HOME_PATH_RE = re.compile(r"(?<![A-Za-z0-9_.-])(?:/root|/home/[^/\s]+)(?:/[^\s:]*)?")


def _is_non_loopback_ipv4(ip: str) -> bool:
    parts = ip.split(".")
    if len(parts) != 4:
        return False
    try:
        octets = [int(item) for item in parts]
    except ValueError:
        return False
    if any(item < 0 or item > 255 for item in octets):
        return False
    if ip.startswith("127."):
        return False
    if ip.startswith("0."):
        return False
    return True


def redact_text(text: str, *, redact_non_loopback_ips: bool = True, redact_home_paths: bool = True) -> str:
    out = text
    out = _URL_CREDENTIAL_RE.sub(r"\1<redacted-user>:<redacted-password>@", out)
    out = _BEARER_RE.sub(r"\1 <redacted-token>", out)
    out = _AUTH_HEADER_RE.sub(r"\1<redacted-auth>", out)
    out = _QUERY_SECRET_RE.sub(r"\1<redacted>", out)
    out = _KV_SECRET_RE.sub(r"\1<redacted>", out)
    out = _JSON_SECRET_RE.sub(r'\1<redacted>\3', out)

    if redact_non_loopback_ips:
        out = _IP_RE.sub(lambda m: "<redacted-ip>" if _is_non_loopback_ipv4(m.group(1)) else m.group(1), out)
    if redact_home_paths:
        out = _HOME_PATH_RE.sub("<redacted-home-path>", out)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Redact sensitive values from ops smoke artifact text files.")
    parser.add_argument("--input", required=True, help="Input text file path.")
    parser.add_argument("--output", default="", help="Output text file path (defaults to --input path).")
    parser.add_argument(
        "--mode",
        choices=("strict", "off"),
        default=os.environ.get("SHARELIFE_SMOKE_PRIVACY_MODE", "strict"),
        help="Redaction mode: strict (default) or off.",
    )
    parser.add_argument(
        "--keep-home-paths",
        action="store_true",
        help="Do not redact absolute home paths (/root, /home/*).",
    )
    parser.add_argument(
        "--keep-non-loopback-ips",
        action="store_true",
        help="Do not redact non-loopback IPv4 addresses.",
    )
    args = parser.parse_args()

    input_path = Path(args.input).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve() if args.output else input_path

    text = input_path.read_text(encoding="utf-8")
    if args.mode == "off":
        output_path.write_text(text, encoding="utf-8")
        return 0

    redacted = redact_text(
        text,
        redact_non_loopback_ips=not args.keep_non_loopback_ips,
        redact_home_paths=not args.keep_home_paths,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(redacted, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
