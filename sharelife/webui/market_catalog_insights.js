(function bootstrapMarketCatalogInsights(globalScope) {
  function parseIsoDate(value) {
    const text = String(value || "").trim()
    if (!text) return 0
    const time = Date.parse(text)
    return Number.isFinite(time) ? time : 0
  }

  function listLength(value) {
    return Array.isArray(value) ? value.length : 0
  }

  function packRiskScore(risk) {
    const text = String(risk || "").trim().toLowerCase()
    if (text === "low") return 20
    if (text === "medium") return 12
    if (text === "high") return 4
    return 8
  }

  function packCompatibilityScore(item) {
    const text = String((item && item.compatibility) || "").trim().toLowerCase()
    if (text === "compatible" || text === "ok") return 14
    if (text === "degraded") return 8
    if (text === "blocked") return 0
    return 6
  }

  function catalogRankScore(item) {
    if (!item || typeof item !== "object") return 0
    const labels = listLength(item.review_labels)
    const warnings = listLength(item.warning_flags)
    const issues = listLength(item.compatibility_issues)
    const featured = item.featured ? 30 : 0
    const freshness = parseIsoDate(item.featured_at || item.published_at || "") > 0 ? 4 : 0
    const score = (
      featured
      + packRiskScore(item.risk_level)
      + packCompatibilityScore(item)
      + labels * 3
      + freshness
      - warnings * 4
      - issues * 2
    )
    return Math.max(0, Math.round(score))
  }

  function catalogMetrics(rows) {
    const items = Array.isArray(rows) ? rows : []
    let featured = 0
    let highRisk = 0
    let safe = 0
    let extension = 0
    let botProfile = 0
    items.forEach((item) => {
      const risk = String(item && item.risk_level || "").trim().toLowerCase()
      const packType = String(item && item.pack_type || "").trim().toLowerCase()
      if (item && item.featured) featured += 1
      if (risk === "high") highRisk += 1
      if (risk === "low") safe += 1
      if (packType === "extension_pack") extension += 1
      if (packType === "bot_profile_pack") botProfile += 1
    })
    return {
      total: items.length,
      featured,
      highRisk,
      safe,
      extension,
      botProfile,
    }
  }

  function catalogTrendScore(item) {
    if (!item || typeof item !== "object") return 0
    const explicit = Number(item.trend_score)
    if (Number.isFinite(explicit)) {
      return Math.max(0, Math.trunc(explicit))
    }
    return catalogRankScore(item)
  }

  function sortedByTrend(rows) {
    const items = Array.isArray(rows) ? rows.slice() : []
    return items.sort((left, right) => {
      const scoreDiff = catalogRankScore(right) - catalogRankScore(left)
      if (scoreDiff !== 0) return scoreDiff
      const leftTime = parseIsoDate(left && (left.featured_at || left.published_at))
      const rightTime = parseIsoDate(right && (right.featured_at || right.published_at))
      if (rightTime !== leftTime) return rightTime - leftTime
      return String(left && left.pack_id || "").localeCompare(String(right && right.pack_id || ""))
    })
  }

  const api = {
    parseIsoDate,
    listLength,
    packRiskScore,
    packCompatibilityScore,
    catalogRankScore,
    catalogMetrics,
    catalogTrendScore,
    sortedByTrend,
  }

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api
  }
  globalScope.SharelifeMarketCatalogInsights = api
})(typeof globalThis !== "undefined" ? globalThis : this)
