(function bootstrapMarketDetailVariant4(globalScope) {
  const shared = globalScope.SharelifeMarketDetailVariantShared || (
    typeof require === "function" ? require("./shared.js") : null
  )
  const MESSAGES = {
    "en-US": {
      "eyebrow": "Trust and compatibility first",
      "summary.fallback": "A trust-posture readout anchored to the same public-first detail context.",
      "section.trust_posture": "Trust posture",
      "section.sync_ready": "Install sync sections",
      "field.compatibility": "Compatibility",
      "field.risk": "Risk",
      "field.maintainer": "Maintainer",
      "field.flags": "Warning flags",
      "empty.none": "No install-sync sections",
    },
    "zh-CN": {
      "eyebrow": "信任与兼容性优先",
      "summary.fallback": "以信任姿态为主的视图，但仍绑定同一份公开优先细则上下文。",
      "section.trust_posture": "信任姿态",
      "section.sync_ready": "安装同步项",
      "field.compatibility": "兼容性",
      "field.risk": "风险",
      "field.maintainer": "维护方",
      "field.flags": "警示标记",
      "empty.none": "没有可同步项",
    },
    "ja-JP": {
      "eyebrow": "信頼と互換性を先頭へ",
      "summary.fallback": "同じ公開優先の detail 文脈に anchored した trust-posture view です。",
      "section.trust_posture": "信頼姿勢",
      "section.sync_ready": "インストール同期セクション",
      "field.compatibility": "互換性",
      "field.risk": "リスク",
      "field.maintainer": "メンテナー",
      "field.flags": "警告フラグ",
      "empty.none": "同期対象はありません",
    },
  }

  function renderVariant4(context = {}) {
    const ctx = shared.createContext(context)
    const locale = shared.resolveLocale(ctx, MESSAGES)
    const summary = ctx.summary || shared.message(MESSAGES, locale, "summary.fallback")
    return [
      '<section class="market-detail-variant market-detail-variant-metrics market-detail-derived-surface market-detail-derived-surface-trust">',
      '<div class="market-detail-derived-hero">',
      `<div class="market-detail-derived-kicker">${shared.escapeHtml(shared.message(MESSAGES, locale, "eyebrow", "Trust and compatibility first"))}</div>`,
      `<h3>${shared.escapeHtml(ctx.title)}</h3>`,
      `<p>${shared.escapeHtml(summary)}</p>`,
      '</div>',
      '<div class="market-detail-derived-grid market-detail-derived-grid-trust">',
      '<article class="market-detail-derived-panel">',
      `<div class="market-detail-derived-panel-title">${shared.escapeHtml(shared.message(MESSAGES, locale, "section.trust_posture", "Trust posture"))}</div>`,
      shared.renderKeyValueRows([
        { label: shared.message(MESSAGES, locale, "field.compatibility", "Compatibility"), value: ctx.compatibility },
        { label: shared.message(MESSAGES, locale, "field.risk", "Risk"), value: ctx.riskLevel },
        { label: shared.message(MESSAGES, locale, "field.maintainer", "Maintainer"), value: ctx.maintainer },
      ]),
      `<div class="market-detail-derived-copy-label">${shared.escapeHtml(shared.message(MESSAGES, locale, "field.flags", "Warning flags"))}</div>`,
      `<div class="market-detail-derived-pill-row">${shared.renderPillRow(ctx.warningFlags, shared.message(MESSAGES, locale, "empty.none", "None declared"))}</div>`,
      '</article>',
      '<article class="market-detail-derived-panel">',
      `<div class="market-detail-derived-panel-title">${shared.escapeHtml(shared.message(MESSAGES, locale, "section.sync_ready", "Install sync sections"))}</div>`,
      shared.renderList(ctx.sections, shared.message(MESSAGES, locale, "empty.none", "No install-sync sections")),
      '</article>',
      '</div>',
      '</section>',
    ].join("")
  }

  if (typeof module !== "undefined" && module.exports) {
    module.exports = { renderVariant4 }
  }
  if (globalScope.SharelifeMarketDetailVariantRegistry) {
    globalScope.SharelifeMarketDetailVariantRegistry.registerVariantRenderer("variant_4", renderVariant4)
  }
  globalScope.SharelifeMarketDetailVariant4 = renderVariant4
})(typeof globalThis !== "undefined" ? globalThis : this)
