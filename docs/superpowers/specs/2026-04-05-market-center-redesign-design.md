# 2026-04-06 v1.2 - Sharelife Market Center Entry Redesign Design

## Time and Version Number

- Date: 2026-04-06
- Version: v1.2
- Status: Updated for implementation
- Canonical language: English
- Localized companions:
  - `docs/superpowers/specs/2026-04-05-market-center-redesign-design.zh-CN.md`
  - `docs/superpowers/specs/2026-04-05-market-center-redesign-design.ja-JP.md`

### Context

`/market` already exists as a standalone Sharelife WebUI route, but the current page still mixes two different jobs:

1. Public catalog browsing.
2. Member-side trial, install, submit, and local-state operations.

That weakens the page in both directions. It does not read cleanly as a public market entry, and it also makes the first screen heavier than necessary for users who only want to browse packs.

The user asked for a deeper market-center refactor with these product constraints:

1. Work in a fresh clone and clean branch.
2. Treat `/market` as the primary slice.
3. Make the first screen public-read-only first.
4. Move member actions behind a card-click detail layer.
5. Do not build always-on compare in the first slice.
6. Use the reference direction of a high-density console, but change the information hierarchy.
7. Later use Stitch MCP to generate at least five detail-layer variants, wait five minutes before fetching them, and make those variants one-click switchable for comparison.

### Goal

Turn `/market` into a clear public market entry that is optimized for browsing and discovery first, while preserving a clean handoff into authenticated member actions after a user opens a specific pack.

### Scope

This design covers:

1. The information architecture of the standalone `/market` page.
2. The card-level contract for the public catalog grid.
3. The detail-layer contract that will hold member actions after card click.
4. The staged execution boundary between the hand-built market entry and later Stitch-generated detail variants.
5. The key constraints needed to preserve existing runtime IDs, API wiring, and tests.

This design does not cover:

1. Refactoring `/`, `/member`, or `/admin` in the same slice.
2. Reintroducing always-on compare in the first slice.
3. Reworking backend market APIs unless the existing payload shape blocks the UI contract.
4. Final visual design of the detail layer before Stitch generation.
5. Any permanent new market ranking system, personalization, or favorites flow.

### Approaches Considered

#### Approach A: Editorial public hub

Pros:

1. Strongest public landing-page feel.
2. Makes featured packs and trust messaging easy to emphasize.

Cons:

1. Weaker at dense catalog browsing.
2. Moves too far away from the existing market-page structure.
3. Adds more layout churn than needed for the first slice.

#### Approach B: Curated catalog console

Pros:

1. Best fit for the reference direction and current `/market` code shape.
2. Preserves high-density browsing while cleaning up action boundaries.
3. Makes later Stitch detail-layer work easier because the list layer stays stable.

Cons:

1. Needs careful hierarchy so it reads like a public market, not a local control room.

#### Approach C: Hybrid landing plus results

Pros:

1. Stronger brand statement than a pure console.
2. Easier to foreground trust and review-process messaging.

Cons:

1. Heavier first screen.
2. Risks diluting search and browsing efficiency.
3. Higher redesign cost for the first slice.

### Decision

Use Approach B: curated catalog console.

The standalone market page should keep the efficient catalog-console structure, but change its semantics from "mixed operations dashboard" to "public market entry." Public browsing becomes the first-screen job. Member actions move behind a card-open detail layer.

### Design

#### 1. Entry Positioning

`/market` becomes the public-read-only front door for the Sharelife market.

On first load, the page should emphasize:

1. What Sharelife Market is.
2. How to browse it.
3. Why the catalog can be trusted.

It should not emphasize:

1. Local installation state refresh.
2. Immediate install or upload actions.
3. Role-specific operations before the user has selected a pack.

#### 2. Information Architecture

The first screen should be reorganized into three stacked layers above the catalog results:

1. Brand and context header.
2. Spotlight-style global search.
3. Result controls.

Below that, the main catalog area remains a two-column structure:

1. Compact left filter rail.
2. Right-side card grid.

#### 3. Header Layer

The header layer should be slimmer and more public in tone than the current top utility bar.

It should contain:

