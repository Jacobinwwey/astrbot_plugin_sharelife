const test = require("node:test")
const assert = require("node:assert/strict")

const {
  buildBadgeFilterPatch,
  buildTemplateSortQuery,
  buildTemplateSelection,
  buildSubmissionSelection,
} = require("../../sharelife/webui/table_interactions.js")

test("buildBadgeFilterPatch maps template badge clicks to template filters", () => {
  assert.deepEqual(
    buildBadgeFilterPatch("template", "tag", "strict-mode"),
    { templateTagFilter: "strict-mode" },
  )
  assert.deepEqual(
    buildBadgeFilterPatch("template", "source_channel", "bundled_official"),
    { templateSourceChannelFilter: "bundled_official" },
  )
  assert.deepEqual(
    buildBadgeFilterPatch("template", "risk_level", "high"),
    { templateRiskFilter: "high" },
  )
  assert.deepEqual(
    buildBadgeFilterPatch("template", "review_label", "prompt_injection_detected"),
    { templateReviewLabelFilter: "prompt_injection_detected" },
  )
  assert.deepEqual(
    buildBadgeFilterPatch("template", "warning_flag", "ignore_previous_instructions"),
    { templateWarningFlagFilter: "ignore_previous_instructions" },
  )
})

test("buildBadgeFilterPatch maps submission badge clicks to submission filters", () => {
  assert.deepEqual(
    buildBadgeFilterPatch("submission", "risk_level", "medium"),
    { submissionRiskFilter: "medium" },
  )
  assert.deepEqual(
    buildBadgeFilterPatch("submission", "review_label", "allow_with_notice"),
    { submissionReviewLabelFilter: "allow_with_notice" },
  )
  assert.deepEqual(
    buildBadgeFilterPatch("submission", "warning_flag", "reveal_system_prompt"),
    { submissionWarningFlagFilter: "reveal_system_prompt" },
  )
})

test("buildBadgeFilterPatch maps profile-pack market badge clicks to market filters", () => {
  assert.deepEqual(
    buildBadgeFilterPatch("profile_pack_submission", "risk_level", "high"),
    { profilePackSubmissionRiskFilter: "high" },
  )
  assert.deepEqual(
    buildBadgeFilterPatch("profile_pack_submission", "review_label", "risk_high"),
    { profilePackSubmissionReviewLabelFilter: "risk_high" },
  )
  assert.deepEqual(
    buildBadgeFilterPatch("profile_pack_catalog", "warning_flag", "reveal_system_prompt"),
    { profilePackCatalogWarningFlagFilter: "reveal_system_prompt" },
  )
})

test("buildBadgeFilterPatch ignores unsupported categories and blank values", () => {
  assert.deepEqual(buildBadgeFilterPatch("template", "source", "uploaded_submission"), {})
  assert.deepEqual(buildBadgeFilterPatch("submission", "risk_level", ""), {})
})

test("buildTemplateSortQuery normalizes supported sort controls", () => {
  assert.deepEqual(
    buildTemplateSortQuery("installs", ""),
    { sort_by: "installs", sort_order: "desc" },
  )
  assert.deepEqual(
    buildTemplateSortQuery("unexpected", "sideways"),
    { sort_by: "template_id", sort_order: "asc" },
  )
})

test("buildTemplateSelection syncs action fields and detail loading", () => {
  const selection = buildTemplateSelection({
    template_id: "community/basic",
    version: "1.0.0",
  })

  assert.equal(selection.selectedId, "community/basic")
  assert.deepEqual(selection.fieldPatches, {
    submitTemplateId: "community/basic",
    trialTemplateId: "community/basic",
  })
  assert.deepEqual(selection.requests, ["template_detail"])
})

test("buildSubmissionSelection syncs moderation fields and detail views", () => {
  const selection = buildSubmissionSelection({
    id: "sub-1",
    submission_id: "sub-1",
    template_id: "community/basic",
    review_labels: ["risk_high", "manual_reviewed"],
    review_note: "Escalate for admin confirmation.",
  })

  assert.equal(selection.selectedId, "sub-1")
  assert.deepEqual(selection.fieldPatches, {
    decisionSubmissionId: "sub-1",
    reviewLabels: "risk_high, manual_reviewed",
    reviewNote: "Escalate for admin confirmation.",
  })
  assert.deepEqual(selection.requests, ["submission_detail", "submission_compare"])
})
