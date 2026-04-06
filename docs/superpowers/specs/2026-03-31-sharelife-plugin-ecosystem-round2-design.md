# Sharelife Plugin Ecosystem Round 2 Design (Baseline)

## Context

Sharelife has reached a stable governance feature set (submission moderation, profile/extension packs, risk labels, compare visualization, and multilingual docs).  
The next stage is platformization: plugin ecosystem, capability boundaries, and composable agent workflows.

## Goal

Define and freeze a Round 2 baseline that enables:

1. Protocol-first plugin contracts.
2. Runtime permission enforcement.
3. Developer onboarding with low friction.
4. Composable plugin-to-plugin pipeline.
5. Market governance with explainable risk evidence.

## Non-Goals (Baseline)

1. Full multi-tenant enterprise control plane.
2. Mandatory hard sandbox isolation on day one.
3. Full remote orchestration service.

## Baseline Deliverables

1. `plugin.manifest.v2.json` schema draft.
2. `astr-agent.yaml` schema draft.
3. Capability gateway design and interception points.
4. Scaffolding and hot-reload design contract.
5. Registry and review-label contract extension plan.

## Architecture

```text
Lifecycle + Event Bus + Capability Gateway + Pipeline Orchestrator + Risk/Audit
                                      |
                               Registry + WebUI/CLI
```

## Key Design Decisions

1. Keep current service boundaries and layer new ecosystem protocols on top.
2. Permission declaration is mandatory for high-impact operations.
3. Plugin install remains admin-confirmed for risky bundles.
4. Composability uses typed context contracts, not ad-hoc JSON blobs.

## Risks

1. DX lag slows ecosystem growth.
2. Permission drift breaks trust model.
3. Over-manual moderation reduces throughput.
4. Contract drift reduces pipeline interoperability.

## Success Criteria

1. Round 2 baseline docs are published and navigable in zh/en/ja docs.
2. A new release tags this baseline as the future development starting point.
3. Next implementation cycle can start from protocol and gateway work without re-framing architecture.