1. `Sharelife` brand mark and market title.
2. A short public-market positioning line.
3. Locale switch.
4. Documentation link and other public-read-only links.

It should remove or demote from the first screen:

1. `Refresh Local Installations`.
2. Member or admin operation emphasis.
3. Upload/install/trial CTAs.

If cross-console links remain, they should read as secondary navigation rather than primary actions.

#### 4. Spotlight-Style Search Layer

The search field becomes the main visual anchor of the page.

Placement:

1. Directly below the main entry header.
2. Above the sort/results row.
3. Wide enough to feel closer to Spotlight or Raycast than to a utility-table filter input.

Behavior:

1. Embedded in-page, not a floating overlay.
2. Searches across `pack_id`, title-like labels, maintainer, tags, review labels, warning flags, compatibility, and summary text where available.
3. Updates the visible grid without changing the page into an authenticated workflow.

Product intent:

1. It should make discovery feel primary.
2. It should reduce the sense that the page is a dense operation console first.

#### 5. Result Controls Layer

The row under the search field should contain only result-navigation controls.

Keep:

1. Sort choice.
2. Result count.
3. Optional view toggle if the current code already supports it cleanly.

Do not mix into this row:

1. Install actions.
2. Upload actions.
3. Auth-first controls.
4. Local installation refresh.

If a refresh affordance is still needed, it should be reframed as catalog refresh rather than local-installation refresh.

#### 6. Filter Rail

The left rail stays because it matches the chosen console direction and existing page structure.

The rail should remain limited to public browsing filters such as:

1. Pack type.
2. Risk level.
3. Compatibility.
4. Featured state.
5. Review labels.
6. Warning flags.

The rail should not become a second control panel for member operations.

#### 7. Catalog Card Contract

The public card layer should answer a narrow question:

What is this pack, how risky is it, and should I open it for more detail?

Each card should expose only public-read-only metadata needed for browsing:

1. Pack identifier or display title.
2. Pack type.
3. Version.
4. Maintainer.
5. Compatibility status.
6. Risk level.
7. Short summary.
8. A small set of tags and review/warning indicators.
9. Lightweight metrics such as section count, label count, or update recency when helpful.

The card layer should not expose direct member action buttons for:

1. Try.
2. Install.
3. Upload.
4. Member login or local environment checks.

Its primary action should be a single detail-opening affordance, for example:

1. Clicking the card.
2. Clicking a `View Details` button.

#### 8. Detail-Layer Contract

Opening a card should move the user into a second-layer surface.

Default form:

1. Desktop uses a right-side detail drawer.
2. Mobile uses a full-screen sheet.

This layer is where deeper information and member actions begin.

The detail layer should be the first place that can show:

1. Try.
2. Install.
3. Upload-related actions or links.
4. Member-only environment notices.
5. Authentication prompts if required.
6. Install-time section-sync choices before the protected install step runs.

Public detail content should remain readable without login. Authentication should be requested only when the user triggers a member action such as try, install, or upload-related flow.

Install must support section-selective sync in the detail layer. Stateful or local-data sections such as `memory_store`, `conversation_history`, and `knowledge_base` should be visible as optional sync targets that the user may intentionally skip during install.

The detail layer should consume a stable data contract based on the existing catalog/detail payload shape:

1. `pack_id`
2. display title if present
3. `version`
4. `maintainer`
5. `pack_type`
6. `risk_level`
7. `compatibility`
8. `review_labels`
9. `warning_flags`
10. `sections`
11. summary or description
12. updated-at style metadata
13. any existing public audit or source facts already returned by the API

This detail-layer contract should stay stable even when the visual layout changes later through Stitch.

#### 9. Two-Phase Delivery

##### Phase 1: Hand-built public entry refactor

Implement:

1. Header rewrite.
2. Spotlight-style search placement.
3. Clean result-controls row.
4. Public-only filter rail.
5. Public card contract.
6. Click-to-open detail-layer shell.

Do not implement in this phase:

1. Always-on compare.
2. Final highly designed detail-layer variants.
3. Broad refactors across other WebUI pages.

##### Phase 2: Stitch-generated detail variants

