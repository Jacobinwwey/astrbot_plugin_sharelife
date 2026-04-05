# Sharelife Bot Profile Pack Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a safe `bot_profile_pack` Phase 1 baseline with export/import, default secret redaction, dry-run diff, and rollback-ready selective apply.

**Architecture:** Add a dedicated profile-pack service and section-adapter registry under existing `application`/`domain` boundaries. Reuse existing package storage, scan service, audit service, and apply guard pipeline instead of introducing a second governance subsystem.

**Tech Stack:** Python 3.12, pytest, existing Sharelife services (`services_package`, `services_scan`, `services_apply`, `services_audit`), Web API v1, standalone WebUI.

---

### Task 1: Domain Models And Validation For Bot Profile Pack

**Files:**
- Create: `sharelife/domain/profile_pack_models.py`
- Modify: `sharelife/domain/models.py`
- Create: `tests/domain/test_profile_pack_models.py`

- [ ] **Step 1: Write failing tests for manifest schema and policy defaults**
- [ ] **Step 2: Run tests to confirm failure**
- [ ] **Step 3: Implement models for `BotProfilePackManifest`, section metadata, redaction policy**
- [ ] **Step 4: Run tests to confirm pass**
- [ ] **Step 5: Commit**

### Task 2: Section Adapter Registry And Safe Redaction

**Files:**
- Create: `sharelife/application/services_profile_section_registry.py`
- Create: `sharelife/application/services_profile_redaction.py`
- Create: `tests/application/test_profile_section_registry.py`

- [ ] **Step 1: Write failing tests for section whitelist and sensitive-key masking**
- [ ] **Step 2: Run tests to confirm failure**
- [ ] **Step 3: Implement adapter registry + default redaction policy**
- [ ] **Step 4: Run tests to confirm pass**
- [ ] **Step 5: Commit**

### Task 3: Profile Pack Export/Import Service

**Files:**
- Create: `sharelife/application/services_profile_pack.py`
- Modify: `sharelife/application/services_package.py`
- Create: `tests/application/test_profile_pack_service.py`

- [ ] **Step 1: Write failing tests for zip layout (`manifest.json`, `sections/*.json`) and parse flow**
- [ ] **Step 2: Run tests to confirm failure**
- [ ] **Step 3: Implement export and import parsing with compatibility checks**
- [ ] **Step 4: Integrate scan summary generation for imported payload**
- [ ] **Step 5: Run tests to confirm pass**
- [ ] **Step 6: Commit**

### Task 4: Dry-Run Diff And Selective Apply Plan

**Files:**
- Create: `sharelife/application/services_profile_diff.py`
- Modify: `sharelife/application/services_apply.py`
- Create: `tests/application/test_profile_diff_apply.py`

- [ ] **Step 1: Write failing tests for per-section dry-run diff and selected-section apply**
- [ ] **Step 2: Run tests to confirm failure**
- [ ] **Step 3: Implement diff model and selective patch plan generation**
- [ ] **Step 4: Reuse rollback guard from apply service for profile apply path**
- [ ] **Step 5: Run tests to confirm pass**
- [ ] **Step 6: Commit**

### Task 5: API/Command Surface

**Files:**
- Modify: `sharelife/interfaces/api_v1.py`
- Modify: `sharelife/interfaces/web_api_v1.py`
- Modify: `sharelife/interfaces/commands_admin.py`
- Modify: `main.py`
- Create: `tests/interfaces/test_profile_pack_api_surface.py`
- Modify: `tests/interfaces/test_main_commands.py`

- [ ] **Step 1: Write failing tests for profile-pack export/import/dry-run/apply endpoints and commands**
- [ ] **Step 2: Run tests to confirm failure**
- [ ] **Step 3: Implement API methods and command mappings**
- [ ] **Step 4: Add audit events for export/import/dry-run/apply actions**
- [ ] **Step 5: Run tests to confirm pass**
- [ ] **Step 6: Commit**

### Task 6: WebUI Phase 1 Panel (minimal)

**Files:**
- Modify: `sharelife/webui/index.html`
- Modify: `sharelife/webui/app.js`
- Create: `sharelife/webui/profile_pack_panel.js`
- Create: `tests/webui/test_profile_pack_panel.js`

- [ ] **Step 1: Write failing tests for section selection payload and dry-run summary rendering**
- [ ] **Step 2: Run WebUI tests to confirm failure**
- [ ] **Step 3: Implement minimal panel and API wiring**
- [ ] **Step 4: Run WebUI tests to confirm pass**
- [ ] **Step 5: Commit**

### Task 7: Documentation And Guardrails

**Files:**
- Modify: `README.md`
- Modify: `docs/en/how-to/community-first-workflow.md`
- Modify: `docs/zh/how-to/community-first-workflow.md`
- Modify: `docs/ja/how-to/community-first-workflow.md`
- Create: `docs/en/how-to/bot-profile-pack.md`
- Create: `docs/zh/how-to/bot-profile-pack.md`
- Create: `docs/ja/how-to/bot-profile-pack.md`

- [ ] **Step 1: Document pack structure, redaction policy, and admin-only apply controls**
- [ ] **Step 2: Add Phase 1 limitations and future-phase roadmap notes**
- [ ] **Step 3: Run docs build**
- [ ] **Step 4: Commit**

### Task 8: Full Verification And Push

**Files:**
- Verify only

- [ ] **Step 1: Run Python tests**
Run: `pytest -q`

- [ ] **Step 2: Run WebUI tests**
Run: `node --test tests/webui/*.js`

- [ ] **Step 3: Run docs build**
Run: `npm run docs:build --prefix docs`

- [ ] **Step 4: Review diff scope**
Run: `git status --short && git diff --stat`

- [ ] **Step 5: Push branch**
Run: `git push --set-upstream origin feature/sharelife-bot-profile-pack-v1`

## Phase 1 Done Criteria

1. `bot_profile_pack` export/import pipeline exists and passes tests.
2. Default export never emits plaintext credentials.
3. Dry-run diff can be reviewed before apply.
4. Selective apply supports rollback path on failure.
5. API/commands/WebUI provide minimum operator loop for personal/community usage.

## Follow-up Baseline (locked after Phase 1)

1. Public market pages deployment strategy is fixed in:
`docs/superpowers/plans/2026-03-30-sharelife-market-deployment-strategy.md`
2. Primary docs/market publishing path is GitHub Pages via GitHub Actions.
3. `gh-pages`-style branch hosting is retained only as optional archive fallback, not primary serving path.
