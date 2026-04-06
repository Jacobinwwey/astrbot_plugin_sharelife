(function bootstrapMarketCompareHelpers(globalScope) {
  function text(value, fallback = "") {
    if (value === undefined || value === null) return fallback
    const output = String(value).trim()
    return output || fallback
  }

  function i18nMessage(options, key, fallback) {
    if (options && typeof options.i18nMessage === "function") {
      return options.i18nMessage(key, fallback)
    }
    return String(fallback || "")
  }

  function i18nFormat(options, key, fallback, tokens = {}) {
    if (options && typeof options.i18nFormat === "function") {
      return options.i18nFormat(key, fallback, tokens)
    }
    return String(fallback || "").replace(/\{([a-zA-Z0-9_]+)\}/g, (match, token) => {
      if (!Object.prototype.hasOwnProperty.call(tokens, token)) return match
      return String(tokens[token] ?? "")
    })
  }

  function resolveCompareChangeSummary(row, options = {}) {
    const filePath = text(row && row.file_path)
    if (filePath) return filePath
    const section = text(row && row.section)
    if (section) return `sections/${section}.json`
    if (row && row.changed) {
      return i18nMessage(options, "market.compare.change_paths_fallback", "Change detected")
    }
    return i18nMessage(options, "market.compare.no_changes", "No change")
  }

  function formatCompareSize(row, options = {}) {
    const bytesLabel = i18nMessage(options, "market.compare.bytes", "bytes")
    const beforeSize = Number((row && row.before_size) || 0)
    const afterSize = Number((row && row.after_size) || 0)
    const delta = Number((row && row.delta_size) || 0)
    const deltaLabel = delta >= 0 ? `+${delta}` : `${delta}`
    return i18nFormat(
      options,
      "market.compare.size_compact",
      "{before} / {after} / {delta} {bytes}",
      {
        before: beforeSize,
        after: afterSize,
        delta: deltaLabel,
        bytes: bytesLabel,
      },
    )
  }

  function buildCompareDetailContent(row, options = {}) {
    const section = text(row && row.section)
    const filePath = text(row && row.file_path, "-")
    const diffRows = Array.isArray(row && row.diff_preview) ? row.diff_preview : []
    const beforeRows = Array.isArray(row && row.before_preview) ? row.before_preview : []
    const afterRows = Array.isArray(row && row.after_preview) ? row.after_preview : []
    const unresolvedFilePath = text(row && row.file_path, "-")
    let diffText = diffRows.join("\n")
    let beforeText = beforeRows.join("\n")
    let afterText = afterRows.join("\n")
    if (!diffText.trim()) {
      diffText = i18nFormat(
        options,
        "market.compare.detail.no_preview_diff",
        "No unified diff preview. File: {file}",
        { file: unresolvedFilePath },
      )
    }
    if (!beforeText.trim()) {
      beforeText = i18nFormat(
        options,
        "market.compare.detail.no_preview_before",
        "No before preview. hash={hash}",
        { hash: text((row && row.before_hash_short) || (row && row.before_hash), "-") },
      )
    }
    if (!afterText.trim()) {
      afterText = i18nFormat(
        options,
        "market.compare.detail.no_preview_after",
        "No after preview. hash={hash}",
        { hash: text((row && row.after_hash_short) || (row && row.after_hash), "-") },
      )
    }
    const truncatedText = i18nMessage(options, "market.compare.detail.truncated", "...truncated for preview")
    if (row && row.diff_preview_truncated) {
      diffText += `\n\n${truncatedText}`
    }
    if (row && row.before_preview_truncated) {
      beforeText += `\n\n${truncatedText}`
    }
    if (row && row.after_preview_truncated) {
      afterText += `\n\n${truncatedText}`
    }
    return {
      detailKey: section,
      metaText: i18nFormat(
        options,
        "market.compare.detail.meta",
        "Section: {section} | File: {file}",
        {
          section: section || "-",
          file: filePath,
        },
      ),
      diffText,
      beforeText,
      afterText,
    }
  }

  function emptyDetailMeta(options = {}) {
    return i18nMessage(
      options,
      "market.compare.detail.empty_meta",
      'Select one changed row and click "Expand Detail".',
    )
  }

  const api = {
    resolveCompareChangeSummary,
    formatCompareSize,
    buildCompareDetailContent,
    emptyDetailMeta,
  }

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api
  }
  globalScope.SharelifeMarketCompareHelpers = api
})(typeof globalThis !== "undefined" ? globalThis : this)
