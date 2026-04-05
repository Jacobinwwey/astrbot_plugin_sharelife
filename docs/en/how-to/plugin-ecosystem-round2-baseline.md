# Plugin ecosystem Round 2 baseline (v0.3.13)

This baseline moves `sharelife` from a feature plugin to a platform-oriented plugin.

## MVP boundary

The minimum viable platform includes:

1. `plugin.manifest.v2.json` contract
2. `astr-agent.yaml` composable pipeline contract
3. Capability gateway for network/file/command/provider/MCP permissions
4. `create-astrbot-plugin` scaffolding
5. Hot-reload dev workflow
6. Market governance flow (risk labels, compatibility checks, install confirmation, audit logs)

## Implementation status (M1-M5)

1. `M1` done: schemas + examples + CI validator (`scripts/validate_protocol_examples.py`)
2. `M2` done: capability gateway (`sharelife/application/services_capability_gateway.py`) with deny-by-default for undeclared high-risk capabilities
3. `M3` done: DX commands (`scripts/create-astrbot-plugin`, `scripts/sharelife-hot-reload`) + SDK contracts (`sharelife/sdk/contracts.py`)
4. `M4` done: pipeline orchestrator (`sharelife/application/services_pipeline.py`) with A->B chaining and `retry/skip/abort`
5. `M5` done: governance metadata (`capability_summary`, `compatibility_matrix`, `review_evidence`) + featured curation gate (`/api/admin/profile-pack/catalog/featured`)

Post-M5 extension:

1. `M6` done: plugin install execution closure (`plan -> confirm -> execute`) is implemented with default-off execution, command-prefix allowlist, timeout guard, execution evidence persistence, and optional `require_success_before_apply`

## Architecture (text)

```text
Plugin Lifecycle -> Capability Gateway -> Runtime Adapters
        |                  |                    |
        v                  v                    v
     Event Bus <-> Pipeline Orchestrator <-> Risk/Audit Engine
        |                  |                    |
        +---------- WebUI/CLI + Registry + Package Storage
```

## Core components

1. Lifecycle manager
2. Capability gateway
3. Manifest/schema validator
4. Pipeline orchestrator
5. Risk/audit engine
6. Registry service
7. DX toolchain

## Main data flows

1. Publish: validate -> package -> scan -> label -> catalog
2. Install: browse -> compatibility check -> permission confirm -> install -> audit
3. Runtime: trigger -> capability check -> plugin call -> audit
4. Profile/extension pack: export -> import -> dry-run -> apply/rollback

## Tech stack

1. Python 3.12 + FastAPI + Pydantic
2. Existing `application/domain/interfaces/infrastructure` service split
3. WebUI + VitePress + GitHub Actions + GitHub Pages + GitHub Releases

## Build order

1. Freeze protocol schemas
2. Implement capability gateway
3. Deliver scaffold + hot reload DX
4. Implement composable pipeline contract
5. Add governance/evidence visibility in market

## Edge cases to cover

1. Missing permission declarations
2. Version incompatibility (`astrbot_version` / `plugin_compat`)
3. Hot-reload state pollution
4. Mid-pipeline partial failure
5. High-risk plugin install without admin confirmation

## v2 direction

1. Stronger sandbox tiers
2. Plugin resource budgets and rate limits
3. Scenario/risk/compatibility market recommendations
4. Plugin-level tracing and failure analytics
5. Unified Astr UI Kit
6. Deep-link one-click install from web market to local AstrBot
