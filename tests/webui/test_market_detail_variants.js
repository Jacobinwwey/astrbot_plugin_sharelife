const test = require("node:test")
const assert = require("node:assert/strict")

const {
  DEFAULT_VARIANTS,
  normalizeVariantId,
  getVariantRenderer,
} = require("../../sharelife/webui/market_detail/variant_registry.js")

function detailContext(overrides = {}) {
  return {
    packId: "profile/<unsafe>",
    title: "Autonomous <Shield>",
    version: "2.4.0",
    packType: "bot_profile_pack",
    compatibility: "v2.0 core",
    riskLevel: "low_moderate",
    maintainer: "Sovereign Archive",
    reviewLabels: ["verified", "approved"],
    warningFlags: ["network_sync_required"],
    sections: ["persona", "tools", "memory_store", "conversation_history", "knowledge_base"],
    summary: "Public-first detail shell for autonomous node operations.",
    featured: true,
    sourceSubmissionId: "official:profile/autonomous-shield",
    packagePath: "packs/autonomous-shield.zip",
    locale: "en-US",
    ...overrides,
  }
}

function loadVariantRenderer(variantId) {
  require(`../../sharelife/webui/market_detail/variants/${variantId}.js`)
  return getVariantRenderer(variantId)
}

test("variant registry keeps five stable ids and normalizes invalid input", () => {
  assert.deepEqual(DEFAULT_VARIANTS, ["variant_1", "variant_2", "variant_3", "variant_4", "variant_5"])
  assert.equal(normalizeVariantId("variant_3"), "variant_3")
  assert.equal(normalizeVariantId("missing"), "variant_1")
})

test("detail variant modules expose direct renderer exports for node:test", () => {
  const variant1 = require("../../sharelife/webui/market_detail/variants/variant_1.js")
  const variant2 = require("../../sharelife/webui/market_detail/variants/variant_2.js")
  const variant3 = require("../../sharelife/webui/market_detail/variants/variant_3.js")
  const variant4 = require("../../sharelife/webui/market_detail/variants/variant_4.js")
  const variant5 = require("../../sharelife/webui/market_detail/variants/variant_5.js")

  assert.equal(typeof variant1.renderVariant1, "function")
  assert.equal(typeof variant2.renderVariant2, "function")
  assert.equal(typeof variant3.renderVariant3, "function")
  assert.equal(typeof variant4.renderVariant4, "function")
  assert.equal(typeof variant5.renderVariant5, "function")
})

test("every default variant has a renderer", () => {
  DEFAULT_VARIANTS.forEach((variantId) => {
    assert.equal(typeof getVariantRenderer(variantId), "function")
  })
})

test("variant 3 renders a split facts-versus-actions shell with escaped pack content", () => {
  require("../../sharelife/webui/market_detail/variants/variant_3.js")

  const renderVariant3 = getVariantRenderer("variant_3")
  const html = renderVariant3({
    packId: "profile/<unsafe>",
    title: "Autonomous <Shield>",
    version: "2.4.0",
    packType: "bot_profile_pack",
    compatibility: "v2.0 core",
    riskLevel: "low_moderate",
    maintainer: "Sovereign Archive",
    reviewLabels: ["verified", "approved"],
    warningFlags: ["network_sync_required"],
    sections: ["persona", "tools", "memory"],
    summary: "Public-first detail shell for autonomous node operations.",
    featured: true,
    sourceSubmissionId: "official:profile/autonomous-shield",
    packagePath: "packs/autonomous-shield.zip",
  })

  assert.match(html, /Public facts/i)
  assert.match(html, /Action readiness/i)
  assert.match(html, /market-detail-v3-grid/)
  assert.match(html, /market-detail-v3-actions/)
  assert.match(html, /market-detail-v3-contract-block/)
  assert.match(html, /data-market-detail-slot="install_sections"/)
  assert.match(html, /data-market-detail-slot="install_options"/)
  assert.match(html, /Public contract/i)
  assert.match(html, /Install Sync Sections/i)
  assert.match(html, /id="btnMarketDetailTrial"/)
  assert.match(html, /id="btnMarketDetailInstall"/)
  assert.match(html, /id="btnMarketCatalogCompare"/)
  assert.match(html, /id="btnMarketCatalogDownload"/)
  assert.match(html, /official:profile\/autonomous-shield/)
  assert.match(html, /packs\/autonomous-shield\.zip/)
  assert.match(html, /Autonomous &lt;Shield&gt;/)
  assert.doesNotMatch(html, /Autonomous <Shield>/)
  assert.doesNotMatch(html, /Upload/i)
  assert.doesNotMatch(html, /Execution flow/i)
  assert.doesNotMatch(html, /Open Stitch HTML/i)
  assert.doesNotMatch(html, /Open Screenshot/i)
  assert.doesNotMatch(html, /Variant 3/i)
  assert.doesNotMatch(html, /data-market-detail-slot="primary_actions"/)
})

