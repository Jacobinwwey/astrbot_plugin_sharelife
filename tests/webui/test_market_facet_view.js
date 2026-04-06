const test = require("node:test")
const assert = require("node:assert/strict")

const {
  facetLabel,
  buildFacetRenderModel,
} = require("../../sharelife/webui/market_facet_view.js")

test("market facet view resolves localized labels by facet type", () => {
  const i18nMessage = (key, fallback) => `i18n:${key || fallback}`
  const enumLabel = (group, value) => `enum:${group}:${value}`
  assert.equal(
    facetLabel({ key: "pack_type" }, "bot_profile_pack", { i18nMessage, enumLabel }),
    "i18n:option.pack_type.bot_profile_pack",
  )
  assert.equal(
    facetLabel({ key: "risk_level" }, "medium", { i18nMessage, enumLabel }),
    "i18n:option.risk.medium",
  )
  assert.equal(
    facetLabel({ key: "compatibility" }, "blocked", { i18nMessage, enumLabel }),
    "enum:compatibility:blocked",
  )
  assert.equal(
    facetLabel({ key: "review_label" }, "approved", { i18nMessage, enumLabel }),
    "enum:review_label:approved",
  )
})

test("market facet view builds render model from buckets and facet selections", () => {
  const groups = [
    {
      key: "risk_level",
      titleKey: "market.filter.group.risk_level",
      titleFallback: "Risk Level",
    },
  ]
  const buckets = {
    risk_level: new Map([["low", 2], ["high", 1]]),
  }
  const facetSelection = {
    risk_level: new Set(["low"]),
  }
  const model = buildFacetRenderModel({
    groups,
    buckets,
    facetSelection,
    completeFacetBucket(_group, bucket) {
      return bucket
    },
    sortedFacetEntries(_group, bucket) {
      return Array.from(bucket.entries())
    },
    i18nMessage(key, fallback) {
      return key || fallback
    },
    enumLabel(group, value) {
      return `${group}:${value}`
    },
  })
  assert.equal(model.length, 1)
  assert.equal(model[0].title, "market.filter.group.risk_level")
  assert.deepEqual(
    model[0].entries.map((entry) => ({
      value: entry.value,
      count: entry.count,
      checked: entry.checked,
    })),
    [
      { value: "low", count: 2, checked: true },
      { value: "high", count: 1, checked: false },
    ],
  )
})
