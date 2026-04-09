(function bootstrapMarketDetailVariant5(globalScope) {
  const shared = globalScope.SharelifeMarketDetailVariantShared || (
    typeof require === "function" ? require("./shared.js") : null
  )
  const MESSAGES = {
    "en-US": {
      "eyebrow": "Boundary and install focus",
      "summary.fallback": "A compact detail view that keeps action boundaries and install sync visible without duplicating the user panel.",
      "section.boundary": "Action boundary",
      "section.sync": "Install sync sections",
      "note.public_first": "Public facts stay readable before login.",
      "note.auth": "Auth only starts when a protected member action actually runs.",
      "note.install": "Install keeps section-selective sync before execution.",
      "empty.none": "No install-sync sections",
    },
    "zh-CN": {
      "eyebrow": "动作边界与安装优先",
      "summary.fallback": "以紧凑方式保留动作边界和安装同步，不再重复用户面板已有能力。",
      "section.boundary": "动作边界",
      "section.sync": "安装同步项",
      "note.public_first": "登录前仍可阅读公开事实。",
      "note.auth": "只有真正运行受保护的成员动作时才触发鉴权。",
      "note.install": "安装在执行前仍保留按配置项选择同步范围。",
      "empty.none": "没有可同步项",
    },
    "ja-JP": {
      "eyebrow": "境界とインストールを優先",
      "summary.fallback": "ユーザーパネルと重複させずに、アクション境界と install sync を簡潔に示す detail view です。",
      "section.boundary": "アクション境界",
      "section.sync": "インストール同期セクション",
      "note.public_first": "login 前でも公開ファクトは読めます。",
      "note.auth": "保護された member action が実際に動く時だけ認証します。",
      "note.install": "install は実行前にセクション単位の同期選択を維持します。",
      "empty.none": "同期対象はありません",
    },
  }

  function renderVariant5(context = {}) {
    const ctx = shared.createContext(context)
    const locale = shared.resolveLocale(ctx, MESSAGES)
    const summary = ctx.summary || shared.message(MESSAGES, locale, "summary.fallback")
    return [
      '<section class="market-detail-variant market-detail-variant-checklist market-detail-derived-surface market-detail-derived-surface-checklist">',
      '<div class="market-detail-derived-hero">',
      `<div class="market-detail-derived-kicker">${shared.escapeHtml(shared.message(MESSAGES, locale, "eyebrow", "Boundary and install focus"))}</div>`,
      `<h3>${shared.escapeHtml(ctx.title)}</h3>`,
      `<p>${shared.escapeHtml(summary)}</p>`,
      '</div>',
      '<div class="market-detail-derived-grid market-detail-derived-grid-checklist">',
      '<article class="market-detail-derived-panel">',
      `<div class="market-detail-derived-panel-title">${shared.escapeHtml(shared.message(MESSAGES, locale, "section.boundary", "Action boundary"))}</div>`,
      '<ul class="market-detail-derived-checklist">',
      `<li><strong>01</strong><span>${shared.escapeHtml(shared.message(MESSAGES, locale, "note.public_first", "Public facts stay readable before login."))}</span></li>`,
      `<li><strong>02</strong><span>${shared.escapeHtml(shared.message(MESSAGES, locale, "note.auth", "Auth only starts when a protected member action actually runs."))}</span></li>`,
      `<li><strong>03</strong><span>${shared.escapeHtml(shared.message(MESSAGES, locale, "note.install", "Install keeps section-selective sync before execution."))}</span></li>`,
      '</ul>',
      '</article>',
      '<article class="market-detail-derived-panel">',
      `<div class="market-detail-derived-panel-title">${shared.escapeHtml(shared.message(MESSAGES, locale, "section.sync", "Install sync sections"))}</div>`,
      shared.renderList(ctx.sections, shared.message(MESSAGES, locale, "empty.none", "No install-sync sections")),
      '</article>',
      '</div>',
      '</section>',
    ].join("")
  }

  if (typeof module !== "undefined" && module.exports) {
    module.exports = { renderVariant5 }
  }
  if (globalScope.SharelifeMarketDetailVariantRegistry) {
    globalScope.SharelifeMarketDetailVariantRegistry.registerVariantRenderer("variant_5", renderVariant5)
  }
  globalScope.SharelifeMarketDetailVariant5 = renderVariant5
})(typeof globalThis !== "undefined" ? globalThis : this)
