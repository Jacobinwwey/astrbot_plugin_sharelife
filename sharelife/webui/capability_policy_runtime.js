(function bootstrapCapabilityPolicyRuntime(globalScope) {
  const ANONYMOUS_MEMBER_FALLBACK_OPERATIONS = Object.freeze([
    "auth.info.read",
    "auth.login",
    "health.read",
    "member.installations.read",
    "member.installations.refresh",
    "member.installations.uninstall",
    "member.tasks.read",
    "member.tasks.refresh",
    "notifications.read",
    "preferences.read",
    "preferences.write",
    "profile_pack.catalog.read",
    "templates.detail",
    "templates.install",
    "templates.list",
    "templates.package.download",
    "templates.trial.request",
    "templates.trial.status",
    "ui.capabilities.read",
  ])

  function normalizeOperations(values) {
    const source = Array.isArray(values) ? values : []
    return Array.from(new Set(source.map((item) => String(item || "").trim()).filter(Boolean)))
  }

  function anonymousMemberFallbackOperations() {
    return normalizeOperations(ANONYMOUS_MEMBER_FALLBACK_OPERATIONS)
  }

  const api = {
    anonymousMemberFallbackOperations,
  }

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api
  }
  globalScope.SharelifeCapabilityPolicyRuntime = api
})(typeof globalThis !== "undefined" ? globalThis : this)
