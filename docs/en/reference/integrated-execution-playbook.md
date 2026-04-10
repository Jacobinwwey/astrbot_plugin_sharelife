# Integrated Execution Playbook (UI Refactor x Storage Persistence)

> Date: `2026-04-04`  
> Audience: maintainers and contributors  
> Goal: one delivery track for user-panel refactor and storage/backup rollout

## 1. Current Engineering Truth

### 1.1 Strong baseline

1. Role baseline exists (`member/reviewer/admin`) with route-level guards.
2. WebUI is already modularized (state helpers, i18n, compare/detail modules).
3. Interface + E2E tests already cover key workflows and role boundaries.
4. Market page already has card-first catalog and compare/detail behaviors.

### 1.2 Remaining debt

1. `app.js` is still an orchestration-heavy monolith.
2. User core flows exist but are spread across mixed surfaces.
3. Install/upload options are partially implicit and not normalized cross-page.
4. Long-retention persistence strategy is still thin under constrained local disk.

### 1.3 Incremental progress (`2026-04-07`)

1. `upload_options.replace_existing` is now behaviorally effective: a new submission can retire previous pending submissions for the same user/template.
2. Market submission storage now persists `upload_options` in SQLite (including auto-migration for older tables missing `upload_options_json`).
3. WebUI status vocabulary was aligned to the execution contract by adding localized labels for `queued/running/succeeded/failed/cancelled/stale`, reducing raw status leakage in member/reviewer/admin surfaces.
4. `profile-pack` submit flow now also supports behavioral `replace_existing`: previous pending submissions (same user + same pack) are retired to `replaced`, with audit and response fields (`replaced_submission_ids`, `replaced_submission_count`).
5. Template submit now supports idempotent replay with `upload_options.idempotency_key` (or `Idempotency-Key` header at WebUI route level): retried requests return the existing submission instead of duplicating records.
6. Idempotency scope conflicts are now rejected deterministically (`idempotency_key_conflict`) when the same key is reused for a different template/version scope.
7. `profile-pack` submit now has the same idempotency model (`submit_options.idempotency_key` + header pass-through) with replay and conflict audit events.

### 1.4 Incremental progress (`2026-04-10`)

1. Member page now has a hard-boundary serving model: `/member` prefers `member.safe.html` and keeps admin/reviewer controls out of the member source template.
2. Runtime still performs post-auth defensive pruning for privileged scopes, so source-template boundary and runtime boundary are both enforced.
3. WebUI binding decomposition moved to a shared slice registry (`app_binding_slices.js`) and `bindButtons()` is now an orchestration shell over slice-level binders.
4. Slice-surface and route-surface meta tests were added to prevent regressions in script order, boundary serving, and member DOM safety.

### 1.5 Incremental progress (`2026-04-10`, observability pass)

1. Public-market autopublish now emits deterministic pipeline trace metadata (`pipeline_trace_id` + stable stage event ids) across decision/publish/snapshot/backup-handoff stages.
2. Entry payload and API publish response now carry the same pipeline trace envelope to support deterministic cross-system correlation.
3. Audit chain adds explicit `profile_pack.public_market.snapshot_rebuilt` and `profile_pack.public_market.backup_handoff` events for operator-facing lifecycle visibility.
4. Public-market backup manifest now includes snapshot-level pipeline summary fields (`pipeline_trace_count`, latest trace and stage events).

### 1.6 Incremental progress (`2026-04-10`, readability gate pass)

1. A deterministic meta-level contrast guard was added for core WebUI theme tokens (member + market critical text/background pairs).
2. Contrast regressions on key semantic tokens now fail CI before merge.

### 1.7 Incremental progress (`2026-04-10`, anonymous-member authz consistency pass)

1. Anonymous-member default API allowlist was aligned with published capability surfaces by adding package-download and notifications read endpoints.
2. Interface tests now pin both sides of the contract: default allowlist permits these reads, and explicit allowlist override still blocks them.

## 2. Cross-Plan Decisions

### 2.1 Unified state vocabulary

Installation/task and backup/restore jobs must share deterministic statuses:

`queued | running | succeeded | failed | cancelled | stale`

### 2.2 Contract-first sequence

To avoid drift from parallel rewrites:

1. Freeze contracts and payloads.
2. Implement backend compatibility layer.
3. Bind UI to contracts.
4. Replace layout shell last.

### 2.3 Audit as hard requirement

All storage actions and install option mutations must write audit events with request-id + actor-role.

## 3. Execution Phases

### Phase A - Contract freeze

1. Member installation endpoints + payload option extensions.
2. Storage job and restore endpoint contracts.
3. Docs-first spec updates and meta tests.

### Phase B - Backend first

1. Installation list/refresh services.
2. Payload option validation/defaulting.
3. Storage policy/job/restore state model.
4. Restic+rclone adapter behind a service boundary.

### Phase C - Frontend integration

1. Apply Stitch-generated shell with runtime ID preservation.
2. Keep top search + locale + `Import local AstrBot config` as first-class actions.
3. Unify upload/install option panel behavior in `/member` and `/market`.
4. Hydrate task and installation states from new endpoints.

### Phase D - Hardening

1. Full interface/unit/E2E matrix.
2. Failure injection:
   - API `429/403/500`
   - backup budget reached
   - restore checksum mismatch
3. Audit and i18n completeness check.

## 4. Tradeoffs

1. Vanilla enhancement now vs full framework migration  
   - Chosen: vanilla enhancement now to preserve compatibility and test anchors.
2. Google Drive as cold backup vs object storage replacement  
   - Chosen: cold backup only, never hot serving.
3. Big-bang delivery vs layered rollout  
   - Chosen: layered rollout for lower blast radius and easier rollback.

## 5. Pitfalls to Avoid

1. Directly replacing runtime IDs with generated markup.
2. Adding new controls without capability mapping.
3. Uploading fragmented raw directories to Drive.
4. Marking backup success without restore-prepare verification.
5. Running backup jobs without disk watermark guard.

## 6. Completion Gates

1. Full test suite green, including WebUI E2E.
2. No RBAC regression on restricted routes.
3. Member and market option behavior is equivalent.
4. Backup/restore actions leave deterministic state transitions and audit trails.
