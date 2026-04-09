# 2026-04-06 v2.1 - Sharelife Market Detail Layer Stitch Design

## Meta

- Date: 2026-04-06
- Version: v2.1
- Status: Current baseline confirmed in Stitch; five-variant regeneration requested
- Canonical language: English
- Localized companions:
  - `sharelife/webui/market_detail/Design.zh-CN.md`
  - `sharelife/webui/market_detail/Design.ja-JP.md`

This file is the canonical Stitch prompt source for the market-detail module.
Do not mix multiple languages into this file again. Keep localized guidance in the companion files.

## Target Surface and User Job

The target is the market detail layer opened from a selected `/market` card.

The user job is:

1. understand what the selected pack is
2. review public facts and risk signals
3. choose a member action such as try, install, compare, or download
4. adjust install sync scope without leaving the selected pack context

## Current Market Center Baseline

This detail layer must derive from the current implemented `/market` baseline, not from any older Sharelife market-hub screen.

The current market-center baseline is:

1. a public-first entry, not a mixed operations dashboard
2. a compact editorial-technical header with brand, locale, trust chips, and health/auth context
3. a large Spotlight-like search field as the main visual anchor
4. a restrained result-control row below the search field
5. a filter rail plus public card grid as the browse surface
6. a detail shell that opens only after card selection

The detail layer must feel like the next depth level of this exact baseline.

It must not feel like:

1. a separate product page
2. a new dashboard invented from scratch
3. a marketing modal
4. a generic SaaS detail card stack

## Required Data Contract

The detail layer must keep using the approved stable contract:

1. `pack_id`
2. display title when present
3. `version`
4. `maintainer`
5. `pack_type`
6. `risk_level`
7. `compatibility`
8. `review_labels`
9. `warning_flags`
10. `sections`
11. summary or description
12. updated-at metadata
13. public audit/source facts

## DOM and Runtime Constraints

The generated visual treatment must not break these containers and expectations:

1. `marketDetailArea`
2. `marketDetailControlStore`
3. `marketDetailActionCluster`
4. `marketDetailInstallSectionsShell`
5. `marketDetailInstallOptionsShell`
6. `marketSummary`

The detail layer must preserve:

1. desktop drawer and mobile sheet behavior
2. pack-context retention while switching variants
3. auth gating only when a member action is triggered
4. compatibility with standalone script loading and globalScope exports

## Derived Detail Layer Rules

The detail layer must strongly inherit the current market-center baseline.

That inheritance means:

1. continue the same monochrome technical-editorial visual language
2. continue the same hierarchy discipline: public facts first, actions second
3. continue the same interaction semantics: browse on the page, act in the detail layer
4. continue the same tonal restraint and avoid dramatic style resets
5. keep the action rail feeling native to the current page, not bolted on
6. merge the shipped action controls into the main detail panel instead of leaving a second member-actions card below it

Allowed variation:

1. rearrange the internal composition of the detail layer
2. change whether trust, facts, or actions lead within the drawer
3. change how evidence and metadata are grouped

Not allowed:

1. changing the overall product personality away from the current market center
2. introducing a radically different visual system
3. making the detail layer feel more important than the page it came from
4. using an older Stitch market-hub design as a stylistic source

## Finalized Stitch MCP Prompt Block

This block must be finalized here before the actual Stitch call. The call must not rely on chat-only instructions.

Use this exact generation direction:

