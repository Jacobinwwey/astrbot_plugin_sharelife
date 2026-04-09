const test = require("node:test")
const assert = require("node:assert/strict")

const {
  normalizeSectionList,
  buildExportPayload,
  buildDryrunPayload,
  buildSelectedSections,
  buildImportAndDryrunPayload,
  normalizeSelectionPaths,
  validateFieldPaths,
} = require("../../sharelife/webui/profile_pack_panel.js")

test("normalizeSectionList de-duplicates comma separated values", () => {
  assert.deepEqual(
    normalizeSectionList("plugins, providers,plugins, skills"),
    ["plugins", "providers", "skills"],
  )
})

test("buildExportPayload applies defaults and normalized sections", () => {
  const payload = buildExportPayload({
    packId: "profile/basic",
    version: "",
    redactionMode: "exclude_secrets",
    sections: "astrbot_core, providers",
    maskPaths: "providers.openai.organization",
    dropPaths: "sharelife_meta.owner",
  })

  assert.deepEqual(payload, {
    pack_id: "profile/basic",
    version: "1.0.0",
    pack_type: "bot_profile_pack",
    redaction_mode: "exclude_secrets",
    sections: ["astrbot_core", "providers"],
    mask_paths: ["providers.openai.organization"],
    drop_paths: ["sharelife_meta.owner"],
  })
})

test("buildSelectedSections resolves checked section names", () => {
  assert.deepEqual(
    buildSelectedSections([
      { name: "astrbot_core", checked: true },
      { name: "providers", checked: false },
      { name: "plugins", checked: true },
    ]),
    ["astrbot_core", "plugins"],
  )
})

test("buildDryrunPayload emits import id, plan id and selected sections", () => {
  const payload = buildDryrunPayload({
    importId: "imp-1",
    planId: "plan-profile-basic",
    sections: [
      { name: "plugins", checked: true },
      { name: "providers", checked: false },
    ],
  })

  assert.deepEqual(payload, {
    import_id: "imp-1",
    plan_id: "plan-profile-basic",
    selected_sections: ["plugins"],
  })
})

test("buildImportAndDryrunPayload prefers artifact source and selected sections", () => {
  const payload = buildImportAndDryrunPayload({
    artifactId: "artifact-123",
    filename: "ignored.zip",
    contentBase64: "ignored",
    planId: "profile-plan-quick",
    sections: [
      { name: "plugins", checked: true },
      { name: "providers", checked: false },
    ],
  })

  assert.equal(payload.artifact_id, "artifact-123")
  assert.equal(payload.plan_id, "profile-plan-quick")
  assert.equal(payload.filename, undefined)
  assert.equal(payload.content_base64, undefined)
  assert.deepEqual(payload.selected_sections, ["plugins"])
})

test("normalizeSelectionPaths de-duplicates nested section item paths", () => {
  assert.deepEqual(
    normalizeSelectionPaths([
      "personas.entries.analyst",
      "personas.entries.analyst",
      "environment_manifest.subagent_orchestrator.agents[0]",
      "",
    ]),
    [
      "personas.entries.analyst",
      "environment_manifest.subagent_orchestrator.agents[0]",
    ],
  )
})

test("validateFieldPaths checks section-prefixed dotted paths", () => {
  const valid = validateFieldPaths({
    mask_paths: ["providers.openai.organization", "sharelife_meta.notes", "knowledge_base.index_path"],
    drop_paths: ["providers.openai.endpoint", "memory_store.session_cache"],
  })
  assert.equal(valid.valid, true)
  assert.deepEqual(valid.errors, [])

  const invalid = validateFieldPaths({
    mask_paths: ["organization"],
    drop_paths: ["unknown_section.path"],
  })
  assert.equal(invalid.valid, false)
  assert.equal(invalid.errors.length, 2)
  assert.equal(invalid.errors[0].field, "mask_paths")
  assert.equal(invalid.errors[1].field, "drop_paths")
})
