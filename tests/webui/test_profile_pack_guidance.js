const test = require("node:test")
const assert = require("node:assert/strict")

const {
  describeSection,
  issueBaseCode,
  resolveActionTarget,
  resolveActionPrefill,
  resolveIssueActionCode,
  buildCompatibilityIssueView,
  formatIssueLabel,
  formatIssueLabels,
} = require("../../sharelife/webui/profile_pack_guidance.js")

test("describeSection exposes metadata for known and unknown sections", () => {
  const memory = describeSection("memory_store")
  assert.equal(memory.known, true)
  assert.equal(memory.stateful, true)
  assert.equal(memory.localData, true)
  assert.equal(memory.titleKey, "profile_pack.section.memory_store.title")

  const unknown = describeSection("custom_unknown_section")
  assert.equal(unknown.known, false)
  assert.equal(unknown.stateful, false)
  assert.equal(unknown.localData, false)
  assert.equal(unknown.titleKey, "")
})

test("issueBaseCode normalizes prefixed section hash mismatch issues", () => {
  assert.equal(issueBaseCode("section_hash_mismatch:knowledge_base"), "section_hash_mismatch")
  assert.equal(issueBaseCode("signature_invalid"), "signature_invalid")
})

test("buildCompatibilityIssueView maps severity and action checklist", () => {
  const view = buildCompatibilityIssueView({
    compatibility: "degraded",
    compatibility_issues: [
      "environment_container_reconfigure_required",
      "knowledge_base_storage_sync_required",
      "section_hash_mismatch:knowledge_base",
      "environment_container_reconfigure_required",
      "custom_unknown_issue",
    ],
  })

  assert.equal(view.blocked, false)
  assert.equal(view.degraded, true)
  assert.equal(view.issues.length, 4)
  assert.equal(
    view.issues.find((item) => item.code === "section_hash_mismatch:knowledge_base").baseCode,
    "section_hash_mismatch",
  )
  assert.equal(
    view.issues.find((item) => item.code === "custom_unknown_issue").issueKey,
    "profile_pack.issue.unknown",
  )
  assert.ok(view.actionCodes.includes("reconfigure_container"))
  assert.ok(view.actionCodes.includes("sync_knowledge_base_storage"))
  assert.ok(view.actionCodes.includes("tell_ai_reconfigure_environment"))
})

test("buildCompatibilityIssueView upgrades unknown blocked issues to danger", () => {
  const view = buildCompatibilityIssueView({
    compatibility: "blocked",
    compatibility_issues: ["some_new_issue_code"],
  })
  assert.equal(view.blocked, true)
  assert.equal(view.issues[0].severity, "danger")
})

test("resolveActionTarget returns navigation metadata for known actions", () => {
  const plugin = resolveActionTarget("reconfigure_plugin_binary")
  assert.equal(plugin.targetId, "profilePackPluginInstallAdvanced")
  assert.equal(plugin.focusId, "btnProfilePackPluginExecute")
  assert.equal(plugin.developerModeRequired, false)

  const developerOnly = resolveActionTarget("tell_ai_reconfigure_environment")
  assert.equal(developerOnly.targetId, "profilePackCompatibilityDeveloper")
  assert.equal(developerOnly.developerModeRequired, true)

  assert.equal(resolveActionTarget("unknown_action_code"), null)
})

test("resolveActionPrefill returns section/plugin suggestions for known actions", () => {
  const plugin = resolveActionPrefill("reconfigure_plugin_binary")
  assert.equal(plugin.prefillPluginIds, true)
  assert.deepEqual(plugin.ensureSections, [])

  const knowledge = resolveActionPrefill("sync_knowledge_base_storage")
  assert.equal(knowledge.prefillPluginIds, false)
  assert.deepEqual(knowledge.ensureSections, ["knowledge_base"])

  const developerOnly = resolveActionPrefill("tell_ai_reconfigure_environment")
  assert.equal(developerOnly.prefillPluginIds, true)
  assert.deepEqual(developerOnly.ensureSections, ["environment_manifest"])

  assert.equal(resolveActionPrefill("unknown_action_code"), null)
})

test("resolveIssueActionCode maps issue code to shortcut action", () => {
  assert.equal(
    resolveIssueActionCode("environment_plugin_binary_reconfigure_required"),
    "reconfigure_plugin_binary",
  )
  assert.equal(
    resolveIssueActionCode("section_hash_mismatch:knowledge_base"),
    "sync_knowledge_base_storage",
  )
  assert.equal(resolveIssueActionCode("signature_invalid"), "")
})

test("formatIssueLabel localizes known issues and preserves section context", () => {
  const messages = {
    "profile_pack.issue.astrbot_raw_import_converted": "Converted from raw AstrBot",
    "profile_pack.issue.section_hash_mismatch_with_section": "Section mismatch: {section}",
  }
  const t = (key, fallback = "") => (Object.hasOwn(messages, key) ? messages[key] : fallback)
  const f = (key, fallback = "", tokens = {}) =>
    String(t(key, fallback)).replace(/\{([a-zA-Z0-9_]+)\}/g, (_match, token) => String(tokens[token] ?? ""))

  assert.equal(
    formatIssueLabel("astrbot_raw_import_converted", { t, f }),
    "Converted from raw AstrBot",
  )
  assert.equal(
    formatIssueLabel("section_hash_mismatch:knowledge_base", { t, f }),
    "Section mismatch: knowledge_base",
  )
  assert.equal(formatIssueLabel("unknown_new_issue", { t, f }), "unknown_new_issue")
})

test("formatIssueLabels deduplicates and formats issue lists", () => {
  const messages = {
    "profile_pack.issue.astrbot_raw_import_converted": "Converted from raw AstrBot",
  }
  const t = (key, fallback = "") => (Object.hasOwn(messages, key) ? messages[key] : fallback)

  assert.deepEqual(
    formatIssueLabels([
      "astrbot_raw_import_converted",
      "astrbot_raw_import_converted",
      "unknown_new_issue",
    ], { t }),
    ["Converted from raw AstrBot", "unknown_new_issue"],
  )
})
