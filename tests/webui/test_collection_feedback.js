const test = require("node:test")
const assert = require("node:assert/strict")

const {
  buildCollectionStateView,
  extractCollectionErrorMessage,
} = require("../../sharelife/webui/collection_feedback.js")
const {
  hasActiveCollectionFilters,
  resolveCollectionStatus,
} = require("../../sharelife/webui/collection_state.js")

test("buildCollectionStateView returns idle guidance before a list is loaded", () => {
  const view = buildCollectionStateView({
    status: "idle",
    resource: "Templates",
    idleMessage: "Load templates to browse published packages.",
  })

  assert.equal(view.visible, true)
  assert.equal(view.tone, "neutral")
  assert.match(view.title, /Templates idle/i)
  assert.match(view.message, /Load templates/i)
})

test("buildCollectionStateView returns loading and differentiated empty feedback", () => {
  const loadingView = buildCollectionStateView({
    status: "loading",
    resource: "Submissions",
  })
  assert.equal(loadingView.visible, true)
  assert.equal(loadingView.tone, "warning")
  assert.match(loadingView.message, /Loading submissions/i)

  const emptyUnfilteredView = buildCollectionStateView({
    status: "empty_unfiltered",
    resource: "Templates",
    emptyUnfilteredMessage: "No templates have been published yet.",
  })
  assert.equal(emptyUnfilteredView.visible, true)
  assert.equal(emptyUnfilteredView.tone, "neutral")
  assert.match(emptyUnfilteredView.message, /published yet/i)

  const emptyFilteredView = buildCollectionStateView({
    status: "empty_filtered",
    resource: "Templates",
    emptyFilteredMessage: "No templates matched the current filters.",
  })
  assert.equal(emptyFilteredView.visible, true)
  assert.equal(emptyFilteredView.tone, "neutral")
  assert.match(emptyFilteredView.message, /No templates matched/i)
})

test("buildCollectionStateView hides the banner when rows are ready", () => {
  const view = buildCollectionStateView({
    status: "ready",
    resource: "Templates",
    count: 3,
  })

  assert.equal(view.visible, false)
  assert.equal(view.tone, "success")
  assert.match(view.title, /Templates ready/i)
})

test("extractCollectionErrorMessage normalizes list failures", () => {
  assert.equal(
    extractCollectionErrorMessage(
      { status: 403, data: { error: { code: "permission_denied" } } },
      "Submissions",
    ),
    "Submissions failed: permission_denied",
  )
})

test("hasActiveCollectionFilters detects meaningful filter values", () => {
  assert.equal(
    hasActiveCollectionFilters({
      template_id: "",
      risk_level: "  ",
      warning_flag: null,
    }),
    false,
  )
  assert.equal(
    hasActiveCollectionFilters({
      template_id: "community/basic",
      risk_level: "",
    }),
    true,
  )
})

test("resolveCollectionStatus distinguishes filtered and unfiltered empties", () => {
  assert.equal(resolveCollectionStatus({ count: 0, hasActiveFilters: false }), "empty_unfiltered")
  assert.equal(resolveCollectionStatus({ count: 0, hasActiveFilters: true }), "empty_filtered")
  assert.equal(resolveCollectionStatus({ count: 2, hasActiveFilters: true }), "ready")
})
