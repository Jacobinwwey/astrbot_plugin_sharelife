# Get started

This tutorial walks through the minimum local workflow for `sharelife`.

## Fast path

```bash
bash scripts/sharelife-init-wizard --yes --output config.generated.yaml
```

Then in chat:

```text
/sharelife_pref
/sharelife_market
/sharelife_trial community/basic
/sharelife_trial_status community/basic
```

If this works, continue below.
One-screen version: [3-Minute QuickStart](/en/tutorials/3-minute-quickstart)

## Prerequisites

1. Python 3.12
2. AstrBot runtime
3. `pip install -r requirements.txt`

Optional: run `/sharelife_webui` to open the standalone page.

## Step 1: check default preferences

```text
/sharelife_pref
```

Expected:

- `execution_mode=subagent_driven`
- `observe_task_details=off`

## Step 2: switch execution mode

```text
/sharelife_mode inline_execution
```

Run `/sharelife_pref` again and confirm the value changed.

## Step 3: enable detail observability

```text
/sharelife_observe on
```

Run `/sharelife_pref` and verify `observe_task_details=on`.

## Step 4: trial state and local install handoff

Member actions:

```text
/sharelife_trial community/basic
/sharelife_trial_status community/basic
```

You should get one of `not_started`, `active`, `expired` plus TTL fields.

Then continue with the local member install flow:

```text
/sharelife_market
/sharelife_prompt community/basic
/sharelife_package community/basic
```

Use `/member` or `/market` in the local WebUI for the actual install controls:

- `preflight`
- `force_reinstall`
- `source_preference=auto|uploaded_submission|generated`

## Step 5: upload and community submission
Template upload in the local WebUI:

1. Open `/member` or `/market`.
2. Choose a template package or generated package output.
3. Direct package upload is capped at `20 MiB`.
4. Available upload controls:
   - `scan_mode=strict|balanced`
   - `visibility=community|private`
   - `replace_existing=true|false`
5. Inspect the result from `My Submissions`.

Profile-pack community submission:

1. Prepare or export a local artifact and copy its `artifact_id`.
2. Submit it from `/member` or `/market`.
3. Available submit controls:
   - `pack_type`
   - `selected_sections`
   - `redaction_mode`
   - `replace_existing`
4. Inspect owner-scoped status and export download from `My Profile-Pack Submissions`.
