(function bootstrapMarketStatusView(globalScope) {
  function text(value, fallback = "") {
    if (value === undefined || value === null) return fallback
    const output = String(value).trim()
    return output || fallback
  }

  function formatMessage(template, tokens = {}) {
    return String(template || "").replace(/\{([a-zA-Z0-9_]+)\}/g, (match, token) => {
      if (!Object.prototype.hasOwnProperty.call(tokens, token)) return match
      return String(tokens[token] ?? "")
    })
  }

  function safeI18nMessage(options, key, fallback) {
    if (options && typeof options.i18nMessage === "function") {
      return options.i18nMessage(key, fallback)
    }
    return String(fallback || "")
  }

  function safeI18nFormat(options, key, fallback, tokens = {}) {
    if (options && typeof options.i18nFormat === "function") {
      return options.i18nFormat(key, fallback, tokens)
    }
    return formatMessage(fallback, tokens)
  }

  function safeEnumLabel(options, group, value) {
    if (options && typeof options.enumLabel === "function") {
      return options.enumLabel(group, value)
    }
    return String(value || "")
  }

  function safePackLabel(options, packId) {
    if (options && typeof options.localizedPackLabel === "function") {
      return options.localizedPackLabel(packId)
    }
    return String(packId || "")
  }

  function buildSummaryText(data, options = {}) {
    if (!data || typeof data !== "object") {
      return safeI18nMessage(options, "market.summary.idle", "No operation yet.")
    }
    const status = text(data.status, "updated")
    const parts = [
      safeI18nFormat(options, "market.summary.part.status", "status={value}", {
        value: safeEnumLabel(options, "status", status),
      }),
    ]
    if (data.pack_id) {
      parts.push(safeI18nFormat(options, "market.summary.part.pack", "pack={value}", {
        value: safePackLabel(options, data.pack_id),
      }))
    }
    if (data.template_id) {
      parts.push(safeI18nFormat(options, "market.summary.part.template", "template={value}", {
        value: text(data.template_id),
      }))
    }
    if (data.submission_id) {
      parts.push(safeI18nFormat(options, "market.summary.part.submission", "submission={value}", {
        value: text(data.submission_id),
      }))
    }
    if (data.version) {
      parts.push(safeI18nFormat(options, "market.summary.part.version", "version={value}", {
        value: text(data.version),
      }))
    }
    if (typeof data.featured === "boolean") {
      parts.push(safeI18nFormat(options, "market.summary.part.featured", "featured={value}", {
        value: data.featured
          ? safeI18nMessage(options, "option.featured_toggle.true", "featured")
          : safeI18nMessage(options, "option.featured_toggle.false", "normal"),
      }))
    }
    if (data.risk_level) {
      parts.push(safeI18nFormat(options, "market.summary.part.risk", "risk={value}", {
        value: safeEnumLabel(options, "risk", data.risk_level),
      }))
    }
    if (Number.isFinite(Number(data.changed_sections_count))) {
      parts.push(safeI18nFormat(options, "market.summary.part.changed", "changed={value}", {
        value: Number(data.changed_sections_count),
      }))
    }
    return parts.join(" | ")
  }

  function safeLocalizedList(options, group, values) {
    if (options && typeof options.localizedList === "function") {
      return options.localizedList(group, values)
    }
    if (!Array.isArray(values) || values.length === 0) return "-"
    return values.map((entry) => String(entry || "").trim()).filter(Boolean).join(", ") || "-"
  }

  function safeFeaturedNote(options, data) {
    if (options && typeof options.localizedPackFeaturedNote === "function") {
      return options.localizedPackFeaturedNote(data.pack_id, text(data.featured_note, "-"))
    }
    return text(data.featured_note, "-")
  }

  function summarizeExecutionGroups(executionSummary, options = {}) {
    if (!executionSummary || typeof executionSummary !== "object" || !executionSummary.groups) return []
    const groups = executionSummary.groups || {}
    const labels = {
      policy_blocked: safeI18nMessage(options, "profile_pack.review.group.policy_blocked", "policy"),
      command_failed: safeI18nMessage(options, "profile_pack.review.group.command_failed", "failed"),
      timed_out: safeI18nMessage(options, "profile_pack.review.group.timed_out", "timeout"),
    }
    const ordered = ["policy_blocked", "command_failed", "timed_out"]
    const output = []
    ordered.forEach((key) => {
      const entries = Array.isArray(groups[key]) ? groups[key].map((item) => text(item)).filter(Boolean) : []
      if (!entries.length) return
      output.push(safeI18nFormat(options, "market.evidence.plugin_install_failure_group", "{group}: {items}", {
        group: labels[key],
        items: entries.join("|"),
      }))
    })
    return output
  }

  function buildEvidenceRows(data, options = {}) {
    if (!data || typeof data !== "object") return []
    const capabilitySummary = data.capability_summary || {}
    const reviewEvidence = data.review_evidence || {}
    const pluginInstall = data.plugin_install && typeof data.plugin_install === "object" ? data.plugin_install : {}
    const latestExecution = pluginInstall.latest_execution && typeof pluginInstall.latest_execution === "object"
      ? pluginInstall.latest_execution
      : null
    const summarizePluginInstallExecution = typeof options.summarizePluginInstallExecution === "function"
      ? options.summarizePluginInstallExecution
      : null
    const executionSummary = latestExecution && summarizePluginInstallExecution
      ? summarizePluginInstallExecution(latestExecution)
      : null
    const executionGroups = summarizeExecutionGroups(executionSummary, options)

    return [
      {
        label: safeI18nMessage(options, "market.evidence.featured_note", "featured note"),
        value: safeFeaturedNote(options, data),
      },
      {
        label: safeI18nMessage(options, "market.evidence.compatibility", "compatibility"),
        value: safeEnumLabel(options, "compatibility", text(data.compatibility, "unknown")),
      },
      {
        label: safeI18nMessage(options, "market.evidence.declared_capabilities", "declared capabilities"),
        value: Array.isArray(capabilitySummary.declared) ? capabilitySummary.declared.join(", ") || "-" : "-",
      },
      {
        label: safeI18nMessage(options, "market.evidence.review_labels", "review labels"),
        value: safeLocalizedList(options, "review_label", reviewEvidence.review_labels),
      },
      {
        label: safeI18nMessage(options, "market.evidence.plugin_install_status", "plugin install status"),
        value: safeEnumLabel(options, "plugin_install_status", text(pluginInstall.status, "unknown")),
      },
      {
        label: safeI18nMessage(options, "market.evidence.plugin_install_execution", "plugin install execution"),
        value: executionSummary
          ? safeI18nFormat(
            options,
            "market.evidence.plugin_install_execution_counts",
            "{status} (installed={installed}, failed={failed}, blocked={blocked})",
            {
              status: safeEnumLabel(options, "plugin_install_status", executionSummary.status),
              installed: Number(executionSummary.installed_count || 0),
              failed: Number(executionSummary.failed_count || 0),
              blocked: Number(executionSummary.blocked_count || 0),
            },
          )
          : "-",
      },
      {
        label: safeI18nMessage(options, "market.evidence.plugin_install_failure_groups", "plugin install failure groups"),
        value: executionGroups.length ? executionGroups.join(" ; ") : "-",
      },
    ]
  }

  function renderDetailCards(node, rows, options = {}) {
    if (!node) return
    const doc = options.document || node.ownerDocument || globalScope.document
    if (!doc || typeof doc.createElement !== "function") return
    node.innerHTML = ""
    const entries = Array.isArray(rows) ? rows : []
    entries.forEach((item) => {
      const card = doc.createElement("div")
      card.className = "detail-card"
      const label = doc.createElement("div")
      label.className = "detail-card-label"
      label.textContent = text(item && item.label, "-")
      card.appendChild(label)
      const value = doc.createElement("div")
      value.className = "detail-card-value"
      value.textContent = text(item && item.value, "-")
      card.appendChild(value)
      node.appendChild(card)
    })
  }

  const api = {
    buildSummaryText,
    buildEvidenceRows,
    renderDetailCards,
  }

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api
  }
  globalScope.SharelifeMarketStatusView = api
})(typeof globalThis !== "undefined" ? globalThis : this)
