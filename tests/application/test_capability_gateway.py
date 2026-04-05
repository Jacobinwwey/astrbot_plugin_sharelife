from datetime import UTC, datetime

from sharelife.application.services_audit import AuditService
from sharelife.application.services_capability_gateway import CapabilityGateway


class FrozenClock:
    def __init__(self, now: datetime):
        self.now = now

    def utcnow(self) -> datetime:
        return self.now


def test_capability_gateway_denies_undeclared_high_risk_and_records_audit():
    audit = AuditService(clock=FrozenClock(datetime(2026, 3, 31, 8, 0, tzinfo=UTC)))
    gateway = CapabilityGateway(audit_service=audit)

    decision = gateway.evaluate(
        actor_id="admin",
        actor_role="admin",
        operation="pipeline.step.install_plugin",
        required_capabilities=["command.exec", "network.outbound"],
        declared_capabilities=["file.read"],
        target_id="step-install",
    )

    assert decision.allowed is False
    assert decision.missing_capabilities == ["command.exec", "network.outbound"]

    events = audit.list_events(limit=5)
    assert len(events) == 1
    assert events[0].action == "capability.gateway_decision"
    assert events[0].status == "deny"
    assert events[0].detail["missing_capabilities"] == ["command.exec", "network.outbound"]


def test_capability_gateway_allows_non_high_risk_without_declaration():
    gateway = CapabilityGateway()
    decision = gateway.evaluate(
        actor_id="member-1",
        actor_role="member",
        operation="pipeline.step.read_context",
        required_capabilities=["file.read"],
        declared_capabilities=[],
    )
    assert decision.allowed is True
    assert decision.missing_capabilities == []
