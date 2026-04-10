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

  function normalizeStringList(value) {
    if (Array.isArray(value)) {
      const out = []
      const seen = new Set()
      value.forEach((item) => {
        const normalized = textValue(item)
        if (!normalized || seen.has(normalized)) return
        seen.add(normalized)
        out.push(normalized)
      })
      return out
    }
    return splitList(value)
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

  function normalizeChoice(value, allowed, fallback) {
    const text = textValue(value).toLowerCase()
    if (Array.isArray(allowed) && allowed.includes(text)) {
      return text
    }
    return fallback
  }

  function buildInstallOptions(input) {
    const data = input || {}
    const selectedSections = normalizeStringList(data.selectedSections)
    return {
      preflight: Boolean(data.preflight),
      force_reinstall: Boolean(data.forceReinstall),
      source_preference: textValue(data.sourcePreference, "auto") || "auto",
      selected_sections: selectedSections,
    }
  }

  function buildUploadOptions(input) {
    const data = input || {}
    const normalized = {
      scan_mode: normalizeChoice(data.scanMode, ["strict", "balanced"], "balanced"),
      visibility: normalizeChoice(data.visibility, ["community", "private"], "community"),
      replace_existing: Boolean(data.replaceExisting),
    }
    const idempotencyKey = textValue(data.idempotencyKey)
    if (idempotencyKey) {
      normalized.idempotency_key = idempotencyKey
    }
    return normalized
  }

  function buildSubmitOptions(input) {
    return buildProfilePackSubmitOptions(input, {
      includeSelectedItemPaths: false,
      includeSource: false,
      includeIdempotencyKey: true,
    })
  }

  function buildProfilePackSubmitOptions(input, options) {
    const data = input || {}
    const config = options && typeof options === "object" ? options : {}
    const selectedSections = normalizeStringList(data.selectedSections)
    const selectedItemPaths = normalizeStringList(data.selectedItemPaths)
    const normalized = {
      pack_type: normalizeChoice(data.packType, ["bot_profile_pack", "extension_pack"], "bot_profile_pack"),
      selected_sections: selectedSections,
      redaction_mode: normalizeChoice(
        data.redactionMode,
        [
          "exclude_secrets",
          "exclude_provider",
          "include_provider_no_key",
          "include_encrypted_secrets",
        ],
        "exclude_secrets",
      ),
      replace_existing: Boolean(data.replaceExisting),
    }
    const includeSelectedItemPaths = config.includeSelectedItemPaths === true
    if (includeSelectedItemPaths) {
      normalized.selected_item_paths = selectedItemPaths
    }

    const includeSource = config.includeSource === true
    if (includeSource) {
      const source = textValue(data.source)
      if (source) {
        normalized.source = source
      }
    }

    const includeIdempotencyKey = config.includeIdempotencyKey !== false
    if (includeIdempotencyKey) {
      const idempotencyKey = textValue(data.idempotencyKey)
      if (idempotencyKey) {
        normalized.idempotency_key = idempotencyKey
      }
    }
    return normalized
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
    normalizeStringList,
    normalizeSubmissionDecision,
    buildInstallOptions,
    buildUploadOptions,
    buildSubmitOptions,
    buildProfilePackSubmitOptions,
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
