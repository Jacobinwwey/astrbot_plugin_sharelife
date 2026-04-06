(function bootstrapMarketFilters(globalScope) {
  const SORT_OPTIONS = Object.freeze({
    TRENDING: "trending",
    DOWNLOADS: "downloads",
    RECENT: "recent",
  })

  const FACET_GROUPS = Object.freeze([
    Object.freeze({
      key: "pack_type",
      titleKey: "market.filter.group.pack_type",
      titleFallback: "Pack Type",
      ordered: Object.freeze(["bot_profile_pack", "extension_pack", "unknown"]),
      seeded: Object.freeze(["bot_profile_pack", "extension_pack", "unknown"]),
      emptyKey: "option.pack_type.all",
      emptyFallback: "All Pack Types",
    }),
    Object.freeze({
      key: "risk_level",
      titleKey: "market.filter.group.risk_level",
      titleFallback: "Risk Level",
      ordered: Object.freeze(["high", "medium", "low", "unknown"]),
      seeded: Object.freeze(["high", "medium", "low", "unknown"]),
      emptyKey: "option.risk.all",
      emptyFallback: "all risk",
    }),
    Object.freeze({
      key: "featured",
      titleKey: "market.filter.group.featured",
      titleFallback: "Featured",
      ordered: Object.freeze(["true", "false"]),
      seeded: Object.freeze(["true", "false"]),
      emptyKey: "option.featured_status.all",
      emptyFallback: "all featured status",
    }),
    Object.freeze({
      key: "compatibility",
      titleKey: "market.filter.group.compatibility",
      titleFallback: "Compatibility",
      ordered: Object.freeze(["compatible", "degraded", "blocked", "unknown"]),
      seeded: Object.freeze(["compatible", "degraded", "blocked", "unknown"]),
    }),
    Object.freeze({
      key: "review_label",
      titleKey: "market.filter.group.review_label",
      titleFallback: "Review Label",
      ordered: Object.freeze([]),
      seeded: Object.freeze([
        "official_featured",
        "approved",
        "community_verified",
        "risk_low",
        "risk_medium",
        "risk_high",
      ]),
    }),
    Object.freeze({
      key: "warning_flag",
      titleKey: "market.filter.group.warning_flag",
      titleFallback: "Warning Flag",
      ordered: Object.freeze([]),
      seeded: Object.freeze([
        "prompt_injection_detected",
        "ignore_previous_instructions",
        "reveal_system_prompt",
        "plugin_install_failed",
        "capability_mismatch",
      ]),
    }),
  ])

  function asGroups(groups) {
    return Array.isArray(groups) ? groups : FACET_GROUPS
  }

  function createFacetSelectionMap(groups = FACET_GROUPS) {
    const selection = {}
    asGroups(groups).forEach((group) => {
      if (!group || !group.key) return
      selection[group.key] = new Set()
    })
    return selection
  }

  function parseCsvQueryValue(value) {
    return String(value || "")
      .split(",")
      .map((item) => String(item || "").trim())
      .filter(Boolean)
  }

  function validSortOption(value, sortOptions = SORT_OPTIONS) {
    const text = String(value || "").trim()
    const options = sortOptions && typeof sortOptions === "object" ? sortOptions : SORT_OPTIONS
    const values = Object.values(options)
    if (values.includes(text)) return text
    return options.TRENDING || SORT_OPTIONS.TRENDING
  }

  function parseQueryState(search, options = {}) {
    const groups = asGroups(options.groups)
    const sortOptions = options.sortOptions && typeof options.sortOptions === "object"
      ? options.sortOptions
      : SORT_OPTIONS
    const params = search instanceof URLSearchParams ? search : new URLSearchParams(String(search || ""))
    const localSearch = String(params.get("q") || "").trim()
    const localSort = validSortOption(params.get("sort") || sortOptions.TRENDING, sortOptions)
    const selectedPackId = String(params.get("pack_id") || "").trim()
    const localFacets = createFacetSelectionMap(groups)
    groups.forEach((group) => {
      if (!group || !group.key) return
      const queryKey = `facet_${group.key}`
      parseCsvQueryValue(params.get(queryKey)).forEach((value) => {
        localFacets[group.key].add(value)
      })
    })
    return {
      localSearch,
      localSort,
      selectedPackId,
      localFacets,
    }
  }

  function buildQueryStateParams(viewState, options = {}) {
    const groups = asGroups(options.groups)
    const sortOptions = options.sortOptions && typeof options.sortOptions === "object"
      ? options.sortOptions
      : SORT_OPTIONS
    const state = viewState && typeof viewState === "object" ? viewState : {}
    const params = new URLSearchParams()
    const localSearch = String(state.localSearch || "").trim()
    const localSort = validSortOption(state.localSort, sortOptions)
    const selectedPackId = String(state.selectedPackId || "").trim()
    if (localSearch) params.set("q", localSearch)
    if (localSort && localSort !== (sortOptions.TRENDING || SORT_OPTIONS.TRENDING)) {
      params.set("sort", localSort)
    }
    if (selectedPackId) params.set("pack_id", selectedPackId)
    groups.forEach((group) => {
      if (!group || !group.key) return
      const selected = state.localFacets && state.localFacets[group.key]
      if (!(selected instanceof Set) || selected.size === 0) return
      params.set(`facet_${group.key}`, Array.from(selected).sort().join(","))
    })
    return params
  }

  function normalizeFacetValue(groupKey, value) {
    const text = String(value || "").trim()
    if (!text) return "unknown"
    if (groupKey === "featured") {
      if (text === "true" || text === "1" || text === "yes") return "true"
      return "false"
    }
    return text
  }

  function facetValuesForItem(item, groupKey) {
    if (!item || typeof item !== "object") return ["unknown"]
    if (groupKey === "pack_type") {
      return [normalizeFacetValue(groupKey, item.pack_type)]
    }
    if (groupKey === "risk_level") {
      return [normalizeFacetValue(groupKey, item.risk_level)]
    }
    if (groupKey === "featured") {
      return [item.featured ? "true" : "false"]
    }
    if (groupKey === "compatibility") {
      return [normalizeFacetValue(groupKey, item.compatibility)]
    }
    if (groupKey === "review_label") {
      const labels = Array.isArray(item.review_labels) ? item.review_labels : []
      return labels.length ? labels.map((entry) => normalizeFacetValue(groupKey, entry)) : ["unknown"]
    }
    if (groupKey === "warning_flag") {
      const flags = Array.isArray(item.warning_flags) ? item.warning_flags : []
      return flags.length ? flags.map((entry) => normalizeFacetValue(groupKey, entry)) : ["unknown"]
    }
    return ["unknown"]
  }

  function marketRowSearchText(item) {
    if (!item || typeof item !== "object") return ""
    const labels = Array.isArray(item.review_labels) ? item.review_labels.join(" ") : ""
    const flags = Array.isArray(item.warning_flags) ? item.warning_flags.join(" ") : ""
    const issues = Array.isArray(item.compatibility_issues) ? item.compatibility_issues.join(" ") : ""
    const source = String(item.source_submission_id || "")
    const packId = String(item.pack_id || "")
    const packType = String(item.pack_type || "")
    const risk = String(item.risk_level || "")
    const compatibility = String(item.compatibility || "")
    const version = String(item.version || "")
    return [packId, packType, risk, compatibility, labels, flags, issues, source, version]
      .join(" ")
      .toLowerCase()
  }

  function rowMatchesSearch(item, searchTerm) {
    const term = String(searchTerm || "").trim().toLowerCase()
    if (!term) return true
    return marketRowSearchText(item).includes(term)
  }

  function rowMatchesFacets(item, facetSelection, options = {}) {
    const groups = asGroups(options.groups)
    const excludedGroup = String(options.excludedGroup || "")
    return groups.every((group) => {
      if (!group || !group.key || group.key === excludedGroup) return true
      const selectedSet = facetSelection && facetSelection[group.key]
      if (!(selectedSet instanceof Set) || selectedSet.size === 0) return true
      const values = facetValuesForItem(item, group.key)
      return values.some((value) => selectedSet.has(value))
    })
  }

  function hasActiveLocalFilters(searchTerm, facetSelection, groups = FACET_GROUPS) {
    const hasSearch = String(searchTerm || "").trim() !== ""
    if (hasSearch) return true
    return asGroups(groups).some((group) => {
      if (!group || !group.key) return false
      const selectedSet = facetSelection && facetSelection[group.key]
      return Boolean(selectedSet && selectedSet.size > 0)
    })
  }

  function fallbackCatalogRankScore(item) {
    return Number(item && item.rank_score || 0)
  }

  function fallbackParseIsoDate(value) {
    if (!value) return 0
    const parsed = Date.parse(String(value))
    return Number.isFinite(parsed) ? parsed : 0
  }

  function sortCatalogRows(rows, sortMode, options = {}) {
    const items = Array.isArray(rows) ? rows.slice() : []
    const mode = validSortOption(sortMode, SORT_OPTIONS)
    const rankScore =
      typeof options.catalogRankScore === "function"
        ? options.catalogRankScore
        : fallbackCatalogRankScore
    const parseIsoDate =
      typeof options.parseIsoDate === "function"
        ? options.parseIsoDate
        : fallbackParseIsoDate
    if (mode === SORT_OPTIONS.DOWNLOADS) {
      return items.sort((left, right) => {
        const leftCount = Number(left && left.engagement && left.engagement.installs || 0)
        const rightCount = Number(right && right.engagement && right.engagement.installs || 0)
        if (rightCount !== leftCount) return rightCount - leftCount
        return rankScore(right) - rankScore(left)
      })
    }
    if (mode === SORT_OPTIONS.RECENT) {
      return items.sort((left, right) => {
        const leftTime = parseIsoDate(left && (left.featured_at || left.published_at))
        const rightTime = parseIsoDate(right && (right.featured_at || right.published_at))
        if (rightTime !== leftTime) return rightTime - leftTime
        return rankScore(right) - rankScore(left)
      })
    }
    return items.sort((left, right) => {
      const scoreDiff = rankScore(right) - rankScore(left)
      if (scoreDiff !== 0) return scoreDiff
      const leftTime = parseIsoDate(left && (left.featured_at || left.published_at))
      const rightTime = parseIsoDate(right && (right.featured_at || right.published_at))
      if (rightTime !== leftTime) return rightTime - leftTime
      return String(left && left.pack_id || "").localeCompare(String(right && right.pack_id || ""))
    })
  }

  function sortedFacetEntries(group, bucket) {
    const entries = Array.from((bucket instanceof Map ? bucket : new Map()).entries())
    const order = Array.isArray(group && group.ordered) ? group.ordered : []
    if (order.length) {
      return entries.sort((left, right) => {
        const leftIndex = order.indexOf(left[0])
        const rightIndex = order.indexOf(right[0])
        const normalizedLeft = leftIndex >= 0 ? leftIndex : Number.MAX_SAFE_INTEGER
        const normalizedRight = rightIndex >= 0 ? rightIndex : Number.MAX_SAFE_INTEGER
        if (normalizedLeft !== normalizedRight) return normalizedLeft - normalizedRight
        if (right[1] !== left[1]) return right[1] - left[1]
        return String(left[0]).localeCompare(String(right[0]))
      })
    }
    return entries.sort((left, right) => {
      if (right[1] !== left[1]) return right[1] - left[1]
      return String(left[0]).localeCompare(String(right[0]))
    })
  }

  function completeFacetBucket(group, bucket, selectedSet) {
    const out = new Map(bucket instanceof Map ? bucket.entries() : [])
    const seeded = Array.isArray(group && group.seeded) ? group.seeded : []
    seeded.forEach((value) => {
      const normalized = normalizeFacetValue(group && group.key, value)
      if (!normalized) return
      if (!out.has(normalized)) out.set(normalized, 0)
    })
    if (selectedSet instanceof Set) {
      selectedSet.forEach((value) => {
        const normalized = normalizeFacetValue(group && group.key, value)
        if (!normalized) return
        if (!out.has(normalized)) out.set(normalized, 0)
      })
    }
    return out
  }

  function computeFacetBuckets(rows, facetSelection, options = {}) {
    const groups = asGroups(options.groups)
    const bucket = {}
    groups.forEach((group) => {
      if (!group || !group.key) return
      const counts = new Map()
      const scopedRows = Array.isArray(rows)
        ? rows.filter((item) =>
          rowMatchesFacets(item, facetSelection, { groups, excludedGroup: group.key }))
        : []
      scopedRows.forEach((item) => {
        facetValuesForItem(item, group.key).forEach((value) => {
          counts.set(value, (counts.get(value) || 0) + 1)
        })
      })
      bucket[group.key] = counts
    })
    return bucket
  }

  function buildLocalCatalogView(baseRows, viewState, options = {}) {
    const rows = Array.isArray(baseRows) ? baseRows : []
    const state = viewState && typeof viewState === "object" ? viewState : {}
    const groups = asGroups(options.groups)
    const searchedRows = rows.filter((item) => rowMatchesSearch(item, state.localSearch))
    const filteredRows = searchedRows.filter((item) =>
      rowMatchesFacets(item, state.localFacets, { groups }))
    const sortedRows = sortCatalogRows(filteredRows, state.localSort, options)
    return {
      baseRows: rows,
      searchedRows,
      filteredRows,
      sortedRows,
    }
  }

  const api = {
    SORT_OPTIONS,
    FACET_GROUPS,
    createFacetSelectionMap,
    parseCsvQueryValue,
    validSortOption,
    parseQueryState,
    buildQueryStateParams,
    normalizeFacetValue,
    facetValuesForItem,
    marketRowSearchText,
    rowMatchesSearch,
    rowMatchesFacets,
    hasActiveLocalFilters,
    sortCatalogRows,
    sortedFacetEntries,
    completeFacetBucket,
    computeFacetBuckets,
    buildLocalCatalogView,
  }

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api
  }

  globalScope.SharelifeMarketFilters = api
})(typeof globalThis !== "undefined" ? globalThis : this)
