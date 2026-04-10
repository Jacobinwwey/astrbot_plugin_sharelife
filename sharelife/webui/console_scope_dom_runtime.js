(function bootstrapConsoleScopeDomRuntime(globalScope) {
  function textValue(value, fallback = "") {
    if (value === undefined || value === null) return fallback
    const text = String(value).trim()
    return text || fallback
  }

  function isManualVisibility(value) {
    return textValue(value) === "manual"
  }

  function buildScopeLineText(scope, options = {}) {
    const formatMessage = typeof options.formatMessage === "function"
      ? options.formatMessage
      : (_key, fallback = "", tokens = {}) => {
          return String(fallback || "").replace(/\{([a-zA-Z0-9_]+)\}/g, (match, token) => {
            if (!Object.prototype.hasOwnProperty.call(tokens, token)) return match
            return String(tokens[token] ?? "")
          })
        }
    return formatMessage("console.scope.line", "view: {scope}", { scope: textValue(scope, "member") })
  }

  function resolveScopeNodeVisibility(node, activeScope, options = {}) {
    const targetScope = textValue(
      node && typeof node.getAttribute === "function"
        ? node.getAttribute("data-console-scope")
        : "",
      "shared",
    )
    const scopeVisible = typeof options.scopeVisible === "function"
      ? options.scopeVisible
      : (target, active) => {
          if (target === "all" || target === "shared") return true
          return target === textValue(active, "member")
        }
    const visible = Boolean(scopeVisible(targetScope, activeScope))
    const manualVisibility = isManualVisibility(
      node && typeof node.getAttribute === "function"
        ? node.getAttribute("data-scope-visibility")
        : "",
    )
    return {
      targetScope,
      visible,
      manualVisibility,
      hide: !visible,
      removeHidden: visible && !manualVisibility,
    }
  }

  const api = {
    textValue,
    isManualVisibility,
    buildScopeLineText,
    resolveScopeNodeVisibility,
  }

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api
  }
  globalScope.SharelifeConsoleScopeDomRuntime = api
})(typeof globalThis !== "undefined" ? globalThis : this)
