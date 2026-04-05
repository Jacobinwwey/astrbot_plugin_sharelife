# Public market read-only hub

This page defines the boundary between public market pages and local privileged operations.

## Objective

1. Publish a usable public catalog.
2. Keep admin-level operations local.

## Related page

[Market Catalog Prototype](/en/how-to/market-catalog-prototype)

## Deployment baseline

Primary path:

1. Branch: `main`
2. Deploy: GitHub Actions -> GitHub Pages
3. URL: `https://jacobinwwey.github.io/astrbot_plugin_sharelife/`

Optional fallback:

1. Keep static snapshots in archive branch for history.
2. Do not use archive branch as primary serving source.

## What public pages can include

1. Template/profile-pack metadata
2. Risk labels and compatibility notes
3. Download links and import guidance
4. Locale-specific copy (`en` / `zh` / `ja`)
5. Sanitized official/community profile-pack artifacts only

## What public pages must not include

1. Admin decision actions
2. Apply/rollback actions
3. Privileged token/auth management
4. Hardcoded mixed-language UI labels

## Locale baseline

1. Public docs should use route/page locale as source of truth.
2. Do not bind docs pages to `sharelife.uiLocale`.
3. Keep `/en`, `/zh`, `/ja` dictionaries aligned.

## Handoff to local WebUI

1. Browse and download in public hub.
2. Import in local Sharelife WebUI.
3. Run dry-run and selective apply locally.

## Approved community publish

1. Only sanitized profile-pack archives may be published publicly.
2. Promote an approved pack with:

```bash
python3 scripts/publish_public_market_pack.py \
  --artifact /abs/path/to/sanitized-pack.zip \
  --pack-id profile/community-example \
  --version 1.0.0 \
  --title "Community Example" \
  --description "Approved community pack" \
  --maintainer community \
  --review-label approved \
  --review-label risk_low
```

3. The script writes `docs/public/market/entries/*.json` and rebuilds `catalog.snapshot.json`.

## Cold backup

1. Public market cold backup covers only `docs/public/market/`.
2. Archive or sync it with:

```bash
python3 scripts/backup_public_market.py \
  --archive-output-dir output/public-market-backups \
  --remote gdrive:/sharelife/public-market
```

3. GitHub Actions workflow `public-market-backup.yml` can run this on a schedule when rclone secrets are configured.

## Reviewer access

1. Reviewer execution is not public.
2. If you want reviewer access, contact `Jacobinwwey` first and wait for an invite.
