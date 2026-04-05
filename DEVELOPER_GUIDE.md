# Sharelife Developer Guide

This guide contains development and maintenance details intentionally kept out of `README.md`.
Use it when you are working on architecture, command surface, CI, release, and documentation delivery.

## Architecture

Codebase boundaries:

- `sharelife/interfaces`: API adapters, WebUI HTTP server, AstrBot integration entry points
- `sharelife/application`: orchestration services (market, package, queue, trial, preferences, audit)
- `sharelife/domain`: policies and domain models
- `sharelife/infrastructure`: notifier/runtime bridge/persistence-facing helpers

Primary entry points:

- runtime: `main.py`
- command/API orchestration: `sharelife/interfaces/api_v1.py`
- HTTP API adapter: `sharelife/interfaces/web_api_v1.py`
- standalone web server: `sharelife/interfaces/webui_server.py`

Migration scope reference (shared with users):

- `docs/en/how-to/profile-pack-migration-scope.md`
- `docs/zh/how-to/profile-pack-migration-scope.md`
- `docs/ja/how-to/profile-pack-migration-scope.md`

## Full Command Surface

User-facing:

- `/sharelife_pref`
- `/sharelife_webui`
- `/sharelife_mode <subagent_driven|inline_execution>`
- `/sharelife_observe <on|off>`
- `/sharelife_submit <template_id> <version>`
- `/sharelife_market`
- `/sharelife_trial <template_id>`
- `/sharelife_trial_status <template_id>`
- `/sharelife_install <template_id>`
- `/sharelife_prompt <template_id>`
- `/sharelife_package <template_id>`

Admin-facing:

- `/sharelife_submission_list [status]`
- `/sharelife_submission_decide <submission_id> <approve|reject>`
- `/sharelife_retry_list`
- `/sharelife_retry_lock <request_id> [force] [reason]`
- `/sharelife_retry_decide <request_id> <approve|reject> [request_version] [lock_version]`
- `/sharelife_dryrun <template_id> [version] [plan_id]`
- `/sharelife_apply <plan_id>`
- `/sharelife_rollback <plan_id>`
- `/sharelife_audit [limit]`
- `/sharelife_profile_export [pack_id] [version] [redaction_mode] [sections_csv] [mask_paths_csv] [drop_paths_csv] [pack_type]`
- `/sharelife_profile_exports [limit]`
- `/sharelife_profile_import <artifact_id_or_zip_path> [--dryrun] [--plan-id <plan_id>] [--sections <sections_csv>]`
- `/sharelife_profile_import_dryrun <artifact_id_or_zip_path> [plan_id] [sections_csv]`
- `/sharelife_profile_import_dryrun_latest [plan_id] [sections_csv]`
- `/sharelife_profile_imports [limit]`
- `/sharelife_profile_plugins <import_id>`
- `/sharelife_profile_plugins_confirm <import_id> [plugins_csv]`
- `/sharelife_profile_plugins_install <import_id> [plugins_csv] [dry_run]`

## WebUI Details

Default local URL:

- `http://127.0.0.1:8106`
- `http://127.0.0.1:8106/market`

Routes:

- `/` full console
- `/member` member-focused console
- `/admin` admin-focused console
- `/market` standalone market page

Key capability groups:

- Trial Status and Admin Apply Workflow panels
- moderation and risk visualization
- template/profile-pack catalog and compare flows
- plugin-install guarded flow (`plan -> confirm -> execute`)
- audit/notification panels
- locale switch (`en-US` / `zh-CN` / `ja-JP`) via `localStorage["sharelife.uiLocale"]`

Recommended auth hardening config:

```json
{
  "webui": {
    "auth": {
      "member_password": "",
      "admin_password": "",
      "token_ttl_seconds": 7200,
      "allow_query_token": false,
      "login_rate_limit_window_seconds": 60,
      "login_rate_limit_max_attempts": 10
    },
    "cors": {
      "allow_origins": ""
    }
  },
  "profile_pack": {
    "signing_key_id": "default",
    "signing_secret": "",
    "trusted_signing_keys": {},
    "secrets_encryption_key": "",
    "plugin_install": {
      "enabled": false,
      "command_timeout_seconds": 180,
      "allowed_command_prefixes": "astrbot,pip,uv,npm,pnpm",
      "allow_http_source": false,
      "require_success_before_apply": false
    }
  }
}
```

