const test = require("node:test")
const assert = require("node:assert/strict")

const {
  resolveUpdatedAt,
  engagementValue,
  buildCardSignalRows,
  buildCardMetaEntries,
  buildMetricCards,
  selectFeaturedCandidate,
  selectTrendingRows,
} = require("../../sharelife/webui/market_catalog_view.js")

test("market catalog view resolves updated date and engagement values", () => {
  const date = resolveUpdatedAt({ featured_at: "2026-04-04T00:00:00Z" }, "en-US")
  assert.ok(String(date).length > 0)
  assert.equal(resolveUpdatedAt({}, "en-US"), "-")
  assert.equal(engagementValue({ engagement: { installs: 12.8 } }, "installs"), 12)
  assert.equal(engagementValue({}, "installs"), 0)
})

test("market catalog view builds card signal rows and meta entries", () => {
  const item = {
    compatibility: "compatible",
    sections: [1, 2],
    review_labels: ["approved"],
    warning_flags: ["warning"],
    featured_at: "2026-04-04T00:00:00Z",
    engagement: {
      installs: 30,
      trial_requests: 12,
    },
  }
  const signals = buildCardSignalRows(item, {
    i18nMessage(key, fallback) {
      return key || fallback
    },
    enumLabel(group, value) {
      return `${group}:${value}`
    },
  })
  assert.equal(signals.length, 4)
  assert.equal(signals[0].value, "compatibility:compatible")

  const meta = buildCardMetaEntries(item, {
    locale: "en-US",
    catalogRankScore() {
      return 88
    },
  })
  assert.equal(meta.length, 4)
  assert.equal(meta[1].value, "30")
  assert.equal(meta[2].value, "12")
  assert.equal(meta[3].value, "88")
})

test("market catalog view builds metric cards and spotlight/trending picks", () => {
  const cards = buildMetricCards({
    total: 10,
    featured: 2,
    safe: 4,
    highRisk: 1,
    extension: 3,
    botProfile: 7,
  })
  assert.equal(cards.length, 6)
  assert.equal(cards[3].tone, "danger")

  const rows = [
    { pack_id: "profile/a", featured: false, rank: 1 },
    { pack_id: "profile/b", featured: true, rank: 2 },
    { pack_id: "profile/c", featured: false, rank: 3 },
  ]
  const featured = selectFeaturedCandidate(rows, null, {
    sortedByTrend(input) {
      return Array.isArray(input) ? input.slice() : []
    },
  })
  assert.equal(featured.pack_id, "profile/b")

  const ranked = selectTrendingRows(rows, null, {
    limit: 2,
    sortedByTrend(input) {
      return Array.isArray(input) ? input.slice() : []
    },
  })
  assert.equal(ranked.length, 2)
  assert.equal(ranked[0].pack_id, "profile/a")
})
