# Market catalog prototype

Use this page as a read-only market prototype for UX checks.

## Scope

1. Public profile-pack filters for pack type, risk, featured state, and labels.
2. Compact catalog cards with source channel, compatibility, maintainer, and download path.
3. Download links point to sanitized public profile-pack artifacts only.
4. Data source: `/market/catalog.snapshot.json` with built-in fallback rows.

## Prototype

<MarketCatalogPrototype locale="en" />

## Notes

1. This prototype is read-only.
2. Snapshot source is `docs/public/market/catalog.snapshot.json`.
3. Admin moderation and apply/import actions stay in local WebUI.
4. Runtime compare cards are implemented in local WebUI (`/` + `/market`), not in this public prototype.
5. Locale is route-driven (`locale` prop), not `sharelife.uiLocale`.
6. Snapshot artifacts are generated from official examples plus approved public entry JSON by:

```bash
npm run docs:prepare:market --prefix docs
```
