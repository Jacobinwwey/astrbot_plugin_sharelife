const test = require("node:test")
const assert = require("node:assert/strict")

const {
  parseIsoDate,
  listLength,
  packRiskScore,
  packCompatibilityScore,
  catalogRankScore,
  catalogMetrics,
  catalogTrendScore,
  sortedByTrend,
} = require("../../sharelife/webui/market_catalog_insights.js")

test("market catalog insights parse and score base inputs", () => {
  assert.ok(parseIsoDate("2026-04-01T00:00:00Z") > 0)
  assert.equal(parseIsoDate("not-a-date"), 0)
  assert.equal(listLength(["a", "b"]), 2)
  assert.equal(listLength(null), 0)
  assert.equal(packRiskScore("low"), 20)
  assert.equal(packRiskScore("medium"), 12)
  assert.equal(packRiskScore("high"), 4)
  assert.equal(packCompatibilityScore({ compatibility: "compatible" }), 14)
  assert.equal(packCompatibilityScore({ compatibility: "degraded" }), 8)
  assert.equal(packCompatibilityScore({ compatibility: "blocked" }), 0)
})

test("market catalog insights derive rank, metrics, and trend order", () => {
  const rows = [
    {
      pack_id: "profile/a",
      featured: true,
      risk_level: "low",
      compatibility: "compatible",
      review_labels: ["approved"],
      warning_flags: [],
      compatibility_issues: [],
      featured_at: "2026-04-01T00:00:00Z",
      pack_type: "bot_profile_pack",
    },
    {
      pack_id: "profile/b",
      featured: false,
      risk_level: "medium",
      compatibility: "degraded",
      review_labels: [],
      warning_flags: ["capability_mismatch"],
      compatibility_issues: [],
      published_at: "2026-04-03T00:00:00Z",
      pack_type: "extension_pack",
      trend_score: 100,
    },
  ]

  assert.ok(catalogRankScore(rows[0]) > catalogRankScore(rows[1]))

  const metrics = catalogMetrics(rows)
  assert.deepEqual(metrics, {
    total: 2,
    featured: 1,
    highRisk: 0,
    safe: 1,
    extension: 1,
    botProfile: 1,
  })

  assert.equal(catalogTrendScore(rows[1]), 100)
  assert.equal(catalogTrendScore(rows[0]), catalogRankScore(rows[0]))

  const ranked = sortedByTrend(rows)
  assert.equal(ranked[0].pack_id, "profile/a")
  assert.equal(ranked[1].pack_id, "profile/b")
})
