"""Official registry source adapter."""

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import unquote, urlparse

import httpx


class OfficialRegistrySource:
    def __init__(self, index_url: str, timeout: float = 10.0):
        self.index_url = index_url
        self.timeout = timeout

    def fetch_index(self) -> dict:
        parsed = urlparse(self.index_url)
        if parsed.scheme in {"http", "https"}:
            response = httpx.get(self.index_url, timeout=self.timeout)
            response.raise_for_status()
            return response.json()

        if parsed.scheme == "file":
            path = Path(unquote(parsed.path))
        else:
            path = Path(self.index_url)

        return json.loads(path.read_text(encoding="utf-8"))
