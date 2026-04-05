from __future__ import annotations

from datetime import UTC, datetime

import yaml

from sharelife.application.services_audit import AuditService
from sharelife.application.services_capability_gateway import CapabilityGateway
from sharelife.application.services_pipeline import PipelineOrchestrator, builtin_pipeline_plugins
from sharelife.application.services_protocol_contracts import ProtocolContractService


class FrozenClock:
    def __init__(self, now: datetime):
        self.now = now

    def utcnow(self) -> datetime:
        return self.now


def _build_orchestrator() -> PipelineOrchestrator:
    audit = AuditService(clock=FrozenClock(datetime(2026, 3, 31, 8, 30, tzinfo=UTC)))
    gateway = CapabilityGateway(audit_service=audit)
    orchestrator = PipelineOrchestrator(
        contract_service=ProtocolContractService(),
        capability_gateway=gateway,
    )
    for plugin_ref, runtime in builtin_pipeline_plugins().items():
        orchestrator.register_plugin(
            plugin_ref=plugin_ref,
            handler=runtime.handler,
            required_capabilities=runtime.required_capabilities,
        )
    return orchestrator


def _base_contract() -> dict:
    return yaml.safe_load(
        """
schema_version: astr-agent.v1
agent:
  id: demo-agent
  name: Demo Agent
  persona: concise
plugins:
  - id: upper
    manifest_ref: plugin.manifest.v2.example.json
    declared_capabilities: [file.read]
    config:
      transform: uppercase
  - id: suffix
    manifest_ref: plugin.manifest.v2.example.json
    declared_capabilities: [file.read]
    config:
      suffix: " ::verified"
pipeline:
  steps:
    - step_id: step_upper
      plugin_ref: upper
      input_from: $input
      output_key: upper_result
      on_failure: abort
      retry: 0
    - step_id: step_suffix
      plugin_ref: suffix
      input_from: step_upper
      output_key: final
      on_failure: abort
      retry: 0
"""
    )


def test_pipeline_orchestrator_chains_step_outputs_without_custom_glue():
    orchestrator = _build_orchestrator()
    result = orchestrator.execute(
        contract=_base_contract(),
        input_payload="hello",
        actor_id="admin",
        actor_role="admin",
        run_id="run-1",
    )

    assert result["status"] == "completed"
    assert result["outputs"]["step_upper"] == "HELLO"
    assert result["outputs"]["final"] == "HELLO ::verified"
    assert result["steps_failed"] == 0


def test_pipeline_orchestrator_denies_undeclared_high_risk_plugin_capability():
    orchestrator = _build_orchestrator()

    def install_handler(value, config, context):
        return f"installed:{value}"

    orchestrator.register_plugin(
        plugin_ref="installer",
        handler=install_handler,
        required_capabilities=["command.exec"],
    )

    contract = yaml.safe_load(
        """
schema_version: astr-agent.v1
agent:
  id: demo-agent
  name: Demo Agent
  persona: strict
plugins:
  - id: installer
    manifest_ref: plugin.manifest.v2.example.json
    declared_capabilities: [file.read]
pipeline:
  steps:
    - step_id: install_step
      plugin_ref: installer
      input_from: $input
      output_key: installed
      on_failure: abort
      retry: 0
"""
    )

    result = orchestrator.execute(
        contract=contract,
        input_payload="pkg",
        actor_id="admin",
        actor_role="admin",
        run_id="run-2",
    )

    assert result["status"] == "failed"
    assert result["steps_failed"] == 1
    assert result["trace"][0]["status"] == "denied"
    assert result["trace"][0]["capability_decision"]["missing_capabilities"] == ["command.exec"]


def test_pipeline_orchestrator_supports_retry_failure_semantics():
    orchestrator = _build_orchestrator()
    attempts = {"count": 0}

    def flaky_handler(value, config, context):
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise ValueError("temporary failure")
        return str(value).upper()

    orchestrator.register_plugin(
        plugin_ref="flaky",
        handler=flaky_handler,
        required_capabilities=["file.read"],
    )

    contract = yaml.safe_load(
        """
schema_version: astr-agent.v1
agent:
  id: demo-agent
  name: Demo Agent
  persona: resilient
plugins:
  - id: flaky
    manifest_ref: plugin.manifest.v2.example.json
    declared_capabilities: [file.read]
pipeline:
  steps:
    - step_id: flaky_step
      plugin_ref: flaky
      input_from: $input
      output_key: final
      on_failure: retry
      retry: 1
"""
    )

    result = orchestrator.execute(
        contract=contract,
        input_payload="retry-me",
        actor_id="admin",
        actor_role="admin",
        run_id="run-3",
    )

    assert result["status"] == "completed"
    assert result["outputs"]["final"] == "RETRY-ME"
    assert attempts["count"] == 2
