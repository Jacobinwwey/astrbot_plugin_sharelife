"""Runtime capability gateway for high-risk operation enforcement."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .services_audit import AuditService


CAP_NETWORK_OUTBOUND = "network.outbound"
CAP_FILE_READ = "file.read"
CAP_FILE_WRITE = "file.write"
CAP_COMMAND_EXEC = "command.exec"
CAP_PROVIDER_ACCESS = "provider.access"
CAP_MCP_INVOKE = "mcp.invoke"

CAPABILITY_CATALOG = {
    CAP_NETWORK_OUTBOUND,
    CAP_FILE_READ,
    CAP_FILE_WRITE,
    CAP_COMMAND_EXEC,
    CAP_PROVIDER_ACCESS,
    CAP_MCP_INVOKE,
}
HIGH_RISK_CAPABILITIES = {
    CAP_NETWORK_OUTBOUND,
    CAP_FILE_WRITE,
    CAP_COMMAND_EXEC,
    CAP_PROVIDER_ACCESS,
    CAP_MCP_INVOKE,
}


@dataclass(slots=True)
class CapabilityDecision:
    allowed: bool
    operation: str
    required_capabilities: list[str]
    declared_capabilities: list[str]
    missing_capabilities: list[str]
    evidence: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "operation": self.operation,
            "required_capabilities": list(self.required_capabilities),
            "declared_capabilities": list(self.declared_capabilities),
            "missing_capabilities": list(self.missing_capabilities),
            "evidence": dict(self.evidence),
        }


class CapabilityGateway:
    """Deny-by-default gateway for undeclared high-risk capabilities."""

    def __init__(self, audit_service: AuditService | None = None):
        self.audit_service = audit_service

    def evaluate(
        self,
        *,
        actor_id: str,
        actor_role: str,
        operation: str,
        required_capabilities: list[str] | None,
        declared_capabilities: list[str] | None,
        target_id: str = "",
        detail: dict[str, Any] | None = None,
    ) -> CapabilityDecision:
        required = self._normalize(required_capabilities)
        declared = self._normalize(declared_capabilities)

        required_high_risk = sorted(item for item in required if item in HIGH_RISK_CAPABILITIES)
        unknown_required = sorted(item for item in required if item not in CAPABILITY_CATALOG)
        missing = sorted({*(item for item in required_high_risk if item not in declared), *unknown_required})

        evidence = {
            "policy": "deny_undeclared_high_risk",
            "required_high_risk": required_high_risk,
            "unknown_required": unknown_required,
        }
        if detail:
            evidence.update(detail)

        decision = CapabilityDecision(
            allowed=not missing,
            operation=str(operation or "").strip() or "unknown_operation",
            required_capabilities=required,
            declared_capabilities=declared,
            missing_capabilities=missing,
            evidence=evidence,
        )
        self._record_decision(
            actor_id=actor_id,
            actor_role=actor_role,
            target_id=target_id or decision.operation,
            decision=decision,
        )
        return decision

    @staticmethod
    def _normalize(values: list[str] | None) -> list[str]:
        out: list[str] = []
        seen: set[str] = set()
        for item in values or []:
            normalized = str(item or "").strip()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            out.append(normalized)
        return out

    def _record_decision(
        self,
        *,
        actor_id: str,
        actor_role: str,
        target_id: str,
        decision: CapabilityDecision,
    ) -> None:
        if self.audit_service is None:
            return
        self.audit_service.record(
            action="capability.gateway_decision",
            actor_id=actor_id or "unknown_actor",
            actor_role=actor_role or "unknown_role",
            target_id=target_id or decision.operation,
            status="allow" if decision.allowed else "deny",
            detail=decision.to_dict(),
        )
