"""Minimal typed contracts for plugin manifest and astr-agent pipeline payloads."""

from __future__ import annotations

from typing import Any, Literal, TypedDict


Capability = Literal[
    "network.outbound",
    "file.read",
    "file.write",
    "command.exec",
    "provider.access",
    "mcp.invoke",
]


class PluginManifestEntry(TypedDict, total=False):
    module: str
    class_name: str
    method: str


class PluginCapabilityGroups(TypedDict, total=False):
    network: list[Literal["outbound", "internal", "loopback"]]
    file: list[Literal["read", "write", "config", "tmp"]]
    command: list[Literal["exec", "shell"]]
    provider: list[Literal["read", "write", "rotate"]]
    mcp: list[Literal["invoke", "install"]]


class PluginManifestCompatibility(TypedDict, total=False):
    astrbot: dict[str, str]
    sharelife: dict[str, str]


class PluginManifestV2(TypedDict, total=False):
    manifest_version: Literal["2.0"]
    plugin_id: str
    version: str
    display_name: str
    summary: str
    entry: PluginManifestEntry
    capabilities: PluginCapabilityGroups
    compatibility: PluginManifestCompatibility
    tags: list[str]


class AstrAgentPluginBinding(TypedDict, total=False):
    id: str
    manifest_ref: str
    declared_capabilities: list[Capability]
    config: dict[str, Any]


class AstrAgentStep(TypedDict, total=False):
    step_id: str
    plugin_ref: str
    input_from: str
    output_key: str
    on_failure: Literal["abort", "skip", "retry"]
    retry: int


class AstrAgentContract(TypedDict, total=False):
    schema_version: Literal["astr-agent.v1"]
    agent: dict[str, Any]
    plugins: list[AstrAgentPluginBinding]
    pipeline: dict[str, list[AstrAgentStep]]
    runtime: dict[str, Any]
