(function bootstrapProfilePackMarket(globalScope) {
  function textValue(value, fallback = "") {
    if (value === undefined || value === null) {
      return fallback
    }
    const text = String(value).trim()
    return text || fallback
  }

  function splitList(value) {
    const text = textValue(value)
    if (!text) return []
    const out = []
    const seen = new Set()
    text.split(",").forEach((item) => {
      const normalized = textValue(item)
      if (!normalized || seen.has(normalized)) return
      seen.add(normalized)
      out.push(normalized)
    })
    return out
  }

  function normalizeSubmissionDecision(value) {
    const normalized = textValue(value).toLowerCase()
    if (normalized === "approve" || normalized === "approved") return "approve"
    if (normalized === "reject" || normalized === "rejected") return "reject"
    return normalized
  }

  function compactQuery(input) {
    const out = {}
    Object.entries(input || {}).forEach(([key, value]) => {
      const text = textValue(value)
      if (!text) return
      out[key] = text
    })
    return out
  }

  function buildSubmitPayload(input) {
    const data = input || {}
    const artifactId = textValue(data.artifactId) || textValue(data.fallbackArtifactId)
    const submitOptions = data.submitOptions && typeof data.submitOptions === "object"
      ? data.submitOptions
      : null
    return {
      user_id: textValue(data.userId, "webui-user"),
      artifact_id: artifactId,
      ...(submitOptions ? { submit_options: submitOptions } : {}),
    }
  }

  function buildSubmissionDecisionPayload(input) {
    const data = input || {}
    return {
      submission_id: textValue(data.submissionId),
      decision: normalizeSubmissionDecision(data.decision),
      review_note: textValue(data.reviewNote),
      review_labels: splitList(data.reviewLabels),
    }
  }

  function buildSubmissionFilterQuery(input) {
    const data = input || {}
    return compactQuery({
      status: data.status,
      pack_id: data.packQuery,
      pack_type: data.packType,
      risk_level: data.riskLevel,
      review_label: data.reviewLabel,
      warning_flag: data.warningFlag,
    })
  }

  function buildCatalogFilterQuery(input) {
    const data = input || {}
    return compactQuery({
      pack_id: data.packQuery,
      pack_type: data.packType,
      risk_level: data.riskLevel,
      featured: data.featured,
      review_label: data.reviewLabel,
      warning_flag: data.warningFlag,
    })
  }

  function buildCatalogCompareQuery(input) {
    const data = input || {}
    return compactQuery({
      pack_id: data.packId,
      selected_sections: splitList(data.selectedSections).join(","),
    })
  }

  function pickProfilePackSubmissionFields(row) {
    const item = row || {}
    return compactQuery({
      profilePackDecisionSubmissionId: textValue(item.submission_id || item.id),
      profilePackCatalogPackId: textValue(item.pack_id),
    })
  }

  function pickProfilePackCatalogFields(row) {
    const item = row || {}
    return compactQuery({
      profilePackCatalogPackId: textValue(item.pack_id),
      profilePackDecisionSubmissionId: textValue(item.source_submission_id),
      profilePackFeaturedPackId: textValue(item.pack_id),
    })
  }

  const api = {
    splitList,
    normalizeSubmissionDecision,
    buildSubmitPayload,
    buildSubmissionDecisionPayload,
    buildSubmissionFilterQuery,
    buildCatalogFilterQuery,
    buildCatalogCompareQuery,
    pickProfilePackSubmissionFields,
    pickProfilePackCatalogFields,
  }

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api
  }
  globalScope.SharelifeProfilePackMarket = api
})(typeof globalThis !== "undefined" ? globalThis : this)
