"""Protocol contract validator for Sharelife plugin ecosystem schemas."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

try:
    from jsonschema import Draft202012Validator
except Exception:  # pragma: no cover - optional import guard for degraded envs
    Draft202012Validator = None  # type: ignore[assignment]


class ProtocolValidationError(ValueError):
    """Raised when protocol contract payloads fail schema validation."""


class ProtocolContractService:
    """Validates plugin manifest and astr-agent contracts against frozen schemas."""

    def __init__(self, schema_root: Path | str | None = None):
        self.schema_root = Path(schema_root) if schema_root else Path(__file__).resolve().parents[1] / "contracts"
        self.plugin_manifest_schema = self._load_json_schema("plugin.manifest.v2.schema.json")
        self.astr_agent_schema = self._load_json_schema("astr-agent.v1.schema.json")

    def validate_plugin_manifest(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._validate(instance=payload, schema=self.plugin_manifest_schema, schema_name="plugin.manifest.v2")

    def validate_astr_agent_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._validate(instance=payload, schema=self.astr_agent_schema, schema_name="astr-agent.v1")

    def validate_astr_agent_yaml(self, text: str) -> dict[str, Any]:
        parsed = yaml.safe_load(text)
        if not isinstance(parsed, dict):
            raise ProtocolValidationError("astr-agent.v1 must be a YAML mapping")
        return self.validate_astr_agent_payload(parsed)

    def validate_example_files(self) -> dict[str, dict[str, Any]]:
        examples = self.schema_root / "examples"
        plugin_payload = json.loads((examples / "plugin.manifest.v2.example.json").read_text(encoding="utf-8"))
        agent_yaml = (examples / "astr-agent.example.yaml").read_text(encoding="utf-8")
        return {
            "plugin_manifest": self.validate_plugin_manifest(plugin_payload),
            "astr_agent": self.validate_astr_agent_yaml(agent_yaml),
        }

    def _validate(
        self,
        *,
        instance: dict[str, Any],
        schema: dict[str, Any],
        schema_name: str,
    ) -> dict[str, Any]:
        if Draft202012Validator is None:
            raise RuntimeError("jsonschema package is required for protocol validation")
        validator = Draft202012Validator(schema)
        errors = sorted(validator.iter_errors(instance), key=lambda item: list(item.absolute_path))
        if errors:
            first = errors[0]
            path = ".".join(str(part) for part in first.absolute_path) or "$"
            message = f"{schema_name} invalid at {path}: {first.message}"
            raise ProtocolValidationError(message)
        return instance

    def _load_json_schema(self, filename: str) -> dict[str, Any]:
        path = self.schema_root / filename
        return json.loads(path.read_text(encoding="utf-8"))
