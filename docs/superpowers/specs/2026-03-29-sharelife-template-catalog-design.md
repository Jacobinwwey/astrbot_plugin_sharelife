# Sharelife Multi-Domain Official Template Catalog Design

## Context

Sharelife now ships a bundled official baseline through `templates/index.json`, but the current baseline is still too narrow for real browsing and discovery:

1. Only two templates are bundled.
2. The catalog has no explicit domain/category model.
3. API and WebUI cannot filter or explain templates by domain, tags, maintainer, or source channel.

That leaves the product technically usable, but weak as a discovery surface.

## Goal

Turn the bundled official baseline into a real starter catalog:

1. Multiple official templates across different usage domains.
2. Strong metadata for browsing and explanation.
3. Server-side filtering and direct WebUI visibility for that metadata.
4. No second market system and no breakage to community-submission flows.

## Scope

This slice covers:

1. Official template metadata schema.
2. Expanded bundled catalog in `templates/index.json`.
3. Startup seeding of that metadata into published official templates.
4. API support for metadata-aware list/detail responses and filters.
5. WebUI support for metadata-aware discovery and detail rendering.
6. Docs updates for the official catalog.

This slice does not cover:

1. Remote sync scheduling.
2. Community voting/ranking.
3. User favorites or personalization.
4. Template version history UI.

## Approaches Considered

### Approach A: Keep catalog data minimal and add only more templates

Pros:

1. Lowest code churn.
2. Fastest short-term expansion.

Cons:

1. Discovery remains weak.
2. WebUI still reads like a raw moderation table instead of a usable catalog.
3. Future metadata features become harder because asset shape stays underspecified.

### Approach B: Add a metadata-rich official catalog on top of the current market flow

Pros:

1. Best balance of product value and implementation cost.
2. Reuses seeded published-template path already in place.
3. Gives both API and WebUI clearer browsing semantics.
4. Keeps community-approved override behavior intact.

Cons:

1. Requires widening the template payload model.
2. Needs coordinated test, API, and WebUI changes.

### Approach C: Build a separate “official catalog” subsystem parallel to market

Pros:

1. Maximum isolation from community submission mechanics.

Cons:

1. Duplicate logic for list/detail/install/package.
2. Higher maintenance burden.
3. Directly conflicts with the current architecture direction.

## Decision

Use Approach B.

The bundled official catalog should remain a first-class input into the existing published-template model, not a separate subsystem. That preserves one install/package path while making discovery meaningfully better.

## Design

### Metadata Model

Official template entries gain:

1. `category`
2. `tags`
3. `maintainer`
4. `source_channel`

Published templates should persist and expose the same fields so seeded official templates and future community-approved templates share one read model.

### Catalog Content

The bundled catalog should expand from two templates to a small but varied starter set, for example:

1. `community/basic`
2. `community/research-safe`
3. `community/writing-polish`
4. `community/coding-review`
5. `community/ops-guarded`
6. `community/support-care`

Each entry should stay strict-mode aligned and low risk unless a stronger label is explicitly justified.

### API

`list_templates()` should support:

1. `category`
2. `tag`
3. `source_channel`

Template list rows and detail payloads should expose metadata fields directly so WebUI does not need asset-specific fallback logic.

### WebUI

Template browsing should show:

1. Category
2. Tags
3. Source channel
4. Maintainer

The filter panel should let users narrow the list by category and source channel, while tag clicks on rows/details should remain lightweight discovery affordances.

### Compatibility and Override Rule

Community-approved templates must still override bundled official templates when they share the same `template_id`.

Seed logic should therefore:

1. Seed official template when missing.
2. Refresh previously seeded official template metadata when the source remains official.
3. Skip seeding when a non-official published template already owns the same `template_id`.

## Errors and Risks

Main risks:

1. Schema widening could break existing payload serializers.
2. WebUI could regress if new fields are absent on older data.
3. Filters could silently exclude templates if normalization is inconsistent.

Mitigations:

1. Default empty metadata values in domain/application payloads.
2. Add targeted API and WebUI tests first.
3. Normalize filters to lowercase/trimmed values consistently.

## Testing Strategy

Add tests for:

1. Bundled catalog surface shape and multiple seeded domains.
2. API metadata filters and detail payload fields.
3. Main command output proving expanded market availability.
4. WebUI detail/list view models rendering metadata.

## Success Criteria

The slice is complete when:

1. A fresh plugin startup exposes a multi-domain official catalog.
2. API filters can narrow by category and source channel.
3. WebUI shows metadata clearly enough for discovery.
4. Existing install/package/community override behavior remains intact.
