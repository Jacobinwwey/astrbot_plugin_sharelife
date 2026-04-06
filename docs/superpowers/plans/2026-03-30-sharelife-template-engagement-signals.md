# Sharelife Template Engagement Signals Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add persistent aggregate template engagement signals and activity-based discovery sorting to Sharelife.

**Architecture:** Reuse `MarketService` as the single source of truth for published-template discovery data. Record aggregate counters from existing API operations, serialize the resulting `engagement` object through the current API adapters, and render the signals in the existing WebUI table/detail panels instead of adding a second analytics subsystem.

**Tech Stack:** Python 3.12, pytest, existing Sharelife services, plain JS WebUI modules, VitePress docs.

---

### Task 1: Add Failing Engagement Service And API Tests

**Files:**
- Modify: `tests/application/test_market_service.py`
- Modify: `tests/interfaces/test_api_v1.py`
- Modify: `tests/interfaces/test_web_api_v1.py`

- [ ] **Step 1: Write the failing tests**

Add tests that prove:

1. `MarketService` records and persists aggregate engagement counters.
2. `SharelifeApiV1.list_templates()` exposes an `engagement` object.
3. `SharelifeApiV1.list_templates()` sorts by `installs` and `recent_activity`.
4. Template detail responses expose the same engagement payload.

- [ ] **Step 2: Run targeted tests to verify they fail**

Run: `pytest -q tests/application/test_market_service.py tests/interfaces/test_api_v1.py tests/interfaces/test_web_api_v1.py -k "engagement or sort"`
Expected: FAIL because the current market and API payloads do not expose engagement state or sorting.

- [ ] **Step 3: Commit**

```bash
git add tests/application/test_market_service.py tests/interfaces/test_api_v1.py tests/interfaces/test_web_api_v1.py
git commit -m "test: cover template engagement signals"
```

### Task 2: Implement Engagement Persistence And API Sorting

**Files:**
- Modify: `sharelife/application/services_market.py`
- Modify: `sharelife/interfaces/api_v1.py`
- Modify: `sharelife/interfaces/web_api_v1.py`
- Modify: `main.py`

- [ ] **Step 1: Write minimal implementation**

Add:

1. Aggregate engagement counters and timestamp fields in the market read model.
2. `MarketService.record_template_event()` and derived submission counts.
3. `list_templates()` support for `sort_by` and `sort_order`.
4. Shared engagement serialization for list/detail payloads.
5. API call-site updates so trial/install/prompt/package operations record events.

- [ ] **Step 2: Run targeted tests to verify they pass**

Run: `pytest -q tests/application/test_market_service.py tests/interfaces/test_api_v1.py tests/interfaces/test_web_api_v1.py -k "engagement or sort"`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add sharelife/application/services_market.py sharelife/interfaces/api_v1.py sharelife/interfaces/web_api_v1.py main.py tests/application/test_market_service.py tests/interfaces/test_api_v1.py tests/interfaces/test_web_api_v1.py
git commit -m "feat: add template engagement signals"
```

### Task 3: Add WebUI Engagement Browsing

**Files:**
- Modify: `sharelife/webui/index.html`
- Modify: `sharelife/webui/app.js`
- Modify: `sharelife/webui/detail_panel.js`
- Modify: `tests/webui/test_detail_panel.js`
- Modify: `tests/webui/test_table_interactions.js`

- [ ] **Step 1: Write failing WebUI tests**

Add checks for:

1. Template detail rows expose engagement counters and recent activity.
2. Template table rows render a compact signals summary.
3. Sort controls map to request parameters.

- [ ] **Step 2: Run targeted WebUI tests to verify failure**

Run: `node --test tests/webui/test_detail_panel.js tests/webui/test_table_interactions.js`
Expected: FAIL because the current detail/table helpers do not expose engagement or sort controls.

- [ ] **Step 3: Implement minimal WebUI support**

Keep rendering modular:

1. Add `sort_by` and `sort_order` controls to the template toolbar.
2. Extend template row rendering with a compact engagement summary.
3. Extend detail view-model mapping with exact engagement rows.

- [ ] **Step 4: Run targeted WebUI tests to verify pass**

Run: `node --test tests/webui/test_detail_panel.js tests/webui/test_table_interactions.js`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add sharelife/webui/index.html sharelife/webui/app.js sharelife/webui/detail_panel.js tests/webui/test_detail_panel.js tests/webui/test_table_interactions.js
git commit -m "feat: expose template engagement in webui"
```

### Task 4: Update Docs And README

**Files:**
- Modify: `README.md`
- Modify: `docs/en/how-to/webui-page.md`
- Modify: `docs/zh/how-to/webui-page.md`
- Modify: `docs/ja/how-to/webui-page.md`
- Modify: `docs/en/how-to/community-first-workflow.md`
- Modify: `docs/zh/how-to/community-first-workflow.md`
- Modify: `docs/ja/how-to/community-first-workflow.md`

- [ ] **Step 1: Update docs**

Document:

1. Template engagement counters.
2. Activity-based browsing and sorting.
3. The aggregate-only privacy boundary.

- [ ] **Step 2: Run docs build**

Run: `npm run docs:build --prefix docs`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add README.md docs/en/how-to/webui-page.md docs/zh/how-to/webui-page.md docs/ja/how-to/webui-page.md docs/en/how-to/community-first-workflow.md docs/zh/how-to/community-first-workflow.md docs/ja/how-to/community-first-workflow.md
git commit -m "docs: describe template engagement signals"
```

### Task 5: Full Verification And Push

**Files:**
- Verify only

- [ ] **Step 1: Run Python test suite**

Run: `pytest -q`
Expected: PASS

- [ ] **Step 2: Run WebUI helper tests**

Run: `node --test tests/webui/*.js`
Expected: PASS

- [ ] **Step 3: Run docs build**

Run: `npm run docs:build --prefix docs`
Expected: PASS

- [ ] **Step 4: Review git diff**

Run: `git status --short && git diff --stat`
Expected: Only intended files changed.

- [ ] **Step 5: Push branch**

Run: `git push`
Expected: Current branch updates on origin.
