#!/usr/bin/env python3
"""Validate frozen Sharelife protocol schemas and bundled examples."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sharelife.application.services_protocol_contracts import ProtocolContractService


def main() -> int:
    validator = ProtocolContractService()
    validator.validate_example_files()
    print("protocol examples are valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
