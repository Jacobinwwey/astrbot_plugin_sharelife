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

## Step 4: trial state and admin apply flow

Member actions:

```text
/sharelife_trial community/basic
/sharelife_trial_status community/basic
```

You should get one of `not_started`, `active`, `expired` plus TTL fields.
Repeated trial on the same template enters the admin queue.

Admin queue actions:

```text
/sharelife_retry_list
/sharelife_retry_lock <request_id>
/sharelife_retry_decide <request_id> approve <request_version> <lock_version>
```

Admin apply flow:

```text
/sharelife_dryrun community/basic 1.0.0
/sharelife_apply <plan_id>
/sharelife_rollback <plan_id>
```

If `plan_id` is omitted, Sharelife derives one like `plan-community-basic`.

## Step 5: community submit and install

Member submit:

```text
/sharelife_submit community/basic 1.0.0
```

Admin moderation:

```text
/sharelife_submission_list
/sharelife_submission_decide <submission_id> approve
```

Member install path:

```text
/sharelife_market
/sharelife_install community/basic
/sharelife_prompt community/basic
/sharelife_package community/basic
```

Admin audit check:

```text
/sharelife_audit 20
```
