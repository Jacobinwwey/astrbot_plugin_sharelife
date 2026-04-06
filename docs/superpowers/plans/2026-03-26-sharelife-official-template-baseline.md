# Sharelife Official Template Baseline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a bundled official template baseline so the plugin actually exposes standard templates from the repository without requiring prior community submissions.

**Architecture:** Keep the current market/install/package flow unchanged. Add a bundled `templates/index.json` asset in the repo, load it through a small bootstrap service at plugin startup, and publish official entries into `MarketService` only when no community-approved template already owns the same `template_id`.

**Tech Stack:** Python 3.12, pytest, existing `MarketService` / `PackageService`, JSON repo assets, AstrBot plugin bootstrap.

---

### Task 1: Add Failing Bootstrap Tests

**Files:**
- Modify: `tests/interfaces/test_main_commands.py`
- Create: `tests/meta/test_official_template_surface.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_plugin_bootstraps_bundled_official_template_into_market(tmp_path):
    ...


def test_repo_ships_bundled_official_templates_index():
    ...
```

- [ ] **Step 2: Run targeted tests to verify they fail**

Run: `pytest -q tests/interfaces/test_main_commands.py tests/meta/test_official_template_surface.py`
Expected: FAIL because the repo does not ship `templates/index.json` and plugin startup does not seed official templates into the market.

- [ ] **Step 3: Commit the failing-test checkpoint**

```bash
git add tests/interfaces/test_main_commands.py tests/meta/test_official_template_surface.py
git commit -m "test: cover bundled official template baseline"
```

### Task 2: Ship Bundled Official Template Assets And Startup Bootstrap

**Files:**
- Create: `templates/index.json`
- Modify: `sharelife/application/services_market.py`
- Create: `sharelife/application/services_registry_bootstrap.py`
- Modify: `main.py`
- Modify: `sharelife/domain/models.py`

- [ ] **Step 1: Write minimal implementation**

Add:

1. A bundled registry index with at least the baseline `community/basic` template and multilingual metadata.
2. A market-level method for seeding official published templates without fabricating community submissions.
3. A bootstrap service that loads bundled index data, validates entries, computes scan metadata where needed, and seeds templates only when no published entry already exists for the same `template_id`.
4. Plugin startup wiring in `main.py`.

- [ ] **Step 2: Run targeted tests to verify they pass**

Run: `pytest -q tests/interfaces/test_main_commands.py tests/meta/test_official_template_surface.py`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add templates/index.json sharelife/application/services_market.py sharelife/application/services_registry_bootstrap.py sharelife/domain/models.py main.py tests/interfaces/test_main_commands.py tests/meta/test_official_template_surface.py
git commit -m "feat: ship bundled official template baseline"
```

### Task 3: Document The Bundled Official Baseline

**Files:**
- Modify: `README.md`
- Modify: `docs/en/how-to/community-first-workflow.md`
- Modify: `docs/zh/how-to/community-first-workflow.md`
- Modify: `docs/ja/how-to/community-first-workflow.md`

- [ ] **Step 1: Update docs**

Document:

1. The repo now ships a bundled official baseline.
2. `community/basic` is available immediately after plugin startup.
3. Community-approved templates can still supersede the baseline by publishing the same `template_id`.

- [ ] **Step 2: Run docs build**

Run: `npm run docs:build --prefix docs`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add README.md docs/en/how-to/community-first-workflow.md docs/zh/how-to/community-first-workflow.md docs/ja/how-to/community-first-workflow.md
git commit -m "docs: document bundled official template baseline"
```

### Task 4: Full Verification

**Files:**
- Verify only

- [ ] **Step 1: Run targeted Python tests**

Run: `pytest -q tests/interfaces/test_main_commands.py tests/meta/test_official_template_surface.py`
Expected: PASS

- [ ] **Step 2: Run full Python suite**

Run: `pytest -q`
Expected: PASS

- [ ] **Step 3: Run docs build**

Run: `npm run docs:build --prefix docs`
Expected: PASS

- [ ] **Step 4: Review git diff**

Run: `git status --short && git diff --stat`
Expected: Only intended files changed.

- [ ] **Step 5: Commit**

```bash
git add .
git commit -m "feat: complete sharelife bundled official template baseline"
```
