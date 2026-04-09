(function bootstrapMarketDetailVariant1(globalScope) {
  const shared = globalScope.SharelifeMarketDetailVariantShared || (
    typeof require === "function" ? require("./shared.js") : null
  )
  const MESSAGES = {
    "en-US": {
      "eyebrow": "Editorial evidence-first",
      "summary.fallback": "Narrative-first detail variant derived from the active V3 shell.",
      "section.public_contract": "Public contract",
      "section.review_narrative": "Review narrative",
      "section.install_sync": "Install sync sections",
      "field.pack": "Pack",
      "field.version": "Version",
      "field.pack_type": "Pack type",
      "field.maintainer": "Maintainer",
      "field.source": "Source",
      "field.package": "Package",
      "group.labels": "Labels",
      "group.flags": "Warning flags",
      "sync.note": "Install can skip stateful sections before any protected execution begins.",
      "empty.none": "No install-sync sections",
    },
    "zh-CN": {
      "eyebrow": "叙事化证据优先",
      "summary.fallback": "从当前 V3 细则层骨架派生出的叙事优先视图。",
      "section.public_contract": "公开契约",
      "section.review_narrative": "审阅叙事",
      "section.install_sync": "安装同步项",
      "field.pack": "包标识",
      "field.version": "版本",
      "field.pack_type": "包类型",
      "field.maintainer": "维护方",
      "field.source": "来源",
      "field.package": "下载包",
      "group.labels": "标签",
      "group.flags": "警示标记",
      "sync.note": "在任何受保护执行开始前，安装都可以跳过有状态的同步项。",
      "empty.none": "没有可同步项",
    },
    "ja-JP": {
      "eyebrow": "エディトリアル証拠優先",
      "summary.fallback": "現在の V3 ベースから派生した、叙述重視の detail view です。",
      "section.public_contract": "公開契約",
      "section.review_narrative": "レビュー文脈",
      "section.install_sync": "インストール同期セクション",
      "field.pack": "パック ID",
      "field.version": "バージョン",
      "field.pack_type": "パック種別",
      "field.maintainer": "メンテナー",
      "field.source": "ソース",
      "field.package": "配布パッケージ",
      "group.labels": "ラベル",
      "group.flags": "警告フラグ",
      "sync.note": "保護された実行が始まる前に、状態を持つ同期対象を install から外せます。",
      "empty.none": "同期対象はありません",
    },
  }

  function renderVariant1(context = {}) {
    const ctx = shared.createContext(context)
    const locale = shared.resolveLocale(ctx, MESSAGES)
    const summary = ctx.summary || shared.message(MESSAGES, locale, "summary.fallback")
    const reviewSignals = ctx.reviewLabels.concat(ctx.warningFlags)
    return [
      '<section class="market-detail-variant market-detail-variant-editorial market-detail-derived-surface">',
      '<div class="market-detail-derived-hero">',
      `<div class="market-detail-derived-kicker">${shared.escapeHtml(shared.message(MESSAGES, locale, "eyebrow", "Editorial evidence-first"))}</div>`,
      `<h3>${shared.escapeHtml(ctx.title)}</h3>`,
      `<p>${shared.escapeHtml(summary)}</p>`,
      '</div>',
      '<div class="market-detail-derived-grid market-detail-derived-grid-editorial">',
      '<article class="market-detail-derived-panel">',
      `<div class="market-detail-derived-panel-title">${shared.escapeHtml(shared.message(MESSAGES, locale, "section.public_contract", "Public contract"))}</div>`,
      shared.renderKeyValueRows([
        { label: shared.message(MESSAGES, locale, "field.pack", "Pack"), value: ctx.packId },
        { label: shared.message(MESSAGES, locale, "field.version", "Version"), value: ctx.version },
        { label: shared.message(MESSAGES, locale, "field.pack_type", "Pack type"), value: ctx.packType },
        { label: shared.message(MESSAGES, locale, "field.maintainer", "Maintainer"), value: ctx.maintainer },
      ]),
      '</article>',
      '<article class="market-detail-derived-panel">',
      `<div class="market-detail-derived-panel-title">${shared.escapeHtml(shared.message(MESSAGES, locale, "section.review_narrative", "Review narrative"))}</div>`,
      '<div class="market-detail-derived-copy-block">',
      `<span class="market-detail-derived-copy-label">${shared.escapeHtml(shared.message(MESSAGES, locale, "group.labels", "Labels"))}</span>`,
      `<div class="market-detail-derived-pill-row">${shared.renderPillRow(ctx.reviewLabels, shared.message(MESSAGES, locale, "empty.none", "None declared"))}</div>`,
      `<span class="market-detail-derived-copy-label">${shared.escapeHtml(shared.message(MESSAGES, locale, "group.flags", "Warning flags"))}</span>`,
      `<div class="market-detail-derived-pill-row">${shared.renderPillRow(reviewSignals, shared.message(MESSAGES, locale, "empty.none", "None declared"))}</div>`,
      '</div>',
      shared.renderKeyValueRows([
        { label: shared.message(MESSAGES, locale, "field.source", "Source"), value: ctx.sourceSubmissionId },
        { label: shared.message(MESSAGES, locale, "field.package", "Package"), value: ctx.packagePath },
      ]),
      '</article>',
      '<article class="market-detail-derived-panel">',
      `<div class="market-detail-derived-panel-title">${shared.escapeHtml(shared.message(MESSAGES, locale, "section.install_sync", "Install sync sections"))}</div>`,
      `<p class="market-detail-derived-note">${shared.escapeHtml(shared.message(MESSAGES, locale, "sync.note", "Install can skip stateful sections before any protected execution begins."))}</p>`,
      shared.renderList(ctx.sections, shared.message(MESSAGES, locale, "empty.none", "No install-sync sections")),
      '</article>',
      '</div>',
      '</section>',
    ].join("")
  }

  if (typeof module !== "undefined" && module.exports) {
    module.exports = { renderVariant1 }
  }
  if (globalScope.SharelifeMarketDetailVariantRegistry) {
    globalScope.SharelifeMarketDetailVariantRegistry.registerVariantRenderer("variant_1", renderVariant1)
  }
  globalScope.SharelifeMarketDetailVariant1 = renderVariant1
})(typeof globalThis !== "undefined" ? globalThis : this)
