(function bootstrapMarketCards(globalScope) {
  function text(value, fallback = "") {
    if (value === undefined || value === null) return fallback
    const output = String(value).trim()
    return output || fallback
  }

  function list(values) {
    return Array.isArray(values)
      ? values.map((item) => text(item)).filter(Boolean)
      : []
  }

  function number(value) {
    const parsed = Number(value)
    return Number.isFinite(parsed) ? parsed : 0
  }

  function compact(value) {
    const amount = number(value)
    if (amount >= 1000000) return `${(amount / 1000000).toFixed(1)}m`
    if (amount >= 1000) return `${(amount / 1000).toFixed(1)}k`
    return String(amount)
  }

  function riskTone(riskLevel) {
    const level = text(riskLevel).toLowerCase()
    if (level === "high") return "danger"
    if (level === "medium") return "warning"
    if (level === "low") return "success"
    return "neutral"
  }

  function badgeTone(label) {
    const value = text(label).toLowerCase()
    if (!value) return "neutral"
    if (
      value.includes("high") ||
      value.includes("prompt_injection") ||
      value.includes("reveal_system_prompt") ||
      value.includes("ignore_previous")
    ) {
      return "danger"
    }
    if (
      value.includes("warning") ||
      value.includes("medium") ||
      value.includes("degraded") ||
      value.includes("notice")
    ) {
      return "warning"
    }
    if (value.includes("featured") || value.includes("official") || value.includes("approved")) {
      return "success"
    }
    return "neutral"
  }

  function engagementSummary(item) {
    const data = item && typeof item === "object" && item.engagement ? item.engagement : {}
    return [
      { key: "trials", label: "Trials", value: compact(data.trial_requests) },
      { key: "installs", label: "Installs", value: compact(data.installs) },
      { key: "prompts", label: "Prompts", value: compact(data.prompt_generations) },
      { key: "packages", label: "Packages", value: compact(data.package_generations) },
    ]
  }

  function buildTemplateCardModel(item) {
    const templateId = text(item && item.template_id)
    const version = text(item && item.version, "-")
    const category = text(item && item.category, "general")
    const tags = list(item && item.tags)
    const reviewLabels = list(item && item.review_labels)
    const warningFlags = list(item && item.warning_flags)
    const risk = text(item && item.risk_level, "unknown")
    return {
      id: templateId,
      title: templateId,
      subtitle: `${category} · v${version}`,
      category,
      risk,
      riskTone: riskTone(risk),
      sourceChannel: text(item && item.source_channel, "community"),
      maintainer: text(item && item.maintainer, "unknown"),
      tags,
      badges: [
        ...tags,
        ...reviewLabels,
        ...warningFlags,
      ].slice(0, 5).map((label) => ({ label, tone: badgeTone(label) })),
      signals: engagementSummary(item),
      raw: item || {},
    }
  }

  function buildTemplateDrawerRows(item) {
    const model = buildTemplateCardModel(item)
    return [
      { label: "Template", value: model.id || "-" },
      { label: "Version", value: text(model.raw && model.raw.version, "-") },
      { label: "Category", value: model.category },
      { label: "Maintainer", value: model.maintainer },
      { label: "Source", value: model.sourceChannel },
      { label: "Risk", value: model.risk },
    ]
  }

  function buildProfilePackCardModel(item) {
    const packId = text(item && item.pack_id)
    const version = text(item && item.version, "-")
    const packType = text(item && item.pack_type, "bot_profile_pack")
    const risk = text(item && item.risk_level, "unknown")
    const reviewLabels = list(item && item.review_labels)
    const warningFlags = list(item && item.warning_flags)
    const sections = list(item && item.sections)

    return {
      id: packId,
      title: packId,
      subtitle: `${packType} · v${version}`,
      packType,
      version,
      risk,
      riskTone: riskTone(risk),
      featured: Boolean(item && item.featured),
      compatibility: text(item && item.compatibility, "unknown"),
      sourceSubmissionId: text(item && item.source_submission_id, "-"),
      badges: [
        ...(Boolean(item && item.featured) ? ["featured"] : []),
        ...reviewLabels,
        ...warningFlags,
      ].slice(0, 6).map((label) => ({ label, tone: badgeTone(label) })),
      signals: [
        { key: "sections", label: "Sections", value: compact(sections.length) },
        { key: "labels", label: "Labels", value: compact(reviewLabels.length) },
        { key: "flags", label: "Flags", value: compact(warningFlags.length) },
      ],
      raw: item || {},
    }
  }

  const api = {
    riskTone,
    badgeTone,
    compact,
    buildTemplateCardModel,
    buildTemplateDrawerRows,
    buildProfilePackCardModel,
  }

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api
  }
  globalScope.SharelifeMarketCards = api
})(typeof globalThis !== "undefined" ? globalThis : this)
