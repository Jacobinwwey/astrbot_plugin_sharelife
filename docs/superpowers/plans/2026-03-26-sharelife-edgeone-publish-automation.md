# Sharelife EdgeOne Publish Automation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a stable one-command local EdgeOne publish entry, an automated GitHub Actions publish workflow, and explicit publish/rollback docs for the Sharelife community docs site.

**Architecture:** Keep local publishing centered on `scripts/deploy_edgeone_docs.sh`, but harden it with sane defaults for the fixed project name and token aliases. Add a dedicated deploy workflow under `.github/workflows/` that builds docs and calls the same script so local and CI deployments stay on one path. Document manual publish, CI publish, and rollback using redeploy-by-ref so operators do not need to reverse-engineer EdgeOne behavior.

**Tech Stack:** Bash, GitHub Actions, VitePress, PyYAML-backed repository tests

---

### Task 1: Harden Local EdgeOne Publish Entry

**Files:**
- Modify: `scripts/deploy_edgeone_docs.sh`
- Create: `Makefile`
- Test: `tests/meta/test_edgeone_publish_surface.py`

- [ ] **Step 1: Write failing tests for script defaults and root publish target**
- [ ] **Step 2: Run targeted tests to verify they fail**
- [ ] **Step 3: Add `sharelife-docs` default project name and token alias fallback to the deploy script**
- [ ] **Step 4: Add a root `make docs-publish-edgeone` entry that calls the deploy script**
- [ ] **Step 5: Re-run targeted tests to verify they pass**

### Task 2: Add GitHub Actions EdgeOne Deploy Workflow

**Files:**
- Create: `.github/workflows/deploy-docs-edgeone.yml`
- Test: `tests/meta/test_edgeone_publish_surface.py`

- [ ] **Step 1: Write failing workflow assertions**
- [ ] **Step 2: Run targeted tests to verify they fail**
- [ ] **Step 3: Add a deploy workflow with `push` and `workflow_dispatch`, support manual `git_ref`, and call the shared deploy script**
- [ ] **Step 4: Re-run targeted tests to verify they pass**

### Task 3: Add Publish And Rollback Docs

**Files:**
- Create: `docs/en/how-to/edgeone-publish.md`
- Create: `docs/zh/how-to/edgeone-publish.md`
- Create: `docs/ja/how-to/edgeone-publish.md`
- Modify: `docs/.vitepress/config.ts`
- Modify: `README.md`
- Test: `npm run docs:build --prefix docs`

- [ ] **Step 1: Write docs pages for local publish, CI publish, and rollback by ref**
- [ ] **Step 2: Add them to the VitePress sidebar and README release section**
- [ ] **Step 3: Run docs build to verify navigation and links stay valid**

### Task 4: Full Verification And Release

**Files:**
- Modify: repository files from Tasks 1-3
- Test: `tests/meta/test_edgeone_publish_surface.py`, `pytest -q`, `npm run docs:build --prefix docs`

- [ ] **Step 1: Run targeted repository tests**
- [ ] **Step 2: Run full test suite**
- [ ] **Step 3: Build docs**
- [ ] **Step 4: Commit with a focused message**
