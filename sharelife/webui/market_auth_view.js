(function bootstrapMarketAuthView(globalScope) {
  function text(value, fallback = "") {
    if (value === undefined || value === null) return fallback
    const output = String(value).trim()
    return output || fallback
  }

  function normalizeRole(role) {
    return text(role).toLowerCase()
  }

  function isReviewerRole(role) {
    return normalizeRole(role) === "reviewer"
  }

  function buildAuthRoleOptions(roles, preferredRole, options = {}) {
    const t = typeof options.i18nMessage === "function"
      ? options.i18nMessage
      : (_key, fallback) => String(fallback || "")
    const preferred = text(preferredRole, "member")
    const inputRoles = Array.isArray(roles) ? roles.map((item) => text(item)).filter(Boolean) : []
    const effectiveRoles = inputRoles.includes(preferred) ? [preferred] : [preferred]
    return effectiveRoles.map((role) => {
      if (role === "member") {
        return { value: role, label: t("option.member", "member"), i18nKey: "option.member" }
      }
      if (role === "reviewer") {
        return { value: role, label: t("option.reviewer", "reviewer"), i18nKey: "option.reviewer" }
      }
      if (role === "admin") {
        return { value: role, label: t("option.admin", "admin"), i18nKey: "option.admin" }
      }
      return { value: role, label: role, i18nKey: "" }
    })
  }

  function resolveConsoleVisibility(authRequired, authRole) {
    const role = normalizeRole(authRole || "member")
    if (!authRequired) {
      return {
        memberHidden: false,
        reviewerHidden: true,
        adminHidden: true,
        fullHidden: true,
      }
    }
    if (role === "admin") {
      return {
        memberHidden: false,
        reviewerHidden: false,
        adminHidden: false,
        fullHidden: false,
      }
    }
    if (role === "reviewer") {
      return {
        memberHidden: false,
        reviewerHidden: false,
        adminHidden: true,
        fullHidden: true,
      }
    }
    return {
      memberHidden: false,
      reviewerHidden: true,
      adminHidden: true,
      fullHidden: true,
    }
  }

  function applyConsoleVisibility(links, visibility) {
    const memberLink = links && links.member ? links.member : null
    const reviewerLink = links && links.reviewer ? links.reviewer : null
    const adminLink = links && links.admin ? links.admin : null
    const fullLink = links && links.full ? links.full : null
    const hide = (node, value) => {
      if (!node || !node.classList || typeof node.classList.toggle !== "function") return
      node.classList.toggle("hidden", Boolean(value))
    }
    hide(memberLink, visibility && visibility.memberHidden)
    hide(reviewerLink, visibility && visibility.reviewerHidden)
    hide(adminLink, visibility && visibility.adminHidden)
    hide(fullLink, visibility && visibility.fullHidden)
  }

  const api = {
    normalizeRole,
    isReviewerRole,
    buildAuthRoleOptions,
    resolveConsoleVisibility,
    applyConsoleVisibility,
  }

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api
  }
  globalScope.SharelifeMarketAuthView = api
})(typeof globalThis !== "undefined" ? globalThis : this)
