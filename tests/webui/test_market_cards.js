const test = require("node:test")
const assert = require("node:assert/strict")

const {
  riskTone,
  badgeTone,
  compact,
  buildTemplateCardModel,
  buildTemplateDrawerRows,
  buildProfilePackCardModel,
} = require("../../sharelife/webui/market_cards.js")

test("compact formats large counters", () => {
  assert.equal(compact(980), "980")
  assert.equal(compact(2400), "2.4k")
  assert.equal(compact(1500000), "1.5m")
})

test("riskTone and badgeTone map risk classes", () => {
  assert.equal(riskTone("high"), "danger")
  assert.equal(riskTone("medium"), "warning")
  assert.equal(riskTone("low"), "success")
  assert.equal(badgeTone("prompt_injection_detected"), "danger")
  assert.equal(badgeTone("approved_with_notice"), "warning")
  assert.equal(badgeTone("featured"), "success")
})

test("buildTemplateCardModel extracts market-ready template fields", () => {
  const card = buildTemplateCardModel({
    template_id: "community/basic",
    version: "1.2.0",
    category: "coding",
    tags: ["review", "strict"],
    risk_level: "medium",
    review_labels: ["approved_with_notice"],
    warning_flags: ["provider_override"],
    source_channel: "community",
    maintainer: "sharelife-core",
    engagement: {
      trial_requests: 1402,
      installs: 992,
      prompt_generations: 212,
      package_generations: 88,
    },
  })

  assert.equal(card.id, "community/basic")
  assert.equal(card.subtitle, "coding · v1.2.0")
  assert.equal(card.riskTone, "warning")
  assert.equal(card.signals[0].value, "1.4k")
  assert.equal(card.signals[1].value, "992")
  assert.equal(card.badges.length, 4)
})

test("buildTemplateDrawerRows exposes structured detail rows", () => {
  const rows = buildTemplateDrawerRows({
    template_id: "community/basic",
    version: "1.0.0",
    category: "support",
    maintainer: "team",
    source_channel: "official",
    risk_level: "low",
  })

  assert.equal(rows[0].label, "Template")
  assert.equal(rows[0].value, "community/basic")
  assert.equal(rows[5].value, "low")
})

test("buildProfilePackCardModel maps catalog rows", () => {
  const card = buildProfilePackCardModel({
    pack_id: "profile/community-safe",
    pack_type: "extension_pack",
    version: "2.0.1",
    risk_level: "low",
    featured: true,
    review_labels: ["approved"],
    warning_flags: [],
    source_submission_id: "sub-20",
  })

  assert.equal(card.id, "profile/community-safe")
  assert.equal(card.subtitle, "extension_pack · v2.0.1")
  assert.equal(card.featured, true)
  assert.equal(card.riskTone, "success")
  assert.equal(card.compatibility, "unknown")
  assert.equal(card.signals[0].key, "sections")
  assert.equal(card.signals[0].value, "0")
  assert.equal(card.badges[0].label, "featured")
})
