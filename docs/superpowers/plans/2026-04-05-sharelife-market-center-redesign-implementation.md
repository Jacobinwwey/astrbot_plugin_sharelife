# Sharelife Market Center Entry Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild `/market` into a public-read-only market entry with Spotlight-style search, public-only cards, and a detail drawer/sheet that becomes the only place where member actions and later Stitch-generated variants live.

**Architecture:** Keep the existing standalone `/market` route and vanilla WebUI stack, but stop adding more responsibility to the 3182-line `market_page.js`. Extract two small helper boundaries: one for the public catalog contract and one for the detail-shell contract. Keep runtime IDs stable where possible, and introduce a dedicated `sharelife/webui/market_detail/` folder because the Stitch pre-call gate requires a module-local `Design.md`.

**Tech Stack:** Static HTML, vanilla JavaScript modules loaded from `sharelife/webui/`, shared `style.css`, shared `webui_i18n.js`, Node `node:test` WebUI tests, Python `pytest` meta surface tests, Stitch MCP for later variant generation.

**Canonical language:** English

**Localized companions:** `docs/superpowers/plans/2026-04-05-sharelife-market-center-redesign-implementation.zh-CN.md`, `docs/superpowers/plans/2026-04-05-sharelife-market-center-redesign-implementation.ja-JP.md`

---

## Implementation Status Snapshot

> Updated: `2026-04-07`

Completed in the current branch:

1. `/market` is now operating on the public-first baseline with Spotlight search above sorting.
2. The public catalog refresh button has been normalized to `Refresh Catalog`.
3. Public search now includes localized search aliases so Chinese terms such as `官方` still resolve official packs.
4. Public catalog cards now expose local like controls and visible like counts.
5. Member installation management now supports refresh, reinstall, and uninstall.
6. Backend support for `member.installations.uninstall` is in place, and local installation visibility is derived from the latest install vs uninstall audit event.

Open verification note:

1. Source tests are green.
2. Browser E2E requires a local `playwright` Node dependency before it can be executed in this environment.

---

## File Structure

### Create

- `sharelife/webui/market_catalog_contract.js`
  Public-read-only catalog helpers: card view model, search text, and detail seed payload.
- `sharelife/webui/market_detail/detail_shell.js`
  Pure helpers for drawer/sheet mode, member-action gating, and default detail state.
- `sharelife/webui/market_detail/variant_registry.js`
  Variant IDs, active-variant normalization, and renderer lookup.
- `sharelife/webui/market_detail/Design.md`
  Module-local Stitch source-of-truth required before any MCP generation call.
- `sharelife/webui/market_detail/variants/variant_1.js`
  Stitch-backed renderer for detail variant 1.
- `sharelife/webui/market_detail/variants/variant_2.js`
  Stitch-backed renderer for detail variant 2.
- `sharelife/webui/market_detail/variants/variant_3.js`
  Stitch-backed renderer for detail variant 3.
- `sharelife/webui/market_detail/variants/variant_4.js`
  Stitch-backed renderer for detail variant 4.
- `sharelife/webui/market_detail/variants/variant_5.js`
  Stitch-backed renderer for detail variant 5.
- `tests/meta/test_market_center_surface.py`
  Surface-level assertions for the public-first market HTML structure.
- `tests/webui/test_market_catalog_contract.js`
  Unit tests for public card/search/detail-seed helpers.
- `tests/webui/test_market_detail_shell.js`
  Unit tests for detail drawer/sheet and member-action gating helpers.
- `tests/webui/test_market_detail_variants.js`
  Unit tests for variant IDs, switching, and renderer registration.

### Modify

- `sharelife/webui/market.html`
  Reorder the first screen into header -> Spotlight search -> result controls, remove first-screen member operation blocks, and add detail-shell placeholders.
- `sharelife/webui/market_page.js`
  Wire the new public catalog contract, move member actions into the detail shell, and host variant switching.
- `sharelife/webui/style.css`
  Add Spotlight search styling, public-entry hierarchy, and drawer/sheet detail-shell presentation.
