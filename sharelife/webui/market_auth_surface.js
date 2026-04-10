(function bootstrapMarketAuthSurface(globalScope) {
  function normalizeRoles(value) {
    if (!Array.isArray(value) || !value.length) return []
    return value
      .map((item) => String(item || "").trim())
      .filter(Boolean)
  }

  function describeMarketAuthSurface(input) {
    const payload = input && typeof input === "object" ? input : {}
    const authRequired = Boolean(payload.authRequired)
    const allowAnonymousMember = Boolean(payload.allowAnonymousMember)
    const authenticated = Boolean(payload.authenticated)
    const promptRequested = Boolean(payload.promptRequested)
    const roles = normalizeRoles(payload.availableRoles)
    const rolesText = roles.length ? roles.join(", ") : "none"

    if (!authRequired) {
      return {
        mode: "disabled",
        rolesText,
        canBrowseAnonymously: false,
        showAuthPanel: false,
      }
    }

    const canBrowseAnonymously = allowAnonymousMember && !authenticated
    if (canBrowseAnonymously) {
      return {
        mode: "optional",
        rolesText,
        canBrowseAnonymously: true,
        showAuthPanel: promptRequested,
      }
    }

    return {
      mode: "required",
      rolesText,
      canBrowseAnonymously: false,
      showAuthPanel: true,
    }
  }

  const api = {
    describeMarketAuthSurface,
  }

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api
  }
  globalScope.SharelifeMarketAuthSurface = api
})(typeof globalThis !== "undefined" ? globalThis : this)
