# Sharelife QuickStart (3 Minutes)

Goal: get `sharelife` running quickly, verify the bot loop, then move to profile-pack replication safely.

## 1. Install

```bash
pip install -r requirements.txt
```

## 2. Generate Config (Wizard)

```bash
bash scripts/sharelife-init-wizard --output config.generated.yaml
```

If you want defaults without prompts:

```bash
bash scripts/sharelife-init-wizard --yes --output config.generated.yaml
```

If you want auth enabled plus explicit anonymous-member policy:

```bash
bash scripts/sharelife-init-wizard --yes \
  --webui-auth true \
  --member-password "<member_password>" \
  --admin-password "<admin_password_12plus>" \
  --allow-anonymous-member true \
  --anonymous-member-user-id "webui-user" \
  --anonymous-member-allowlist "POST /api/trial,GET /api/trial/status,POST /api/templates/install,GET /api/member/installations,POST /api/member/installations/refresh,GET /api/preferences,POST /api/preferences/mode,POST /api/preferences/observe" \
  --output config.generated.yaml
```

## 3. Start AstrBot + Sharelife

Load the plugin with your generated config and enter chat:

```text
/sharelife_pref
/sharelife_market
/sharelife_trial community/basic
/sharelife_trial_status community/basic
```

Expected: you should see explicit trial state (`active/not_started/expired`) and no permission errors for member-safe commands.

## 4. Admin Strict Apply Loop

```text
/sharelife_dryrun community/basic 1.0.0
/sharelife_apply <plan_id>
/sharelife_rollback <plan_id>
```

## 5. Profile-Pack Replication Loop

```text
/sharelife_profile_export profile/basic 1.0.0
/sharelife_profile_import <artifact_id> --dryrun --plan-id profile-plan-basic --sections plugins,providers
```

If plugin section requires install confirmation:

```text
/sharelife_profile_plugins <import_id>
/sharelife_profile_plugins_confirm <import_id> [plugins_csv]
/sharelife_profile_plugins_install <import_id> [plugins_csv] [dry_run]
```

Notes:

1. Plugin-install execution is disabled by default; enable it in `profile_pack.plugin_install.enabled`.
2. Use `config.template.yaml` as the self-documented baseline for all config fields.
3. Standalone local AstrBot import is disabled by default. Enable explicitly when needed:
   - `python3 scripts/run_sharelife_webui_standalone.py --enable-local-astrbot-import`
   - or `SHARELIFE_ENABLE_LOCAL_ASTRBOT_IMPORT=1`
4. If host auto-detection cannot find your local `cmd_config.json`, set one of:
   - `SHARELIFE_ASTRBOT_CONFIG_PATH=/absolute/path/to/cmd_config.json`
   - `SHARELIFE_ASTRBOT_SEARCH_ROOTS=/path/root-a:/path/root-b` (Windows uses `;`)