- `sharelife/webui/webui_i18n.js`
  Add new market entry/detail/variant copy for `en-US`, `zh-CN`, and `ja-JP`.
- `docs/superpowers/specs/2026-04-05-market-center-redesign-design.md`
  Only if the implementation reveals a true spec contradiction; otherwise leave untouched.

### Module Export Rule

Any new browser helper added in this slice must follow the same dual-export pattern already used by `market_cards.js`:

1. `module.exports` for `node:test`
2. `globalScope.<Name>` for browser runtime

Do not introduce bundler-only imports into the standalone WebUI path.

### Keep As-Is

- `sharelife/webui/market_cards.js`
  Do not expand this file further for the new market-center slice. Keep it focused on legacy shared card helpers while new public-contract logic lives in `market_catalog_contract.js`.

## Task 1: Lock the Public-First Market Surface

**Files:**
- Create: `tests/meta/test_market_center_surface.py`
- Modify: `sharelife/webui/market.html`

- [ ] **Step 1: Write the failing surface test**

```python
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_market_surface_promotes_public_search_and_detail_shell():
    html = (REPO_ROOT / "sharelife" / "webui" / "market.html").read_text(encoding="utf-8")

    assert 'id="marketGlobalSearch"' in html
    assert html.index('id="marketGlobalSearch"') < html.index('id="marketSortBy"')
    assert 'id="btnMarketRefreshInstallations"' not in html
    assert "market.operations.heading" not in html
    assert 'id="marketDetailVariantTabs"' in html
    assert 'id="marketDetailMemberActions"' in html
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
python3 -m pytest -q tests/meta/test_market_center_surface.py
```

Expected: FAIL because the current `market.html` still contains first-screen member operations and does not expose the new detail-shell containers.

- [ ] **Step 3: Write the minimal HTML skeleton**

Implement in `sharelife/webui/market.html`:

```html
<header id="marketEntryHeader" class="market-entry-header">...</header>
<section id="marketSearchSection" class="market-spotlight-shell">
  <input id="marketGlobalSearch" ... />
</section>
<section id="marketResultControls" class="market-result-controls">...</section>

<section id="marketDetailArea" class="market-detail-canvas hidden">
  <div id="marketDetailVariantTabs" class="market-detail-variant-tabs"></div>
  <div id="marketDetailPublicFacts" class="market-detail-public-facts"></div>
  <div id="marketDetailMemberActions" class="market-detail-member-actions"></div>
</section>
```

Remove from the first screen:

1. `btnMarketRefreshInstallations`
2. the first-screen template install/upload operations block
3. any immediate trial/install/upload CTA in the primary catalog canvas

- [ ] **Step 4: Run the test to verify it passes**

Run:

```bash
python3 -m pytest -q tests/meta/test_market_center_surface.py
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/meta/test_market_center_surface.py sharelife/webui/market.html
git commit -m "refactor: lock market public entry skeleton"
```

## Task 2: Extract the Public Catalog Contract

**Files:**
- Create: `sharelife/webui/market_catalog_contract.js`
- Create: `tests/webui/test_market_catalog_contract.js`
- Modify: `sharelife/webui/market_page.js`

- [ ] **Step 1: Write the failing contract test**

```javascript
const test = require("node:test")
const assert = require("node:assert/strict")

const {
  buildPublicCatalogCard,
  buildPublicCatalogSearchText,
  buildDetailSeed,
} = require("../../sharelife/webui/market_catalog_contract.js")

test("public catalog contract exposes only open-detail as the primary action", () => {
  const item = {
    pack_id: "profile/community-safe",
    version: "2.0.1",
    pack_type: "extension_pack",
    risk_level: "low",
    compatibility: "compatible",
    maintainer: "sharelife-core",
    review_labels: ["approved"],
    warning_flags: [],
    sections: ["plugins", "providers"],
  }

  const card = buildPublicCatalogCard(item)
  assert.equal(card.primaryAction.kind, "open_detail")
  assert.equal(card.memberActionsVisible, false)
  assert.match(buildPublicCatalogSearchText(item), /community-safe/i)
  assert.equal(buildDetailSeed(item).packId, "profile/community-safe")
})
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
node --test tests/webui/test_market_catalog_contract.js
```

