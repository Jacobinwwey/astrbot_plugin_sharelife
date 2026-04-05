# Contributing Guide

This project is community-first.  
If you want to contribute template packs, profile packs, docs, or code changes, follow this guide.

## 1. Template/Pack Submission Flow

### 1.1 Scope

Supported submission types now:

1. Template submission (`/sharelife_submit`)
2. `bot_profile_pack` submission
3. `extension_pack` submission

For profile-pack migration boundaries, read:

1. `docs/zh/how-to/profile-pack-migration-scope.md`
2. `docs/en/how-to/profile-pack-migration-scope.md`
3. `docs/ja/how-to/profile-pack-migration-scope.md`

### 1.2 Recommended contributor workflow

1. Prepare package locally (template/package/profile-pack).
2. Validate metadata and compatibility (`astrbot_version`, `plugin_compat`, review labels).
3. Run local dry-run before community submission.
4. Submit from command or WebUI.
5. Wait for admin review and risk labeling.

### 1.3 Command examples

Template:

```text
/sharelife_submit <template_id> <version>
```

Profile pack export/import/dry-run:

```text
/sharelife_profile_export profile/basic 1.0.0 exclude_secrets astrbot_core,providers,plugins "" "" bot_profile_pack
/sharelife_profile_import <artifact_id> --dryrun --plan-id profile-plan-basic --sections plugins,providers
```

Profile pack community submission:

```text
# In WebUI Profile Pack Market panel
# 1) submit artifact_id
# 2) admin review
# 3) publish to catalog
```

### 1.4 Safety requirements for submissions

1. Do not include plaintext secrets.
2. Prefer `exclude_secrets` unless encryption policy is explicitly configured.
3. Keep warning flags and review labels truthful; do not hide high-risk behavior.
4. If plugin installation is needed, provide explicit source/version/hash/install metadata.

## 2. Pull Request Rules

### 2.1 Branch and commit

1. Use feature/fix/docs style branch names.
2. Keep commits focused and reviewable.
3. Do not mix unrelated refactors with feature changes.

### 2.2 PR description minimum fields

Every PR should include:

1. Problem statement
2. What changed (behavioral)
3. Risk and compatibility impact
4. Test evidence (commands + pass result)
5. Docs/i18n updates (if UI/API changed)

### 2.3 Must-update policy

When you change one of these surfaces, update docs and tests in the same PR:

1. Command/API surface
2. WebUI text/UI locale keys
3. Profile-pack schema/section behavior
4. Governance and moderation behavior

## 3. Minimal Acceptance Checklist

Before opening PR, run and verify:

```bash
pytest -q
node --test tests/webui/*.js
npm run docs:build --prefix docs
```

Required checklist:

1. [ ] Python tests pass
2. [ ] WebUI JS tests pass
3. [ ] Docs build passes
4. [ ] New UI strings are i18n-keyed and translated for `en-US` / `zh-CN` / `ja-JP`
5. [ ] If migration behavior changed, migration-scope docs are updated
6. [ ] If profile-pack behavior changed, dry-run/apply/rollback path has test coverage
7. [ ] No secret/token leakage in code, docs, examples, or CI config

## 4. Reviewer Focus

Reviewers prioritize:

1. Behavior correctness over style-only changes
2. Security and governance regressions
3. i18n completeness and UI consistency
4. Backward compatibility for command/API payloads
