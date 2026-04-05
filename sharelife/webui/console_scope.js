(function bootstrapConsoleScope(globalScope) {
  const PAGE_MODES = ["auto", "member", "reviewer", "admin"]
  const SCOPES = ["shared", "member", "reviewer", "admin", "all"]

  function normalizePageMode(value) {
    const text = String(value || "").trim().toLowerCase()
    if (text === "member") return "member"
    if (text === "reviewer") return "reviewer"
    if (text === "admin") return "admin"
    return "auto"
  }

  function pageModeFromPath(pathname) {
    const text = String(pathname || "")
      .trim()
      .toLowerCase()
    if (text === "/user" || text === "/user/") return "member"
    if (text === "/member" || text === "/member/") return "member"
    if (text === "/reviewer" || text === "/reviewer/") return "reviewer"
    if (text === "/admin" || text === "/admin/") return "admin"
    return "auto"
  }

  function normalizeScope(value) {
    const text = String(value || "").trim().toLowerCase()
    if (text === "member") return "member"
    if (text === "reviewer") return "reviewer"
    if (text === "admin") return "admin"
    if (text === "all") return "all"
    return "shared"
  }

  function resolveConsoleScope(input) {
    const payload = input && typeof input === "object" ? input : {}
    const mode = normalizePageMode(payload.pageMode)
    if (mode === "member" || mode === "reviewer" || mode === "admin") return mode
    const authRequired = Boolean(payload.authRequired)
    const authRole = String(payload.authRole || "").trim().toLowerCase()
    if (authRequired) {
      if (authRole === "admin") return "admin"
      if (authRole === "reviewer") return "reviewer"
      return "member"
    }
    const manualRole = String(payload.manualRole || "").trim().toLowerCase()
    if (manualRole === "reviewer") return "reviewer"
    return manualRole === "admin" ? "admin" : "member"
  }

  function scopeVisible(targetScope, activeScope) {
    const scope = normalizeScope(targetScope)
    const active = normalizeScope(activeScope)
    if (scope === "all" || scope === "shared") return true
    if (active !== "member" && active !== "reviewer" && active !== "admin") return false
    return scope === active
  }

  const api = {
    PAGE_MODES,
    SCOPES,
    normalizePageMode,
    pageModeFromPath,
    normalizeScope,
    resolveConsoleScope,
    scopeVisible,
  }

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api
  }
  globalScope.SharelifeConsoleScope = api
})(typeof globalThis !== "undefined" ? globalThis : this)
