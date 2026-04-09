(function bootstrapMarketDetailVariant2(globalScope) {
  const shared = globalScope.SharelifeMarketDetailVariantShared || (
    typeof require === "function" ? require("./shared.js") : null
  )
  const MESSAGES = {
    "en-US": {
      "eyebrow": "Operator console derivative",
      "summary.fallback": "Matrix-oriented detail variant that keeps the current pack context intact.",
      "section.operator_matrix": "Operator matrix",
      "section.action_readiness": "Action readiness",
      "section.sync_scope": "Install sync sections",
      "field.compatibility": "Compatibility",
      "field.risk": "Risk",
      "field.source": "Source",
      "field.package": "Package",
      "field.labels": "Labels",
      "action.try": "Try stays public-first until execution starts.",
      "action.install": "Install inherits section-selective sync before it crosses the protected boundary.",
      "action.compare": "Runtime comparison stays available from the public action rail.",
      "action.download": "Download remains public when the package path is exposed.",
      "empty.none": "None declared",
    },
    "zh-CN": {
      "eyebrow": "运维控制台派生版",
      "summary.fallback": "以矩阵视角展示当前配置包，切换时不会丢失上下文。",
      "section.operator_matrix": "操作矩阵",
      "section.action_readiness": "动作就绪",
      "section.sync_scope": "安装同步项",
      "field.compatibility": "兼容性",
      "field.risk": "风险",
      "field.source": "来源",
      "field.package": "包路径",
      "field.labels": "标签",
      "action.try": "试用在真正执行前仍保持公开优先。",
      "action.install": "安装沿用配置项级的可选同步，并在跨越保护边界前确认。",
      "action.compare": "运行时对比仍通过公开操作栏触发。",
      "action.download": "当包路径已公开时，下载仍保持公开可见。",
      "empty.none": "没有可同步项",
    },
    "ja-JP": {
      "eyebrow": "オペレーターコンソール派生",
      "summary.fallback": "同じパック文脈を保ったまま、マトリクス視点で表示する detail view です。",
      "section.operator_matrix": "運用マトリクス",
      "section.action_readiness": "実行準備",
      "section.sync_scope": "インストール同期セクション",
      "field.compatibility": "互換性",
      "field.risk": "リスク",
      "field.source": "ソース",
      "field.package": "配布パッケージ",
      "field.labels": "ラベル",
      "action.try": "試用は実行開始まで公開優先のままです。",
      "action.install": "install は保護境界を越える前にセクション単位の同期選択を維持します。",
      "action.compare": "runtime 比較は公開アクションレールから継続して使えます。",
      "action.download": "package path が公開されている場合は download も公開のままです。",
      "empty.none": "同期対象はありません",
    },
  }

  function renderVariant2(context = {}) {
    const ctx = shared.createContext(context)
    const locale = shared.resolveLocale(ctx, MESSAGES)
    const summary = ctx.summary || shared.message(MESSAGES, locale, "summary.fallback")
    return [
      '<section class="market-detail-variant market-detail-variant-console market-detail-derived-surface">',
      '<div class="market-detail-derived-hero market-detail-derived-hero-tight">',
      `<div class="market-detail-derived-kicker">${shared.escapeHtml(shared.message(MESSAGES, locale, "eyebrow", "Operator console derivative"))}</div>`,
      `<h3>${shared.escapeHtml(ctx.title)}</h3>`,
      `<p>${shared.escapeHtml(summary)}</p>`,
      '</div>',
      '<div class="market-detail-derived-grid market-detail-derived-grid-console">',
      '<article class="market-detail-derived-panel">',
      `<div class="market-detail-derived-panel-title">${shared.escapeHtml(shared.message(MESSAGES, locale, "section.operator_matrix", "Operator matrix"))}</div>`,
      shared.renderKeyValueRows([
        { label: shared.message(MESSAGES, locale, "field.compatibility", "Compatibility"), value: ctx.compatibility },
        { label: shared.message(MESSAGES, locale, "field.risk", "Risk"), value: ctx.riskLevel },
        { label: shared.message(MESSAGES, locale, "field.source", "Source"), value: ctx.sourceSubmissionId },
        { label: shared.message(MESSAGES, locale, "field.package", "Package"), value: ctx.packagePath },
      ]),
      '</article>',
      '<article class="market-detail-derived-panel">',
      `<div class="market-detail-derived-panel-title">${shared.escapeHtml(shared.message(MESSAGES, locale, "section.action_readiness", "Action readiness"))}</div>`,
      '<ul class="market-detail-derived-checklist">',
      `<li><strong>Try</strong><span>${shared.escapeHtml(shared.message(MESSAGES, locale, "action.try", "Try stays public-first until execution starts."))}</span></li>`,
      `<li><strong>Install</strong><span>${shared.escapeHtml(shared.message(MESSAGES, locale, "action.install", "Install inherits section-selective sync before it crosses the protected boundary."))}</span></li>`,
      `<li><strong>Compare</strong><span>${shared.escapeHtml(shared.message(MESSAGES, locale, "action.compare", "Runtime comparison stays available from the public action rail."))}</span></li>`,
      `<li><strong>Download</strong><span>${shared.escapeHtml(shared.message(MESSAGES, locale, "action.download", "Download remains public when the package path is exposed."))}</span></li>`,
      '</ul>',
      '</article>',
      '<article class="market-detail-derived-panel">',
      `<div class="market-detail-derived-panel-title">${shared.escapeHtml(shared.message(MESSAGES, locale, "section.sync_scope", "Install sync sections"))}</div>`,
      shared.renderList(ctx.sections, shared.message(MESSAGES, locale, "empty.none", "None declared")),
      `<div class="market-detail-derived-copy-label">${shared.escapeHtml(shared.message(MESSAGES, locale, "field.labels", "Labels"))}</div>`,
      `<div class="market-detail-derived-pill-row">${shared.renderPillRow(ctx.reviewLabels, shared.message(MESSAGES, locale, "empty.none", "None declared"))}</div>`,
      '</article>',
      '</div>',
      '</section>',
    ].join("")
  }

  if (typeof module !== "undefined" && module.exports) {
    module.exports = { renderVariant2 }
  }
  if (globalScope.SharelifeMarketDetailVariantRegistry) {
    globalScope.SharelifeMarketDetailVariantRegistry.registerVariantRenderer("variant_2", renderVariant2)
  }
  globalScope.SharelifeMarketDetailVariant2 = renderVariant2
})(typeof globalThis !== "undefined" ? globalThis : this)