Expected: FAIL with module-not-found or missing exports.

- [ ] **Step 3: Write the minimal helper module**

Implement in `sharelife/webui/market_catalog_contract.js`:

```javascript
function buildPublicCatalogCard(item) {
  return {
    id: item.pack_id,
    title: item.pack_id,
    primaryAction: { kind: "open_detail", label: "Open" },
    memberActionsVisible: false,
    // ...subtitle, risk, compatibility, badges, signals
  }
}

function buildPublicCatalogSearchText(item) {
  return [
    item.pack_id,
    item.maintainer,
    ...(item.review_labels || []),
    ...(item.warning_flags || []),
    item.compatibility,
    item.summary,
    item.description,
  ].filter(Boolean).join(" ").toLowerCase()
}

function buildDetailSeed(item) {
  return { packId: item.pack_id, version: item.version || "", packType: item.pack_type || "" }
}
```

Then update `market_page.js` to consume this new module instead of growing local card/search logic further.

Load it in `market.html` before `market_page.js`:

```html
<script src="/market_catalog_contract.js"></script>
```

- [ ] **Step 4: Run the test to verify it passes**

Run:

```bash
node --test tests/webui/test_market_catalog_contract.js
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add sharelife/webui/market_catalog_contract.js tests/webui/test_market_catalog_contract.js sharelife/webui/market_page.js
git commit -m "feat: add public market catalog contract helpers"
```

## Task 3: Create the Detail-Shell Module Boundary and Stitch Source File

**Files:**
- Create: `sharelife/webui/market_detail/detail_shell.js`
- Create: `sharelife/webui/market_detail/Design.md`
- Create: `tests/webui/test_market_detail_shell.js`

- [ ] **Step 1: Write the failing detail-shell test**

```javascript
const test = require("node:test")
const assert = require("node:assert/strict")

const {
  DEFAULT_VARIANTS,
  resolveDetailPresentation,
  buildMemberActionState,
} = require("../../sharelife/webui/market_detail/detail_shell.js")

test("detail shell defaults to five variants and auth-gates member actions", () => {
  assert.deepEqual(DEFAULT_VARIANTS, ["variant_1", "variant_2", "variant_3", "variant_4", "variant_5"])
  assert.equal(resolveDetailPresentation({ viewportWidth: 1440 }), "drawer")
  assert.equal(resolveDetailPresentation({ viewportWidth: 390 }), "sheet")

  const installState = buildMemberActionState({ isAuthenticated: false, action: "install" })
  assert.equal(installState.requiresAuth, true)
  assert.equal(installState.visible, true)
})
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
node --test tests/webui/test_market_detail_shell.js
```

Expected: FAIL because the module does not exist yet.

- [ ] **Step 3: Write the minimal detail-shell helper and `Design.md` scaffold**

Implement in `sharelife/webui/market_detail/detail_shell.js`:

```javascript
const DEFAULT_VARIANTS = ["variant_1", "variant_2", "variant_3", "variant_4", "variant_5"]

function resolveDetailPresentation({ viewportWidth }) {
  return Number(viewportWidth) <= 768 ? "sheet" : "drawer"
}

function buildMemberActionState({ isAuthenticated, action }) {
  return {
    action,
    visible: true,
    requiresAuth: !isAuthenticated,
  }
}
```

Create `sharelife/webui/market_detail/Design.md` with these sections:

1. target surface and user job
2. required data contract
3. DOM/runtime constraints
4. finalized Stitch MCP prompt block placeholder
5. expected variant count and comparison behavior
6. post-generation acceptance checks

Keep `Design.md` bilingual, using the same top-level structure as the approved spec:

1. time/version metadata
2. complete English section
3. complete Chinese section

- [ ] **Step 4: Run the test to verify it passes**

Run:

