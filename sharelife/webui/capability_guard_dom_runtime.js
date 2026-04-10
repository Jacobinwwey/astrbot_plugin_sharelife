(function bootstrapCapabilityGuardDomRuntime(globalScope) {
  function applyCapabilityGuardToNode(node, options = {}) {
    if (!node) return
    const allowed = options.allowed !== false
    const lockedHint = String(options.lockedHint || "")

    if (node.classList && typeof node.classList.toggle === "function") {
      node.classList.toggle("capability-blocked", !allowed)
    }
    if (typeof node.setAttribute === "function") {
      node.setAttribute("aria-disabled", allowed ? "false" : "true")
    }

    if (!allowed) {
      if (typeof node.setAttribute === "function") {
        node.setAttribute("data-capability-locked", "1")
      }
      if ("disabled" in node) {
        node.disabled = true
      }
      node.title = lockedHint
      return
    }

    const locked = typeof node.getAttribute === "function"
      ? node.getAttribute("data-capability-locked") === "1"
      : false
    if (locked && "disabled" in node) {
      node.disabled = false
    }
    if (typeof node.removeAttribute === "function") {
      if (locked) {
        node.removeAttribute("data-capability-locked")
      }
      node.removeAttribute("title")
    } else {
      node.title = ""
    }
  }

  const api = {
    applyCapabilityGuardToNode,
  }

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api
  }
  globalScope.SharelifeCapabilityGuardDomRuntime = api
})(typeof globalThis !== "undefined" ? globalThis : this)
