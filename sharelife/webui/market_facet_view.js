(function bootstrapMarketFacetView(globalScope) {
  function text(value, fallback = "") {
    if (value === undefined || value === null) return fallback
    const output = String(value).trim()
    return output || fallback
  }

  function asGroups(groups) {
    return Array.isArray(groups) ? groups : []
  }

  function asMap(value) {
    return value instanceof Map ? value : new Map()
  }

  function asEntries(rows) {
    return Array.isArray(rows) ? rows : []
  }

  function defaultFacetLabel(group, value, options = {}) {
    const i18nMessage = typeof options.i18nMessage === "function"
      ? options.i18nMessage
      : (_key, fallback) => String(fallback || "")
    const enumLabel = typeof options.enumLabel === "function"
      ? options.enumLabel
      : (_group, enumValue) => String(enumValue || "")

    if (value === "unknown") {
      return i18nMessage("market.filter.value.unknown", "unknown")
    }
    if (group && group.key === "pack_type") {
      if (value === "bot_profile_pack") {
        return i18nMessage("option.pack_type.bot_profile_pack", "Bot Profile Pack (Full Bot Setup)")
      }
      if (value === "extension_pack") {
        return i18nMessage("option.pack_type.extension_pack", "Extension Pack (Skills/Personas/MCP/Plugins)")
      }
    }
    if (group && group.key === "risk_level") {
      if (value === "high") return i18nMessage("option.risk.high", "high")
      if (value === "medium") return i18nMessage("option.risk.medium", "medium")
      if (value === "low") return i18nMessage("option.risk.low", "low")
    }
    if (group && group.key === "featured") {
      if (value === "true") return i18nMessage("option.featured_status.true", "featured only")
      if (value === "false") return i18nMessage("option.featured_status.false", "non-featured only")
    }
    if (group && group.key === "compatibility") {
      return enumLabel("compatibility", value)
    }
    if (group && group.key === "review_label") {
      return enumLabel("review_label", value)
    }
    if (group && group.key === "warning_flag") {
      return enumLabel("warning_flag", value)
    }
    return value
  }

  function buildFacetRenderModel(options = {}) {
    const groups = asGroups(options.groups)
    const buckets = options && typeof options.buckets === "object" ? options.buckets : {}
    const facetSelection = options && typeof options.facetSelection === "object" ? options.facetSelection : {}
    const i18nMessage = typeof options.i18nMessage === "function"
      ? options.i18nMessage
      : (_key, fallback) => String(fallback || "")
    const completeFacetBucket = typeof options.completeFacetBucket === "function"
      ? options.completeFacetBucket
      : (_group, bucket) => asMap(bucket)
    const sortedFacetEntries = typeof options.sortedFacetEntries === "function"
      ? options.sortedFacetEntries
      : (_group, bucket) => Array.from(asMap(bucket).entries())
    const labelResolver = typeof options.labelResolver === "function"
      ? options.labelResolver
      : (group, value) => defaultFacetLabel(group, value, options)

    return groups.map((group) => {
      const groupKey = text(group && group.key)
      const normalizedBucket = completeFacetBucket(group, buckets[groupKey] || new Map())
      const entries = sortedFacetEntries(group, normalizedBucket).map(([value, count]) => {
        const normalizedValue = text(value)
        const selected = facetSelection[groupKey]
        return {
          value: normalizedValue,
          count: Number.isFinite(Number(count)) ? Number(count) : 0,
          checked: Boolean(selected instanceof Set && selected.has(normalizedValue)),
          label: labelResolver(group, normalizedValue),
        }
      })
      return {
        key: groupKey,
        title: i18nMessage(text(group && group.titleKey), text(group && group.titleFallback)),
        titleKey: text(group && group.titleKey),
        titleFallback: text(group && group.titleFallback),
        entries: asEntries(entries),
      }
    })
  }

  function renderFacetRenderModel(root, model, onToggle, options = {}) {
    if (!root) return
    const doc = options.document || root.ownerDocument || globalScope.document
    if (!doc || typeof doc.createElement !== "function") return
    const onFacetToggle = typeof onToggle === "function" ? onToggle : () => {}
    const groups = asEntries(model)
    const emptyText = text(options.emptyText, "No values")

    root.innerHTML = ""
    groups.forEach((group) => {
      const detail = doc.createElement("details")
      detail.className = "market-facet-group"
      detail.open = true

      const summary = doc.createElement("summary")
      summary.className = "market-facet-title"
      summary.textContent = text(group && group.title, text(group && group.titleFallback))
      detail.appendChild(summary)

      const list = doc.createElement("div")
      list.className = "market-facet-list"
      const entries = asEntries(group && group.entries)
      if (!entries.length) {
        const empty = doc.createElement("div")
        empty.className = "market-facet-empty"
        empty.textContent = emptyText
        list.appendChild(empty)
      } else {
        entries.forEach((entry) => {
          const row = doc.createElement("label")
          row.className = "market-facet-option"

          const checkbox = doc.createElement("input")
          checkbox.type = "checkbox"
          checkbox.checked = Boolean(entry && entry.checked)
          checkbox.setAttribute("data-market-facet-group", text(group && group.key))
          checkbox.setAttribute("data-market-facet-value", text(entry && entry.value))
          checkbox.addEventListener("change", () => {
            onFacetToggle(text(group && group.key), text(entry && entry.value), checkbox.checked)
          })
          row.appendChild(checkbox)

          const label = doc.createElement("span")
          label.className = "market-facet-option-label"
          label.textContent = text(entry && entry.label, text(entry && entry.value))
          row.appendChild(label)

          const badge = doc.createElement("span")
          badge.className = "market-facet-option-count"
          badge.textContent = String(Number.isFinite(Number(entry && entry.count)) ? Number(entry.count) : 0)
          row.appendChild(badge)

          list.appendChild(row)
        })
      }
      detail.appendChild(list)
      root.appendChild(detail)
    })
  }

  const api = {
    facetLabel: defaultFacetLabel,
    buildFacetRenderModel,
    renderFacetRenderModel,
  }

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api
  }
  globalScope.SharelifeMarketFacetView = api
})(typeof globalThis !== "undefined" ? globalThis : this)
