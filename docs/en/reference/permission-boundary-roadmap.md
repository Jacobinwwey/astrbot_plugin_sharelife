# Permission Boundary & Role-Decoupling Roadmap (User / Reviewer / Admin / Developer)

> Baseline: `v0.3.x`  
> Last consolidated: `2026-04-04`  
> Scope: Sharelife WebUI, API surface, command surface, and VitePress information architecture

## 1. Objective and Principles

This roadmap moves Sharelife from a feature-stacked console into a role-first governance model with verifiable authorization boundaries.

Core principles:
- Role isolation before feature expansion: define who can act before adding new actions.
- Documentation is an auth contract: permission labels in docs must map to route-level guards in code.
- Least privilege by default: only expose operationally necessary capabilities to each role.

## 2. Frozen Role Matrix

| Role | Allowed | Denied |
| --- | --- | --- |
| User | Market search, install/uninstall, upload/download, progress visibility | Moderation decisions, strict apply, rollback, reviewer device-key operations |
| Reviewer | Review queue handling, risk labeling, moderation decisions, device key self-management (max 3) | System-level apply/rollback, global config mutation |
| Admin | Full library governance, publishing controls, destructive operations, reviewer access distribution | None (subject to full audit) |
| Developer | Architecture evolution, API extension, tests/docs maintenance | Runtime auth bypass |

Additional constraints:
- Reviewer device cap: default `3` (configurable).
- Single active reviewer session per `reviewer_id`.
- Revoking a device immediately invalidates dependent reviewer tokens.

## 3. Key Issuance & Refresh Strategy

### 3.1 Issuance chain
1. Admin generates invitation key (short TTL, one-time use).
2. Reviewer redeems invitation and binds identity (`reviewer_id`).
3. Reviewer registers trusted device key.
4. Reviewer login validates `reviewer_id + reviewer_device_key + reviewer_password`.

### 3.2 Rotation and revocation
- Invitation key: short-lived + single-use.
- Reviewer session token: default TTL 7 days.
- Device key: revocable and replaceable; cap enforcement requires explicit delete-first.
- Incident mode: admin can force-revoke invitation tokens and reviewer sessions.

## 4. Frontend / Backend / Docs Workstream

### 4.1 Frontend (WebUI)
- Completed:
  - Dedicated reviewer page and role-aware entry routing.
  - Clear separation across member, reviewer, and admin views.
- Next:
  - Keep all destructive action controls inside admin-only context.
  - Preserve risk evidence for reviewers while reducing default technical noise.

### 4.2 Backend (API / WebUI server)
- Completed:
  - `reviewer` auth flow and reviewer device register/list/revoke APIs.
  - Backward-compatible `user -> member` role mapping.
  - Consistent `403` for unauthorized admin/reviewer route access.
  - Aggregated audit summary on `GET /api/admin/audit` grouped by reviewer/device/action.
- Next:
  - Add tighter rate limiting and anomaly alerting on sensitive routes.

### 4.3 Documentation (VitePress)
- Completed:
  - Sidebar partitioned into User / Reviewer / Administration / Developers domains.
  - Reviewer device key SOP published in `zh/en/ja`.
- Next:
  - Require auth badges on API pages (for example `System.Admin`).
  - Add explicit warning + rollback notes before destructive operations.

## 5. Acceptance Criteria

This stage is considered complete only if all items are true:
1. Interface and WebUI tests pass, including reviewer device/session paths.
2. Unauthorized roles get deterministic `403` on restricted operations.
3. All three locales provide aligned role-domain entry docs.
4. Newly added APIs include required-role and deny-behavior docs.

## 6. Next Iteration Targets

1. Optional external IdP support (LDAP/OAuth) while keeping local reviewer key fallback.
2. Policy-driven moderation queue assignment by risk class.
3. Visualized permission-change audit timeline (actor, device, action).
4. Docs-code CI gating: missing auth badges fail the docs pipeline.
