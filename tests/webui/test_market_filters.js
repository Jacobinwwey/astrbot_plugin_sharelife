const test = require("node:test")
const assert = require("node:assert/strict")

const {
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
} = require("../../sharelife/webui/market_filters.js")

test("market filters expose deterministic sort options and query parsing helpers", () => {
  assert.equal(validSortOption("downloads"), SORT_OPTIONS.DOWNLOADS)
  assert.equal(validSortOption(""), SORT_OPTIONS.TRENDING)
  assert.deepEqual(parseCsvQueryValue(" risk_low , official_featured ,, "), ["risk_low", "official_featured"])
})

test("market filters parse and serialize query state for facet selections", () => {
  const groups = FACET_GROUPS
  const parsed = parseQueryState("?q=starter&sort=downloads&pack_id=profile%2Fofficial&facet_risk_level=low,medium", {
    groups,
    sortOptions: SORT_OPTIONS,
  })
  assert.equal(parsed.localSearch, "starter")
  assert.equal(parsed.localSort, "downloads")
  assert.equal(parsed.selectedPackId, "profile/official")
  assert.equal(parsed.localFacets.risk_level.has("low"), true)
  assert.equal(parsed.localFacets.risk_level.has("medium"), true)

  const params = buildQueryStateParams(parsed, {
    groups,
    sortOptions: SORT_OPTIONS,
  })
  assert.equal(params.get("q"), "starter")
  assert.equal(params.get("sort"), "downloads")
  assert.equal(params.get("pack_id"), "profile/official")
  assert.equal(params.get("facet_risk_level"), "low,medium")
})

test("market filters normalize facet values and search source text", () => {
  assert.equal(normalizeFacetValue("featured", "yes"), "true")
  assert.equal(normalizeFacetValue("risk_level", ""), "unknown")
  assert.deepEqual(
    facetValuesForItem(
      {
        featured: true,
        review_labels: ["approved"],
        warning_flags: ["plugin_install_failed"],
      },
      "review_label",
    ),
    ["approved"],
  )
  const row = {
    pack_id: "profile/official-starter",
    pack_type: "bot_profile_pack",
    risk_level: "low",
    review_labels: ["approved"],
    warning_flags: [],
    source_submission_id: "sub-100",
    version: "1.0.1",
  }
  assert.match(marketRowSearchText(row), /official-starter/)
  assert.equal(rowMatchesSearch(row, "official-starter"), true)
  assert.equal(rowMatchesSearch(row, "community-only"), false)
})

test("market filters evaluate facet predicates and active state", () => {
  const selection = createFacetSelectionMap(FACET_GROUPS)
  selection.risk_level.add("low")
  selection.pack_type.add("bot_profile_pack")
  const passRow = { risk_level: "low", pack_type: "bot_profile_pack", featured: false }
  const blockedRow = { risk_level: "high", pack_type: "bot_profile_pack", featured: false }
  assert.equal(rowMatchesFacets(passRow, selection, { groups: FACET_GROUPS }), true)
  assert.equal(rowMatchesFacets(blockedRow, selection, { groups: FACET_GROUPS }), false)
  assert.equal(hasActiveLocalFilters("", selection, FACET_GROUPS), true)
  assert.equal(hasActiveLocalFilters("official", createFacetSelectionMap(FACET_GROUPS), FACET_GROUPS), true)
  assert.equal(hasActiveLocalFilters("", createFacetSelectionMap(FACET_GROUPS), FACET_GROUPS), false)
})

test("market filters sort catalog rows by downloads, recency, and trending", () => {
  const rows = [
    {
      pack_id: "profile/a",
      rank_score: 70,
      featured_at: "2026-04-01T00:00:00Z",
      engagement: { installs: 2 },
    },
    {
      pack_id: "profile/b",
      rank_score: 50,
      featured_at: "2026-04-03T00:00:00Z",
      engagement: { installs: 9 },
    },
    {
      pack_id: "profile/c",
      rank_score: 75,
      featured_at: "2026-03-29T00:00:00Z",
      engagement: { installs: 9 },
    },
  ]
  const options = {
    catalogRankScore(item) {
      return Number(item.rank_score || 0)
    },
    parseIsoDate(value) {
      return Date.parse(String(value || ""))
    },
  }
  const byDownloads = sortCatalogRows(rows, SORT_OPTIONS.DOWNLOADS, options)
  assert.deepEqual(byDownloads.map((item) => item.pack_id), ["profile/c", "profile/b", "profile/a"])

  const byRecent = sortCatalogRows(rows, SORT_OPTIONS.RECENT, options)
  assert.deepEqual(byRecent.map((item) => item.pack_id), ["profile/b", "profile/a", "profile/c"])

  const byTrending = sortCatalogRows(rows, SORT_OPTIONS.TRENDING, options)
  assert.deepEqual(byTrending.map((item) => item.pack_id), ["profile/c", "profile/a", "profile/b"])
})

test("market filters compute/complete/sort facet buckets", () => {
  const rows = [
    {
      pack_type: "bot_profile_pack",
      risk_level: "low",
      featured: true,
      compatibility: "compatible",
      review_labels: ["approved"],
      warning_flags: [],
    },
    {
      pack_type: "extension_pack",
      risk_level: "medium",
      featured: false,
      compatibility: "degraded",
      review_labels: [],
      warning_flags: ["capability_mismatch"],
    },
  ]
  const selection = createFacetSelectionMap(FACET_GROUPS)
  const buckets = computeFacetBuckets(rows, selection, { groups: FACET_GROUPS })
  assert.equal(buckets.pack_type.get("bot_profile_pack"), 1)
  assert.equal(buckets.pack_type.get("extension_pack"), 1)
  assert.equal(buckets.risk_level.get("low"), 1)
  assert.equal(buckets.risk_level.get("medium"), 1)

  const riskGroup = FACET_GROUPS.find((group) => group.key === "risk_level")
  const completed = completeFacetBucket(
    riskGroup,
    new Map([["low", 2]]),
    new Set(["custom_risk"]),
  )
  assert.equal(completed.get("high"), 0)
  assert.equal(completed.get("custom_risk"), 0)

  const sorted = sortedFacetEntries(riskGroup, completed)
  assert.equal(sorted[0][0], "high")
})
