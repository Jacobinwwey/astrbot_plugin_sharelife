(function bootstrapCapabilityRoleRuntime(globalScope) {
  function normalizeRole(value, fallback = "") {
    const text = String(value || "").trim().toLowerCase()
    if (text === "member" || text === "reviewer" || text === "admin" || text === "public") {
      return text
    }
    return String(fallback || "")
  }

  function fixedRoleByPageMode(pageMode, options = {}) {
    const mode = normalizeRole(pageMode)
    const reviewerAdminBridgeActive = options.reviewerAdminBridgeActive === true
    if (mode === "member" || mode === "admin") {
      return mode
    }
    if (mode === "reviewer") {
      return reviewerAdminBridgeActive ? "admin" : "member"
    }
    return ""
  }

  function fallbackCapabilityRole(options = {}) {
    const mode = normalizeRole(options.pageMode)
    const reviewerAdminBridgeActive = options.reviewerAdminBridgeActive === true
    if (mode === "reviewer" && !reviewerAdminBridgeActive) {
      return "public"
    }
    const fixedRole = fixedRoleByPageMode(mode, {
      reviewerAdminBridgeActive,
    })
    if (fixedRole) return fixedRole
    const manualRole = normalizeRole(options.roleFieldValue)
    if (manualRole) return manualRole
    return "member"
  }

  const api = {
    normalizeRole,
    fixedRoleByPageMode,
    fallbackCapabilityRole,
  }

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api
  }
  globalScope.SharelifeCapabilityRoleRuntime = api
})(typeof globalThis !== "undefined" ? globalThis : this)
