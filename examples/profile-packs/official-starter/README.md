# Official Starter Profile-Pack Example

This directory ships a reference `bot_profile_pack` in exploded form:

1. `manifest.json`
2. `sections/*.json`

Use it for:

1. Understanding exact pack structure (`manifest + section payloads`).
2. Import/dry-run/apply rehearsal in local environment.
3. Team onboarding baseline for pack authoring conventions.

Create a local zip package from this directory:

```bash
cd examples/profile-packs/official-starter
zip -r profile-official-starter-1.0.0.bot-profile-pack.zip manifest.json sections
```

Then import with dry-run:

```text
/sharelife_profile_import_dryrun examples/profile-packs/official-starter/profile-official-starter-1.0.0.bot-profile-pack.zip profile-plan-official astrbot_core,providers,plugins
```

Notes:

1. `providers.openai.api_key` is intentionally redacted (`<REDACTED>`).
2. `environment_manifest` is included to demonstrate post-migration environment reconfigure hints.
3. Hashes in `manifest.json` match `sections/*.json`.