```bash
node --test tests/webui/test_market_detail_shell.js
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add sharelife/webui/market_detail/detail_shell.js sharelife/webui/market_detail/Design.md tests/webui/test_market_detail_shell.js
git commit -m "feat: add market detail shell contract"
```

## Task 4: Move Member Actions Behind the Detail Shell

**Files:**
- Modify: `sharelife/webui/market.html`
- Modify: `sharelife/webui/market_page.js`
- Modify: `sharelife/webui/market_catalog_contract.js`
- Modify: `sharelife/webui/market_detail/detail_shell.js`
- Test: `tests/meta/test_market_center_surface.py`
- Test: `tests/webui/test_market_catalog_contract.js`
- Test: `tests/webui/test_market_detail_shell.js`

- [ ] **Step 1: Extend the failing surface test for action placement**

Add to `tests/meta/test_market_center_surface.py`:

```python
assert 'id="btnMarketTemplateTrial"' not in html
assert 'id="btnMarketTemplateInstall"' not in html
assert 'id="btnMarketTemplateSubmit"' not in html
assert 'id="btnMarketProfilePackSubmit"' not in html
assert 'id="marketDetailActionRail"' in html
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:

```bash
python3 -m pytest -q tests/meta/test_market_center_surface.py
node --test tests/webui/test_market_catalog_contract.js tests/webui/test_market_detail_shell.js
```

Expected: FAIL because the old action controls still live in the first-screen markup and are not yet rendered through the detail shell.

- [ ] **Step 3: Write the minimal runtime wiring**

In `sharelife/webui/market_page.js`:

```javascript
function openDetailShell(item) {
  state.selectedPackId = item.pack_id
  setMarketDetailExpanded(true)
  renderDetailPublicFacts(item)
  renderDetailMemberActions(item)
}

function renderDetailMemberActions(item) {
  const root = byId("marketDetailMemberActions")
  clearChildren(root)
  ;["try", "install", "upload"].forEach((action) => {
    const state = detailShellHelpers().buildMemberActionState({
      isAuthenticated: Boolean(state.token),
      action,
    })
    root.appendChild(renderMemberActionButton(state, item))
  })
}
```

Use card click and the `Open` action to call `openDetailShell(item)`. Do not reintroduce first-screen trial/install/upload buttons.

Also load the detail helper before `market_page.js`:

```html
<script src="/market_detail/detail_shell.js"></script>
```

- [ ] **Step 4: Run the tests to verify they pass**

Run:

```bash
python3 -m pytest -q tests/meta/test_market_center_surface.py
node --test tests/webui/test_market_catalog_contract.js tests/webui/test_market_detail_shell.js
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add sharelife/webui/market.html sharelife/webui/market_page.js sharelife/webui/market_catalog_contract.js sharelife/webui/market_detail/detail_shell.js tests/meta/test_market_center_surface.py
git commit -m "refactor: move market member actions into detail shell"
```

## Task 5: Apply the Spotlight Hierarchy and i18n Copy

**Files:**
- Modify: `sharelife/webui/style.css`
- Modify: `sharelife/webui/webui_i18n.js`
- Modify: `tests/webui/test_webui_i18n.js`

- [ ] **Step 1: Write the failing i18n assertions**

Add to `tests/webui/test_webui_i18n.js`:

```javascript
assert.equal(getMessage("en-US", "market.entry.subtitle_public", ""), "Public-read-only market entry")
assert.equal(getMessage("zh-CN", "market.search.spotlight_hint", ""), "像 Spotlight 一样搜索 pack、标签与风险")
assert.equal(getMessage("ja-JP", "market.detail.member_actions", ""), "メンバー操作")
assert.equal(getMessage("en-US", "market.variant.tab_1", ""), "Variant 1")
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
node --test tests/webui/test_webui_i18n.js
```

Expected: FAIL because the new market entry/detail keys do not exist.

- [ ] **Step 3: Write the minimal CSS and i18n updates**

In `sharelife/webui/style.css`, add focused classes such as:

```css
.market-spotlight-shell { max-width: 72rem; margin: 0 auto; }
.market-spotlight-shell input { min-height: 72px; border-radius: 22px; }
.market-result-controls { display: grid; grid-template-columns: 1fr auto auto; gap: 12px; }
.market-detail-variant-tabs { display: flex; gap: 8px; flex-wrap: wrap; }
.market-detail-member-actions { display: grid; gap: 12px; }
```

In `sharelife/webui/webui_i18n.js`, add new keys for:

1. public market entry copy
2. Spotlight search hint
3. detail shell labels
4. variant tab labels 1-5

- [ ] **Step 4: Run the test to verify it passes**

Run:

```bash
node --test tests/webui/test_webui_i18n.js
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add sharelife/webui/style.css sharelife/webui/webui_i18n.js tests/webui/test_webui_i18n.js
git commit -m "style: restage market entry hierarchy and copy"
```

## Task 6: Add the Variant Registry Before Stitch Output Lands

**Files:**
- Create: `sharelife/webui/market_detail/variant_registry.js`
- Create: `tests/webui/test_market_detail_variants.js`
- Modify: `sharelife/webui/market.html`
- Modify: `sharelife/webui/market_page.js`
- Modify: `sharelife/webui/webui_i18n.js`

- [ ] **Step 1: Write the failing variant-registry test**

```javascript
const test = require("node:test")
const assert = require("node:assert/strict")