```text
Design a Sharelife market detail layer for a selected profile pack. This is not a full page and not a dashboard. It is a detail drawer on desktop and a full-screen sheet on mobile, opened after clicking a market card.

The surface must support one selected pack context and must keep that context stable while the user switches among five variants.

Use the currently implemented Sharelife market center as the only visual source-of-truth. The detail layer must read as a derived second layer of that exact market center, not as a separate product page or a redesign of an older market hub.

Required information zones:
1. pack identity: pack_id, display title, version, maintainer, pack_type
2. trust and compatibility: risk_level, compatibility, review_labels, warning_flags
3. public facts: sections, summary/description, update metadata, public source/audit facts
4. member actions: try, install, compare, download

Critical product rules:
1. first-screen public market entry is already built and is the baseline; do not redesign the whole market page
2. this target is only the clicked-card detail layer
3. strongly inherit the current market center's monochrome technical-editorial language
4. keep the interaction feel professional, high-density, restrained, and intentional
5. avoid generic SaaS cards, decorative clutter, and dramatic visual resets
6. preserve a clear member action rail
7. public facts should remain readable before login; authentication should only be required when the user actually triggers a member action
8. install-related member actions must clearly allow section-selective sync before execution
9. stateful or local-data sections such as memory_store, conversation_history, and knowledge_base must read as optional sync targets rather than mandatory payload
10. upload and submission flows belong to the user panel, not this detail layer
11. internal Stitch variants may still exist for design comparison, but the shipped detail layer must not expose a visible Variant 1-5 switch row

Generate five clearly different variants of this same detail-layer job:
- Variant 1: editorial evidence-first
- Variant 2: dense operator console
- Variant 3: split facts vs actions
- Variant 4: trust/risk first
- Variant 5: action checklist first

Each variant should feel materially different in hierarchy and composition, but all must remain compatible with the same stable data contract and runtime shell.
```

## Expected Variant Count and Comparison Behavior

Required internal design output:

1. `variant_1`
2. `variant_2`
3. `variant_3`
4. `variant_4`
5. `variant_5`

These variants are retained as design references and implementation comparison inputs. They are no longer a mandatory end-user switch row inside the shipped detail page.

## Current Native Implementation Direction

The active local implementation direction is now anchored on `variant_3`.

This means:

1. `variant_3` is now the first native detail impression to refine
2. the local renderer must translate the approved Stitch split-layout reference into a native Sharelife detail-shell section
3. the native `variant_3` should keep public facts on the left and member-action readiness on the right
4. actual protected actions now live inside the `Action readiness` block in the main panel, not in a separate card below the viewport
5. install-time selective section sync is part of the native member-action flow, not a detached wizard
6. stateful or local-data sections such as `memory_store`, `conversation_history`, and `knowledge_base` may be intentionally deselected and skipped during install
7. before any future Stitch call for this module, this `Design.md` must first be updated to match the latest market-center baseline and the current member-action rules
8. future Stitch or local iterations must preserve this inheritance chain instead of drifting back toward generic placeholder shells
9. native `variant_1`, `variant_2`, `variant_4`, and `variant_5` should also be implemented as V3-derived detail compositions, not thin link-only placeholders detached from the active shell
10. the install-sync section is the only section-centric block in the detail viewport; do not duplicate it with a separate declared-sections block
11. do not place upload or submit UI in the detail layer when the member panel already owns those flows
12. the install source / preflight / force-reinstall controls plus the local-installations state and list sit between install-sync and review-signal sections inside the main panel

## Acceptance Checks

After generation and integration:

1. the selected pack context stays stable across variant switches
2. member action rail remains usable
3. no variant removes required public facts
4. no variant breaks the standalone WebUI script/runtime model
5. the generated result must visibly look derived from the current market-center baseline
6. if a generated variant drifts toward an older market hub language, reject it

## Historical Note

Previous generation session `14909211256281812924` and the later archived project `projects/614617403044256572` are misaligned references only.

They may still be useful for comparison history, but they must not be reused as the current visual baseline.

## Active Stitch Baseline

Current approved-on-fetch baseline project: `projects/1791941634823407461`

Current approved-on-fetch baseline screen:

1. `detail_baseline`: `3ef1d2a12c3449f593141520a70ec987`

Current baseline title:

1. `Sharelife Market Detail Concept`

Current five-variant regeneration result:

1. variant session: `14727920063696137864`
2. `variant_1`: `0a22321fc4244a8cbb4b80c7ff88543a`
3. `variant_2`: `926623465dd94241a9f2f4ba68811dad`
4. `variant_3`: `4d71151e5e0a499fbbb9e2b78b7676aa`
5. `variant_4`: `2faed839bb5d4de4ad6887c795b30733`
6. `variant_5`: `9ad760cf710c4b83972b04fbe2e39580`

Implementation preference remains:

1. `variant_3` is still the native implementation anchor
2. `variant_5` is now the clearest execution checklist fallback
3. `variant_2` remains useful as an operator-only density reference, not as the default direction
