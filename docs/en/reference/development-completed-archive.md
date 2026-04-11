# Development Completed Archive (Public)

> Last updated: `2026-04-11`  
> Scope: items completed and publicly verifiable in code/tests/docs

## Completed streams

1. Role boundary baseline
- Member/reviewer/admin/market surfaces are separated with route-level guard semantics (`401` unauthenticated, `403` forbidden).
- Member source templates are pruned from privileged controls rather than relying on CSS hiding.

2. Promotion and publication safety rails
- Public promotion gate blocks private-doc roots, local secret-like files, gitlink/submodule mode mutations, and non-allowlisted path additions.
- Public projection manifests and tests are in place for safe private->public synchronization.

3. Market/member capability guard convergence
- Market capability runtime reuses shared guard helpers to reduce authz drift between pages.
- Anonymous member allowlist behavior is contract-tested across API and WebUI paths.

4. Persistent execution/installation model
- Upload/install/submit contracts are normalized for option shape consistency.
- Idempotency conflict handling is enforced (`idempotency_key_conflict`) for submit paths.

5. Decomposition governance
- CI line-budget guardrails were added for major monolithic files to prevent silent coupling growth during refactor.

## Verification sources

1. `tests/infrastructure/test_public_promotion_gate.py`
2. `tests/meta/test_market_capability_runtime_surface.py`
3. `tests/meta/test_decomposition_budget_surface.py`
4. `tests/interfaces/test_webui_server.py`
5. `tests/meta/test_permission_boundary_roadmap_surface.py`

## Boundary note

This archive is public-contract only.
Operator SOP, secret rotation runbooks, and privileged recovery procedures remain private.

