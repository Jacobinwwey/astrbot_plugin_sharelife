# Sharelife GitHub Pages Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move the Sharelife docs site from EdgeOne-first publishing to GitHub Pages project-site publishing at `https://jacobinwwey.github.io/astrbot_plugin_sharelife/` while preserving rollback and a manual EdgeOne fallback path.

**Architecture:** Keep the docs site in the existing `docs/` VitePress app, add an explicit `DOCS_BASE`-driven base path for GitHub Pages, and publish through the standard GitHub Pages Actions artifact flow. Demote EdgeOne from default public publishing to a manual fallback path so the public docs entrypoint, README guidance, and localized how-to pages all point to one primary URL.

**Tech Stack:** VitePress, GitHub Actions Pages, Python repository surface tests, Bash, Markdown

---

## File Structure

- Modify: `docs/.vitepress/config.ts`
  Responsibility: read `DOCS_BASE`, keep `cleanUrls`, and switch how-to navigation to the GitHub Pages publishing guides.
- Create: `.github/workflows/deploy-docs-github-pages.yml`
  Responsibility: primary GitHub Pages build and deploy workflow with `push` + `workflow_dispatch` + `git_ref` rollback support.
- Modify: `.github/workflows/deploy-docs-edgeone.yml`
  Responsibility: retain EdgeOne as a manual fallback workflow only, no longer the default auto-publish path.
- Modify: `Makefile`
  Responsibility: expose local verification targets for GitHub Pages builds while keeping the manual EdgeOne publish target available.
- Modify: `README.md`
  Responsibility: document GitHub Pages as the public docs entrypoint and reframe EdgeOne as a fallback path.
- Create: `docs/zh/how-to/github-pages-publish.md`
  Responsibility: Chinese operator guide for GitHub Pages publish and rollback.
- Create: `docs/en/how-to/github-pages-publish.md`
  Responsibility: English operator guide for GitHub Pages publish and rollback.
- Create: `docs/ja/how-to/github-pages-publish.md`
  Responsibility: Japanese operator guide for GitHub Pages publish and rollback.
- Modify: `docs/zh/how-to/edgeone-publish.md`
  Responsibility: archive the old EdgeOne-first instructions and point readers to the new default path.
- Modify: `docs/en/how-to/edgeone-publish.md`
  Responsibility: archive the old EdgeOne-first instructions and point readers to the new default path.
- Modify: `docs/ja/how-to/edgeone-publish.md`
  Responsibility: archive the old EdgeOne-first instructions and point readers to the new default path.
- Create: `tests/meta/test_github_pages_publish_surface.py`
  Responsibility: assert the new GitHub Pages workflow, `DOCS_BASE` config, and public docs guidance surface.
- Modify: `tests/meta/test_edgeone_publish_surface.py`
  Responsibility: narrow EdgeOne assertions to the remaining manual fallback surfaces instead of the primary publish path.

---

### Task 1: Add GitHub Pages Surface Tests

**Files:**
- Create: `tests/meta/test_github_pages_publish_surface.py`
- Modify: `tests/meta/test_edgeone_publish_surface.py`

- [ ] **Step 1: Write the failing GitHub Pages workflow and config tests**

```python
from pathlib import Path
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_docs_config_uses_docs_base_with_project_site_default():
    text = (REPO_ROOT / "docs" / ".vitepress" / "config.ts").read_text(encoding="utf-8")
    assert "DOCS_BASE" in text
    assert "/astrbot_plugin_sharelife/" in text


def test_github_pages_workflow_exists_and_supports_git_ref():
    workflow_path = REPO_ROOT / ".github" / "workflows" / "deploy-docs-github-pages.yml"
    workflow = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
    assert "workflow_dispatch" in workflow["on"]
    assert "git_ref" in workflow["on"]["workflow_dispatch"]["inputs"]
```

- [ ] **Step 2: Narrow the EdgeOne surface test to backup-only expectations**

```python
def test_edgeone_workflow_is_manual_fallback_only():
    workflow_path = REPO_ROOT / ".github" / "workflows" / "deploy-docs-edgeone.yml"
    workflow = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
    assert "workflow_dispatch" in workflow["on"]
    assert "push" not in workflow["on"]
```

- [ ] **Step 3: Run the targeted surface tests and confirm they fail**

Run: `pytest tests/meta/test_github_pages_publish_surface.py tests/meta/test_edgeone_publish_surface.py -q`
Expected: FAIL because the GitHub Pages workflow and `DOCS_BASE` support do not exist yet.

- [ ] **Step 4: Commit the failing-test checkpoint**

