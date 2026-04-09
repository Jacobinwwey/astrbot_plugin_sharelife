(function bootstrapMarketDetailVariantShared(globalScope) {
  const DEFAULT_LOCALE = "en-US"
  const STATEFUL_SECTION_IDS = ["memory_store", "conversation_history", "knowledge_base"]

  function escapeHtml(value) {
    return String(value || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;")
  }

  function normalizeList(items) {
    const rows = Array.isArray(items) ? items : [items]
    const out = []
    const seen = new Set()
    rows.forEach((item) => {
      const value = String(item || "").trim()
      if (!value || seen.has(value)) return
      seen.add(value)
      out.push(value)
    })
    return out
  }

  function resolveLocale(context = {}, messages = {}) {
    const contextLocale = String(context.locale || "").trim()
    const documentLocale = typeof document !== "undefined" && document.documentElement
      ? String(document.documentElement.getAttribute("lang") || "").trim()
      : ""
    const rawLocale = contextLocale || documentLocale || DEFAULT_LOCALE
    return Object.prototype.hasOwnProperty.call(messages, rawLocale)
      ? rawLocale
      : DEFAULT_LOCALE
  }

  function message(messages, locale, key, fallback = "") {
    const bundle = messages[locale] || messages[DEFAULT_LOCALE] || {}
    if (Object.prototype.hasOwnProperty.call(bundle, key)) {
      return bundle[key]
    }
    return fallback || key
  }

  function format(messages, locale, key, tokens = {}, fallback = "") {
    return String(message(messages, locale, key, fallback)).replace(/\{([a-zA-Z0-9_]+)\}/g, (match, token) => {
      if (!Object.prototype.hasOwnProperty.call(tokens, token)) {
        return match
      }
      return String(tokens[token] ?? "")
    })
  }

  function createContext(context = {}) {
    const sections = normalizeList(context.sections)
    const statefulSections = STATEFUL_SECTION_IDS.filter((sectionName) => sections.includes(sectionName))
    return {
      packId: String(context.packId || "").trim(),
      title: String(context.title || context.packId || "Selected Pack").trim() || "Selected Pack",
      summary: String(context.summary || "").trim(),
      version: String(context.version || "").trim() || "-",
      packType: String(context.packType || "").trim() || "-",
      compatibility: String(context.compatibility || "").trim() || "-",
      riskLevel: String(context.riskLevel || "").trim() || "-",
      maintainer: String(context.maintainer || "").trim() || "-",
      reviewLabels: normalizeList(context.reviewLabels),
      warningFlags: normalizeList(context.warningFlags),
      sections,
      statefulSections,
      featured: Boolean(context.featured),
      sourceSubmissionId: String(context.sourceSubmissionId || "").trim() || "-",
      packagePath: String(context.packagePath || "").trim() || "-",
      locale: String(context.locale || DEFAULT_LOCALE).trim() || DEFAULT_LOCALE,
    }
  }

  function renderKeyValueRows(rows, rowClass = "market-detail-derived-row") {
    return rows
      .map((row) => [
        `<div class="${rowClass}">`,
        `<span>${escapeHtml(row.label)}</span>`,
        `<strong>${escapeHtml(row.value)}</strong>`,
        "</div>",
      ].join(""))
      .join("")
  }

  function renderPillRow(items, emptyLabel) {
    const rows = normalizeList(items)
    if (!rows.length) {
      return `<span class="market-detail-derived-empty">${escapeHtml(emptyLabel)}</span>`
    }
    return rows
      .map((item) => `<span class="market-detail-derived-pill">${escapeHtml(item)}</span>`)
      .join("")
  }

  function renderList(items, emptyLabel) {
    const rows = normalizeList(items)
    if (!rows.length) {
      return `<div class="market-detail-derived-empty">${escapeHtml(emptyLabel)}</div>`
    }
    return [
      '<ul class="market-detail-derived-list">',
      ...rows.map((item) => `<li>${escapeHtml(item)}</li>`),
      "</ul>",
    ].join("")
  }

  function renderLinks(messages, locale, htmlUrl, screenshotUrl) {
    return [
      '<div class="market-detail-variant-links">',
      `<a href="${escapeHtml(htmlUrl)}" target="_blank" rel="noreferrer">${escapeHtml(message(messages, locale, "link.html", "Open Stitch HTML"))}</a>`,
      `<a href="${escapeHtml(screenshotUrl)}" target="_blank" rel="noreferrer">${escapeHtml(message(messages, locale, "link.screenshot", "Open Screenshot"))}</a>`,
      "</div>",
    ].join("")
  }

  const api = {
    STATEFUL_SECTION_IDS,
    escapeHtml,
    resolveLocale,
    message,
    format,
    createContext,
    renderKeyValueRows,
    renderPillRow,
    renderList,
    renderLinks,
  }

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api
  }
  globalScope.SharelifeMarketDetailVariantShared = api
})(typeof globalThis !== "undefined" ? globalThis : this)
