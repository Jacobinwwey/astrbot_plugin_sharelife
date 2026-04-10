(function bootstrapConsoleSurfaceControls(globalScope) {
  function normalizeScope(value) {
    const text = String(value || "").trim().toLowerCase()
    if (text === "admin") return "admin"
    if (text === "reviewer") return "reviewer"
    return "member"
  }

  function normalizePageMode(value) {
    const text = String(value || "").trim().toLowerCase()
    if (text === "member") return "member"
    if (text === "reviewer") return "reviewer"
    if (text === "admin") return "admin"
    return "auto"
  }

  function resolveConsoleHint(scope, options = {}) {
    const normalizedScope = normalizeScope(scope)
    const bridgeActive = options.bridgeActive === true
    if (normalizedScope === "admin") {
      return {
        hintKey: "console.switch.hint.admin",
        fallback: "Admin console focuses on review/apply/governance operations.",
      }
    }
    if (normalizedScope === "reviewer") {
      if (bridgeActive) {
        return {
          hintKey: "console.switch.hint.reviewer",
          fallback: "Reviewer console focuses on moderation queue and risk labeling.",
        }
      }
      return {
        hintKey: "console.switch.hint.reviewer_readonly",
        fallback: "Reviewer console is read-only until an admin session is handed off from /admin.",
      }
    }
    return {
      hintKey: "console.switch.hint.member",
      fallback: "Member console focuses on trial/market operations.",
    }
  }

  function visibilityForPageMode(pageMode) {
    const mode = normalizePageMode(pageMode)
    if (mode === "member") {
      return { member: true, market: true, reviewer: false, admin: false, full: false }
    }
    if (mode === "reviewer") {
      return { member: true, market: true, reviewer: false, admin: true, full: true }
    }
    if (mode === "admin") {
      return { member: true, market: true, reviewer: true, admin: false, full: true }
    }
    return { member: true, market: true, reviewer: true, admin: true, full: true }
  }

  const api = {
    normalizeScope,
    normalizePageMode,
    resolveConsoleHint,
    visibilityForPageMode,
  }

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api
  }
  globalScope.SharelifeConsoleSurfaceControls = api
})(typeof globalThis !== "undefined" ? globalThis : this)
