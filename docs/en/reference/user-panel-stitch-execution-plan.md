# User Panel + Market Refactor Execution Plan

> Date: `2026-04-04`  
> Owner: WebUI Architecture  
> Scope: member-facing panel and `/market` parity

## 0. Execution Status

Implemented in the current codebase:

1. `/member` now exposes the four user workflows as first-class surfaces:
   - spotlight-style store search
   - installation management
   - upload center with drag/drop
   - task queue/history
2. `/market` now exposes equivalent install/upload controls, local installation refresh, and drag/drop upload affordance.
3. Backward-compatible API extensions are live for:
   - `GET /api/member/installations`
   - `POST /api/member/installations/refresh`
   - `install_options`
   - `upload_options`
   - `submit_options`
4. Verification landed in interface tests, WebUI unit tests, and browser E2E.
5. `/member` is now spotlight-first: locale switch, primary local-refresh action, and a single global search field lead the page; duplicated member-side `Market Hub` framing was removed from the result surface.

Current tradeoff:

1. `install_options.source_preference=generated` now changes package resolution behavior.
2. Other option blocks are normalized, persisted, and surfaced back to the UI/API, but not all of them change downstream governance semantics yet.

## 1. Target

Restructure the user-facing WebUI into four explicit workflows while preserving existing contracts and route guards:

1. Store Search  
2. Manage Installations  
3. Upload Center  
4. Download & Task Management

## 2. Non-Negotiable Baseline

1. Keep current vanilla modular runtime (`app.js`, `market_page.js`, helper modules).  
2. Keep capability gating from `/api/ui/capabilities`.  
3. Keep runtime i18n key system (`webui_i18n.js`) as mandatory.  
4. Keep existing DOM ID anchors used by tests and orchestration.

## 3. IA and UI Shape

### 3.1 Member surface

1. Top bar:
   - global spotlight-style search
   - locale switch
   - always-visible `刷新本地已有配置` primary utility action
2. Main default pane: installed resources overview.
3. Secondary pane:
   - upload drop zone + upload options
   - download/task queue with progress + history
4. Mobile:
   - side navigation collapsed to drawer
   - top search remains first-class (single-row or stacked)

### 3.2 Market surface parity

`/market` must expose equivalent install/upload option controls and not degrade to a read-only shell.

## 4. API Contract Extensions (Backward-Compatible)

### 4.1 Member installation APIs

1. `GET /api/member/installations`  
2. `POST /api/member/installations/refresh`

Response envelope stays unchanged:
`{ ok, message, data, error? }`

### 4.2 Payload expansion

1. `POST /api/templates/install`
   - `install_options.preflight: bool`
   - `install_options.force_reinstall: bool`
   - `install_options.source_preference: auto|uploaded_submission|generated`
2. `POST /api/templates/submit`
   - `upload_options.scan_mode: strict|balanced`
   - `upload_options.visibility: community|private`
   - `upload_options.replace_existing: bool`
3. `POST /api/profile-pack/submit`
   - `submit_options.pack_type`
   - `submit_options.selected_sections`
   - `submit_options.redaction_mode`

## 5. Stitch Integration Discipline

1. Treat `DESIGN.md` as the source-of-truth contract.  
2. Generate member and market layouts through Stitch.  
3. Only merge generated fragments through adapter boundaries:
   - preserve IDs
   - preserve i18n keys
   - preserve capability bindings
4. Reject generated snippets that break event wiring or RBAC boundaries.

## 6. Verification Matrix

1. Interface tests:
   - member installation endpoints
   - payload defaults and validation
2. WebUI unit tests:
   - view-model mapping for installation/task/options states
   - i18n key completeness
3. E2E:
   - card click -> detail drawer
   - upload with options
   - install with options
   - local refresh -> installation list update
   - member/market parity

## 7. Risks and Controls

1. Risk: generated markup breaks existing runtime bindings  
   Control: strict ID-preservation checks in review.
2. Risk: simplified UX removes power-user controls  
   Control: collapse advanced controls instead of deleting them.
3. Risk: UI/back-end capability drift  
   Control: every control maps into `CONTROL_CAPABILITY_MAP` before merge.
