"""Bootstrap bundled official profile-pack examples into the profile-pack catalog."""

from __future__ import annotations

from typing import Any

from ..official_profile_pack_examples import official_profile_pack_examples
from .services_profile_pack import ProfilePackService


class ProfilePackBootstrapService:
    def __init__(self, profile_pack_service: ProfilePackService):
        self.profile_pack_service = profile_pack_service

    def sync(self) -> dict[str, int]:
        seeded = 0
        skipped = 0

        for item in self._official_examples():
            pack_id = str(item.get("pack_id", "") or "").strip()
            version = str(item.get("version", "") or "").strip()
            if not pack_id or not version:
                skipped += 1
                continue

            existing = self.profile_pack_service.get_published_pack(pack_id=pack_id)
            if existing is not None:
                source_submission_id = str(existing.source_submission_id or "")
                if not source_submission_id.startswith("official:"):
                    skipped += 1
                    continue
                if not self._official_pack_requires_refresh(existing=existing, expected_version=version):
                    skipped += 1
                    continue

            self.profile_pack_service.publish_official_pack(
                pack_id=pack_id,
                version=version,
                pack_type=str(item.get("pack_type", "bot_profile_pack") or "bot_profile_pack"),
                sections=dict(item.get("sections", {}) or {}),
                review_note=str(
                    item.get("review_note", "Bundled official profile-pack baseline.")
                    or "Bundled official profile-pack baseline."
                ),
                reviewer_id="official:sharelife",
                featured=bool(item.get("featured", True)),
                featured_note=str(item.get("featured_note", "Official reference profile-pack.") or ""),
            )
            seeded += 1

        return {"seeded": seeded, "skipped": skipped}

    @staticmethod
    def _official_pack_requires_refresh(
        *,
        existing,
        expected_version: str,
    ) -> bool:
        if str(existing.version or "").strip() != str(expected_version or "").strip():
            return True
        risk_level = str(getattr(existing, "risk_level", "") or "").strip().lower()
        if risk_level != "low":
            return True
        review_labels = {
            str(item or "").strip().lower()
            for item in (getattr(existing, "review_labels", []) or [])
            if str(item or "").strip()
        }
        if "official_profile_pack" not in review_labels:
            return True
        if "risk_low" not in review_labels:
            return True
        return False

    @staticmethod
    def _official_examples() -> list[dict[str, Any]]:
        return official_profile_pack_examples()
