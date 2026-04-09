const test = require("node:test")
const assert = require("node:assert/strict")

const {
  buildPublicCatalogCard,
  buildPublicCatalogSearchText,
  buildDetailSeed,
} = require("../../sharelife/webui/market_catalog_contract.js")

test("public catalog contract exposes only open-detail as the primary action", () => {
  const item = {
    pack_id: "profile/community-safe",
    version: "2.0.1",
    pack_type: "extension_pack",
    risk_level: "low",
    compatibility: "compatible",
    maintainer: "sharelife-core",
    review_labels: ["approved"],
    warning_flags: [],
    sections: ["plugins", "providers"],
    summary: "A safe shared setup",
  }

  const card = buildPublicCatalogCard(item)
  assert.equal(card.id, "profile/community-safe")
  assert.equal(card.primaryAction.kind, "open_detail")
  assert.equal(card.memberActionsVisible, false)
  assert.equal(card.compatibility, "compatible")
  assert.match(buildPublicCatalogSearchText(item), /community-safe/i)
  assert.match(buildPublicCatalogSearchText(item), /sharelife-core/i)
  assert.equal(buildDetailSeed(item).packId, "profile/community-safe")
})

test("public catalog contract accepts localized search aliases and like count metadata", () => {
  const item = {
    pack_id: "profile/official-safe-reference",
    version: "1.0.1",
    pack_type: "bot_profile_pack",
    risk_level: "low",
    compatibility: "compatible",
    maintainer: "Sharelife",
    review_labels: ["approved"],
    warning_flags: [],
    sections: ["memory_store", "knowledge_base"],
    summary: "Safety-first reference pack",
    search_aliases: ["官方安全包", "official-safe"],
  }

  const card = buildPublicCatalogCard(item, {
    likeCount: 12,
    liked: true,
  })
  assert.equal(card.likeCount, 12)
  assert.equal(card.liked, true)

  const search = buildPublicCatalogSearchText(item, {
    localizedTerms: [
      "官方安全参考包",
      "官方",
      "official safe reference",
    ],
  })
  assert.match(search, /官方安全参考包/)
  assert.match(search, /官方/)
  assert.match(search, /official safe reference/i)
  assert.match(search, /官方安全包/)
  assert.match(search, /official-safe/i)
})
