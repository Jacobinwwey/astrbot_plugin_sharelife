(function bootstrapMarketDetailVariantRegistry(globalScope) {
  const DEFAULT_VARIANTS = ["variant_1", "variant_2", "variant_3", "variant_4", "variant_5"]
  const renderers = new Map()

  function normalizeVariantId(value) {
    const text = String(value || "").trim()
    return DEFAULT_VARIANTS.includes(text) ? text : DEFAULT_VARIANTS[0]
  }

  function placeholderRendererFactory(variantId) {
    return function renderPlaceholder(context = {}) {
      const title = String(context.title || context.packId || "Selected Pack")
      return [
        `<section class="market-detail-variant market-detail-variant-${variantId}">`,
        `<div class="market-detail-variant-label">${variantId.replace("_", " ").toUpperCase()}</div>`,
        `<h3>${title}</h3>`,
        `<p>${String(context.summary || "Detail variant placeholder until Stitch output is integrated.")}</p>`,
        "</section>",
      ].join("")
    }
  }

  function registerVariantRenderer(variantId, renderer) {
    const normalized = normalizeVariantId(variantId)
    if (typeof renderer !== "function") return
    renderers.set(normalized, renderer)
  }

  function getVariantRenderer(variantId) {
    const normalized = normalizeVariantId(variantId)
    return renderers.get(normalized) || placeholderRendererFactory(normalized)
  }

  DEFAULT_VARIANTS.forEach((variantId) => {
    renderers.set(variantId, placeholderRendererFactory(variantId))
  })

  const api = {
    DEFAULT_VARIANTS,
    normalizeVariantId,
    registerVariantRenderer,
    getVariantRenderer,
  }

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api
  }
  globalScope.SharelifeMarketDetailVariantRegistry = api
})(typeof globalThis !== "undefined" ? globalThis : this)
