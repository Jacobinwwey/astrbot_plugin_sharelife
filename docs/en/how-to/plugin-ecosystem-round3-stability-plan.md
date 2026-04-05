# Plugin ecosystem Round 3 stability and extensibility plan (v0.4.x)

This plan builds on Round 2 (M1-M6). The goal is to move `sharelife` from feature-complete to operationally stable and easier to evolve at scale.

## 1. Goals and boundary

### 1.1 Goals

1. Stability under concurrency, failures, and version drift.
2. Extensibility without repeated architectural rewrites.
3. Alignment with product direction: high-fidelity replication plus strict governance.

### 1.2 Non-goals

1. No full frontend rewrite to a heavy SPA framework in this stage.
2. No distributed data layer in this stage.
3. No default-open install/approval behavior.

## 2. Recommendation triage

### 2.1 Adopt now

1. Introduce `Vite` build pipeline while preserving vanilla module boundaries.
2. Consolidate UI state updates through one event bus (`EventTarget`).
3. Sanitize all user-sourced dynamic HTML with `DOMPurify`.
4. Add accessibility baseline: ARIA, keyboard flow, drawer/modal focus trap.
5. Move persistence to repository interface + SQLite implementation + JSON fallback.
6. Move heavy scan/diff tasks to background execution (`asyncio.to_thread`/workers).
7. Strengthen middleware: auth dependency consistency, rate limiting, strict CORS, security headers.
8. Add observability: structured logging (`structlog`) and Prometheus metrics export.
9. Provide official container path: multi-stage Docker image + compose baseline.
10. Add CI gates for coverage, i18n/docs/protocol consistency.

### 2.2 Defer

1. PWA offline and install shell.
2. Infinite-scroll UX as default interaction model.
3. Full Tailwind restyling of existing pages.
4. Direct PostgreSQL/`asyncpg` migration before SQLite phase is proven.

### 2.3 Not adopted in this stage

1. Full migration to a heavy SPA stack.
2. Relaxing review/install guardrails for speed.

## 3. Architecture decisions (ADR summary)

### ADR-1: Frontend evolution

Decision:

1. Keep vanilla JS module responsibilities.
2. Add Vite bundling and artifact governance.
3. Add centralized event bus for state synchronization.

Reasoning:

1. Lowest migration risk with immediate maintainability gains.
2. Removes script-global coupling and manual load cost.
3. Creates a path for incremental declarative updates later.

### ADR-2: Persistence

Decision:

1. Standardize repository interfaces for market/profile-pack/audit/trial data.
2. Switch default storage to SQLite.
3. Keep JSON repository for local fallback and rollback.

Reasoning:

1. Better write concurrency and query capability with low migration cost.
2. Preserves existing layered architecture.
3. Enables staged cutover rather than hard break.

### ADR-3: Security and observability first

Decision:

1. Prioritize auth/rate-limit/security-header/exception hardening.
2. Add structured logs and metrics in the same phase.

Reasoning:

1. Lowers exposure before feature acceleration.
2. Avoids blind operation during scale-up.

## 4. Milestones (N1-N5)

### N1 (consistency closure)

Scope:

1. Version consistency across plugin metadata, API metadata, and docs baseline.
2. Round 2 status text aligned with actual implementation.
3. Canonical error-code documentation alignment.

Acceptance:

1. Version drift meta-tests pass.
2. Docs status assertions pass.

### N2 (frontend maintainability and safety)

Scope:

1. Vite build integration.
2. Event-bus migration for key state flows.
3. DOMPurify integration.
4. ARIA/keyboard/focus accessibility baseline.

Acceptance:

1. `node --test tests/webui/*.js` passes.
2. E2E keeps `market -> drawer -> wizard -> compare` chain green.
3. XSS regression payloads are sanitized.

### N3 (backend persistence and concurrency baseline)

Scope:

1. SQLite repository implementation and migration utility.
2. Service layer repository abstraction adoption.
3. Query indexes on `pack_id/status/risk_level/created_at`.

Acceptance:

1. JSON and SQLite backends both pass regression.
2. No state corruption in concurrent write scenarios.

### N4 (security and observability hardening)

Scope:

1. Login/API rate limiting.
2. Security headers and strict CORS defaults.
3. Structured log schema (`request_id/actor/route/error_code`).
4. Metrics endpoint and baseline alert suggestions.

Acceptance:

1. Security regression (authz/bruteforce/CORS) passes.
2. Failures are diagnosable from logs and metrics.

### N5 (delivery and operations)

Scope:

1. Official Docker image and compose sample.
2. Data volume mount and health checks.
3. Deploy and rollback runbook update.

Acceptance:

1. Container startup reproduces WebUI and core APIs.
2. Docs cover both local and container deployment.

## 5. Risks and trade-offs

1. Build tooling adds frontend complexity.
   Mitigation: preserve module boundaries and avoid heavy framework adoption.
2. Storage migration introduces compatibility risk.
   Mitigation: migration tooling, dual-path validation, staged cutover.
3. Stronger security defaults can reduce local convenience.
   Mitigation: explicit dev/prod config profiles.

## 6. Progress snapshot (as of April 2, 2026)

1. N1 completed: version/doc consistency tests landed and are in CI.
2. N2 completed: event bus, i18n synchronization hardening, accessibility/focus controls, and browser E2E chain are green.
3. N3 completed:
   repository abstraction landed for `MarketService`, `ProfilePackService`, `PreferenceService`, `RetryQueueService`, `TrialService`, `TrialRequestService`, `AuditService`, and `InMemoryNotifier` with JSON/SQLite implementations, SQLite indexes, and legacy migration path.
4. N4 completed baseline:
   login/API rate limiting, strict security headers, request-id tracing, structured request logging, unified web error envelopes (including `internal_server_error` fallback), `/api/metrics` with dedicated auth/rate-limit counters, plus metric path-cardinality guardrails and error-storm scrape regression tests.
5. N5 completed baseline:
   official Dockerfile/compose path, health checks, standalone WebUI runner, and dedicated WebUI observability/rollback runbook for on-call operations.
6. N5+ operational closure completed:
   shipped `docker-compose` observability overlay, automated smoke script (`scripts/smoke_observability_stack.sh`), and a dedicated `ops-smoke` GitHub Actions workflow for scheduled/manual runtime checks with diagnostic artifact upload.
7. N5++ diagnostics acceleration completed:
   smoke diagnostics now generate structured triage markdown/json (`output/ops-smoke/triage.md` + `triage.json`), publish markdown to GitHub Actions Job Summary, and emit signal/action annotations for faster first response.

## 7. Recommended execution order

1. N1 -> N2 -> N3 -> N4 -> N5.
2. Resume major feature expansion only after N1-N2 closure.
3. Each milestone must ship tests, docs, and rollback notes together.

## 8. Relation to existing roadmap

1. Round 2 capabilities remain unchanged.
2. Round 3 focuses on engineering quality and operational readiness.
3. Governance invariants stay fixed: dry-run before apply, rollback availability, and auditable actions.
