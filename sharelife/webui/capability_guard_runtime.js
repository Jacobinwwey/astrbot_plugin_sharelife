(function bootstrapCapabilityGuardRuntime(globalScope) {
  const DEFAULT_BASE_OPERATIONS = Object.freeze([
    "auth.info.read",
    "auth.login",
    "health.read",
    "ui.capabilities.read",
  ])

  const DEFAULT_MEMBER_OPERATIONS = Object.freeze([
    "member.installations.read",
    "member.installations.refresh",
    "member.installations.uninstall",
    "member.profile_pack.imports.delete",
    "member.profile_pack.imports.local_astrbot",
    "member.profile_pack.imports.package_upload",
    "member.profile_pack.imports.read",
    "member.profile_pack.imports.write",
    "member.tasks.read",
    "member.tasks.refresh",
    "member.submissions.read",
    "member.submissions.detail.read",
    "member.submissions.package.download",
    "member.profile_pack.submissions.read",
    "member.profile_pack.submissions.detail.read",
    "member.profile_pack.submissions.withdraw",
    "member.profile_pack.submissions.export.download",
    "notifications.read",
    "preferences.read",
    "preferences.write",
    "profile_pack.catalog.read",
    "profile_pack.community.submit",
    "templates.detail",
    "templates.install",
    "templates.list",
    "templates.package.download",
    "templates.package.generate",
    "templates.prompt.generate",
    "templates.submit",
    "templates.trial.request",
    "templates.trial.status",
  ])

  const DEFAULT_ADMIN_OPERATIONS = Object.freeze([
    "admin.apply.workflow",
    "admin.audit.read",
    "admin.reviewer.lifecycle.manage",
    "admin.storage.jobs.read",
    "admin.storage.jobs.run",
    "admin.storage.local_summary.read",
    "admin.storage.policies.read",
    "admin.storage.policies.write",
    "admin.storage.restore.cancel",
    "admin.storage.restore.commit",
    "admin.storage.restore.prepare",
    "admin.storage.restore.read",
    "admin.pipeline.run",
    "admin.profile_pack.featured.write",
    "admin.profile_pack.manage",
    "admin.profile_pack.market.review",
    "admin.retry.manage",
    "admin.submissions.compare",
    "admin.submissions.decide",
    "admin.submissions.package.download",
    "admin.submissions.read",
    "admin.submissions.review",
  ])

  const DEFAULT_REVIEWER_OPERATIONS = Object.freeze([
    "admin.profile_pack.market.review",
    "admin.submissions.compare",
    "admin.submissions.decide",
    "admin.submissions.package.download",
    "admin.submissions.read",
    "admin.submissions.review",
  ])

  const DEFAULT_ANONYMOUS_MEMBER_OPERATIONS = Object.freeze([
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

  function fallbackCapabilityOperations(role, options = {}) {
    const normalizedRole = String(role || "").trim().toLowerCase()
    const authenticated = options.authenticated !== false
    const allowAnonymousMember = options.allowAnonymousMember === true
    const base = normalizeOperations(options.baseOperations || DEFAULT_BASE_OPERATIONS)
    const member = normalizeOperations(options.memberOperations || DEFAULT_MEMBER_OPERATIONS)
    const reviewer = normalizeOperations(options.reviewerOperations || DEFAULT_REVIEWER_OPERATIONS)
    const admin = normalizeOperations(options.adminOperations || DEFAULT_ADMIN_OPERATIONS)
    const anonymousMember = normalizeOperations(
      options.anonymousMemberFallbackOperations || DEFAULT_ANONYMOUS_MEMBER_OPERATIONS,
    )

    if (normalizedRole === "admin") {
      return normalizeOperations([...base, ...member, ...reviewer, ...admin])
    }
    if (normalizedRole === "reviewer") {
      return normalizeOperations([...base, ...member, ...reviewer])
    }
    if (normalizedRole === "member") {
      if (!authenticated && allowAnonymousMember) {
        return anonymousMember.slice()
      }
      return normalizeOperations([...base, ...member])
    }
    return base.slice()
  }

  function hasCapability(capability, options = {}) {
    const required = String(capability || "").trim()
    if (!required) return true

    const pageMode = String(options.pageMode || "").trim().toLowerCase()
    const reviewerAdminBridgeActive = options.reviewerAdminBridgeActive === true
    if (pageMode === "reviewer" && !reviewerAdminBridgeActive) {
      return false
    }

    const operations = normalizeOperations(options.operations)
    return operations.includes(required)
  }

  function requiredCapabilityForControl(controlId, controlCapabilityMap = {}) {
    if (!controlCapabilityMap || typeof controlCapabilityMap !== "object") {
      return ""
    }
    return String(controlCapabilityMap[String(controlId || "")] || "").trim()
  }

  function isControlCapabilityAllowed(controlId, options = {}) {
    const required = requiredCapabilityForControl(controlId, options.controlCapabilityMap)
    return hasCapability(required, options)
  }

  const api = {
    fallbackCapabilityOperations,
    hasCapability,
    requiredCapabilityForControl,
    isControlCapabilityAllowed,
  }

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api
  }
  globalScope.SharelifeCapabilityGuardRuntime = api
})(typeof globalThis !== "undefined" ? globalThis : this)
