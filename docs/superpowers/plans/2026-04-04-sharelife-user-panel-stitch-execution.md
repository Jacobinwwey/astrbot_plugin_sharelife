# Sharelife User Panel Refactor Execution Plan (Member + Market)

Date: 2026-04-04  
Owner: WebUI Architecture  
Status: Ready for implementation

## 1. Objective

Restructure user-facing WebUI around four explicit workflows:

1. Store Search
2. Manage Installations
3. Upload Center
4. Download & Task Management

while preserving existing API contracts, RBAC capability gating, and E2E anchor stability.

## 2. Architectural Baseline

- Keep Vanilla modular architecture (`app.js`, `market_page.js`, view-model helper modules).
- Keep capability control via `/api/ui/capabilities`.
- Keep i18n key architecture (`webui_i18n.js`) as hard requirement.
- Keep backward compatibility for existing DOM IDs referenced by orchestrators and tests.

## 3. IA and UI refactor target

### 3.1 Unified user IA

- Top control bar:
  - centered global search (Spotlight/Raycast behavior)
  - locale switch
  - `刷新本地已有配置` button (middle position, always visible)
- Main region default tab: Installed resources view.
- Secondary region:
  - Upload drop zone with explicit options
  - Download/task queue with progress and history
- Mobile:
  - collapse side nav to drawer
  - keep global search usable in single-row or stacked mode

### 3.2 Market parity

- `/market` must expose equivalent upload/install option controls, not a downgraded surface.
- Keep card-first catalog view and detail/compare panel behavior.

## 4. API/interface changes (backward-compatible)

### 4.1 New endpoints

1. `GET /api/member/installations`
2. `POST /api/member/installations/refresh`

Return envelope remains standard:
`{ ok, message, data, error? }`

### 4.2 Extended payload contracts

1. `POST /api/templates/install`
   - add optional `install_options`:
     - `preflight: bool`
     - `force_reinstall: bool`
     - `source_preference: auto|uploaded_submission|generated`

2. `POST /api/templates/submit`
   - add optional `upload_options`:
     - `scan_mode: strict|balanced`
     - `visibility: community|private`
     - `replace_existing: bool`

3. `POST /api/profile-pack/submit`
   - add optional `submit_options`:
     - `pack_type`
     - `selected_sections`
     - `redaction_mode`

## 5. Stitch workflow integration

1. Feed `DESIGN.md` as source-of-truth context.
2. Generate member and market layout variants using Stitch.
3. Apply output to production HTML/CSS with adapter discipline:
   - keep runtime IDs
   - keep i18n keys
   - keep capability map bindings
4. Reject generated fragments that break event or RBAC boundaries.

## 6. Verification matrix

1. Interface tests:
   - new installation APIs
   - extended payload validation and defaults
2. WebUI unit tests:
   - view model mapping for installations/task queue/options
   - i18n key completeness
3. E2E:
   - card click -> detail
   - upload with options
   - install with options
   - refresh local config updates installations and local records
   - market parity assertions

## 7. Risks and controls

1. Risk: Stitch output breaks existing bindings  
   Control: strict adapter layer and ID preservation checks.

2. Risk: UX cleanup regresses power-user flows  
   Control: advanced controls collapsed, not removed.

3. Risk: capability drift between UI and backend  
   Control: new controls must be wired into `CONTROL_CAPABILITY_MAP`.
