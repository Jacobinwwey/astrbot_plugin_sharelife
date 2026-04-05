#!/usr/bin/env python3
"""Emit GitHub Actions annotations from ops-smoke triage JSON."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish GitHub annotations from ops-smoke triage.json")
    parser.add_argument("--triage-json", required=True, help="Path to triage.json")
    args = parser.parse_args()

    triage_path = Path(args.triage_json).expanduser().resolve()
    payload = _read_json(triage_path)
    if not payload:
        print(f"::warning title=ops-smoke::triage json missing or invalid: {triage_path}")
        return 0

    result = str(payload.get("result", "FAIL")).strip().upper()
    exit_code = payload.get("exit_code", 1)
    last_step = str(payload.get("last_step", "-")).strip()
    signals = payload.get("signals", [])
    actions = payload.get("actions", [])

    if result == "PASS":
        print(f"::notice title=ops-smoke::PASS exit_code={exit_code} last_step={last_step}")
        return 0

    print(f"::error title=ops-smoke::FAIL exit_code={exit_code} last_step={last_step}")

    if isinstance(signals, list):
        for signal in signals:
            if not isinstance(signal, dict):
                continue
            ok = bool(signal.get("ok", False))
            if ok:
                continue
            key = str(signal.get("key", "unknown")).strip() or "unknown"
            label = str(signal.get("label", key)).strip() or key
            print(f"::error title=ops-smoke-signal::{label} failed (key={key})")

    if isinstance(actions, list):
        for idx, action in enumerate(actions, start=1):
            text = str(action).strip()
            if not text:
                continue
            print(f"::warning title=ops-smoke-action::{idx}. {text}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
