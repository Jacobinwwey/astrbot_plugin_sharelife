(function bootstrapMarketPage(globalScope) {
  const UI_LOCALE_STORAGE_KEY = "sharelife.uiLocale"
  const MARKET_LIKES_STORAGE_KEY = "sharelife.marketLikes"
  const MARKET_PAGE_INSTANCE_ID = `sharelife-market-${Math.random().toString(36).slice(2)}`
  const marketFilterApi = globalScope.SharelifeMarketFilters || null
  const MARKET_PAGE_KIND = String(
    globalScope.__SHARELIFE_MARKET_PAGE_KIND
      || (globalScope.document && globalScope.document.body && globalScope.document.body.dataset.marketSurface)
      || "catalog",
  ).trim().toLowerCase() || "catalog"
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
  const QUICK_FILTER_PRESETS = Object.freeze({
    all: null,
    bot_profile_pack: {
      groupKey: "pack_type",
      values: ["bot_profile_pack"],
    },
    extension_pack: {
      groupKey: "pack_type",
      values: ["extension_pack"],
    },
    featured: {
      groupKey: "featured",
      values: ["true"],
    },
    low_risk: {
      groupKey: "risk_level",
      values: ["low"],
    },
  })

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
    allowAnonymousMember: false,
    authResolved: false,
    authPromptRequested: false,
    authRole: "",
    availableRoles: [],
    capabilities: {
      role: "member",
      authenticated: false,
      anonymousMember: false,
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
    activeQuickFilter: "all",
    filterDrawerOpen: false,
    logExpanded: false,
    detailExpanded: false,
    activeDetailVariant: "variant_3",
    compareDetailKey: "",
    installSectionSelections: {},
    memberInstallations: [],
    memberInstallationsRequested: false,
    likedPackIds: new Set(),
    publicCatalogRows: [],
    publicCatalogAvailable: false,
    catalogSourceMode: "runtime",
  }
  const CONTROL_CAPABILITY_MAP = Object.freeze({
    btnMarketLogin: "auth.login",
    btnMarketListCatalog: "profile_pack.catalog.read",
    btnMarketCatalogDetail: "profile_pack.catalog.read",
    btnMarketCatalogCompare: "profile_pack.catalog.read",
  })
  const MARKET_BASE_FALLBACK_OPERATIONS = Object.freeze([
    "auth.info.read",
    "auth.login",
    "health.read",
    "ui.capabilities.read",
  ])
  const MARKET_MEMBER_FALLBACK_OPERATIONS = Object.freeze([
    "member.installations.read",
    "member.installations.refresh",
    "member.installations.uninstall",
    "templates.trial.request",
    "templates.install",
    "templates.submit",
    "profile_pack.catalog.read",
    "profile_pack.community.submit",
    "notifications.read",
  ])
  const ANONYMOUS_MEMBER_FALLBACK_OPERATIONS = Object.freeze(
    (
      globalScope.SharelifeCapabilityPolicyRuntime
      && globalScope.SharelifeCapabilityPolicyRuntime.anonymousMemberFallbackOperations
    )
      ? globalScope.SharelifeCapabilityPolicyRuntime.anonymousMemberFallbackOperations()
      : [
        "auth.info.read",
        "auth.login",
        "health.read",
        "ui.capabilities.read",
      ],
  )
  let storageSyncBound = false
  let uiEventBusBound = false
  const compareViewHelper = globalScope.SharelifeProfilePackCompareView

  function profilePackMarketHelpers() {
    return globalScope.SharelifeProfilePackMarket || null
  }

  function profilePackGuidanceHelpers() {
    return globalScope.SharelifeProfilePackGuidance || null
  }

  function marketCardHelpers() {
    return globalScope.SharelifeMarketCards || null
  }

  function marketCatalogContractHelpers() {
    return globalScope.SharelifeMarketCatalogContract || null
  }

  function detailShellHelpers() {
    return globalScope.SharelifeMarketDetailShell || null
  }

  function variantRegistryHelpers() {
    return globalScope.SharelifeMarketDetailVariantRegistry || null
  }

  function uiEventBusHelpers() {
    return globalScope.SharelifeUiEventBus || null
  }

  function marketAuthSurfaceHelpers() {
    return globalScope.SharelifeMarketAuthSurface || null
  }

  function capabilityGuardHelpers() {
    return globalScope.SharelifeCapabilityGuardRuntime || null
  }

  function capabilityGuardDomHelpers() {
    return globalScope.SharelifeCapabilityGuardDomRuntime || null
  }

  function byId(id) {
    return document.getElementById(id)
  }

  function isDetailPage() {
    return MARKET_PAGE_KIND === "detail"
  }

  function encodePackIdForPath(packId) {
    return String(packId || "")
      .split("/")
      .map((part) => encodeURIComponent(part))
      .join("/")
  }

  function routeSelectedPackId() {
    if (!globalScope || !globalScope.location) return ""
    const prefix = "/market/packs/"
    const pathname = String(globalScope.location.pathname || "")
    if (!pathname.startsWith(prefix)) return ""
    return pathname.slice(prefix.length)
      .split("/")
      .map((part) => decodeURIComponent(part))
      .join("/")
      .trim()
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

  function readStoredMarketLikes() {
    if (!globalScope.localStorage) return new Set()
    try {
      const raw = String(globalScope.localStorage.getItem(MARKET_LIKES_STORAGE_KEY) || "")
      if (!raw) return new Set()
      const parsed = JSON.parse(raw)
      const values = Array.isArray(parsed)
        ? parsed
        : (parsed && typeof parsed === "object" ? Object.keys(parsed).filter((key) => parsed[key]) : [])
      return new Set(
        values.map((item) => String(item || "").trim()).filter(Boolean),
      )
    } catch (_error) {
      return new Set()
    }
  }

  function persistMarketLikes() {
    if (!globalScope.localStorage) return
    try {
      globalScope.localStorage.setItem(
        MARKET_LIKES_STORAGE_KEY,
        JSON.stringify(Array.from(state.likedPackIds)),
      )
    } catch (_error) {
      // Ignore localStorage write failures and keep the current in-memory state.
    }
  }

  function isPackLiked(packId) {
    const normalized = String(packId || "").trim()
    if (!normalized) return false
    return state.likedPackIds.has(normalized)
  }

  function catalogBaseLikeCount(item) {
    const explicit = Number(item && item.like_count)
    if (Number.isFinite(explicit)) return Math.max(0, Math.trunc(explicit))
    const engagementCount = Number(item && item.engagement && item.engagement.likes)
    if (Number.isFinite(engagementCount)) return Math.max(0, Math.trunc(engagementCount))
    return 0
  }

  function catalogLikeCount(item) {
    return catalogBaseLikeCount(item) + (isPackLiked(item && item.pack_id) ? 1 : 0)
  }

  function toggleCatalogLike(item) {
    const packId = String(item && item.pack_id || "").trim()
    if (!packId) return
    if (state.likedPackIds.has(packId)) {
      state.likedPackIds.delete(packId)
    } else {
      state.likedPackIds.add(packId)
    }
    persistMarketLikes()
    renderCatalogCards(state.catalog)
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
    if (state.selectedPackId) {
      renderSelectedDetailShell()
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
    if (!event) return
    const key = String(event.key || "")
    if (key === MARKET_LIKES_STORAGE_KEY) {
      state.likedPackIds = readStoredMarketLikes()
      renderCatalogCards(state.catalog)
      return
    }
    if (key !== UI_LOCALE_STORAGE_KEY) return
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

  function quickFilterButtons() {
    return Array.from(document.querySelectorAll("[data-market-quick-filter]"))
  }

  function parseCsvQueryValue(value) {
    return String(value || "")
      .split(",")
      .map((item) => String(item || "").trim())
      .filter(Boolean)
  }

  function currentCatalogQueryParams() {
    const next = new URLSearchParams()
    const q = String(state.localSearch || "").trim()
    const sort = validSortOption(state.localSort)
    if (q) next.set("q", q)
    if (sort && sort !== LOCAL_SORT_OPTIONS.TRENDING) next.set("sort", sort)
    LOCAL_FACET_GROUPS.forEach((group) => {
      const selected = state.localFacets[group.key]
      if (!(selected instanceof Set) || selected.size === 0) return
      next.set(`facet_${group.key}`, Array.from(selected).sort().join(","))
    })
    return next
  }

  function detailHref(packId) {
    const encodedPackId = encodePackIdForPath(packId)
    const search = currentCatalogQueryParams().toString()
    return `/market/packs/${encodedPackId}${search ? `?${search}` : ""}`
  }

  function navigateToDetail(packId) {
    const targetPackId = String(packId || "").trim()
    if (!targetPackId || !globalScope || !globalScope.location) return
    globalScope.location.href = detailHref(targetPackId)
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
    const params = new URLSearchParams(globalScope.location.search || "")
    state.localSearch = String(params.get("q") || "").trim()
    state.localSort = validSortOption(params.get("sort") || LOCAL_SORT_OPTIONS.TRENDING)
    state.selectedPackId = isDetailPage()
      ? routeSelectedPackId()
      : String(params.get("pack_id") || "").trim()
    state.localFacets = createFacetSelectionMap()
    LOCAL_FACET_GROUPS.forEach((group) => {
      const queryKey = `facet_${group.key}`
      parseCsvQueryValue(params.get(queryKey)).forEach((value) => {
        state.localFacets[group.key].add(value)
      })
    })
    state.activeQuickFilter = detectActiveQuickFilter()
  }

  function syncQueryState() {
    if (!globalScope || !globalScope.location || !globalScope.history) return
    if (isDetailPage()) return
    const next = currentCatalogQueryParams()
    if (state.selectedPackId) next.set("pack_id", state.selectedPackId)
    const search = next.toString()
    const nextHref = `${globalScope.location.pathname}${search ? `?${search}` : ""}${globalScope.location.hash || ""}`
    const currentHref = `${globalScope.location.pathname}${globalScope.location.search || ""}${globalScope.location.hash || ""}`
    if (nextHref === currentHref) return
    globalScope.history.replaceState(null, "", nextHref)
  }

  function facetSignatureFromSelection(selection) {
    const out = []
    LOCAL_FACET_GROUPS.forEach((group) => {
      const bucket = selection && selection[group.key]
      if (!(bucket instanceof Set)) return
      Array.from(bucket)
        .map((value) => normalizeFacetValue(group.key, value))
        .filter(Boolean)
        .sort()
        .forEach((value) => {
          out.push(`${group.key}:${value}`)
        })
    })
    return out.sort()
  }

  function quickFilterSelection(key) {
    const preset = QUICK_FILTER_PRESETS[key]
    const selection = createFacetSelectionMap()
    if (!preset || !preset.groupKey) return selection
    const bucket = selection[preset.groupKey]
    if (bucket instanceof Set) {
      preset.values.forEach((value) => {
        bucket.add(normalizeFacetValue(preset.groupKey, value))
      })
    }
    return selection
  }

  function signaturesMatch(left, right) {
    if (!Array.isArray(left) || !Array.isArray(right)) return false
    if (left.length !== right.length) return false
    return left.every((value, index) => value === right[index])
  }

  function detectActiveQuickFilter() {
    const activeSignature = facetSignatureFromSelection(state.localFacets)
    if (!activeSignature.length) return "all"
    return Object.keys(QUICK_FILTER_PRESETS).find((key) => (
      key !== "all" && signaturesMatch(activeSignature, facetSignatureFromSelection(quickFilterSelection(key)))
    )) || ""
  }

  function rowMatchesQuickFilter(item, key) {
    const presetKey = String(key || "all").trim()
    if (!presetKey || presetKey === "all") return true
    if (presetKey === "bot_profile_pack" || presetKey === "extension_pack") {
      return normalizeFacetValue("pack_type", item && item.pack_type) === presetKey
    }
    if (presetKey === "featured") {
      return Boolean(item && item.featured)
    }
    if (presetKey === "low_risk") {
      return normalizeFacetValue("risk_level", item && item.risk_level) === "low"
    }
    return true
  }

  function updateQuickFilterButtons(rows = state.catalogRaw) {
    const items = Array.isArray(rows) ? rows : []
    quickFilterButtons().forEach((button) => {
      const key = String(button.getAttribute("data-market-quick-filter") || "").trim() || "all"
      const active = key === state.activeQuickFilter
      button.classList.toggle("is-active", active)
      button.setAttribute("aria-pressed", active ? "true" : "false")
      const countNode = button.querySelector(".market-sidebar-category-count")
      if (countNode) {
        countNode.textContent = String(items.filter((item) => rowMatchesQuickFilter(item, key)).length)
      }
    })
  }

  function applyQuickFilter(key) {
    const presetKey = Object.prototype.hasOwnProperty.call(QUICK_FILTER_PRESETS, key) ? key : "all"
    state.localFacets = quickFilterSelection(presetKey)
    state.activeQuickFilter = detectActiveQuickFilter() || presetKey
    applyLocalCatalogView()
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
    return findCatalogItemByPackId(selectedPackId)
  }

  function findCatalogItemByPackId(packId, rows = null) {
    const targetPackId = String(packId || "").trim()
    if (!targetPackId) return null
    const candidates = Array.isArray(rows)
      ? rows
      : [
        ...(Array.isArray(state.catalog) ? state.catalog : []),
        ...(Array.isArray(state.catalogRaw) ? state.catalogRaw : []),
      ]
    return candidates.find((item) => String(item && item.pack_id || "").trim() === targetPackId) || null
  }

  function resolveDefaultCatalogSelection(rows) {
    const helper = detailShellHelpers()
    if (helper && typeof helper.resolveDefaultSelectedPackId === "function") {
      return String(helper.resolveDefaultSelectedPackId({
        selectedPackId: state.selectedPackId,
        rows,
      }) || "").trim()
    }
    if (state.selectedPackId) return String(state.selectedPackId || "").trim()
    const items = Array.isArray(rows) ? rows : []
    const featured = items.find((item) => Boolean(item && item.featured))
    if (featured) return String(featured.pack_id || "").trim()
    return String((items[0] && items[0].pack_id) || "").trim()
  }

  function catalogRowHasRuntime(item) {
    if (!item || typeof item !== "object") return false
    return item.runtime_available !== false
  }

  function updateCatalogDetailActions() {
    const selected = selectedCatalogRow()
    const shellState = detailShellState(selected)
    const compareButton = byId("btnMarketCatalogCompare")
    const downloadButton = byId("btnMarketCatalogDownload")
    const downloadUrl = catalogPackageUrl(selected)
    const runtimeAvailable = shellState.hasSelection
      && selected
      && catalogRowHasRuntime(selected)
      && hasCapability("profile_pack.catalog.read")

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
      const available = Boolean(downloadUrl)
      downloadButton.disabled = !available
      downloadButton.setAttribute("aria-disabled", available ? "false" : "true")
      if (available) {
        downloadButton.dataset.downloadUrl = downloadUrl
        downloadButton.removeAttribute("title")
      } else {
        delete downloadButton.dataset.downloadUrl
        downloadButton.title = i18nMessage(
          "market.download.unavailable",
          "No public download is available for this catalog row.",
        )
      }
    }

    applyDetailMemberActionStates(selected)
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

  function detailSeed(item = selectedCatalogRow()) {
    const helper = marketCatalogContractHelpers()
    if (helper && typeof helper.buildDetailSeed === "function") {
      return helper.buildDetailSeed(item)
    }
    return {
      packId: String((item && item.pack_id) || "").trim(),
      title: String((item && item.pack_id) || "").trim() || "-",
      version: String((item && item.version) || "").trim(),
      packType: String((item && item.pack_type) || "bot_profile_pack").trim(),
      compatibility: String((item && item.compatibility) || "unknown").trim(),
      riskLevel: String((item && item.risk_level) || "unknown").trim(),
      maintainer: String((item && item.maintainer) || "unknown").trim(),
      reviewLabels: Array.isArray(item && item.review_labels) ? item.review_labels : [],
      warningFlags: Array.isArray(item && item.warning_flags) ? item.warning_flags : [],
      sections: Array.isArray(item && item.sections) ? item.sections : [],
      summary: String((item && (item.summary || item.description)) || "").trim(),
      featured: Boolean(item && item.featured),
      packagePath: String((item && item.package_path) || "").trim(),
      sourceSubmissionId: String((item && item.source_submission_id) || "").trim(),
      locale: state.uiLocale || "en-US",
    }
  }

  function detailShellState(item = selectedCatalogRow(), overrides = {}) {
    const helper = detailShellHelpers()
    const registry = variantRegistryHelpers()
    const availableVariants = registry && Array.isArray(registry.DEFAULT_VARIANTS)
      ? registry.DEFAULT_VARIANTS
      : null
    const selectedPackId = overrides.selectedPackId !== undefined
      ? String(overrides.selectedPackId || "").trim()
      : String((item && item.pack_id) || state.selectedPackId || "").trim()
    if (helper && typeof helper.buildDetailShellState === "function") {
      return helper.buildDetailShellState({
        selectedPackId,
        activeVariant: overrides.activeVariant !== undefined ? overrides.activeVariant : state.activeDetailVariant,
        availableVariants,
        viewportWidth: overrides.viewportWidth !== undefined ? overrides.viewportWidth : (globalScope.innerWidth || 0),
        normalizeVariantId: registry && typeof registry.normalizeVariantId === "function"
          ? registry.normalizeVariantId
          : null,
      })
    }
    const presentation = helper && typeof helper.resolveDetailPresentation === "function"
      ? helper.resolveDetailPresentation({
        viewportWidth: overrides.viewportWidth !== undefined ? overrides.viewportWidth : (globalScope.innerWidth || 0),
      })
      : "drawer"
    const fallbackVariants = Array.isArray(availableVariants) && availableVariants.length
      ? availableVariants.slice()
      : ["variant_1", "variant_2", "variant_3", "variant_4", "variant_5"]
    const requestedVariant = overrides.activeVariant !== undefined ? overrides.activeVariant : state.activeDetailVariant
    const fallbackActiveVariant = registry && typeof registry.normalizeVariantId === "function"
      ? registry.normalizeVariantId(requestedVariant)
      : String(requestedVariant || fallbackVariants[0]).trim() || fallbackVariants[0]
    return {
      selectedPackId,
      hasSelection: Boolean(selectedPackId),
      presentation,
      activeVariant: fallbackVariants.includes(fallbackActiveVariant) ? fallbackActiveVariant : fallbackVariants[0],
      availableVariants: fallbackVariants,
    }
  }

  function detailMemberActionStates(item = selectedCatalogRow()) {
    const helper = detailShellHelpers()
    const shellState = detailShellState(item)
    if (!(helper && typeof helper.buildDetailMemberActionStates === "function")) {
      return []
    }
    return helper.buildDetailMemberActionStates({
      selectedPackId: shellState.selectedPackId,
      isAuthenticated: hasAuthenticatedSession(),
      capabilities: {
        "templates.trial.request": hasCapability("templates.trial.request"),
        "templates.install": hasCapability("templates.install"),
        "templates.submit": hasCapability("templates.submit"),
        "member.installations.refresh": hasCapability("member.installations.refresh"),
        "profile_pack.community.submit": hasCapability("profile_pack.community.submit"),
      },
    })
  }

  function applyDetailMemberActionStates(item = selectedCatalogRow()) {
    detailMemberActionStates(item).forEach((actionState) => {
      const node = byId(actionState.controlId)
      if (!node) return
      node.classList.toggle("hidden", !actionState.visible)
      node.disabled = Boolean(actionState.disabled)
      node.setAttribute("aria-disabled", actionState.disabled ? "true" : "false")
      if (actionState.blockedReason === "capability") {
        node.title = i18nFormat(
          "capability.locked_hint",
          "Requires capability: {capability}",
          { capability: actionState.capability },
        )
      } else {
        node.removeAttribute("title")
      }
    })
  }

  function normalizeUniqueStringList(values) {
    const rows = Array.isArray(values) ? values : [values]
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

  function availableInstallSections(item = selectedCatalogRow()) {
    return installSectionState(item).availableSections
  }

  function installSectionSelectionKey(item = selectedCatalogRow()) {
    return String(detailSeed(item).packId || "").trim()
  }

  function installSectionState(item = selectedCatalogRow(), overrides = {}) {
    const key = installSectionSelectionKey(item)
    const hasSavedSelection = overrides.hasSavedSelection !== undefined
      ? Boolean(overrides.hasSavedSelection)
      : Boolean(key) && Object.prototype.hasOwnProperty.call(state.installSectionSelections, key)
    const savedSections = overrides.savedSections !== undefined
      ? overrides.savedSections
      : (hasSavedSelection ? state.installSectionSelections[key] : [])
    const helper = detailShellHelpers()
    if (helper && typeof helper.buildInstallSectionSelectionState === "function") {
      return helper.buildInstallSectionSelectionState({
        availableSections: item && item.sections,
        savedSections,
        hasSavedSelection,
        describeSection: sectionDisplayMeta,
      })
    }
    const availableSections = normalizeUniqueStringList(item && item.sections)
    const selectedSections = hasSavedSelection
      ? normalizeUniqueStringList(savedSections).filter((section) => availableSections.includes(section))
      : availableSections.slice()
    const statefulCount = availableSections.filter((sectionName) => {
      const meta = sectionDisplayMeta(sectionName)
      return Boolean(meta && (meta.stateful || meta.localData))
    }).length
    let summaryKey = "market.install.sections.summary"
    if (!availableSections.length) {
      summaryKey = "market.install.sections.empty"
    } else if (!selectedSections.length) {
      summaryKey = "market.install.sections.none_selected"
    } else if (statefulCount > 0) {
      summaryKey = "market.install.sections.summary_stateful"
    }
    return {
      availableSections,
      selectedSections,
      statefulCount,
      summaryKey,
      summaryValues: {
        selected: selectedSections.length,
        total: availableSections.length,
        stateful: statefulCount,
      },
    }
  }

  function resolvedInstallSections(item = selectedCatalogRow()) {
    return installSectionState(item).selectedSections
  }

  function rememberInstallSections(item = selectedCatalogRow(), sections = []) {
    const key = installSectionSelectionKey(item)
    if (!key) return
    state.installSectionSelections[key] = installSectionState(item, {
      savedSections: sections,
      hasSavedSelection: true,
    }).selectedSections
  }

  function readSelectedInstallSections() {
    const inputs = Array.from(document.querySelectorAll("input[data-market-install-section]"))
    return normalizeUniqueStringList(
      inputs
        .filter((node) => Boolean(node.checked))
        .map((node) => String(node.getAttribute("data-market-install-section") || "")),
    )
  }

  function sectionDisplayMeta(sectionName) {
    const guidance = profilePackGuidanceHelpers()
    return guidance && typeof guidance.describeSection === "function"
      ? guidance.describeSection(sectionName)
      : {
        name: String(sectionName || ""),
        known: false,
        titleKey: "",
        descriptionKey: "",
        stateful: false,
        localData: false,
      }
  }

  function syncInstallSectionSummary(item = selectedCatalogRow()) {
    const summaryNode = byId("marketInstallSectionSummary")
    if (!summaryNode) return
    const selected = readSelectedInstallSections()
    rememberInstallSections(item, selected)
    const installState = installSectionState(item, {
      savedSections: selected,
      hasSavedSelection: true,
    })
    if (!installState.availableSections.length) {
      summaryNode.textContent = i18nMessage(
        "market.install.sections.empty",
        "No declared sections on this pack.",
      )
      return
    }
    if (!installState.selectedSections.length) {
      summaryNode.textContent = i18nMessage(
        "market.install.sections.none_selected",
        "No sections selected. Install will skip section sync.",
      )
      return
    }
    summaryNode.textContent = installState.statefulCount > 0
      ? i18nFormat(
        "market.install.sections.summary_stateful",
        "{selected}/{total} sections selected · {stateful} stateful/local sections can be skipped",
        installState.summaryValues,
      )
      : i18nFormat(
        "market.install.sections.summary",
        "{selected}/{total} sections selected for install sync",
        installState.summaryValues,
      )
  }

  function renderMarketInstallSectionList(item = selectedCatalogRow()) {
    const root = byId("marketInstallSectionList")
    if (!root) return
    root.innerHTML = ""
    const installState = installSectionState(item)
    if (!installState.availableSections.length) {
      syncInstallSectionSummary(item)
      return
    }
    const selectedSet = new Set(installState.selectedSections)
    installState.availableSections.forEach((sectionName) => {
      const meta = sectionDisplayMeta(sectionName)
      const label = document.createElement("label")
      label.className = "profile-pack-section-item market-install-section-item"

      const input = document.createElement("input")
      input.type = "checkbox"
      input.checked = selectedSet.has(sectionName)
      input.setAttribute("data-market-install-section", sectionName)
      input.addEventListener("change", () => {
        syncInstallSectionSummary(item)
      })
      label.appendChild(input)

      const body = document.createElement("span")
      body.className = "profile-pack-section-body"
      const titleRow = document.createElement("span")
      titleRow.className = "profile-pack-section-title-row"

      const title = document.createElement("span")
      title.className = "profile-pack-section-title"
      title.textContent = meta.known && meta.titleKey
        ? i18nMessage(meta.titleKey, sectionName)
        : sectionName
      titleRow.appendChild(title)

      if (meta.stateful) {
        appendPill(
          titleRow,
          i18nMessage("profile_pack.section.badge.stateful", "Stateful"),
          "warning",
        )
      }
      if (meta.localData) {
        appendPill(
          titleRow,
          i18nMessage("profile_pack.section.badge.local_data", "Local Data"),
          "neutral",
        )
      }

      body.appendChild(titleRow)

      const description = document.createElement("span")
      description.className = "profile-pack-section-description"
      description.textContent = meta.known && meta.descriptionKey
        ? i18nMessage(meta.descriptionKey, sectionName)
        : sectionName
      body.appendChild(description)

      label.appendChild(body)
      root.appendChild(label)
    })
    syncInstallSectionSummary(item)
  }

  function hasAuthenticatedSession() {
    return !state.authRequired || state.capabilities.authenticated === true
  }

  function ensureMemberActionCapability(capability, actionKey) {
    if (hasCapability(capability)) return true
    state.authPromptRequested = true
    setMarketDetailExpanded(true)
    updateSummary({
      ...(selectedCatalogRow() || {}),
      status: "auth_required",
      message: i18nFormat(
        "market.detail.auth_required_action",
        "Login is required before using {action}.",
        { action: actionKey },
      ),
    })
    updateAuthUi()
    const passwordNode = byId("marketAuthPassword")
    if (passwordNode && typeof passwordNode.focus === "function") {
      passwordNode.focus()
    }
    return false
  }

  function renderDetailVariantTabs(item = selectedCatalogRow()) {
    const root = byId("marketDetailVariantTabs")
    if (!root) return
    root.innerHTML = ""
    const shellState = detailShellState(item)
    state.activeDetailVariant = shellState.activeVariant
    shellState.availableVariants.forEach((variantId, index) => {
      const button = document.createElement("button")
      button.type = "button"
      button.className = "locale-pill"
      if (variantId === shellState.activeVariant) {
        button.classList.add("is-active")
        button.setAttribute("aria-pressed", "true")
      } else {
        button.setAttribute("aria-pressed", "false")
      }
      button.textContent = i18nMessage(`market.variant.tab_${index + 1}`, `Variant ${index + 1}`)
      button.addEventListener("click", () => {
        state.activeDetailVariant = detailShellState(item, { activeVariant: variantId }).activeVariant
        renderDetailVariantViewport(item)
        renderDetailVariantTabs(item)
      })
      root.appendChild(button)
    })
  }

  function renderDetailVariantViewport(item = selectedCatalogRow()) {
    const root = byId("marketDetailVariantViewport")
    if (!root) return
    restoreDetailEmbeddedControls()
    const registry = variantRegistryHelpers()
    const context = detailSeed(item)
    const shellState = detailShellState(item)
    const variantId = shellState.activeVariant
    state.activeDetailVariant = variantId
    const renderer = registry && typeof registry.getVariantRenderer === "function"
      ? registry.getVariantRenderer(variantId)
      : null
    root.innerHTML = typeof renderer === "function"
      ? renderer(context)
      : ""
  }

  function renderDetailPublicFacts(item = selectedCatalogRow()) {
    const root = byId("marketDetailPublicFacts")
    if (!root) return
    root.innerHTML = ""
    const context = detailSeed(item)
    const helper = detailShellHelpers()
    const rows = helper && typeof helper.buildDetailPublicFactRows === "function"
      ? helper.buildDetailPublicFactRows(context, {
        message: i18nMessage,
        enumLabel,
        localizedList,
      })
      : [
        { label: i18nMessage("table.header.pack", "Pack"), value: context.title || context.packId || "-" },
        { label: i18nMessage("table.header.version", "Version"), value: context.version || "-" },
        { label: i18nMessage("table.header.pack_type", "Pack Type"), value: enumLabel("pack_type", context.packType) },
        { label: i18nMessage("market.evidence.compatibility", "compatibility"), value: enumLabel("compatibility", context.compatibility) },
        { label: i18nMessage("table.header.risk", "Risk"), value: enumLabel("risk", context.riskLevel) },
        { label: i18nMessage("table.header.maintainer", "Maintainer"), value: context.maintainer || "-" },
        { label: i18nMessage("table.header.labels", "Labels"), value: localizedList("review_label", context.reviewLabels) },
        { label: i18nMessage("table.header.flags", "Flags"), value: localizedList("warning_flag", context.warningFlags) },
      ]
    rows.forEach((itemRow) => {
      const card = document.createElement("div")
      card.className = "detail-card"
      const label = document.createElement("div")
      label.className = "detail-card-label"
      label.textContent = itemRow.label
      card.appendChild(label)
      const value = document.createElement("div")
      value.className = "detail-card-value"
      value.textContent = itemRow.value
      card.appendChild(value)
      root.appendChild(card)
    })
  }

  function syncDetailActionPrefill(item = selectedCatalogRow()) {
    const context = detailSeed(item)
    const packNode = byId("marketPackId")
    if (packNode) {
      packNode.value = context.packId || ""
    }
    const templateNode = byId("marketTemplateId")
    if (templateNode && !String(templateNode.value || "").trim()) {
      templateNode.value = context.packId || ""
    }
  }

  function renderSelectedDetailShell(item = selectedCatalogRow()) {
    if (!item) return
    syncDetailActionPrefill(item)
    renderDetailVariantViewport(item)
    mountDetailEmbeddedControls()
    renderMarketInstallSectionList(item)
    updateCatalogDetailActions()
    maybeLoadDetailInstallations()
  }

  function detailControlStore() {
    return byId("marketDetailControlStore")
  }

  function detailControlSlot(slotName) {
    const viewport = byId("marketDetailVariantViewport")
    if (!viewport) return null
    return viewport.querySelector(`[data-market-detail-slot="${slotName}"]`)
  }

  function restoreDetailEmbeddedControls() {
    const store = detailControlStore()
    if (!store) return
    ;[
      "marketDetailInstallSectionsShell",
      "marketDetailInstallOptionsShell",
    ].forEach((controlId) => {
      const node = byId(controlId)
      if (node && node.parentElement !== store) {
        store.appendChild(node)
      }
    })
  }

  function mountDetailEmbeddedControls() {
    const store = detailControlStore()
    if (!store) return
    const placements = [
      ["marketDetailInstallSectionsShell", "install_sections"],
      ["marketDetailInstallOptionsShell", "install_options"],
    ]
    placements.forEach(([controlId, slotName]) => {
      const node = byId(controlId)
      const slot = detailControlSlot(slotName)
      if (!node) return
      if (slot) {
        slot.replaceChildren(node)
        return
      }
      if (node.parentElement !== store) {
        store.appendChild(node)
      }
    })
  }

  function maybeLoadDetailInstallations() {
    if (!isDetailPage()) return
    if (!selectedCatalogRow()) return
    if (state.memberInstallationsRequested) return
    if (!hasCapability("member.installations.read")) return
    state.memberInstallationsRequested = true
    void loadMarketInstallations()
  }

  function fallbackCapabilityOperations(role, options = {}) {
    const helper = capabilityGuardHelpers()
    if (helper && helper.fallbackCapabilityOperations) {
      return helper.fallbackCapabilityOperations(role, {
        authenticated: options.authenticated,
        allowAnonymousMember: options.allowAnonymousMember,
        baseOperations: MARKET_BASE_FALLBACK_OPERATIONS,
        memberOperations: MARKET_MEMBER_FALLBACK_OPERATIONS,
        reviewerOperations: [],
        adminOperations: [],
        anonymousMemberFallbackOperations: ANONYMOUS_MEMBER_FALLBACK_OPERATIONS,
      })
    }
    const normalized = String(role || "").trim().toLowerCase()
    const authenticated = options.authenticated !== false
    const allowAnonymousMember = options.allowAnonymousMember === true
    const base = MARKET_BASE_FALLBACK_OPERATIONS
    const member = MARKET_MEMBER_FALLBACK_OPERATIONS
    if (normalized === "admin" || normalized === "reviewer" || normalized === "member") {
      if (normalized === "member" && !authenticated && allowAnonymousMember) {
        return ANONYMOUS_MEMBER_FALLBACK_OPERATIONS.slice()
      }
      return Array.from(new Set([...base, ...member]))
    }
    return base
  }

  function hasCapability(capability) {
    const helper = capabilityGuardHelpers()
    const required = String(capability || "").trim()
    if (!required) return true
    const operations = Array.isArray(state.capabilities.operations)
      ? state.capabilities.operations
      : []
    if (helper && helper.hasCapability) {
      return helper.hasCapability(required, {
        pageMode: state.pageMode,
        reviewerAdminBridgeActive: false,
        operations,
      })
    }
    return operations.includes(required)
  }

  function applyCapabilityGuardToControl(controlId) {
    const required = CONTROL_CAPABILITY_MAP[controlId] || ""
    if (!required) return
    const node = byId(controlId)
    if (!node) return
    const allowed = hasCapability(required)
    const domHelper = capabilityGuardDomHelpers()
    if (domHelper && domHelper.applyCapabilityGuardToNode) {
      domHelper.applyCapabilityGuardToNode(node, {
        allowed,
        requiredCapability: required,
        lockedHint: i18nFormat(
          "capability.locked_hint",
          "Requires capability: {capability}",
          { capability: required },
        ),
      })
      return
    }
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
  }

  function setCapabilities(payload) {
    const data = payload && typeof payload === "object" ? payload : {}
    const role = String(data.role || "member").trim().toLowerCase() || "member"
    const authenticated = typeof data.authenticated === "boolean"
      ? data.authenticated
      : (!state.authRequired || (Boolean(state.token) && state.token !== "no-auth"))
    const anonymousMember = data.anonymous_member === true
    const operations = Array.isArray(data.operations)
      ? data.operations.map((item) => String(item || "").trim()).filter(Boolean)
      : fallbackCapabilityOperations(role, {
        authenticated,
        allowAnonymousMember: state.allowAnonymousMember,
      })
    state.capabilities = {
      role,
      authenticated,
      anonymousMember,
      operations: Array.from(new Set(operations)),
    }
    applyCapabilityGuards()
    updateCatalogDetailActions()
  }

  async function refreshCapabilities() {
    const query = {}
    if (!state.authRequired) {
      query.role = fixedAuthRole()
    }
    if (state.pageMode && state.pageMode !== "auto") {
      query.page_mode = state.pageMode
    }
    const response = await api(`/api/ui/capabilities${queryString(query)}`)
    if (!response || response.status >= 400 || !(response.data && response.data.ok)) {
      const fallbackAnonymousMember = (
        state.authRequired &&
        state.allowAnonymousMember &&
        !state.token &&
        state.pageMode !== "reviewer" &&
        state.pageMode !== "admin"
      )
      const fallbackRole = fallbackAnonymousMember
        ? "member"
        : (state.authRequired ? "public" : fixedAuthRole())
      setCapabilities({
        role: fallbackRole,
        authenticated: !fallbackAnonymousMember && (!state.authRequired || (Boolean(state.token) && state.token !== "no-auth")),
        anonymous_member: fallbackAnonymousMember,
        operations: fallbackCapabilityOperations(fallbackRole, {
          authenticated: !fallbackAnonymousMember && (!state.authRequired || (Boolean(state.token) && state.token !== "no-auth")),
          allowAnonymousMember: state.allowAnonymousMember,
        }),
      })
      return response
    }
    setCapabilities(response.data)
    return response
  }

  function renderLog(name, payload) {
    const node = byId("marketResult")
    if (!node) return
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
      const shellState = detailShellState(selectedCatalogRow(), {
        selectedPackId: state.selectedPackId,
      })
      state.activeDetailVariant = shellState.activeVariant
      area.classList.toggle("hidden", !nextState)
      area.setAttribute("aria-hidden", nextState ? "false" : "true")
      area.classList.toggle("is-drawer", shellState.presentation === "drawer")
      area.classList.toggle("is-sheet", shellState.presentation === "sheet")
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

  function localizedCatalogSearchTerms(item) {
    if (!item || typeof item !== "object") return []
    const packId = String(item.pack_id || "").trim()
    return [
      resolveCatalogPackTitle(item),
      localizedPackLabel(packId, { includeId: true }),
      localizedPackDescription(packId, String(item.description || item.summary || "").trim()),
      localizedPackFeaturedNote(packId, String(item.featured_note || "").trim()),
      localizedSourceSubmission(item.source_submission_id, packId),
      resolveCatalogPackSubtitle(item),
      enumLabel("risk", String(item.risk_level || "unknown")),
      enumLabel("compatibility", String(item.compatibility || "unknown")),
      ...normalizeStringArray(item.review_labels).map((value) => enumLabel("review_label", value)),
      ...normalizeStringArray(item.warning_flags).map((value) => enumLabel("warning_flag", value)),
      ...normalizeStringArray(item.compatibility_issues),
    ]
      .map((value) => String(value || "").trim())
      .filter(Boolean)
  }

  function marketRowSearchText(item) {
    const localizedTerms = localizedCatalogSearchTerms(item)
    const helper = marketCatalogContractHelpers()
    if (helper && typeof helper.buildPublicCatalogSearchText === "function") {
      return helper.buildPublicCatalogSearchText(item, { localizedTerms })
    }
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
    return [packId, packType, risk, compatibility, labels, flags, issues, source, version, localizedTerms.join(" ")]
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

  function facetLabel(group, value) {
    if (value === "unknown") {
      return i18nMessage("market.filter.value.unknown", "unknown")
    }
    if (group.key === "pack_type") {
      if (value === "bot_profile_pack") {
        return i18nMessage("option.pack_type.bot_profile_pack", "Bot Profile Pack (Full Bot Setup)")
      }
      if (value === "extension_pack") {
        return i18nMessage("option.pack_type.extension_pack", "Extension Pack (Skills/Personas/MCP/Plugins)")
      }
    }
    if (group.key === "risk_level") {
      if (value === "high") return i18nMessage("option.risk.high", "high")
      if (value === "medium") return i18nMessage("option.risk.medium", "medium")
      if (value === "low") return i18nMessage("option.risk.low", "low")
    }
    if (group.key === "featured") {
      if (value === "true") return i18nMessage("option.featured_status.true", "featured only")
      if (value === "false") return i18nMessage("option.featured_status.false", "non-featured only")
    }
    if (group.key === "compatibility") {
      return enumLabel("compatibility", value)
    }
    if (group.key === "review_label") {
      return enumLabel("review_label", value)
    }
    if (group.key === "warning_flag") {
      return enumLabel("warning_flag", value)
    }
    return value
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

  function applyLocalCatalogView(options = {}) {
    const baseRows = Array.isArray(state.catalogRaw) ? state.catalogRaw : []
    const searchedRows = baseRows.filter((item) => rowMatchesSearch(item, state.localSearch))
    const filteredRows = searchedRows.filter((item) => rowMatchesFacets(item))
    const sortedRows = sortCatalogRows(filteredRows)
    state.catalog = sortedRows
    updateCatalogTable(state.catalog, { skipFilterSync: true })
    updateCatalogCountChips(state.catalog, baseRows)
    renderFacetFilters(searchedRows)
    updateQuickFilterButtons(baseRows)
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
    if (isDetailPage() && state.selectedPackId) {
      const selected = selectedCatalogRow()
      if (selected) {
        renderSelectedDetailShell(selected)
      }
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
    state.activeQuickFilter = detectActiveQuickFilter()
    applyLocalCatalogView()
  }

  function renderFacetFilters(rows) {
    const root = byId("marketFacetFilters")
    if (!root) return
    root.innerHTML = ""
    const buckets = computeFacetBuckets(rows)
    LOCAL_FACET_GROUPS.forEach((group) => {
      const detail = document.createElement("details")
      detail.className = "market-facet-group"
      detail.open = true
      const summary = document.createElement("summary")
      summary.className = "market-facet-title"
      summary.textContent = i18nMessage(group.titleKey, group.titleFallback)
      detail.appendChild(summary)
      const list = document.createElement("div")
      list.className = "market-facet-list"
      const entries = sortedFacetEntries(group, completeFacetBucket(group, buckets[group.key] || new Map()))
      if (!entries.length) {
        const empty = document.createElement("div")
        empty.className = "market-facet-empty"
        empty.textContent = i18nMessage("market.filter.group_empty", "No values")
        list.appendChild(empty)
      } else {
        entries.forEach(([value, count]) => {
          const row = document.createElement("label")
          row.className = "market-facet-option"
          const checkbox = document.createElement("input")
          checkbox.type = "checkbox"
          checkbox.checked = Boolean(state.localFacets[group.key] && state.localFacets[group.key].has(value))
          checkbox.setAttribute("data-market-facet-group", group.key)
          checkbox.setAttribute("data-market-facet-value", value)
          checkbox.addEventListener("change", () => {
            onFacetToggle(group.key, value, checkbox.checked)
          })
          row.appendChild(checkbox)
          const label = document.createElement("span")
          label.className = "market-facet-option-label"
          label.textContent = facetLabel(group, value)
          row.appendChild(label)
          const badge = document.createElement("span")
          badge.className = "market-facet-option-count"
          badge.textContent = String(count)
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
    if (!node) return
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
    const healthNode = byId("marketHealthLine")
    if (!healthNode) return
    healthNode.textContent = i18nFormat(
      "market.health.line",
      "health: {status} {url}",
      { status, url },
    ).trim()
  }

  function updateSummary(data) {
    const summaryNode = byId("marketSummary")
    const detailsNode = byId("marketDetails")
    const helper = detailShellHelpers()
    const summaryView = helper && typeof helper.buildDetailSummaryViewModel === "function"
      ? helper.buildDetailSummaryViewModel(data, {
        message: i18nMessage,
        format: i18nFormat,
        enumLabel,
        resolvePackLabel: localizedPackLabel,
      })
      : null
    if (!data || typeof data !== "object") {
      state.lastSummary = null
      if (summaryNode) {
        summaryNode.textContent = summaryView ? summaryView.text : i18nMessage("market.summary.idle", "No operation yet.")
      }
      if (detailsNode) {
        detailsNode.textContent = ""
      }
      renderEvidence(null)
      return
    }
    state.lastSummary = data
    if (summaryNode) {
      summaryNode.textContent = summaryView
        ? summaryView.text
        : i18nMessage("market.summary.idle", "No operation yet.")
    }
    renderEvidence(data)
    if (detailsNode) {
      detailsNode.textContent = JSON.stringify(data, null, 2)
    }
  }

  function renderEvidence(data) {
    const node = byId("marketEvidenceRows")
    if (!node) return
    node.innerHTML = ""
    if (!data || typeof data !== "object") return
    const capabilitySummary = data.capability_summary || {}
    const reviewEvidence = data.review_evidence || {}
    const pluginInstall = data.plugin_install && typeof data.plugin_install === "object" ? data.plugin_install : {}
    const latestExecution = pluginInstall.latest_execution && typeof pluginInstall.latest_execution === "object"
      ? pluginInstall.latest_execution
      : null
    const executionSummary = latestExecution && compareViewHelper && typeof compareViewHelper.summarizePluginInstallExecution === "function"
      ? compareViewHelper.summarizePluginInstallExecution(latestExecution)
      : null
    const executionGroups = []
    if (executionSummary && executionSummary.groups) {
      if (Array.isArray(executionSummary.groups.policy_blocked) && executionSummary.groups.policy_blocked.length) {
        executionGroups.push(
          i18nFormat("market.evidence.plugin_install_failure_group", "{group}: {items}", {
            group: i18nMessage("profile_pack.review.group.policy_blocked", "policy"),
            items: executionSummary.groups.policy_blocked.join("|"),
          }),
        )
      }
      if (Array.isArray(executionSummary.groups.command_failed) && executionSummary.groups.command_failed.length) {
        executionGroups.push(
          i18nFormat("market.evidence.plugin_install_failure_group", "{group}: {items}", {
            group: i18nMessage("profile_pack.review.group.command_failed", "failed"),
            items: executionSummary.groups.command_failed.join("|"),
          }),
        )
      }
      if (Array.isArray(executionSummary.groups.timed_out) && executionSummary.groups.timed_out.length) {
        executionGroups.push(
          i18nFormat("market.evidence.plugin_install_failure_group", "{group}: {items}", {
            group: i18nMessage("profile_pack.review.group.timed_out", "timeout"),
            items: executionSummary.groups.timed_out.join("|"),
          }),
        )
      }
    }
    const rows = [
      {
        label: i18nMessage("market.evidence.featured_note", "featured note"),
        value: localizedPackFeaturedNote(data.pack_id, String(data.featured_note || "-")),
      },
      {
        label: i18nMessage("market.evidence.compatibility", "compatibility"),
        value: enumLabel("compatibility", String(data.compatibility || "unknown")),
      },
      {
        label: i18nMessage("market.evidence.declared_capabilities", "declared capabilities"),
        value: Array.isArray(capabilitySummary.declared) ? capabilitySummary.declared.join(", ") || "-" : "-",
      },
      {
        label: i18nMessage("market.evidence.review_labels", "review labels"),
        value: localizedList("review_label", reviewEvidence.review_labels),
      },
      {
        label: i18nMessage("market.evidence.plugin_install_status", "plugin install status"),
        value: enumLabel("plugin_install_status", String(pluginInstall.status || "unknown")),
      },
      {
        label: i18nMessage("market.evidence.plugin_install_execution", "plugin install execution"),
        value: executionSummary
          ? i18nFormat(
            "market.evidence.plugin_install_execution_counts",
            "{status} (installed={installed}, failed={failed}, blocked={blocked})",
            {
              status: enumLabel("plugin_install_status", executionSummary.status),
              installed: executionSummary.installed_count,
              failed: executionSummary.failed_count,
              blocked: executionSummary.blocked_count,
            },
          )
          : "-",
      },
      {
        label: i18nMessage(
          "market.evidence.plugin_install_failure_groups",
          "plugin install failure groups",
        ),
        value: executionGroups.length ? executionGroups.join(" ; ") : "-",
      },
    ]
    rows.forEach((item) => {
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
      node.appendChild(card)
    })
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

    const summaryNode = byId("marketSummary")
    if (summaryNode) {
      summaryNode.textContent = view.summary
    }
  }

  function applyAuthOptions(roles) {
    const roleNode = byId("marketAuthRole")
    if (!roleNode) return
    roleNode.innerHTML = ""
    const preferredRole = fixedAuthRole()
    const inputRoles = Array.isArray(roles) ? roles : []
    const effectiveRoles = inputRoles.includes(preferredRole) ? [preferredRole] : [preferredRole]
    effectiveRoles.forEach((role) => {
      const option = document.createElement("option")
      option.value = role
      if (role === "member") {
        option.setAttribute("data-i18n-key", "option.member")
        option.textContent = i18nMessage("option.member", "member")
      } else if (role === "reviewer") {
        option.setAttribute("data-i18n-key", "option.reviewer")
        option.textContent = i18nMessage("option.reviewer", "reviewer")
      } else if (role === "admin") {
        option.setAttribute("data-i18n-key", "option.admin")
        option.textContent = i18nMessage("option.admin", "admin")
      } else {
        option.textContent = role
      }
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
    const role = String(roleNode.value || "").trim().toLowerCase()
    fieldsNode.classList.toggle("hidden", role !== "reviewer")
  }

  function updateAuthUi() {
    const helper = marketAuthSurfaceHelpers()
    const surface = helper && typeof helper.describeMarketAuthSurface === "function"
      ? helper.describeMarketAuthSurface({
        authRequired: state.authRequired,
        allowAnonymousMember: state.allowAnonymousMember,
        authenticated: state.capabilities.authenticated === true,
        availableRoles: state.availableRoles,
        promptRequested: state.authPromptRequested,
      })
      : {
        mode: state.authRequired ? "required" : "disabled",
        rolesText: state.availableRoles.length ? state.availableRoles.join(", ") : "none",
        canBrowseAnonymously: false,
        showAuthPanel: state.authRequired,
      }
    const rolesText = surface.rolesText
    const authLine = byId("marketAuthLine")
    const roleLine = byId("marketRoleLine")
    const authPanel = byId("marketAuthPanel")
    const authHelp = byId("marketAuthHelp")
    const authGuidance = byId("marketAuthGuidance")
    const openLoginButton = byId("btnMarketOpenLoginPanel")
    if (authLine) {
      authLine.textContent = i18nFormat(
        "market.auth.line",
        "auth: {status}",
        {
          status: surface.mode === "optional"
            ? i18nFormat("auth.status.optional", "optional ({roles})", { roles: rolesText })
            : (state.authRequired
              ? i18nFormat("auth.status.required", "required ({roles})", { roles: rolesText })
              : i18nMessage("auth.status.disabled", "disabled")),
        },
      )
    }
    if (roleLine) {
      roleLine.textContent = i18nFormat(
        "market.role.line",
        "role: {role}",
        {
          role: state.authRole || i18nMessage("market.role.not_logged_in", "not logged in"),
        },
      )
    }
    if (authPanel) {
      const shouldShowAuthPanel = surface.showAuthPanel
      authPanel.classList.toggle("hidden", !shouldShowAuthPanel)
      authPanel.toggleAttribute("hidden", !shouldShowAuthPanel)
      authPanel.setAttribute("aria-hidden", shouldShowAuthPanel ? "false" : "true")
    }
    if (authHelp) {
      authHelp.textContent = surface.mode === "optional"
        ? i18nMessage(
          "market.login.hint.optional",
          "Anonymous browsing and installation are available. Login is only required for submission and other protected actions.",
        )
        : (state.authRequired
          ? i18nMessage(
            "market.login.hint.required",
            "This deployment requires credentials before protected actions can run. Use the operator-provided onboarding flow if you do not have an account yet.",
          )
          : i18nMessage(
            "market.login.hint",
            "When auth is disabled, this panel remains hidden.",
          ))
    }
    if (authGuidance) {
      const shouldShowGuidance = surface.mode === "optional" && !surface.showAuthPanel
      authGuidance.textContent = i18nMessage(
        "market.auth.guidance.optional",
        "Browse and install anonymously. Open login only when you need to submit, manage protected actions, or use a higher-privilege role.",
      )
      authGuidance.classList.toggle("hidden", !shouldShowGuidance)
      authGuidance.toggleAttribute("hidden", !shouldShowGuidance)
    }
    if (openLoginButton) {
      const shouldShowOpenButton = surface.mode === "optional" && !surface.showAuthPanel
      openLoginButton.classList.toggle("hidden", !shouldShowOpenButton)
      openLoginButton.toggleAttribute("hidden", !shouldShowOpenButton)
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
    const hide = (node, value) => {
      if (!node) return
      node.classList.toggle("hidden", Boolean(value))
    }

    if (!state.authResolved) {
      hide(memberLink, true)
      hide(reviewerLink, true)
      hide(adminLink, true)
      hide(fullLink, true)
      return
    }

    // Public/no-auth market should only expose member console entry.
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
    state.allowAnonymousMember = Boolean(response.data.allow_anonymous_member)
    state.authPromptRequested = false
    state.authResolved = true
    state.availableRoles = Array.isArray(response.data.available_roles) ? response.data.available_roles : []
    applyAuthOptions(state.availableRoles)
    if (!state.authRequired) {
      state.token = "no-auth"
      state.authRole = "member"
    }
    updateAuthUi()
    await refreshCapabilities()
  }

  async function login() {
    const role = fixedAuthRole()
    const password = String(byId("marketAuthPassword")?.value || "")
    const body = { role, password }
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
    state.authResolved = true
    state.authRole = String(response.data.role || role)
    state.availableRoles = Array.isArray(response.data.available_roles)
      ? response.data.available_roles
      : state.availableRoles
    state.authPromptRequested = true
    state.memberInstallationsRequested = false
    applyAuthOptions(state.availableRoles)
    updateAuthUi()
    await refreshCapabilities()
    maybeLoadDetailInstallations()
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
      user_id: "webui-user",
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
    const helper = profilePackMarketHelpers()
    const input = {
      preflight: Boolean(byId("marketInstallPreflight") && byId("marketInstallPreflight").checked),
      forceReinstall: Boolean(byId("marketInstallForceReinstall") && byId("marketInstallForceReinstall").checked),
      sourcePreference: String(byId("marketInstallSourcePreference")?.value || "auto").trim() || "auto",
      selectedSections: readSelectedInstallSections(),
    }
    if (helper && typeof helper.buildInstallOptions === "function") {
      return helper.buildInstallOptions(input)
    }
    return {
      preflight: Boolean(input.preflight),
      force_reinstall: Boolean(input.forceReinstall),
      source_preference: String(input.sourcePreference || "auto").trim() || "auto",
      selected_sections: normalizeUniqueStringList(input.selectedSections),
    }
  }

  function readMarketUploadOptions() {
    const helper = profilePackMarketHelpers()
    const input = {
      scanMode: String(byId("marketUploadScanMode")?.value || "balanced").trim() || "balanced",
      visibility: String(byId("marketUploadVisibility")?.value || "community").trim() || "community",
      replaceExisting: Boolean(byId("marketUploadReplaceExisting") && byId("marketUploadReplaceExisting").checked),
    }
    if (helper && typeof helper.buildUploadOptions === "function") {
      return helper.buildUploadOptions(input)
    }
    return {
      scan_mode: input.scanMode,
      visibility: input.visibility,
      replace_existing: Boolean(input.replaceExisting),
    }
  }

  function readMarketSubmitOptions() {
    const helper = profilePackMarketHelpers()
    const input = {
      packType: String(byId("marketSubmitPackType")?.value || "bot_profile_pack").trim() || "bot_profile_pack",
      selectedSections: String(byId("marketSubmitSelectedSections")?.value || ""),
      redactionMode: String(byId("marketSubmitRedactionMode")?.value || "exclude_secrets").trim() || "exclude_secrets",
      replaceExisting: Boolean(byId("marketSubmitReplaceExisting") && byId("marketSubmitReplaceExisting").checked),
    }
    if (helper && typeof helper.buildProfilePackSubmitOptions === "function") {
      return helper.buildProfilePackSubmitOptions(input, {
        includeSelectedItemPaths: false,
        includeSource: false,
        includeIdempotencyKey: true,
      })
    }
    if (helper && typeof helper.buildSubmitOptions === "function") {
      return helper.buildSubmitOptions(input)
    }
    return {
      pack_type: input.packType,
      selected_sections: normalizeList(input.selectedSections),
      redaction_mode: input.redactionMode,
      replace_existing: Boolean(input.replaceExisting),
    }
  }

  function setMarketInstallationsState(status, message) {
    const node = byId("marketInstallationsState")
    if (!node) return
    node.classList.remove("is-neutral", "is-warning", "is-danger", "is-success")
    if (status === "loading" || status === "warning") node.classList.add("is-warning")
    else if (status === "error") node.classList.add("is-danger")
    else if (status === "success") node.classList.add("is-success")
    else node.classList.add("is-neutral")
    node.textContent = message
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

  function setMarketInstallationActionBusy(button, busy) {
    if (!button) return
    button.disabled = Boolean(busy)
    button.setAttribute("aria-busy", busy ? "true" : "false")
  }

  function focusMarketInstallation(item) {
    const templateId = String(item && item.template_id || "").trim()
    const templateNode = byId("marketTemplateId")
    if (templateNode) {
      templateNode.value = templateId
    }
  }

  async function reinstallMarketInstallation(item, button) {
    const templateId = String(item && item.template_id || "").trim()
    if (!templateId) return
    const actor = marketActor()
    const installOptions = item && typeof item.install_options === "object"
      ? { ...item.install_options, force_reinstall: true }
      : { force_reinstall: true }
    setMarketInstallationActionBusy(button, true)
    const response = await api("/api/templates/install", {
      method: "POST",
      body: {
        ...actor,
        template_id: templateId,
        install_options: installOptions,
      },
    })
    renderLog("market_template_install", response)
    updateSummary(response.data.ok ? apiData(response) : {
      status: "error",
      message: response.data.message || "request_failed",
    })
    if (response.data.ok) {
      await loadMarketInstallations({ refresh: true })
    }
    setMarketInstallationActionBusy(button, false)
  }

  async function uninstallMarketInstallation(item, button) {
    const templateId = String(item && item.template_id || "").trim()
    if (!templateId) return
    const actor = marketActor()
    setMarketInstallationActionBusy(button, true)
    const response = await api("/api/member/installations/uninstall", {
      method: "POST",
      body: {
        user_id: actor.user_id,
        template_id: templateId,
      },
    })
    renderLog("member_installations_uninstall", response)
    updateSummary(response.data.ok ? apiData(response) : {
      status: "error",
      message: response.data.message || "request_failed",
    })
    if (response.data.ok) {
      await loadMarketInstallations({ refresh: true })
    }
    setMarketInstallationActionBusy(button, false)
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
      const row = document.createElement("article")
      row.className = "member-install-item"
      row.tabIndex = 0
      row.setAttribute("role", "button")
      const title = document.createElement("strong")
      title.textContent = String(item.template_id || "-")
      const body = document.createElement("div")
      body.className = "member-install-item-body"
      body.appendChild(title)
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
      body.appendChild(meta)
      row.appendChild(body)

      const actions = document.createElement("div")
      actions.className = "member-install-actions"

      const reinstallButton = document.createElement("button")
      reinstallButton.type = "button"
      reinstallButton.className = "btn-ghost member-install-action"
      reinstallButton.textContent = i18nMessage("member.installations.reinstall", "Reinstall")
      reinstallButton.disabled = false
      reinstallButton.setAttribute("data-member-install-action", "reinstall")
      reinstallButton.addEventListener("click", (event) => {
        event.stopPropagation()
        void reinstallMarketInstallation(item, reinstallButton)
      })
      actions.appendChild(reinstallButton)

      const uninstallButton = document.createElement("button")
      uninstallButton.type = "button"
      uninstallButton.className = "btn-ghost member-install-action"
      uninstallButton.textContent = i18nMessage("member.installations.uninstall", "Uninstall")
      uninstallButton.disabled = false
      uninstallButton.setAttribute("data-member-install-action", "uninstall")
      uninstallButton.addEventListener("click", (event) => {
        event.stopPropagation()
        void uninstallMarketInstallation(item, uninstallButton)
      })
      actions.appendChild(uninstallButton)

      row.appendChild(actions)
      row.addEventListener("click", () => {
        focusMarketInstallation(item)
      })
      row.addEventListener("keydown", (event) => {
        if (event.key !== "Enter" && event.key !== " ") return
        event.preventDefault()
        focusMarketInstallation(item)
      })
      root.appendChild(row)
    })
  }

  async function loadMarketInstallations(options = {}) {
    state.memberInstallationsRequested = true
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

  function catalogFilters() {
    return {
      pack_id: String(byId("marketPackFilter")?.value || ""),
      pack_type: String(byId("marketPackTypeFilter")?.value || ""),
      risk_level: String(byId("marketRiskFilter")?.value || ""),
      featured: String(byId("marketFeaturedFilter")?.value || ""),
      review_label: String(byId("marketReviewLabelFilter")?.value || ""),
      warning_flag: String(byId("marketWarningFlagFilter")?.value || ""),
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
    const sections = normalizeList(byId("marketCompareSections")?.value || "")
    return {
      pack_id: String(byId("marketPackId")?.value || ""),
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
    const text = String(value || "").trim()
    if (!text) return 0
    const time = Date.parse(text)
    return Number.isFinite(time) ? time : 0
  }

  function listLength(value) {
    return Array.isArray(value) ? value.length : 0
  }

  function packRiskScore(risk) {
    const text = String(risk || "").trim().toLowerCase()
    if (text === "low") return 20
    if (text === "medium") return 12
    if (text === "high") return 4
    return 8
  }

  function packCompatibilityScore(item) {
    const text = String((item && item.compatibility) || "").trim().toLowerCase()
    if (text === "compatible" || text === "ok") return 14
    if (text === "degraded") return 8
    if (text === "blocked") return 0
    return 6
  }

  function catalogRankScore(item) {
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
    const cards = [
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
    const sorted = sortedByTrend(rows)
    const featuredRows = sorted.filter((item) => Boolean(item && item.featured))
    const candidate = (featuredOverride && typeof featuredOverride === "object")
      ? featuredOverride
      : (featuredRows[0] || sorted[0] || null)
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
    const ranked = Array.isArray(trendingOverride) && trendingOverride.length
      ? trendingOverride.slice(0, 6)
      : sortedByTrend(rows).slice(0, 6)
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
    renderEntryFeaturedPreview(rows, normalized ? normalized.metrics : null, normalized ? normalized.featured : null)
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
    renderEntryFeaturedPreview([], null, null)
  }

  function renderEntryFeaturedPreview(rows, metricOverride = null, featuredOverride = null) {
    const totalValue = byId("marketEntryStatTotalValue")
    const featuredValue = byId("marketEntryStatFeaturedValue")
    const titleNode = byId("marketEntryFeaturedTitle")
    const summaryNode = byId("marketEntryFeaturedSummary")
    const metaNode = byId("marketEntryFeaturedMeta")
    const pillRoot = byId("marketEntryFeaturedPills")
    const jumpButton = byId("btnMarketJumpToFeaturedDetail")
    const metric = metricOverride && typeof metricOverride === "object"
      ? metricOverride
      : catalogMetrics(rows)
    if (totalValue) totalValue.textContent = String(toSafeInt(metric.total))
    if (featuredValue) featuredValue.textContent = String(toSafeInt(metric.featured))

    const selected = selectedCatalogRow()
    const resolvedPackId = selected
      ? String(selected.pack_id || "").trim()
      : resolveDefaultCatalogSelection(rows)
    const candidate = selected
      || (featuredOverride && typeof featuredOverride === "object" ? featuredOverride : null)
      || findCatalogItemByPackId(resolvedPackId, rows)

    if (!titleNode || !summaryNode || !metaNode || !pillRoot || !jumpButton) return

    pillRoot.innerHTML = ""
    if (!candidate) {
      titleNode.textContent = i18nMessage(
        "market.entry.default_detail_loading_title",
        "Loading default detail baseline...",
      )
      summaryNode.textContent = i18nMessage(
        "market.entry.default_detail_loading_summary",
        "Catalog insights will pin a default detail candidate here.",
      )
      metaNode.textContent = ""
      jumpButton.disabled = true
      jumpButton.setAttribute("aria-disabled", "true")
      jumpButton.dataset.packId = ""
      return
    }

    const candidatePackId = String(candidate.pack_id || "").trim()
    titleNode.textContent = resolveCatalogPackTitle(candidate) || candidatePackId || "-"
    summaryNode.textContent = cardDescription(candidate)
      || localizedPackFeaturedNote(candidatePackId, "")
      || i18nMessage("market.card.description_fallback", "No description provided.")
    metaNode.textContent = [
      resolveCatalogPackSubtitle(candidate),
      i18nFormat("market.featured.risk_and_compat", "risk={risk} · compatibility={compatibility}", {
        risk: enumLabel("risk", String(candidate.risk_level || "unknown")),
        compatibility: enumLabel("compatibility", String(candidate.compatibility || "unknown")),
      }),
    ].filter(Boolean).join(" · ")

    if (candidate.featured) {
      appendPill(
        pillRoot,
        i18nMessage("market.badge.featured", "featured"),
        "success",
      )
    }
    normalizeStringArray(candidate.review_labels).slice(0, 2).forEach((label) => {
      appendPill(pillRoot, enumLabel("review_label", label), pillTone(label))
    })
    normalizeStringArray(candidate.warning_flags).slice(0, 2).forEach((flag) => {
      appendPill(pillRoot, enumLabel("warning_flag", flag), pillTone(flag))
    })
    if (!pillRoot.childNodes.length) {
      appendPill(
        pillRoot,
        enumLabel("compatibility", String(candidate.compatibility || "unknown")),
        "neutral",
      )
    }

    jumpButton.disabled = !candidatePackId
    jumpButton.setAttribute("aria-disabled", candidatePackId ? "false" : "true")
    jumpButton.dataset.packId = candidatePackId
  }

  function scrollMarketDetailIntoView() {
    const area = byId("marketDetailArea")
    if (area && typeof area.scrollIntoView === "function") {
      area.scrollIntoView({ behavior: "smooth", block: "start" })
    }
  }

  function selectCatalogItem(item) {
    const packId = String((item && item.pack_id) || "").trim()
    if (!packId) return
    if (!isDetailPage()) {
      state.selectedPackId = packId
      navigateToDetail(packId)
      return
    }
    state.selectedPackId = packId
    setMarketDetailExpanded(true)
    resetCompareView()
    renderSelectedDetailShell(item)
    updateSummary(item)
    updateCatalogTable(state.catalog)
    updateCatalogDetailActions()
    syncQueryState()
  }

  function resolvedUpdatedAt(item) {
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
      const contractHelper = marketCatalogContractHelpers()
      const likeCount = catalogLikeCount(item)
      const liked = isPackLiked(item && item.pack_id)
      const contractModel = contractHelper && typeof contractHelper.buildPublicCatalogCard === "function"
        ? contractHelper.buildPublicCatalogCard(item, { likeCount, liked })
        : null
      const model = contractModel || profilePackCardModel(item)
      const displayedLikeCount = Number.isFinite(Number(model.likeCount))
        ? Math.max(0, Math.trunc(Number(model.likeCount)))
        : likeCount
      const displayedLiked = Object.prototype.hasOwnProperty.call(model, "liked")
        ? Boolean(model.liked)
        : liked
      const card = document.createElement("article")
      card.className = "template-card"
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
      subtitle.textContent = resolveCatalogPackSubtitle(item) || model.subtitle || i18nMessage("market.card.subtitle_fallback", "profile pack")
      card.appendChild(subtitle)

      const packIdLine = document.createElement("p")
      packIdLine.className = "template-card-pack-id"
      packIdLine.textContent = String((item && item.pack_id) || "").trim() || "-"
      card.appendChild(packIdLine)

      const desc = document.createElement("p")
      desc.className = "template-card-description"
      desc.textContent = model.summary || cardDescription(item) || i18nMessage("market.card.description_fallback", "No description provided.")
      card.appendChild(desc)

      if (Array.isArray(model.badges) && model.badges.length) {
        const badgeRow = document.createElement("div")
        badgeRow.className = "pill-row"
        model.badges.forEach((badge) => {
          appendPill(badgeRow, enumLabel("review_label", badge), pillTone(badge))
        })
        card.appendChild(badgeRow)
      }

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
      const metaEntries = [
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
      useBtn.textContent = model.primaryAction && model.primaryAction.label
        ? model.primaryAction.label
        : i18nMessage("market.card.open", "Open")
      useBtn.addEventListener("click", (event) => {
        event.stopPropagation()
        selectCatalogItem(item)
      })
      actions.appendChild(useBtn)

      const likeButton = document.createElement("button")
      likeButton.type = "button"
      likeButton.className = "btn-ghost market-card-like-button"
      likeButton.setAttribute("data-market-like-button", "true")
      likeButton.setAttribute("aria-pressed", displayedLiked ? "true" : "false")
      likeButton.addEventListener("click", (event) => {
        event.stopPropagation()
        toggleCatalogLike(item)
      })
      const likeLabel = document.createElement("span")
      likeLabel.textContent = i18nMessage("market.card.like", "Like")
      likeButton.appendChild(likeLabel)
      const likeCountNode = document.createElement("span")
      likeCountNode.className = "market-card-like-count"
      likeCountNode.setAttribute("data-market-like-count", "true")
      likeCountNode.textContent = String(displayedLikeCount)
      likeButton.appendChild(likeCountNode)
      actions.appendChild(likeButton)

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
    const bytesLabel = i18nMessage("market.compare.bytes", "bytes")
    const beforeSize = Number(row.before_size || 0)
    const afterSize = Number(row.after_size || 0)
    const delta = Number(row.delta_size || 0)
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
      meta.textContent = i18nMessage(
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
    const table = byId("marketCatalogTable")
    const tbody = table ? table.querySelector("tbody") : null
    if (tbody) {
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
    }
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
    if (isDetailPage()) {
      const requestedPackId = String(state.selectedPackId || "").trim()
      const nextSelectedPackId = requestedPackId || resolveDefaultCatalogSelection(state.catalogRaw)
      state.selectedPackId = nextSelectedPackId
      const selected = nextSelectedPackId
        ? findCatalogItemByPackId(nextSelectedPackId, state.catalogRaw)
        : null
      if (selected) {
        setMarketDetailExpanded(true)
        resetCompareView()
        renderSelectedDetailShell(selected)
        updateSummary(selected)
        updateCatalogTable(state.catalog)
      } else if (requestedPackId) {
        setMarketDetailExpanded(true)
        updateSummary({
          status: "error",
          pack_id: requestedPackId,
          message: i18nMessage(
            "market.error.pack_not_found",
            "The requested pack is not available in the current catalog.",
          ),
        })
      } else {
        setMarketDetailExpanded(false)
      }
    } else {
      state.selectedPackId = ""
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
    updateSummary(
      isDetailPage()
        ? (
          findCatalogItemByPackId(state.selectedPackId, state.catalogRaw)
          || { status: "listed", count: state.catalog.length }
        )
        : { status: "listed", count: state.catalog.length },
    )
    return response
  }

  async function loadCatalogDetail() {
    if (!isDetailPage()) {
      const packId = String(byId("marketPackId")?.value || state.selectedPackId || "").trim()
      if (packId) {
        navigateToDetail(packId)
      }
      return
    }
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
    const packId = String(byId("marketPackId")?.value || "").trim()
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
      renderSelectedDetailShell(selected)
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
    renderSelectedDetailShell(selectedCatalogRow())
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
    renderSelectedDetailShell(selectedCatalogRow())
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
      void listCatalog()
    }
  }

  function bindEvents() {
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
    const openLoginButton = byId("btnMarketOpenLoginPanel")
    if (openLoginButton) {
      openLoginButton.addEventListener("click", () => {
        state.authPromptRequested = true
        updateAuthUi()
        const passwordNode = byId("marketAuthPassword")
        if (passwordNode && typeof passwordNode.focus === "function") {
          passwordNode.focus()
        }
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
    const detailButton = byId("btnMarketCatalogDetail")
    if (detailButton) {
      detailButton.addEventListener("click", () => {
        void loadCatalogDetail()
      })
    }
    const searchNode = byId("marketGlobalSearch")
    if (searchNode) {
      searchNode.addEventListener("input", () => {
        state.localSearch = String(searchNode.value || "").trim()
        applyLocalCatalogView()
      })
    }
    quickFilterButtons().forEach((button) => {
      button.addEventListener("click", () => {
        const key = String(button.getAttribute("data-market-quick-filter") || "").trim() || "all"
        applyQuickFilter(key)
      })
    })
    const sortNode = byId("marketSortBy")
    if (sortNode) {
      sortNode.addEventListener("change", () => {
        state.localSort = String(sortNode.value || LOCAL_SORT_OPTIONS.TRENDING)
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
    const pickNode = (...ids) => {
      for (const id of ids) {
        const node = byId(id)
        if (node) return node
      }
      return null
    }

    const refreshInstallationsBtn = pickNode(
      "btnMarketDetailRefreshInstallations",
      "btnMarketRefreshInstallations"
    )
    if (refreshInstallationsBtn) {
      refreshInstallationsBtn.addEventListener("click", () => {
        if (!ensureMemberActionCapability("member.installations.refresh", i18nMessage("button.refresh_local_installations", "Refresh Local Installations"))) return
        void loadMarketInstallations({ refresh: true })
      })
    }
    const templateTrialBtn = pickNode("btnMarketDetailTrial", "btnMarketTemplateTrial")
    if (templateTrialBtn) {
      templateTrialBtn.addEventListener("click", () => {
        if (!ensureMemberActionCapability("templates.trial.request", i18nMessage("button.request_trial", "Request Trial"))) return
        void runMarketTemplateTrial()
      })
    }
    const templateInstallBtn = pickNode("btnMarketDetailInstall", "btnMarketTemplateInstall")
    if (templateInstallBtn) {
      templateInstallBtn.addEventListener("click", () => {
        if (!ensureMemberActionCapability("templates.install", i18nMessage("button.install_template", "Install Template"))) return
        void runMarketTemplateInstall()
      })
    }
    const templateSubmitBtn = pickNode("btnMarketDetailSubmitTemplate", "btnMarketTemplateSubmit")
    if (templateSubmitBtn) {
      templateSubmitBtn.addEventListener("click", () => {
        if (!ensureMemberActionCapability("templates.submit", i18nMessage("button.submit_template", "Submit Template"))) return
        void runMarketTemplateSubmit()
      })
    }
    const profilePackSubmitBtn = pickNode(
      "btnMarketDetailSubmitProfilePack",
      "btnMarketProfilePackSubmit"
    )
    if (profilePackSubmitBtn) {
      profilePackSubmitBtn.addEventListener("click", () => {
        if (!ensureMemberActionCapability("profile_pack.community.submit", i18nMessage("profile_pack.market.submit_btn", "Submit To Community"))) return
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
    const entryPreviewButton = byId("btnMarketJumpToFeaturedDetail")
    if (entryPreviewButton) {
      entryPreviewButton.addEventListener("click", () => {
        const packId = String(entryPreviewButton.dataset.packId || state.selectedPackId || "").trim()
        const item = packId ? findCatalogItemByPackId(packId) : null
        if (item && packId !== state.selectedPackId) {
          selectCatalogItem(item)
        } else if (packId && isDetailPage()) {
          setMarketDetailExpanded(true)
          updateCatalogDetailActions()
        }
        if (isDetailPage()) {
          scrollMarketDetailIntoView()
        }
      })
    }
    document.addEventListener("click", (event) => {
      const target = event.target instanceof Element ? event.target : null
      const actionButton = target
        ? target.closest(
          [
            "#btnMarketCatalogCompare",
            "#btnMarketCatalogDownload",
            "#btnMarketDetailTrial",
            "#btnMarketDetailInstall",
            "#btnMarketTemplateTrial",
            "#btnMarketTemplateInstall",
            "#btnMarketDetailSubmitTemplate",
            "#btnMarketTemplateSubmit",
            "#btnMarketDetailSubmitProfilePack",
            "#btnMarketProfilePackSubmit",
          ].join(", ")
        )
        : null
      if (!actionButton) return
      if (actionButton.id === "btnMarketCatalogCompare") {
        void compareCatalogPack()
        return
      }
      if (actionButton.id === "btnMarketCatalogDownload") {
        triggerCatalogDownload()
        return
      }
      if (actionButton.id === "btnMarketDetailTrial" || actionButton.id === "btnMarketTemplateTrial") {
        if (!ensureMemberActionCapability("templates.trial.request", i18nMessage("button.request_trial", "Request Trial"))) return
        void runMarketTemplateTrial()
        return
      }
      if (actionButton.id === "btnMarketDetailInstall" || actionButton.id === "btnMarketTemplateInstall") {
        if (!ensureMemberActionCapability("templates.install", i18nMessage("button.install_template", "Install Template"))) return
        void runMarketTemplateInstall()
        return
      }
      if (actionButton.id === "btnMarketDetailSubmitTemplate" || actionButton.id === "btnMarketTemplateSubmit") {
        if (!ensureMemberActionCapability("templates.submit", i18nMessage("button.submit_template", "Submit Template"))) return
        void runMarketTemplateSubmit()
        return
      }
      if (actionButton.id === "btnMarketDetailSubmitProfilePack" || actionButton.id === "btnMarketProfilePackSubmit") {
        if (!ensureMemberActionCapability("profile_pack.community.submit", i18nMessage("profile_pack.market.submit_btn", "Submit To Community"))) return
        void runMarketProfilePackSubmit()
      }
    })
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && state.filterDrawerOpen) {
        setFilterDrawerOpen(false)
      }
    })
  }

  async function init() {
    state.likedPackIds = readStoredMarketLikes()
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
    updateQuickFilterButtons([])
    updateCatalogCountChips([], [])
    setMarketLogExpanded(false)
    setMarketDetailExpanded(Boolean(state.selectedPackId))
    resetCompareView()
    resetCatalogInsights()
    updateCatalogDetailActions()
    await refreshHealth()
    await initAuth()
    if (hasCapability("profile_pack.catalog.read")) {
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
