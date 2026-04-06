# Sharelife Integrated Execution Playbook (UI Refactor × Storage Persistence)

Date: 2026-04-04  
Audience: maintainers and contributors  
Goal: converge UI workflow refactor and storage/backup architecture into one implementable track.

## 1. Current project truth (engineering view)

### 1.1 What is already strong

1. RBAC baseline is in place (`member/reviewer/admin`) with route-level enforcement and capability gating.
2. WebUI has mature module split (view-model helpers, state helpers, i18n, compare/detail renderers).
3. E2E and interface tests already cover key user workflows and role boundaries.
4. Market page already supports catalog cards, compare drawer, URL-synced local filters.

### 1.2 Structural debt that still matters

1. `app.js` is still a large orchestration monolith; feature cohesion is module-based but not domain-bounded.
2. User-facing core workflows (search/install/upload/download) are present but spread across mixed surfaces.
3. Install/upload option modeling is partially implicit in payloads; not a normalized cross-page contract yet.
4. Local persistence/backup strategy is operationally thin for long retention under constrained disk.

## 2. Cross-analysis: where the two big plans intersect

### 2.1 Shared boundary: “state truth”

- UI refactor needs deterministic installation/task state.
- Storage plan introduces backup/restore/job states that are operationally meaningful to UI.
- Therefore, installation/task and backup/job must share the same typed status semantics.

Decision:
- Add a unified status vocabulary (`queued/running/succeeded/failed/cancelled/stale`) across:
  - installation rows
  - download/upload task queues
  - backup jobs and restore jobs.

### 2.2 Shared risk: accidental complexity from parallel rewrites

- Rewriting UI IA and introducing storage orchestration simultaneously can create regressions if API contracts drift.

Decision:
- Sequence by contract-first:
  1. finalize endpoint and payload specs
  2. implement backend compatibility layer
  3. wire UI
  4. only then replace layout shell.

### 2.3 Shared operational requirement: auditability

- Review/admin safety model depends on clear traceability.
- Backup/restore actions are high-risk operations.

Decision:
- All new storage and installation option mutations must emit audit events with request ID and actor role.

## 3. Implementation strategy (single execution track)

### Phase A — Contract freeze

1. Freeze new interface contracts:
   - `GET /api/member/installations`
   - `POST /api/member/installations/refresh`
   - `install_options` / `upload_options` / `submit_options` payload extensions
   - admin storage endpoints (job + restore lifecycle)
2. Add docs-first specs and meta tests before code changes.

### Phase B — Backend first

1. Implement installation list/refresh services.
2. Implement optional payload fields with strict defaults and validation.
3. Introduce backup job state tables and policy tables.
4. Integrate restic+rclone execution adapter behind service boundary.

### Phase C — Frontend integration

1. Build new member/market shell from Stitch output, but preserve runtime ID anchors.
2. Bind top search + locale + `刷新本地已有配置` as stable primary actions.
3. Add unified option panels for upload/install in both `/member` and `/market`.
4. Add task queue rendering and status hydration from backend endpoints.

### Phase D — Hardening

1. Run full interface + webui unit + e2e matrix.
2. Execute failure injection:
   - API 429/403/500
   - backup upload budget hit
   - restore prepare checksum mismatch
3. Verify audit completeness and i18n completeness.

## 4. Tradeoffs and selected positions

1. Vanilla + modular enhancement vs full framework migration  
   - Chosen: Vanilla enhancement now.
   - Reason: preserves test and runtime contracts; avoids migration-induced delivery stall.

2. Google Drive as cold backup vs object storage replacement  
   - Chosen: cold backup only.
   - Reason: cost-efficient, but constrained by Drive limits; not suitable for hot serving.

3. Large immediate feature set vs layered rollout  
   - Chosen: layered rollout (contract -> backend -> UI -> hardening).
   - Reason: lower blast radius and easier rollback.

## 5. Pitfalls to avoid

1. Stitch output directly replacing runtime HTML IDs (breaks app.js/E2E silently).
2. Introducing new option fields without capability mapping.
3. Uploading raw fragmented directories to Drive (API throttling and sync collapse).
4. Marking backup success without restore-prepare verification.
5. Letting backup jobs compete with runtime disk headroom (no watermark guard).

## 6. Best practices (project-specific)

1. Treat `DESIGN.md` as the UI contract, not only style notes.
2. Keep adapter seams explicit:
   - UI-generated layout
   - runtime-binding IDs
   - API payload serializers
3. Every new button:
   - i18n key
   - capability key
   - E2E anchor
4. Every backup release gate:
   - one successful restore-prepare drill
   - key custody check
   - retention policy dry-run report

## 7. Completion gates

1. Full test suite green, including webui E2E.
2. No RBAC regression in restricted routes.
3. Member and market options are behavior-equivalent.
4. Backup/restore paths have audit records and deterministic state transitions.
