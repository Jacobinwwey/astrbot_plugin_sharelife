(function bootstrapMarketDetailVariant3(globalScope) {
  const DEFAULT_LOCALE = "en-US"
  const MESSAGES = {
    "en-US": {
      "chip.featured": "Featured",
      "summary.fallback": "Focused detail shell derived from the current market center.",
      "section.public_facts": "Public facts",
      "section.public_contract": "Public contract",
      "section.review_signal_set": "Review signal set",
      "section.install_sections": "Install Sync Sections",
      "section.action_readiness": "Action readiness",
      "group.labels": "Labels",
      "group.warning_flags": "Warning flags",
      "definition.version": "Version",
      "definition.maintainer": "Maintainer",
      "definition.pack_type": "Pack type",
      "definition.source": "Source",
      "definition.risk_level": "Risk level",
      "definition.compatibility": "Compatibility",
      "definition.sections": "Sections",
      "empty.no_sections": "No install-sync sections",
      "empty.no_review_labels": "No review labels",
      "empty.no_warning_flags": "No warning flags",
      "action.try.name": "Try",
      "action.try.note": "Public facts first, auth only when execution starts.",
      "action.install.name": "Install",
      "action.install.note_with_package": "Bundle exposed at {path}. Install can limit sync to chosen sections before execution.",
      "action.install.note_without_package": "Install after choosing sync sections and install source below.",
      "action.compare.name": "Compare",
      "action.compare.note": "Run a runtime diff from this panel when local runtime data is available.",
      "action.download.name": "Download",
      "action.download.note_with_package": "Open the public package path directly from this panel.",
      "action.download.note_without_package": "No public package path is available for this row yet.",
      "install.note": "Choose which sections should sync during install. Stateful local data can be skipped.",
    },
    "zh-CN": {
      "chip.featured": "推荐",
      "summary.fallback": "从当前市场中心派生出的精简细则层。",
      "section.public_facts": "公开信息",
      "section.public_contract": "公开契约",
      "section.review_signal_set": "审阅信号",
      "section.install_sections": "安装同步项",
      "section.action_readiness": "动作就绪",
      "group.labels": "标签",
      "group.warning_flags": "警示标记",
      "definition.version": "版本",
      "definition.maintainer": "维护方",
      "definition.pack_type": "包类型",
      "definition.source": "来源",
      "definition.risk_level": "风险级别",
      "definition.compatibility": "兼容性",
      "definition.sections": "同步项数量",
      "empty.no_sections": "暂无可同步项",
      "empty.no_review_labels": "暂无标签",
      "empty.no_warning_flags": "暂无警示",
      "action.try.name": "试用",
      "action.try.note": "先阅读公开事实，真正执行时再触发鉴权。",
      "action.install.name": "安装",
      "action.install.note_with_package": "已暴露下载包路径 {path}。执行安装前可限制同步项。",
      "action.install.note_without_package": "先在下方选择同步项与安装来源，再执行安装。",
      "action.compare.name": "对比",
      "action.compare.note": "当本地运行态可用时，可直接在此处发起运行时对比。",
      "action.download.name": "下载",
      "action.download.note_with_package": "可直接从此面板打开公开下载路径。",
      "action.download.note_without_package": "当前条目尚未暴露公开下载路径。",
      "install.note": "选择安装时需要同步的配置项。有状态或本地数据项可以跳过不同步。",
    },
    "ja-JP": {
      "chip.featured": "注目",
      "summary.fallback": "現在の market center から派生した簡潔な detail shell です。",
      "section.public_facts": "公開情報",
      "section.public_contract": "公開契約",
      "section.review_signal_set": "レビューシグナル",
      "section.install_sections": "インストール同期セクション",
      "section.action_readiness": "実行準備",
      "group.labels": "ラベル",
      "group.warning_flags": "警告フラグ",
      "definition.version": "バージョン",
      "definition.maintainer": "メンテナー",
      "definition.pack_type": "パック種別",
      "definition.source": "ソース",
      "definition.risk_level": "リスクレベル",
      "definition.compatibility": "互換性",
      "definition.sections": "セクション数",
      "empty.no_sections": "同期対象はありません",
      "empty.no_review_labels": "レビューラベルはありません",
      "empty.no_warning_flags": "警告フラグはありません",
      "action.try.name": "試用",
      "action.try.note": "まず公開ファクトを確認し、実行開始時にだけ認証を要求します。",
      "action.install.name": "インストール",
      "action.install.note_with_package": "配布パッケージは {path} に公開されています。実行前に同期セクションを絞り込めます。",
      "action.install.note_without_package": "下の同期セクションと install source を選んでから実行します。",
      "action.compare.name": "比較",
      "action.compare.note": "local runtime が利用可能なときは、このパネルから比較を開始できます。",
      "action.download.name": "ダウンロード",
      "action.download.note_with_package": "このパネルから公開ダウンロード経路を直接開けます。",
      "action.download.note_without_package": "この行にはまだ公開ダウンロード経路がありません。",
      "install.note": "install 時に同期する設定項目を選びます。stateful / local-data 系の項目は同期しない選択もできます。",
    },
  }

  function i18nHelpers() {
    return globalScope.SharelifeWebuiI18n || null
  }

  function resolveLocale(context = {}) {
    const helper = i18nHelpers()
    const contextLocale = String(context.locale || "").trim()
    const documentLocale = typeof document !== "undefined" && document.documentElement
      ? String(document.documentElement.getAttribute("lang") || "").trim()
      : ""
    const rawLocale = contextLocale || documentLocale || DEFAULT_LOCALE
    if (helper && typeof helper.normalizeLocale === "function") {
      return helper.normalizeLocale(rawLocale)
    }
    return MESSAGES[rawLocale] ? rawLocale : DEFAULT_LOCALE
  }

  function message(locale, key, fallback = "") {
    const bundle = MESSAGES[locale] || MESSAGES[DEFAULT_LOCALE]
    if (Object.prototype.hasOwnProperty.call(bundle, key)) {
      return bundle[key]
    }
    return fallback || MESSAGES[DEFAULT_LOCALE][key] || key
  }

  function format(locale, key, tokens = {}, fallback = "") {
    const template = message(locale, key, fallback)
    return String(template).replace(/\{([a-zA-Z0-9_]+)\}/g, (match, token) => {
      if (!Object.prototype.hasOwnProperty.call(tokens, token)) {
        return match
      }
      return String(tokens[token] ?? "")
    })
  }

  function escapeHtml(value) {
    return String(value || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;")
  }

  function renderInlinePills(items, emptyLabel) {
    const rows = Array.isArray(items) ? items.filter(Boolean) : []
    if (!rows.length) {
      return `<span class="market-detail-v3-empty">${escapeHtml(emptyLabel)}</span>`
    }
    return rows
      .map((item) => `<span class="market-detail-v3-pill">${escapeHtml(item)}</span>`)
      .join("")
  }

  function renderSectionList(items, emptyLabel) {
    const rows = Array.isArray(items) ? items.filter(Boolean) : []
    if (!rows.length) {
      return `<div class="market-detail-v3-empty">${escapeHtml(emptyLabel)}</div>`
    }
    return [
      '<ul class="market-detail-v3-sections">',
      ...rows.map((item) => `<li>${escapeHtml(item)}</li>`),
      "</ul>",
    ].join("")
  }

  function renderDefinitionRow(label, value) {
    return [
      '<div class="market-detail-v3-definition-row">',
      `<span class="market-detail-v3-definition-label">${escapeHtml(label)}</span>`,
      `<strong>${escapeHtml(value)}</strong>`,
      "</div>",
    ].join("")
  }

  function renderActionButton(item) {
    const classes = ["market-detail-v3-action-button"]
    if (item.tone === "primary") {
      classes.push("is-primary")
    }
    return [
      `<button id="${escapeHtml(item.id)}" class="${escapeHtml(classes.join(" "))}" type="button">`,
      `<span class="market-detail-v3-action-name">${escapeHtml(item.name)}</span>`,
      `<span class="market-detail-v3-action-note">${escapeHtml(item.note)}</span>`,
      "</button>",
    ].join("")
  }

  function renderContractLine(label, value) {
    return `<div><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`
  }

  function renderVariant3(context = {}) {
    const locale = resolveLocale(context)
    const title = String(context.title || context.packId || "Selected Pack")
    const summary = String(context.summary || message(locale, "summary.fallback"))
    const sections = Array.isArray(context.sections) ? context.sections : []
    const reviewLabels = Array.isArray(context.reviewLabels) ? context.reviewLabels : []
    const warningFlags = Array.isArray(context.warningFlags) ? context.warningFlags : []
    const packagePath = String(context.packagePath || "").trim()
    const sourceSubmissionId = String(context.sourceSubmissionId || "official").trim()
    const identityRows = [
      { label: message(locale, "definition.version"), value: String(context.version || "-") },
      { label: message(locale, "definition.maintainer"), value: String(context.maintainer || "unknown") },
      { label: message(locale, "definition.pack_type"), value: String(context.packType || "bot_profile_pack") },
      { label: message(locale, "definition.source"), value: sourceSubmissionId || "-" },
    ]
    const actionRows = [
      {
        id: "btnMarketDetailTrial",
        name: message(locale, "action.try.name"),
        note: message(locale, "action.try.note"),
      },
      {
        id: "btnMarketDetailInstall",
        tone: "primary",
        name: message(locale, "action.install.name"),
        note: packagePath
          ? format(locale, "action.install.note_with_package", { path: packagePath })
          : message(locale, "action.install.note_without_package"),
      },
      {
        id: "btnMarketCatalogCompare",
        name: message(locale, "action.compare.name"),
        note: message(locale, "action.compare.note"),
      },
      {
        id: "btnMarketCatalogDownload",
        name: message(locale, "action.download.name"),
        note: packagePath
          ? message(locale, "action.download.note_with_package")
          : message(locale, "action.download.note_without_package"),
      },
    ]
    const contractLines = [
      { label: "[pack_id]", value: String(context.packId || "-") },
      { label: "[version]", value: String(context.version || "-") },
      { label: "[compatibility]", value: String(context.compatibility || "unknown") },
      { label: "[risk_level]", value: String(context.riskLevel || "unknown") },
      { label: "[source]", value: sourceSubmissionId || "-" },
      { label: "[package]", value: packagePath || "generated_or_uploaded" },
    ]

    return `
      <section class="market-detail-variant market-detail-variant-split market-detail-variant-v3">
        <div class="market-detail-v3-pack-chip-row">
          <span class="market-detail-v3-pack-chip">${escapeHtml(context.packId || "-")}</span>
          ${context.featured ? `<span class="market-detail-v3-pack-chip is-accent">${escapeHtml(message(locale, "chip.featured"))}</span>` : ""}
        </div>
        <div class="market-detail-v3-header">
          <div>
            <h3>${escapeHtml(title)}</h3>
          </div>
          <p class="market-detail-v3-summary">${escapeHtml(summary)}</p>
        </div>
        <div class="market-detail-v3-grid">
          <div class="market-detail-v3-main">
            <section class="market-detail-v3-panel">
              <div class="market-detail-v3-section-label">${escapeHtml(message(locale, "section.public_facts"))}</div>
              <div class="market-detail-v3-identity-grid">
                ${identityRows.map((row) => renderDefinitionRow(row.label, row.value)).join("")}
              </div>
              <div class="market-detail-v3-signal-strip">
                ${renderDefinitionRow(message(locale, "definition.risk_level"), String(context.riskLevel || "unknown"))}
                ${renderDefinitionRow(message(locale, "definition.compatibility"), String(context.compatibility || "unknown"))}
                ${renderDefinitionRow(message(locale, "definition.sections"), String(sections.length))}
              </div>
            </section>
            <section class="market-detail-v3-panel">
              <div class="market-detail-v3-section-label">${escapeHtml(message(locale, "section.public_contract"))}</div>
              <div class="market-detail-v3-contract-block">
                ${contractLines.map((line) => renderContractLine(line.label, line.value)).join("")}
              </div>
            </section>
            <section class="market-detail-v3-panel">
              <div class="market-detail-v3-section-label">${escapeHtml(message(locale, "section.install_sections"))}</div>
              <div class="market-detail-v3-slot" data-market-detail-slot="install_sections">
                <p class="market-detail-v3-action-note">${escapeHtml(message(locale, "install.note"))}</p>
                ${renderSectionList(sections, message(locale, "empty.no_sections"))}
              </div>
            </section>
            <section class="market-detail-v3-panel">
              <div class="market-detail-v3-slot" data-market-detail-slot="install_options"></div>
            </section>
            <section class="market-detail-v3-panel">
              <div class="market-detail-v3-section-label">${escapeHtml(message(locale, "section.review_signal_set"))}</div>
              <div class="market-detail-v3-group">
                <div class="market-detail-v3-group-label">${escapeHtml(message(locale, "group.labels"))}</div>
                <div class="market-detail-v3-chip-row">${renderInlinePills(reviewLabels, message(locale, "empty.no_review_labels"))}</div>
              </div>
              <div class="market-detail-v3-group">
                <div class="market-detail-v3-group-label">${escapeHtml(message(locale, "group.warning_flags"))}</div>
                <div class="market-detail-v3-chip-row">${renderInlinePills(warningFlags, message(locale, "empty.no_warning_flags"))}</div>
              </div>
            </section>
          </div>
          <aside class="market-detail-v3-side">
            <section class="market-detail-v3-panel market-detail-v3-actions">
              <div class="market-detail-v3-section-label">${escapeHtml(message(locale, "section.action_readiness"))}</div>
              <div class="market-detail-v3-action-list">
                ${actionRows.map((item) => renderActionButton(item)).join("")}
              </div>
            </section>
          </aside>
        </div>
      </section>
    `
  }

  if (typeof module !== "undefined" && module.exports) {
    module.exports = { renderVariant3 }
  }
  if (globalScope.SharelifeMarketDetailVariantRegistry) {
    globalScope.SharelifeMarketDetailVariantRegistry.registerVariantRenderer("variant_3", renderVariant3)
  }
  globalScope.SharelifeMarketDetailVariant3 = renderVariant3
})(typeof globalThis !== "undefined" ? globalThis : this)