After the main entry and detail-layer contract are stable, use Stitch MCP for the detail layer only.

The first-screen market entry remains hand-integrated production HTML/CSS/JS. The detail layer is the visual surface that gets variant exploration.

#### 10. Stitch Generation Rules

When the project reaches the detail-layer generation step, use these rules:

1. Generate at least five variants in one run target.
2. The variants must all represent the same detail-layer job, not five unrelated screens.
3. After the Stitch generation call, wait five minutes before fetching the result.
4. If Stitch returns suggestion-style output instead of final variants, accept the needed follow-up path but still drive toward at least five usable variants.
5. The resulting variants must be easy to compare from a single opened pack context.
6. The generated detail direction must leave room for install-time section sync choices and must not imply that every declared section is always mandatory.

The production requirement is not "five separate dead-end mockups." The production requirement is "five detail-layer options that can be switched with one click for comparison."

Recommended production affordance:

1. A segmented control or tab strip such as `Variant 1`, `Variant 2`, `Variant 3`, `Variant 4`, `Variant 5`.
2. Switching should keep the same selected pack context and swap only the detail presentation.

##### Stitch MCP Pre-Call Gate

Before any Stitch MCP call is allowed for this slice:

1. The team must first finalize the improved Stitch MCP instruction set for the exact target being generated.
2. That instruction set must not live only in chat history. It must be written into a module-local `Design.md`.
3. The `Design.md` must live under an independent folder for the frontend adjustment module that owns the Stitch-generated surface.
4. For this market-center slice, the Stitch-owned target is the detail layer, not the first-screen market entry.
5. The module-local `Design.md` must record at least:
   1. target surface and user job
   2. required data contract
   3. DOM/runtime constraints that cannot be broken
   4. the finalized Stitch MCP prompt or instruction block
   5. expected variant count and comparison behavior
   6. acceptance checks after generation
   7. the latest approved market-center baseline and the current install-time section-sync rules
6. Only after that `Design.md` exists and is reviewed may the Stitch generation call be issued.

#### 11. Runtime Constraints To Preserve

The refactor should preserve the current architecture wherever possible:

1. Keep `/market` on the existing standalone route.
2. Reuse current `market.html`, `market_page.js`, `market_cards.js`, and `style.css` structure unless a focused split is needed.
3. Preserve DOM IDs and hooks relied on by current JS and tests unless a test-backed rename is deliberate.
4. Keep locale behavior consistent with current WebUI i18n support.
5. Preserve the current catalog source strategy between runtime catalog data and public snapshot data.

#### 12. Risks

Main risks:

1. The page could still feel too operational if old action affordances remain visually dominant.
2. Search could become shallow if it only filters pack IDs and ignores other public metadata.
3. The detail layer could become over-coupled to a temporary hand-built layout, making Stitch replacement expensive.
4. Existing JS wiring could break if markup changes remove required IDs or expected containers.

Mitigations:

1. Remove high-priority member actions from the first screen.
2. Define and test the search fields explicitly.
3. Treat the detail layer as a stable data contract plus replaceable presentation shell.
4. Add targeted WebUI tests before changing production code.

#### 13. Testing Strategy

Before production changes, add or extend tests for:

1. Market card view-model behavior that supports the new public card contract.
2. Search behavior over the chosen metadata fields.
3. Separation between first-screen public browsing and detail-layer member actions.
4. Any new detail-layer state and variant-switching shell introduced before Stitch visuals land.

Visual verification should confirm:

1. The search field is visually primary.
2. The first screen reads as a public catalog, not a member operations page.
3. Cards do not expose direct install/trial/upload actions.
4. Clicking a card is the clear path into deeper actions.

### Success Criteria

This redesign slice is complete when:

1. `/market` reads as a public-read-only market entry on first load.
2. The global Spotlight-style search sits under the entry header and above the sort row.
3. The first screen supports browsing, filtering, and search without exposing member actions directly on cards.
4. Clicking a card opens a stable detail-layer shell that is ready to host member actions.
5. The detail-layer contract is stable enough to support later Stitch generation without rewriting the list layer.
6. The later Stitch step can produce at least five detail variants and make them one-click switchable for comparison.
