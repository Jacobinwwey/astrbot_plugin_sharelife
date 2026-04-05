(function bootstrapWorkspaceFeedback(globalScope) {
  function textValue(value, fallback = "") {
    if (value === undefined || value === null || value === "") {
      return fallback
    }
    return String(value)
  }

  function buildPanelStateView(input) {
    const data = input || {}
    const status = textValue(data.status, "idle")
    const resource = textValue(data.resource, "Workspace panel")
    const id = textValue(data.id)
    const emptyMessage = textValue(data.emptyMessage, `Select an item to load ${resource.toLowerCase()}.`)
    const errorMessage = textValue(data.errorMessage, "unknown_error")

    if (status === "loading") {
      return {
        visible: true,
        tone: "warning",
        title: `Loading ${resource}`,
        message: id ? `Loading ${resource.toLowerCase()} for ${id}...` : `Loading ${resource.toLowerCase()}...`,
      }
    }

    if (status === "error") {
      return {
        visible: true,
        tone: "danger",
        title: `${resource} unavailable`,
        message: errorMessage,
      }
    }

    if (status === "ready") {
      return {
        visible: false,
        tone: "success",
        title: `${resource} ready`,
        message: "",
      }
    }

    return {
      visible: true,
      tone: "neutral",
      title: `${resource} idle`,
      message: emptyMessage,
    }
  }

  function extractPanelErrorMessage(response, resource) {
    const label = textValue(resource, "Request")
    const payload = response && response.data ? response.data : {}
    const code = payload && payload.error && payload.error.code ? payload.error.code : ""
    const message = payload && payload.message ? payload.message : ""
    const simpleError = payload && payload.error && typeof payload.error === "string" ? payload.error : ""
    const detail = code || message || simpleError || `http_${textValue(response && response.status, "unknown")}`
    return `${label} failed: ${detail}`
  }

  const api = {
    buildPanelStateView,
    extractPanelErrorMessage,
  }

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api
  }
  globalScope.SharelifeWorkspaceFeedback = api
})(typeof globalThis !== "undefined" ? globalThis : this)
