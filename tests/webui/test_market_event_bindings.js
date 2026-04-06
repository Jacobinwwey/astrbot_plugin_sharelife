const test = require("node:test")
const assert = require("node:assert/strict")

const { bindMarketEvents } = require("../../sharelife/webui/market_event_bindings.js")

function createNode(initial = {}) {
  const listeners = new Map()
  const attrs = new Map(Object.entries(initial.attrs || {}))
  return {
    value: initial.value || "",
    addEventListener(name, handler) {
      listeners.set(name, handler)
    },
    trigger(name, event = {}) {
      const handler = listeners.get(name)
      if (handler) handler(event)
    },
    getAttribute(name) {
      return attrs.has(name) ? attrs.get(name) : null
    },
    setAttribute(name, value) {
      attrs.set(String(name), String(value))
    },
  }
}

test("market event bindings wire locale/search/sort and action buttons", async () => {
  const nodes = {
    marketUiLocale: createNode({ value: "zh-CN" }),
    btnMarketLogin: createNode(),
    marketAuthRole: createNode(),
    btnMarketListCatalog: createNode(),
    btnMarketCatalogDetail: createNode(),
    btnMarketCatalogCompare: createNode(),
    btnMarketCatalogDownload: createNode(),
    marketGlobalSearch: createNode({ value: "official" }),
    marketSortBy: createNode({ value: "downloads" }),
    btnMarketOpenFilterDrawer: createNode(),
    btnMarketCloseFilterDrawer: createNode(),
    marketFilterOverlay: createNode(),
    btnMarketToggleLog: createNode(),
    btnMarketRefreshInstallations: createNode(),
    btnMarketListSubmissions: createNode(),
    btnMarketListProfilePackSubmissions: createNode(),
    btnMarketDownloadProfilePackSubmission: createNode(),
    btnMarketTemplateTrial: createNode(),
    btnMarketTemplateInstall: createNode(),
    btnMarketTemplateSubmit: createNode(),
    btnMarketProfilePackSubmit: createNode(),
  }
  const quickLocale = createNode({ attrs: { "data-market-locale-option": "ja-JP" } })
  const calls = []
  const doc = {
    addEventListener(name, handler) {
      if (name === "keydown") {
        this.keydown = handler
      }
    },
    keydown: null,
  }
  const state = {
    localSearch: "",
    localSort: "trending",
    logExpanded: false,
    filterDrawerOpen: true,
  }

  bindMarketEvents({
    byId(id) {
      return nodes[id] || null
    },
    state,
    localeQuickButtons() {
      return [quickLocale]
    },
    applyUiLocale(locale, options) {
      calls.push(["locale", locale, Boolean(options && options.persist)])
    },
    login() {
      calls.push(["login"])
      return Promise.resolve()
    },
    syncReviewerAuthFields() {
      calls.push(["sync_role"])
    },
    listCatalog() {
      calls.push(["catalog"])
      return Promise.resolve()
    },
    loadCatalogDetail() {
      calls.push(["detail"])
      return Promise.resolve()
    },
    compareCatalogPack() {
      calls.push(["compare"])
      return Promise.resolve()
    },
    triggerCatalogDownload() {
      calls.push(["download"])
    },
    applyLocalCatalogView() {
      calls.push(["local_view", state.localSearch, state.localSort])
    },
    setFilterDrawerOpen(open) {
      calls.push(["drawer", Boolean(open)])
      state.filterDrawerOpen = Boolean(open)
    },
    setMarketLogExpanded(open) {
      calls.push(["log", Boolean(open)])
      state.logExpanded = Boolean(open)
    },
    loadMarketInstallations(options) {
      calls.push(["installations", Boolean(options && options.refresh)])
      return Promise.resolve()
    },
    listMarketTemplateSubmissions() {
      calls.push(["template_submissions"])
      return Promise.resolve()
    },
    listMarketProfilePackSubmissions() {
      calls.push(["profile_pack_submissions"])
      return Promise.resolve()
    },
    downloadMarketProfilePackSubmissionExport() {
      calls.push(["download_submission"])
      return Promise.resolve()
    },
    runMarketTemplateTrial() {
      calls.push(["trial"])
      return Promise.resolve()
    },
    runMarketTemplateInstall() {
      calls.push(["install"])
      return Promise.resolve()
    },
    runMarketTemplateSubmit() {
      calls.push(["submit"])
      return Promise.resolve()
    },
    runMarketProfilePackSubmit() {
      calls.push(["profile_submit"])
      return Promise.resolve()
    },
    bindUploadDropZone(config) {
      calls.push(["upload_bind", config.zoneId, config.inputId, config.outputId])
    },
    sortFallback: "trending",
    document: doc,
  })

  nodes.marketUiLocale.trigger("change")
  quickLocale.trigger("click")
  nodes.marketGlobalSearch.trigger("input")
  nodes.marketSortBy.trigger("change")
  nodes.btnMarketOpenFilterDrawer.trigger("click")
  nodes.btnMarketCloseFilterDrawer.trigger("click")
  nodes.marketFilterOverlay.trigger("click")
  nodes.btnMarketToggleLog.trigger("click")
  nodes.btnMarketRefreshInstallations.trigger("click")
  nodes.btnMarketListSubmissions.trigger("click")
  nodes.btnMarketListProfilePackSubmissions.trigger("click")
  nodes.btnMarketDownloadProfilePackSubmission.trigger("click")
  nodes.btnMarketTemplateTrial.trigger("click")
  nodes.btnMarketTemplateInstall.trigger("click")
  nodes.btnMarketTemplateSubmit.trigger("click")
  nodes.btnMarketProfilePackSubmit.trigger("click")
  nodes.btnMarketLogin.trigger("click")
  nodes.marketAuthRole.trigger("change")
  nodes.btnMarketListCatalog.trigger("click")
  nodes.btnMarketCatalogDetail.trigger("click")
  nodes.btnMarketCatalogCompare.trigger("click")
  nodes.btnMarketCatalogDownload.trigger("click")
  assert.ok(typeof doc.keydown === "function")
  doc.keydown({ key: "Escape" })

  assert.ok(calls.some((entry) => entry[0] === "locale" && entry[1] === "zh-CN" && entry[2] === true))
  assert.ok(calls.some((entry) => entry[0] === "locale" && entry[1] === "ja-JP" && entry[2] === true))
  assert.ok(calls.some((entry) => entry[0] === "local_view" && entry[1] === "official"))
  assert.ok(calls.some((entry) => entry[0] === "local_view" && entry[2] === "downloads"))
  assert.ok(calls.some((entry) => entry[0] === "drawer" && entry[1] === true))
  assert.ok(calls.some((entry) => entry[0] === "drawer" && entry[1] === false))
  assert.ok(calls.some((entry) => entry[0] === "log" && entry[1] === true))
  assert.ok(calls.some((entry) => entry[0] === "upload_bind"))
  assert.ok(calls.some((entry) => entry[0] === "login"))
  assert.ok(calls.some((entry) => entry[0] === "catalog"))
  assert.ok(calls.some((entry) => entry[0] === "detail"))
  assert.ok(calls.some((entry) => entry[0] === "compare"))
  assert.ok(calls.some((entry) => entry[0] === "download"))
  assert.ok(calls.some((entry) => entry[0] === "trial"))
  assert.ok(calls.some((entry) => entry[0] === "install"))
  assert.ok(calls.some((entry) => entry[0] === "submit"))
  assert.ok(calls.some((entry) => entry[0] === "profile_submit"))
})
