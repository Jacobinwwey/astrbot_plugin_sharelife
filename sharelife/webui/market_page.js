(function bootstrapMarketPage(globalScope) {
  const UI_LOCALE_STORAGE_KEY = "sharelife.uiLocale"
  const MARKET_PAGE_INSTANCE_ID = `sharelife-market-${Math.random().toString(36).slice(2)}`
  const marketFilterApi = globalScope.SharelifeMarketFilters || null
  const LOCAL_SORT_OPTIONS = Object.freeze({
    TRENDING: "trending",
    DOWNLOADS: "downloads",
    RECENT: "recent",
  })
  const LOCAL_FACET_GROUPS = Object.freeze([
    {
      key: "pack_type",
      titleKey: "market.filter.group.pack_type",
      titleFallback: "Pack Type",
      ordered: ["bot_profile_pack", "extension_pack", "unknown"],
      seeded: ["bot_profile_pack", "extension_pack", "unknown"],
      emptyKey: "option.pack_type.all",
      emptyFallback: "All Pack Types",
    },
    {
      key: "risk_level",
      titleKey: "market.filter.group.risk_level",
      titleFallback: "Risk Level",
      ordered: ["high", "medium", "low", "unknown"],
      seeded: ["high", "medium", "low", "unknown"],
      emptyKey: "option.risk.all",
      emptyFallback: "all risk",
    },
    {
      key: "featured",
      titleKey: "market.filter.group.featured",
      titleFallback: "Featured",
      ordered: ["true", "false"],
      seeded: ["true", "false"],
      emptyKey: "option.featured_status.all",
      emptyFallback: "all featured status",
    },
    {
      key: "compatibility",
      titleKey: "market.filter.group.compatibility",
      titleFallback: "Compatibility",
      ordered: ["compatible", "degraded", "blocked", "unknown"],
      seeded: ["compatible", "degraded", "blocked", "unknown"],
    },
    {
      key: "review_label",
      titleKey: "market.filter.group.review_label",
      titleFallback: "Review Label",
      ordered: [],
      seeded: [
        "official_featured",
        "approved",
        "community_verified",
        "risk_low",
        "risk_medium",
        "risk_high",
      ],
    },
    {
      key: "warning_flag",
      titleKey: "market.filter.group.warning_flag",
      titleFallback: "Warning Flag",
      ordered: [],
      seeded: [
        "prompt_injection_detected",
        "ignore_previous_instructions",
        "reveal_system_prompt",
        "plugin_install_failed",
        "capability_mismatch",
      ],
    },
  ])

  function createFacetSelectionMap() {
    const selection = {}
    LOCAL_FACET_GROUPS.forEach((group) => {
      selection[group.key] = new Set()
    })
    return selection
  }

  const state = {
    token: "",
    authRequired: false,
    authRole: "",
    availableRoles: [],
    capabilities: {
      role: "member",
      operations: [],
    },
    catalog: [],
    catalogRaw: [],
    catalogInsights: null,
    selectedPackId: "",
    uiLocale: "en-US",
    health: null,
    lastSummary: null,
    lastComparePayload: null,
    localSearch: "",
    localSort: LOCAL_SORT_OPTIONS.TRENDING,
    localFacets: createFacetSelectionMap(),
    filterDrawerOpen: false,
    logExpanded: false,
    detailExpanded: false,
    compareDetailKey: "",
    memberInstallations: [],
    memberTemplateSubmissions: [],
    memberProfilePackSubmissions: [],
    selectedProfilePackSubmissionId: "",
    memberUserId: "webui-user",
    publicCatalogRows: [],
    publicCatalogAvailable: false,
    catalogSourceMode: "runtime",
  }
  const CONTROL_CAPABILITY_MAP = Object.freeze({
    btnMarketLogin: "auth.login",
    btnMarketRefreshInstallations: "member.installations.refresh",
    btnMarketListCatalog: "profile_pack.catalog.read",
    btnMarketCatalogDetail: "profile_pack.catalog.read",
    btnMarketCatalogCompare: "profile_pack.catalog.read",
    btnMarketTemplateTrial: "templates.trial.request",
    btnMarketTemplateInstall: "templates.install",
    btnMarketTemplateSubmit: "templates.submit",
    btnMarketProfilePackSubmit: "profile_pack.community.submit",
    btnMarketListSubmissions: "member.submissions.read",
    btnMarketListProfilePackSubmissions: "member.profile_pack.submissions.read",
    btnMarketDownloadProfilePackSubmission: "member.profile_pack.submissions.export.download",
  })
  let storageSyncBound = false
  let uiEventBusBound = false
  const compareViewHelper = globalScope.SharelifeProfilePackCompareView

  function marketCardHelpers() {
    return globalScope.SharelifeMarketCards || null
  }

  function marketFacetViewHelpers() {
    return globalScope.SharelifeMarketFacetView || null
  }

  function marketEventBindingHelpers() {
    return globalScope.SharelifeMarketEventBindings || null
  }

  function marketStatusViewHelpers() {
    return globalScope.SharelifeMarketStatusView || null
  }

  function marketAuthViewHelpers() {
    return globalScope.SharelifeMarketAuthView || null
  }

  function marketCatalogInsightsHelpers() {
    return globalScope.SharelifeMarketCatalogInsights || null
  }

  function marketCatalogViewHelpers() {
    return globalScope.SharelifeMarketCatalogView || null
  }

  function marketCompareHelpers() {
    return globalScope.SharelifeMarketCompareHelpers || null
  }

  function uiEventBusHelpers() {
    return globalScope.SharelifeUiEventBus || null
  }

  function byId(id) {
    return document.getElementById(id)
  }

  function fixedAuthRole() {
    return "member"
  }

  function i18nHelpers() {
    return globalScope.SharelifeWebuiI18n || null
  }

  function readStoredUiLocale() {
    if (!globalScope.localStorage) return ""
    try {
      return String(globalScope.localStorage.getItem(UI_LOCALE_STORAGE_KEY) || "")
    } catch (_error) {
      return ""
    }
  }

  function saveUiLocale(locale) {
    if (!globalScope.localStorage) return
    try {
      globalScope.localStorage.setItem(UI_LOCALE_STORAGE_KEY, locale)
    } catch (_error) {
      // noop
    }
  }

  function uiEventTopic(topicName, fallback) {
    const bus = uiEventBusHelpers()
    if (!bus || !bus.TOPICS) return fallback
    return bus.TOPICS[topicName] || fallback
  }

  function emitUiEvent(topicName, fallbackTopic, payload) {
    const bus = uiEventBusHelpers()
    if (!bus || typeof bus.emit !== "function") return
    const topic = uiEventTopic(topicName, fallbackTopic)
    bus.emit(topic, payload || {})
  }

  function normalizeUiLocale(locale) {
    const helper = i18nHelpers()
    if (helper && helper.normalizeLocale) {
      return helper.normalizeLocale(locale, state.uiLocale || "en-US")
    }
    const value = String(locale || "").trim()
    return value || "en-US"
  }

  function browserUiLocale() {
    if (!globalScope.navigator) return ""
    const languages = Array.isArray(globalScope.navigator.languages)
      ? globalScope.navigator.languages
      : []
    if (languages.length > 0) {
      return String(languages[0] || "")
    }
    return String(globalScope.navigator.language || "")
  }

  function i18nMessage(key, fallback = "") {
    const helper = i18nHelpers()
    if (helper && helper.getMessage) {
      return helper.getMessage(state.uiLocale, key, fallback)
    }
    return fallback
  }

  function localeQuickButtons() {
    return Array.from(document.querySelectorAll("[data-market-locale-option]"))
  }

  function updateLocaleQuickButtons() {
    localeQuickButtons().forEach((node) => {
      const locale = String(node.getAttribute("data-market-locale-option") || "").trim()
      const active = locale === state.uiLocale
      node.classList.toggle("is-active", active)
      node.setAttribute("aria-pressed", active ? "true" : "false")
    })
  }

  function i18nFormat(key, fallback, tokens = {}) {
    const template = i18nMessage(key, fallback)
    return String(template).replace(/\{([a-zA-Z0-9_]+)\}/g, (match, token) => {
      if (!Object.prototype.hasOwnProperty.call(tokens, token)) {
        return match
      }
      return String(tokens[token] ?? "")
    })
  }

  function humanizeCode(value) {
    const text = String(value || "").trim()
    if (!text) return "-"
    return text.replace(/[_-]+/g, " ").trim()
  }

  function enumLabel(group, value) {
    const text = String(value || "").trim()
    if (!text) return "-"
    if (group === "pack_type") {
      if (text === "bot_profile_pack") {
        return i18nMessage("option.pack_type.bot_profile_pack", "Bot Profile Pack")
      }
      if (text === "extension_pack") {
        return i18nMessage("option.pack_type.extension_pack", "Extension Pack")
      }
    }
    const key = `enum.${group}.${text.toLowerCase()}`
    return i18nMessage(key, humanizeCode(text))
  }

  function localizedList(group, values) {
    const rows = Array.isArray(values) ? values.filter(Boolean) : []
    if (!rows.length) return "-"
    return rows.map((item) => enumLabel(group, item)).join(", ")
  }

  function normalizePackIdKey(packId) {
    return String(packId || "")
      .trim()
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "_")
      .replace(/^_+|_+$/g, "")
  }

  function localizedPackTitle(packId) {
    const id = String(packId || "").trim()
    if (!id) return "-"
    const key = normalizePackIdKey(id)
    if (!key) return id
    return i18nMessage(`market.pack.${key}.title`, id)
  }

  function localizedPackLabel(packId, options = {}) {
    const id = String(packId || "").trim()
    if (!id) return "-"
    const title = localizedPackTitle(id)
    if (!title || title === id) return id
    if (options && options.includeId) {
      return i18nFormat("market.pack.label", "{title} ({pack_id})", {
        title,
        pack_id: id,
      })
    }
    return title
  }

  function localizedPackDescription(packId, fallback = "") {
    const id = String(packId || "").trim()
    if (!id) return String(fallback || "")
    const key = normalizePackIdKey(id)
    if (!key) return String(fallback || "")
    return i18nMessage(`market.pack.${key}.description`, String(fallback || ""))
  }

  function localizedPackFeaturedNote(packId, fallback = "") {
    const id = String(packId || "").trim()
    if (!id) return String(fallback || "")
    const key = normalizePackIdKey(id)
    if (!key) return String(fallback || "")
    return i18nMessage(`market.pack.${key}.featured_note`, String(fallback || ""))
  }

  function localizedSourceSubmission(sourceSubmissionId, fallbackPackId = "") {
    const raw = String(sourceSubmissionId || "").trim()
    if (!raw) {
      return i18nMessage("market.source.official", "official")
    }
    if (!raw.startsWith("official:")) {
      return raw
    }
    const normalizedPackId = String(raw.slice("official:".length) || "").trim()
      || String(fallbackPackId || "").trim()
    if (!normalizedPackId) {
      return i18nMessage("market.source.official", "official")
    }
    const label = localizedPackLabel(normalizedPackId)
    if (!label || label === normalizedPackId) {
      return i18nMessage("market.source.official", "official")
    }
    return i18nFormat("market.source.official_pack", "official · {pack}", {
      pack: label,
    })
  }

  function resolveCatalogPackTitle(item) {
    return localizedPackTitle(String((item && item.pack_id) || "").trim())
  }

  function resolveCatalogPackLabel(item) {
    const packId = String((item && item.pack_id) || "").trim()
    if (!packId) return "-"
    return localizedPackLabel(packId)
  }

  function resolveCatalogPackSubtitle(item) {
    const packType = enumLabel("pack_type", String((item && item.pack_type) || "bot_profile_pack"))
    const version = String((item && item.version) || "-")
    return i18nFormat("market.card.subtitle", "{pack_type} · v{version}", {
      pack_type: packType,
      version,
    })
  }

  function applyUiLocale(locale, options = {}) {
    const normalized = normalizeUiLocale(locale)
    state.uiLocale = normalized
    const localeField = byId("marketUiLocale")
    if (localeField && localeField.value !== normalized) {
      localeField.value = normalized
    }

    const helper = i18nHelpers()
    if (helper && helper.applyLocale) {
      helper.applyLocale(document, normalized)
    }
    updateLocaleQuickButtons()
    if (options.persist !== false) {
      saveUiLocale(normalized)
    }
    if (options.emit !== false) {
      emitUiEvent("UI_LOCALE_CHANGED", "ui.locale.changed", {
        locale: normalized,
        source: options.source || "market",
        sourceId: options.sourceId || MARKET_PAGE_INSTANCE_ID,
      })
    }
    updateAuthUi()
    updateHealthUi()
    setMarketLogExpanded(state.logExpanded)
    if (state.catalogRaw.length) {
      applyLocalCatalogView({ updateSummary: false })
    } else {
      updateCatalogTable(state.catalog)
      updateCatalogCountChips([], [])
      renderFacetFilters([])
    }
    updateSummary(state.lastSummary)
    if (state.lastComparePayload) {
      renderCompareView(state.lastComparePayload)
    }
    return normalized
  }

  function initializeUiLocale() {
    const helper = i18nHelpers()
    const stored = readStoredUiLocale()
    const fallback = browserUiLocale() || "en-US"
    const defaultLocale = helper && helper.DEFAULT_LOCALE ? helper.DEFAULT_LOCALE : "en-US"
    const initial = normalizeUiLocale(stored || fallback || defaultLocale)
    applyUiLocale(initial, { persist: false })
  }

  function handleUiStorageSync(event) {
    if (!event || String(event.key || "") !== UI_LOCALE_STORAGE_KEY) return
    const incoming = String(event.newValue || "").trim()
    const nextLocale = normalizeUiLocale(incoming || browserUiLocale() || "en-US")
    if (nextLocale === state.uiLocale) return
    applyUiLocale(nextLocale, {
      persist: false,
      emit: false,
      source: "storage",
      sourceId: "storage",
    })
  }

  function bindStorageSync() {
    if (storageSyncBound) return
    if (!globalScope || typeof globalScope.addEventListener !== "function") return
    globalScope.addEventListener("storage", handleUiStorageSync)
    storageSyncBound = true
  }

  function bindUiEventBusSync() {
    if (uiEventBusBound) return
    const bus = uiEventBusHelpers()
    if (!bus || typeof bus.on !== "function") return
    const localeTopic = uiEventTopic("UI_LOCALE_CHANGED", "ui.locale.changed")
    bus.on(localeTopic, (payload) => {
      if (!payload || payload.sourceId === MARKET_PAGE_INSTANCE_ID) return
      const nextLocale = normalizeUiLocale(payload.locale || "")
      if (nextLocale === state.uiLocale) return
      applyUiLocale(nextLocale, {
        persist: false,
        emit: false,
        source: payload.source || "event_bus",
        sourceId: payload.sourceId || "event_bus",
      })
    })
    uiEventBusBound = true
  }

  function queryString(params) {
    const query = new URLSearchParams()
    Object.entries(params || {}).forEach(([key, value]) => {
      if (value === undefined || value === null || value === "") return
      query.set(key, String(value))
    })
    const text = query.toString()
    return text ? `?${text}` : ""
  }

  function validSortOption(value) {
    const text = String(value || "").trim()
    const values = Object.values(LOCAL_SORT_OPTIONS)
    if (values.includes(text)) return text
    return LOCAL_SORT_OPTIONS.TRENDING
  }

  function parseCsvQueryValue(value) {
    return String(value || "")
      .split(",")
      .map((item) => String(item || "").trim())
      .filter(Boolean)
  }

  function applyQueryStateToControls() {
    const searchNode = byId("marketGlobalSearch")
    if (searchNode) {
      searchNode.value = state.localSearch
    }
    const sortNode = byId("marketSortBy")
    if (sortNode) {
      sortNode.value = validSortOption(state.localSort)
    }
    const packNode = byId("marketPackId")
    if (packNode && state.selectedPackId) {
      packNode.value = state.selectedPackId
    }
  }

  function loadQueryState() {
    if (!globalScope || !globalScope.location) return
    const search = globalScope.location.search || ""
    if (marketFilterApi && typeof marketFilterApi.parseQueryState === "function") {
      const parsed = marketFilterApi.parseQueryState(search, {
        groups: LOCAL_FACET_GROUPS,
        sortOptions: LOCAL_SORT_OPTIONS,
      })
      state.localSearch = parsed.localSearch
      state.localSort = parsed.localSort
      state.selectedPackId = parsed.selectedPackId
      state.localFacets = parsed.localFacets
      return
    }
    const params = new URLSearchParams(search)
    state.localSearch = String(params.get("q") || "").trim()
    state.localSort = validSortOption(params.get("sort") || LOCAL_SORT_OPTIONS.TRENDING)
    state.selectedPackId = String(params.get("pack_id") || "").trim()
    state.localFacets = createFacetSelectionMap()
    LOCAL_FACET_GROUPS.forEach((group) => {
      const queryKey = `facet_${group.key}`
      parseCsvQueryValue(params.get(queryKey)).forEach((value) => {
        state.localFacets[group.key].add(value)
      })
    })
  }

  function syncQueryState() {
    if (!globalScope || !globalScope.location || !globalScope.history) return
    let next = null
    if (marketFilterApi && typeof marketFilterApi.buildQueryStateParams === "function") {
      next = marketFilterApi.buildQueryStateParams(state, {
        groups: LOCAL_FACET_GROUPS,
        sortOptions: LOCAL_SORT_OPTIONS,
      })
    } else {
      next = new URLSearchParams()
      const q = String(state.localSearch || "").trim()
      const sort = validSortOption(state.localSort)
      if (q) next.set("q", q)
      if (sort && sort !== LOCAL_SORT_OPTIONS.TRENDING) next.set("sort", sort)
      if (state.selectedPackId) next.set("pack_id", state.selectedPackId)
      LOCAL_FACET_GROUPS.forEach((group) => {
        const selected = state.localFacets[group.key]
        if (!(selected instanceof Set) || selected.size === 0) return
        next.set(`facet_${group.key}`, Array.from(selected).sort().join(","))
      })
    }
    const search = next.toString()
    const nextHref = `${globalScope.location.pathname}${search ? `?${search}` : ""}${globalScope.location.hash || ""}`
    const currentHref = `${globalScope.location.pathname}${globalScope.location.search || ""}${globalScope.location.hash || ""}`
    if (nextHref === currentHref) return
    globalScope.history.replaceState(null, "", nextHref)
  }

  function headers() {
    const out = { "Content-Type": "application/json" }
    if (state.token && state.token !== "no-auth") {
      out.Authorization = `Bearer ${state.token}`
    }
    return out
  }

  async function api(path, options = {}) {
    const init = {
      method: options.method || "GET",
      headers: headers(),
    }
    if (options.body !== undefined) {
      init.body = JSON.stringify(options.body)
    }
    const response = await fetch(path, init)
    const data = await response.json().catch(() => ({ ok: false, message: "invalid_json" }))
    return { status: response.status, data }
  }

  function apiData(response) {
    if (response && response.data && response.data.data !== undefined) {
      return response.data.data
    }
    return {}
  }

  function publicMarketBasePath() {
    return "/public-market"
  }

  function publicMarketCatalogUrl() {
    return `${publicMarketBasePath()}/market/catalog.snapshot.json`
  }

  function normalizeStringArray(value) {
    if (!Array.isArray(value)) return []
    return value.map((item) => String(item || "").trim()).filter(Boolean)
  }

  function normalizeObject(value) {
    return value && typeof value === "object" ? value : {}
  }

  function normalizePublicCatalogRows(input) {
    if (!Array.isArray(input)) return []
    return input
      .filter((item) => item && typeof item === "object")
      .map((item) => {
        const raw = normalizeObject(item)
        const packId = String(raw.pack_id || raw.template_id || "").trim()
        const version = String(raw.version || "").trim()
        if (!packId || !version) return null
        const engagement = normalizeObject(raw.engagement)
        return {
          ...raw,
          pack_id: packId,
          template_id: packId,
          version,
          pack_type: String(raw.pack_type || "bot_profile_pack").trim() || "bot_profile_pack",
          review_labels: normalizeStringArray(raw.review_labels),
          warning_flags: normalizeStringArray(raw.warning_flags),
          compatibility_issues: normalizeStringArray(raw.compatibility_issues),
          sections: normalizeStringArray(raw.sections),
          package_path: String(raw.package_path || "").trim(),
          title: String(raw.title || "").trim(),
          description: String(raw.description || "").trim(),
          source_channel: String(raw.source_channel || "community_submission").trim() || "community_submission",
          maintainer: String(raw.maintainer || "community").trim() || "community",
          engagement: {
            installs: toSafeInt(engagement.installs),
            trial_requests: toSafeInt(engagement.trial_requests),
          },
          capability_summary: normalizeObject(raw.capability_summary),
          compatibility_matrix: normalizeObject(raw.compatibility_matrix),
          review_evidence: normalizeObject(raw.review_evidence),
          scan_summary: normalizeObject(raw.scan_summary),
          featured: Boolean(raw.featured),
          runtime_available: false,
          catalog_origin: "public",
        }
      })
      .filter(Boolean)
  }

  function rowMatchesServerCatalogFilters(item, filters) {
    if (!item || typeof item !== "object") return false
    const current = filters && typeof filters === "object" ? filters : {}
    const packQuery = String(current.pack_id || "").trim().toLowerCase()
    const packType = String(current.pack_type || "").trim().toLowerCase()
    const risk = String(current.risk_level || "").trim().toLowerCase()
    const featured = String(current.featured || "").trim().toLowerCase()
    const reviewLabel = String(current.review_label || "").trim().toLowerCase()
    const warningFlag = String(current.warning_flag || "").trim().toLowerCase()
    if (packQuery && !String(item.pack_id || "").trim().toLowerCase().includes(packQuery)) return false
    if (packType && String(item.pack_type || "").trim().toLowerCase() !== packType) return false
    if (risk && String(item.risk_level || "").trim().toLowerCase() !== risk) return false
    if (featured === "true" && !item.featured) return false
    if (featured === "false" && item.featured) return false
    if (reviewLabel) {
      const labels = normalizeStringArray(item.review_labels).map((value) => value.toLowerCase())
      if (!labels.includes(reviewLabel)) return false
    }
    if (warningFlag) {
      const flags = normalizeStringArray(item.warning_flags).map((value) => value.toLowerCase())
      if (!flags.includes(warningFlag)) return false
    }
    return true
  }

  async function fetchPublicCatalogRows() {
    try {
      const response = await fetch(publicMarketCatalogUrl(), {
        method: "GET",
        cache: "no-store",
      })
      if (!response.ok) return []
      const payload = await response.json()
      const rows = normalizePublicCatalogRows(payload && payload.rows)
      const filters = catalogFilters()
      return rows.filter((item) => rowMatchesServerCatalogFilters(item, filters))
    } catch (_error) {
      return []
    }
  }

  function catalogRowKey(item) {
    const packId = String(item && item.pack_id || "").trim()
    const version = String(item && item.version || "").trim()
    return `${packId}@@${version}`
  }

  function mergeCatalogRows(runtimeRows, publicRows) {
    const out = new Map()
    ;(Array.isArray(publicRows) ? publicRows : []).forEach((item) => {
      if (!item || typeof item !== "object") return
      out.set(catalogRowKey(item), {
        ...item,
        runtime_available: false,
        catalog_origin: "public",
      })
    })
    ;(Array.isArray(runtimeRows) ? runtimeRows : []).forEach((item) => {
      if (!item || typeof item !== "object") return
      const key = catalogRowKey(item)
      const publicRow = out.get(key)
      const merged = publicRow
        ? {
          ...publicRow,
          ...item,
          engagement: {
            installs: toSafeInt(publicRow.engagement && publicRow.engagement.installs),
            trial_requests: toSafeInt(publicRow.engagement && publicRow.engagement.trial_requests),
            ...(item.engagement && typeof item.engagement === "object" ? item.engagement : {}),
          },
          package_path: String(item.package_path || publicRow.package_path || "").trim(),
          title: String(item.title || publicRow.title || "").trim(),
          description: String(item.description || publicRow.description || "").trim(),
          runtime_available: true,
          catalog_origin: "merged",
        }
        : {
          ...item,
          runtime_available: true,
          catalog_origin: "runtime",
        }
      out.set(key, merged)
    })
    return Array.from(out.values())
  }

  function deriveCatalogInsightsPayload(rows) {
    const metric = catalogMetrics(rows)
    const ranked = Array.isArray(rows) ? rows.slice() : []
    ranked.sort((left, right) => {
      const scoreDiff = catalogTrendScore(right) - catalogTrendScore(left)
      if (scoreDiff !== 0) return scoreDiff
      const leftTime = parseIsoDate(left && (left.featured_at || left.published_at))
      const rightTime = parseIsoDate(right && (right.featured_at || right.published_at))
      if (rightTime !== leftTime) return rightTime - leftTime
      return String(left && left.pack_id || "").localeCompare(String(right && right.pack_id || ""))
    })
    const featured = ranked.find((item) => Boolean(item && item.featured)) || ranked[0] || null
    return {
      metrics: {
        total: metric.total,
        featured: metric.featured,
        high_risk: metric.highRisk,
        low_risk: metric.safe,
        extension_pack: metric.extension,
        bot_profile_pack: metric.botProfile,
      },
      featured,
      trending: ranked.slice(0, 6),
      total: metric.total,
    }
  }

  function catalogPackageUrl(item) {
    const packagePath = String(item && item.package_path || "").trim()
    if (!packagePath) return ""
    if (/^https?:\/\//i.test(packagePath)) return packagePath
    if (packagePath.startsWith("/")) {
      return `${publicMarketBasePath()}${packagePath}`
    }
    return `${publicMarketBasePath()}/${packagePath.replace(/^\/+/, "")}`
  }

  function selectedCatalogRow() {
    const selectedPackId = String(state.selectedPackId || "").trim()
    if (!selectedPackId) return null
    const candidates = []
    if (Array.isArray(state.catalog)) candidates.push(...state.catalog)
    if (Array.isArray(state.catalogRaw)) candidates.push(...state.catalogRaw)
    return candidates.find((item) => String(item && item.pack_id || "").trim() === selectedPackId) || null
  }

  function catalogRowHasRuntime(item) {
    if (!item || typeof item !== "object") return false
    return item.runtime_available !== false
  }

  function updateCatalogDetailActions() {
    const selected = selectedCatalogRow()
    const compareButton = byId("btnMarketCatalogCompare")
    const downloadButton = byId("btnMarketCatalogDownload")
    const downloadUrl = catalogPackageUrl(selected)
    const runtimeAvailable = selected && catalogRowHasRuntime(selected) && hasCapability("profile_pack.catalog.read")

    if (compareButton) {
      compareButton.disabled = !runtimeAvailable
      compareButton.setAttribute("aria-disabled", runtimeAvailable ? "false" : "true")
      if (!runtimeAvailable) {
        compareButton.title = i18nMessage(
          "market.compare.runtime_unavailable",
          "Runtime compare is available only for locally published packs.",
        )
      } else {
        compareButton.removeAttribute("title")
      }
    }

    if (downloadButton) {
      const visible = Boolean(downloadUrl)
      downloadButton.classList.toggle("hidden", !visible)
      downloadButton.disabled = !visible
      downloadButton.setAttribute("aria-disabled", visible ? "false" : "true")
      downloadButton.dataset.downloadUrl = downloadUrl
    }
  }

  function triggerCatalogDownload(item = selectedCatalogRow()) {
    const url = catalogPackageUrl(item)
    if (!url) {
      updateSummary({
        status: "download_unavailable",
        message: i18nMessage(
          "market.download.unavailable",
          "No public download is available for this catalog row.",
        ),
        ...(item && typeof item === "object" ? item : {}),
      })
      return
    }
    if (globalScope && typeof globalScope.open === "function") {
      globalScope.open(url, "_blank", "noopener,noreferrer")
      return
    }
    if (globalScope && globalScope.location) {
      globalScope.location.href = url
    }
  }

  function fallbackCapabilityOperations(role) {
    const normalized = String(role || "").trim().toLowerCase()
    const base = [
      "auth.info.read",
      "auth.login",
      "health.read",
      "ui.capabilities.read",
    ]
    const member = [
      "member.installations.read",
      "member.installations.refresh",
      "member.submissions.read",
      "member.submissions.detail.read",
      "member.profile_pack.submissions.read",
      "member.profile_pack.submissions.detail.read",
      "member.profile_pack.submissions.export.download",
      "templates.trial.request",
      "templates.install",
      "templates.submit",
      "profile_pack.catalog.read",
      "profile_pack.community.submit",
      "notifications.read",
    ]
    if (normalized === "admin" || normalized === "reviewer" || normalized === "member") {
      return Array.from(new Set([...base, ...member]))
    }
    return base
  }

  function hasCapability(capability) {
    const required = String(capability || "").trim()
    if (!required) return true
    const operations = Array.isArray(state.capabilities.operations)
      ? state.capabilities.operations
      : []
    return operations.includes(required)
  }

  function applyCapabilityGuardToControl(controlId) {
    const required = CONTROL_CAPABILITY_MAP[controlId] || ""
    if (!required) return
    const node = byId(controlId)
    if (!node) return
    const allowed = hasCapability(required)
    node.classList.toggle("capability-blocked", !allowed)
    node.setAttribute("aria-disabled", allowed ? "false" : "true")
    if ("disabled" in node) {
      node.disabled = !allowed
    }
    if (allowed) {
      node.removeAttribute("title")
      return
    }
    node.title = i18nFormat(
      "capability.locked_hint",
      "Requires capability: {capability}",
      { capability: required },
    )
  }

  function applyCapabilityGuards() {
    Object.keys(CONTROL_CAPABILITY_MAP).forEach((controlId) => {
      applyCapabilityGuardToControl(controlId)
    })
    syncMarketProfilePackSubmissionActions()
  }

  function setCapabilities(payload) {
    const data = payload && typeof payload === "object" ? payload : {}
    const role = String(data.role || "member").trim().toLowerCase() || "member"
    const operations = Array.isArray(data.operations)
      ? data.operations.map((item) => String(item || "").trim()).filter(Boolean)
      : fallbackCapabilityOperations(role)
    state.capabilities = {
      role,
      operations: Array.from(new Set(operations)),
    }
    applyCapabilityGuards()
  }

  async function refreshCapabilities() {
    const query = {}
    if (!state.authRequired) {
      query.role = fixedAuthRole()
    }
    const response = await api(`/api/ui/capabilities${queryString(query)}`)
    if (!response || response.status >= 400 || !(response.data && response.data.ok)) {
      setCapabilities({
        role: state.authRequired ? "public" : fixedAuthRole(),
        operations: fallbackCapabilityOperations(
          state.authRequired ? "public" : fixedAuthRole(),
        ),
      })
      return response
    }
    setCapabilities(response.data)
    return response
  }

  function renderLog(name, payload) {
    const node = byId("marketResult")
    const line = `[${new Date().toISOString()}] ${name}\n${JSON.stringify(payload, null, 2)}\n\n`
    node.textContent = line + node.textContent
  }

  function clearChildren(node) {
    if (!node) return
    node.innerHTML = ""
  }

  function setFilterDrawerOpen(open) {
    const nextState = Boolean(open)
    state.filterDrawerOpen = nextState
    const sidebar = byId("marketFilterSidebar")
    const overlay = byId("marketFilterOverlay")
    const toggleButton = byId("btnMarketOpenFilterDrawer")
    if (sidebar) {
      sidebar.classList.toggle("is-drawer-open", nextState)
      sidebar.setAttribute("aria-hidden", nextState ? "false" : "true")
    }
    if (overlay) {
      overlay.classList.toggle("hidden", !nextState)
      overlay.classList.toggle("is-active", nextState)
      overlay.setAttribute("aria-hidden", nextState ? "false" : "true")
    }
    if (toggleButton) {
      toggleButton.setAttribute("aria-expanded", nextState ? "true" : "false")
    }
    document.body.classList.toggle("market-filter-drawer-open", nextState)
  }

  function setMarketLogExpanded(open) {
    const nextState = Boolean(open)
    state.logExpanded = nextState
    const panel = byId("marketLogArea")
    if (panel) {
      panel.classList.toggle("hidden", !nextState)
      panel.setAttribute("aria-hidden", nextState ? "false" : "true")
    }
    const button = byId("btnMarketToggleLog")
    if (button) {
      button.setAttribute("aria-expanded", nextState ? "true" : "false")
      button.textContent = nextState
        ? i18nMessage("market.log.toggle_hide", "Hide Operation Log")
        : i18nMessage("market.log.toggle_show", "Show Operation Log")
    }
  }

  function setMarketDetailExpanded(open) {
    const nextState = Boolean(open)
    state.detailExpanded = nextState
    const area = byId("marketDetailArea")
    if (area) {
      area.classList.toggle("hidden", !nextState)
      area.setAttribute("aria-hidden", nextState ? "false" : "true")
    }
    const panel = byId("marketDetailPanel")
    if (!panel) return
    panel.open = nextState
    panel.setAttribute("aria-expanded", nextState ? "true" : "false")
  }

  function normalizeFacetValue(groupKey, value) {
    const text = String(value || "").trim()
    if (!text) {
      return "unknown"
    }
    if (groupKey === "featured") {
      if (text === "true" || text === "1" || text === "yes") return "true"
      return "false"
    }
    return text
  }

  function facetValuesForItem(item, groupKey) {
    if (!item || typeof item !== "object") return ["unknown"]
    if (groupKey === "pack_type") {
      return [normalizeFacetValue(groupKey, item.pack_type)]
    }
    if (groupKey === "risk_level") {
      return [normalizeFacetValue(groupKey, item.risk_level)]
    }
    if (groupKey === "featured") {
      return [item.featured ? "true" : "false"]
    }
    if (groupKey === "compatibility") {
      return [normalizeFacetValue(groupKey, item.compatibility)]
    }
    if (groupKey === "review_label") {
      const labels = Array.isArray(item.review_labels) ? item.review_labels : []
      return labels.length ? labels.map((entry) => normalizeFacetValue(groupKey, entry)) : ["unknown"]
    }
    if (groupKey === "warning_flag") {
      const flags = Array.isArray(item.warning_flags) ? item.warning_flags : []
      return flags.length ? flags.map((entry) => normalizeFacetValue(groupKey, entry)) : ["unknown"]
    }
    return ["unknown"]
  }

  function marketRowSearchText(item) {
    if (!item || typeof item !== "object") return ""
    const labels = Array.isArray(item.review_labels) ? item.review_labels.join(" ") : ""
    const flags = Array.isArray(item.warning_flags) ? item.warning_flags.join(" ") : ""
    const issues = Array.isArray(item.compatibility_issues) ? item.compatibility_issues.join(" ") : ""
    const source = String(item.source_submission_id || "")
    const packId = String(item.pack_id || "")
    const packType = String(item.pack_type || "")
    const risk = String(item.risk_level || "")
    const compatibility = String(item.compatibility || "")
    const version = String(item.version || "")
    return [packId, packType, risk, compatibility, labels, flags, issues, source, version]
      .join(" ")
      .toLowerCase()
  }

  function rowMatchesSearch(item, searchTerm) {
    const term = String(searchTerm || "").trim().toLowerCase()
    if (!term) return true
    return marketRowSearchText(item).includes(term)
  }

  function rowMatchesFacets(item, excludedGroup = "") {
    return LOCAL_FACET_GROUPS.every((group) => {
      if (group.key === excludedGroup) return true
      const selectedSet = state.localFacets[group.key]
      if (!selectedSet || selectedSet.size === 0) return true
      const values = facetValuesForItem(item, group.key)
      return values.some((value) => selectedSet.has(value))
    })
  }

  function hasActiveLocalFilters() {
    const hasSearch = String(state.localSearch || "").trim() !== ""
    if (hasSearch) return true
    return LOCAL_FACET_GROUPS.some((group) => {
      const selectedSet = state.localFacets[group.key]
      return Boolean(selectedSet && selectedSet.size > 0)
    })
  }

  function sortCatalogRows(rows) {
    const items = Array.isArray(rows) ? rows.slice() : []
    const mode = String(state.localSort || LOCAL_SORT_OPTIONS.TRENDING)
    if (mode === LOCAL_SORT_OPTIONS.DOWNLOADS) {
      return items.sort((left, right) => {
        const leftCount = Number(left && left.engagement && left.engagement.installs || 0)
        const rightCount = Number(right && right.engagement && right.engagement.installs || 0)
        if (rightCount !== leftCount) return rightCount - leftCount
        return catalogRankScore(right) - catalogRankScore(left)
      })
    }
    if (mode === LOCAL_SORT_OPTIONS.RECENT) {
      return items.sort((left, right) => {
        const leftTime = parseIsoDate(left && (left.featured_at || left.published_at))
        const rightTime = parseIsoDate(right && (right.featured_at || right.published_at))
        if (rightTime !== leftTime) return rightTime - leftTime
        return catalogRankScore(right) - catalogRankScore(left)
      })
    }
    return items.sort((left, right) => {
      const scoreDiff = catalogRankScore(right) - catalogRankScore(left)
      if (scoreDiff !== 0) return scoreDiff
      const leftTime = parseIsoDate(left && (left.featured_at || left.published_at))
      const rightTime = parseIsoDate(right && (right.featured_at || right.published_at))
      if (rightTime !== leftTime) return rightTime - leftTime
      return String(left && left.pack_id || "").localeCompare(String(right && right.pack_id || ""))
    })
  }

  function updateCatalogCountChips(visibleRows, totalRows) {
    const visible = Array.isArray(visibleRows) ? visibleRows.length : 0
    const total = Array.isArray(totalRows) ? totalRows.length : 0
    const totalNode = byId("marketTotalCount")
    if (totalNode) {
      totalNode.textContent = String(total)
    }
    const resultNode = byId("marketResultCount")
    if (resultNode) {
      resultNode.textContent = String(visible)
    }
  }

  function sortedFacetEntries(group, bucket) {
    const entries = Array.from(bucket.entries())
    const order = Array.isArray(group.ordered) ? group.ordered : []
    if (order.length) {
      entries.sort((left, right) => {
        const leftIndex = order.indexOf(left[0])
        const rightIndex = order.indexOf(right[0])
        const normalizedLeft = leftIndex >= 0 ? leftIndex : Number.MAX_SAFE_INTEGER
        const normalizedRight = rightIndex >= 0 ? rightIndex : Number.MAX_SAFE_INTEGER
        if (normalizedLeft !== normalizedRight) return normalizedLeft - normalizedRight
        if (right[1] !== left[1]) return right[1] - left[1]
        return String(left[0]).localeCompare(String(right[0]))
      })
      return entries
    }
    return entries.sort((left, right) => {
      if (right[1] !== left[1]) return right[1] - left[1]
      return String(left[0]).localeCompare(String(right[0]))
    })
  }

  function completeFacetBucket(group, bucket) {
    const out = new Map(bucket instanceof Map ? bucket.entries() : [])
    const seeded = Array.isArray(group.seeded) ? group.seeded : []
    seeded.forEach((value) => {
      const normalized = normalizeFacetValue(group.key, value)
      if (!normalized) return
      if (!out.has(normalized)) {
        out.set(normalized, 0)
      }
    })
    const selected = state.localFacets[group.key]
    if (selected instanceof Set) {
      selected.forEach((value) => {
        const normalized = normalizeFacetValue(group.key, value)
        if (!normalized) return
        if (!out.has(normalized)) {
          out.set(normalized, 0)
        }
      })
    }
    return out
  }

  function computeFacetBuckets(rows) {
    const bucket = {}
    LOCAL_FACET_GROUPS.forEach((group) => {
      const counts = new Map()
      const scopedRows = Array.isArray(rows)
        ? rows.filter((item) => rowMatchesFacets(item, group.key))
        : []
      scopedRows.forEach((item) => {
        facetValuesForItem(item, group.key).forEach((value) => {
          counts.set(value, (counts.get(value) || 0) + 1)
        })
      })
      bucket[group.key] = counts
    })
    return bucket
  }

  function buildFacetRenderModel(rows) {
    const buckets = computeFacetBuckets(rows)
    const facetView = marketFacetViewHelpers()
    if (facetView && typeof facetView.buildFacetRenderModel === "function") {
      return facetView.buildFacetRenderModel({
        groups: LOCAL_FACET_GROUPS,
        buckets,
        facetSelection: state.localFacets,
        completeFacetBucket: (group, bucket) => completeFacetBucket(group, bucket),
        sortedFacetEntries: (group, bucket) => sortedFacetEntries(group, bucket),
        i18nMessage,
        enumLabel,
      })
    }
    return LOCAL_FACET_GROUPS.map((group) => {
      const entries = sortedFacetEntries(group, completeFacetBucket(group, buckets[group.key] || new Map()))
      return {
        key: group.key,
        title: i18nMessage(group.titleKey, group.titleFallback),
        entries: entries.map(([value, count]) => ({
          value: String(value),
          count: Number(count || 0),
          checked: Boolean(state.localFacets[group.key] && state.localFacets[group.key].has(value)),
          label: String(value),
        })),
      }
    })
  }

  function applyLocalCatalogView(options = {}) {
    const baseRows = Array.isArray(state.catalogRaw) ? state.catalogRaw : []
    let searchedRows = baseRows.filter((item) => rowMatchesSearch(item, state.localSearch))
    let sortedRows = sortCatalogRows(searchedRows.filter((item) => rowMatchesFacets(item)))
    if (marketFilterApi && typeof marketFilterApi.buildLocalCatalogView === "function") {
      const computed = marketFilterApi.buildLocalCatalogView(baseRows, {
        localSearch: state.localSearch,
        localFacets: state.localFacets,
        localSort: state.localSort,
      }, {
        groups: LOCAL_FACET_GROUPS,
        catalogRankScore,
        parseIsoDate,
      })
      searchedRows = computed.searchedRows
      sortedRows = computed.sortedRows
    }
    state.catalog = sortedRows
    updateCatalogTable(state.catalog, { skipFilterSync: true })
    updateCatalogCountChips(state.catalog, baseRows)
    renderFacetFilters(searchedRows)
    syncQueryState()
    if (options.updateSummary !== false && state.catalogRaw.length > 0) {
      setCatalogState(
        "success",
        i18nFormat(
          "market.catalog.filtered",
          "Showing {shown} of {total} profile packs.",
          { shown: state.catalog.length, total: state.catalogRaw.length },
        ),
      )
    }
  }

  function onFacetToggle(groupKey, value, checked) {
    const normalizedKey = String(groupKey || "")
    const normalizedValue = String(value || "")
    const bucket = state.localFacets[normalizedKey]
    if (!bucket || !(bucket instanceof Set)) return
    if (checked) {
      bucket.add(normalizedValue)
    } else {
      bucket.delete(normalizedValue)
    }
    applyLocalCatalogView()
  }

  function renderFacetFilters(rows) {
    const root = byId("marketFacetFilters")
    if (!root) return
    const model = buildFacetRenderModel(rows)
    const facetView = marketFacetViewHelpers()
    if (facetView && typeof facetView.renderFacetRenderModel === "function") {
      facetView.renderFacetRenderModel(root, model, onFacetToggle, {
        document,
        emptyText: i18nMessage("market.filter.group_empty", "No values"),
      })
      return
    }

    root.innerHTML = ""
    model.forEach((group) => {
      const detail = document.createElement("details")
      detail.className = "market-facet-group"
      detail.open = true
      const summary = document.createElement("summary")
      summary.className = "market-facet-title"
      summary.textContent = String(group.title || "")
      detail.appendChild(summary)
      const list = document.createElement("div")
      list.className = "market-facet-list"
      const entries = Array.isArray(group.entries) ? group.entries : []
      if (!entries.length) {
        const empty = document.createElement("div")
        empty.className = "market-facet-empty"
        empty.textContent = i18nMessage("market.filter.group_empty", "No values")
        list.appendChild(empty)
      } else {
        entries.forEach((entry) => {
          const row = document.createElement("label")
          row.className = "market-facet-option"
          const checkbox = document.createElement("input")
          checkbox.type = "checkbox"
          checkbox.checked = Boolean(entry.checked)
          checkbox.setAttribute("data-market-facet-group", String(group.key || ""))
          checkbox.setAttribute("data-market-facet-value", String(entry.value || ""))
          checkbox.addEventListener("change", () => {
            onFacetToggle(String(group.key || ""), String(entry.value || ""), checkbox.checked)
          })
          row.appendChild(checkbox)
          const label = document.createElement("span")
          label.className = "market-facet-option-label"
          label.textContent = String(entry.label || entry.value || "")
          row.appendChild(label)
          const badge = document.createElement("span")
          badge.className = "market-facet-option-count"
          badge.textContent = String(Number.isFinite(Number(entry.count)) ? Number(entry.count) : 0)
          row.appendChild(badge)
          list.appendChild(row)
        })
      }
      detail.appendChild(list)
      root.appendChild(detail)
    })
  }

  function setCatalogState(status, message) {
    const node = byId("marketCatalogState")
    node.classList.remove("is-neutral", "is-warning", "is-danger", "is-success")
    if (status === "loading") {
      node.classList.add("is-warning")
    } else if (status === "error") {
      node.classList.add("is-danger")
    } else if (status === "success") {
      node.classList.add("is-success")
    } else {
      node.classList.add("is-neutral")
    }
    node.textContent = message
  }

  function updateHealthUi() {
    const status = state.health && state.health.status !== undefined ? String(state.health.status) : "loading"
    const url = state.health && state.health.data && state.health.data.webui_url
      ? String(state.health.data.webui_url)
      : ""
    byId("marketHealthLine").textContent = i18nFormat(
      "market.health.line",
      "health: {status} {url}",
      { status, url },
    ).trim()
  }

  function updateSummary(data) {
    const summaryNode = byId("marketSummary")
    const detailsNode = byId("marketDetails")
    if (!data || typeof data !== "object") {
      state.lastSummary = null
      const statusView = marketStatusViewHelpers()
      if (statusView && typeof statusView.buildSummaryText === "function") {
        summaryNode.textContent = statusView.buildSummaryText(null, { i18nMessage, i18nFormat })
      } else {
        summaryNode.textContent = i18nMessage("market.summary.idle", "No operation yet.")
      }
      detailsNode.textContent = ""
      renderEvidence(null)
      return
    }
    state.lastSummary = data
    const statusView = marketStatusViewHelpers()
    if (statusView && typeof statusView.buildSummaryText === "function") {
      summaryNode.textContent = statusView.buildSummaryText(data, {
        i18nMessage,
        i18nFormat,
        enumLabel,
        localizedPackLabel,
      })
    } else {
      summaryNode.textContent = i18nFormat("market.summary.part.status", "status={value}", {
        value: enumLabel("status", String(data.status || "updated")),
      })
    }
    renderEvidence(data)
    detailsNode.textContent = JSON.stringify(data, null, 2)
  }

  function renderEvidence(data) {
    const node = byId("marketEvidenceRows")
    if (!node) return
    node.innerHTML = ""
    if (!data || typeof data !== "object") return
    const statusView = marketStatusViewHelpers()
    if (statusView && typeof statusView.buildEvidenceRows === "function") {
      const rows = statusView.buildEvidenceRows(data, {
        i18nMessage,
        i18nFormat,
        enumLabel,
        localizedPackFeaturedNote,
        localizedList,
        summarizePluginInstallExecution:
          compareViewHelper && typeof compareViewHelper.summarizePluginInstallExecution === "function"
            ? (execution) => compareViewHelper.summarizePluginInstallExecution(execution)
            : null,
      })
      if (typeof statusView.renderDetailCards === "function") {
        statusView.renderDetailCards(node, rows, { document })
        return
      }
    }

    const fallback = document.createElement("div")
    fallback.className = "detail-card"
    const label = document.createElement("div")
    label.className = "detail-card-label"
    label.textContent = i18nMessage("market.evidence.plugin_install_status", "plugin install status")
    fallback.appendChild(label)
    const value = document.createElement("div")
    value.className = "detail-card-value"
    value.textContent = enumLabel("plugin_install_status", String(data.plugin_install && data.plugin_install.status || "unknown"))
    fallback.appendChild(value)
    node.appendChild(fallback)
  }

  function resetCompareView() {
    state.lastComparePayload = null
    state.compareDetailKey = ""
    const shell = byId("marketCompareShell")
    if (!shell) return
    shell.classList.add("hidden")
    const highlights = byId("marketCompareHighlights")
    const warnings = byId("marketCompareWarnings")
    const cards = byId("marketCompareCards")
    const tableBody = byId("marketCompareTable").querySelector("tbody")
    highlights.innerHTML = ""
    warnings.innerHTML = ""
    cards.innerHTML = ""
    tableBody.innerHTML = ""
    resetCompareDetailPane()
  }

  function renderCompareView(payload) {
    state.lastComparePayload = payload || null
    if (!compareViewHelper || typeof compareViewHelper.buildProfilePackCompareView !== "function") {
      resetCompareView()
      return
    }

    const view = compareViewHelper.buildProfilePackCompareView(payload, {
      t: i18nMessage,
      f: i18nFormat,
      resolvePackLabel: (packId) => {
        const id = String(packId || "").trim()
        if (!id) return "-"
        return localizedPackLabel(id)
      },
    })
    const shell = byId("marketCompareShell")
    if (!shell) return
    if (view.empty) {
      shell.classList.add("hidden")
      return
    }
    shell.classList.remove("hidden")

    const highlights = byId("marketCompareHighlights")
    highlights.innerHTML = ""
    ;(view.highlights || []).forEach((item) => appendPill(highlights, item.label, item.tone || "neutral"))

    const warnings = byId("marketCompareWarnings")
    warnings.innerHTML = ""
    ;(view.warnings || []).forEach((item) => {
      const entry = document.createElement("div")
      entry.className = "warning-item"
      if (item.tone === "danger") {
        entry.classList.add("warning-item-danger")
      }
      entry.textContent = item.message
      warnings.appendChild(entry)
    })

    const cards = byId("marketCompareCards")
    cards.innerHTML = ""
    ;(view.cards || []).forEach((item) => {
      const card = document.createElement("div")
      card.className = "detail-card"

      const label = document.createElement("div")
      label.className = "detail-card-label"
      label.textContent = item.label
      card.appendChild(label)

      const value = document.createElement("div")
      value.className = "detail-card-value"
      value.textContent = item.value
      card.appendChild(value)

      if (item.tone && item.tone !== "neutral") {
        const toneRow = document.createElement("div")
        toneRow.className = "pill-row"
        appendPill(toneRow, item.tone, item.tone)
        card.appendChild(toneRow)
      }

      cards.appendChild(card)
    })

    const tableBody = byId("marketCompareTable").querySelector("tbody")
    tableBody.innerHTML = ""
    ;(view.sections || []).forEach((item) => {
      const tr = document.createElement("tr")
      tr.appendChild(textCell(item.section))
      tr.appendChild(compareChangedCell(item))
      tr.appendChild(compareChangeSummaryCell(item))
      tr.appendChild(compareSizeCell(item))
      tableBody.appendChild(tr)
    })
    if (state.compareDetailKey) {
      const selected = (view.sections || []).find((item) => String(item.section || "") === state.compareDetailKey)
      if (selected) {
        renderCompareDetailPane(selected)
      } else {
        resetCompareDetailPane()
      }
    } else {
      resetCompareDetailPane()
    }

    byId("marketSummary").textContent = view.summary
  }

  function applyAuthOptions(roles) {
    const roleNode = byId("marketAuthRole")
    if (!roleNode) return
    roleNode.innerHTML = ""
    const preferredRole = fixedAuthRole()
    const authView = marketAuthViewHelpers()
    const options = authView && typeof authView.buildAuthRoleOptions === "function"
      ? authView.buildAuthRoleOptions(roles, preferredRole, { i18nMessage })
      : [{ value: preferredRole, label: i18nMessage("option.member", "member"), i18nKey: "option.member" }]
    options.forEach((entry) => {
      const option = document.createElement("option")
      option.value = String(entry.value || preferredRole)
      if (entry.i18nKey) {
        option.setAttribute("data-i18n-key", String(entry.i18nKey))
      }
      option.textContent = String(entry.label || entry.value || preferredRole)
      roleNode.appendChild(option)
    })
    roleNode.value = preferredRole
    roleNode.disabled = true
    syncReviewerAuthFields()
  }

  function syncReviewerAuthFields() {
    const roleNode = byId("marketAuthRole")
    const fieldsNode = byId("marketReviewerAuthFields")
    if (!roleNode || !fieldsNode) return
    const authView = marketAuthViewHelpers()
    const role = String(roleNode.value || "").trim()
    const visible = authView && typeof authView.isReviewerRole === "function"
      ? authView.isReviewerRole(role)
      : role.toLowerCase() === "reviewer"
    fieldsNode.classList.toggle("hidden", !visible)
  }

  function updateAuthUi() {
    const rolesText = state.availableRoles.length ? state.availableRoles.join(", ") : "none"
    byId("marketAuthLine").textContent = i18nFormat(
      "market.auth.line",
      "auth: {status}",
      {
        status: state.authRequired
          ? i18nFormat("auth.status.required", "required ({roles})", { roles: rolesText })
          : i18nMessage("auth.status.disabled", "disabled"),
      },
    )
    byId("marketRoleLine").textContent = i18nFormat(
      "market.role.line",
      "role: {role}",
      {
        role: state.authRole || i18nMessage("market.role.not_logged_in", "not logged in"),
      },
    )
    byId("marketAuthPanel").classList.toggle("hidden", !state.authRequired)
    const authUserIdNode = byId("marketAuthUserId")
    if (authUserIdNode) {
      authUserIdNode.value = String(state.memberUserId || "webui-user").trim() || "webui-user"
    }
    syncReviewerAuthFields()
    updateConsoleLinkVisibility()
    applyCapabilityGuards()
  }

  function updateConsoleLinkVisibility() {
    const memberLink = byId("marketMemberConsoleLink")
    const reviewerLink = byId("marketReviewerConsoleLink")
    const adminLink = byId("marketAdminConsoleLink")
    const fullLink = byId("marketFullConsoleLink")
    const authView = marketAuthViewHelpers()
    if (authView && typeof authView.resolveConsoleVisibility === "function" && typeof authView.applyConsoleVisibility === "function") {
      const visibility = authView.resolveConsoleVisibility(state.authRequired, state.authRole)
      authView.applyConsoleVisibility(
        {
          member: memberLink,
          reviewer: reviewerLink,
          admin: adminLink,
          full: fullLink,
        },
        visibility,
      )
      return
    }
    const hide = (node, value) => {
      if (!node) return
      node.classList.toggle("hidden", Boolean(value))
    }
    if (!state.authRequired) {
      hide(memberLink, false)
      hide(reviewerLink, true)
      hide(adminLink, true)
      hide(fullLink, true)
      return
    }
    const role = String(state.authRole || "member").trim().toLowerCase()
    if (role === "admin") {
      hide(memberLink, false)
      hide(reviewerLink, false)
      hide(adminLink, false)
      hide(fullLink, false)
      return
    }
    if (role === "reviewer") {
      hide(memberLink, false)
      hide(reviewerLink, false)
      hide(adminLink, true)
      hide(fullLink, true)
      return
    }
    hide(memberLink, false)
    hide(reviewerLink, true)
    hide(adminLink, true)
    hide(fullLink, true)
  }

  async function refreshHealth() {
    const response = await api("/api/health")
    state.health = response
    updateHealthUi()
  }

  async function initAuth() {
    const response = await api("/api/auth-info")
    state.authRequired = Boolean(response.data.auth_required)
    state.availableRoles = Array.isArray(response.data.available_roles) ? response.data.available_roles : []
    applyAuthOptions(state.availableRoles)
    if (!state.authRequired) {
      state.token = "no-auth"
      state.authRole = "member"
      state.memberUserId = String(byId("marketAuthUserId")?.value || "webui-user").trim() || "webui-user"
    }
    updateAuthUi()
    await refreshCapabilities()
  }

  async function login() {
    const role = fixedAuthRole()
    const password = byId("marketAuthPassword").value
    const body = { role, password }
    if (role === "member") {
      body.user_id = String(byId("marketAuthUserId")?.value || "webui-user").trim() || "webui-user"
    }
    if (role === "reviewer") {
      body.reviewer_id = String(byId("marketAuthReviewerId")?.value || "").trim()
      body.reviewer_device_key = String(byId("marketAuthReviewerDeviceKey")?.value || "").trim()
    }
    const response = await api("/api/login", {
      method: "POST",
      body,
    })
    renderLog("login", response)
    if (!response.data.ok) {
      updateSummary({
        status: "error",
        message: response.data.message || i18nMessage("market.error.login_failed", "login failed"),
      })
      return
    }
    state.token = String(response.data.token || "")
    state.authRole = String(response.data.role || role)
    if (state.authRole === "member") {
      state.memberUserId = String(response.data.user_id || body.user_id || state.memberUserId || "webui-user").trim() || "webui-user"
    }
    state.availableRoles = Array.isArray(response.data.available_roles)
      ? response.data.available_roles
      : state.availableRoles
    applyAuthOptions(state.availableRoles)
    updateAuthUi()
    await refreshCapabilities()
    if (hasCapability("profile_pack.catalog.read")) {
      await listCatalog()
    }
  }

  function normalizeList(value) {
    return String(value || "")
      .split(",")
      .map((item) => String(item || "").trim())
      .filter(Boolean)
  }

  function marketActor() {
    return {
      user_id: String(state.memberUserId || "webui-user").trim() || "webui-user",
      session_id: "market-session",
    }
  }

  function readFileAsBase64(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onerror = () => reject(new Error("file_read_failed"))
      reader.onload = () => {
        const result = String(reader.result || "")
        const parts = result.split(",", 2)
        resolve(parts.length === 2 ? parts[1] : result)
      }
      reader.readAsDataURL(file)
    })
  }

  const UPLOAD_LIMIT_BYTES = 20 * 1024 * 1024

  function uploadLimitLabel() {
    return "20 MiB"
  }

  function assertUploadFileAllowed(file) {
    if (!file) return
    const size = Number(file.size || 0)
    if (size <= UPLOAD_LIMIT_BYTES) return
    throw new Error("package_too_large")
  }

  function uploadTooLargeMessage() {
    return i18nFormat(
      "upload.error.package_too_large",
      "Package exceeds the {limit} limit.",
      { limit: uploadLimitLabel() },
    )
  }

  function readMarketInstallOptions() {
    return {
      preflight: Boolean(byId("marketInstallPreflight") && byId("marketInstallPreflight").checked),
      force_reinstall: Boolean(byId("marketInstallForceReinstall") && byId("marketInstallForceReinstall").checked),
      source_preference: String(byId("marketInstallSourcePreference")?.value || "auto").trim() || "auto",
    }
  }

  function readMarketUploadOptions() {
    return {
      scan_mode: String(byId("marketUploadScanMode")?.value || "balanced").trim() || "balanced",
      visibility: String(byId("marketUploadVisibility")?.value || "community").trim() || "community",
      replace_existing: Boolean(byId("marketUploadReplaceExisting") && byId("marketUploadReplaceExisting").checked),
    }
  }

  function readMarketSubmitOptions() {
    return {
      pack_type: String(byId("marketSubmitPackType")?.value || "bot_profile_pack").trim() || "bot_profile_pack",
      selected_sections: normalizeList(byId("marketSubmitSelectedSections")?.value || ""),
      redaction_mode: String(byId("marketSubmitRedactionMode")?.value || "exclude_secrets").trim() || "exclude_secrets",
      replace_existing: Boolean(
        byId("marketSubmitReplaceExisting") && byId("marketSubmitReplaceExisting").checked
      ),
    }
  }

  function setMarketInstallationsState(status, message) {
    setCollectionState("marketInstallationsState", status, message)
  }

  function setCollectionState(nodeId, status, message) {
    const node = byId(nodeId)
    if (!node) return
    node.classList.remove("is-neutral", "is-warning", "is-danger", "is-success")
    if (status === "loading" || status === "warning") node.classList.add("is-warning")
    else if (status === "error") node.classList.add("is-danger")
    else if (status === "success") node.classList.add("is-success")
    else node.classList.add("is-neutral")
    node.textContent = message
  }

  function setMarketTemplateSubmissionsState(status, message) {
    setCollectionState("marketSubmissionsState", status, message)
  }

  function setMarketProfilePackSubmissionsState(status, message) {
    setCollectionState("marketProfilePackSubmissionsState", status, message)
  }

  function selectedProfilePackSubmissionId() {
    const selected = String(state.selectedProfilePackSubmissionId || "").trim()
    if (selected) return selected
    const first = Array.isArray(state.memberProfilePackSubmissions) ? state.memberProfilePackSubmissions[0] : null
    return String((first && (first.submission_id || first.id)) || "").trim()
  }

  function syncMarketProfilePackSubmissionActions() {
    const button = byId("btnMarketDownloadProfilePackSubmission")
    if (!button) return
    const required = "member.profile_pack.submissions.export.download"
    const allowed = hasCapability(required)
    const submissionId = selectedProfilePackSubmissionId()
    const enabled = allowed && Boolean(submissionId)
    button.disabled = !enabled
    button.setAttribute("aria-disabled", enabled ? "false" : "true")
    if (!allowed) {
      button.title = i18nFormat(
        "capability.locked_hint",
        "Requires capability: {capability}",
        { capability: required },
      )
      return
    }
    if (!submissionId) {
      button.title = i18nMessage("moderation.no_selection", "No submission selected.")
      return
    }
    button.removeAttribute("title")
  }

  function updateSelectedFileName(inputId, outputId, emptyKey, emptyFallback) {
    const input = byId(inputId)
    const output = byId(outputId)
    if (!input || !output) return
    const file = input.files && input.files[0] ? input.files[0] : null
    output.textContent = file
      ? String(file.name || file.type || "package")
      : i18nMessage(emptyKey, emptyFallback)
  }

  function bindUploadDropZone({ zoneId, inputId, outputId, emptyKey, emptyFallback }) {
    const zone = byId(zoneId)
    const input = byId(inputId)
    if (!zone || !input) return
    const resetDragging = () => {
      zone.classList.remove("is-dragging")
    }
    const syncFileName = () => {
      updateSelectedFileName(inputId, outputId, emptyKey, emptyFallback)
    }
    input.addEventListener("change", syncFileName)
    ;["dragenter", "dragover"].forEach((eventName) => {
      zone.addEventListener(eventName, (event) => {
        event.preventDefault()
        zone.classList.add("is-dragging")
      })
    })
    ;["dragleave", "dragend"].forEach((eventName) => {
      zone.addEventListener(eventName, resetDragging)
    })
    zone.addEventListener("drop", (event) => {
      event.preventDefault()
      resetDragging()
      const files = event.dataTransfer && event.dataTransfer.files ? event.dataTransfer.files : null
      if (!files || !files.length) return
      try {
        const transfer = new DataTransfer()
        Array.from(files).forEach((file) => transfer.items.add(file))
        input.files = transfer.files
        syncFileName()
      } catch (_error) {
        syncFileName()
      }
    })
    syncFileName()
  }

  function renderMarketInstallations(rows) {
    const root = byId("marketInstallationsList")
    if (!root) return
    root.innerHTML = ""
    const items = Array.isArray(rows) ? rows : []
    if (!items.length) {
      root.textContent = i18nMessage("member.installations.empty", "No local installations yet.")
      return
    }
    items.forEach((item) => {
      const button = document.createElement("button")
      button.type = "button"
      button.className = "member-install-item"
      const title = document.createElement("strong")
      title.textContent = String(item.template_id || "-")
      button.appendChild(title)
      const version = String(item.version || "-")
      const risk = enumLabel("risk", String(item.risk_level || "unknown"))
      const installedAt = String(item.installed_at || "-")
      const meta = document.createElement("span")
      meta.textContent = i18nFormat(
        "member.installations.meta",
        "v{version} · {risk} · {installed_at}",
        {
          version,
          risk,
          installed_at: installedAt,
        },
      )
      button.appendChild(meta)
      button.addEventListener("click", () => {
        const templateNode = byId("marketTemplateId")
        if (templateNode) {
          templateNode.value = String(item.template_id || "")
        }
      })
      root.appendChild(button)
    })
  }

  async function loadMarketInstallations(options = {}) {
    if (!hasCapability("member.installations.read")) {
      setMarketInstallationsState(
        "warning",
        i18nFormat(
          "capability.locked_hint",
          "Requires capability: {capability}",
          { capability: "member.installations.read" },
        ),
      )
      return
    }
    const shouldRefresh = Boolean(options.refresh)
    const actor = marketActor()
    setMarketInstallationsState(
      "loading",
      i18nMessage("member.installations.loading", "Loading local installations..."),
    )
    const response = shouldRefresh
      ? await api("/api/member/installations/refresh", {
        method: "POST",
        body: { user_id: actor.user_id, limit: 50 },
      })
      : await api(`/api/member/installations${queryString({ user_id: actor.user_id, limit: 50 })}`)
    renderLog(shouldRefresh ? "member_installations_refresh" : "member_installations", response)
    if (!response.data.ok) {
      setMarketInstallationsState(
        "error",
        i18nFormat("member.installations.error", "Failed to load installations: {message}", {
          message: String(response.data.message || "request_failed"),
        }),
      )
      return
    }
    const rows = Array.isArray(apiData(response).installations) ? apiData(response).installations : []
    state.memberInstallations = rows
    renderMarketInstallations(rows)
    setMarketInstallationsState(
      rows.length ? "success" : "neutral",
      i18nFormat("member.installations.ready", "Local installations: {count}", {
        count: rows.length,
      }),
    )
  }

  function renderMemberSubmissionList({
    rootId,
    rows,
    emptyKey,
    emptyFallback,
    titleBuilder,
    metaBuilder,
    onSelect,
  }) {
    const root = byId(rootId)
    if (!root) return
    root.innerHTML = ""
    const items = Array.isArray(rows) ? rows : []
    if (!items.length) {
      root.textContent = i18nMessage(emptyKey, emptyFallback)
      return
    }
    items.forEach((item) => {
      const button = document.createElement("button")
      button.type = "button"
      button.className = "member-task-item"
      const title = document.createElement("strong")
      title.textContent = titleBuilder(item)
      button.appendChild(title)
      const meta = document.createElement("span")
      meta.textContent = metaBuilder(item)
      button.appendChild(meta)
      button.addEventListener("click", () => {
        onSelect(item)
      })
      root.appendChild(button)
    })
  }

  function renderMarketTemplateSubmissions(rows) {
    renderMemberSubmissionList({
      rootId: "marketSubmissionsList",
      rows,
      emptyKey: "submissions.empty_unfiltered",
      emptyFallback: "No submissions are available yet.",
      titleBuilder: (item) => {
        const templateId = String(item.template_id || "-").trim() || "-"
        const version = String(item.version || "").trim()
        return version ? `${templateId}@${version}` : templateId
      },
      metaBuilder: (item) => {
        const submissionId = String(item.submission_id || item.id || "-").trim() || "-"
        const status = enumLabel("status", String(item.status || "unknown"))
        const risk = enumLabel("risk", String(item.risk_level || "unknown"))
        return `${submissionId} · ${status} · ${risk}`
      },
      onSelect: (item) => {
        const templateId = String(item.template_id || "").trim()
        const submissionId = String(item.submission_id || item.id || "").trim()
        if (templateId) {
          const node = byId("marketTemplateId")
          if (node) node.value = templateId
        }
        if (submissionId) {
          void loadMarketTemplateSubmissionDetail(submissionId)
        }
      },
    })
  }

  function renderMarketProfilePackSubmissions(rows) {
    renderMemberSubmissionList({
      rootId: "marketProfilePackSubmissionsList",
      rows,
      emptyKey: "profile_pack.market.submissions_empty_unfiltered",
      emptyFallback: "No profile-pack submissions are available yet.",
      titleBuilder: (item) => {
        const packId = String(item.pack_id || "-").trim() || "-"
        const packType = String(item.pack_type || "").trim()
        return packType ? `${packId} (${enumLabel("pack_type", packType)})` : packId
      },
      metaBuilder: (item) => {
        const submissionId = String(item.submission_id || item.id || "-").trim() || "-"
        const status = enumLabel("status", String(item.status || "unknown"))
        const risk = enumLabel("risk", String(item.risk_level || "unknown"))
        return `${submissionId} · ${status} · ${risk}`
      },
      onSelect: (item) => {
        const submissionId = String(item.submission_id || item.id || "").trim()
        state.selectedProfilePackSubmissionId = submissionId
        syncMarketProfilePackSubmissionActions()
        if (submissionId) {
          void loadMarketProfilePackSubmissionDetail(submissionId)
        }
      },
    })
  }

  async function loadMarketTemplateSubmissionDetail(submissionId) {
    const actor = marketActor()
    const sid = String(submissionId || "").trim()
    if (!sid) return
    const response = await api(`/api/member/submissions/detail${queryString({ user_id: actor.user_id, submission_id: sid })}`)
    renderLog("member_submission_detail_market", response)
    if (!response.data.ok) {
      updateSummary({ status: "error", message: response.data.message || "request_failed" })
      return response
    }
    const payload = apiData(response)
    const templateId = String(payload.template_id || "").trim()
    if (templateId) {
      const node = byId("marketTemplateId")
      if (node) node.value = templateId
    }
    updateSummary(payload)
    return response
  }

  async function loadMarketProfilePackSubmissionDetail(submissionId) {
    const actor = marketActor()
    const sid = String(submissionId || "").trim()
    if (!sid) return
    const response = await api(
      `/api/member/profile-pack/submissions/detail${queryString({ user_id: actor.user_id, submission_id: sid })}`,
    )
    renderLog("member_profile_pack_submission_detail_market", response)
    if (!response.data.ok) {
      updateSummary({ status: "error", message: response.data.message || "request_failed" })
      return response
    }
    const payload = apiData(response)
    const packId = String(payload.pack_id || "").trim()
    const artifactId = String(payload.artifact_id || "").trim()
    if (packId) {
      const packNode = byId("marketPackId")
      if (packNode) packNode.value = packId
    }
    if (artifactId) {
      const artifactNode = byId("marketSubmitArtifactId")
      if (artifactNode) artifactNode.value = artifactId
    }
    updateSummary(payload)
    return response
  }

  async function listMarketTemplateSubmissions() {
    if (!hasCapability("member.submissions.read")) {
      setMarketTemplateSubmissionsState(
        "warning",
        i18nFormat(
          "capability.locked_hint",
          "Requires capability: {capability}",
          { capability: "member.submissions.read" },
        ),
      )
      return
    }
    const actor = marketActor()
    setMarketTemplateSubmissionsState(
      "loading",
      i18nMessage("submissions.loading", "Loading submissions..."),
    )
    const response = await api(`/api/member/submissions${queryString({ user_id: actor.user_id })}`)
    renderLog("member_list_submissions_market", response)
    if (!response.data.ok) {
      setMarketTemplateSubmissionsState(
        "error",
        i18nFormat("submissions.error", "Failed to load submissions: {message}", {
          message: String(response.data.message || "request_failed"),
        }),
      )
      return response
    }
    const rows = Array.isArray(apiData(response).submissions) ? apiData(response).submissions : []
    state.memberTemplateSubmissions = rows
    renderMarketTemplateSubmissions(rows)
    setMarketTemplateSubmissionsState(
      rows.length ? "success" : "neutral",
      rows.length
        ? i18nFormat("market.submissions.ready", "Submissions: {count}", { count: rows.length })
        : i18nMessage("submissions.empty_unfiltered", "No submissions are available yet."),
    )
    return response
  }

  async function listMarketProfilePackSubmissions() {
    if (!hasCapability("member.profile_pack.submissions.read")) {
      setMarketProfilePackSubmissionsState(
        "warning",
        i18nFormat(
          "capability.locked_hint",
          "Requires capability: {capability}",
          { capability: "member.profile_pack.submissions.read" },
        ),
      )
      return
    }
    const actor = marketActor()
    setMarketProfilePackSubmissionsState(
      "loading",
      i18nMessage("profile_pack.market.submissions_loading", "Loading profile-pack submissions..."),
    )
    const response = await api(`/api/member/profile-pack/submissions${queryString({ user_id: actor.user_id })}`)
    renderLog("member_list_profile_pack_submissions_market", response)
    if (!response.data.ok) {
      setMarketProfilePackSubmissionsState(
        "error",
        i18nFormat("profile_pack.market.submissions_error", "Failed to load profile-pack submissions: {message}", {
          message: String(response.data.message || "request_failed"),
        }),
      )
      return response
    }
    const rows = Array.isArray(apiData(response).submissions) ? apiData(response).submissions : []
    state.memberProfilePackSubmissions = rows
    const selectedId = selectedProfilePackSubmissionId()
    const selectedExists = rows.some((item) => String(item.submission_id || item.id || "").trim() === selectedId)
    state.selectedProfilePackSubmissionId = selectedExists
      ? selectedId
      : String((rows[0] && (rows[0].submission_id || rows[0].id)) || "").trim()
    renderMarketProfilePackSubmissions(rows)
    syncMarketProfilePackSubmissionActions()
    setMarketProfilePackSubmissionsState(
      rows.length ? "success" : "neutral",
      rows.length
        ? i18nFormat("market.profile_pack_submissions.ready", "Profile-pack submissions: {count}", { count: rows.length })
        : i18nMessage("profile_pack.market.submissions_empty_unfiltered", "No profile-pack submissions are available yet."),
    )
    return response
  }

  async function downloadMarketProfilePackSubmissionExport() {
    if (!hasCapability("member.profile_pack.submissions.export.download")) {
      updateSummary({
        status: "permission_denied",
        message: i18nFormat(
          "capability.locked_hint",
          "Requires capability: {capability}",
          { capability: "member.profile_pack.submissions.export.download" },
        ),
      })
      syncMarketProfilePackSubmissionActions()
      return
    }
    const submissionId = selectedProfilePackSubmissionId()
    if (!submissionId) {
      updateSummary({
        status: "error",
        message: i18nMessage("moderation.no_selection", "No submission selected."),
      })
      syncMarketProfilePackSubmissionActions()
      return
    }
    const actor = marketActor()
    const response = await fetch(
      `/api/member/profile-pack/submissions/export/download${queryString({
        user_id: actor.user_id,
        submission_id: submissionId,
      })}`,
      {
        method: "GET",
        headers: state.token && state.token !== "no-auth" ? { Authorization: `Bearer ${state.token}` } : {},
      },
    )
    if (!response.ok) {
      const data = await response.json().catch(() => ({ ok: false, message: "download_failed" }))
      renderLog("member_profile_pack_submission_download_market", { status: response.status, data })
      updateSummary({
        status: "download_failed",
        message: String((data && data.message) || "download_failed"),
      })
      return
    }
    const blob = await response.blob()
    const disposition = response.headers.get("Content-Disposition") || ""
    const match = disposition.match(/filename=\"?([^"]+)\"?$/i)
    const filename = match ? match[1] : `${submissionId}.zip`
    const url = URL.createObjectURL(blob)
    const link = document.createElement("a")
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    link.remove()
    URL.revokeObjectURL(url)
    const payload = {
      status: "downloaded",
      submission_id: submissionId,
      filename,
      size_bytes: blob.size,
    }
    renderLog("member_profile_pack_submission_download_market", { status: response.status, data: payload })
    updateSummary(payload)
  }

  function catalogFilters() {
    return {
      pack_id: byId("marketPackFilter").value,
      pack_type: byId("marketPackTypeFilter").value,
      risk_level: byId("marketRiskFilter").value,
      featured: byId("marketFeaturedFilter").value,
      review_label: byId("marketReviewLabelFilter").value,
      warning_flag: byId("marketWarningFlagFilter").value,
    }
  }

  function toSafeInt(value, fallback = 0) {
    const parsed = Number(value)
    if (!Number.isFinite(parsed)) return fallback
    return Math.max(0, Math.trunc(parsed))
  }

  function normalizeCatalogInsights(payload) {
    if (!payload || typeof payload !== "object") return null
    const metrics = payload.metrics && typeof payload.metrics === "object"
      ? payload.metrics
      : {}
    return {
      metrics: {
        total: toSafeInt(metrics.total),
        featured: toSafeInt(metrics.featured),
        highRisk: toSafeInt(metrics.high_risk),
        safe: toSafeInt(metrics.low_risk),
        extension: toSafeInt(metrics.extension_pack),
        botProfile: toSafeInt(metrics.bot_profile_pack),
      },
      featured: payload.featured && typeof payload.featured === "object"
        ? payload.featured
        : null,
      trending: Array.isArray(payload.trending)
        ? payload.trending.filter((item) => item && typeof item === "object")
        : [],
      total: toSafeInt(payload.total),
    }
  }

  function catalogCompareQuery() {
    const sections = normalizeList(byId("marketCompareSections").value)
    return {
      pack_id: byId("marketPackId").value,
      selected_sections: sections.join(","),
    }
  }

  function pillTone(label) {
    const text = String(label || "").toLowerCase()
    if (!text) return "neutral"
    if (text.includes("high") || text.includes("prompt_injection") || text.includes("reveal_system_prompt")) {
      return "danger"
    }
    if (text.includes("medium") || text.includes("degraded") || text.includes("warning")) {
      return "warning"
    }
    return "neutral"
  }

  function appendPill(container, label, tone) {
    const span = document.createElement("span")
    span.className = `pill is-${tone || pillTone(label)}`
    span.textContent = String(label || "")
    container.appendChild(span)
  }

  function pillsCell(values, group = "") {
    const td = document.createElement("td")
    const row = document.createElement("div")
    row.className = "pill-row"
    const list = Array.isArray(values) ? values : []
    if (!list.length) {
      row.textContent = "-"
    } else {
      list.forEach((item) => appendPill(row, enumLabel(group, item), pillTone(item)))
    }
    td.appendChild(row)
    return td
  }

  function textCell(value) {
    const td = document.createElement("td")
    const text = String(value || "").trim()
    td.textContent = text || "-"
    return td
  }

  function profilePackCardModel(item) {
    const helper = marketCardHelpers()
    if (helper && helper.buildProfilePackCardModel) {
      return helper.buildProfilePackCardModel(item)
    }
    return {
      id: String((item && item.pack_id) || ""),
      title: String((item && item.pack_id) || ""),
      subtitle: `${String((item && item.pack_type) || "bot_profile_pack")} · v${String((item && item.version) || "-")}`,
      risk: String((item && item.risk_level) || "unknown"),
      riskTone: pillTone(item && item.risk_level),
      badges: [],
      featured: Boolean(item && item.featured),
      raw: item || {},
    }
  }

  function parseIsoDate(value) {
    const helper = marketCatalogInsightsHelpers()
    if (helper && typeof helper.parseIsoDate === "function") {
      return helper.parseIsoDate(value)
    }
    const text = String(value || "").trim()
    if (!text) return 0
    const time = Date.parse(text)
    return Number.isFinite(time) ? time : 0
  }

  function listLength(value) {
    const helper = marketCatalogInsightsHelpers()
    if (helper && typeof helper.listLength === "function") {
      return helper.listLength(value)
    }
    return Array.isArray(value) ? value.length : 0
  }

  function packRiskScore(risk) {
    const helper = marketCatalogInsightsHelpers()
    if (helper && typeof helper.packRiskScore === "function") {
      return helper.packRiskScore(risk)
    }
    const text = String(risk || "").trim().toLowerCase()
    if (text === "low") return 20
    if (text === "medium") return 12
    if (text === "high") return 4
    return 8
  }

  function packCompatibilityScore(item) {
    const helper = marketCatalogInsightsHelpers()
    if (helper && typeof helper.packCompatibilityScore === "function") {
      return helper.packCompatibilityScore(item)
    }
    const text = String((item && item.compatibility) || "").trim().toLowerCase()
    if (text === "compatible" || text === "ok") return 14
    if (text === "degraded") return 8
    if (text === "blocked") return 0
    return 6
  }

  function catalogRankScore(item) {
    const helper = marketCatalogInsightsHelpers()
    if (helper && typeof helper.catalogRankScore === "function") {
      return helper.catalogRankScore(item)
    }
    if (!item || typeof item !== "object") return 0
    const labels = listLength(item.review_labels)
    const warnings = listLength(item.warning_flags)
    const issues = listLength(item.compatibility_issues)
    const featured = item.featured ? 30 : 0
    const freshness = parseIsoDate(item.featured_at || item.published_at || "") > 0 ? 4 : 0
    const score = (
      featured
      + packRiskScore(item.risk_level)
      + packCompatibilityScore(item)
      + labels * 3
      + freshness
      - warnings * 4
      - issues * 2
    )
    return Math.max(0, Math.round(score))
  }

  function catalogMetrics(rows) {
    const helper = marketCatalogInsightsHelpers()
    if (helper && typeof helper.catalogMetrics === "function") {
      return helper.catalogMetrics(rows)
    }
    const items = Array.isArray(rows) ? rows : []
    let featured = 0
    let highRisk = 0
    let safe = 0
    let extension = 0
    let botProfile = 0
    items.forEach((item) => {
      const risk = String(item && item.risk_level || "").trim().toLowerCase()
      const packType = String(item && item.pack_type || "").trim().toLowerCase()
      if (item && item.featured) featured += 1
      if (risk === "high") highRisk += 1
      if (risk === "low") safe += 1
      if (packType === "extension_pack") extension += 1
      if (packType === "bot_profile_pack") botProfile += 1
    })
    return {
      total: items.length,
      featured,
      highRisk,
      safe,
      extension,
      botProfile,
    }
  }

  function catalogTrendScore(item) {
    const helper = marketCatalogInsightsHelpers()
    if (helper && typeof helper.catalogTrendScore === "function") {
      return helper.catalogTrendScore(item)
    }
    if (!item || typeof item !== "object") return 0
    const explicit = Number(item.trend_score)
    if (Number.isFinite(explicit)) {
      return Math.max(0, Math.trunc(explicit))
    }
    return catalogRankScore(item)
  }

  function renderCatalogMetrics(rows, metricOverride = null) {
    const root = byId("marketCatalogMetrics")
    if (!root) return
    root.innerHTML = ""
    const metric = metricOverride && typeof metricOverride === "object"
      ? {
        total: toSafeInt(metricOverride.total),
        featured: toSafeInt(metricOverride.featured),
        highRisk: toSafeInt(metricOverride.highRisk),
        safe: toSafeInt(metricOverride.safe),
        extension: toSafeInt(metricOverride.extension),
        botProfile: toSafeInt(metricOverride.botProfile),
      }
      : catalogMetrics(rows)
    const viewHelper = marketCatalogViewHelpers()
    const cards = viewHelper && typeof viewHelper.buildMetricCards === "function"
      ? viewHelper.buildMetricCards(metric)
      : [
        {
          key: "market.metric.total",
          fallback: "Total Packs",
          value: String(metric.total),
        },
        {
          key: "market.metric.featured",
          fallback: "Featured",
          value: String(metric.featured),
          tone: "success",
        },
        {
          key: "market.metric.safe",
          fallback: "Low Risk",
          value: String(metric.safe),
          tone: "success",
        },
        {
          key: "market.metric.high_risk",
          fallback: "High Risk",
          value: String(metric.highRisk),
          tone: metric.highRisk > 0 ? "danger" : "",
        },
        {
          key: "market.metric.extension",
          fallback: "Extension Pack",
          value: String(metric.extension),
        },
        {
          key: "market.metric.bot_profile",
          fallback: "Bot Profile Pack",
          value: String(metric.botProfile),
        },
      ]
    cards.forEach((entry) => {
      const card = document.createElement("div")
      card.className = "market-metric-card"
      const label = document.createElement("div")
      label.className = "market-metric-label"
      label.textContent = i18nMessage(entry.key, entry.fallback)
      card.appendChild(label)
      const value = document.createElement("div")
      value.className = "market-metric-value"
      if (entry.tone === "danger") value.classList.add("is-danger")
      if (entry.tone === "success") value.classList.add("is-success")
      value.textContent = entry.value
      card.appendChild(value)
      root.appendChild(card)
    })
  }

  function sortedByTrend(rows) {
    const helper = marketCatalogInsightsHelpers()
    if (helper && typeof helper.sortedByTrend === "function") {
      return helper.sortedByTrend(rows)
    }
    const items = Array.isArray(rows) ? rows.slice() : []
    return items.sort((left, right) => {
      const scoreDiff = catalogRankScore(right) - catalogRankScore(left)
      if (scoreDiff !== 0) return scoreDiff
      const leftTime = parseIsoDate(left && (left.featured_at || left.published_at))
      const rightTime = parseIsoDate(right && (right.featured_at || right.published_at))
      if (rightTime !== leftTime) return rightTime - leftTime
      return String(left && left.pack_id || "").localeCompare(String(right && right.pack_id || ""))
    })
  }

  function setInsightState(nodeId, status, message) {
    const node = byId(nodeId)
    if (!node) return
    node.classList.remove("is-neutral", "is-warning", "is-danger", "is-success", "hidden")
    if (status === "warning") node.classList.add("is-warning")
    else if (status === "error") node.classList.add("is-danger")
    else if (status === "success") node.classList.add("is-success")
    else node.classList.add("is-neutral")
    node.textContent = message
  }

  function renderFeaturedSpotlight(rows, featuredOverride = null) {
    const root = byId("marketFeaturedSpotlight")
    if (!root) return
    root.innerHTML = ""
    const viewHelper = marketCatalogViewHelpers()
    const candidate = viewHelper && typeof viewHelper.selectFeaturedCandidate === "function"
      ? viewHelper.selectFeaturedCandidate(rows, featuredOverride, { sortedByTrend })
      : (() => {
        const sorted = sortedByTrend(rows)
        const featuredRows = sorted.filter((item) => Boolean(item && item.featured))
        return (featuredOverride && typeof featuredOverride === "object")
          ? featuredOverride
          : (featuredRows[0] || sorted[0] || null)
      })()
    if (!candidate) {
      setInsightState(
        "marketFeaturedState",
        "warning",
        i18nMessage("market.featured.empty", "No featured spotlight is available yet."),
      )
      return
    }
    setInsightState("marketFeaturedState", "success", i18nMessage("market.featured.ready", "Featured spotlight ready."))
    const model = profilePackCardModel(candidate)
    const button = document.createElement("button")
    button.type = "button"
    button.className = "featured-template-entry"
    if (state.selectedPackId && state.selectedPackId === model.id) {
      button.classList.add("is-selected")
    }
    const title = document.createElement("div")
    title.className = "featured-template-title"
    title.textContent = resolveCatalogPackTitle(candidate) || model.title || "-"
    button.appendChild(title)
    const subtitle = document.createElement("div")
    subtitle.className = "featured-template-subtitle"
    subtitle.textContent = resolveCatalogPackSubtitle(candidate)
    button.appendChild(subtitle)
    const description = document.createElement("div")
    description.className = "featured-template-description"
    description.textContent = cardDescription(candidate) || i18nMessage("market.card.description_fallback", "No description provided.")
    button.appendChild(description)
    const metrics = document.createElement("div")
    metrics.className = "featured-template-metrics"
    metrics.textContent = i18nFormat("market.featured.risk_and_compat", "risk={risk} · compatibility={compatibility}", {
      risk: enumLabel("risk", String(candidate.risk_level || "unknown")),
      compatibility: enumLabel("compatibility", String(candidate.compatibility || "unknown")),
    })
    button.appendChild(metrics)
    const score = document.createElement("div")
    score.className = "featured-template-score"
    score.textContent = i18nFormat(
      "market.trending.score",
      "trend score {score}",
      { score: String(catalogTrendScore(candidate)) },
    )
    button.appendChild(score)
    const action = document.createElement("div")
    action.className = "featured-template-action"
    action.textContent = i18nMessage("market.featured.action", "Open detail and compare")
    button.appendChild(action)
    button.addEventListener("click", () => {
      selectCatalogItem(candidate)
    })
    root.appendChild(button)
  }

  function renderTrendingRack(rows, trendingOverride = null) {
    const root = byId("marketTrendingRack")
    if (!root) return
    root.innerHTML = ""
    const viewHelper = marketCatalogViewHelpers()
    const ranked = viewHelper && typeof viewHelper.selectTrendingRows === "function"
      ? viewHelper.selectTrendingRows(rows, trendingOverride, { sortedByTrend, limit: 6 })
      : (Array.isArray(trendingOverride) && trendingOverride.length
        ? trendingOverride.slice(0, 6)
        : sortedByTrend(rows).slice(0, 6))
    if (!ranked.length) {
      setInsightState(
        "marketTrendingState",
        "warning",
        i18nMessage("market.trending.empty", "No trending ranking is available yet."),
      )
      return
    }
    setInsightState("marketTrendingState", "success", i18nMessage("market.trending.ready", "Trending ranking ready."))
    ranked.forEach((item, index) => {
      const row = document.createElement("button")
      row.type = "button"
      row.className = "trending-template-item"
      if (state.selectedPackId && state.selectedPackId === String(item.pack_id || "")) {
        row.classList.add("is-selected")
      }
      const rank = document.createElement("span")
      rank.className = "trending-template-rank"
      rank.textContent = `#${index + 1}`
      row.appendChild(rank)
      const name = document.createElement("span")
      name.className = "trending-template-name"
      name.textContent = resolveCatalogPackTitle(item) || String(item.pack_id || "-")
      row.appendChild(name)
      const score = document.createElement("span")
      score.className = "trending-template-score"
      score.textContent = String(catalogTrendScore(item))
      row.appendChild(score)
      row.addEventListener("click", () => {
        selectCatalogItem(item)
      })
      root.appendChild(row)
    })
  }

  function refreshCatalogInsights(rows, insights = null) {
    const normalized = insights && insights.metrics && Object.prototype.hasOwnProperty.call(insights.metrics, "highRisk")
      ? insights
      : normalizeCatalogInsights(insights)
    renderCatalogMetrics(rows, normalized ? normalized.metrics : null)
    renderFeaturedSpotlight(rows, normalized ? normalized.featured : null)
    renderTrendingRack(rows, normalized ? normalized.trending : null)
  }

  function resetCatalogInsights() {
    state.catalogInsights = null
    renderCatalogMetrics([])
    setInsightState(
      "marketFeaturedState",
      "neutral",
      i18nMessage("market.featured.idle_profile_pack", "Load catalog to compute featured spotlight."),
    )
    setInsightState(
      "marketTrendingState",
      "neutral",
      i18nMessage("market.trending.idle_profile_pack", "Load catalog to compute trending ranking."),
    )
    const featured = byId("marketFeaturedSpotlight")
    if (featured) featured.innerHTML = ""
    const trending = byId("marketTrendingRack")
    if (trending) trending.innerHTML = ""
  }

  function selectCatalogItem(item) {
    const packId = String((item && item.pack_id) || "").trim()
    if (!packId) return
    state.selectedPackId = packId
    byId("marketPackId").value = packId
    setMarketDetailExpanded(true)
    resetCompareView()
    updateSummary(item)
    updateCatalogTable(state.catalog)
    updateCatalogDetailActions()
    syncQueryState()
  }

  function resolvedUpdatedAt(item) {
    const viewHelper = marketCatalogViewHelpers()
    if (viewHelper && typeof viewHelper.resolveUpdatedAt === "function") {
      return viewHelper.resolveUpdatedAt(item, state.uiLocale || "en-US")
    }
    const raw = String((item && (item.featured_at || item.published_at)) || "").trim()
    if (!raw) return "-"
    const time = Date.parse(raw)
    if (!Number.isFinite(time)) return raw
    try {
      return new Date(time).toLocaleDateString(state.uiLocale || "en-US", {
        year: "numeric",
        month: "short",
        day: "numeric",
      })
    } catch (_error) {
      return new Date(time).toISOString().slice(0, 10)
    }
  }

  function engagementValue(item, key) {
    const viewHelper = marketCatalogViewHelpers()
    if (viewHelper && typeof viewHelper.engagementValue === "function") {
      return viewHelper.engagementValue(item, key)
    }
    if (!item || typeof item !== "object") return 0
    const raw = Number(item.engagement && item.engagement[key] || 0)
    if (!Number.isFinite(raw)) return 0
    return Math.max(0, Math.trunc(raw))
  }

  function cardDescription(item) {
    return localizedPackDescription(
      item && item.pack_id,
      String((item && (item.description || item.summary || "")) || "").trim(),
    )
  }

  function cardSignalRows(item) {
    const viewHelper = marketCatalogViewHelpers()
    if (viewHelper && typeof viewHelper.buildCardSignalRows === "function") {
      return viewHelper.buildCardSignalRows(item, {
        i18nMessage,
        enumLabel,
      })
    }
    const sections = Array.isArray(item && item.sections) ? item.sections.length : 0
    const labels = Array.isArray(item && item.review_labels) ? item.review_labels.length : 0
    const flags = Array.isArray(item && item.warning_flags) ? item.warning_flags.length : 0
    return [
      {
        label: i18nMessage("profile_pack.compare.card.compatibility", "Compatibility"),
        value: enumLabel("compatibility", String((item && item.compatibility) || "unknown")),
      },
      {
        label: i18nMessage("market.metric.sections", "Sections"),
        value: String(sections),
      },
      {
        label: i18nMessage("table.header.labels", "Labels"),
        value: String(labels),
      },
      {
        label: i18nMessage("table.header.flags", "Flags"),
        value: String(flags),
      },
    ]
  }

  function renderCatalogCards(rows) {
    const grid = byId("marketCatalogGrid")
    if (!grid) return
    clearChildren(grid)
    const items = Array.isArray(rows) ? rows : []
    if (!items.length) {
      const empty = document.createElement("div")
      empty.className = "template-grid-empty"
      empty.textContent = i18nMessage(
        "market.catalog.empty_cards",
        "No profile-pack cards to display.",
      )
      grid.appendChild(empty)
      return
    }
    items.forEach((item) => {
      const model = profilePackCardModel(item)
      const card = document.createElement("article")
      card.className = "template-card hf-like-card"
      card.tabIndex = 0
      if (model.id && model.id === state.selectedPackId) {
        card.classList.add("is-selected")
      }

      const top = document.createElement("div")
      top.className = "template-card-top"
      const owner = document.createElement("span")
      owner.className = "template-card-owner"
      owner.textContent = localizedSourceSubmission(
        item && item.source_submission_id,
        item && item.pack_id,
      )
      top.appendChild(owner)
      const risk = document.createElement("span")
      risk.className = `pill is-${model.riskTone || "neutral"}`
      risk.textContent = enumLabel("risk", String((item && item.risk_level) || model.risk || "unknown"))
      top.appendChild(risk)
      card.appendChild(top)

      const title = document.createElement("h3")
      title.className = "template-card-title"
      title.textContent = resolveCatalogPackTitle(item) || model.title || "-"
      card.appendChild(title)

      const subtitle = document.createElement("p")
      subtitle.className = "template-card-subtitle"
      subtitle.textContent = resolveCatalogPackSubtitle(item) || i18nMessage("market.card.subtitle_fallback", "profile pack")
      card.appendChild(subtitle)

      const desc = document.createElement("p")
      desc.className = "template-card-description"
      desc.textContent = cardDescription(item) || i18nMessage("market.card.description_fallback", "No description provided.")
      card.appendChild(desc)

      const signals = document.createElement("div")
      signals.className = "template-card-signals"
      cardSignalRows(item).forEach((entry) => {
        const signal = document.createElement("div")
        signal.className = "template-card-signal"
        const label = document.createElement("span")
        label.textContent = entry.label
        signal.appendChild(label)
        const value = document.createElement("strong")
        value.textContent = entry.value
        signal.appendChild(value)
        signals.appendChild(signal)
      })
      card.appendChild(signals)

      const meta = document.createElement("div")
      meta.className = "template-card-meta-line"
      const viewHelper = marketCatalogViewHelpers()
      const metaEntries = viewHelper && typeof viewHelper.buildCardMetaEntries === "function"
        ? viewHelper.buildCardMetaEntries(item, {
          locale: state.uiLocale || "en-US",
          resolveUpdatedAt: (entry) => resolvedUpdatedAt(entry),
          engagementValue: (entry, key) => engagementValue(entry, key),
          catalogRankScore,
        })
        : [
          {
            key: "market.card.updated",
            fallback: "Updated {value}",
            value: resolvedUpdatedAt(item),
          },
          {
            key: "market.card.downloads",
            fallback: "Installs {value}",
            value: String(engagementValue(item, "installs")),
          },
          {
            key: "market.card.trials",
            fallback: "Trials {value}",
            value: String(engagementValue(item, "trial_requests")),
          },
          {
            key: "market.card.score",
            fallback: "Score {value}",
            value: String(catalogRankScore(item)),
          },
        ]
      metaEntries.forEach((entry) => {
        const cell = document.createElement("span")
        cell.className = "template-card-meta-item"
        cell.textContent = i18nFormat(entry.key, entry.fallback, { value: entry.value })
        meta.appendChild(cell)
      })
      card.appendChild(meta)

      const actions = document.createElement("div")
      actions.className = "inline-form wrap template-card-actions"
      const useBtn = document.createElement("button")
      useBtn.type = "button"
      useBtn.className = "btn-ghost"
      useBtn.textContent = i18nMessage("market.card.open", "Open")
      useBtn.addEventListener("click", (event) => {
        event.stopPropagation()
        selectCatalogItem(item)
      })
      actions.appendChild(useBtn)
      const packageUrl = catalogPackageUrl(item)
      if (packageUrl) {
        const downloadBtn = document.createElement("button")
        downloadBtn.type = "button"
        downloadBtn.className = "btn-primary"
        downloadBtn.textContent = i18nMessage("button.download_package", "Download Package")
        downloadBtn.addEventListener("click", (event) => {
          event.stopPropagation()
          selectCatalogItem(item)
          triggerCatalogDownload(item)
        })
        actions.appendChild(downloadBtn)
      } else {
        const compareBtn = document.createElement("button")
        compareBtn.type = "button"
        compareBtn.className = "btn-ghost"
        compareBtn.textContent = i18nMessage("market.card.compare", "Compare")
        if (!hasCapability("profile_pack.catalog.read")) {
          compareBtn.disabled = true
          compareBtn.classList.add("capability-blocked")
          compareBtn.setAttribute("aria-disabled", "true")
          compareBtn.title = i18nFormat(
            "capability.locked_hint",
            "Requires capability: {capability}",
            { capability: "profile_pack.catalog.read" },
          )
        }
        compareBtn.addEventListener("click", (event) => {
          event.stopPropagation()
          selectCatalogItem(item)
          void compareCatalogPack()
        })
        actions.appendChild(compareBtn)
      }
      card.appendChild(actions)

      const onSelect = () => {
        selectCatalogItem(item)
      }
      card.addEventListener("click", onSelect)
      card.addEventListener("keydown", (event) => {
        if (event.key !== "Enter" && event.key !== " ") return
        event.preventDefault()
        onSelect()
      })
      grid.appendChild(card)
    })
  }

  function compareChangeSummaryCell(row) {
    const td = document.createElement("td")
    const wrapper = document.createElement("div")
    wrapper.className = "compare-row-value compare-change-cell"

    const summary = document.createElement("div")
    summary.className = "compare-row-text"
    summary.textContent = resolveCompareChangeSummary(row)
    wrapper.appendChild(summary)

    const button = document.createElement("button")
    button.type = "button"
    button.className = "btn-ghost compare-inline-action"
    button.textContent = i18nMessage("market.compare.expand_detail", "Expand Detail")
    if (!row || !row.changed) {
      button.disabled = true
      button.setAttribute("aria-disabled", "true")
    } else {
      button.addEventListener("click", () => {
        renderCompareDetailPane(row)
      })
    }
    wrapper.appendChild(button)

    td.appendChild(wrapper)
    return td
  }

  function resolveCompareChangeSummary(row) {
    const helper = marketCompareHelpers()
    if (helper && typeof helper.resolveCompareChangeSummary === "function") {
      return helper.resolveCompareChangeSummary(row, { i18nMessage, i18nFormat })
    }
    const filePath = String((row && row.file_path) || "").trim()
    if (filePath) return filePath
    const section = String((row && row.section) || "").trim()
    if (section) return `sections/${section}.json`
    if (row && row.changed) {
      return i18nMessage("market.compare.change_paths_fallback", "Change detected")
    }
    return i18nMessage("market.compare.no_changes", "No change")
  }

  function compareChangedCell(row) {
    const td = document.createElement("td")
    const wrapper = document.createElement("div")
    wrapper.className = "pill-row"
    if (row.changed) {
      appendPill(wrapper, i18nMessage("market.compare.changed", "changed"), "danger")
    } else {
      appendPill(wrapper, i18nMessage("market.compare.same", "same"), "success")
    }
    td.appendChild(wrapper)
    return td
  }

  function compareSizeCell(row) {
    const td = document.createElement("td")
    const helper = marketCompareHelpers()
    if (helper && typeof helper.formatCompareSize === "function") {
      td.textContent = helper.formatCompareSize(row, { i18nMessage, i18nFormat })
      return td
    }
    const bytesLabel = i18nMessage("market.compare.bytes", "bytes")
    const beforeSize = Number(row && row.before_size || 0)
    const afterSize = Number(row && row.after_size || 0)
    const delta = Number(row && row.delta_size || 0)
    const deltaLabel = delta >= 0 ? `+${delta}` : `${delta}`
    td.textContent = i18nFormat(
      "market.compare.size_compact",
      "{before} / {after} / {delta} {bytes}",
      {
        before: beforeSize,
        after: afterSize,
        delta: deltaLabel,
        bytes: bytesLabel,
      },
    )
    return td
  }

  function renderCompareDetailPane(row) {
    const pane = byId("marketCompareDetailPane")
    const meta = byId("marketCompareDetailMeta")
    const diff = byId("marketCompareDetailDiff")
    const before = byId("marketCompareDetailBefore")
    const after = byId("marketCompareDetailAfter")
    if (!pane || !meta || !diff || !before || !after) return
    const helper = marketCompareHelpers()
    if (helper && typeof helper.buildCompareDetailContent === "function") {
      const detail = helper.buildCompareDetailContent(row, { i18nMessage, i18nFormat })
      state.compareDetailKey = String(detail.detailKey || "").trim()
      pane.classList.remove("hidden")
      meta.textContent = String(detail.metaText || "")
      diff.textContent = String(detail.diffText || "")
      before.textContent = String(detail.beforeText || "")
      after.textContent = String(detail.afterText || "")
      return
    }
    state.compareDetailKey = String((row && row.section) || "").trim()
    pane.classList.remove("hidden")
    meta.textContent = i18nFormat(
      "market.compare.detail.meta",
      "Section: {section} | File: {file}",
      {
        section: String((row && row.section) || "-"),
        file: String((row && row.file_path) || "-"),
      },
    )
    const diffRows = Array.isArray(row && row.diff_preview) ? row.diff_preview : []
    const beforeRows = Array.isArray(row && row.before_preview) ? row.before_preview : []
    const afterRows = Array.isArray(row && row.after_preview) ? row.after_preview : []
    const filePath = String((row && row.file_path) || "-")
    diff.textContent = diffRows.join("\n")
    before.textContent = beforeRows.join("\n")
    after.textContent = afterRows.join("\n")
    if (!diff.textContent.trim()) {
      diff.textContent = i18nFormat(
        "market.compare.detail.no_preview_diff",
        "No unified diff preview. File: {file}",
        { file: filePath },
      )
    }
    if (!before.textContent.trim()) {
      before.textContent = i18nFormat(
        "market.compare.detail.no_preview_before",
        "No before preview. hash={hash}",
        { hash: String((row && row.before_hash_short) || (row && row.before_hash) || "-") },
      )
    }
    if (!after.textContent.trim()) {
      after.textContent = i18nFormat(
        "market.compare.detail.no_preview_after",
        "No after preview. hash={hash}",
        { hash: String((row && row.after_hash_short) || (row && row.after_hash) || "-") },
      )
    }
    if (row && row.diff_preview_truncated) {
      diff.textContent += `\n\n${i18nMessage("market.compare.detail.truncated", "...truncated for preview")}`
    }
    if (row && row.before_preview_truncated) {
      before.textContent += `\n\n${i18nMessage("market.compare.detail.truncated", "...truncated for preview")}`
    }
    if (row && row.after_preview_truncated) {
      after.textContent += `\n\n${i18nMessage("market.compare.detail.truncated", "...truncated for preview")}`
    }
  }

  function resetCompareDetailPane() {
    const pane = byId("marketCompareDetailPane")
    const meta = byId("marketCompareDetailMeta")
    const diff = byId("marketCompareDetailDiff")
    const before = byId("marketCompareDetailBefore")
    const after = byId("marketCompareDetailAfter")
    if (pane) pane.classList.add("hidden")
    if (meta) {
      const helper = marketCompareHelpers()
      meta.textContent = helper && typeof helper.emptyDetailMeta === "function"
        ? helper.emptyDetailMeta({ i18nMessage, i18nFormat })
        : i18nMessage(
          "market.compare.detail.empty_meta",
          'Select one changed row and click "Expand Detail".',
        )
    }
    if (diff) diff.textContent = ""
    if (before) before.textContent = ""
    if (after) after.textContent = ""
  }

  function compareValueLine(side, value) {
    const line = document.createElement("div")
    const sideNode = document.createElement("span")
    sideNode.className = "compare-row-side"
    const sideKey = `market.compare.${String(side || "").toLowerCase()}`
    const sideLabel = i18nMessage(sideKey, String(side || ""))
    sideNode.textContent = `${sideLabel}: `
    line.appendChild(sideNode)

    const textNode = document.createElement("span")
    textNode.className = "compare-row-text"
    textNode.textContent = String(value || "-")
    line.appendChild(textNode)
    return line
  }

  async function listCatalogInsights(rows) {
    const response = await api(`/api/profile-pack/catalog/insights${queryString(catalogFilters())}`)
    renderLog("profile_pack_catalog_insights", response)
    const derivedInsights = normalizeCatalogInsights(deriveCatalogInsightsPayload(rows))
    if (!response.data.ok) {
      state.catalogInsights = derivedInsights
      refreshCatalogInsights(rows, state.catalogInsights)
      return response
    }
    const runtimeInsights = normalizeCatalogInsights(apiData(response))
    state.catalogInsights = state.publicCatalogAvailable ? derivedInsights : (runtimeInsights || derivedInsights)
    refreshCatalogInsights(rows, state.catalogInsights)
    return response
  }

  function updateCatalogTable(rows) {
    state.catalog = Array.isArray(rows) ? rows : []
    const tbody = byId("marketCatalogTable").querySelector("tbody")
    tbody.innerHTML = ""
    state.catalog.forEach((item) => {
      const tr = document.createElement("tr")
      const packId = String(item.pack_id || "")
      tr.dataset.packId = packId
      tr.classList.add("interactive-row")
      tr.classList.toggle("is-selected", packId !== "" && packId === state.selectedPackId)
      const packLabel = resolveCatalogPackLabel(item)
      tr.appendChild(textCell(packLabel))
      tr.appendChild(textCell(item.version || ""))
      tr.appendChild(
        textCell(
          item.featured
            ? i18nMessage("market.state.featured", "featured")
            : i18nMessage("market.state.normal", "normal"),
        ),
      )
      tr.appendChild(pillsCell(item.risk_level ? [item.risk_level] : [], "risk"))
      tr.appendChild(pillsCell(item.review_labels, "review_label"))
      tr.appendChild(pillsCell(item.warning_flags, "warning_flag"))
      tr.appendChild(textCell(localizedSourceSubmission(item.source_submission_id, item.pack_id)))
      tr.addEventListener("click", () => {
        selectCatalogItem(item)
      })
      tbody.appendChild(tr)
    })
    renderCatalogCards(state.catalog)
    refreshCatalogInsights(state.catalog, hasActiveLocalFilters() ? null : state.catalogInsights)
  }

  async function listCatalog() {
    if (!hasCapability("profile_pack.catalog.read")) {
      setCatalogState(
        "warning",
        i18nFormat(
          "capability.locked_hint",
          "Requires capability: {capability}",
          { capability: "profile_pack.catalog.read" },
        ),
      )
      return { status: 403, data: { ok: false, message: "capability_locked" } }
    }
    setCatalogState(
      "loading",
      i18nMessage("market.catalog.loading", "Loading profile-pack catalog..."),
    )
    const response = await api(`/api/profile-pack/catalog${queryString(catalogFilters())}`)
    renderLog("profile_pack_catalog_list", response)
    const runtimeRows = response.data.ok
      ? (Array.isArray(apiData(response).packs) ? apiData(response).packs : [])
      : []
    const publicRows = await fetchPublicCatalogRows()
    state.publicCatalogRows = publicRows
    state.publicCatalogAvailable = publicRows.length > 0
    state.catalogSourceMode = publicRows.length && runtimeRows.length
      ? "merged"
      : publicRows.length
        ? "public"
        : response.data.ok
          ? "runtime"
          : "empty"
    state.catalogRaw = mergeCatalogRows(runtimeRows, publicRows)
    state.catalogInsights = null
    updateCatalogTable(state.catalogRaw)
    await listCatalogInsights(state.catalogRaw)
    applyLocalCatalogView({ updateSummary: false })
    if (state.selectedPackId) {
      const selected = state.catalog.find(
        (item) => String(item && item.pack_id || "").trim() === state.selectedPackId,
      )
      if (selected) {
        setMarketDetailExpanded(true)
        updateSummary(selected)
      } else {
        setMarketDetailExpanded(false)
      }
    } else {
      setMarketDetailExpanded(false)
    }
    updateCatalogDetailActions()
    if (!state.catalogRaw.length) {
      const message = response.data.ok
        ? i18nMessage(
          "market.catalog.empty_filtered",
          "No published profile packs matched current filters.",
        )
        : i18nFormat("market.catalog.error", "Request failed: {message}", {
          message: response.data.message || "unknown error",
        })
      setCatalogState(
        response.data.ok ? "warning" : "error",
        message,
      )
    } else {
      setCatalogState(
        "success",
        i18nFormat(
          "market.catalog.filtered",
          "Showing {shown} of {total} profile packs.",
          { shown: state.catalog.length, total: state.catalogRaw.length },
        ),
      )
    }
    resetCompareView()
    updateSummary({ status: "listed", count: state.catalog.length })
    return response
  }

  async function loadCatalogDetail() {
    if (!hasCapability("profile_pack.catalog.read")) {
      resetCompareView()
      updateSummary({
        status: "error",
        message: i18nFormat(
          "capability.locked_hint",
          "Requires capability: {capability}",
          { capability: "profile_pack.catalog.read" },
        ),
      })
      return
    }
    const packId = String(byId("marketPackId").value || "").trim()
    if (!packId) {
      resetCompareView()
      updateSummary({
        status: "error",
        message: i18nMessage("market.error.pack_required", "pack_id is required"),
      })
      return
    }
    const selected = selectedCatalogRow()
    if (selected && !catalogRowHasRuntime(selected)) {
      state.selectedPackId = packId
      setMarketDetailExpanded(true)
      resetCompareView()
      updateSummary(selected)
      updateCatalogDetailActions()
      return
    }
    const response = await api(`/api/profile-pack/catalog/detail${queryString({ pack_id: packId })}`)
    renderLog("profile_pack_catalog_detail", response)
    if (!response.data.ok) {
      resetCompareView()
      updateSummary({ status: "error", message: response.data.message || "request_failed" })
      return
    }
    state.selectedPackId = packId
    setMarketDetailExpanded(true)
    updateCatalogTable(state.catalog)
    resetCompareView()
    updateSummary(apiData(response))
    updateCatalogDetailActions()
  }

  async function compareCatalogPack() {
    if (!hasCapability("profile_pack.catalog.read")) {
      resetCompareView()
      updateSummary({
        status: "error",
        message: i18nFormat(
          "capability.locked_hint",
          "Requires capability: {capability}",
          { capability: "profile_pack.catalog.read" },
        ),
      })
      return
    }
    const query = catalogCompareQuery()
    const packId = String(query.pack_id || "").trim()
    if (!packId) {
      resetCompareView()
      updateSummary({
        status: "error",
        message: i18nMessage("market.error.pack_required", "pack_id is required"),
      })
      return
    }
    const selected = selectedCatalogRow()
    if (selected && !catalogRowHasRuntime(selected)) {
      resetCompareView()
      updateSummary({
        ...selected,
        status: "runtime_unavailable",
        message: i18nMessage(
          "market.compare.runtime_unavailable",
          "Runtime compare is available only for locally published packs.",
        ),
      })
      updateCatalogDetailActions()
      return
    }
    const response = await api(`/api/profile-pack/catalog/compare${queryString(query)}`)
    renderLog("profile_pack_catalog_compare", response)
    if (!response.data.ok) {
      resetCompareView()
      updateSummary({ status: "error", message: response.data.message || "request_failed" })
      return
    }
    state.selectedPackId = packId
    setMarketDetailExpanded(true)
    updateCatalogTable(state.catalog)
    const payload = apiData(response)
    updateSummary(payload)
    renderCompareView(payload)
    updateCatalogDetailActions()
  }

  function selectedMarketTemplateId() {
    return String(byId("marketTemplateId")?.value || "").trim()
  }

  async function runMarketTemplateTrial() {
    const templateId = selectedMarketTemplateId()
    if (!templateId) {
      updateSummary({
        status: "error",
        message: i18nMessage("market.error.template_required", "template_id is required"),
      })
      return
    }
    const actor = marketActor()
    const response = await api("/api/trial", {
      method: "POST",
      body: {
        ...actor,
        template_id: templateId,
      },
    })
    renderLog("market_template_trial", response)
    updateSummary(response.data.ok ? apiData(response) : { status: "error", message: response.data.message || "request_failed" })
    if (response.data.ok) {
      void loadMarketInstallations()
    }
  }

  async function runMarketTemplateInstall() {
    const templateId = selectedMarketTemplateId()
    if (!templateId) {
      updateSummary({
        status: "error",
        message: i18nMessage("market.error.template_required", "template_id is required"),
      })
      return
    }
    const actor = marketActor()
    const response = await api("/api/templates/install", {
      method: "POST",
      body: {
        ...actor,
        template_id: templateId,
        install_options: readMarketInstallOptions(),
      },
    })
    renderLog("market_template_install", response)
    updateSummary(response.data.ok ? apiData(response) : { status: "error", message: response.data.message || "request_failed" })
    if (response.data.ok) {
      void loadMarketInstallations({ refresh: true })
      void listCatalog()
    }
  }

  async function runMarketTemplateSubmit() {
    const templateId = selectedMarketTemplateId()
    if (!templateId) {
      updateSummary({
        status: "error",
        message: i18nMessage("market.error.template_required", "template_id is required"),
      })
      return
    }
    const version = String(byId("marketSubmitVersion")?.value || "1.0.0").trim() || "1.0.0"
    const payload = {
      ...marketActor(),
      template_id: templateId,
      version,
      upload_options: readMarketUploadOptions(),
    }
    const input = byId("marketSubmitPackageFile")
    const file = input && input.files ? input.files[0] : null
    if (file) {
      try {
        assertUploadFileAllowed(file)
      } catch (error) {
        renderLog("market_template_submit", {
          status: 413,
          data: {
            ok: false,
            message: uploadTooLargeMessage(),
            error: {
              code: "package_too_large",
              message: uploadTooLargeMessage(),
            },
          },
        })
        updateSummary({ status: "error", message: uploadTooLargeMessage() })
        return
      }
      payload.package_name = file.name
      payload.package_base64 = await readFileAsBase64(file)
    }
    const response = await api("/api/templates/submit", {
      method: "POST",
      body: payload,
    })
    renderLog("market_template_submit", response)
    updateSummary(response.data.ok ? apiData(response) : { status: "error", message: response.data.message || "request_failed" })
    if (response.data.ok) {
      void listMarketTemplateSubmissions()
      void listCatalog()
    }
  }

  async function runMarketProfilePackSubmit() {
    const artifactId = String(byId("marketSubmitArtifactId")?.value || "").trim()
    if (!artifactId) {
      updateSummary({
        status: "error",
        message: i18nMessage("market.error.artifact_required", "artifact_id is required"),
      })
      return
    }
    const payload = {
      ...marketActor(),
      artifact_id: artifactId,
      submit_options: readMarketSubmitOptions(),
    }
    const response = await api("/api/profile-pack/submit", {
      method: "POST",
      body: payload,
    })
    renderLog("market_profile_pack_submit", response)
    updateSummary(response.data.ok ? apiData(response) : { status: "error", message: response.data.message || "request_failed" })
    if (response.data.ok) {
      void listMarketProfilePackSubmissions()
      void listCatalog()
    }
  }

  function bindEvents() {
    const helper = marketEventBindingHelpers()
    if (helper && typeof helper.bindMarketEvents === "function") {
      helper.bindMarketEvents({
        byId,
        state,
        localeQuickButtons,
        applyUiLocale,
        login,
        syncReviewerAuthFields,
        listCatalog,
        loadCatalogDetail,
        compareCatalogPack,
        triggerCatalogDownload,
        applyLocalCatalogView,
        setFilterDrawerOpen,
        setMarketLogExpanded,
        loadMarketInstallations,
        listMarketTemplateSubmissions,
        listMarketProfilePackSubmissions,
        downloadMarketProfilePackSubmissionExport,
        runMarketTemplateTrial,
        runMarketTemplateInstall,
        runMarketTemplateSubmit,
        runMarketProfilePackSubmit,
        bindUploadDropZone,
        sortFallback: LOCAL_SORT_OPTIONS.TRENDING,
        document,
      })
      return
    }

    bindUploadDropZone({
      zoneId: "marketUploadDropzone",
      inputId: "marketSubmitPackageFile",
      outputId: "marketUploadFileName",
      emptyKey: "market.upload.file_idle",
      emptyFallback: "No file selected. Template submit can still use generated output.",
    })
  }

  async function init() {
    bindUiEventBusSync()
    bindStorageSync()
    bindEvents()
    loadQueryState()
    applyQueryStateToControls()
    initializeUiLocale()
    setFilterDrawerOpen(false)
    state.localSearch = String(byId("marketGlobalSearch")?.value || state.localSearch || "").trim()
    state.localSort = validSortOption(byId("marketSortBy")?.value || state.localSort || LOCAL_SORT_OPTIONS.TRENDING)
    renderFacetFilters([])
    updateCatalogCountChips([], [])
    setMarketLogExpanded(false)
    setMarketDetailExpanded(Boolean(state.selectedPackId))
    resetCompareView()
    resetCatalogInsights()
    updateCatalogDetailActions()
    await refreshHealth()
    await initAuth()
    await loadMarketInstallations()
    await listMarketTemplateSubmissions()
    await listMarketProfilePackSubmissions()
    if (!state.authRequired && hasCapability("profile_pack.catalog.read")) {
      await listCatalog()
    }
  }

  void init()
  globalScope.SharelifeMarketPage = {
    listCatalog,
    loadCatalogDetail,
    compareCatalogPack,
  }
})(typeof globalThis !== "undefined" ? globalThis : this)