test("variant 3 localizes shell copy for ja-JP", () => {
  require("../../sharelife/webui/market_detail/variants/variant_3.js")

  const renderVariant3 = getVariantRenderer("variant_3")
  const html = renderVariant3({
    packId: "profile-safe",
    title: "Autonomous Shield",
    version: "2.4.0",
    packType: "bot_profile_pack",
    compatibility: "v2.0 core",
    riskLevel: "low_moderate",
    maintainer: "Sovereign Archive",
    reviewLabels: ["verified"],
    warningFlags: [],
    sections: ["memory_store"],
    locale: "ja-JP",
  })

  assert.match(html, /公開情報/)
  assert.match(html, /実行準備/)
  assert.match(html, /インストール同期セクション/)
  assert.match(html, /data-market-detail-slot="install_sections"/)
  assert.match(html, /id="btnMarketDetailInstall"/)
  assert.doesNotMatch(html, /スクリーンショットを開く/)
})

test("variant 1 stays anchored to the V3 public-facts baseline", () => {
  const renderVariant1 = loadVariantRenderer("variant_1")
  const html = renderVariant1(detailContext())

  assert.match(html, /Editorial evidence-first/i)
  assert.match(html, /Public contract/i)
  assert.match(html, /Install sync sections/i)
  assert.match(html, /memory_store/)
  assert.match(html, /persona/)
  assert.match(html, /official:profile\/autonomous-shield/)
  assert.match(html, /Autonomous &lt;Shield&gt;/)
  assert.doesNotMatch(html, /Autonomous <Shield>/)
  assert.doesNotMatch(html, /Variant 1/i)
  assert.doesNotMatch(html, /Open Stitch HTML/i)
})

test("variant 2 renders an operator view without losing selective sync context", () => {
  const renderVariant2 = loadVariantRenderer("variant_2")
  const html = renderVariant2(detailContext())

  assert.match(html, /Operator matrix/i)
  assert.match(html, /Action readiness/i)
  assert.match(html, /conversation_history/)
  assert.match(html, /knowledge_base/)
  assert.match(html, /Compare/)
  assert.match(html, /packs\/autonomous-shield\.zip/)
  assert.match(html, /verified/i)
  assert.doesNotMatch(html, /Upload/i)
  assert.doesNotMatch(html, /Open Screenshot/i)
})

test("variant 4 foregrounds trust posture while preserving pack detail context", () => {
  const renderVariant4 = loadVariantRenderer("variant_4")
  const html = renderVariant4(detailContext())

  assert.match(html, /Trust posture/i)
  assert.match(html, /Compatibility/i)
  assert.match(html, /network_sync_required/)
  assert.match(html, /knowledge_base/)
  assert.match(html, /Sovereign Archive/)
  assert.doesNotMatch(html, /Variant 4/i)
  assert.doesNotMatch(html, /Open Stitch HTML/i)
})

test("variant 5 localizes the compact action-boundary view for zh-CN", () => {
  const renderVariant5 = loadVariantRenderer("variant_5")
  const html = renderVariant5(detailContext({ locale: "zh-CN" }))

  assert.match(html, /动作边界/)
  assert.match(html, /安装同步项/)
  assert.match(html, /knowledge_base/)
  assert.doesNotMatch(html, /打开截图/)
  assert.doesNotMatch(html, /执行清单/)
})
