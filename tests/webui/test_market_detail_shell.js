const test = require("node:test")
const assert = require("node:assert/strict")

const {
  DEFAULT_VARIANTS,
  resolveDetailPresentation,
  resolveDefaultSelectedPackId,
  buildMemberActionState,
  buildDetailShellState,
  buildDetailMemberActionStates,
  buildInstallSectionSelectionState,
  buildDetailPublicFactRows,
  buildDetailSummaryViewModel,
} = require("../../sharelife/webui/market_detail/detail_shell.js")

test("detail shell defaults to five variants and auth-gates member actions", () => {
  assert.deepEqual(DEFAULT_VARIANTS, ["variant_1", "variant_2", "variant_3", "variant_4", "variant_5"])
  assert.equal(resolveDetailPresentation({ viewportWidth: 1440 }), "drawer")
  assert.equal(resolveDetailPresentation({ viewportWidth: 390 }), "sheet")

  const installState = buildMemberActionState({ isAuthenticated: false, action: "install" })
  assert.equal(installState.requiresAuth, true)
  assert.equal(installState.visible, true)
  assert.equal(installState.action, "install")
})

test("detail shell state normalizes selection, variant, and presentation", () => {
  const shellState = buildDetailShellState({
    selectedPackId: "profile/native-sharelife-v3",
    activeVariant: "missing",
    availableVariants: ["variant_3", "variant_4"],
    viewportWidth: 428,
    normalizeVariantId(value, variants) {
      return variants.includes(value) ? value : variants[0]
    },
  })

  assert.equal(shellState.selectedPackId, "profile/native-sharelife-v3")
  assert.equal(shellState.hasSelection, true)
  assert.equal(shellState.presentation, "sheet")
  assert.equal(shellState.activeVariant, "variant_3")
  assert.deepEqual(shellState.availableVariants, ["variant_3", "variant_4"])
})

test("detail shell resolves default pack selection from featured rows only when no explicit pack is set", () => {
  assert.equal(
    resolveDefaultSelectedPackId({
      selectedPackId: "",
      rows: [
        { pack_id: "profile/standard", featured: false },
        { pack_id: "profile/native-sharelife-v3", featured: true },
      ],
    }),
    "profile/native-sharelife-v3",
  )

  assert.equal(
    resolveDefaultSelectedPackId({
      selectedPackId: "",
      rows: [
        { pack_id: "profile/standard", featured: false },
        { pack_id: "profile/fallback", featured: false },
      ],
    }),
    "profile/standard",
  )

  assert.equal(
    resolveDefaultSelectedPackId({
      selectedPackId: "profile/explicit",
      rows: [
        { pack_id: "profile/native-sharelife-v3", featured: true },
      ],
    }),
    "profile/explicit",
  )
})

test("detail shell member actions keep stable order and gate by selection plus capability", () => {
  const actionStates = buildDetailMemberActionStates({
    selectedPackId: "profile/native-sharelife-v3",
    isAuthenticated: false,
    capabilities: {
      "templates.trial.request": true,
      "templates.install": false,
    },
  })

  assert.deepEqual(
    actionStates.map((item) => item.id),
    ["trial", "install"],
  )

  const trial = actionStates.find((item) => item.id === "trial")
  const install = actionStates.find((item) => item.id === "install")

  assert.equal(trial.visible, true)
  assert.equal(trial.requiresAuth, true)
  assert.equal(trial.disabled, false)
  assert.equal(trial.controlId, "btnMarketDetailTrial")

  assert.equal(install.disabled, true)
  assert.equal(install.blockedReason, "capability")
})

test("detail shell install-section state normalizes available and persisted section sync choices", () => {
  const installState = buildInstallSectionSelectionState({
    availableSections: ["memory_store", "conversation_history", "memory_store", "knowledge_base"],
    savedSections: ["knowledge_base", "missing", "memory_store", "memory_store"],
    hasSavedSelection: true,
    describeSection(sectionName) {
      return {
        stateful: sectionName === "memory_store",
        localData: sectionName === "knowledge_base",
      }
    },
  })

  assert.deepEqual(
    installState.availableSections,
    ["memory_store", "conversation_history", "knowledge_base"],
  )
  assert.deepEqual(
    installState.selectedSections,
    ["knowledge_base", "memory_store"],
  )
  assert.equal(installState.statefulCount, 2)
  assert.equal(installState.summaryKey, "market.install.sections.summary_stateful")
  assert.deepEqual(installState.summaryValues, {
    selected: 2,
    total: 3,
    stateful: 2,
  })
})

test("detail shell public facts rows normalize labels and display values", () => {
  const rows = buildDetailPublicFactRows({
    title: "Native Sharelife V3",
    packId: "profile/native-sharelife-v3",
    version: "3.4.1",
    packType: "bot_profile_pack",
    compatibility: "compatible",
    riskLevel: "low",
    maintainer: "sharelife-core",
    reviewLabels: ["approved", "community_verified"],
    warningFlags: ["network_sync_required"],
  }, {
    message(_key, fallback) {
      return fallback
    },
    enumLabel(group, value) {
      return `${group}:${value}`
    },
    localizedList(_group, values) {
      return values.join(" | ")
    },
  })

  assert.deepEqual(rows, [
    { label: "Pack", value: "Native Sharelife V3" },
    { label: "Version", value: "3.4.1" },
    { label: "Pack Type", value: "pack_type:bot_profile_pack" },
    { label: "compatibility", value: "compatibility:compatible" },
    { label: "Risk", value: "risk:low" },
    { label: "Maintainer", value: "sharelife-core" },
    { label: "Labels", value: "approved | community_verified" },
    { label: "Flags", value: "network_sync_required" },
  ])
})

test("detail shell summary view model composes localized summary parts", () => {
  const view = buildDetailSummaryViewModel({
    status: "listed",
    pack_id: "profile/native-sharelife-v3",
    version: "3.4.1",
    featured: true,
    risk_level: "low",
    changed_sections_count: 3,
    message: "Ready for review.",
  }, {
    message(_key, fallback) {
      return fallback
    },
    format(_key, fallback, values) {
      return fallback.replace(/\{(\w+)\}/g, (_match, key) => String(values[key]))
    },
    enumLabel(group, value) {
      return `${group}:${value}`
    },
    resolvePackLabel(value) {
      return `Pack ${value}`
    },
  })

  assert.equal(view.empty, false)
  assert.equal(
    view.text,
    "status=status:listed | pack=Pack profile/native-sharelife-v3 | version=3.4.1 | featured=featured | risk=risk:low | changed=3 | Ready for review.",
  )
})