const {
  DEFAULT_VARIANTS,
  normalizeVariantId,
} = require("../../sharelife/webui/market_detail/variant_registry.js")

test("variant registry keeps five stable ids and normalizes invalid input", () => {
  assert.deepEqual(DEFAULT_VARIANTS, ["variant_1", "variant_2", "variant_3", "variant_4", "variant_5"])
  assert.equal(normalizeVariantId("variant_3"), "variant_3")
  assert.equal(normalizeVariantId("missing"), "variant_1")
})
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
node --test tests/webui/test_market_detail_variants.js
```

Expected: FAIL because the registry file does not exist.

- [ ] **Step 3: Write the minimal registry and tab wiring**

Implement in `sharelife/webui/market_detail/variant_registry.js`:

```javascript
const DEFAULT_VARIANTS = ["variant_1", "variant_2", "variant_3", "variant_4", "variant_5"]

function normalizeVariantId(value) {
  return DEFAULT_VARIANTS.includes(value) ? value : DEFAULT_VARIANTS[0]
}
```

Then render the tab strip in `market_page.js`:

```javascript
function renderVariantTabs() {
  const root = byId("marketDetailVariantTabs")
  clearChildren(root)
  variantRegistry.DEFAULT_VARIANTS.forEach((variantId, index) => {
    root.appendChild(renderVariantTabButton(variantId, index + 1))
  })
}
```

The tab strip is placeholder-safe in this phase: it can exist before final Stitch visuals land.

Load the registry before `market_page.js`:

```html
<script src="/market_detail/variant_registry.js"></script>
```

- [ ] **Step 4: Run the test to verify it passes**

Run:

```bash
node --test tests/webui/test_market_detail_variants.js
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add sharelife/webui/market_detail/variant_registry.js tests/webui/test_market_detail_variants.js sharelife/webui/market.html sharelife/webui/market_page.js sharelife/webui/webui_i18n.js
git commit -m "feat: add market detail variant registry shell"
```

## Task 7: Finalize `Design.md`, Run Stitch, and Integrate Five Variants

**Files:**
- Modify: `sharelife/webui/market_detail/Design.md`
- Create: `sharelife/webui/market_detail/variants/variant_1.js`
- Create: `sharelife/webui/market_detail/variants/variant_2.js`
- Create: `sharelife/webui/market_detail/variants/variant_3.js`
- Create: `sharelife/webui/market_detail/variants/variant_4.js`
- Create: `sharelife/webui/market_detail/variants/variant_5.js`
- Modify: `sharelife/webui/market_detail/variant_registry.js`
- Modify: `sharelife/webui/market_page.js`
- Modify: `sharelife/webui/style.css`
- Test: `tests/webui/test_market_detail_variants.js`

- [ ] **Step 1: Freeze the failing readiness check**

Extend `tests/webui/test_market_detail_variants.js`:

```javascript
const { DEFAULT_VARIANTS, getVariantRenderer } = require("../../sharelife/webui/market_detail/variant_registry.js")

