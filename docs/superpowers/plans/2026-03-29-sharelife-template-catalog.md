# Sharelife Multi-Domain Official Template Catalog Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expand Sharelife’s bundled official catalog into a multi-domain starter library with metadata-aware API and WebUI browsing.

**Architecture:** Reuse the current bundled-registry bootstrap and published-template flow. Widen template metadata in the shared read model, seed a richer official catalog from `templates/index.json`, then expose category/source/tag data through API serializers and WebUI rendering instead of building a parallel catalog subsystem.

**Tech Stack:** Python 3.12, pytest, existing Sharelife application services, plain JS WebUI modules, VitePress docs.

---

### Task 1: Add Failing Catalog Surface Tests

**Files:**
- Modify: `tests/meta/test_official_template_surface.py`
- Modify: `tests/interfaces/test_main_commands.py`
- Modify: `tests/interfaces/test_api_v1.py`
- Modify: `tests/webui/test_detail_panel.js`

- [ ] **Step 1: Write the failing tests**

Add tests that prove:

1. `templates/index.json` ships multiple domain templates.
2. Startup market listing includes more than the baseline pair.
3. `list_templates()` can filter by `category` and `source_channel`.
4. Template detail/list rendering exposes metadata rows and badges.

- [ ] **Step 2: Run targeted tests to verify they fail**

Run: `pytest -q tests/meta/test_official_template_surface.py tests/interfaces/test_main_commands.py tests/interfaces/test_api_v1.py && node --test tests/webui/test_detail_panel.js`
Expected: FAIL because the current model and serializers do not expose metadata-aware catalog browsing.

- [ ] **Step 3: Commit**

```bash
git add tests/meta/test_official_template_surface.py tests/interfaces/test_main_commands.py tests/interfaces/test_api_v1.py tests/webui/test_detail_panel.js
git commit -m "test: cover official catalog metadata browsing"
```

### Task 2: Implement Metadata-Aware Official Catalog

**Files:**
- Modify: `sharelife/domain/models.py`
- Modify: `sharelife/application/services_market.py`
- Modify: `sharelife/application/services_registry_bootstrap.py`
- Modify: `sharelife/interfaces/api_v1.py`
- Modify: `sharelife/interfaces/web_api_v1.py`
- Modify: `templates/index.json`

- [ ] **Step 1: Write minimal implementation**

Add:

1. Shared metadata fields on template manifest and published template records.
2. Multi-domain bundled template entries.
3. Bootstrap mapping from manifest metadata to published-template records.
4. API list/detail serializers and filters for `category`, `tag`, and `source_channel`.

- [ ] **Step 2: Run targeted tests to verify they pass**

Run: `pytest -q tests/meta/test_official_template_surface.py tests/interfaces/test_main_commands.py tests/interfaces/test_api_v1.py`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add sharelife/domain/models.py sharelife/application/services_market.py sharelife/application/services_registry_bootstrap.py sharelife/interfaces/api_v1.py sharelife/interfaces/web_api_v1.py templates/index.json tests/meta/test_official_template_surface.py tests/interfaces/test_main_commands.py tests/interfaces/test_api_v1.py
git commit -m "feat: expand official template catalog metadata"
```

### Task 3: Add WebUI Metadata Browsing

**Files:**
- Modify: `sharelife/webui/index.html`
- Modify: `sharelife/webui/app.js`
- Modify: `sharelife/webui/detail_panel.js`
- Modify: `tests/webui/test_detail_panel.js`
- Modify: `tests/e2e/sharelife_webui_e2e.cjs`

- [ ] **Step 1: Write failing WebUI test coverage**

Add checks for:

1. Template detail rows show category, maintainer, source channel, and tags.
2. Templates table shows category/source metadata.
3. E2E asserts at least one official template metadata element is visible.

- [ ] **Step 2: Run WebUI tests to verify failure**

Run: `node --test tests/webui/test_detail_panel.js`
Expected: FAIL because the current detail model ignores the new metadata.

- [ ] **Step 3: Implement minimal WebUI support**

Keep rendering modular:

1. Extend detail view-model mapping.
2. Extend templates table columns/rows.
3. Add category/source filters without disturbing existing risk/status filters.

- [ ] **Step 4: Run WebUI tests to verify pass**

Run: `node --test tests/webui/test_detail_panel.js`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add sharelife/webui/index.html sharelife/webui/app.js sharelife/webui/detail_panel.js tests/webui/test_detail_panel.js tests/e2e/sharelife_webui_e2e.cjs
git commit -m "feat: expose official catalog metadata in webui"
```

### Task 4: Update Docs

**Files:**
- Modify: `README.md`
- Modify: `docs/en/how-to/community-first-workflow.md`
- Modify: `docs/zh/how-to/community-first-workflow.md`
- Modify: `docs/ja/how-to/community-first-workflow.md`
- Modify: `docs/en/how-to/webui-page.md`
- Modify: `docs/zh/how-to/webui-page.md`
- Modify: `docs/ja/how-to/webui-page.md`

- [ ] **Step 1: Update docs**

Document:

1. The multi-domain official starter catalog.
2. Category/source browsing support.
3. Community-approved override behavior.

- [ ] **Step 2: Run docs build**

Run: `npm run docs:build --prefix docs`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add README.md docs/en/how-to/community-first-workflow.md docs/zh/how-to/community-first-workflow.md docs/ja/how-to/community-first-workflow.md docs/en/how-to/webui-page.md docs/zh/how-to/webui-page.md docs/ja/how-to/webui-page.md
git commit -m "docs: describe multi-domain official catalog"
```

### Task 5: Full Verification And Push

**Files:**
- Verify only

- [ ] **Step 1: Run Python test suite**

Run: `pytest -q`
Expected: PASS

- [ ] **Step 2: Run WebUI helper tests**

Run: `node --test tests/webui/test_detail_panel.js`
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