```bash
git add tests/meta/test_github_pages_publish_surface.py tests/meta/test_edgeone_publish_surface.py
git commit -m "test: add GitHub Pages publish surface coverage"
```

### Task 2: Implement Base-Path Support And Primary GitHub Pages Workflow

**Files:**
- Modify: `docs/.vitepress/config.ts`
- Create: `.github/workflows/deploy-docs-github-pages.yml`
- Modify: `Makefile`
- Test: `tests/meta/test_github_pages_publish_surface.py`

- [ ] **Step 1: Add `DOCS_BASE` support to the VitePress config**

```ts
import { defineConfig } from 'vitepress'

const base = process.env.DOCS_BASE || '/astrbot_plugin_sharelife/'

export default defineConfig({
  base,
  cleanUrls: true,
  // keep existing locales and theme config
})
```

- [ ] **Step 2: Add the primary GitHub Pages workflow**

```yaml
name: deploy-docs-github-pages

on:
  push:
    branches: [main]
    paths:
      - 'docs/**'
      - 'README.md'
      - '.github/workflows/deploy-docs-github-pages.yml'
  workflow_dispatch:
    inputs:
      git_ref:
        description: 'Optional git ref for rollback or replay'
        required: false
        type: string

permissions:
  contents: read
  pages: write
  id-token: write
```

Implementation details to include:

- `actions/checkout@v6` with `fetch-depth: 0`
- `actions/setup-node@v6` with Node 24
- `actions/configure-pages@v6`
- `npm ci --prefix docs`
- `DOCS_BASE=/astrbot_plugin_sharelife/ npm run docs:build --prefix docs`
- `actions/upload-pages-artifact@v4` from `docs/.vitepress/dist`
- `actions/deploy-pages@v5`
- `environment: github-pages`
- `concurrency` guard for production deploys

- [ ] **Step 3: Add a local GitHub Pages build target to the Makefile**

```make
docs-build:
	npm run docs:build --prefix docs


docs-build-github-pages:
	DOCS_BASE=/astrbot_plugin_sharelife/ npm run docs:build --prefix docs
```

Keep the existing `docs-publish-edgeone` target unchanged for manual fallback use.

- [ ] **Step 4: Re-run the targeted surface tests and verify they pass**

Run: `pytest tests/meta/test_github_pages_publish_surface.py tests/meta/test_edgeone_publish_surface.py -q`
Expected: PASS

- [ ] **Step 5: Build the docs with the project-site base path**

Run: `make docs-build-github-pages`
Expected: `docs/.vitepress/dist` builds successfully, and generated HTML references `/astrbot_plugin_sharelife/` asset paths.

- [ ] **Step 6: Commit the workflow and config change**

```bash
git add docs/.vitepress/config.ts .github/workflows/deploy-docs-github-pages.yml Makefile
git commit -m "feat: add GitHub Pages docs deployment"
```

### Task 3: Migrate Public Docs Guidance To GitHub Pages

**Files:**
- Modify: `README.md`
- Create: `docs/zh/how-to/github-pages-publish.md`
- Create: `docs/en/how-to/github-pages-publish.md`
- Create: `docs/ja/how-to/github-pages-publish.md`
- Modify: `docs/zh/how-to/edgeone-publish.md`
- Modify: `docs/en/how-to/edgeone-publish.md`
- Modify: `docs/ja/how-to/edgeone-publish.md`
- Modify: `docs/.vitepress/config.ts`
- Test: `tests/meta/test_github_pages_publish_surface.py`

- [ ] **Step 1: Extend the GitHub Pages surface test to cover docs guidance**

```python
def test_localized_docs_point_to_github_pages_publish_guides():
    config_text = (REPO_ROOT / 'docs' / '.vitepress' / 'config.ts').read_text(encoding='utf-8')
    assert '/zh/how-to/github-pages-publish' in config_text
    assert '/en/how-to/github-pages-publish' in config_text
    assert '/ja/how-to/github-pages-publish' in config_text


def test_readme_names_the_github_pages_url():
    text = (REPO_ROOT / 'README.md').read_text(encoding='utf-8')
    assert 'https://jacobinwwey.github.io/astrbot_plugin_sharelife/' in text
```

- [ ] **Step 2: Run the targeted GitHub Pages test and confirm it fails**

Run: `pytest tests/meta/test_github_pages_publish_surface.py -q`
Expected: FAIL because the localized GitHub Pages how-to pages and README guidance do not exist yet.

- [ ] **Step 3: Write the new GitHub Pages how-to guides in all three locales**

