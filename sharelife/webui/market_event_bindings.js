(function bootstrapMarketEventBindings(globalScope) {
  function noop() {}

  function bindMarketEvents(options = {}) {
    const byId = typeof options.byId === "function" ? options.byId : () => null
    const state = options.state && typeof options.state === "object" ? options.state : {}
    const localeQuickButtons = typeof options.localeQuickButtons === "function" ? options.localeQuickButtons : () => []
    const applyUiLocale = typeof options.applyUiLocale === "function" ? options.applyUiLocale : noop
    const login = typeof options.login === "function" ? options.login : noop
    const syncReviewerAuthFields = typeof options.syncReviewerAuthFields === "function" ? options.syncReviewerAuthFields : noop
    const listCatalog = typeof options.listCatalog === "function" ? options.listCatalog : noop
    const loadCatalogDetail = typeof options.loadCatalogDetail === "function" ? options.loadCatalogDetail : noop
    const compareCatalogPack = typeof options.compareCatalogPack === "function" ? options.compareCatalogPack : noop
    const triggerCatalogDownload = typeof options.triggerCatalogDownload === "function" ? options.triggerCatalogDownload : noop
    const applyLocalCatalogView = typeof options.applyLocalCatalogView === "function" ? options.applyLocalCatalogView : noop
    const setFilterDrawerOpen = typeof options.setFilterDrawerOpen === "function" ? options.setFilterDrawerOpen : noop
    const setMarketLogExpanded = typeof options.setMarketLogExpanded === "function" ? options.setMarketLogExpanded : noop
    const loadMarketInstallations = typeof options.loadMarketInstallations === "function" ? options.loadMarketInstallations : noop
    const listMarketTemplateSubmissions = typeof options.listMarketTemplateSubmissions === "function" ? options.listMarketTemplateSubmissions : noop
    const listMarketProfilePackSubmissions = typeof options.listMarketProfilePackSubmissions === "function" ? options.listMarketProfilePackSubmissions : noop
    const downloadMarketProfilePackSubmissionExport = typeof options.downloadMarketProfilePackSubmissionExport === "function"
      ? options.downloadMarketProfilePackSubmissionExport
      : noop
    const runMarketTemplateTrial = typeof options.runMarketTemplateTrial === "function" ? options.runMarketTemplateTrial : noop
    const runMarketTemplateInstall = typeof options.runMarketTemplateInstall === "function" ? options.runMarketTemplateInstall : noop
    const runMarketTemplateSubmit = typeof options.runMarketTemplateSubmit === "function" ? options.runMarketTemplateSubmit : noop
    const runMarketProfilePackSubmit = typeof options.runMarketProfilePackSubmit === "function" ? options.runMarketProfilePackSubmit : noop
    const bindUploadDropZone = typeof options.bindUploadDropZone === "function" ? options.bindUploadDropZone : noop
    const sortFallback = String(options.sortFallback || "trending")
    const doc = options.document || globalScope.document

    const localeNode = byId("marketUiLocale")
    if (localeNode) {
      localeNode.addEventListener("change", () => {
        applyUiLocale(localeNode.value, { persist: true })
      })
    }

    localeQuickButtons().forEach((node) => {
      node.addEventListener("click", () => {
        const locale = String(node.getAttribute("data-market-locale-option") || "").trim()
        if (!locale) return
        applyUiLocale(locale, { persist: true })
      })
    })

    const loginButton = byId("btnMarketLogin")
    if (loginButton) {
      loginButton.addEventListener("click", () => {
        void login()
      })
    }

    const authRoleNode = byId("marketAuthRole")
    if (authRoleNode) {
      authRoleNode.addEventListener("change", syncReviewerAuthFields)
    }

    const listCatalogButton = byId("btnMarketListCatalog")
    if (listCatalogButton) {
      listCatalogButton.addEventListener("click", () => {
        void listCatalog()
      })
    }

    const catalogDetailButton = byId("btnMarketCatalogDetail")
    if (catalogDetailButton) {
      catalogDetailButton.addEventListener("click", () => {
        void loadCatalogDetail()
      })
    }

    const catalogCompareButton = byId("btnMarketCatalogCompare")
    if (catalogCompareButton) {
      catalogCompareButton.addEventListener("click", () => {
        void compareCatalogPack()
      })
    }

    const downloadButton = byId("btnMarketCatalogDownload")
    if (downloadButton) {
      downloadButton.addEventListener("click", () => {
        triggerCatalogDownload()
      })
    }

    const searchNode = byId("marketGlobalSearch")
    if (searchNode) {
      searchNode.addEventListener("input", () => {
        state.localSearch = String(searchNode.value || "").trim()
        applyLocalCatalogView()
      })
    }

    const sortNode = byId("marketSortBy")
    if (sortNode) {
      sortNode.addEventListener("change", () => {
        state.localSort = String(sortNode.value || sortFallback)
        applyLocalCatalogView()
      })
    }

    const openDrawerButton = byId("btnMarketOpenFilterDrawer")
    if (openDrawerButton) {
      openDrawerButton.addEventListener("click", () => {
        setFilterDrawerOpen(true)
      })
    }

    const closeDrawerButton = byId("btnMarketCloseFilterDrawer")
    if (closeDrawerButton) {
      closeDrawerButton.addEventListener("click", () => {
        setFilterDrawerOpen(false)
      })
    }

    const overlay = byId("marketFilterOverlay")
    if (overlay) {
      overlay.addEventListener("click", () => {
        setFilterDrawerOpen(false)
      })
    }

    const logToggleButton = byId("btnMarketToggleLog")
    if (logToggleButton) {
      logToggleButton.addEventListener("click", () => {
        setMarketLogExpanded(!state.logExpanded)
      })
    }

    const refreshInstallationsBtn = byId("btnMarketRefreshInstallations")
    if (refreshInstallationsBtn) {
      refreshInstallationsBtn.addEventListener("click", () => {
        void loadMarketInstallations({ refresh: true })
      })
    }

    const listSubmissionsBtn = byId("btnMarketListSubmissions")
    if (listSubmissionsBtn) {
      listSubmissionsBtn.addEventListener("click", () => {
        void listMarketTemplateSubmissions()
      })
    }

    const listProfilePackSubmissionsBtn = byId("btnMarketListProfilePackSubmissions")
    if (listProfilePackSubmissionsBtn) {
      listProfilePackSubmissionsBtn.addEventListener("click", () => {
        void listMarketProfilePackSubmissions()
      })
    }

    const downloadProfilePackSubmissionBtn = byId("btnMarketDownloadProfilePackSubmission")
    if (downloadProfilePackSubmissionBtn) {
      downloadProfilePackSubmissionBtn.addEventListener("click", () => {
        void downloadMarketProfilePackSubmissionExport()
      })
    }

    const templateTrialBtn = byId("btnMarketTemplateTrial")
    if (templateTrialBtn) {
      templateTrialBtn.addEventListener("click", () => {
        void runMarketTemplateTrial()
      })
    }

    const templateInstallBtn = byId("btnMarketTemplateInstall")
    if (templateInstallBtn) {
      templateInstallBtn.addEventListener("click", () => {
        void runMarketTemplateInstall()
      })
    }

    const templateSubmitBtn = byId("btnMarketTemplateSubmit")
    if (templateSubmitBtn) {
      templateSubmitBtn.addEventListener("click", () => {
        void runMarketTemplateSubmit()
      })
    }

    const profilePackSubmitBtn = byId("btnMarketProfilePackSubmit")
    if (profilePackSubmitBtn) {
      profilePackSubmitBtn.addEventListener("click", () => {
        void runMarketProfilePackSubmit()
      })
    }

    bindUploadDropZone({
      zoneId: "marketUploadDropzone",
      inputId: "marketSubmitPackageFile",
      outputId: "marketUploadFileName",
      emptyKey: "market.upload.file_idle",
      emptyFallback: "No file selected. Template submit can still use generated output.",
    })

    if (doc && typeof doc.addEventListener === "function") {
      doc.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && state.filterDrawerOpen) {
          setFilterDrawerOpen(false)
        }
      })
    }
  }

  const api = {
    bindMarketEvents,
  }

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api
  }
  globalScope.SharelifeMarketEventBindings = api
})(typeof globalThis !== "undefined" ? globalThis : this)
