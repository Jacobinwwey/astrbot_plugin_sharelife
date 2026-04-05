const test = require("node:test")
const assert = require("node:assert/strict")

const {
  buildWorkspaceHash,
  parseWorkspaceHash,
  buildWorkspaceSummary,
  buildSubmissionModerationViewModel,
} = require("../../sharelife/webui/workspace_state.js")

test("buildWorkspaceHash encodes template and submission routes", () => {
  assert.equal(
    buildWorkspaceHash({ scope: "template", id: "community/basic" }),
    "#scope=template&id=community%2Fbasic",
  )
  assert.equal(
    buildWorkspaceHash({ scope: "submission", id: "sub-1" }),
    "#scope=submission&id=sub-1",
  )
})

test("parseWorkspaceHash round-trips supported routes and rejects invalid ones", () => {
  assert.deepEqual(parseWorkspaceHash("#scope=template&id=community%2Fbasic"), {
    scope: "template",
    id: "community/basic",
  })
  assert.deepEqual(parseWorkspaceHash("#scope=submission&id=sub-1"), {
    scope: "submission",
    id: "sub-1",
  })
  assert.deepEqual(parseWorkspaceHash("#scope=unknown&id=x"), { scope: "", id: "" })
  assert.deepEqual(parseWorkspaceHash(""), { scope: "", id: "" })
})

test("buildWorkspaceSummary describes the active deep-linked workspace", () => {
  const empty = buildWorkspaceSummary({ scope: "", id: "" })
  assert.equal(empty.empty, true)
  assert.match(empty.title, /No active workspace/i)

  const template = buildWorkspaceSummary({ scope: "template", id: "community/basic" })
  assert.equal(template.empty, false)
  assert.equal(template.title, "Template workspace")
  assert.match(template.description, /community\/basic/)
  assert.match(template.routeLabel, /scope=template/)
})

test("buildSubmissionModerationViewModel exposes warnings and hydrated fields", () => {
  const empty = buildSubmissionModerationViewModel({}, null)
  assert.equal(empty.empty, true)
  assert.equal(empty.canReview, false)

  const view = buildSubmissionModerationViewModel(
    {
      submission_id: "sub-9",
      template_id: "community/basic",
      version: "1.2.0",
      status: "pending",
      risk_level: "high",
      review_labels: ["risk_high", "manual_reviewed"],
      review_note: "Escalate for final approval.",
      warning_flags: ["ignore_previous_instructions"],
      package_artifact: { filename: "community-basic-1_2.zip" },
    },
    {
      comparison: {
        status: "baseline_available",
      },
      details: {
        warning_flags: {
          submission: ["ignore_previous_instructions", "reveal_system_prompt"],
        },
      },
    },
  )

  assert.equal(view.empty, false)
  assert.equal(view.title, "sub-9")
  assert.equal(view.summary, "community/basic@1.2.0")
  assert.equal(view.compareStatus, "baseline_available")
  assert.deepEqual(
    view.highlights.map((item) => item.label),
    ["pending", "high", "compare:baseline_available"],
  )
  assert.match(view.warnings[0], /High-risk submission/i)
  assert.match(view.warnings[1], /ignore_previous_instructions/)
  assert.equal(view.reviewLabels, "risk_high, manual_reviewed")
  assert.equal(view.reviewNote, "Escalate for final approval.")
  assert.equal(view.canReview, true)
  assert.equal(view.canDownload, true)
})
