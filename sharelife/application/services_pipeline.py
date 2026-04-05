"""Composable pipeline orchestrator with capability-gated execution."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from .services_capability_gateway import CapabilityGateway
from .services_protocol_contracts import ProtocolContractService, ProtocolValidationError


PipelineHandler = Callable[[Any, dict[str, Any], dict[str, Any]], Any]


@dataclass(slots=True)
class PipelinePluginRuntime:
    plugin_ref: str
    handler: PipelineHandler
    required_capabilities: list[str]


class PipelineOrchestrator:
    """Executes astr-agent pipeline steps with strict failure semantics."""

    def __init__(
        self,
        *,
        contract_service: ProtocolContractService | None = None,
        capability_gateway: CapabilityGateway | None = None,
    ):
        self.contract_service = contract_service or ProtocolContractService()
        self.capability_gateway = capability_gateway or CapabilityGateway()
        self._plugins: dict[str, PipelinePluginRuntime] = {}

    def register_plugin(
        self,
        *,
        plugin_ref: str,
        handler: PipelineHandler,
        required_capabilities: list[str] | None = None,
    ) -> None:
        normalized = str(plugin_ref or "").strip()
        if not normalized:
            raise ValueError("PIPELINE_PLUGIN_REF_REQUIRED")
        self._plugins[normalized] = PipelinePluginRuntime(
            plugin_ref=normalized,
            handler=handler,
            required_capabilities=self._normalize_caps(required_capabilities),
        )

    def execute(
        self,
        *,
        contract: dict[str, Any],
        input_payload: Any,
        actor_id: str,
        actor_role: str,
        run_id: str = "",
    ) -> dict[str, Any]:
        try:
            validated = self.contract_service.validate_astr_agent_payload(contract)
        except ProtocolValidationError as exc:
            return {
                "status": "invalid_contract",
                "error": str(exc),
                "run_id": run_id,
                "trace": [],
                "outputs": {},
            }

        plugins = {
            str(item.get("id", "") or ""): item
            for item in list(validated.get("plugins", []) or [])
            if str(item.get("id", "") or "").strip()
        }
        steps = list((validated.get("pipeline", {}) or {}).get("steps", []) or [])
        outputs: dict[str, Any] = {}
        trace: list[dict[str, Any]] = []
        final_status = "completed"

        for step in steps:
            step_id = str(step.get("step_id", "") or "").strip()
            plugin_ref = str(step.get("plugin_ref", "") or "").strip()
            step_trace = {
                "step_id": step_id,
                "plugin_ref": plugin_ref,
                "on_failure": str(step.get("on_failure", "abort") or "abort"),
                "retry": int(step.get("retry", 0) or 0),
            }

            plugin_manifest = plugins.get(plugin_ref)
            runtime_plugin = self._plugins.get(plugin_ref)
            if plugin_manifest is None or runtime_plugin is None:
                step_trace.update(
                    {
                        "status": "failed",
                        "error": "pipeline_plugin_not_registered",
                    }
                )
                trace.append(step_trace)
                final_status = "failed"
                break

            declared_capabilities = self._normalize_caps(plugin_manifest.get("declared_capabilities"))
            decision = self.capability_gateway.evaluate(
                actor_id=actor_id,
                actor_role=actor_role,
                operation=f"pipeline.step.{step_id}",
                required_capabilities=runtime_plugin.required_capabilities,
                declared_capabilities=declared_capabilities,
                target_id=step_id or plugin_ref,
                detail={"plugin_ref": plugin_ref, "run_id": run_id},
            )
            step_trace["capability_decision"] = decision.to_dict()

            if not decision.allowed:
                step_trace.update(
                    {
                        "status": "denied",
                        "error": "capability_denied",
                    }
                )
                trace.append(step_trace)
                handling = self._handle_failure(
                    outputs=outputs,
                    step=step,
                    step_trace=step_trace,
                    input_payload=input_payload,
                )
                if handling in {"aborted", "failed"}:
                    final_status = "failed"
                    break
                continue

            step_input = self._resolve_step_input(
                input_payload=input_payload,
                outputs=outputs,
                input_from=str(step.get("input_from", "$input") or "$input"),
            )

            retries = max(0, int(step.get("retry", 0) or 0))
            attempts = retries + 1
            executed = False
            last_error = ""
            for attempt in range(1, attempts + 1):
                try:
                    result = runtime_plugin.handler(
                        step_input,
                        dict(plugin_manifest.get("config", {}) or {}),
                        {"step": dict(step), "outputs": outputs, "run_id": run_id},
                    )
                    output_key = str(step.get("output_key", "") or "").strip() or step_id
                    if output_key:
                        outputs[output_key] = result
                    if step_id:
                        outputs[step_id] = result
                    step_trace.update(
                        {
                            "status": "succeeded",
                            "attempt": attempt,
                            "output_key": output_key,
                        }
                    )
                    executed = True
                    break
                except Exception as exc:  # pragma: no cover - branch covered via failure tests
                    last_error = str(exc)
                    if attempt < attempts and str(step.get("on_failure", "abort")) == "retry":
                        continue
                    break

            if not executed:
                step_trace.update(
                    {
                        "status": "failed",
                        "error": last_error or "pipeline_step_failed",
                    }
                )
                trace.append(step_trace)
                handling = self._handle_failure(
                    outputs=outputs,
                    step=step,
                    step_trace=step_trace,
                    input_payload=input_payload,
                )
                if handling in {"aborted", "failed"}:
                    final_status = "failed"
                    break
                continue

            trace.append(step_trace)

        return {
            "status": final_status,
            "run_id": run_id,
            "outputs": outputs,
            "trace": trace,
            "steps_total": len(steps),
            "steps_executed": len([item for item in trace if item.get("status") == "succeeded"]),
            "steps_failed": len([item for item in trace if item.get("status") in {"failed", "denied"}]),
        }

    @staticmethod
    def _normalize_caps(values: list[str] | Any) -> list[str]:
        out: list[str] = []
        seen: set[str] = set()
        for item in values or []:
            normalized = str(item or "").strip()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            out.append(normalized)
        return out

    @staticmethod
    def _resolve_step_input(*, input_payload: Any, outputs: dict[str, Any], input_from: str) -> Any:
        normalized = str(input_from or "$input").strip()
        if normalized in {"$input", "input"}:
            return input_payload
        return outputs.get(normalized)

    @staticmethod
    def _handle_failure(
        *,
        outputs: dict[str, Any],
        step: dict[str, Any],
        step_trace: dict[str, Any],
        input_payload: Any,
    ) -> str:
        on_failure = str(step.get("on_failure", "abort") or "abort").strip().lower()
        if on_failure == "skip":
            step_trace["failure_action"] = "skipped"
            return "skipped"
        if on_failure == "retry":
            step_trace["failure_action"] = "aborted_after_retries"
            return "aborted"
        step_trace["failure_action"] = "aborted"
        return "aborted"


def builtin_pipeline_plugins() -> dict[str, PipelinePluginRuntime]:
    """Built-in reference processors for contract testing and quickstarts."""

    def uppercase_handler(value: Any, config: dict[str, Any], _: dict[str, Any]) -> str:
        source = "" if value is None else str(value)
        if str(config.get("transform", "") or "").lower() == "lowercase":
            return source.lower()
        return source.upper()

    def suffix_handler(value: Any, config: dict[str, Any], _: dict[str, Any]) -> str:
        source = "" if value is None else str(value)
        suffix = str(config.get("suffix", "") or "")
        return f"{source}{suffix}"

    return {
        "upper": PipelinePluginRuntime(
            plugin_ref="upper",
            handler=uppercase_handler,
            required_capabilities=["file.read"],
        ),
        "suffix": PipelinePluginRuntime(
            plugin_ref="suffix",
            handler=suffix_handler,
            required_capabilities=["file.read"],
        ),
    }
