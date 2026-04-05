(function bootstrapCollectionState(globalScope) {
  function textValue(value) {
    if (value === undefined || value === null) {
      return ""
    }
    return String(value).trim()
  }

  function hasActiveCollectionFilters(filters) {
    return Object.values(filters || {}).some((value) => textValue(value) !== "")
  }

  function resolveCollectionStatus(input) {
    const count = Number((input && input.count) || 0)
    if (count > 0) {
      return "ready"
    }
    return input && input.hasActiveFilters ? "empty_filtered" : "empty_unfiltered"
  }

  const api = {
    hasActiveCollectionFilters,
    resolveCollectionStatus,
  }

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api
  }
  globalScope.SharelifeCollectionState = api
})(typeof globalThis !== "undefined" ? globalThis : this)