Content each page must cover:

1. Public docs URL
2. Automatic `push -> deploy` behavior
3. Manual `workflow_dispatch` publish
4. Rollback by `git_ref`
5. Local verification with `make docs-build-github-pages`
6. EdgeOne is no longer the default public entrypoint

- [ ] **Step 4: Update the VitePress sidebar links to point to the new pages**

```ts
{ text: 'GitHub Pages 文档发布', link: '/zh/how-to/github-pages-publish' }
{ text: 'Publish Docs To GitHub Pages', link: '/en/how-to/github-pages-publish' }
{ text: 'GitHub Pages 公開', link: '/ja/how-to/github-pages-publish' }
```

Keep the archived EdgeOne pages out of the primary sidebar.

- [ ] **Step 5: Rewrite the README publishing section**

README requirements:

1. State GitHub Pages is the primary public site
2. Include the exact URL
3. Document the primary deploy workflow name
4. Document rollback by `git_ref`
5. Reframe EdgeOne as manual fallback, not default publishing

- [ ] **Step 6: Archive the old EdgeOne how-to pages instead of deleting them**

Add a short banner near the top of each localized EdgeOne page that says the default public docs path has moved to GitHub Pages and links to the new how-to page.

- [ ] **Step 7: Re-run the targeted GitHub Pages docs surface test**

Run: `pytest tests/meta/test_github_pages_publish_surface.py -q`
Expected: PASS

- [ ] **Step 8: Commit the docs migration**

```bash
git add README.md docs/.vitepress/config.ts docs/zh/how-to/github-pages-publish.md docs/en/how-to/github-pages-publish.md docs/ja/how-to/github-pages-publish.md docs/zh/how-to/edgeone-publish.md docs/en/how-to/edgeone-publish.md docs/ja/how-to/edgeone-publish.md tests/meta/test_github_pages_publish_surface.py
git commit -m "docs: move publish guidance to GitHub Pages"
```

### Task 4: Demote EdgeOne Automation To Manual Fallback

**Files:**
- Modify: `.github/workflows/deploy-docs-edgeone.yml`
- Modify: `tests/meta/test_edgeone_publish_surface.py`
- Test: `tests/meta/test_edgeone_publish_surface.py`

- [ ] **Step 1: Make the EdgeOne workflow manual-only**

Implementation target:

```yaml
on:
  workflow_dispatch:
    inputs:
      git_ref:
        description: 'Optional git ref to deploy for fallback replay'
        required: false
        type: string
```

Remove the `push` trigger so EdgeOne no longer competes with GitHub Pages as the primary publish path.

- [ ] **Step 2: Keep the shared EdgeOne deploy script path intact**

Do not remove `scripts/deploy_edgeone_docs.sh` or the `docs-publish-edgeone` Makefile target in this task.

- [ ] **Step 3: Re-run the EdgeOne fallback surface test**

Run: `pytest tests/meta/test_edgeone_publish_surface.py -q`
Expected: PASS

- [ ] **Step 4: Commit the fallback demotion**

```bash
git add .github/workflows/deploy-docs-edgeone.yml tests/meta/test_edgeone_publish_surface.py
git commit -m "chore: demote EdgeOne docs deploy to fallback"
```

### Task 5: Full Verification And Release Checkpoint

**Files:**
- Modify: repository files from Tasks 1-4
- Test: `tests/meta/test_github_pages_publish_surface.py`, `tests/meta/test_edgeone_publish_surface.py`, `pytest -q`, `npm run docs:build --prefix docs`, `make docs-build-github-pages`

- [ ] **Step 1: Run targeted meta tests**

Run: `pytest tests/meta/test_github_pages_publish_surface.py tests/meta/test_edgeone_publish_surface.py tests/meta/test_docs_command_surface.py -q`
Expected: PASS

- [ ] **Step 2: Run the full Python test suite**

Run: `pytest -q`
Expected: PASS

- [ ] **Step 3: Run the default docs build**

Run: `npm run docs:build --prefix docs`
Expected: PASS

- [ ] **Step 4: Run the GitHub Pages docs build**

Run: `make docs-build-github-pages`
Expected: PASS

- [ ] **Step 5: Spot-check the built HTML base path**

Run: `rg -n "/astrbot_plugin_sharelife/(assets|zh/|en/|ja/)" docs/.vitepress/dist -g '*.html'`
Expected: matches in generated HTML output.

- [ ] **Step 6: Commit the verification checkpoint**

```bash
git add -A
git commit -m "test: verify GitHub Pages docs migration"
```
