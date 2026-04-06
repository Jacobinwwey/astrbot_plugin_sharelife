# Sharelife Plugin Ecosystem Round 2 Execution Plan

## Goal

Execute Round 2 baseline from protocol to runtime governance without derailing current community-first product flow.

## Milestones

### M1: Protocol Freeze

- [x] Define `plugin.manifest.v2.json` schema and examples.
- [x] Define `astr-agent.yaml` schema and examples.
- [x] Add CI schema validation tasks.

Exit criteria:

1. Invalid manifests fail CI.
2. Valid examples pass schema checks.

### M2: Capability Gateway

- [x] Implement permission interception points for network/file/command/provider/mcp.
- [x] Add deny-by-default behavior for undeclared high-risk capabilities.
- [x] Add structured audit events for allow/deny decisions.

Exit criteria:

1. Permission-denied paths are test-covered.
2. Audit trail includes policy decision evidence.

### M3: Developer Experience Baseline

- [x] Implement `create-astrbot-plugin` scaffolding command.
- [x] Add hot-reload development command.
- [x] Publish minimal SDK type contracts and examples.

Exit criteria:

1. New plugin from scaffold can run within 10 minutes.
2. Hot reload shortens local feedback loop.

### M4: Composability Baseline

- [x] Add pipeline context contract.
- [x] Implement A->B plugin output/input chaining.
- [x] Add failure handling semantics (retry/skip/abort).

Exit criteria:

1. Two independent plugins can be composed without custom glue code.
2. Pipeline failures are observable and recoverable.

### M5: Registry Governance Upgrade

- [x] Extend registry metadata for capability summary and compatibility matrix.
- [x] Add review evidence rendering in WebUI.
- [x] Add `featured` curation process doc and gate.

Exit criteria:

1. Users can inspect risk and permission footprint before install.
2. Featured process is documented and reproducible.

## Rollout Strategy

1. Start with personal/community mode defaults.
2. Keep enterprise knobs optional and disabled by default.
3. Roll out per capability category, not all at once.

## Verification

1. `pytest -q`
2. `node --test tests/webui/*.js`
3. `npm run docs:build --prefix docs`
