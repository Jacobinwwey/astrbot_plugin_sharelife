---
title: Sharelife Release Evolution Baseline (v0.1.0 to v0.3.13)
date: 2026-04-02
category: documentation-gaps
module: release_management
problem_type: documentation_gap
component: documentation
severity: medium
applies_when:
  - A maintainer needs a single source of truth for major changes from v0.1 onward
  - Release notes, roadmap docs, and implementation state start to drift
  - A new contributor needs high-confidence historical context before planning
symptoms:
  - Versioned capabilities are spread across release pages, docs, and commits
  - Team members re-derive the same timeline repeatedly during planning
  - '"What changed when?" is answered inconsistently across channels'
root_cause: inadequate_documentation
resolution_type: documentation_update
related_components:
  - development_workflow
  - tooling
tags:
  - release-baseline
  - changelog-governance
  - documentation-compounding
  - profile-pack
  - observability
  - webui
---

# Sharelife Release Evolution Baseline (v0.1.0 to v0.3.13)

## Context

Between `v0.1.0` and `v0.3.13`, Sharelife shipped multiple high-impact tracks in short cycles:

- bot profile-pack governance and market UX
- Round2 M1-M5 ecosystem baseline
- risk-evidence developer workflow
- observability and ops-smoke hardening
- dual-path onboarding and locale-first WebUI

These updates exist in valid sources (Git tags, GitHub Releases, docs), but there was no consolidated knowledge entry under `docs/solutions/` that maps all releases into one engineering baseline.

## Guidance

Use this document as the canonical "release evolution baseline" for planning and review work.

### 1. Canonical timeline (v0.1.0 -> v0.3.13)

| Version | Date (UTC) | Core change focus |
|---|---|---|
| `v0.1.0` | 2026-03-31 | Delivered profile-pack governance loop, plugin-install confirmation gate, supply-chain scan heuristics, market snapshot pipeline, GitHub Pages as primary docs path |
| `v0.1.1` | 2026-03-31 | Added visual profile-pack compare cards and section-level diff/risk visualization in `/market` |
| `v0.1.2` | 2026-03-31 | Unified compare UX across `/` and `/market`; clarified runtime compare vs public prototype boundary |
| `v0.3.0` | 2026-03-31 | Completed Round2 M1-M5 baseline: protocol freeze, capability gateway, DX scaffolding/hot-reload, composability pipeline, registry governance |
| `v0.3.1` | 2026-04-01 | Added developer evidence jump flow and structured `risk_evidence`; seeded `profile/official-starter@1.0.0` |
| `v0.3.2` | 2026-04-01 | Stabilized and re-cut the evidence-jump + official-starter baseline release |
| `v0.3.3` | 2026-04-01 | Strengthened WebUI observability counters and error-envelope consistency; aligned version surfaces |
| `v0.3.4` | 2026-04-01 | Humanized EN/ZH docs while preserving protocol/API terminology; aligned version metadata |
| `v0.3.5` | 2026-04-02 | Closed N4/N5 observability gaps with metric cardinality guardrails and runbook hardening |
| `v0.3.6` | 2026-04-02 | Added ops baseline assets: Prometheus/Grafana configs, compose overlay, ops asset validator |
| `v0.3.7` | 2026-04-02 | Added executable observability smoke script + CI workflow (`ops-smoke`) |
| `v0.3.8` | 2026-04-02 | Added default diagnostics artifact collection and CI artifact upload for smoke runs |
| `v0.3.9` | 2026-04-02 | Added structured triage generation (`triage.md`) from smoke artifacts |
| `v0.3.10` | 2026-04-02 | Added machine-readable triage (`triage.json`) and GitHub annotations publishing |
| `v0.3.11` | 2026-04-02 | Hardened CI edge cases: artifact writable fallback, privacy redaction, preflight guards, reduced Docker build noise |
| `v0.3.12` | 2026-04-02 | Added adaptive host-port resolution and compose collision resilience for ops-smoke |
| `v0.3.13` | 2026-04-02 | Added human+AI quick onboarding, locale-first topbar UX, default-collapsed low-frequency controls, stronger browser E2E assertions |

### 2. Phase framing for decision-making

Use the timeline in five phases when reasoning about roadmap impact:

1. Foundation (`v0.1.0` to `v0.1.2`):
   profile-pack governance + compare experience + market/public boundary clarity.
2. Ecosystem baseline (`v0.3.0`):
   protocol/capability/DX/composability/governance M1-M5 closure.
3. Developer workflow and docs quality (`v0.3.1` to `v0.3.4`):
   evidence jump loop, official starter seed, observability surfacing, doc readability.
4. Ops and observability executable maturity (`v0.3.5` to `v0.3.10`):
   runbooks -> stack assets -> smoke workflow -> triage -> annotations.
5. CI robustness and onboarding UX consolidation (`v0.3.11` to `v0.3.13`):
   privacy-safe artifacts, collision resilience, quick-start dual path, locale-first UI.

### 3. Required source hierarchy when updating this baseline

When adding `vNext`, reconcile data in this order:

1. Git tags in local repo (`git tag --sort=v:refname`)
2. GitHub Releases metadata/body
3. Repo docs for architectural framing and operator guidance

Do not derive this baseline only from commit messages. Release bodies carry operator-level intent and verification surfaces that short commit subjects cannot represent.

## Why This Matters

Without a consolidated release baseline:

- planning work re-opens already settled questions
- review quality drops because milestone context is missing
- roadmap discussions confuse "planned", "implemented", and "hardened"

With this baseline:

- maintainers can map any proposal to known maturity phase quickly
- contributors can avoid duplicate "rediscovery" work
- release and docs consistency checks become deterministic

## When to Apply

- Before writing new phase plans (for example Round3/Round4 stability tracks)
- Before scope triage for multi-release refactors
- Before producing release notes, grant submissions, or architecture audits
- During onboarding of maintainers who need full historical context quickly

## Examples

### Example A: Rebuild timeline for `vNext`

```bash
git tag --sort=v:refname
gh release list --repo Jacobinwwey/astrbot_plugin_sharelife --limit 50
gh release view v0.3.13 --repo Jacobinwwey/astrbot_plugin_sharelife --json tagName,name,publishedAt,body,url
```

Expected outcome:

- every tagged release has a traceable date and intent
- this baseline table can be extended with one new row per release

### Example B: Phase-aware proposal check

If a proposal claims "new observability baseline work", first compare against `v0.3.5` to `v0.3.12` here. If the behavior already exists in those releases, scope should move from "build" to "harden/integrate" instead of re-implementing.

## Related

- [Round2 Baseline (EN)](/en/how-to/plugin-ecosystem-round2-baseline)
- [Round3 Stability Plan (EN)](/en/how-to/plugin-ecosystem-round3-stability-plan)
- WebUI observability runbook is now intentionally private and maintained outside the public docs site.
- [GitHub release list](https://github.com/Jacobinwwey/astrbot_plugin_sharelife/releases)
- [Latest release v0.3.13](https://github.com/Jacobinwwey/astrbot_plugin_sharelife/releases/tag/v0.3.13)