## Bundled Catalog Baseline

Shipped from `templates/index.json`:

- `community/basic@1.0.0`
- `community/research-safe@1.0.0`
- `community/writing-polish@1.0.0`
- `community/coding-review@1.0.0`
- `community/ops-guarded@1.0.0`
- `community/support-care@1.0.0`

Behavior:

- available immediately after plugin startup
- includes `category`, `tags`, `maintainer`, `source_channel`
- includes aggregate `engagement` fields
- community-approved same `template_id` version takes precedence

## Documentation Delivery (GitHub Pages)

Public site:

- `https://jacobinwwey.github.io/astrbot_plugin_sharelife/`

Primary workflow:

- file: `.github/workflows/deploy-docs-github-pages.yml`
- workflow name: `deploy-docs-github-pages`
- ops smoke workflow: `.github/workflows/ops-smoke.yml` (`workflow_dispatch` + weekly schedule)

Publish behavior:

1. qualifying push to `main` triggers build and deploy
2. path filter includes `docs/**`, `templates/**`, `scripts/build_market_snapshot.py`, and workflow file
3. local parity build: `make docs-build-github-pages`

Manual rollback:

1. run workflow via `workflow_dispatch`
2. set `git_ref` to known-good commit/tag/branch
3. re-run deployment

Docs scripts:

- `npm run docs:prepare:market --prefix docs`
- `npm run docs:dev --prefix docs`
- `npm run docs:build --prefix docs`
- `make docs-build-github-pages`

## Development Workflow

Core local loop:

```bash
pytest -q
node --test tests/webui/*.js
python3 scripts/validate_protocol_examples.py
python3 scripts/validate_ops_assets.py
bash scripts/run_webui_e2e.sh
bash scripts/smoke_observability_stack.sh --no-build
```

Optional observability stack bootstrap:

```bash
docker compose -f docker-compose.yml -f docker-compose.observability.yml up -d --build
bash scripts/smoke_observability_stack.sh --artifacts-dir output/ops-smoke
make ops-triage
```

The `ops-smoke` workflow uploads `output/ops-smoke` as diagnostic artifact on every run (success/failure).
It also publishes `output/ops-smoke/triage.md` to GitHub Actions Job Summary and emits annotations from `output/ops-smoke/triage.json`.
By default, diagnostics are privacy-redacted (`SHARELIFE_SMOKE_PRIVACY_MODE=strict`) through `scripts/redact_ops_artifacts.py`.
Use `--privacy-mode off` only when debugging in an isolated local environment.
If `output/ops-smoke` is not writable, smoke automatically falls back to `/tmp/sharelife-ops-smoke.*`; the effective path is persisted to `.ops-smoke-last-artifacts-path`.
Smoke preflight blocks known bad startup conditions (container-name conflicts and occupied host ports 8106/9090/3000) before compose up.
With `SHARELIFE_SMOKE_AUTO_PORTS=1` (default), smoke can auto-pick free host ports and reports requested/effective ports in diagnostics summary.
Smoke also prepares `output/docker-data/prometheus` and `output/docker-data/grafana` with writable permissions so non-root Prometheus/Grafana containers can pass health checks in CI/local Linux hosts.

Helpers:

```bash
bash scripts/create-astrbot-plugin --name astrbot_plugin_demo --output output
bash scripts/sharelife-init-wizard --yes --output config.generated.yaml
bash scripts/sharelife-hot-reload --watch . --cmd "python3 -m pytest -q" --dry-run
```

## Persistence

Data is persisted under plugin data directory:

- preferences/trials/retry queue/notifications/market records/audit events
- generated and uploaded packages under `packages/`
- cached registry payloads under `registry/`

## Security Notes

- never commit publish tokens or any secret material
- plugin install execution is disabled by default
- community-first moderation favors risk labeling and transparency over aggressive auto-rejection, except clearly malicious configurations
