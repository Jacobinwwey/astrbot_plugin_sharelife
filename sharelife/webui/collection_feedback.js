(function bootstrapCollectionFeedback(globalScope) {
  function textValue(value, fallback = "") {
    if (value === undefined || value === null || value === "") {
      return fallback
    }
    return String(value)
  }

  function buildCollectionStateView(input) {
    const data = input || {}
    const status = textValue(data.status, "idle")
    const resource = textValue(data.resource, "Items")
    const idleMessage = textValue(data.idleMessage, `Load ${resource.toLowerCase()} to continue.`)
    const emptyUnfilteredMessage = textValue(
      data.emptyUnfilteredMessage,
      `No ${resource.toLowerCase()} are available yet.`,
    )
    const emptyFilteredMessage = textValue(
      data.emptyFilteredMessage,
      `No ${resource.toLowerCase()} matched the current filters.`,
    )
    const errorMessage = textValue(data.errorMessage, "unknown_error")
    const count = Number(data.count || 0)

    if (status === "loading") {
      return {
        visible: true,
        tone: "warning",
        title: `Loading ${resource}`,
        message: `Loading ${resource.toLowerCase()}...`,
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

    if (status === "empty_unfiltered") {
      return {
        visible: true,
        tone: "neutral",
        title: `${resource} empty`,
        message: emptyUnfilteredMessage,
      }
    }

    if (status === "empty_filtered" || status === "empty") {
      return {
        visible: true,
        tone: "neutral",
        title: `${resource} empty`,
        message: emptyFilteredMessage,
      }
    }

    if (status === "ready") {
      return {
        visible: false,
        tone: "success",
        title: `${resource} ready`,
        message: count > 0 ? `${count} loaded.` : "",
      }
    }

    return {
      visible: true,
      tone: "neutral",
      title: `${resource} idle`,
      message: idleMessage,
    }
  }

  function extractCollectionErrorMessage(response, resource) {
    const label = textValue(resource, "Request")
    const payload = response && response.data ? response.data : {}
    const code = payload && payload.error && payload.error.code ? payload.error.code : ""
    const message = payload && payload.message ? payload.message : ""
    const simpleError = payload && payload.error && typeof payload.error === "string" ? payload.error : ""
    const detail = code || message || simpleError || `http_${textValue(response && response.status, "unknown")}`
    return `${label} failed: ${detail}`
  }

  const api = {
    buildCollectionStateView,
    extractCollectionErrorMessage,
  }

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api
  }
  globalScope.SharelifeCollectionFeedback = api
})(typeof globalThis !== "undefined" ? globalThis : this)
