# AstrBot Plugin: Sharelife

<p align="center">
  <img src="assets/logo/logo.png" alt="Sharelife Logo" width="120" />
</p>

<p align="center">
  <a href="https://github.com/Jacobinwwey/astrbot_plugin_sharelife/stargazers"><img src="https://img.shields.io/github/stars/Jacobinwwey/astrbot_plugin_sharelife?style=flat-square" alt="Stars"></a>
  <a href="https://github.com/Jacobinwwey/astrbot_plugin_sharelife/network/members"><img src="https://img.shields.io/github/forks/Jacobinwwey/astrbot_plugin_sharelife?style=flat-square" alt="Forks"></a>
  <a href="https://github.com/Jacobinwwey/astrbot_plugin_sharelife/issues"><img src="https://img.shields.io/github/issues/Jacobinwwey/astrbot_plugin_sharelife?style=flat-square" alt="Issues"></a>
  <a href="https://github.com/Jacobinwwey/astrbot_plugin_sharelife/releases"><img src="https://img.shields.io/github/v/release/Jacobinwwey/astrbot_plugin_sharelife?style=flat-square" alt="Release"></a>
  <a href="https://github.com/Jacobinwwey/astrbot_plugin_sharelife/pulls"><img src="https://img.shields.io/badge/PRs-welcome-brightgreen?style=flat-square" alt="PRs Welcome"></a>
</p>

> 我们很难定义记忆与怀念，也许它们就是生命的印迹。Sharelife 希望陪伴你体验每一段珍贵的生命，消融所有界限的枷锁。（无损接入任意 bot 与设置）

`sharelife` is an AstrBot plugin for secure, high-fidelity Agent/Bot setup sharing.
It gives you a practical workflow to trial community templates, use guarded review handoff, and replicate bot configurations with rollback safety.

