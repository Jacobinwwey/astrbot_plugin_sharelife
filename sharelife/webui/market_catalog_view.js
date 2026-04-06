(function bootstrapMarketCatalogView(globalScope) {
  function text(value, fallback = "") {
    if (value === undefined || value === null) return fallback
    const output = String(value).trim()
    return output || fallback
  }

  function toSafeInt(value, fallback = 0) {
    const parsed = Number(value)
    if (!Number.isFinite(parsed)) return Number(fallback || 0)
    return Math.max(0, Math.trunc(parsed))
  }

  function resolveUpdatedAt(item, locale = "en-US") {
    const raw = text(item && (item.featured_at || item.published_at))
    if (!raw) return "-"
    const time = Date.parse(raw)
    if (!Number.isFinite(time)) return raw
    try {
      return new Date(time).toLocaleDateString(locale || "en-US", {
        year: "numeric",
        month: "short",
        day: "numeric",
      })
    } catch (_error) {
      return new Date(time).toISOString().slice(0, 10)
    }
  }

  function engagementValue(item, key) {
    if (!item || typeof item !== "object") return 0
    const raw = Number(item.engagement && item.engagement[key] || 0)
    if (!Number.isFinite(raw)) return 0
    return Math.max(0, Math.trunc(raw))
  }

  function buildCardSignalRows(item, options = {}) {
    const t = typeof options.i18nMessage === "function"
      ? options.i18nMessage
      : (_key, fallback) => String(fallback || "")
    const enumLabel = typeof options.enumLabel === "function"
      ? options.enumLabel
      : (_group, value) => String(value || "")
    const sections = Array.isArray(item && item.sections) ? item.sections.length : 0
    const labels = Array.isArray(item && item.review_labels) ? item.review_labels.length : 0
    const flags = Array.isArray(item && item.warning_flags) ? item.warning_flags.length : 0
    return [
      {
        label: t("profile_pack.compare.card.compatibility", "Compatibility"),
        value: enumLabel("compatibility", text(item && item.compatibility, "unknown")),
      },
      {
        label: t("market.metric.sections", "Sections"),
        value: String(sections),
      },
      {
        label: t("table.header.labels", "Labels"),
        value: String(labels),
      },
      {
        label: t("table.header.flags", "Flags"),
        value: String(flags),
      },
    ]
  }

  function buildCardMetaEntries(item, options = {}) {
    const resolvedUpdated = typeof options.resolveUpdatedAt === "function"
      ? options.resolveUpdatedAt(item)
      : resolveUpdatedAt(item, String(options.locale || "en-US"))
    const installs = typeof options.engagementValue === "function"
      ? options.engagementValue(item, "installs")
      : engagementValue(item, "installs")
    const trials = typeof options.engagementValue === "function"
      ? options.engagementValue(item, "trial_requests")
      : engagementValue(item, "trial_requests")
    const score = typeof options.catalogRankScore === "function"
      ? options.catalogRankScore(item)
      : 0
    return [
      {
        key: "market.card.updated",
        fallback: "Updated {value}",
        value: String(resolvedUpdated),
      },
      {
        key: "market.card.downloads",
        fallback: "Installs {value}",
        value: String(installs),
      },
      {
        key: "market.card.trials",
        fallback: "Trials {value}",
        value: String(trials),
      },
      {
        key: "market.card.score",
        fallback: "Score {value}",
        value: String(score),
      },
    ]
  }

  function buildMetricCards(metric) {
    const safe = metric && typeof metric === "object" ? metric : {}
    const normalized = {
      total: toSafeInt(safe.total),
      featured: toSafeInt(safe.featured),
      highRisk: toSafeInt(safe.highRisk),
      safe: toSafeInt(safe.safe),
      extension: toSafeInt(safe.extension),
      botProfile: toSafeInt(safe.botProfile),
    }
    return [
      {
        key: "market.metric.total",
        fallback: "Total Packs",
        value: String(normalized.total),
        tone: "",
      },
      {
        key: "market.metric.featured",
        fallback: "Featured",
        value: String(normalized.featured),
        tone: "success",
      },
      {
        key: "market.metric.safe",
        fallback: "Low Risk",
        value: String(normalized.safe),
        tone: "success",
      },
      {
        key: "market.metric.high_risk",
        fallback: "High Risk",
        value: String(normalized.highRisk),
        tone: normalized.highRisk > 0 ? "danger" : "",
      },
      {
        key: "market.metric.extension",
        fallback: "Extension Pack",
        value: String(normalized.extension),
        tone: "",
      },
      {
        key: "market.metric.bot_profile",
        fallback: "Bot Profile Pack",
        value: String(normalized.botProfile),
        tone: "",
      },
    ]
  }

  function selectFeaturedCandidate(rows, featuredOverride, options = {}) {
    if (featuredOverride && typeof featuredOverride === "object") return featuredOverride
    const sortedByTrend = typeof options.sortedByTrend === "function"
      ? options.sortedByTrend
      : (input) => (Array.isArray(input) ? input : [])
    const sorted = sortedByTrend(rows)
    const featuredRows = sorted.filter((item) => Boolean(item && item.featured))
    return featuredRows[0] || sorted[0] || null
  }

  function selectTrendingRows(rows, trendingOverride, options = {}) {
    const limit = toSafeInt(options.limit, 6) || 6
    if (Array.isArray(trendingOverride) && trendingOverride.length) {
      return trendingOverride.slice(0, limit)
    }
    const sortedByTrend = typeof options.sortedByTrend === "function"
      ? options.sortedByTrend
      : (input) => (Array.isArray(input) ? input : [])
    return sortedByTrend(rows).slice(0, limit)
  }

  const api = {
    resolveUpdatedAt,
    engagementValue,
    buildCardSignalRows,
    buildCardMetaEntries,
    buildMetricCards,
    selectFeaturedCandidate,
    selectTrendingRows,
  }

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api
  }
  globalScope.SharelifeMarketCatalogView = api
})(typeof globalThis !== "undefined" ? globalThis : this)