test("every default variant has a renderer", () => {
  DEFAULT_VARIANTS.forEach((variantId) => {
    assert.equal(typeof getVariantRenderer(variantId), "function")
  })
})
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
node --test tests/webui/test_market_detail_variants.js
```

Expected: FAIL because renderer functions for all five variants are not registered yet.

- [ ] **Step 3: Finalize `sharelife/webui/market_detail/Design.md`**

Update the file so it contains:

1. final stable runtime IDs from `market.html`
2. final member-action gating behavior
3. final data contract
4. the exact Stitch MCP prompt block
5. the rule that the target is the detail layer only
6. the requirement for five one-click-switchable variants

Keep the file bilingual and update the prompt block only inside that checked-in `Design.md`, never only in chat.

- [ ] **Step 4: Run Stitch MCP and wait five minutes before fetch**

Tool sequence:

1. Use the module-local `Design.md` as the only design-source prompt context.
2. Generate five detail-layer variants for the already selected pack context.
3. Wait five minutes after the generation call.
4. Fetch the generated variants.

Use Stitch MCP, not ad-hoc HTML handcrafting, for the five final visual treatments.

- [ ] **Step 5: Write the minimal integration**

Create one renderer per variant:

```javascript
// sharelife/webui/market_detail/variants/variant_1.js
function renderVariant1(context) {
  return `<section class="market-detail-variant">...</section>`
}
module.exports = { renderVariant1 }
```

Register them in `variant_registry.js`, update `market_page.js` to swap renderers by selected variant ID, and keep the same pack context while switching tabs.

Load the stitched variant files before `market_page.js`:

```html
<script src="/market_detail/variants/variant_1.js"></script>
<script src="/market_detail/variants/variant_2.js"></script>
<script src="/market_detail/variants/variant_3.js"></script>
<script src="/market_detail/variants/variant_4.js"></script>
<script src="/market_detail/variants/variant_5.js"></script>
```

- [ ] **Step 6: Run the tests and visual verification**

Run:

```bash
node --test tests/webui/test_market_catalog_contract.js tests/webui/test_market_detail_shell.js tests/webui/test_market_detail_variants.js tests/webui/test_webui_i18n.js
python3 -m pytest -q tests/meta/test_market_center_surface.py
```

Then visually verify `/market` in the local WebUI and the docs portal:

1. first screen is public-read-only
2. detail drawer/sheet hosts member actions
3. `Variant 1-5` switch without losing pack context

- [ ] **Step 7: Commit**

```bash
git add sharelife/webui/market_detail/Design.md sharelife/webui/market_detail/variant_registry.js sharelife/webui/market_detail/variants sharelife/webui/market_page.js sharelife/webui/style.css tests/webui/test_market_detail_variants.js
git commit -m "feat: integrate stitch-backed market detail variants"
```

## Final Verification

- [ ] Run the focused WebUI suite:

```bash
node --test tests/webui/test_market_catalog_contract.js tests/webui/test_market_detail_shell.js tests/webui/test_market_detail_variants.js tests/webui/test_webui_i18n.js
```

- [ ] Run the market surface meta test:

```bash
python3 -m pytest -q tests/meta/test_market_center_surface.py
```

- [ ] Run the broader existing WebUI safety net:

```bash
node --test tests/webui/*.js
```

- [ ] If docs/private indexes were refreshed during implementation, re-run:

```bash
python3 scripts/sync_local_private_docs.py
```

- [ ] Confirm manual smoke behavior:

1. `/market` loads with public-first header/search/results structure.
2. No install/trial/upload action is exposed on the first-screen cards.
3. Clicking a card opens the detail drawer/sheet.
4. Member actions prompt for auth only when triggered.
5. Variant switching stays inside the opened pack context.
