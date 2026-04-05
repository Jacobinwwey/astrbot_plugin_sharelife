(function bootstrapTableInteractions(globalScope) {
  const filterFieldIds = {
    template: {
      tag: "templateTagFilter",
      source_channel: "templateSourceChannelFilter",
      risk_level: "templateRiskFilter",
      review_label: "templateReviewLabelFilter",
      warning_flag: "templateWarningFlagFilter",
    },
    submission: {
      risk_level: "submissionRiskFilter",
      review_label: "submissionReviewLabelFilter",
      warning_flag: "submissionWarningFlagFilter",
    },
    profile_pack_submission: {
      risk_level: "profilePackSubmissionRiskFilter",
      review_label: "profilePackSubmissionReviewLabelFilter",
      warning_flag: "profilePackSubmissionWarningFlagFilter",
    },
    profile_pack_catalog: {
      risk_level: "profilePackCatalogRiskFilter",
      review_label: "profilePackCatalogReviewLabelFilter",
      warning_flag: "profilePackCatalogWarningFlagFilter",
    },
  }

  function textValue(value, fallback = "") {
    if (value === undefined || value === null) {
      return fallback
    }
    return String(value)
  }

  function joinList(items) {
    return Array.isArray(items) && items.length ? items.join(", ") : ""
  }

  function buildTemplateSortQuery(sortBy, sortOrder) {
    const supportedSorts = new Set(["template_id", "recent_activity", "trial_requests", "installs"])
    const normalizedSort = supportedSorts.has(textValue(sortBy).trim())
      ? textValue(sortBy).trim()
      : "template_id"
    const normalizedOrder = textValue(sortOrder).trim().toLowerCase()
    const fallbackOrder = normalizedSort === "template_id" ? "asc" : "desc"
    return {
      sort_by: normalizedSort,
      sort_order: normalizedOrder === "asc" || normalizedOrder === "desc" ? normalizedOrder : fallbackOrder,
    }
  }

  function buildBadgeFilterPatch(scope, category, value) {
    const fieldId = filterFieldIds[scope] && filterFieldIds[scope][category]
    if (!fieldId || value === undefined || value === null || value === "") {
      return {}
    }
    return { [fieldId]: String(value) }
  }

  function buildTemplateSelection(item) {
    const data = item || {}
    const templateId = textValue(data.template_id)
    return {
      selectedId: templateId,
      fieldPatches: templateId
        ? {
            submitTemplateId: templateId,
            trialTemplateId: templateId,
          }
        : {},
      requests: templateId ? ["template_detail"] : [],
    }
  }

  function buildSubmissionSelection(item) {
    const data = item || {}
    const submissionId = textValue(data.submission_id || data.id)
    return {
      selectedId: submissionId,
      fieldPatches: submissionId
        ? {
            decisionSubmissionId: submissionId,
            reviewLabels: joinList(data.review_labels),
            reviewNote: textValue(data.review_note),
          }
        : {},
      requests: submissionId ? ["submission_detail", "submission_compare"] : [],
    }
  }

  const api = {
    buildBadgeFilterPatch,
    buildTemplateSortQuery,
    buildTemplateSelection,
    buildSubmissionSelection,
  }

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api
  }
  globalScope.SharelifeTableInteractions = api
})(typeof globalThis !== "undefined" ? globalThis : this)
