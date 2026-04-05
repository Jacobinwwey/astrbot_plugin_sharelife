# Sharelife Market Public Hub Deployment Strategy

## Decision Scope

This document fixes the deployment baseline for the future Sharelife market-facing WebUI/Public Hub pages.

Target:

1. Keep private/admin write operations in local plugin WebUI.
2. Publish community-facing read-only market pages to a stable public URL.
3. Keep rollback and historical traceability practical for personal/community operation.

## Current Publishing Progress (2026-03-31)

What is already in place:

1. Public docs hosting baseline is stable on GitHub Pages project site:
   `https://jacobinwwey.github.io/astrbot_plugin_sharelife/`.
2. Deployment workflow exists with `push` and `workflow_dispatch` (`git_ref`) support:
   `.github/workflows/deploy-docs-github-pages.yml`.
3. Public market-facing docs pages exist in `en/zh/ja`:
   `market-public-hub.md` and `market-catalog-prototype.md`.
4. The market catalog prototype is locale-dictionary driven and avoids hardcoded table headers.

What is still prototype-level:

1. Community market page is static demo data, not server-driven community catalog data.
2. Publishing quality gates currently focus on surface presence, not end-to-end content quality (links, parity, deploy smoke).
3. Release observability (deploy digest, health checks, stale-page detection) is still minimal.

## Compared Options

### Option A: GitHub Pages from GitHub Actions (recommended baseline)

Flow:

1. Source in `main`.
2. GitHub Actions builds static output.
3. Deploy via `actions/deploy-pages`.

Pros:

1. Single source of truth (`main`).
2. Cleaner review and CI governance.
3. Better maintainability as feature count grows.
4. Less risk of source/output drift.

Cons:

1. Requires Pages + Actions setup.
2. Depends on CI workflow health.

### Option B: GitHub Pages from `gh-pages` branch

Flow:

1. Build static site.
2. Commit generated output into `gh-pages`.
3. Pages serves directly from this branch.

Pros:

1. Very explicit artifact history.
2. Manual rollback by switching branch commit is straightforward.

Cons:

1. Generated artifacts pollute git history.
2. High drift risk between source and deployed content.
3. More merge/conflict overhead.
4. Harder long-term modular evolution.

## Final Choice

Use **Option A** as primary production path.

Reserve **Option B** only as optional archive strategy:

1. Keep an optional `gh-pages-archive` branch for build snapshots.
2. Do not serve production from this archive branch.

## Integration With Bot Profile Pack Roadmap

This deployment strategy is now part of future phases:

1. Phase 2+: Add market/public pages that expose read-only `bot_profile_pack` catalog metadata.
2. Phase 3+: Add community extension/bundle pages with the same deployment model.
3. All admin-only write actions remain local WebUI/API; public pages remain read-only.

## Publishing Gaps To Improve

### 1) Release Quality Gates

Current gap:

1. CI verifies workflow/config surfaces, but does not yet verify link integrity for market pages or cross-locale nav parity at page level.

Improve:

1. Add market-page link checks for `/en|/zh|/ja` hub/prototype pages.
2. Add a locale-parity check for required sections and outbound link targets.
3. Keep docs build as hard gate (already present), and add targeted market-page assertions.

### 2) Deploy Reliability And Operator Visibility

Current gap:

1. Workflow can finish build while skipping deploy when Pages readiness fails.
2. Operator feedback is warning-based but lacks structured release summary.

Improve:

1. Add a concise deploy summary (commit, ref, URL, locale pages touched, deploy status).
2. Add explicit guidance in summary when deploy is skipped (who should fix what).
3. Add optional scheduled smoke check for published URL health.

### 3) Community Interface Productization

Current gap:

1. Public catalog is static prototype and not synced with live approved community submissions.

Improve:

1. Introduce a build-time generated read-only market snapshot (`public/market/*.json`) sourced from approved records.
2. Upgrade prototype component to consume snapshot data first, with graceful fallback to demo data.
3. Add detail page route pattern for pack/template cards and risk/compatibility explainers.

### 4) Multilingual Consistency

Current gap:

1. Component-level locale dictionaries are covered; page-level semantic consistency can still drift.

Improve:

1. Enforce parity for required sections across `en/zh/ja` public market docs.
2. Add checks to prevent mixed-language fallback strings in public-market UI copy.
3. Track locale update checklist in PR template for market-page changes.

### 5) Public/Private Boundary Hardening

Current gap:

1. Boundary rules are documented, but there is no automatic policy check for accidental privileged links/buttons in public pages.

Improve:

1. Add a static scan test to block admin/apply/review action controls from public hub/prototype pages.
2. Keep privileged operations exclusive to local WebUI/API.

## Development Plan Sync (Market Publishing Track)

### Track M1: Publishing Guardrails And Tests

1. Add market-page link integrity checks.
2. Add locale parity checks for public market pages.
3. Add public/private boundary static checks.

Done criteria:

1. CI fails when a locale page misses required market sections or has broken internal links.
2. CI fails when public pages expose privileged operation entrypoints.

### Track M2: Deploy Observability

1. Add workflow release summary output.
2. Add post-deploy smoke verification script (optional manual + scheduled mode).

Done criteria:

1. Each deploy exposes a clear summary with URL and status.
2. Failed readiness/deploy paths are actionable without log digging.

### Track M3: API-Driven Read-Only Community Catalog

1. Add snapshot-generation pipeline for approved community records.
2. Render catalog from snapshot data in public page component.
3. Keep static fallback so docs still build when snapshot is unavailable.

Done criteria:

1. Public catalog reflects approved records rather than hardcoded demo rows.
2. No privileged action endpoint is exposed on public pages.

### Track M4: Community Detail Experience

1. Add read-only detail views for template/profile-pack cards.
2. Add risk/compatibility explanation blocks and install/import handoff guidance.
3. Add locale parity tests for detail-view copy.

Done criteria:

1. Users can complete discovery and handoff to local WebUI without ambiguity.
2. `en/zh/ja` detail pages remain semantically aligned.

## Guardrails

1. Never expose admin apply/review APIs on public pages.
2. Public pages may show risk labels and compatibility but cannot perform privileged apply.
3. Download/install instructions must always route users back to local Sharelife WebUI for execution.
