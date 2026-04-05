"""Profile section adapter registry for bot_profile_pack capture/apply."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from ..domain.profile_pack_models import PROFILE_ALLOWED_SECTIONS


@dataclass(slots=True)
class ProfileSectionAdapter:
    section_name: str
    state_key: str
    default_value: dict[str, Any] | list[Any] | str | int | float | bool | None = None

    def capture(self, snapshot: dict[str, Any]) -> Any:
        value = snapshot.get(self.state_key, self.default_value)
        return deepcopy(value)

    def to_patch(self, payload: Any) -> dict[str, Any]:
        return {self.state_key: deepcopy(payload)}


class ProfileSectionAdapterRegistry:
    def __init__(self, adapters: list[ProfileSectionAdapter]):
        self._adapters: dict[str, ProfileSectionAdapter] = {}
        for adapter in adapters:
            self._adapters[adapter.section_name] = adapter

    @classmethod
    def default_registry(cls) -> "ProfileSectionAdapterRegistry":
        adapters = [
            ProfileSectionAdapter(section_name="astrbot_core", state_key="astrbot_core", default_value={}),
            ProfileSectionAdapter(section_name="providers", state_key="providers", default_value={}),
            ProfileSectionAdapter(section_name="plugins", state_key="plugins", default_value={}),
            ProfileSectionAdapter(section_name="skills", state_key="skills", default_value={}),
            ProfileSectionAdapter(section_name="personas", state_key="personas", default_value={}),
            ProfileSectionAdapter(section_name="mcp_servers", state_key="mcp_servers", default_value={}),
            ProfileSectionAdapter(section_name="sharelife_meta", state_key="sharelife_meta", default_value={}),
            ProfileSectionAdapter(section_name="memory_store", state_key="memory_store", default_value={}),
            ProfileSectionAdapter(
                section_name="conversation_history",
                state_key="conversation_history",
                default_value=[],
            ),
            ProfileSectionAdapter(section_name="knowledge_base", state_key="knowledge_base", default_value={}),
            ProfileSectionAdapter(
                section_name="environment_manifest",
                state_key="environment_manifest",
                default_value={},
            ),
        ]
        return cls(adapters=adapters)

    def allowed_sections(self) -> list[str]:
        return [section for section in PROFILE_ALLOWED_SECTIONS if section in self._adapters]

    def normalize_sections(self, selected_sections: list[str] | None = None) -> list[str]:
        if selected_sections is None:
            return self.allowed_sections()

        out: list[str] = []
        seen: set[str] = set()
        for section in selected_sections:
            item = str(section or "").strip()
            if not item:
                continue
            if item not in self._adapters:
                raise ValueError("PROFILE_SECTION_NOT_ALLOWED")
            if item in seen:
                continue
            seen.add(item)
            out.append(item)
        if not out:
            raise ValueError("PROFILE_SECTION_SELECTION_EMPTY")
        return out

    def capture(self, snapshot: dict[str, Any], selected_sections: list[str] | None = None) -> dict[str, Any]:
        sections = self.normalize_sections(selected_sections)
        out: dict[str, Any] = {}
        for section in sections:
            out[section] = self._adapters[section].capture(snapshot)
        return out

    def build_patch(
        self,
        sections_payload: dict[str, Any],
        selected_sections: list[str] | None = None,
    ) -> dict[str, Any]:
        sections = self.normalize_sections(selected_sections or list(sections_payload.keys()))
        patch: dict[str, Any] = {}
        for section in sections:
            if section not in sections_payload:
                raise ValueError("PROFILE_SECTION_PAYLOAD_MISSING")
            patch.update(self._adapters[section].to_patch(sections_payload[section]))
        return patch