Language Switch:
- English Docs: [GitHub Pages EN](https://jacobinwwey.github.io/astrbot_plugin_sharelife/en/)
- 中文文档: [GitHub Pages ZH](https://jacobinwwey.github.io/astrbot_plugin_sharelife/zh/)
- 日本語ドキュメント: [GitHub Pages JA](https://jacobinwwey.github.io/astrbot_plugin_sharelife/ja/)

## Why Sharelife

- Community template market with safe trial before apply.
- High-fidelity replication (`bot_profile_pack` / `extension_pack`) with section-level diff and rollback.
- Optional stateful migration (`memory_store` / `conversation_history` / `knowledge_base`) with explicit environment reconfigure notices (`environment_manifest`).
- Risk-aware governance with labels, warning flags, prompt-injection detection, and audit timeline.
- Standalone WebUI (`/`, `/member`, `/market`) with i18n (`en-US` / `zh-CN` / `ja-JP`).
- Plugin-install execution guard (`plan -> confirm -> execute`) with explicit privileged control.

## 3-Minute Onboarding

Human quick install (minimal):

```bash
pip install -r requirements.txt
bash scripts/sharelife-init-wizard --yes --output config.generated.yaml
pytest -q && node --test tests/webui/*.js
```

Useful wizard flags for public/member deployment:

```text
--webui-auth true
--member-password "<member_password>"
--allow-anonymous-member true
--anonymous-member-user-id "webui-user"
--anonymous-member-allowlist "POST /api/trial,GET /api/trial/status,POST /api/templates/install,GET /api/member/installations,POST /api/member/installations/refresh,GET /api/preferences,POST /api/preferences/mode,POST /api/preferences/observe"
```

Privileged auth bootstrap and secret-handling runbooks stay in private operator docs.

Then verify in chat:

```text
/sharelife_pref
/sharelife_market
/sharelife_trial community/basic
/sharelife_trial_status community/basic
```

AI quick-install prompt (copy once):

```text
Act as a terminal setup agent in repo root `astrbot_plugin_sharelife`. Run exactly: (1) `pip install -r requirements.txt`; (2) `bash scripts/sharelife-init-wizard --yes --output config.generated.yaml`; (3) `pytest -q`; (4) `node --test tests/webui/*.js`. If any step fails, stop and print only: failed step + root cause + exact fix command. If all pass, output: `READY`, generated config path, and the four validation chat commands: `/sharelife_pref`, `/sharelife_market`, `/sharelife_trial community/basic`, `/sharelife_trial_status community/basic`.
```

If this passes, continue with local install, upload, and profile-pack flow in [QUICKSTART.md](QUICKSTART.md) or the docs site.

## Init Wizard And Config Template

Interactive wizard:

```bash
bash scripts/sharelife-init-wizard --output config.generated.yaml
```

Reference template:

```text
config.template.yaml
```

The template keeps provider, WebUI auth, profile-pack signing/encryption, and plugin-install execution gates close to real config keys.

## Common Commands

User-side:
- `/sharelife_market`
- `/sharelife_trial <template_id>`
- `/sharelife_trial_status <template_id>`
- `/sharelife_submit <template_id> <version>`
- `/sharelife_webui`

<details>
<summary><b>Advanced Profile-Pack Commands</b></summary>

- `/sharelife_profile_import_dryrun <artifact_id_or_zip_path> [plan_id] [sections_csv]`
- `/sharelife_profile_import_dryrun_latest [plan_id] [sections_csv]`
- `/sharelife_profile_plugins <import_id>`
- `/sharelife_profile_plugins_confirm <import_id> [plugins_csv]`
- `/sharelife_profile_plugins_install <import_id> [plugins_csv] [dry_run]`

</details>

## WebUI

Default local URL:
- `http://127.0.0.1:8106`
- Market page: `http://127.0.0.1:8106/market`

Privileged auth boundary:
- Privileged auth procedures and secret-backup steps are intentionally excluded from the public README and docs site.
- Maintain those runbooks locally under `docs-private/` or in a separate internal repository.

WebUI capability highlights:
- Trial Status panel for TTL and remaining time.
- Local installation management with reinstall/uninstall handoff.
- Template and profile-pack market browsing, compare, upload, and owner-scoped submission visibility.
- Built-in profile-pack reference sample: `profile/official-starter` (`bot_profile_pack`, featured).
- Public downloadable market packs are published under `docs/public/market/` and served on GitHub Pages after push to `main`.

Standalone local AstrBot import defaults:
- Host-local AstrBot config import is disabled by default in standalone mode.
- Enable explicitly when needed:
  - CLI: `--enable-local-astrbot-import`
  - Env: `SHARELIFE_ENABLE_LOCAL_ASTRBOT_IMPORT=1`
- Optional anonymous local import (only when your deployment policy allows it):
  - CLI: `--allow-anonymous-local-astrbot-import`
  - Env: `SHARELIFE_ALLOW_ANONYMOUS_LOCAL_ASTRBOT_IMPORT=1`
- Optional local config path hints for host auto-detection:
  - `SHARELIFE_ASTRBOT_CONFIG_PATH=/path/to/cmd_config.json`
  - `SHARELIFE_ASTRBOT_CONFIG_PATH=/path/a:/path/b` (Windows uses `;`)
  - `SHARELIFE_ASTRBOT_SEARCH_ROOTS=/path/root-a:/path/root-b` (Windows uses `;`)
  - `SHARELIFE_ASTRBOT_HOME=/path/to/astrbot`

Reference sample pack (for users/developers):
- Exploded sample pack: `examples/profile-packs/official-starter/`
- Manifest file: `examples/profile-packs/official-starter/manifest.json`
- Section payloads: `examples/profile-packs/official-starter/sections/*.json`

Create importable zip locally:

```bash
cd examples/profile-packs/official-starter
zip -r profile-official-starter-1.0.0.bot-profile-pack.zip manifest.json sections
```

Optional observability stack (Prometheus + Grafana):

```bash
docker compose -f docker-compose.yml -f docker-compose.observability.yml up -d --build
bash scripts/smoke_observability_stack.sh
```

Smoke diagnostics are written to `output/ops-smoke` and uploaded by the `ops-smoke` GitHub Actions workflow.
The workflow also publishes `output/ops-smoke/triage.md` into Job Summary and emits signal/action annotations from `output/ops-smoke/triage.json`.
Artifacts are privacy-redacted by default (`SHARELIFE_SMOKE_PRIVACY_MODE=strict`) via `scripts/redact_ops_artifacts.py`.
Use `--privacy-mode off` only for isolated local debugging.
If `output/ops-smoke` is not writable, smoke diagnostics automatically fall back to `/tmp/sharelife-ops-smoke.*` and the resolved path is written to `.ops-smoke-last-artifacts-path`.
Smoke also runs preflight checks for container-name conflicts and required host ports (`8106/9090/3000`) before compose startup.
When those default ports are busy, smoke can auto-select free host ports (`SHARELIFE_SMOKE_AUTO_PORTS=1`) and records requested/effective ports in `summary.txt`.
Before compose startup, smoke also pre-creates `output/docker-data/prometheus` and `output/docker-data/grafana` and applies writable permissions for non-root container users to avoid Prometheus/Grafana healthcheck stalls in CI/local Linux environments.

Bundled assets live in:
- `ops/prometheus/sharelife-webui-alerts.rules.yml`
- `ops/prometheus/prometheus.sample.yml`
- `ops/grafana/dashboards/sharelife-webui-dashboard.json`

## Documentation

Docs site:
- `https://jacobinwwey.github.io/astrbot_plugin_sharelife/`

Quick links:

| Topic | English | 中文 | 日本語 |
|---|---|---|---|
| 3-Minute QuickStart | [3-Minute QuickStart](docs/en/tutorials/3-minute-quickstart.md) | [3 分钟快速跑通](docs/zh/tutorials/3-minute-quickstart.md) | [3分クイックスタート](docs/ja/tutorials/3-minute-quickstart.md) |
| Get Started | [Get Started](docs/en/tutorials/get-started.md) | [快速开始](docs/zh/tutorials/get-started.md) | [はじめに](docs/ja/tutorials/get-started.md) |
| Init Wizard + Config | [Init Wizard + Config Template](docs/en/how-to/init-wizard-and-config-template.md) | [初始化向导与配置模板](docs/zh/how-to/init-wizard-and-config-template.md) | [初期化ウィザードと設定テンプレート](docs/ja/how-to/init-wizard-and-config-template.md) |
| Standalone WebUI | [WebUI Guide](docs/en/how-to/webui-page.md) | [WebUI 使用](docs/zh/how-to/webui-page.md) | [WebUI ガイド](docs/ja/how-to/webui-page.md) |
| Bot Profile Pack | [Bot Profile Pack](docs/en/how-to/bot-profile-pack.md) | [Bot Profile Pack](docs/zh/how-to/bot-profile-pack.md) | [Bot Profile Pack](docs/ja/how-to/bot-profile-pack.md) |
| Profile Migration Scope | [Migration Scope](docs/en/how-to/profile-pack-migration-scope.md) | [迁移范围真值表](docs/zh/how-to/profile-pack-migration-scope.md) | [移行スコープ](docs/ja/how-to/profile-pack-migration-scope.md) |
| Public Market Hub | [Public Market Hub](docs/en/how-to/market-public-hub.md) | [市场只读公开页](docs/zh/how-to/market-public-hub.md) | [公開マーケット](docs/ja/how-to/market-public-hub.md) |
| API Reference | [API v1](docs/en/reference/api-v1.md) | [API v1](docs/zh/reference/api-v1.md) | [API v1](docs/ja/reference/api-v1.md) |

## Community And Contributing

Want to share your own setup?
1. Build your template/package locally.
2. Submit via `/sharelife_submit <template_id> <version>` (or WebUI submit flow).
3. The submission enters the gated review queue.

Reviewer access is invite-only.
- If you want to become a reviewer, contact `Jacobinwwey` first.

Contribution channels:
- Issues: [Report bugs / request features](https://github.com/Jacobinwwey/astrbot_plugin_sharelife/issues)
- Pull Requests: [Open a PR](https://github.com/Jacobinwwey/astrbot_plugin_sharelife/pulls)
- Contributing Guide: [CONTRIBUTING.md](CONTRIBUTING.md)

## For Developers

Common commands:

```bash
pytest -q
node --test tests/webui/*.js
python3 scripts/validate_protocol_examples.py
bash scripts/sharelife-hot-reload --watch . --cmd "python3 -m pytest -q" --dry-run
```

Detailed developer references:
- [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)

Security note:
- Do not commit publish tokens or any secret material.
- Community-first moderation prioritizes risk labeling and visibility over aggressive auto-rejection, except for clearly malicious configurations.
