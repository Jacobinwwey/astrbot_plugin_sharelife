# Sharelife Template Engagement Signals Design

## Context

Sharelife now has a usable official catalog, community submission flow, risk labels, and metadata-aware browsing. What it still lacks is lightweight community signal data.

Today, templates can be listed and filtered, but the product cannot answer basic discovery questions:

1. Which templates are actually being tried or installed?
2. Which templates have recent activity?
3. Which entries have community submission momentum behind them?

That makes the market operational, but still weak as a community discovery surface.

## Goal

Add low-risk, aggregate engagement signals so the template market reads more like a real community catalog:

1. Record aggregate template activity counters.
2. Expose those counters in API list/detail payloads.
3. Support stable server-side sorting by activity and recency.
4. Surface the signals in WebUI without introducing a new subsystem.

## Scope

This slice covers:

1. Persistent aggregate engagement counters per `template_id`.
2. Event recording from existing API operations.
3. API list/detail exposure for engagement metrics.
4. List sorting by `recent_activity`, `trial_requests`, and `installs`.
5. WebUI list/detail rendering for those signals.
6. README and multilingual docs updates.

This slice does not cover:

1. Public comments or discussion threads.
2. User identity exposure inside engagement metrics.
3. Personalized ranking or recommendation models.
4. External analytics backends.
5. Cross-instance federation.

## Approaches Considered

### Approach A: Derive activity on demand from the audit log

Pros:

1. Avoids widening market state.
2. Reuses existing audit events.

Cons:

1. Sorting becomes more expensive and less deterministic.
2. Audit retention policy should not dictate product browse behavior.
3. Payload shaping becomes coupled to unrelated audit concerns.

### Approach B: Persist aggregate counters inside the market service

Pros:

1. Fits the existing market state boundary.
2. Makes sorting fast and deterministic.
3. Keeps only aggregate numbers, not user-level activity history.
4. Simple to expose in API and WebUI.

Cons:

1. Requires a small state migration/defaulting path.
2. Needs coordinated updates across API methods.

### Approach C: Add a separate analytics service and storage area

Pros:

1. Maximum conceptual isolation.

Cons:

1. Too heavy for the current product stage.
2. Duplicate persistence and serialization work.
3. Directly conflicts with the current modular simplicity goal.

## Decision

Use Approach B.

Engagement signals should live as aggregate template-level state in `MarketService`, because the product already treats published templates as the shared read model for both bundled official content and approved community content.

## Design

### Metrics Model

Each published template should expose an `engagement` object containing:

1. `trial_requests`
2. `installs`
3. `prompt_generations`
4. `package_generations`
5. `community_submissions`
6. `last_activity_at`

`community_submissions` should be derived from submission records for the same `template_id`, while the other counters should be recorded as aggregate events.

### Event Recording

Record counters only for existing user-visible actions:

1. Trial request processed
2. Template install processed
3. Prompt bundle generated
4. Package generated/exported

The counters stay aggregate. No per-user or per-session event history is added to the market state.

### API

`list_templates()` should accept a new `sort_by` parameter with these values:

1. `template_id` (default)
2. `recent_activity`
3. `trial_requests`
4. `installs`

A companion `sort_order` parameter should support `asc` and `desc`, defaulting to `desc` for activity-based sorts and `asc` for `template_id`.

List rows and detail payloads should both include the same `engagement` object.

### WebUI

The templates table should gain one compact `Signals` column, for example:

1. `trial 12`
2. `install 5`
3. `prompt 7`
4. `pkg 4`

The detail panel should show a dedicated engagement section with the exact counters and `last_activity_at` value.

The filter/control bar should also expose sort selection so the catalog can be switched between alphabetic browsing and activity-driven browsing.

### Persistence And Compatibility

Older market state should continue to load with zero/default engagement values.

If a template is not yet present in the published set, event recording should no-op instead of creating synthetic template entries.

## Risks

Main risks:

1. Event recording could overcount if the same action path is triggered multiple times.
2. Sorting defaults could unexpectedly change current list behavior.
3. WebUI could become visually noisy if signals are rendered too verbosely.

Mitigations:

1. Keep counters tied to explicit API calls only.
2. Preserve `template_id` ascending as the default list order.
3. Use one compact table column and a fuller detail view.

## Testing Strategy

Add tests for:

1. Market-service metric recording and state persistence.
2. API list/detail engagement payload exposure.
3. API sorting by recent activity and install count.
4. WebUI detail/table rendering of engagement data.

## Success Criteria

The slice is complete when:

1. Published templates persist aggregate engagement counters.
2. Existing trial/install/prompt/package actions update those counters.
3. API consumers can sort templates by activity or installs.
4. WebUI clearly shows activity signals without breaking current moderation flows.
