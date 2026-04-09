(function bootstrapMarketCatalogContract(globalScope) {
  function text(value, fallback = "") {
    if (value === undefined || value === null) return fallback
    const normalized = String(value).trim()
    return normalized || fallback
  }

  function list(values) {
    return Array.isArray(values)
      ? values.map((item) => text(item)).filter(Boolean)
      : []
  }

  function buildBadges(item) {
    const badges = []
    if (item && item.featured) badges.push("featured")
    badges.push(...list(item && item.review_labels))
    badges.push(...list(item && item.warning_flags))
    return badges.slice(0, 6)
  }

  function buildSignals(item) {
    const sections = Array.isArray(item && item.sections) ? item.sections.length : 0
    const labels = Array.isArray(item && item.review_labels) ? item.review_labels.length : 0
    const flags = Array.isArray(item && item.warning_flags) ? item.warning_flags.length : 0
    return [
      { key: "compatibility", value: text(item && item.compatibility, "unknown") },
      { key: "sections", value: String(sections) },
      { key: "labels", value: String(labels) },
      { key: "flags", value: String(flags) },
    ]
  }

  function buildPublicCatalogCard(item, options = {}) {
    const likeCount = Number(options && options.likeCount)
    return {
      id: text(item && item.pack_id),
      title: text(item && (item.title || item.pack_id), "-"),
      subtitle: `${text(item && item.pack_type, "bot_profile_pack")} · v${text(item && item.version, "-")}`,
      maintainer: text(item && item.maintainer, "unknown"),
      compatibility: text(item && item.compatibility, "unknown"),
      risk: text(item && item.risk_level, "unknown"),
      badges: buildBadges(item),
      signals: buildSignals(item),
      summary: text(item && (item.summary || item.description), ""),
      memberActionsVisible: false,
      primaryAction: {
        kind: "open_detail",
        label: "Open",
      },
      likeCount: Number.isFinite(likeCount) ? Math.max(0, Math.trunc(likeCount)) : 0,
      liked: Boolean(options && options.liked),
      raw: item || {},
    }
  }

  function buildPublicCatalogSearchText(item, options = {}) {
    const localizedTerms = list(options && options.localizedTerms)
    const searchAliases = list(item && item.search_aliases)
    return [
      text(item && item.pack_id),
      text(item && item.title),
      text(item && item.maintainer),
      text(item && item.pack_type),
      text(item && item.version),
      text(item && item.compatibility),
      text(item && item.risk_level),
      text(item && item.summary),
      text(item && item.description),
      list(item && item.review_labels).join(" "),
      list(item && item.warning_flags).join(" "),
      list(item && item.sections).join(" "),
      searchAliases.join(" "),
      localizedTerms.join(" "),
    ]
      .filter(Boolean)
      .join(" ")
      .toLowerCase()
  }

  function buildDetailSeed(item) {
    return {
      packId: text(item && item.pack_id),
      title: text(item && (item.title || item.pack_id), "-"),
      version: text(item && item.version, ""),
      packType: text(item && item.pack_type, "bot_profile_pack"),
      compatibility: text(item && item.compatibility, "unknown"),
      riskLevel: text(item && item.risk_level, "unknown"),
      maintainer: text(item && item.maintainer, "unknown"),
      reviewLabels: list(item && item.review_labels),
      warningFlags: list(item && item.warning_flags),
      sections: list(item && item.sections),
      summary: text(item && (item.summary || item.description), ""),
      featured: Boolean(item && item.featured),
      packagePath: text(item && item.package_path),
      sourceSubmissionId: text(item && item.source_submission_id),
    }
  }

  const api = {
    buildPublicCatalogCard,
    buildPublicCatalogSearchText,
    buildDetailSeed,
  }

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api
  }
  globalScope.SharelifeMarketCatalogContract = api
})(typeof globalThis !== "undefined" ? globalThis : this)
