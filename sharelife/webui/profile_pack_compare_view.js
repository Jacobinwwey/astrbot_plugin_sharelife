(function bootstrapProfilePackCompareView(globalScope) {
  function textValue(value, fallback = "-") {
    if (value === undefined || value === null || value === "") {
      return fallback
    }
    return String(value)
  }

  function listValue(values) {
    const rows = Array.isArray(values) ? values.filter(Boolean) : []
    if (!rows.length) return "-"
    return rows.join(", ")
  }

  function numberValue(value, fallback = 0) {
    const parsed = Number(value)
    if (!Number.isFinite(parsed)) return fallback
    return parsed
  }

  function buildI18n(options = {}) {
    const t = typeof options.t === "function"
      ? options.t
      : (_key, fallback = "") => String(fallback || "")
    const f = typeof options.f === "function"
      ? options.f
      : (key, fallback = "", tokens = {}) => {
        const template = t(key, fallback)
        return String(template).replace(/\{([a-zA-Z0-9_]+)\}/g, (match, token) => {
          if (!Object.prototype.hasOwnProperty.call(tokens, token)) return match
          return String(tokens[token] ?? "")
        })
      }
    const resolvePackLabel = typeof options.resolvePackLabel === "function"
      ? options.resolvePackLabel
      : (packId) => textValue(packId)
    return { t, f, resolvePackLabel }
  }

  function classifyPluginInstallAttempt(attempt) {
    const row = attempt && typeof attempt === "object" ? attempt : {}
    const status = textValue(row.status, "").toLowerCase()
    const reason = textValue(row.reason, "").toLowerCase()
    if (row.timed_out || reason === "timed_out") return "timed_out"
    if (status === "blocked" || reason.startsWith("install_command_") || reason.includes("http_not_allowed")) {
      return "policy_blocked"
    }
    if (status === "failed" || reason === "command_failed") return "command_failed"
    return "other"
  }

  function summarizePluginInstallExecution(execution) {
    const payload = execution && typeof execution === "object" ? execution : {}
    const result = payload.result && typeof payload.result === "object" ? payload.result : payload
    const attempts = Array.isArray(result.attempts) ? result.attempts : []
    const groups = {
      policy_blocked: [],
      command_failed: [],
      timed_out: [],
      other: [],
    }
    attempts.forEach((attempt) => {
      const pluginId = textValue(attempt && attempt.plugin_id, "unknown")
      const bucket = classifyPluginInstallAttempt(attempt)
      groups[bucket].push(pluginId)
    })
    return {
      status: textValue(payload.status || result.status, "unknown"),
      installed_count: numberValue(result.installed_count, 0),
      failed_count: numberValue(result.failed_count, 0),
      blocked_count: numberValue(result.blocked_count, 0),
      groups,
    }
  }

  function shortHash(value) {
    const text = textValue(value, "")
    if (!text || text.length <= 12) return text || "-"
    return `${text.slice(0, 12)}...`
  }

  function toneFromLabel(value) {
    const text = String(value || "").toLowerCase()
    if (!text) return "neutral"
    if (
      text.includes("high") ||
      text.includes("blocked") ||
      text.includes("prompt_injection") ||
      text.includes("confirmation_required")
    ) {
      return "danger"
    }
    if (text.includes("medium") || text.includes("degraded") || text.includes("warning")) {
      return "warning"
    }
    if (text.includes("compatible") || text.includes("confirmed")) {
      return "success"
    }
    return "neutral"
  }

  function fallbackCodeLabel(value) {
    const text = textValue(value, "")
    if (!text) return "-"
    return text
      .replace(/_/g, " ")
      .replace(/-/g, " ")
      .trim()
  }

  function i18nEnum(i18n, group, value) {
    const code = textValue(value, "")
    if (!code) return "-"
    if (String(group || "").toLowerCase() === "plugin") {
      return code
    }
    const key = `enum.${group}.${String(code).toLowerCase()}`
    return i18n.t(key, fallbackCodeLabel(code))
  }

  function i18nIssue(i18n, code) {
    const raw = String(code || "").trim()
    if (!raw) return "-"
    const normalized = raw.toLowerCase()
    if (normalized.startsWith("section_hash_mismatch:")) {
      const section = raw.split(":", 2)[1] || ""
      return i18n.f(
        "profile_pack.issue.section_hash_mismatch_with_section",
        "Section hash mismatch: {section}",
        { section: section || "-" },
      )
    }

    const issueKey = `profile_pack.issue.${normalized}`
    const issueLabel = i18n.t(issueKey, "")
    if (issueLabel) return issueLabel
    const normalizedBase = normalized.split(":", 1)[0]
    if (normalizedBase && normalizedBase !== normalized) {
      const baseKey = `profile_pack.issue.${normalizedBase}`
      const baseLabel = i18n.t(baseKey, "")
      if (baseLabel) return baseLabel
    }
    return i18nEnum(i18n, "review_label", normalizedBase || normalized)
  }

  function buildSectionRows(payload, options = {}) {
    const i18n = buildI18n(options)
    const rows = payload && payload.diff && Array.isArray(payload.diff.sections) ? payload.diff.sections : []
    return rows.map((item) => {
      const beforeSize = numberValue(item.before_size, 0)
      const afterSize = numberValue(item.after_size, 0)
      const changedPathsPreview = Array.isArray(item.changed_paths_preview)
        ? item.changed_paths_preview.map((entry) => String(entry || "").trim()).filter(Boolean)
        : []
      const changedPathsCount = numberValue(item.changed_paths_count, changedPathsPreview.length)
      const changedPathsTruncated = Boolean(item.changed_paths_truncated)
      const filePath = textValue(item.file_path, `sections/${textValue(item.section, "unknown")}.json`)
      const beforePreview = Array.isArray(item.before_preview)
        ? item.before_preview.map((line) => String(line ?? ""))
        : []
      const afterPreview = Array.isArray(item.after_preview)
        ? item.after_preview.map((line) => String(line ?? ""))
        : []
      const diffPreview = Array.isArray(item.diff_preview)
        ? item.diff_preview.map((line) => String(line ?? ""))
        : []
      return {
        section: textValue(item.section),
        file_path: filePath,
        changed: Boolean(item.changed),
        tone: item.changed ? "danger" : "neutral",
        before_hash: textValue(item.before_hash),
        after_hash: textValue(item.after_hash),
        before_hash_short: shortHash(item.before_hash),
        after_hash_short: shortHash(item.after_hash),
        before_size: beforeSize,
        after_size: afterSize,
        delta_size: afterSize - beforeSize,
        changed_paths_preview: changedPathsPreview,
        changed_paths_count: changedPathsCount,
        changed_paths_truncated: changedPathsTruncated,
        change_overview: buildSectionChangeSummary(
          {
            changed: Boolean(item.changed),
            file_path: filePath,
            changed_paths_preview: changedPathsPreview,
            changed_paths_count: changedPathsCount,
            changed_paths_truncated: changedPathsTruncated,
          },
          i18n,
        ),
        before_preview: beforePreview,
        after_preview: afterPreview,
        diff_preview: diffPreview,
        before_preview_truncated: Boolean(item.before_preview_truncated),
        after_preview_truncated: Boolean(item.after_preview_truncated),
        diff_preview_truncated: Boolean(item.diff_preview_truncated),
      }
    })
  }

  function buildSectionChangeSummary(row, i18n) {
    if (!row || !row.changed) {
      return i18n.t("market.compare.no_changes", "No change")
    }
    const preview = Array.isArray(row.changed_paths_preview) ? row.changed_paths_preview : []
    const count = numberValue(row.changed_paths_count, preview.length)
    if (!preview.length) {
      const filePath = String(row.file_path || "").trim()
      if (filePath) {
        return i18n.f(
          "market.compare.change_paths_fallback_with_file",
          "File updated: {file}",
          { file: filePath },
        )
      }
      return i18n.t("market.compare.change_paths_fallback", "Change detected")
    }
    const joined = preview.slice(0, 3).join(", ")
    if (row.changed_paths_truncated || count > preview.length) {
      const extra = Math.max(1, count - preview.length)
      return i18n.f(
        "market.compare.change_paths_summary_more",
        "{paths} (+{extra} more)",
        { paths: joined, extra: String(extra) },
      )
    }
    return i18n.f("market.compare.change_paths_summary_exact", "{paths}", { paths: joined })
  }

  function buildWarnings(payload, options = {}) {
    const i18n = buildI18n(options)
    const rows = []
    const compatibilityCode = textValue(payload && payload.compatibility, "unknown")
    const compatibility = i18nEnum(i18n, "compatibility", compatibilityCode)
    if (compatibilityCode !== "compatible") {
      const issues = Array.isArray(payload && payload.compatibility_issues)
        ? payload.compatibility_issues.map((item) => i18nIssue(i18n, item))
        : []
      rows.push({
        tone: toneFromLabel(compatibilityCode),
        message: i18n.f(
          "profile_pack.compare.warning.compatibility",
          "Compatibility: {compatibility}{issues}",
          {
            compatibility,
            issues: issues.length ? ` (${issues.join(", ")})` : "",
          },
        ),
      })
    }

    const pluginInstall = payload && typeof payload.plugin_install === "object" ? payload.plugin_install : null
    if (pluginInstall && pluginInstall.confirmation_required) {
      const missing = Array.isArray(pluginInstall.missing_plugins)
        ? pluginInstall.missing_plugins.map((item) => i18nEnum(i18n, "plugin", item))
        : []
      rows.push({
        tone: "warning",
        message: i18n.f(
          "profile_pack.compare.warning.plugin_confirm",
          "Plugin install confirmation required: {missing}",
          {
            missing: missing.length
              ? missing.join(", ")
              : i18n.t("profile_pack.compare.warning.plugin_confirm_pending", "pending admin confirmation"),
          },
        ),
      })
    }
    const latestExecution = pluginInstall && typeof pluginInstall.latest_execution === "object"
      ? pluginInstall.latest_execution
      : null
    if (latestExecution) {
      const executionSummary = summarizePluginInstallExecution(latestExecution)
      const executionStatus = i18nEnum(i18n, "plugin_install_status", executionSummary.status)
      rows.push({
        tone: toneFromLabel(executionSummary.status),
        message: i18n.f(
          "profile_pack.compare.warning.plugin_exec",
          "Plugin install execution: {status} (installed={installed}, failed={failed}, blocked={blocked})",
          {
            status: executionStatus,
            installed: executionSummary.installed_count,
            failed: executionSummary.failed_count,
            blocked: executionSummary.blocked_count,
          },
        ),
      })
      if (executionSummary.groups.policy_blocked.length) {
        rows.push({
          tone: "warning",
          message: i18n.f(
            "profile_pack.compare.warning.plugin_policy_blocks",
            "Plugin install policy blocks: {items}",
            { items: executionSummary.groups.policy_blocked.map((item) => i18nEnum(i18n, "plugin", item)).join(", ") },
          ),
        })
      }
      if (executionSummary.groups.command_failed.length) {
        rows.push({
          tone: "danger",
          message: i18n.f(
            "profile_pack.compare.warning.plugin_command_failures",
            "Plugin install command failures: {items}",
            { items: executionSummary.groups.command_failed.map((item) => i18nEnum(i18n, "plugin", item)).join(", ") },
          ),
        })
      }
      if (executionSummary.groups.timed_out.length) {
        rows.push({
          tone: "danger",
          message: i18n.f(
            "profile_pack.compare.warning.plugin_timeouts",
            "Plugin install timeouts: {items}",
            { items: executionSummary.groups.timed_out.map((item) => i18nEnum(i18n, "plugin", item)).join(", ") },
          ),
        })
      }
    }

    const scan = payload && typeof payload.scan_summary === "object" ? payload.scan_summary : {}
    const scanRiskCode = textValue(scan.risk_level, "")
    const scanRisk = i18nEnum(i18n, "risk", scanRiskCode)
    if (scanRiskCode === "high") {
      rows.push({
        tone: "danger",
        message: i18n.f(
          "profile_pack.compare.warning.scan_risk",
          "Scan risk level: {risk}",
          { risk: scanRisk },
        ),
      })
    }
    const warningFlags = Array.isArray(scan.warning_flags) ? scan.warning_flags : []
    if (warningFlags.length) {
      rows.push({
        tone: "warning",
        message: i18n.f(
          "profile_pack.compare.warning.scan_flags",
          "Warning flags: {flags}",
          { flags: warningFlags.map((item) => i18nEnum(i18n, "warning_flag", item)).join(", ") },
        ),
      })
    }
    const promptInjection = scan && typeof scan.prompt_injection === "object" ? scan.prompt_injection : {}
    if (promptInjection.detected) {
      rows.push({
        tone: "danger",
        message: i18n.f(
          "profile_pack.compare.warning.prompt_injection",
          "Prompt injection detected: {rules}",
          {
            rules: listValue(
              (Array.isArray(promptInjection.matched_rules) ? promptInjection.matched_rules : []).map((item) =>
                i18nEnum(i18n, "warning_flag", item)
              ),
            ),
          },
        ),
      })
    }
    return rows
  }

  function buildHighlights(payload, sectionRows, options = {}) {
    const i18n = buildI18n(options)
    const rows = []
    const changedSections = Array.isArray(payload && payload.changed_sections) ? payload.changed_sections : []
    changedSections.forEach((section) => {
      rows.push({
        label: i18n.f("profile_pack.compare.highlight.changed", "changed: {section}", { section }),
        tone: "danger",
      })
    })
    if (!changedSections.length && sectionRows.length) {
      rows.push({
        label: i18n.t("profile_pack.compare.highlight.no_change", "no section changed"),
        tone: "success",
      })
    }

    const compatibilityCode = textValue(payload && payload.compatibility, "unknown")
    const compatibility = i18nEnum(i18n, "compatibility", compatibilityCode)
    rows.push({
      label: i18n.f("profile_pack.compare.highlight.compatibility", "compatibility: {compatibility}", { compatibility }),
      tone: toneFromLabel(compatibilityCode),
    })

    const pluginInstall = payload && typeof payload.plugin_install === "object" ? payload.plugin_install : null
    if (pluginInstall) {
      rows.push({
        label: i18n.f("profile_pack.compare.highlight.plugin_install", "plugin install: {status}", {
          status: i18nEnum(i18n, "plugin_install_status", textValue(pluginInstall.status, "unknown")),
        }),
        tone: toneFromLabel(pluginInstall.status),
      })
      const latestExecution = pluginInstall && typeof pluginInstall.latest_execution === "object"
        ? pluginInstall.latest_execution
        : null
      if (latestExecution) {
        const summary = summarizePluginInstallExecution(latestExecution)
        rows.push({
          label: i18n.f("profile_pack.compare.highlight.plugin_exec", "plugin install execution: {status}", {
            status: i18nEnum(i18n, "plugin_install_status", summary.status),
          }),
          tone: toneFromLabel(summary.status),
        })
      }
    }
    return rows
  }

  function buildCards(payload, sectionRows, options = {}) {
    const i18n = buildI18n(options)
    const selectedSections = Array.isArray(payload && payload.selected_sections) ? payload.selected_sections : []
    const changedCount = numberValue(payload && payload.changed_sections_count, 0)
    const pluginInstall = payload && typeof payload.plugin_install === "object" ? payload.plugin_install : null
    const pluginStatusCode = pluginInstall ? textValue(pluginInstall.status, "unknown") : "not_applicable"
    const executionStatusCode = pluginInstall && pluginInstall.latest_execution
      ? textValue(pluginInstall.latest_execution.status, "unknown")
      : "not_available"
    return [
      {
        label: i18n.t("profile_pack.compare.card.pack", "Pack"),
        value: i18n.resolvePackLabel(textValue(payload && payload.pack_id, "")),
        tone: "neutral",
      },
      {
        label: i18n.t("profile_pack.compare.card.version", "Version"),
        value: textValue(payload && payload.version),
        tone: "neutral",
      },
      {
        label: i18n.t("profile_pack.compare.card.selected_sections", "Selected Sections"),
        value: `${selectedSections.length || sectionRows.length}`,
        tone: "neutral",
      },
      {
        label: i18n.t("profile_pack.compare.card.changed_sections", "Changed Sections"),
        value: `${changedCount}`,
        tone: changedCount > 0 ? "danger" : "success",
      },
      {
        label: i18n.t("profile_pack.compare.card.compatibility", "Compatibility"),
        value: i18nEnum(i18n, "compatibility", textValue(payload && payload.compatibility, "unknown")),
        tone: toneFromLabel(payload && payload.compatibility),
      },
      {
        label: i18n.t("profile_pack.compare.card.plugin_install", "Plugin Install"),
        value: i18nEnum(i18n, "plugin_install_status", pluginStatusCode),
        tone: toneFromLabel(pluginStatusCode),
      },
      {
        label: i18n.t("profile_pack.compare.card.plugin_install_exec", "Plugin Install Exec"),
        value: i18nEnum(i18n, "plugin_install_status", executionStatusCode),
        tone: toneFromLabel(executionStatusCode),
      },
    ]
  }

  function buildProfilePackCompareView(payload, options = {}) {
    const i18n = buildI18n(options)
    const data = payload && typeof payload === "object" ? payload : {}
    if (textValue(data.status, "") !== "compare_ready") {
      return {
        empty: true,
        message: i18n.t("profile_pack.compare.empty", "No compare payload loaded yet."),
        summary: i18n.t("profile_pack.compare.empty", "No compare payload loaded yet."),
        cards: [],
        highlights: [],
        warnings: [],
        sections: [],
        raw: data,
      }
    }

    const sectionRows = buildSectionRows(data, options)
    const changedCount = numberValue(data.changed_sections_count, sectionRows.filter((item) => item.changed).length)
    const selectedCount = Array.isArray(data.selected_sections) ? data.selected_sections.length : sectionRows.length
    return {
      empty: false,
      message: "",
      summary: i18n.f(
        "profile_pack.compare.summary",
        "Pack {pack_id} compare ready: {changed}/{selected} sections changed.",
        {
          pack_id: i18n.resolvePackLabel(textValue(data.pack_id, "")),
          changed: String(changedCount),
          selected: String(selectedCount),
        },
      ),
      cards: buildCards(data, sectionRows, options),
      highlights: buildHighlights(data, sectionRows, options),
      warnings: buildWarnings(data, options),
      sections: sectionRows,
      raw: data,
    }
  }

  const api = {
    buildProfilePackCompareView,
    summarizePluginInstallExecution,
    toneFromLabel,
  }
  if (typeof module !== "undefined" && module.exports) {
    module.exports = api
  }
  globalScope.SharelifeProfilePackCompareView = api
})(typeof globalThis !== "undefined" ? globalThis : this)
