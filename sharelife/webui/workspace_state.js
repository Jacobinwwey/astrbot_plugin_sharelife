(function bootstrapWorkspaceState(globalScope) {
  function textValue(value, fallback = "") {
    if (value === undefined || value === null || value === "") {
      return fallback
    }
    return String(value)
  }

  function joinList(items) {
    return Array.isArray(items) && items.length ? items.join(", ") : ""
  }

  function uniqueList(items) {
    return Array.from(new Set((Array.isArray(items) ? items : []).filter(Boolean).map((item) => String(item))))
  }

  function buildWorkspaceHash(route) {
    const scope = textValue(route && route.scope)
    const id = textValue(route && route.id)
    if (!id || (scope !== "template" && scope !== "submission")) {
      return ""
    }
    const params = new URLSearchParams({ scope, id })
    return `#${params.toString()}`
  }

  function parseWorkspaceHash(hash) {
    const raw = textValue(hash)
    const fragment = raw.startsWith("#") ? raw.slice(1) : raw
    if (!fragment) {
      return { scope: "", id: "" }
    }
    const params = new URLSearchParams(fragment)
    const scope = textValue(params.get("scope"))
    const id = textValue(params.get("id"))
    if (!id || (scope !== "template" && scope !== "submission")) {
      return { scope: "", id: "" }
    }
    return { scope, id }
  }

  function buildWorkspaceSummary(route) {
    const scope = textValue(route && route.scope)
    const id = textValue(route && route.id)
    if (!id || (scope !== "template" && scope !== "submission")) {
      return {
        empty: true,
        title: "No active workspace",
        routeLabel: "route: idle",
        description: "Select a template or submission row to create a persistent workspace route.",
        scope: "",
        id: "",
      }
    }
    return {
      empty: false,
      title: scope === "template" ? "Template workspace" : "Submission workspace",
      routeLabel: buildWorkspaceHash({ scope, id }) || "route: idle",
      description:
        scope === "template"
          ? `Pinned to template ${id}. Refreshing the page restores this selection.`
          : `Pinned to submission ${id}. Refreshing the page restores review context and compare state.`,
      scope,
      id,
    }
  }

  function buildSubmissionModerationViewModel(detail, comparePayload) {
    const data = detail || {}
    const compare = comparePayload || {}
    if (!data.submission_id) {
      return {
        empty: true,
        title: "No submission selected",
        summary: "Select a submission row to hydrate review fields and compare state.",
        compareStatus: "not_loaded",
        highlights: [],
        warnings: [],
        reviewLabels: "",
        reviewNote: "",
        canReview: false,
        canDownload: false,
      }
    }

    const compareStatus = textValue(compare.comparison && compare.comparison.status, "not_loaded")
    const flags = uniqueList([
      ...(Array.isArray(data.warning_flags) ? data.warning_flags : []),
      ...((compare.details && compare.details.warning_flags && compare.details.warning_flags.submission) || []),
    ])

    const warnings = []
    if (textValue(data.risk_level) === "high") {
      warnings.push("High-risk submission. Confirm prompt diff, labels, and warning flags before approval.")
    }
    if (flags.length) {
      warnings.push(`Warning flags: ${flags.join(", ")}`)
    }
    if (compareStatus === "baseline_missing") {
      warnings.push("No published baseline exists yet. Approval will establish the first baseline.")
    }

    return {
      empty: false,
      title: textValue(data.submission_id, "-"),
      summary: `${textValue(data.template_id, "-")}@${textValue(data.version, "-")}`,
      compareStatus,
      highlights: [
        { label: textValue(data.status, "unknown"), tone: "neutral" },
        { label: textValue(data.risk_level, "unknown"), tone: textValue(data.risk_level) === "high" ? "danger" : "neutral" },
        { label: `compare:${compareStatus}`, tone: compareStatus === "baseline_available" ? "warning" : "neutral" },
      ],
      warnings,
      reviewLabels: joinList(data.review_labels),
      reviewNote: textValue(data.review_note),
      canReview: true,
      canDownload: Boolean(data.package_artifact && data.package_artifact.filename),
    }
  }

  const api = {
    buildWorkspaceHash,
    parseWorkspaceHash,
    buildWorkspaceSummary,
    buildSubmissionModerationViewModel,
  }

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api
  }
  globalScope.SharelifeWorkspace = api
})(typeof globalThis !== "undefined" ? globalThis : this)
