# Publish docs to GitHub Pages

## Public URL

`https://jacobinwwey.github.io/astrbot_plugin_sharelife/`

## Automatic deployment

Primary workflow:

1. File: `.github/workflows/deploy-docs-github-pages.yml`
2. Workflow name: `deploy-docs-github-pages`

Default behavior:

1. Qualifying push to `main` triggers build and deploy.
2. Path filter includes `docs/**`, `README.md`, and the workflow file itself.
3. Build uses `DOCS_BASE=/astrbot_plugin_sharelife/` for project site path.

Prerequisites:

1. `Settings -> Pages -> Build and deployment -> Source = GitHub Actions`
2. Optional bootstrap secret: `PAGES_ENABLEMENT_TOKEN` (repo-admin PAT)

## Manual deploy

1. Open `deploy-docs-github-pages` workflow.
2. Run `workflow_dispatch`.
3. Optional: set `git_ref` to a specific commit/tag/branch.

If you see `Get Pages site failed`, enable Pages first, then rerun.

## Rollback

1. Run workflow manually.
2. Set `git_ref` to a known-good commit/tag.
3. Publish again.

## Local verification

```bash
make docs-build-github-pages
```

This matches the production `DOCS_BASE` behavior.
