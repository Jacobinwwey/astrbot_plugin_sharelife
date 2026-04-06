# Permission Boundary & Role-Decoupling Roadmap (User / Reviewer / Admin / Developer)

> Baseline: `v1.0`  
> Last consolidated: `2026-04-06`  
> Scope: Sharelife WebUI, API surface, command surface, and public VitePress information architecture

## 1. Objective and Principles

This roadmap keeps Sharelife on a role-first governance path while reducing unnecessary auth complexity and public exposure.

Core principles:
- Role isolation before feature expansion: define who can act before adding more actions.
- Least privilege by default: user-facing surfaces expose only the minimum operational capability.
- Public docs are not operator runbooks: public pages describe boundaries and stable behaviors, while sensitive auth and recovery procedures stay private.
- Authorization semantics must stay deterministic: unauthenticated access returns `401`, authenticated-but-denied access returns `403`.

## 2. Runtime Role Matrix

| Role | Allowed | Denied |
| --- | --- | --- |
| User | Market search, install/uninstall, upload/download, progress visibility, owner-aware actions on their own pending submissions | Moderation decisions, strict apply, rollback, reviewer/admin key management |
| Reviewer | Review queue handling, risk labeling, moderation decisions, evidence inspection | System-level apply/rollback, global configuration mutation |
| Admin | Publishing controls, destructive operations, reviewer access distribution, reviewer session/device reset | Audit-log mutation |
| Developer | Architecture evolution, API extension, tests/docs maintenance | Runtime auth bypass |

Notes:
- Sharelife does **not** introduce a separate runtime `Creator` role. Resource ownership is handled as an authorization rule, not as a standalone login role.
- Local reviewer device-backed auth remains a temporary fallback path. The exact issuance, recovery, and revocation SOP is intentionally private.

## 3. Current Progress and Known Gaps

### 3.1 Completed
- Dedicated member, reviewer, admin, and market pages with role-aware entry routing.
- Route-level auth middleware with stable `401` / `403` behavior on privileged paths.
- Reviewer invite/device/session primitives exist in the backend.
- Aggregated audit summary exists for reviewer/device/action visibility.
- Public docs and private docs have been separated: detailed operator/auth runbooks are no longer part of the public site.

### 3.2 Not complete yet
- Admin-to-reviewer key management is **not** fully closed from frontend to backend.
  - The backend has invite/device foundations.
  - The admin WebUI does not yet provide a complete reviewer lifecycle management console.
- Owner-aware policy is still incomplete across all mutation paths.
  - Submission and profile-pack resources already carry owner identity fields.
  - Full backend enforcement is not yet uniformly applied across every user-facing mutation.
- Reviewer session behavior still needs refinement.
  - The roadmap no longer treats reviewer-global single-session behavior as a target state.
  - The intended direction is device-granular session invalidation.

## 4. Public-Facing Execution Direction

### 4.1 Auth strategy
- Keep the current local auth stack stable before considering larger identity changes.
- Treat local reviewer invite/device auth as a fallback implementation, not as the long-term center of the product.
- Keep external IdP support (`OIDC` / `OAuth2` / enterprise providers) as a next-stage direction rather than an immediate rewrite.

### 4.2 Reviewer workspace
- Reviewers must retain access to technical evidence.
- The preferred UX is: risk summary first, expandable technical payload second.
- Public docs should describe this as “evidence-first review” rather than exposing internal payload structures.

### 4.3 Documentation contract
- Public docs must state required role behavior and deny behavior.
- Private docs must carry reviewer invite, device key, secret rotation, recovery, and operator-only runbooks.
- The longer-term goal is code-first auth metadata with docs generated or synchronized from route-level declarations.

## 5. Acceptance Criteria

This stage is only considered complete when all of the following are true:
1. Interface and WebUI tests pass, including reviewer invite/device/session paths.
2. Unauthenticated privileged access returns `401`, and authenticated-but-denied access returns `403`.
3. User mutation paths are owner-aware for their own resources and deny access to non-owned resources.
4. Public docs no longer expose reviewer/admin operator procedures, secret handling, or recovery runbooks.
5. `admin-to-reviewer` key management closure is documented as an explicit in-progress workstream rather than implied as complete.

## 6. Next Iteration Targets

1. Close the `admin-to-reviewer` lifecycle from frontend to backend:
   - invite issuance
   - device visibility/reset
   - session revoke
   - audit trace
2. Add owner-aware authorization checks across user mutation flows without creating a separate `Creator` role.
3. Refine reviewer session handling toward device-granular invalidation.
4. Move toward code-first auth metadata and generated permission documentation.
5. Evaluate optional external identity providers only after the local model is internally consistent.
