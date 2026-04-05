# Bot profile pack operations

Use this runbook for day-to-day `bot_profile_pack` and `extension_pack` operations.

Need the exact migration boundary first? Start here:
[Bot profile migration scope (ground truth)](/en/how-to/profile-pack-migration-scope)

## What this flow gives you

1. Export runtime config into a transferable package.
2. Keep secrets redacted by default.
3. Preview section-level diff before apply.
4. Apply with rollback available.
5. Share extension-oriented bundles (`skills`, `personas`, `mcp_servers`, `plugins`).

## Official reference pack

Sharelife now seeds one published starter pack automatically:

1. `pack_id`: `profile/official-starter`
2. `pack_type`: `bot_profile_pack`
3. `version`: `1.0.0`
4. `featured`: `true`

Use this as your baseline for:

1. catalog filtering (`pack_id=profile/official-starter`)
2. compare-with-runtime walkthrough
3. import + dry-run + apply rehearsal before sharing your own pack

The repository also includes a concrete sample pack in exploded form:

1. `examples/profile-packs/official-starter/manifest.json`
2. `examples/profile-packs/official-starter/sections/*.json`

To build an importable zip locally:

```bash
cd examples/profile-packs/official-starter
zip -r profile-official-starter-1.0.0.bot-profile-pack.zip manifest.json sections
```

## Admin command flow

```text
/sharelife_profile_export profile/basic 1.0.0 exclude_secrets astrbot_core,providers,plugins providers.openai.base_url sharelife_meta.owner bot_profile_pack
/sharelife_profile_export extension/community-tools 1.0.0 exclude_secrets "" "" "" extension_pack
/sharelife_profile_exports 20
/sharelife_profile_import <artifact_id> --dryrun --plan-id profile-plan-basic --sections plugins,providers
/sharelife_profile_plugins <import_id>
/sharelife_profile_plugins_confirm <import_id> [plugins_csv]
/sharelife_profile_plugins_install <import_id> [plugins_csv] [dry_run]
/sharelife_profile_import_dryrun <artifact_id> profile-plan-basic plugins,providers
/sharelife_profile_import_dryrun_latest profile-plan-basic plugins,providers
/sharelife_profile_imports 20
```

### Notes

1. `/sharelife_profile_import` source accepts `artifact_id` or local `.zip` path.
2. `--dryrun` runs dry-run right after import.
3. `--plan-id` and `--sections` are optional.
4. Export positional args:
   `pack_id version redaction_mode sections_csv mask_paths_csv drop_paths_csv pack_type`.
5. If dry-run returns `profile_pack_plugin_install_confirm_required`, run
   `/sharelife_profile_plugins` then `/sharelife_profile_plugins_confirm`, then rerun dry-run.
6. `/sharelife_profile_plugins_install` executes only when
   `profile_pack.plugin_install.enabled=true`.

## WebUI flow

In **Bot Profile Pack** panel:

1. Export (`Export Profile Pack`).
2. Import by file or export artifact.
3. Optional one-click `Import + Dry-Run`.
4. Or select sections and run dry-run manually.
5. For plugin sections: `Plugin Install Plan` -> `Confirm Plugin Install` -> `Execute Plugin Install`.
6. Apply or rollback with the plan controls.

### Compatibility guidance panel (WebUI)

After import or dry-run, Sharelife now renders a dedicated **Compatibility Guidance** block:

1. `Compatibility` summary (`compatible` / `degraded` / `blocked`).
2. Human-readable issue list (signature/encrypted-secrets/runtime mismatch families).
3. Action checklist for environment follow-up:
   container reconfigure, system dependency reinstall, plugin binary reinstall, KB storage sync.
4. Clickable action shortcuts: each action jumps to the relevant operation area (plugin install controls / section selector / developer payload).
5. Issue rows with known mappings are also clickable and reuse the same shortcut pipeline.
6. Shortcut clicks now prefill follow-up inputs when possible:
   plugin-related actions auto-fill `plugin_ids` from `missing_plugins`, and KB sync actions auto-select `knowledge_base` section.
7. For developer-only targets, the shortcut asks you to enable Developer Mode, then resumes automatically after toggle.
8. Developer Mode only:
   raw `compatibility_issues` + normalized `action_codes` payload.

Use this block as the source of truth for "migration is technically imported, but still needs environment reconfiguration".

## Redaction modes

1. `exclude_secrets` (default): keep provider structure, mask secret values.
2. `exclude_provider`: remove provider section.
3. `include_provider_no_key`: keep provider fields except key-like secrets.
4. `include_encrypted_secrets`: export encrypted secrets and decrypt on import/dry-run/apply when `profile_pack.secrets_encryption_key` is configured.

Advanced overrides:

1. `mask_paths`: force mask by dotted path.
2. `drop_paths`: remove by dotted path.

## Pack types

1. `bot_profile_pack`: full runtime sections (`astrbot_core/providers/plugins/skills/personas/mcp_servers/sharelife_meta/memory_store/conversation_history/knowledge_base/environment_manifest`).
2. `extension_pack`: extension sections only (`plugins/skills/personas/mcp_servers`).

## Security config keys

1. `profile_pack.signing_key_id`
2. `profile_pack.signing_secret`
3. `profile_pack.trusted_signing_keys`
4. `profile_pack.secrets_encryption_key`
5. `profile_pack.plugin_install.enabled`
6. `profile_pack.plugin_install.command_timeout_seconds`
7. `profile_pack.plugin_install.allowed_command_prefixes`
8. `profile_pack.plugin_install.allow_http_source`
9. `profile_pack.plugin_install.require_success_before_apply`

## Governance metadata in published packs

1. `capability_summary`
2. `compatibility_matrix`
3. `review_evidence`
4. `featured` + admin curation note

## HTTP API surface

1. `POST /api/admin/profile-pack/export`
2. `GET /api/admin/profile-pack/export/download`
3. `GET /api/admin/profile-pack/exports`
4. `POST /api/admin/profile-pack/import`
5. `POST /api/admin/profile-pack/import/from-export`
6. `POST /api/admin/profile-pack/import-and-dryrun`
7. `GET /api/admin/profile-pack/imports`
8. `POST /api/admin/profile-pack/dryrun`
9. `GET /api/admin/profile-pack/plugin-install-plan`
10. `POST /api/admin/profile-pack/plugin-install-confirm`
11. `POST /api/admin/profile-pack/plugin-install-execute`
12. `POST /api/admin/profile-pack/apply`
13. `POST /api/admin/profile-pack/rollback`
14. `POST /api/admin/profile-pack/catalog/featured`
