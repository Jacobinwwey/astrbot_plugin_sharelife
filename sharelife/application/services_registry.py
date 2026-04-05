"""Registry service for template index refresh and fallback."""

from __future__ import annotations

from typing import Any

from ..infrastructure.local_store import LocalStore


class RegistryService:
    def __init__(self, source: Any, store: LocalStore):
        self.source = source
        self.store = store

    def refresh_or_load(self) -> dict[str, Any]:
        try:
            latest = self.source.fetch_index()
            self.store.save_json("registry/index.json", latest)
            return latest
        except Exception:
            return self.store.load_json("registry/index.json", {"templates": []})
