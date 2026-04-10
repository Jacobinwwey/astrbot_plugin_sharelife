const test = require("node:test")
const assert = require("node:assert/strict")

const {
  buildInstallOptions,
  buildUploadOptions,
  buildSubmitOptions,
  buildProfilePackSubmitOptions,
  buildSubmitPayload,
  buildSubmissionDecisionPayload,
  buildSubmissionFilterQuery,
  buildCatalogFilterQuery,
  buildCatalogCompareQuery,
  pickProfilePackSubmissionFields,
  pickProfilePackCatalogFields,
} = require("../../sharelife/webui/profile_pack_market.js")

test("buildInstallOptions includes normalized selected sections for install sync control", () => {
  const payload = buildInstallOptions({
    preflight: true,
    forceReinstall: true,
    sourcePreference: "generated",
    selectedSections: " memory_store, conversation_history, memory_store, knowledge_base ",
  })
  assert.deepEqual(payload, {
    preflight: true,
    force_reinstall: true,
    source_preference: "generated",
    selected_sections: ["memory_store", "conversation_history", "knowledge_base"],
  })
})

test("buildUploadOptions normalizes upload mode and visibility", () => {
  const payload = buildUploadOptions({
    scanMode: "UNKNOWN",
    visibility: "PRIVATE",
    replaceExisting: 1,
    idempotencyKey: "upload-1",
  })
  assert.deepEqual(payload, {
    scan_mode: "balanced",
    visibility: "private",
    replace_existing: true,
    idempotency_key: "upload-1",
  })
})

test("buildSubmitOptions normalizes sections, enums, and idempotency key", () => {
  const payload = buildSubmitOptions({
    packType: "Extension_Pack",
    selectedSections: " plugins,providers,plugins ",
    redactionMode: "not-valid",
    replaceExisting: true,
    idempotencyKey: "submit-2",
  })
  assert.deepEqual(payload, {
    pack_type: "extension_pack",
    selected_sections: ["plugins", "providers"],
    redaction_mode: "exclude_secrets",
    replace_existing: true,
    idempotency_key: "submit-2",
  })
})

test("buildProfilePackSubmitOptions supports member selection payload including selected_item_paths and source", () => {
  const payload = buildProfilePackSubmitOptions(
    {
      packType: "bot_profile_pack",
      selectedSections: ["personas", "personas", "environment_manifest"],
      selectedItemPaths: [
        "personas.entries.alpha",
        "personas.entries.alpha",
        "environment_manifest.subagent_orchestrator.agents[0]",
      ],
      redactionMode: "exclude_provider",
      replaceExisting: 1,
      source: "member_import",
      idempotencyKey: "member-submit-ignored",
    },
    {
      includeSelectedItemPaths: true,
      includeSource: true,
      includeIdempotencyKey: false,
    },
  )
  assert.deepEqual(payload, {
    pack_type: "bot_profile_pack",
    selected_sections: ["personas", "environment_manifest"],
    redaction_mode: "exclude_provider",
    replace_existing: true,
    selected_item_paths: [
      "personas.entries.alpha",
      "environment_manifest.subagent_orchestrator.agents[0]",
    ],
    source: "member_import",
  })
})

test("buildSubmitPayload falls back to export artifact id", () => {
  const payload = buildSubmitPayload({
    userId: "member-1",
    artifactId: "",
    fallbackArtifactId: "exp-1",
  })
  assert.deepEqual(payload, {
    user_id: "member-1",
    artifact_id: "exp-1",
  })
})

test("buildSubmitPayload includes normalized submit options when present", () => {
  const payload = buildSubmitPayload({
    userId: "member-1",
    artifactId: "exp-2",
    submitOptions: {
      pack_type: "extension_pack",
      selected_sections: ["plugins", "providers"],
      redaction_mode: "include_provider_no_key",
      replace_existing: true,
    },
  })
  assert.deepEqual(payload, {
    user_id: "member-1",
    artifact_id: "exp-2",
    submit_options: {
      pack_type: "extension_pack",
      selected_sections: ["plugins", "providers"],
      redaction_mode: "include_provider_no_key",
      replace_existing: true,
    },
  })
})

test("buildSubmissionDecisionPayload normalizes decision and labels", () => {
  const payload = buildSubmissionDecisionPayload({
    submissionId: "sub-1",
    decision: "APPROVE",
    reviewNote: "Approved with notice.",
    reviewLabels: " risk_medium , approved_with_notice , ",
  })
  assert.deepEqual(payload, {
    submission_id: "sub-1",
    decision: "approve",
    review_note: "Approved with notice.",
    review_labels: ["risk_medium", "approved_with_notice"],
  })
})

test("buildSubmissionFilterQuery maps profile-pack submission filters", () => {
  const query = buildSubmissionFilterQuery({
    status: "pending",
    packQuery: "community",
    packType: "extension_pack",
    riskLevel: "high",
    reviewLabel: "prompt_injection_detected",
    warningFlag: "reveal_system_prompt",
  })
  assert.deepEqual(query, {
    status: "pending",
    pack_id: "community",
    pack_type: "extension_pack",
    risk_level: "high",
    review_label: "prompt_injection_detected",
    warning_flag: "reveal_system_prompt",
  })
})

test("buildCatalogFilterQuery maps profile-pack catalog filters", () => {
  const query = buildCatalogFilterQuery({
    packQuery: "safe",
    packType: "bot_profile_pack",
    riskLevel: "low",
    featured: "true",
    reviewLabel: "approved",
    warningFlag: "",
  })
  assert.deepEqual(query, {
    pack_id: "safe",
    pack_type: "bot_profile_pack",
    risk_level: "low",
    featured: "true",
    review_label: "approved",
  })
})

test("buildCatalogCompareQuery maps compare query with normalized sections", () => {
  const query = buildCatalogCompareQuery({
    packId: "profile/community-safe",
    selectedSections: " plugins, providers, plugins ",
  })
  assert.deepEqual(query, {
    pack_id: "profile/community-safe",
    selected_sections: "plugins,providers",
  })
})

test("pickProfilePackSubmissionFields extracts row values for quick fill", () => {
  const fields = pickProfilePackSubmissionFields({
    submission_id: "sub-9",
    pack_id: "profile/community-basic",
  })
  assert.deepEqual(fields, {
    profilePackDecisionSubmissionId: "sub-9",
    profilePackCatalogPackId: "profile/community-basic",
  })
})

test("pickProfilePackCatalogFields extracts row values for detail query", () => {
  const fields = pickProfilePackCatalogFields({
    pack_id: "profile/community-safe",
    source_submission_id: "sub-10",
  })
  assert.deepEqual(fields, {
    profilePackCatalogPackId: "profile/community-safe",
    profilePackDecisionSubmissionId: "sub-10",
    profilePackFeaturedPackId: "profile/community-safe",
  })
})
