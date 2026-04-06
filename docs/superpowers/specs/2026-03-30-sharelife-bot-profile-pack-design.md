# Sharelife Bot Profile Pack Design

## Context

Sharelife currently provides template/package governance, risk scanning, moderation, audit, WebUI role separation, and safe apply/rollback controls. Those primitives are strong enough to carry a larger product objective:

1. Copy and migrate a bot's effective setup.
2. Share setup as installable package.
3. Selectively exclude secrets/provider credentials.
4. Re-apply setup with dry-run visibility and rollback safety.

The missing piece is not governance. The missing piece is a dedicated "cross-module configuration capture / mapping / replay" layer.

## Goal

Ship a new package capability named `bot_profile_pack` that supports one-click export/import of bot setup while preserving safety controls.

Target scope:

1. Capture settings by section (`astrbot_core`, `providers`, `plugins`, `skills`, `personas`, `mcp_servers`, `sharelife_meta`).
2. Export as zip package with structured manifest.
3. Support redaction strategies (`exclude_secrets` default, optional provider exclusion).
4. Import with dry-run diff, selective section apply, and rollback.

## Non-Goals

1. Full enterprise secret vault integration in v1.
2. Cross-instance remote control plane.
3. Auto-install untrusted plugin binaries without admin confirmation.
4. New parallel governance subsystem outside current Sharelife flow.

## Design Principles

1. Reuse existing package/scan/audit/moderation foundations.
2. Keep section adapters modular; each adapter owns one config domain.
3. Default to safe export (`exclude_secrets`) and explicit admin confirmation for risky operations.
4. Persist full operation timeline in audit log.

## Package Model

### Pack Types

1. `template_pack` (existing)
2. `bot_profile_pack` (new)
3. `extension_pack` (future: skills/personas/mcp/plugin set)

### Bot Profile Pack Layout

1. `manifest.json`
2. `sections/astrbot_core.json`
3. `sections/providers.json`
4. `sections/plugins.json`
5. `sections/skills.json`
6. `sections/personas.json`
7. `sections/mcp_servers.json`
8. `sections/sharelife_meta.json`
9. `artifacts/*` (optional file-based assets)

### Manifest Required Fields

1. `pack_type=bot_profile_pack`
2. `pack_id`
3. `version`
4. `created_at`
5. `astrbot_version`
6. `plugin_compat`
7. `sections`
8. `redaction_policy`
9. `hashes`

## Export Policy

### Default Policy

`exclude_secrets=true` by default.

### Policy Modes

1. `exclude_secrets` (default)
2. `exclude_provider`
3. `include_provider_no_key`
4. `include_encrypted_secrets` (Phase 4)

### Redaction Rules

1. Known secret keys are removed or masked.
2. Provider entries can be dropped entirely when policy requires.
3. Unknown sensitive-like keys (token/key/secret/password) are quarantined and flagged.

## Apply Policy

1. Import package -> parse manifest -> compatibility check.
2. Build section diff against current runtime/config snapshot.
3. Produce dry-run report with per-section risk labels.
4. Admin selects sections to apply.
5. Apply through guarded path with rollback snapshot.

## Compatibility Gate

1. Block on hard mismatch (`astrbot_version`, `plugin_compat`) unless explicit override policy is enabled.
2. Mark degraded on partial section mismatch and allow selective apply.

## Risk and Supply-Chain Controls

1. Section whitelist only; unknown section files go to quarantine.
2. Plugin section stores metadata (`name/version/source/hash`) and requires explicit admin confirm before install operations.
3. Scan service receives combined payload for prompt-injection and dangerous override markers.

## Architecture

### New Application Services

1. `ProfilePackService`: export/import package orchestrator.
2. `ProfileSectionAdapterRegistry`: adapter registration and section dispatch.
3. `ProfileDiffService`: compute dry-run diff model.

### New Domain Models

1. `BotProfilePackManifest`
2. `BotProfileSection`
3. `RedactionPolicy`
4. `ProfileApplyPlan`

### Interfaces

1. API v1 methods for export/import/dry-run/selective apply.
2. Web API + WebUI controls for section selection.
3. New admin commands for package apply pipeline.

## Phased Delivery

### Phase 1 (must ship first)

1. `bot_profile_pack` export/import minimal closed loop.
2. Default `exclude_secrets`.
3. Dry-run diff + rollback apply.
4. Command/API coverage.

### Phase 2

1. WebUI selective section apply.
2. Field-level redaction controls.

### Phase 3

1. Community `extension_pack` moderation flow.
2. Skills/personas/mcp/plugin bundles as publishable artifacts.

### Phase 4

1. Encrypted secrets option.
2. Package signing and verification.

## Success Criteria

1. A bot setup can be exported and imported as `bot_profile_pack`.
2. Default exports do not include plaintext credentials.
3. Import supports dry-run and selective apply with rollback.
4. Risk report and audit events cover the full pipeline.
