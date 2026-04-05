"""Dependency-light official profile-pack examples shared by runtime and docs build."""

from __future__ import annotations

import copy
from typing import Any


def official_profile_pack_examples() -> list[dict[str, Any]]:
    starter_sections = {
        "astrbot_core": {
            "name": "sharelife-official-starter",
            "language": "en-US",
            "execution_mode": "subagent_driven",
        },
        "providers": {
            "openai": {
                "base_url": "https://api.openai.com/v1",
                "model": "gpt-4.1-mini",
                "api_key": "<REDACTED>",
            }
        },
        "plugins": {
            "sharelife": {
                "enabled": True,
                "observe_task_details": True,
            }
        },
        "skills": {
            "translator": {
                "enabled": True,
            },
            "writer": {
                "enabled": True,
            },
        },
        "personas": {
            "default": {
                "tone": "helpful",
                "style": "concise",
            }
        },
        "mcp_servers": {
            "filesystem": {
                "endpoint": "https://mcp.example.invalid/filesystem",
            }
        },
        "sharelife_meta": {
            "owner": "official",
            "notes": "Starter reference pack shipped with Sharelife.",
        },
    }
    return copy.deepcopy(
        [
            {
                "pack_type": "bot_profile_pack",
                "pack_id": "profile/official-starter",
                "version": "1.0.1",
                "created_at": "2026-04-05T00:00:00+00:00",
                "published_at": "2026-04-05T00:00:00+00:00",
                "featured": True,
                "featured_note": "Official starter profile for first-time import/dry-run/apply walkthrough.",
                "review_note": "Bundled official profile-pack baseline for market reference.",
                "sections": starter_sections,
            },
            {
                "pack_type": "bot_profile_pack",
                "pack_id": "profile/official-safe-reference",
                "version": "1.0.1",
                "created_at": "2026-04-05T00:00:00+00:00",
                "published_at": "2026-04-05T00:00:00+00:00",
                "featured": True,
                "featured_note": "Official safety-first reference profile for review and compare workflows.",
                "review_note": "Bundled official profile-pack baseline for safety-first market reference.",
                "sections": {
                    **starter_sections,
                    "astrbot_core": {
                        **dict(starter_sections.get("astrbot_core", {}) or {}),
                        "name": "sharelife-official-safe-reference",
                    },
                    "personas": {
                        "default": {
                            "tone": "calm",
                            "style": "risk-aware",
                        }
                    },
                    "sharelife_meta": {
                        "owner": "official",
                        "notes": "Safety-first reference pack shipped with Sharelife.",
                    },
                },
            },
        ]
    )
