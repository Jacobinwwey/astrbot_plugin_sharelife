# Sharelife WebUI Design System Baseline (2026-04-04)

## 1. Scope

This document is the single source of truth for the next user-facing panel refactor.
It covers:

- `/member` user console
- `/market` standalone market
- shared visual language in `sharelife/webui/style.css`
- runtime binding constraints in `sharelife/webui/app.js` and `sharelife/webui/market_page.js`

## 2. Current Progress

### 2.1 Frontend architecture

- Vanilla modular architecture is already split across focused files:
  - page orchestrators: `app.js`, `market_page.js`
  - view models: `market_cards.js`, `detail_panel.js`, `compare_panel.js`, `profile_pack_compare_view.js`
  - state helpers: `collection_state.js`, `workspace_state.js`, `workspace_payload.js`
  - capability gate and scope: `console_scope.js`, `/api/ui/capabilities` contract
  - i18n: `webui_i18n.js` (en-US / zh-CN / ja-JP)
- Existing E2E coverage already verifies:
  - member role locking
  - market cards and detail drawer
  - wizard submit flow
  - compare/detail render
  - capability-gated controls

### 2.2 Business workflows already available

- Template flow: list/detail/submit/trial/install/prompt/package/download.
- Profile-pack flow: submit/catalog/detail/compare/featured, import/export/dryrun/apply/rollback.
- Reviewer/Admin split and capability gating already implemented at HTTP + UI layers.

### 2.3 Constraint anchors (must preserve)

- Keep existing API paths and response envelope:
  - `{"ok": bool, "message": str, "data": any, "error": {...}}`
- Keep critical DOM IDs used by orchestrators/E2E.
- Keep `/api/ui/capabilities` as backend source of truth for button-level operation gates.

## 3. Future Needs (Target UX)

User panel must center around 4 workflows with low cognitive load:

1. Store Search: global command search entry, keyboard-first.
2. Manage Installations: installed resources as default view, status-first.
3. Upload Center: drag/drop plus explicit option set.
4. Download & Task Management: running queue + history + failure reason.

Additionally:

- Add top-center actionable button: `刷新本地已有配置`.
- Align `/market` with the same upload/install options model used in `/member`.
- Keep non-frequent controls collapsed by default or behind developer mode.

## 4. Visual System (Extracted Baseline)

### 4.1 Theme tokens

- Color mode: dark-only at root (`:root { color-scheme: dark; }`).
- Core palette:
  - background: `#131313` / `#1c1b1b`
  - surface: `#201f1f` / `#2a2a2a`
  - text: `#e5e2e1`, muted `#bfc9c3`
  - accent: emerald `#68dba9`, `#4fd09f`
- Border/shadow:
  - default border token `--border: #404944`
  - primary shadow `0 22px 48px rgba(0,0,0,0.45)`

### 4.2 Typography

- Main UI text: `Sora`
- Titles/brand: `Manrope`
- Code/status payload zones: `JetBrains Mono`

### 4.3 Spacing, shape, hierarchy

- Rounded corners: 14px/16px/20px common radii.
- Sticky top utility bar + card-driven sections.
- Dense but still readable layout; current weakness is workflow scattering.

## 5. Interaction Contracts

### 5.1 Capability gate contract

- Buttons must remain mapped to operation keys in `CONTROL_CAPABILITY_MAP`.
- Any new action button requires:
  - capability key mapping
  - locked hint fallback
  - disabled/aria-disabled consistency

### 5.2 i18n contract

- All new labels/buttons/placeholders must have keys in `webui_i18n.js` for:
  - `en-US`
  - `zh-CN`
  - `ja-JP`
- Avoid literal strings in templates except fallback text.

### 5.3 URL/state sync

- Market keeps URL-sync for local filters:
  - `q`, `sort`, `facet_*`, `pack_id`
- New installation/task filters should follow the same deterministic serialization model.

## 6. API Contract Surface for Next Iteration

### 6.1 Existing APIs to keep stable

- `POST /api/templates/submit` (already supports package payload)
- `POST /api/templates/install`
- `GET /api/profile-pack/catalog` + `/insights` + `/detail` + `/compare`
- `GET /api/ui/capabilities`

### 6.2 Planned extension points

- Installation list/refresh endpoints for local configuration visibility.
- Extend template install payload with option block (preflight/reinstall/source policy).
- Extend template submit/profile-pack submit with option blocks (scan/visibility/sections strategy).

All extensions must be backward compatible (optional fields with server defaults).

## 7. Stitch-to-Production Mapping Rules

- Stitch output is design source, not runtime source.
- Preserve runtime IDs and event boundaries while remapping structure and class system.
- Reject any generated fragment that:
  - breaks i18n key-based rendering
  - bypasses capability gating
  - removes existing E2E anchor IDs without replacement adapters

## 8. Non-Goals (This round)

- No full framework migration to React/Vue.
- No replacement of current auth/rbac model.
- No rewrite of submission/review domain logic.
