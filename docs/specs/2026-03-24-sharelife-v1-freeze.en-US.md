# Sharelife v1 Frozen Plan (2026-03-24)

## 1. Scope and Intent

`sharelife` is an AstrBot plugin for template distribution and controlled rollout under strict governance.

v1 scope:

1. Official template source only.
2. Strict-mode execution.
3. Session-level user trial without global mutation.
4. Admin-governed apply and rollback.
5. Dedicated Sharelife WebUI page.
6. VitePress + Diataxis docs with bilingual support.

## 2. Frozen Decisions

1. Source: `Jacobinwwey/astrbot_plugin_sharelife` only.
2. Coverage: subagent + agent + broader AstrBot settings.
3. Mode: strict.
4. Trial allowed for normal users.
5. Trial TTL: 2 hours.
6. Trial renewal: forbidden.
7. First trial triggers dual notification once (user + admin).
8. Retry requests are queued and admins are notified.
9. Queue timeout after 72h goes to `manual_backlog`, not auto-closed.
10. Any admin can process manual backlog.
11. 10-minute lock is enabled for admin review.
12. Force takeover is allowed but reason is mandatory.
13. Notification channels: WebUI notification center + admin DM.
14. Real-time admin notifications route to current on-call only.
15. Offline admins receive offline-window digest after coming online.
16. Docs: zh-CN + en-US in parallel, ja-JP reserved.
17. SDK v4 migration readiness via runtime compatibility ports.
18. Priority path: `v1 is personal-user/community-first`; enterprise mechanisms (on-call rotation, takeover lock, offline digest) remain as future-ready options.
19. Personal user preference controls: switch between two execution modes and toggle task-detail observability (default off).

## 3. Modular Architecture

Layers:

1. Domain: models, policy rules, state machines.
2. Application: use-case orchestration.
3. Infrastructure: GitHub source, storage, runtime adapters, notifications.
4. Interfaces: commands, APIs, WebUI DTOs.

Dependency direction:

`interfaces -> application -> domain`, with infrastructure implementing ports only.

## 4. Strict Mode and Risk Tiers

1. L1: low-risk content tuning.
2. L2: medium-risk routing/tool-whitelist changes.
3. L3: high-risk provider/permission/global security-affecting changes.

Rules:

1. Global apply requires dry-run first.
2. L3 is disabled by default.
3. Session trial cannot activate L3.

## 5. Session Trial Model

1. Overlay-only on session scope.
2. No global config writes.
3. Lifecycle: preview -> dryrun -> start -> in_trial -> stop/expire.
4. TTL: 7200s.
5. Retry requires admin path, no renewal.

## 6. Retry Queue and Manual Backlog

State machine:

`queued -> notified -> reviewing -> approved | rejected | manual_backlog -> closed`

Rules:

1. At 72h, request moves to `manual_backlog`.
2. Backlog remains actionable.
3. Duplicate retry requests are merged.

## 7. Concurrency Controls

1. Opening a request acquires a 10-minute lock.
2. Others are read-only unless takeover.
3. Force takeover requires mandatory reason.
4. Decision submission uses optimistic concurrency (`request_version + lock_version`).

## 8. Notification Contract

Channels:

1. WebUI notification center.
2. Admin DM.

Routing:

1. Real-time -> current on-call admin.
2. Offline digest -> admins after online return.

## 9. v1 API Draft

User:

1. `GET /api/sharelife/v1/templates`
2. `GET /api/sharelife/v1/templates/{id}`
3. `POST /api/sharelife/v1/trial/dryrun`
4. `POST /api/sharelife/v1/trial/start`
5. `POST /api/sharelife/v1/trial/stop`
6. `POST /api/sharelife/v1/trial/retry-request`
7. `GET /api/sharelife/v1/trial/retry-request/status`
8. `GET /api/sharelife/v1/preferences`
9. `POST /api/sharelife/v1/preferences/mode`
10. `POST /api/sharelife/v1/preferences/observe-details`

Admin:

1. `GET /api/sharelife/v1/admin/retry-requests`
2. `POST /api/sharelife/v1/admin/retry-requests/{id}/decision`
3. `POST /api/sharelife/v1/admin/retry-requests/{id}/takeover`
4. `POST /api/sharelife/v1/admin/dryrun`
5. `POST /api/sharelife/v1/admin/apply`
6. `POST /api/sharelife/v1/admin/rollback`
7. `GET /api/sharelife/v1/admin/audit`

## 10. Documentation and i18n

1. VitePress with Diataxis structure.
2. Bilingual docs (zh/en) in parallel.
3. ja-JP is reserved as beta expansion.

## 11. SDK v4 Migration Path

1. Introduce `RuntimePort` as a stable boundary.
2. Keep `runtime_v3` now and prepare `runtime_v4` adapter.
3. Keep business logic SDK-agnostic.
4. Use capability detection and feature flags for phased migration.

## 12. Development Priority (Community-First)

v1 priority:

1. Official template distribution and standard package rules.
2. Strict-mode session trial + admin-governed apply/rollback.
3. Core notifications and audit for personal users and small communities.
4. Bilingual docs (zh/en) with ja-JP reserved.

Future-ready enterprise options:

1. On-call rotation.
2. Multi-admin takeover locks and advanced concurrency governance.
3. Offline-window digest and richer enterprise workflows.

## 13. Open Items

1. On-call source mechanism: manual switching vs scheduler.
2. Offline digest frequency and cap.
3. Escalation channel when admin DM delivery fails.

---

This document is the frozen baseline; future changes should be incremental updates on top of it.
