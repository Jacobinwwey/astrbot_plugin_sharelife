"""Policy helpers for risk and compatibility evaluation."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any

from .models import TemplateManifest


@dataclass(slots=True)
class RiskEvidence:
    category: str
    rule: str
    severity: str
    file: str
    path: str
    line: int
    column: int
    phrase: str


@dataclass(slots=True)
class PromptInjectionReport:
    detected: bool
    severity: str
    matched_rules: list[str]
    matched_phrases: list[str]
    matched_locations: list[RiskEvidence]


@dataclass(slots=True)
class ScanReport:
    levels: list[str]
    compatibility: str
    risk_level: str
    review_labels: list[str]
    warning_flags: list[str]
    prompt_injection: PromptInjectionReport
    risk_evidence: list[RiskEvidence]


def classify_levels(payload: dict[str, Any]) -> set[str]:
    levels: set[str] = set()

    if "provider_settings" in payload or "command_permission" in payload:
        levels.add("L3")
    if "subagent_orchestrator" in payload or "agent" in payload:
        levels.add("L2")
    if not levels:
        levels.add("L1")

    return levels


def resolve_compatibility(manifest: TemplateManifest | None) -> str:
    if manifest and manifest.astrbot_version:
        return "compatible"
    return "degraded"


PROMPT_INJECTION_RULES: tuple[tuple[str, str, str], ...] = (
    ("ignore_previous_instructions", r"ignore (all |any |the )?(previous|above) instructions", "high"),
    ("reveal_system_prompt", r"(reveal|show|print).{0,32}(system prompt|developer message)", "high"),
    ("bypass_safety", r"(bypass|disable|ignore).{0,24}(safety|guardrails|restrictions)", "high"),
    ("privilege_escalation", r"(act as root|sudo |administrator mode|tool override)", "medium"),
)


def line_column_for_offset(text: str, offset: int) -> tuple[int, int]:
    normalized = str(text or "")
    clamped = max(0, min(len(normalized), int(offset)))
    line = normalized.count("\n", 0, clamped) + 1
    previous_newline = normalized.rfind("\n", 0, clamped)
    column = clamped + 1 if previous_newline < 0 else clamped - previous_newline
    return line, column


def _normalize_scan_sources(
    text: str,
    sources: list[dict[str, Any]] | None = None,
) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    if isinstance(sources, list):
        for index, item in enumerate(sources[:200]):
            if not isinstance(item, dict):
                continue
            snippet = str(item.get("text", "") or "").strip()
            if not snippet:
                continue
            filename = str(item.get("file", "") or "").strip() or f"payload_source_{index + 1}"
            path = str(item.get("path", "") or "").strip() or "$"
            out.append(
                {
                    "file": filename,
                    "path": path,
                    "text": snippet[:6000],
                }
            )
    if out:
        return out
    fallback = str(text or "").strip()
    if not fallback:
        return []
    return [{"file": "payload", "path": "$", "text": fallback[:6000]}]


def detect_prompt_injection(
    text: str,
    *,
    sources: list[dict[str, Any]] | None = None,
) -> PromptInjectionReport:
    normalized = str(text or "")
    matched_rules: list[str] = []
    matched_phrases: list[str] = []
    matched_locations: list[RiskEvidence] = []
    severity = "none"
    seen_phrases: set[str] = set()
    scan_sources = _normalize_scan_sources(normalized, sources)
    max_locations = 60
    should_stop = False

    for source in scan_sources:
        source_text = source["text"]
        for rule_name, pattern, rule_severity in PROMPT_INJECTION_RULES:
            for match in re.finditer(pattern, source_text, flags=re.IGNORECASE | re.DOTALL):
                phrase = match.group(0).strip()[:120]
                if rule_name not in matched_rules:
                    matched_rules.append(rule_name)
                phrase_key = phrase.lower()
                if phrase and phrase_key not in seen_phrases:
                    matched_phrases.append(phrase)
                    seen_phrases.add(phrase_key)
                line, column = line_column_for_offset(source_text, match.start())
                matched_locations.append(
                    RiskEvidence(
                        category="prompt_injection",
                        rule=rule_name,
                        severity=rule_severity,
                        file=source["file"],
                        path=source["path"],
                        line=line,
                        column=column,
                        phrase=phrase,
                    )
                )
                if rule_severity == "high":
                    severity = "high"
                elif severity == "none":
                    severity = rule_severity
                if len(matched_locations) >= max_locations:
                    should_stop = True
                    break
            if should_stop:
                break
        if should_stop:
            break

    return PromptInjectionReport(
        detected=bool(matched_rules),
        severity=severity,
        matched_rules=matched_rules,
        matched_phrases=matched_phrases,
        matched_locations=matched_locations,
    )
