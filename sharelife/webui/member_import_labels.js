(function bootstrapMemberImportLabels(globalScope) {
  const RAW_ASTRBOT_IMPORT_CODE = "astrbot_raw_import_converted"

  function normalizeText(value) {
    return String(value || "").trim()
  }

  function dedupeStringList(values) {
    const rows = Array.isArray(values) ? values : [values]
    const out = []
    const seen = new Set()
    rows.forEach((item) => {
      const text = normalizeText(item)
      if (!text || seen.has(text)) return
      seen.add(text)
      out.push(text)
    })
    return out
  }

  function localizedIssueLabels(values, options = {}) {
    const formatter = options && typeof options.formatIssueLabels === "function"
      ? options.formatIssueLabels
      : null
    if (!formatter) return dedupeStringList(values)
    const formatted = formatter(values)
    return dedupeStringList(formatted)
  }

  function isRawAstrBotImportItem(item) {
    const issues = Array.isArray(item && item.compatibility_issues) ? item.compatibility_issues : []
    return issues.some(
      (entry) => normalizeText(entry).toLowerCase() === RAW_ASTRBOT_IMPORT_CODE,
    )
  }

  function buildIssueSummary(values, options = {}) {
    const labels = localizedIssueLabels(values, options)
    if (!labels.length) return ""
    const limit = Math.max(1, Number(options.limit || 2) || 2)
    const preview = labels.slice(0, limit).join(" · ")
    if (labels.length <= limit) return preview
    return `${preview} +${labels.length - limit}`
  }

  function importSourceLabel(item, options = {}) {
    const rawLabel = normalizeText(options.rawLabel) || "Raw AstrBot export (converted)"
    const standardLabel = normalizeText(options.standardLabel) || "Sharelife standard import"
    return isRawAstrBotImportItem(item) ? rawLabel : standardLabel
  }

  function buildImportSummaryText(item, options = {}) {
    const formatMessage = typeof options.formatMessage === "function"
      ? options.formatMessage
      : (_key, fallback = "", tokens = {}) => String(fallback || "").replace(
          /\{([a-zA-Z0-9_]+)\}/g,
          (match, token) => {
            if (!Object.prototype.hasOwnProperty.call(tokens, token)) return match
            return String(tokens[token] ?? "")
          },
        )
    const summary = item && typeof item.import_summary === "object" && item.import_summary
      ? item.import_summary
      : {}
    const parts = []
    const defaultPersonality = normalizeText(summary.default_personality)
    const personaCount = Number(summary.persona_count || 0)
    const subagentCount = Number(summary.subagent_count || 0)
    const platformCount = Number(summary.platform_count || 0)
    const fieldDiagnosticCount = Number(summary.field_diagnostic_count || 0)
    if (defaultPersonality) {
      parts.push(
        formatMessage(
          "member.imports.summary_default_personality",
          "Persona: {value}",
          { value: defaultPersonality },
        ),
      )
    }
    if (personaCount > 0) {
      parts.push(
        formatMessage(
          "member.imports.summary_persona_count",
          "Personas: {count}",
          { count: personaCount },
        ),
      )
    }
    if (subagentCount > 0) {
      parts.push(
        formatMessage(
          "member.imports.summary_subagent_count",
          "Subagents: {count}",
          { count: subagentCount },
        ),
      )
    }
    if (platformCount > 0) {
      parts.push(
        formatMessage(
          "member.imports.summary_platform_count",
          "Platforms: {count}",
          { count: platformCount },
        ),
      )
    }
    if (fieldDiagnosticCount > 0) {
      parts.push(
        formatMessage(
          "member.imports.summary_field_diagnostic_count",
          "Field diagnostics: {count}",
          { count: fieldDiagnosticCount },
        ),
      )
    }
    return parts.join(" · ")
  }

  const api = {
    RAW_ASTRBOT_IMPORT_CODE,
    dedupeStringList,
    localizedIssueLabels,
    isRawAstrBotImportItem,
    buildIssueSummary,
    importSourceLabel,
    buildImportSummaryText,
  }

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api
  }
  globalScope.SharelifeMemberImportLabels = api
})(typeof globalThis !== "undefined" ? globalThis : this)
