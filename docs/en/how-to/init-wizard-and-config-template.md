# Init wizard and config template

This page turns setup docs into executable onboarding.

## Why this page exists

1. Reduce first-run drift across machines.
2. Shorten time-to-value.
3. Keep config guidance close to the config itself.

## Run the wizard

Interactive:

```bash
bash scripts/sharelife-init-wizard --output config.generated.yaml
```

Non-interactive defaults:

```bash
bash scripts/sharelife-init-wizard --yes --output config.generated.yaml
```

Common flags:

1. `--provider openai|claude|deepseek`
2. `--api-key <value>`
3. `--preset standard_qa|sharelife_companion|research_safe`
4. `--webui-auth true|false`
5. `--allow-anonymous-member true|false`
6. `--anonymous-member-user-id <value>`
7. `--anonymous-member-allowlist "POST /api/trial,GET /api/trial/status,..."`
8. `--enable-plugin-install-exec true|false`
9. `--print-only`

## Use the config template

`config.template.yaml` is the baseline reference.

It includes:

1. provider/model blocks
2. WebUI auth and rate-limit settings
3. profile-pack signing/encryption fields
4. plugin-install guardrails (default off, allowlist, timeout)
5. anonymous member mode defaults and endpoint allowlist override fields

## Team workflow that works

1. Keep `config.template.yaml` in git.
2. Generate local `config.generated.yaml` from wizard.
3. Keep real secrets in local/private files only.
4. Smoke test with `/sharelife_pref` and `/sharelife_trial_status` after config changes.
