(function bootstrapWorkspacePayload(globalScope) {
  function isObject(value) {
    return Boolean(value) && typeof value === "object" && !Array.isArray(value)
  }

  function extractWorkspacePayload(response) {
    if (!isObject(response)) {
      return {}
    }

    if (Object.prototype.hasOwnProperty.call(response, "ok")) {
      return isObject(response.data) ? response.data : {}
    }

    if (!isObject(response.data)) {
      return response
    }

    if (Object.prototype.hasOwnProperty.call(response.data, "ok")) {
      return isObject(response.data.data) ? response.data.data : {}
    }

    if (!Object.prototype.hasOwnProperty.call(response.data, "ok")) {
      return response.data
    }

    return response
  }

  const api = {
    extractWorkspacePayload,
  }

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api
  }
  globalScope.SharelifeWorkspacePayload = api
})(typeof globalThis !== "undefined" ? globalThis : this)
