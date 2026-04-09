(function bootstrapMarketDetailShell(globalScope) {
  const DEFAULT_VARIANTS = ["variant_1", "variant_2", "variant_3", "variant_4", "variant_5"]
  const DEFAULT_MEMBER_ACTIONS = Object.freeze([
    {
      id: "trial",
      action: "trial",
      controlId: "btnMarketDetailTrial",
      capability: "templates.trial.request",
    },
    {
      id: "install",
      action: "install",
      controlId: "btnMarketDetailInstall",
      capability: "templates.install",
    },
  ])

  function normalizeAvailableVariants(availableVariants) {
    const values = Array.isArray(availableVariants)
      ? availableVariants
        .map((item) => String(item || "").trim())
        .filter(Boolean)
      : []
    if (values.length) {
      return Array.from(new Set(values))
    }
    return DEFAULT_VARIANTS.slice()
  }

  function normalizeStringList(values) {
    const rows = Array.isArray(values) ? values : [values]
    const out = []
    const seen = new Set()
    rows.forEach((item) => {
      const value = String(item || "").trim()
      if (!value || seen.has(value)) return
      seen.add(value)
      out.push(value)
    })
    return out
  }

  function resolveDetailPresentation(options = {}) {
    const viewportWidth = Number(options.viewportWidth || 0)
    if (viewportWidth > 0 && viewportWidth <= 768) {
      return "sheet"
    }
    return "drawer"
  }

  function buildMemberActionState(options = {}) {
    const action = String(options.action || "").trim().toLowerCase()
    const isAuthenticated = Boolean(options.isAuthenticated)
    const hasCapability = options.hasCapability !== false
    return {
      action,
      visible: Boolean(action),
      requiresAuth: Boolean(action) && !isAuthenticated,
      disabled: !hasCapability,
    }
  }

  function hasActionCapability(capabilities, capability) {
    const key = String(capability || "").trim()
    if (!key) return true
    if (Array.isArray(capabilities)) {
      return capabilities.includes(key)
    }
    if (capabilities && typeof capabilities === "object") {
      return capabilities[key] !== false
    }
    return true
  }

  function buildDetailShellState(options = {}) {
    const selectedPackId = String(options.selectedPackId || "").trim()
    const availableVariants = normalizeAvailableVariants(options.availableVariants)
    const normalizeVariantId = typeof options.normalizeVariantId === "function"
      ? options.normalizeVariantId
      : null
    const requestedVariant = String(options.activeVariant || "").trim()
    let activeVariant = requestedVariant || availableVariants[0]

    if (normalizeVariantId) {
      activeVariant = String(normalizeVariantId(activeVariant, availableVariants.slice()) || "").trim()
    }

    if (!availableVariants.includes(activeVariant)) {
      activeVariant = availableVariants[0]
    }

    return {
      selectedPackId,
      hasSelection: Boolean(selectedPackId),
      presentation: resolveDetailPresentation(options),
      activeVariant,
      availableVariants,
    }
  }

  function resolveDefaultSelectedPackId(options = {}) {
    const explicitSelection = String(options.selectedPackId || "").trim()
    if (explicitSelection) {
      return explicitSelection
    }
    const rows = Array.isArray(options.rows)
      ? options.rows
        .map((item) => item && typeof item === "object" ? item : null)
        .filter(Boolean)
      : []
    const featuredRow = rows.find((item) => {
      const packId = String(item.pack_id || "").trim()
      return packId && Boolean(item.featured)
    })
    if (featuredRow) {
      return String(featuredRow.pack_id || "").trim()
    }
    const firstRow = rows.find((item) => String(item.pack_id || "").trim())
    return firstRow ? String(firstRow.pack_id || "").trim() : ""
  }

  function buildDetailMemberActionStates(options = {}) {
    const selectedPackId = String(options.selectedPackId || "").trim()
    const isSelected = Boolean(selectedPackId)
    return DEFAULT_MEMBER_ACTIONS.map((definition) => {
      const hasCapability = hasActionCapability(options.capabilities, definition.capability)
      const state = buildMemberActionState({
        action: definition.action,
        isAuthenticated: options.isAuthenticated,
        hasCapability,
      })
      let blockedReason = ""
      if (!isSelected) {
        blockedReason = "selection_required"
      } else if (!hasCapability) {
        blockedReason = "capability"
      }
      return {
        ...definition,
        ...state,
        visible: isSelected && state.visible,
        disabled: !isSelected || state.disabled,
        blockedReason,
      }
    })
  }

  function buildInstallSectionSelectionState(options = {}) {
    const availableSections = normalizeStringList(options.availableSections)
    const hasSavedSelection = options.hasSavedSelection === true
    const savedSections = normalizeStringList(options.savedSections)
    const selectedSections = hasSavedSelection
      ? savedSections.filter((section) => availableSections.includes(section))
      : availableSections.slice()
    const describeSection = typeof options.describeSection === "function"
      ? options.describeSection
      : null
    const statefulCount = availableSections.filter((sectionName) => {
      const meta = describeSection ? describeSection(sectionName) : null
      return Boolean(meta && (meta.stateful || meta.localData))
    }).length

    let summaryKey = "market.install.sections.summary"
    if (!availableSections.length) {
      summaryKey = "market.install.sections.empty"
    } else if (!selectedSections.length) {
      summaryKey = "market.install.sections.none_selected"
    } else if (statefulCount > 0) {
      summaryKey = "market.install.sections.summary_stateful"
    }

    return {
      availableSections,
      selectedSections,
      statefulCount,
      summaryKey,
      summaryValues: {
        selected: selectedSections.length,
        total: availableSections.length,
        stateful: statefulCount,
      },
    }
  }

  function buildDetailPublicFactRows(context = {}, options = {}) {
    const message = typeof options.message === "function"
      ? options.message
      : (_key, fallback) => fallback
    const enumLabel = typeof options.enumLabel === "function"
      ? options.enumLabel
      : (_group, value) => String(value || "-")
    const localizedList = typeof options.localizedList === "function"
      ? options.localizedList
      : (_group, values) => normalizeStringList(values).join(", ") || "-"
    return [
      { label: message("table.header.pack", "Pack"), value: String(context.title || context.packId || "-") || "-" },
      { label: message("table.header.version", "Version"), value: String(context.version || "-") || "-" },
      { label: message("table.header.pack_type", "Pack Type"), value: enumLabel("pack_type", context.packType) },
      { label: message("market.evidence.compatibility", "compatibility"), value: enumLabel("compatibility", context.compatibility) },
      { label: message("table.header.risk", "Risk"), value: enumLabel("risk", context.riskLevel) },
      { label: message("table.header.maintainer", "Maintainer"), value: String(context.maintainer || "-") || "-" },
      { label: message("table.header.labels", "Labels"), value: localizedList("review_label", context.reviewLabels) || "-" },
      { label: message("table.header.flags", "Flags"), value: localizedList("warning_flag", context.warningFlags) || "-" },
    ]
  }

  function buildDetailSummaryViewModel(data, options = {}) {
    const message = typeof options.message === "function"
      ? options.message
      : (_key, fallback) => fallback
    const format = typeof options.format === "function"
      ? options.format
      : (_key, fallback, values) => String(fallback || "").replace(/\{(\w+)\}/g, (_match, key) => String(values[key]))
    const enumLabel = typeof options.enumLabel === "function"
      ? options.enumLabel
      : (_group, value) => String(value || "-")
    const resolvePackLabel = typeof options.resolvePackLabel === "function"
      ? options.resolvePackLabel
      : (value) => String(value || "-")
    if (!data || typeof data !== "object") {
      return {
        empty: true,
        text: message("market.summary.idle", "No operation yet."),
      }
    }
    const status = String(data.status || "updated")
    const parts = [
      format("market.summary.part.status", "status={value}", {
        value: enumLabel("status", status),
      }),
    ]
    if (data.pack_id) {
      parts.push(format("market.summary.part.pack", "pack={value}", {
        value: resolvePackLabel(data.pack_id),
      }))
    }
    if (data.version) {
      parts.push(format("market.summary.part.version", "version={value}", {
        value: data.version,
      }))
    }
    if (typeof data.featured === "boolean") {
      parts.push(format("market.summary.part.featured", "featured={value}", {
        value: data.featured
          ? message("option.featured_toggle.true", "featured")
          : message("option.featured_toggle.false", "normal"),
      }))
    }
    if (data.risk_level) {
      parts.push(format("market.summary.part.risk", "risk={value}", {
        value: enumLabel("risk", data.risk_level),
      }))
    }
    if (Number.isFinite(Number(data.changed_sections_count))) {
      parts.push(format("market.summary.part.changed", "changed={value}", {
        value: Number(data.changed_sections_count),
      }))
    }
    if (data.message) {
      parts.push(String(data.message))
    }
    return {
      empty: false,
      text: parts.join(" | "),
    }
  }

  const api = {
    DEFAULT_VARIANTS,
    resolveDetailPresentation,
    resolveDefaultSelectedPackId,
    buildMemberActionState,
    buildDetailShellState,
    buildDetailMemberActionStates,
    buildInstallSectionSelectionState,
    buildDetailPublicFactRows,
    buildDetailSummaryViewModel,
  }

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api
  }
  globalScope.SharelifeMarketDetailShell = api
})(typeof globalThis !== "undefined" ? globalThis : this)
