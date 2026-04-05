# Bot profile migration scope (ground truth)

If you only need one answer, this is it: **what settings Sharelife migrates today**.

## Baseline (current implementation)

1. AstrBot upstream baseline: `origin/master@9d4472cb2d0108869d688a4ac731e539d41b919e` (2026-04-02).
2. Branch note: AstrBot upstream currently uses `master` as the primary branch, not `main`.
3. Sharelife baseline: `main@7aebf279d074b80df7566c2d957f58d2c3cd6efd`.
4. Migration model: **section-level snapshot/patch** from Sharelife runtime state (default `runtime_state.json`), not a direct full rewrite of AstrBot config files.

## Quick answer

1. `bot_profile_pack` migrates:
   `astrbot_core/providers/plugins/skills/personas/mcp_servers/sharelife_meta/memory_store/conversation_history/knowledge_base/environment_manifest`
2. `extension_pack` migrates:
   `plugins/skills/personas/mcp_servers`
3. Migration is key-preserving replay, without semantic field remapping.

## Scope matrix (implemented now)

| Section | Source key (runtime snapshot) | Current migration behavior | Notes |
|---|---|---|---|
| `astrbot_core` | `snapshot["astrbot_core"]` | Full export/import/dry-run/apply/rollback | Carries bot core mirror state, not AstrBot full root config |
| `providers` | `snapshot["providers"]` | Full workflow supported | Supports `exclude_secrets` / `exclude_provider` / `include_provider_no_key` / `include_encrypted_secrets` |
| `plugins` | `snapshot["plugins"]` | Full workflow supported | Plugin install metadata triggers `plan -> confirm -> execute` guard |
| `skills` | `snapshot["skills"]` | Full workflow supported | Suitable for capability bundle sharing |
| `personas` | `snapshot["personas"]` | Full workflow supported | Suitable for persona bundle sharing |
| `mcp_servers` | `snapshot["mcp_servers"]` | Full workflow supported | MCP server declarations can be migrated with the pack |
| `sharelife_meta` | `snapshot["sharelife_meta"]` | Full workflow (`bot_profile_pack` only) | Sharelife internal metadata, not AstrBot core config |
| `memory_store` | `snapshot["memory_store"]` | Full workflow (`bot_profile_pack` only) | Optional local memory migration; evaluate size/sensitivity before apply |
| `conversation_history` | `snapshot["conversation_history"]` | Full workflow (`bot_profile_pack` only) | Optional chat-history migration; may include sensitive user content |
| `knowledge_base` | `snapshot["knowledge_base"]` | Full workflow (`bot_profile_pack` only) | Migrates KB config/index metadata; external raw files still need manual sync |
| `environment_manifest` | `snapshot["environment_manifest"]` | Exported and surfaced in compatibility notices (`bot_profile_pack` only) | Declares container/system/plugin-binary reconfiguration requirements; no automatic system mutation |

## Explicitly out of scope today

1. Keys in AstrBot `data/cmd_config.json` that are not mirrored into the listed sections are not auto-migrated.
2. No field-level translator against AstrBot config schema exists yet; adapters are currently `section_name -> state_key`.
3. Plugin binaries, system dependencies, container runtime state, and external DB/KB raw files are not bundled by profile pack; `environment_manifest` only carries reconfiguration metadata.
4. Plugin install command execution is default-off; install metadata still needs explicit admin confirmation and execution-gate config.
5. Cross-version support relies on declaration checks (`astrbot_version` / `plugin_compat`), not automatic semantic migration.
6. If a pack includes `environment_manifest` or KB external paths, import will keep `compatibility=degraded` with explicit `compatibility_issues` so operators can run post-migration reconfiguration.

## Accuracy and safety controls (current)

1. Per-section hash verification on import.
2. Optional HMAC manifest signing and trusted-key verification.
3. `include_encrypted_secrets` supports encrypted export and decrypt-on-import/dry-run/apply (requires `profile_pack.secrets_encryption_key`).
4. Apply path is snapshot-backed and rollback-capable.
5. Risk and governance evidence are persisted in `capability_summary` and `review_evidence`.
6. `environment_manifest` is converted into explicit `environment_*_reconfigure_required` issues to prevent false assumptions about system-level auto-migration.

## How users can verify migration content before apply

1. Confirm target section data exists in runtime state.
2. Export with section control:
   `/sharelife_profile_export <pack_id> <version> exclude_secrets <sections_csv>`
3. Import with dry-run:
   `/sharelife_profile_import <artifact_id> --dryrun --plan-id <plan_id> --sections <sections_csv>`
4. Review `selected_sections`, `changed_sections`, and `diff` before apply.
5. If `compatibility_issues` includes `environment_*_reconfigure_required` or `knowledge_base_storage_sync_required`, hand that list to your AI/Ops agent after migration and execute environment reconfiguration explicitly.

## Maintenance checklist (for developers)

When AstrBot upstream config changes, keep this document and implementation aligned:

1. Update the baseline commit references on this page (AstrBot + Sharelife).
2. Diff upstream config keys (see AstrBot config docs).
3. Decide section ownership for new keys and extend section adapters if needed.
4. Add tests for export/import/dry-run/apply/rollback.
5. Sync README and multilingual docs entry points to avoid doc/behavior drift.

## References

1. AstrBot config docs: <https://github.com/AstrBotDevs/AstrBot/blob/master/docs/zh/dev/astrbot-config.md>
2. Sharelife Bot Profile Pack operations: [/en/how-to/bot-profile-pack](/en/how-to/bot-profile-pack)
