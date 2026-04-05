"""Scan service for risk and compatibility reports."""

from __future__ import annotations

from dataclasses import asdict
import re
from typing import Any

from ..domain.models import TemplateManifest
from ..domain.policies import (
    RiskEvidence,
    ScanReport,
    classify_levels,
    detect_prompt_injection,
    line_column_for_offset,
    resolve_compatibility,
)


class ScanService:
    def scan(
        self,
        payload: dict[str, Any],
        manifest: TemplateManifest | None = None,
    ) -> ScanReport:
        levels = sorted(classify_levels(payload))
        compatibility = resolve_compatibility(manifest)
        prompt_text = self._prompt_text(payload)
        scan_sources = self._scan_sources(payload, prompt_text)
        injection = detect_prompt_injection(prompt_text, sources=scan_sources)
        supply_chain_flags, supply_chain_high, supply_chain_evidence = self._supply_chain_flags(
            prompt_text,
            scan_sources,
        )
        risk_level = self._risk_level(
            levels,
            compatibility,
            injection.detected,
            supply_chain_high=supply_chain_high,
            supply_chain_flags=supply_chain_flags,
        )
        review_labels = self._review_labels(
            levels,
            compatibility,
            risk_level,
            injection.detected,
            supply_chain_flags=supply_chain_flags,
        )
        warning_flags = list(injection.matched_rules) + list(supply_chain_flags)
        risk_evidence = self._unique_risk_evidence(
            [*injection.matched_locations, *supply_chain_evidence]
        )
        return ScanReport(
            levels=levels,
            compatibility=compatibility,
            risk_level=risk_level,
            review_labels=review_labels,
            warning_flags=warning_flags,
            prompt_injection=injection,
            risk_evidence=risk_evidence,
        )

    @staticmethod
    def to_dict(report: ScanReport) -> dict[str, Any]:
        payload = asdict(report)
        payload["review_labels"] = sorted(set(payload["review_labels"]))
        payload["warning_flags"] = sorted(set(payload["warning_flags"]))
        return payload

    @staticmethod
    def _prompt_text(payload: dict[str, Any]) -> str:
        parts: list[str] = []
        for key in ("prompt", "prompt_template", "raw_text"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                parts.append(value.strip())
        files = payload.get("files")
        if isinstance(files, list):
            parts.extend(str(item) for item in files[:20])
        return "\n".join(parts)

    @staticmethod
    def _scan_sources(payload: dict[str, Any], prompt_text: str) -> list[dict[str, str]]:
        sources: list[dict[str, str]] = []
        raw_sources = payload.get("scan_sources")
        if isinstance(raw_sources, list):
            for index, item in enumerate(raw_sources[:200]):
                if not isinstance(item, dict):
                    continue
                snippet = str(item.get("text", "") or "").strip()
                if not snippet:
                    continue
                filename = str(item.get("file", "") or "").strip() or f"payload_source_{index + 1}"
                path = str(item.get("path", "") or "").strip() or "$"
                sources.append({"file": filename, "path": path, "text": snippet[:6000]})
        if sources:
            return sources
        fallback = str(prompt_text or "").strip()
        if not fallback:
            return []
        filename = str(payload.get("filename", "") or "").strip() or "payload"
        return [{"file": filename, "path": "$", "text": fallback[:6000]}]

    @staticmethod
    def _risk_level(
        levels: list[str],
        compatibility: str,
        injection_detected: bool,
        *,
        supply_chain_high: bool,
        supply_chain_flags: list[str],
    ) -> str:
        if injection_detected or "L3" in levels or supply_chain_high:
            return "high"
        if "L2" in levels or compatibility != "compatible" or supply_chain_flags:
            return "medium"
        return "low"

    @staticmethod
    def _review_labels(
        levels: list[str],
        compatibility: str,
        risk_level: str,
        injection_detected: bool,
        *,
        supply_chain_flags: list[str],
    ) -> list[str]:
        labels = [f"risk_{risk_level}"]
        if "L3" in levels:
            labels.append("provider_override")
        if "L2" in levels:
            labels.append("agent_orchestration")
        if compatibility != "compatible":
            labels.append("compatibility_review_needed")
        if injection_detected:
            labels.append("prompt_injection_detected")
        if supply_chain_flags:
            labels.append("supply_chain_review_needed")
        if any(
            flag in {"insecure_http_source", "shell_pipe_download", "unpinned_remote_install"}
            for flag in supply_chain_flags
        ):
            labels.append("supply_chain_high_risk")
        return labels

    @staticmethod
    def _supply_chain_flags(
        text: str,
        scan_sources: list[dict[str, str]],
    ) -> tuple[list[str], bool, list[RiskEvidence]]:
        flags: list[str] = []
        evidences: list[RiskEvidence] = []
        normalized = str(text or "")
        patterns: tuple[tuple[str, str, str, bool], ...] = (
            ("insecure_http_source", r"http://[^\s\"']+", "high", True),
            ("shell_pipe_download", r"(curl|wget).{0,48}\|\s*(sh|bash)", "high", True),
            ("unpinned_remote_install", r"\b(pip|npm|pnpm|uv)\s+install\b.{0,80}(git\+|https?://)", "high", True),
            ("floating_git_ref", r"github\.com/[^\s\"']+/(main|master|head)\b", "medium", False),
        )
        high = False
        sources = scan_sources or [{"file": "payload", "path": "$", "text": normalized}]
        for name, pattern, severity, is_high in patterns:
            rule_matched = False
            for source in sources:
                source_text = str(source.get("text", "") or "")
                if not source_text:
                    continue
                for match in re.finditer(pattern, source_text, flags=re.IGNORECASE | re.DOTALL):
                    if not rule_matched:
                        flags.append(name)
                        rule_matched = True
                        if is_high:
                            high = True
                    line, column = line_column_for_offset(source_text, match.start())
                    evidences.append(
                        RiskEvidence(
                            category="supply_chain",
                            rule=name,
                            severity=severity,
                            file=str(source.get("file", "") or "payload"),
                            path=str(source.get("path", "") or "$"),
                            line=line,
                            column=column,
                            phrase=match.group(0).strip()[:120],
                        )
                    )
                    if len(evidences) >= 60:
                        break
                if len(evidences) >= 60:
                    break
            if len(evidences) >= 60:
                break
        return flags, high, evidences

    @staticmethod
    def _unique_risk_evidence(items: list[RiskEvidence]) -> list[RiskEvidence]:
        seen: set[tuple[str, str, str, str, int, int, str]] = set()
        out: list[RiskEvidence] = []
        for item in items:
            key = (
                item.category,
                item.rule,
                item.file,
                item.path,
                int(item.line),
                int(item.column),
                item.phrase,
            )
            if key in seen:
                continue
            seen.add(key)
            out.append(item)
        return out
