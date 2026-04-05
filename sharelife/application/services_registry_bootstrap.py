"""Bootstrap bundled official template registry into the market."""

from __future__ import annotations

from typing import Any

from ..domain.models import TemplateManifest
from .services_market import MarketService
from .services_registry import RegistryService
from .services_scan import ScanService


class RegistryBootstrapService:
    def __init__(
        self,
        registry_service: RegistryService,
        market_service: MarketService,
        scan_service: ScanService | None = None,
    ):
        self.registry_service = registry_service
        self.market_service = market_service
        self.scan_service = scan_service or ScanService()

    def sync(self) -> dict[str, int]:
        payload = self.registry_service.refresh_or_load()
        seeded = 0
        skipped = 0

        for item in payload.get("templates", []):
            manifest = TemplateManifest.model_validate(item)
            existing = self.market_service.get_published_template(manifest.template_id)
            if existing is not None and not str(existing.source_submission_id).startswith("official:"):
                skipped += 1
                continue

            summary = self._scan_summary(manifest)
            review_labels = sorted(
                set(["official_template", *manifest.review_labels, *summary.get("review_labels", [])])
            )
            warning_flags = sorted(
                set([*manifest.warning_flags, *summary.get("warning_flags", [])])
            )
            risk_level = str(manifest.risk_level or summary.get("risk_level") or "low")

            self.market_service.publish_official_template(
                template_id=manifest.template_id,
                version=manifest.version,
                prompt_template=manifest.prompt_template or self._default_prompt(manifest),
                review_note="Bundled official template baseline.",
                scan_summary=summary,
                review_labels=review_labels,
                warning_flags=warning_flags,
                risk_level=risk_level,
                category=manifest.category,
                tags=list(manifest.tags or []),
                maintainer=manifest.maintainer or "Sharelife",
                source_channel=manifest.source_channel or "bundled_official",
            )
            seeded += 1

        return {"seeded": seeded, "skipped": skipped}

    def _scan_summary(self, manifest: TemplateManifest) -> dict[str, Any]:
        if manifest.scan_summary:
            return dict(manifest.scan_summary)

        report = self.scan_service.scan(
            {
                "template_id": manifest.template_id,
                "version": manifest.version,
                "prompt": manifest.prompt_template,
                "prompt_template": manifest.prompt_template,
                "astrbot_version": manifest.astrbot_version,
            }
        )
        return self.scan_service.to_dict(report)

    @staticmethod
    def _default_prompt(manifest: TemplateManifest) -> str:
        return (
            "You are running Sharelife official template "
            f"{manifest.template_id} (version {manifest.version}). "
            "Follow strict-mode safety boundaries and avoid privilege escalation."
        )
