import json

import pytest
import yaml

from sharelife.application.services_protocol_contracts import (
    ProtocolContractService,
    ProtocolValidationError,
)


def test_protocol_contract_service_validates_bundled_examples():
    service = ProtocolContractService()
    result = service.validate_example_files()
    assert result["plugin_manifest"]["manifest_version"] == "2.0"
    assert result["astr_agent"]["schema_version"] == "astr-agent.v1"


def test_protocol_contract_service_rejects_invalid_plugin_manifest():
    service = ProtocolContractService()
    payload = {
        "manifest_version": "2.0",
        "plugin_id": "bad.plugin",
        "version": "1.0.0",
        "display_name": "Bad Plugin",
        "entry": {"module": "x", "class_name": "Runner"},
        "compatibility": {
            "astrbot": {"min": "4.0.0", "max": "5.x"},
            "sharelife": {"plugin_api": "v1"},
        },
    }
    with pytest.raises(ProtocolValidationError):
        service.validate_plugin_manifest(payload)


def test_protocol_contract_service_rejects_invalid_astr_agent_contract():
    service = ProtocolContractService()
    payload = yaml.safe_load(
        """
schema_version: astr-agent.v1
agent:
  id: demo-agent
  name: demo
  persona: test
plugins:
  - id: first
    manifest_ref: plugin.manifest.v2.example.json
    declared_capabilities: [file.read]
pipeline:
  steps:
    - step_id: s1
      on_failure: explode
"""
    )
    with pytest.raises(ProtocolValidationError):
        service.validate_astr_agent_payload(payload)


def test_protocol_contract_service_accepts_valid_manifest_payload():
    service = ProtocolContractService()
    payload = json.loads(
        (
            service.schema_root
            / "examples"
            / "plugin.manifest.v2.example.json"
        ).read_text(encoding="utf-8")
    )
    validated = service.validate_plugin_manifest(payload)
    assert validated["plugin_id"].startswith("sharelife.")
