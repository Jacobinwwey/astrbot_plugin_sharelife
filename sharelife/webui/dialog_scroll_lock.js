(function bootstrapDialogScrollLock(globalScope) {
  const BODY_SCROLL_LOCK_CLASS = "modal-scroll-locked"

  function normalizeScopeKey(value) {
    return String(value || "").trim()
  }

  function nextOpenDialogScopes(currentScopes, scopeKey, isOpen) {
    const target = normalizeScopeKey(scopeKey)
    const next = new Set(
      Array.isArray(currentScopes)
        ? currentScopes.map((item) => normalizeScopeKey(item)).filter(Boolean)
        : [],
    )
    if (!target) {
      return Array.from(next).sort()
    }
    if (isOpen) next.add(target)
    else next.delete(target)
    return Array.from(next).sort()
  }

  function shouldLockBodyScroll(currentScopes) {
    return Array.isArray(currentScopes) && currentScopes.length > 0
  }

  function syncBodyScrollLock(bodyNode, currentScopes) {
    const locked = shouldLockBodyScroll(currentScopes)
    if (bodyNode && bodyNode.classList && typeof bodyNode.classList.toggle === "function") {
      bodyNode.classList.toggle(BODY_SCROLL_LOCK_CLASS, locked)
    }
    return locked
  }

  const api = {
    BODY_SCROLL_LOCK_CLASS,
    nextOpenDialogScopes,
    shouldLockBodyScroll,
    syncBodyScrollLock,
  }

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api
  }
  globalScope.SharelifeDialogScrollLock = api
})(typeof globalThis !== "undefined" ? globalThis : this)
