const test = require("node:test")
const assert = require("node:assert/strict")

const {
  buildPanelStateView,
  extractPanelErrorMessage,
} = require("../../sharelife/webui/workspace_feedback.js")

test("buildPanelStateView returns empty guidance for idle workspace panels", () => {
  const view = buildPanelStateView({
    status: "idle",
    resource: "Template detail",
    emptyMessage: "Select a template row to load detail.",
  })

  assert.equal(view.visible, true)
  assert.equal(view.tone, "neutral")
  assert.match(view.title, /Template detail/i)
  assert.match(view.message, /Select a template row/i)
})

test("buildPanelStateView returns loading feedback with selected id", () => {
  const view = buildPanelStateView({
    status: "loading",
    resource: "Submission compare",
    id: "sub-42",
  })

  assert.equal(view.visible, true)
  assert.equal(view.tone, "warning")
  assert.match(view.message, /sub-42/)
  assert.match(view.title, /Loading/i)
})

test("buildPanelStateView returns error feedback and hides banner when ready", () => {
  const errorView = buildPanelStateView({
    status: "error",
    resource: "Submission detail",
    errorMessage: "permission_denied",
  })
  assert.equal(errorView.visible, true)
  assert.equal(errorView.tone, "danger")
  assert.match(errorView.message, /permission_denied/)

  const readyView = buildPanelStateView({
    status: "ready",
    resource: "Submission detail",
  })
  assert.equal(readyView.visible, false)
  assert.equal(readyView.tone, "success")
})

test("extractPanelErrorMessage normalizes error payloads", () => {
  assert.equal(
    extractPanelErrorMessage(
      { status: 403, data: { error: { code: "permission_denied" } } },
      "Submission detail",
    ),
    "Submission detail failed: permission_denied",
  )

  assert.equal(
    extractPanelErrorMessage(
      { status: 500, data: { message: "invalid_json" } },
      "Template detail",
    ),
    "Template detail failed: invalid_json",
  )
})
