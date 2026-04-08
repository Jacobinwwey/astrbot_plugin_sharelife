# 3-minute quickstart

Goal: verify the member-side loop in minutes, then continue into the local WebUI flows.

## 0) Human quick install

```bash
pip install -r requirements.txt
bash scripts/sharelife-init-wizard --yes --output config.generated.yaml
pytest -q && node --test tests/webui/*.js
```

Interactive setup mode:

```bash
bash scripts/sharelife-init-wizard --output config.generated.yaml
```

## 1) AI quick-install prompt (copy once)

```text
Act as a terminal setup agent in repo root `astrbot_plugin_sharelife`. Run exactly: (1) `pip install -r requirements.txt`; (2) `bash scripts/sharelife-init-wizard --yes --output config.generated.yaml`; (3) `pytest -q`; (4) `node --test tests/webui/*.js`. If any step fails, stop and print only: failed step + root cause + exact fix command. If all pass, output: `READY`, generated config path, and the four validation chat commands: `/sharelife_pref`, `/sharelife_market`, `/sharelife_trial community/basic`, `/sharelife_trial_status community/basic`.
```

## 2) Verify in chat

```text
/sharelife_pref
/sharelife_market
/sharelife_trial community/basic
/sharelife_trial_status community/basic
```

Expected result: trial state is explicit and market calls return usable data.

## 3) Verify the member handoff

1. Open the local WebUI with `/sharelife_webui`.
2. Use `/member` or `/market` for protected member actions.
3. Continue with install, upload, or profile-pack submission from the local UI.
4. Keep privileged moderation and recovery flows outside the public docs surface.

## 4) Continue

1. Full walkthrough: [Get Started](/en/tutorials/get-started)
2. Setup details: [Init Wizard + Config Template](/en/how-to/init-wizard-and-config-template)
3. Local runbook: [QUICKSTART.md](https://github.com/Jacobinwwey/astrbot_plugin_sharelife/blob/main/QUICKSTART.md)
