# Public Market Read-Only Hub

This page defines the public boundary for the market surface.

## Objective

1. Publish a usable catalog.
2. Keep privileged execution local.
3. Hand users off cleanly into the member WebUI for install or submission.

## Related page

[Market Catalog Prototype](/en/how-to/market-catalog-prototype)

## What public pages can include

1. template/profile-pack metadata
2. risk labels and compatibility notes
3. detail + compare views
4. download/import guidance
5. locale-specific copy (`en` / `zh` / `ja`)
6. sanitized official/community artifacts only

## What public pages must not include

1. moderation decision actions
2. privileged apply/rollback actions
3. privileged auth or secret management
4. operator backup/restore procedures
5. featured curation controls

## Current public surface

As of `2026-04-07`, the public market surface is expected to behave as follows:

1. Spotlight-style search is the first interaction.
2. Catalog cards are public read-only.
3. `Detail & Compare` can stay visible for pack selection and section review.
4. Protected member actions stay inside the local `/member` or `/market` WebUI surfaces and do not become public first-screen controls.

## Handoff to local WebUI

1. Browse in the public hub.
2. Open the local Sharelife WebUI.
3. Use `/member` or `/market` for protected actions.
4. Authenticate as `member` if auth is enabled.
5. Continue with one of these local flows:
   - install with `preflight` / `force_reinstall` / `source_preference`
   - template upload with `scan_mode` / `visibility` / `replace_existing`
   - profile-pack community submit with `artifact_id` and `submit_options`
6. Track your own submissions from the member-scoped lists.

## Upload chain notes

1. Template package upload is capped at `20 MiB`.
2. Profile-pack community submission is currently `artifact_id`-based on the main branch.
3. Public pages can explain the handoff, but they must not expose privileged operator actions.

## Locale baseline

1. Public docs use route locale as the source of truth.
2. Do not bind public docs pages to local operator state.
3. Keep `/en`, `/zh`, and `/ja` aligned on public boundary language.

## Invitation-only roles

1. Public pages do not expose review or operations controls.
2. Invitation-only review access is coordinated privately; contact `Jacobinwwey` if needed.
