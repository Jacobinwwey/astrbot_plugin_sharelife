const state = {
  token: "",
  authRequired: false,
  allowAnonymousMember: false,
  authPromptRequested: false,
  authRole: "",
  availableRoles: [],
  uiLocale: "en-US",
  developerMode: false,
  pageMode: "auto",
  activeScope: "member",
  templates: [],
  submissions: [],
  selectedTemplateId: "",
  selectedSubmissionId: "",
  templateDetail: {},
  submissionDetail: {},
  submissionCompare: null,
  scanPanel: {
    scanSummary: null,
    reviewLabels: [],
    warningFlags: [],
  },
  pendingCompareEvidenceFocus: null,
  trialStatus: null,
  applyPlanResult: null,
  profilePack: {
    lastOperation: null,
    exportArtifactId: "",
    importId: "",
    planId: "",
    pendingCompatibilityAction: "",
    sections: [],
    dryrun: null,
    records: {
      exports: [],
      imports: [],
    },
    recordPackFilter: "",
    market: {
      submissions: [],
      catalog: [],
      lastOperation: null,
    },
  },
  pendingWorkspaceScrollTarget: "",
  collectionStatus: {
    templates: { status: "idle", count: 0, errorMessage: "" },
    submissions: { status: "idle", count: 0, errorMessage: "" },
    profilePackSubmissions: { status: "idle", count: 0, errorMessage: "" },
    profilePackCatalog: { status: "idle", count: 0, errorMessage: "" },
  },
  panelStatus: {
    templateDetail: { status: "idle", id: "", errorMessage: "" },
    submissionDetail: { status: "idle", id: "", errorMessage: "" },
    compare: { status: "idle", id: "", errorMessage: "" },
  },
  capabilities: {
    role: "member",
    authenticated: false,
    anonymousMember: false,
    operations: [],
    availableRoles: ["member", "reviewer", "admin"],
  },
  runtimeFeatures: {
    supportsLocalAstrbotImport: true,
    allowAnonymousLocalAstrbotImport: false,
  },
  marketHub: {
    selectedTemplateId: "",
    wizardStep: 1,
    templateDrawerOpen: false,
  },
  memberPanel: {
    installations: [],
    importDrafts: [],
    tasks: [],
    searchQuery: "",
    selectedImportDraftId: "",
    uploadSelectionTree: [],
    uploadSelectedNodePath: "",
  },
  reviewerLifecycle: {
    invites: [],
    accounts: [],
    devices: [],
    sessions: [],
    maxDevices: 0,
    selectedReviewerId: "",
  },
}

const UI_LOCALE_STORAGE_KEY = "sharelife.uiLocale"
const DEVELOPER_MODE_STORAGE_KEY = "sharelife.developerMode"
const ADMIN_AUTH_SESSION_STORAGE_KEY = "sharelife.adminAuthSession"
const APP_PAGE_INSTANCE_ID = `sharelife-app-${Math.random().toString(36).slice(2)}`

const CONTROL_CAPABILITY_MAP = Object.freeze({
  loginBtn: "auth.login",
  btnPrefGet: "preferences.read",
  btnModeSet: "preferences.write",
  btnObserveSet: "preferences.write",
  btnTemplates: "templates.list",
  btnOpenSubmitWizard: "templates.submit",
  btnSubmitWizardPublish: "templates.submit",
  btnSubmitTemplate: "templates.submit",
  btnTrial: "templates.trial.request",
  btnTrialStatus: "templates.trial.status",
  btnInstall: "templates.install",
  btnImportAstrbotConfig: "member.profile_pack.imports.local_astrbot",
  btnImportConfigPackFile: "member.profile_pack.imports.package_upload",
  btnOpenMemberImportReview: "member.profile_pack.imports.read",
  btnMemberProfilePackUploadDelete: "member.profile_pack.imports.delete",
  btnRefreshMemberInstallationsInline: "member.installations.refresh",
  btnPrompt: "templates.prompt.generate",
  btnPackage: "templates.package.generate",
  btnPackageDownload: "templates.package.download",
  btnTemplateDetail: "templates.detail",
  btnDrawerTrial: "templates.trial.request",
  btnDrawerInstall: "templates.install",
  btnDrawerPrompt: "templates.prompt.generate",
  btnDrawerPackage: "templates.package.generate",
  btnDrawerDetail: "templates.detail",
  btnDryrunPlan: "admin.apply.workflow",
  btnApplyPlan: "admin.apply.workflow",
  btnRollbackPlan: "admin.apply.workflow",
  btnListSubmissions: "member.submissions.read",
  btnSubmissionDetail: "member.submissions.detail.read",
  btnCompareSubmission: "admin.submissions.compare",
  btnSaveSubmissionReview: "admin.submissions.review",
  btnApproveSubmission: "admin.submissions.decide",
  btnRejectSubmission: "admin.submissions.decide",
  btnDownloadSubmissionPackage: "member.submissions.package.download",
  btnListRetry: "admin.retry.manage",
  btnLockRetry: "admin.retry.manage",
  btnRetryDecide: "admin.retry.manage",
  btnAudit: "admin.audit.read",
  btnReviewerInviteCreate: "admin.reviewer.lifecycle.manage",
  btnReviewerInviteList: "admin.reviewer.lifecycle.manage",
  btnReviewerAccountList: "admin.reviewer.lifecycle.manage",
  btnReviewerDeviceList: "admin.reviewer.lifecycle.manage",
  btnReviewerDeviceReset: "admin.reviewer.lifecycle.manage",
  btnReviewerSessionList: "admin.reviewer.lifecycle.manage",
  btnReviewerSessionRevoke: "admin.reviewer.lifecycle.manage",
  btnNotice: "notifications.read",
  btnStorageSummary: "admin.storage.local_summary.read",
  btnStoragePoliciesGet: "admin.storage.policies.read",
  btnStoragePoliciesSet: "admin.storage.policies.write",
  btnStorageRunBackup: "admin.storage.jobs.run",
  btnStorageJobsList: "admin.storage.jobs.read",
  btnStorageJobGet: "admin.storage.jobs.read",
  btnStorageRestorePrepare: "admin.storage.restore.prepare",
  btnStorageRestoreCommit: "admin.storage.restore.commit",
  btnStorageRestoreCancel: "admin.storage.restore.cancel",
  btnStorageRestoreJobsList: "admin.storage.restore.read",
  btnStorageRestoreJobGet: "admin.storage.restore.read",
  btnContinuityList: "admin.apply.workflow",
  btnContinuityGet: "admin.apply.workflow",
  btnProfilePackExport: "admin.profile_pack.manage",
  btnProfilePackDownloadExport: "member.profile_pack.submissions.export.download",
  btnProfilePackListExports: "admin.profile_pack.manage",
  btnProfilePackImport: "admin.profile_pack.manage",
  btnProfilePackImportFromExport: "admin.profile_pack.manage",
  btnProfilePackImportDryrun: "admin.profile_pack.manage",
  btnProfilePackListImports: "admin.profile_pack.manage",
  btnProfilePackDryrun: "admin.profile_pack.manage",
  btnProfilePackApply: "admin.profile_pack.manage",
  btnProfilePackRollback: "admin.profile_pack.manage",
  btnProfilePackPluginPlan: "admin.profile_pack.manage",
  btnProfilePackPluginConfirm: "admin.profile_pack.manage",
  btnProfilePackPluginExecute: "admin.profile_pack.manage",
  btnProfilePackSubmitCommunity: "profile_pack.community.submit",
  btnProfilePackListPackSubmissions: "member.profile_pack.submissions.read",
  btnProfilePackDecideSubmission: "admin.profile_pack.market.review",
  btnProfilePackListCatalog: "profile_pack.catalog.read",
  btnProfilePackCatalogDetail: "profile_pack.catalog.read",
  btnProfilePackCatalogCompare: "profile_pack.catalog.read",
  btnProfilePackSetFeatured: "admin.profile_pack.featured.write",
  btnMemberProfilePackUploadSubmit: "profile_pack.community.submit",
})

const ANONYMOUS_MEMBER_FALLBACK_OPERATIONS = Object.freeze([
  "auth.info.read",
  "auth.login",
  "health.read",
  "member.installations.read",
  "member.installations.refresh",
  "member.installations.uninstall",
  "member.tasks.read",
  "member.tasks.refresh",
  "notifications.read",
  "preferences.read",
  "preferences.write",
  "profile_pack.catalog.read",
  "templates.detail",
  "templates.install",
  "templates.list",
  "templates.package.download",
  "templates.trial.request",
  "templates.trial.status",
  "ui.capabilities.read",
])

const FOCUSABLE_SELECTOR = [
  "button:not([disabled])",
  "[href]",
  "input:not([disabled])",
  "select:not([disabled])",
  "textarea:not([disabled])",
  "[tabindex]:not([tabindex='-1'])",
].join(",")

const dialogFocusState = {
  templateDrawer: {
    keydownHandler: null,
    restoreFocusTarget: null,
    resolveFallbackFocus: null,
  },
  submitWizard: {
    keydownHandler: null,
    restoreFocusTarget: null,
    resolveFallbackFocus: null,
  },
  memberProfilePackUpload: {
    keydownHandler: null,
    restoreFocusTarget: null,
    resolveFallbackFocus: null,
  },
}

let openDialogScopes = []

let storageSyncBound = false
let uiEventBusBound = false
const uiEventBusUnsubscribe = []

function byId(id) {
  return document.getElementById(id)
}

function actor() {
  const fixedRole = fixedRoleByPageMode()
  const roleNode = byId("role")
  const normalizedRole = fixedRole
    ? fixedRole
    : String(roleNode && roleNode.value ? roleNode.value : "member").trim()
  return {
    user_id: String(byId("userId").value || "webui-user").trim() || "webui-user",
    session_id: String(byId("sessionId").value || "webui-session").trim() || "webui-session",
    role: normalizedRole || "member",
    admin_id: String(byId("adminId").value || "webui-admin").trim() || "webui-admin"
  }
}

function reviewLabelsArray() {
  const raw = String(byId("reviewLabels").value || "")
  return raw
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean)
}

function compareHelpers() {
  return globalThis.SharelifeCompare || null
}

function detailHelpers() {
  return globalThis.SharelifeDetail || null
}

function tableInteractionHelpers() {
  return globalThis.SharelifeTableInteractions || null
}

function workspaceHelpers() {
  return globalThis.SharelifeWorkspace || null
}

function feedbackHelpers() {
  return globalThis.SharelifeWorkspaceFeedback || null
}

function collectionFeedbackHelpers() {
  return globalThis.SharelifeCollectionFeedback || null
}

function collectionStateHelpers() {
  return globalThis.SharelifeCollectionState || null
}

function payloadHelpers() {
  return globalThis.SharelifeWorkspacePayload || null
}

function profilePackHelpers() {
  return globalThis.SharelifeProfilePackPanel || null
}

function profilePackRecordHelpers() {
  return globalThis.SharelifeProfilePackRecords || null
}

function profilePackMarketHelpers() {
  return globalThis.SharelifeProfilePackMarket || null
}

function profilePackCompareViewHelpers() {
  return globalThis.SharelifeProfilePackCompareView || null
}

function profilePackGuidanceHelpers() {
  return globalThis.SharelifeProfilePackGuidance || null
}

function i18nHelpers() {
  return globalThis.SharelifeWebuiI18n || null
}

function consoleScopeHelpers() {
  return globalThis.SharelifeConsoleScope || null
}

function marketCardHelpers() {
  return globalThis.SharelifeMarketCards || null
}

function uiEventBusHelpers() {
  return globalThis.SharelifeUiEventBus || null
}

function authSurfaceHelpers() {
  return globalThis.SharelifeMarketAuthSurface || null
}

function dialogScrollLockHelpers() {
  return globalThis.SharelifeDialogScrollLock || null
}

function readStoredUiLocale() {
  if (!globalThis.localStorage) return ""
  try {
    return String(globalThis.localStorage.getItem(UI_LOCALE_STORAGE_KEY) || "")
  } catch (_error) {
    return ""
  }
}

function readStoredDeveloperMode() {
  if (!globalThis.localStorage) return false
  try {
    const raw = globalThis.localStorage.getItem(DEVELOPER_MODE_STORAGE_KEY)
    return parseDeveloperModeValue(raw)
  } catch (_error) {
    return false
  }
}

function parseDeveloperModeValue(value) {
  const raw = String(value || "").trim().toLowerCase()
  return raw === "1" || raw === "true" || raw === "on"
}

function saveDeveloperMode(enabled) {
  if (!globalThis.localStorage) return
  try {
    globalThis.localStorage.setItem(DEVELOPER_MODE_STORAGE_KEY, enabled ? "1" : "0")
  } catch (_error) {
    // noop: localStorage can be unavailable in strict privacy modes
  }
}

function saveUiLocale(locale) {
  if (!globalThis.localStorage) return
  try {
    globalThis.localStorage.setItem(UI_LOCALE_STORAGE_KEY, locale)
  } catch (_error) {
    // noop: localStorage can be unavailable in strict privacy modes
  }
}

function readSessionJson(key) {
  if (!globalThis.sessionStorage) return null
  try {
    const raw = String(globalThis.sessionStorage.getItem(key) || "").trim()
    if (!raw) return null
    const payload = JSON.parse(raw)
    return payload && typeof payload === "object" ? payload : null
  } catch (_error) {
    return null
  }
}

function clearAdminAuthSession() {
  if (!globalThis.sessionStorage) return
  try {
    globalThis.sessionStorage.removeItem(ADMIN_AUTH_SESSION_STORAGE_KEY)
  } catch (_error) {
    // noop
  }
}

function persistAdminAuthSession() {
  if (!globalThis.sessionStorage) return
  const isAdminSession = state.authRequired && state.authRole === "admin" && state.token && state.token !== "no-auth"
  const allowBridgePersistence = state.pageMode === "admin" || isReviewerAdminBridgeActive()
  if (!allowBridgePersistence || !isAdminSession) {
    clearAdminAuthSession()
    return
  }
  try {
    globalThis.sessionStorage.setItem(
      ADMIN_AUTH_SESSION_STORAGE_KEY,
      JSON.stringify({
        token: state.token,
        role: "admin",
        sourcePage: "admin",
        savedAt: Date.now(),
        availableRoles: Array.isArray(state.availableRoles) ? state.availableRoles : [],
      }),
    )
  } catch (_error) {
    // noop
  }
}

function restoreAdminAuthSession() {
  if (!state.authRequired) {
    clearAdminAuthSession()
    return false
  }
  if (state.pageMode !== "admin" && state.pageMode !== "reviewer") {
    return false
  }
  const payload = readSessionJson(ADMIN_AUTH_SESSION_STORAGE_KEY)
  if (!payload) return false
  const token = String(payload.token || "").trim()
  const role = String(payload.role || "").trim().toLowerCase()
  const sourcePage = String(payload.sourcePage || "").trim().toLowerCase()
  if (!token || role !== "admin") {
    clearAdminAuthSession()
    return false
  }
  if (state.pageMode === "reviewer" && sourcePage !== "admin") {
    return false
  }
  state.token = token
  state.authRole = "admin"
  const availableRoles = Array.isArray(payload.availableRoles)
    ? payload.availableRoles.map((item) => String(item || "").trim()).filter(Boolean)
    : []
  if (availableRoles.length) {
    state.availableRoles = availableRoles
  }
  return true
}

function isReviewerAdminBridgeActive() {
  return (
    state.pageMode === "reviewer" &&
    state.authRequired &&
    String(state.authRole || "").trim().toLowerCase() === "admin" &&
    Boolean(state.token) &&
    state.token !== "no-auth"
  )
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
  if (!globalThis.navigator) return ""
  const languages = Array.isArray(globalThis.navigator.languages)
    ? globalThis.navigator.languages
    : []
  if (languages.length > 0) {
    return String(languages[0] || "")
  }
  return String(globalThis.navigator.language || "")
}

function i18nMessage(key, fallback = "") {
  const helper = i18nHelpers()
  if (helper && helper.getMessage) {
    return helper.getMessage(state.uiLocale, key, fallback)
  }
  return fallback
}

function localeQuickButtons() {
  return Array.from(document.querySelectorAll("[data-locale-option]"))
}

function updateLocaleQuickButtons() {
  localeQuickButtons().forEach((node) => {
    const locale = String(node.getAttribute("data-locale-option") || "").trim()
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

function localizedProfilePackIssueLabels(values) {
  const guidance = profilePackGuidanceHelpers()
  const options = {
    t: (key, fallback = "") => i18nMessage(key, fallback),
    f: (key, fallback = "", tokens = {}) => i18nFormat(key, fallback, tokens),
  }
  if (guidance && guidance.formatIssueLabels) {
    return guidance.formatIssueLabels(values, options)
  }
  const rows = Array.isArray(values) ? values : []
  return rows
    .map((item) => String(item || "").trim())
    .filter(Boolean)
    .filter((item, index, all) => all.indexOf(item) === index)
}

function isRawAstrBotImportItem(item) {
  const issues = Array.isArray(item && item.compatibility_issues) ? item.compatibility_issues : []
  return issues.some((entry) => String(entry || "").trim().toLowerCase() === "astrbot_raw_import_converted")
}

function memberImportIssueSummary(values, limit = 2) {
  const labels = localizedProfilePackIssueLabels(values)
  if (!labels.length) return ""
  const preview = labels.slice(0, Math.max(1, Number(limit) || 1)).join(" · ")
  if (labels.length <= limit) return preview
  return `${preview} +${labels.length - limit}`
}

function memberImportSourceLabel(item) {
  if (isRawAstrBotImportItem(item)) {
    return i18nMessage(
      "member.upload_detail.import_source_astrbot_raw",
      "Raw AstrBot export (converted)",
    )
  }
  return i18nMessage(
    "member.upload_detail.import_source_standard",
    "Sharelife standard import",
  )
}

function memberImportSummaryText(item) {
  const summary = item && typeof item.import_summary === "object" && item.import_summary
    ? item.import_summary
    : {}
  const parts = []
  const defaultPersonality = String(summary.default_personality || "").trim()
  const personaCount = Number(summary.persona_count || 0)
  const subagentCount = Number(summary.subagent_count || 0)
  const platformCount = Number(summary.platform_count || 0)
  if (defaultPersonality) {
    parts.push(
      i18nFormat(
        "member.imports.summary_default_personality",
        "Persona: {value}",
        { value: defaultPersonality },
      ),
    )
  }
  if (personaCount > 0) {
    parts.push(
      i18nFormat(
        "member.imports.summary_persona_count",
        "Personas: {count}",
        { count: personaCount },
      ),
    )
  }
  if (subagentCount > 0) {
    parts.push(
      i18nFormat(
        "member.imports.summary_subagent_count",
        "Subagents: {count}",
        { count: subagentCount },
      ),
    )
  }
  if (platformCount > 0) {
    parts.push(
      i18nFormat(
        "member.imports.summary_platform_count",
        "Platforms: {count}",
        { count: platformCount },
      ),
    )
  }
  return parts.join(" · ")
}

function humanizeCodeValue(value) {
  const text = String(value || "").trim()
  if (!text) return "-"
  return text.replace(/[_-]+/g, " ").trim()
}

function normalizeEnumGroup(group) {
  const text = String(group || "").trim().toLowerCase()
  if (!text) return "status"
  if (text === "risk_level") return "risk"
  return text
}

function enumLabelValue(group, value) {
  const code = String(value || "").trim()
  if (!code) return "-"
  const normalizedGroup = normalizeEnumGroup(group)
  const key = `enum.${normalizedGroup}.${code.toLowerCase()}`
  return i18nMessage(key, humanizeCodeValue(code))
}

function localizedCodeList(group, values) {
  const rows = Array.isArray(values) ? values.filter(Boolean) : []
  if (!rows.length) return "-"
  return rows.map((item) => enumLabelValue(group, item)).join(", ")
}

function applyUiLocale(locale, options = {}) {
  const normalized = normalizeUiLocale(locale)
  state.uiLocale = normalized
  const localeField = byId("uiLocale")
  if (localeField && localeField.value !== normalized) {
    localeField.value = normalized
  }

  const helper = i18nHelpers()
  if (helper && helper.applyLocale) {
    helper.applyLocale(document, normalized)
  }
  updateLocaleQuickButtons()
  updateDeveloperModeUi()
  renderRiskGlossary()
  if (options.persist !== false) {
    saveUiLocale(normalized)
  }
  if (options.emit !== false) {
    emitUiEvent("UI_LOCALE_CHANGED", "ui.locale.changed", {
      locale: normalized,
      source: options.source || "app",
      sourceId: options.sourceId || APP_PAGE_INSTANCE_ID,
    })
  }
  if (options.refreshCollections !== false) {
    renderCollectionState("templates")
    renderCollectionState("submissions")
    renderCollectionState("profilePackSubmissions")
    renderCollectionState("profilePackCatalog")
    renderPanelState("templateDetail")
    renderPanelState("submissionDetail")
    renderPanelState("compare")
    updateTrialStatusPanel(state.trialStatus)
    updateApplyWorkflowPanel(state.applyPlanResult)
    updateProfilePackPanel(state.profilePack.lastOperation)
    renderProfilePackSections(state.profilePack.sections)
    renderProfilePackRecords()
    renderModerationWorkspace()
    updateWorkspaceContext(activeWorkspaceRoute())
    updateProfilePackMarketPanel(state.profilePack.market.lastOperation)
    updateTemplatesTable(state.templates)
    updateProfilePackCatalogTable(state.profilePack.market.catalog)
    renderMemberInstallations(state.memberPanel.installations)
    renderMemberImportDrafts(state.memberPanel.importDrafts)
    renderMemberTaskQueue()
    syncMemberProfilePackUploadModal()
    updateReviewerInviteTable(state.reviewerLifecycle.invites)
    updateReviewerAccountTable(state.reviewerLifecycle.accounts)
    updateReviewerDeviceTable(state.reviewerLifecycle.devices)
    renderReviewerLifecycleAuthState()
    applyConsoleScope()
    setWizardStep(state.marketHub.wizardStep || 1)
    rerenderScanPanelFromState()
  }
  return normalized
}

function initializeUiLocale() {
  const helper = i18nHelpers()
  const stored = readStoredUiLocale()
  const fallback = browserUiLocale() || "en-US"
  const defaultLocale = helper && helper.DEFAULT_LOCALE ? helper.DEFAULT_LOCALE : "en-US"
  const initial = normalizeUiLocale(stored || fallback || defaultLocale)
  applyUiLocale(initial, { persist: false, refreshCollections: false })
}

function updateDeveloperModeUi() {
  const isMemberPage = state.pageMode === "member"
  const isReviewerReadonlyPage = state.pageMode === "reviewer" && !isReviewerAdminBridgeActive()
  const hideDeveloperMode = isMemberPage || isReviewerReadonlyPage
  const button = byId("btnToggleDeveloperMode")
  if (button) {
    button.textContent = state.developerMode
      ? i18nMessage("button.developer_mode_on", "Developer Mode: ON")
      : i18nMessage("button.developer_mode_off", "Developer Mode: OFF")
    button.classList.toggle("hidden", hideDeveloperMode)
  }
  const line = byId("developerModeLine")
  if (line) {
    line.textContent = state.developerMode
      ? i18nMessage("developer_mode.status.on", "Developer mode: on")
      : i18nMessage("developer_mode.status.off", "Developer mode: off")
    line.classList.toggle("hidden", hideDeveloperMode)
  }
  if (document && document.body && document.body.classList) {
    document.body.classList.toggle("developer-mode", state.developerMode)
  }
}

function setDeveloperMode(enabled, options = {}) {
  const allowDeveloperMode = state.pageMode !== "member" && (
    state.pageMode !== "reviewer" || isReviewerAdminBridgeActive()
  )
  state.developerMode = allowDeveloperMode ? Boolean(enabled) : false
  updateDeveloperModeUi()
  if (options.persist !== false || !allowDeveloperMode) {
    saveDeveloperMode(state.developerMode)
  }
  if (options.emit !== false) {
    emitUiEvent("DEVELOPER_MODE_CHANGED", "ui.developer_mode.changed", {
      enabled: state.developerMode,
      source: options.source || "app",
      sourceId: options.sourceId || APP_PAGE_INSTANCE_ID,
    })
  }
  rerenderScanPanelFromState()
  updateProfilePackPanel(state.profilePack.lastOperation)
  if (state.developerMode && state.profilePack.pendingCompatibilityAction) {
    const pending = String(state.profilePack.pendingCompatibilityAction || "").trim()
    if (pending) {
      state.profilePack.pendingCompatibilityAction = ""
      applyProfilePackActionShortcut(pending)
    }
  }
}

function initializeDeveloperMode() {
  const stored = readStoredDeveloperMode()
  setDeveloperMode(stored, { persist: false })
}

function pageModeFromLocation() {
  const helper = consoleScopeHelpers()
  const pathname = globalThis.location && globalThis.location.pathname ? globalThis.location.pathname : ""
  if (helper && helper.pageModeFromPath) {
    return helper.pageModeFromPath(pathname)
  }
  const text = String(pathname || "").trim().toLowerCase()
  if (text === "/member.html") return "member"
  if (text === "/reviewer.html") return "reviewer"
  if (text === "/admin.html") return "admin"
  if (text === "/user" || text === "/user/") return "member"
  if (text === "/member" || text === "/member/") return "member"
  if (text === "/reviewer" || text === "/reviewer/") return "reviewer"
  if (text === "/admin" || text === "/admin/") return "admin"
  return "auto"
}

function resolveActiveConsoleScope() {
  const helper = consoleScopeHelpers()
  const manualRole = byId("role") ? byId("role").value : "member"
  if (helper && helper.resolveConsoleScope) {
    return helper.resolveConsoleScope({
      pageMode: state.pageMode,
      authRequired: state.authRequired,
      authRole: state.authRole,
      manualRole,
    })
  }
  if (state.pageMode === "admin" || state.pageMode === "reviewer" || state.pageMode === "member") {
    return state.pageMode
  }
  if (state.authRequired) {
    if (state.authRole === "admin") return "admin"
    if (state.authRole === "reviewer") return "reviewer"
    return "member"
  }
  if (String(manualRole || "member") === "admin") return "admin"
  if (String(manualRole || "member") === "reviewer") return "reviewer"
  return "member"
}

function scopeVisible(targetScope, activeScope) {
  const helper = consoleScopeHelpers()
  if (helper && helper.scopeVisible) {
    return helper.scopeVisible(targetScope, activeScope)
  }
  const scope = String(targetScope || "shared")
  if (scope === "all" || scope === "shared") return true
  return scope === activeScope
}

function setConsoleSwitchHint(scope) {
  const hintNode = byId("consoleScopeHint")
  if (!hintNode) return
  let hintKey = "console.switch.hint.member"
  let fallback = "Member console focuses on trial/market operations."
  if (scope === "reviewer") {
    if (isReviewerAdminBridgeActive()) {
      hintKey = "console.switch.hint.reviewer"
      fallback = "Reviewer console focuses on moderation queue and risk labeling."
    } else {
      hintKey = "console.switch.hint.reviewer_readonly"
      fallback = "Reviewer console is read-only until an admin session is handed off from /admin."
    }
  } else if (scope === "admin") {
    hintKey = "console.switch.hint.admin"
    fallback = "Admin console focuses on review/apply/governance operations."
  }
  hintNode.setAttribute("data-i18n-key", hintKey)
  hintNode.textContent = i18nMessage(hintKey, fallback)
}

function setConsoleLinkActive(scope) {
  const links = [
    { node: byId("memberConsoleLink"), scope: "member" },
    { node: byId("reviewerConsoleLink"), scope: "reviewer" },
    { node: byId("adminConsoleLink"), scope: "admin" },
  ]
  links.forEach((item) => {
    if (!item.node) return
    item.node.classList.toggle("is-active", item.scope === scope)
  })
}

function setConsoleLinkVisibility() {
  const memberLink = byId("memberConsoleLink")
  const reviewerLink = byId("reviewerConsoleLink")
  const adminLink = byId("adminConsoleLink")
  const marketLink = byId("marketConsoleLink")
  const fullLink = byId("fullConsoleLink")
  const hide = (node, value) => {
    if (!node) return
    node.classList.toggle("hidden", Boolean(value))
  }

  // Member page is intentionally simplified: only member + market entry points.
  if (state.pageMode === "member") {
    hide(memberLink, false)
    hide(marketLink, false)
    hide(reviewerLink, true)
    hide(adminLink, true)
    hide(fullLink, true)
    return
  }
  if (state.pageMode === "reviewer") {
    hide(memberLink, false)
    hide(marketLink, false)
    hide(reviewerLink, true)
    hide(adminLink, false)
    hide(fullLink, false)
    return
  }
  if (state.pageMode === "admin") {
    hide(memberLink, false)
    hide(marketLink, false)
    hide(reviewerLink, false)
    hide(adminLink, true)
    hide(fullLink, false)
    return
  }
  hide(memberLink, false)
  hide(marketLink, false)
  hide(reviewerLink, false)
  hide(adminLink, false)
  hide(fullLink, false)
}

function applyConsoleScope() {
  const scope = resolveActiveConsoleScope()
  state.activeScope = scope
  const scopeLine = byId("consoleScopeLine")
  if (scopeLine) {
    scopeLine.textContent = i18nFormat("console.scope.line", "view: {scope}", { scope })
  }

  const scopedNodes = document.querySelectorAll("[data-console-scope]")
  scopedNodes.forEach((node) => {
    const targetScope = String(node.getAttribute("data-console-scope") || "shared")
    const visible = scopeVisible(targetScope, scope)
    const manualVisibility = String(node.getAttribute("data-scope-visibility") || "").trim() === "manual"
    if (!visible) {
      node.classList.add("hidden")
      return
    }
    if (!manualVisibility) {
      node.classList.remove("hidden")
    }
  })

  setConsoleSwitchHint(scope)
  setConsoleLinkActive(scope)
  setConsoleLinkVisibility()
  applyCapabilityGuards()
}

function workspacePayload(payload) {
  const helper = payloadHelpers()
  if (helper && helper.extractWorkspacePayload) {
    return helper.extractWorkspacePayload(payload)
  }
  if (payload && payload.data && payload.data.data) {
    return payload.data.data
  }
  if (payload && payload.data) {
    return payload.data
  }
  return payload || {}
}

function badgeTone(value) {
  const text = String(value || "").toLowerCase()
  if (!text) return "neutral"
  if (
    text.includes("prompt_injection") ||
    text.includes("reveal_system_prompt") ||
    text.includes("ignore_previous") ||
    text.includes("risk_high")
  ) {
    return "danger"
  }
  if (
    text.includes("risk_medium") ||
    text.includes("compatibility") ||
    text.includes("provider_override") ||
    text.includes("agent_orchestration") ||
    text.includes("allow_with_notice")
  ) {
    return "warning"
  }
  return "neutral"
}

function appendPill(container, text, tone = "neutral") {
  const badge = document.createElement("span")
  badge.className = `pill is-${tone}`
  badge.textContent = text
  container.appendChild(badge)
}

function appendInteractivePill(container, scope, category, value, tone = "neutral", displayText = null) {
  const badge = document.createElement("button")
  badge.type = "button"
  badge.className = `pill pill-button is-${tone}`
  badge.textContent = String(displayText || value || "")
  badge.addEventListener("click", (event) => {
    event.stopPropagation()
    void applyBadgeFilter(scope, category, value)
  })
  container.appendChild(badge)
}

function headers() {
  const out = { "Content-Type": "application/json" }
  if (state.token && state.token !== "no-auth") {
    out.Authorization = `Bearer ${state.token}`
  }
  return out
}

function render(name, payload) {
  const resultNode = byId("result")
  const timestamp = new Date().toISOString()
  const block = `[${timestamp}] ${name}\n${JSON.stringify(payload, null, 2)}\n\n`
  resultNode.textContent = block + resultNode.textContent
  updateScanPanelFromPayload(payload)
  updateComparePanel(payload)
  updateDetailPanelsFromPayload(payload)
  const taskNames = new Set([
    "list_templates",
    "submit_template",
    "submit_template_wizard",
    "trial",
    "trial_status",
    "install",
    "prompt",
    "package",
    "package_download",
    "member_installations",
    "member_installations_refresh",
    "member_installations_uninstall",
    "member_profile_pack_import",
    "member_profile_pack_submit",
    "profile_pack_submit",
  ])
  if (taskNames.has(String(name || ""))) {
    pushMemberTask(name, payload)
  }
}

function queryString(params) {
  const q = new URLSearchParams()
  Object.entries(params).forEach(([k, v]) => {
    if (v === undefined || v === null || v === "") return
    q.set(k, String(v))
  })
  const out = q.toString()
  return out ? `?${out}` : ""
}

function apiData(response) {
  if (response && response.data && response.data.data !== undefined) {
    return response.data.data
  }
  return {}
}

function responseErrorCode(response) {
  return String(response && response.data && response.data.error && response.data.error.code || "").trim()
}

function fixedRoleByPageMode() {
  if (state.pageMode === "member" || state.pageMode === "admin") {
    return state.pageMode
  }
  if (state.pageMode === "reviewer") {
    return isReviewerAdminBridgeActive() ? "admin" : "member"
  }
  return ""
}

function fallbackCapabilityRole() {
  if (state.pageMode === "reviewer" && !isReviewerAdminBridgeActive()) {
    return "public"
  }
  const fixedRole = fixedRoleByPageMode()
  if (fixedRole) return fixedRole
  const roleField = byId("role")
  if (roleField && roleField.value) {
    return String(roleField.value || "").trim().toLowerCase() || "member"
  }
  return "member"
}

function fallbackCapabilityOperations(role, options = {}) {
  const normalizedRole = String(role || "").trim().toLowerCase()
  const authenticated = options.authenticated !== false
  const allowAnonymousMember = options.allowAnonymousMember === true
  const base = [
    "auth.info.read",
    "auth.login",
    "health.read",
    "ui.capabilities.read",
  ]
  const member = [
    "member.installations.read",
    "member.installations.refresh",
    "member.installations.uninstall",
    "member.profile_pack.imports.delete",
    "member.profile_pack.imports.local_astrbot",
    "member.profile_pack.imports.package_upload",
    "member.profile_pack.imports.read",
    "member.profile_pack.imports.write",
    "member.tasks.read",
    "member.tasks.refresh",
    "member.submissions.read",
    "member.submissions.detail.read",
    "member.submissions.package.download",
    "member.profile_pack.submissions.read",
    "member.profile_pack.submissions.detail.read",
    "member.profile_pack.submissions.withdraw",
    "member.profile_pack.submissions.export.download",
    "notifications.read",
    "preferences.read",
    "preferences.write",
    "profile_pack.catalog.read",
    "profile_pack.community.submit",
    "templates.detail",
    "templates.install",
    "templates.list",
    "templates.package.download",
    "templates.package.generate",
    "templates.prompt.generate",
    "templates.submit",
    "templates.trial.request",
    "templates.trial.status",
  ]
  const admin = [
    "admin.apply.workflow",
    "admin.audit.read",
    "admin.reviewer.lifecycle.manage",
    "admin.storage.jobs.read",
    "admin.storage.jobs.run",
    "admin.storage.local_summary.read",
    "admin.storage.policies.read",
    "admin.storage.policies.write",
    "admin.storage.restore.cancel",
    "admin.storage.restore.commit",
    "admin.storage.restore.prepare",
    "admin.storage.restore.read",
    "admin.pipeline.run",
    "admin.profile_pack.featured.write",
    "admin.profile_pack.manage",
    "admin.profile_pack.market.review",
    "admin.retry.manage",
    "admin.submissions.compare",
    "admin.submissions.decide",
    "admin.submissions.package.download",
    "admin.submissions.read",
    "admin.submissions.review",
  ]
  const reviewer = [
    "admin.profile_pack.market.review",
    "admin.submissions.compare",
    "admin.submissions.decide",
    "admin.submissions.package.download",
    "admin.submissions.read",
    "admin.submissions.review",
  ]
  if (normalizedRole === "admin") {
    return Array.from(new Set([...base, ...member, ...reviewer, ...admin]))
  }
  if (normalizedRole === "reviewer") {
    return Array.from(new Set([...base, ...member, ...reviewer]))
  }
  if (normalizedRole === "member") {
    if (!authenticated && allowAnonymousMember) {
      return ANONYMOUS_MEMBER_FALLBACK_OPERATIONS.slice()
    }
    return Array.from(new Set([...base, ...member]))
  }
  return base.slice()
}

function setCapabilities(payload, options = {}) {
  const data = payload && typeof payload === "object" ? payload : {}
  const role = String(data.role || fallbackCapabilityRole()).trim().toLowerCase()
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
  const availableRoles = Array.isArray(data.available_roles)
    ? data.available_roles.map((item) => String(item || "").trim()).filter(Boolean)
    : ["member", "reviewer", "admin"]
  state.runtimeFeatures.supportsLocalAstrbotImport = data.supports_local_astrbot_import !== false
  state.runtimeFeatures.allowAnonymousLocalAstrbotImport = Boolean(
    data.allow_anonymous_local_astrbot_import,
  )
  state.capabilities = {
    role: role || fallbackCapabilityRole(),
    authenticated,
    anonymousMember,
    operations: Array.from(new Set(operations)),
    availableRoles: availableRoles.length ? availableRoles : ["member", "reviewer", "admin"],
  }
  applyCapabilityGuards()
  syncMemberLocalImportEntrySurface()
  renderModerationWorkspace()
  if (options.updateScope !== false) {
    applyConsoleScope()
  }
}

function hasCapability(capability) {
  const required = String(capability || "").trim()
  if (!required) return true
  if (state.pageMode === "reviewer" && !isReviewerAdminBridgeActive()) {
    return false
  }
  const operations = Array.isArray(state.capabilities.operations)
    ? state.capabilities.operations
    : []
  return operations.includes(required)
}

function requiredCapabilityForControl(controlId) {
  return CONTROL_CAPABILITY_MAP[controlId] || ""
}

function isControlCapabilityAllowed(controlId) {
  const required = requiredCapabilityForControl(controlId)
  return hasCapability(required)
}

function capabilityLockedHint(capability) {
  return i18nFormat(
    "capability.locked_hint",
    "Requires capability: {capability}",
    { capability: String(capability || "") },
  )
}

function applyCapabilityGuardToControl(controlId) {
  const requiredCapability = requiredCapabilityForControl(controlId)
  if (!requiredCapability) return
  const node = byId(controlId)
  if (!node) return

  const allowed = hasCapability(requiredCapability)
  node.classList.toggle("capability-blocked", !allowed)
  node.setAttribute("aria-disabled", allowed ? "false" : "true")

  if (!allowed) {
    node.setAttribute("data-capability-locked", "1")
    if ("disabled" in node) {
      node.disabled = true
    }
    node.title = capabilityLockedHint(requiredCapability)
    return
  }

  if (node.getAttribute("data-capability-locked") === "1") {
    if ("disabled" in node) {
      node.disabled = false
    }
    node.removeAttribute("data-capability-locked")
  }
  node.removeAttribute("title")
}

function applyCapabilityGuards() {
  Object.keys(CONTROL_CAPABILITY_MAP).forEach((controlId) => {
    applyCapabilityGuardToControl(controlId)
  })
}

async function refreshCapabilities(options = {}) {
  const query = {}
  if (!state.authRequired) {
    query.role = fallbackCapabilityRole()
  }
  if (state.pageMode && state.pageMode !== "auto") {
    query.page_mode = state.pageMode
  }
  const response = await api(`/api/ui/capabilities${queryString(query)}`)
  if (!response || response.status >= 400 || !(response.data && response.data.ok)) {
    if (response && response.status === 401 && state.authRequired && state.token && state.token !== "no-auth") {
      state.token = ""
      state.authRole = ""
      clearAdminAuthSession()
      updateAuthUi()
    }
    const fallbackAnonymousMember = (
      state.authRequired &&
      state.allowAnonymousMember &&
      !state.token &&
      state.pageMode !== "reviewer" &&
      state.pageMode !== "admin"
    )
    const fallbackRole = fallbackAnonymousMember
      ? "member"
      : (state.authRequired && (!state.token || state.token === "no-auth")
        ? "public"
        : fallbackCapabilityRole())
    setCapabilities(
      {
        role: fallbackRole,
        authenticated: !fallbackAnonymousMember && (!state.authRequired || (Boolean(state.token) && state.token !== "no-auth")),
        anonymous_member: fallbackAnonymousMember,
        operations: fallbackCapabilityOperations(fallbackRole, {
          authenticated: !fallbackAnonymousMember && (!state.authRequired || (Boolean(state.token) && state.token !== "no-auth")),
          allowAnonymousMember: state.allowAnonymousMember,
        }),
        available_roles: ["member", "reviewer", "admin"],
      },
      { updateScope: options.updateScope !== false },
    )
    return response
  }
  setCapabilities(response.data, { updateScope: options.updateScope !== false })
  return response
}

function defaultPlanId(templateId) {
  const normalized = String(templateId || "")
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
  return `plan-${normalized || "template"}`
}

async function api(path, options = {}) {
  const method = options.method || "GET"
  const body = options.body
  const init = { method, headers: headers() }
  if (body !== undefined) {
    init.body = JSON.stringify(body)
  }
  const res = await fetch(path, init)
  const data = await res.json().catch(() => ({ ok: false, message: "invalid_json" }))
  return { status: res.status, data }
}

function applyAuthOptions(roles) {
  const authRole = byId("authRole")
  if (!authRole) return
  const fixedRole = fixedRoleByPageMode()
  const inputRoles = Array.isArray(roles) ? roles : []
  const effectiveRoles = fixedRole
    ? [fixedRole]
    : (inputRoles.length ? inputRoles : ["member", "reviewer", "admin"])
  authRole.innerHTML = ""
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
    authRole.appendChild(option)
  })
  if (state.authRole && effectiveRoles.includes(state.authRole)) {
    authRole.value = state.authRole
  } else if (fixedRole) {
    authRole.value = fixedRole
  }
  authRole.disabled = Boolean(fixedRole)
}

function syncRoleFields() {
  const roleField = byId("role")
  if (!roleField) return
  const fixedRole = fixedRoleByPageMode()
  if (fixedRole) {
    roleField.disabled = true
    roleField.value = fixedRole
    return
  }
  if (state.authRequired) {
    roleField.disabled = true
    roleField.value = state.authRole || "member"
  } else {
    roleField.disabled = false
  }
}

function syncReviewerAuthFields() {
  const authRoleNode = byId("authRole")
  const reviewerFields = byId("reviewerAuthFields")
  if (!authRoleNode || !reviewerFields) return
  const role = String(authRoleNode.value || "").trim().toLowerCase()
  const visible = role === "reviewer"
  reviewerFields.classList.toggle("hidden", !visible)
}

function updateAuthUi() {
  const helper = authSurfaceHelpers()
  const optionalAnonymousMember = (
    state.allowAnonymousMember
    && state.pageMode !== "reviewer"
    && state.pageMode !== "admin"
  )
  const surface = helper && typeof helper.describeMarketAuthSurface === "function"
    ? helper.describeMarketAuthSurface({
      authRequired: state.authRequired,
      allowAnonymousMember: optionalAnonymousMember,
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
  const reviewerReadonly = state.pageMode === "reviewer" && !isReviewerAdminBridgeActive()
  const authPanel = byId("authPanel")
  const authHelp = byId("authHelp")
  const authGuidance = byId("authGuidance")
  const openLoginButton = byId("btnAuthOpenLoginPanel")
  const readonlyNotice = byId("reviewerReadonlyNotice")
  const adminLinkedNotice = byId("reviewerAdminLinkedNotice")
  byId("authLine").textContent = i18nFormat(
    "auth.line",
    "auth: {status}",
    {
      status: surface.mode === "optional"
        ? i18nFormat("auth.status.optional", "optional ({roles})", { roles: rolesText })
        : (state.authRequired
          ? i18nFormat("auth.status.required", "required ({roles})", { roles: rolesText })
          : i18nMessage("auth.status.disabled", "disabled")),
    },
  )
  byId("authRoleLine").textContent = i18nFormat("auth.role.line", "role: {role}", {
    role: state.authRole || i18nMessage("auth.role.not_logged_in", "not logged in"),
  })
  if (authPanel) {
    const shouldShowAuthPanel = state.pageMode !== "reviewer" && surface.showAuthPanel
    if (state.pageMode === "reviewer") {
      authPanel.classList.add("hidden")
    } else {
      authPanel.classList.toggle("hidden", !shouldShowAuthPanel)
    }
    authPanel.toggleAttribute("hidden", !shouldShowAuthPanel)
    authPanel.setAttribute("aria-hidden", shouldShowAuthPanel ? "false" : "true")
  }
  if (authHelp) {
    if (state.pageMode === "reviewer") {
      authHelp.textContent = i18nMessage(
        "auth.help.reviewer_locked",
        "Reviewer direct login is disabled on this route. Login on /admin and open /reviewer from there.",
      )
    } else if (surface.mode === "optional") {
      authHelp.textContent = i18nMessage(
        "auth.help.optional",
        "Anonymous browsing and installation stay available. Login is only required for uploads, submission management, or other protected actions.",
      )
    } else {
      authHelp.textContent = state.authRequired
        ? i18nMessage(
            "auth.help.required",
            "This deployment requires credentials before protected actions can run. Use the operator-provided onboarding flow if you do not have an account yet.",
          )
        : i18nMessage(
            "auth.help.disabled",
            "If auth is disabled in plugin config, this panel stays hidden.",
          )
    }
  }
  if (authGuidance) {
    const shouldShowGuidance = surface.mode === "optional" && !surface.showAuthPanel
    authGuidance.textContent = i18nMessage(
      "auth.guidance.optional",
      "Continue anonymously for browsing and installation. Open login only when you need upload, submission management, or a higher-privilege role.",
    )
    authGuidance.classList.toggle("hidden", !shouldShowGuidance)
    authGuidance.toggleAttribute("hidden", !shouldShowGuidance)
  }
  if (openLoginButton) {
    const shouldShowOpenButton = surface.mode === "optional" && !surface.showAuthPanel
    openLoginButton.classList.toggle("hidden", !shouldShowOpenButton)
    openLoginButton.toggleAttribute("hidden", !shouldShowOpenButton)
  }
  if (readonlyNotice) {
    readonlyNotice.classList.toggle("hidden", !reviewerReadonly)
  }
  if (adminLinkedNotice) {
    adminLinkedNotice.classList.toggle("hidden", !isReviewerAdminBridgeActive())
  }
  syncRoleFields()
  syncReviewerAuthFields()
  renderReviewerLifecycleAuthState()
  updateDeveloperModeUi()
  applyConsoleScope()
}

function setScanPanelSource(scanSummary, reviewLabels = [], warningFlags = []) {
  state.scanPanel = {
    scanSummary: scanSummary && typeof scanSummary === "object" ? scanSummary : null,
    reviewLabels: Array.isArray(reviewLabels) ? reviewLabels : [],
    warningFlags: Array.isArray(warningFlags) ? warningFlags : [],
  }
}

function clearScanPanelSource() {
  setScanPanelSource(null, [], [])
}

function rerenderScanPanelFromState() {
  const source = state.scanPanel || {}
  updateScanPanel(source.scanSummary, source.reviewLabels || [], source.warningFlags || [])
}

function normalizeRiskEvidenceItem(item) {
  if (!item || typeof item !== "object") {
    return null
  }
  return {
    category: String(item.category || "unknown"),
    rule: String(item.rule || "unknown"),
    severity: String(item.severity || "unknown"),
    file: String(item.file || "-"),
    path: String(item.path || "$"),
    line: Number(item.line || 0),
    column: Number(item.column || 0),
    phrase: String(item.phrase || "").trim(),
  }
}

function clearScanEvidenceList() {
  const hintNode = byId("scanEvidenceHint")
  const listNode = byId("scanEvidenceList")
  if (hintNode) hintNode.classList.add("hidden")
  if (listNode) {
    listNode.innerHTML = ""
    listNode.classList.add("hidden")
  }
}

function renderScanEvidenceList(evidenceItems) {
  const hintNode = byId("scanEvidenceHint")
  const listNode = byId("scanEvidenceList")
  if (!hintNode || !listNode) return
  if (!state.developerMode || !Array.isArray(evidenceItems) || evidenceItems.length === 0) {
    hintNode.classList.add("hidden")
    listNode.innerHTML = ""
    listNode.classList.add("hidden")
    return
  }

  hintNode.classList.remove("hidden")
  listNode.classList.remove("hidden")
  listNode.innerHTML = ""

  evidenceItems.slice(0, 80).forEach((entry, index) => {
    const item = normalizeRiskEvidenceItem(entry)
    if (!item) return
    const button = document.createElement("button")
    button.type = "button"
    button.className = "scan-evidence-item"
    const position = `${item.file}:${item.line > 0 ? item.line : "-"}:${item.column > 0 ? item.column : "-"}`
    button.textContent = `${index + 1}. ${item.rule} | ${position} | ${item.path}`
    button.addEventListener("click", () => {
      void jumpToCompareWithEvidence(item)
    })
    listNode.appendChild(button)
  })
}

function applyCompareEvidenceFocus() {
  const focus = state.pendingCompareEvidenceFocus
  if (!focus) return
  const item = normalizeRiskEvidenceItem(focus)
  state.pendingCompareEvidenceFocus = null
  if (!item) return

  const highlightsNode = byId("compareHighlights")
  if (highlightsNode) {
    appendPill(
      highlightsNode,
      i18nFormat(
        "compare.evidence_focus",
        "evidence {rule} @ {file}:{line}:{column}",
        {
          rule: item.rule,
          file: item.file,
          line: item.line > 0 ? item.line : "-",
          column: item.column > 0 ? item.column : "-",
        },
      ),
      badgeTone(item.severity || item.rule),
    )
  }

  const compareRawNode = byId("compareDetails")
    ? byId("compareDetails").closest(".compare-raw")
    : null
  if (compareRawNode) {
    compareRawNode.open = true
  }
  const compareDetailsNode = byId("compareDetails")
  if (compareDetailsNode && compareDetailsNode.classList) {
    compareDetailsNode.classList.add("is-focus-target")
    setTimeout(() => {
      compareDetailsNode.classList.remove("is-focus-target")
    }, 1600)
  }
  const target = byId("compareSections") || byId("submissionWorkspaceSection")
  if (target && target.scrollIntoView) {
    target.scrollIntoView({ behavior: "smooth", block: "start" })
  }
}

async function jumpToCompareWithEvidence(item) {
  const normalized = normalizeRiskEvidenceItem(item)
  if (!normalized) return
  if (!hasCapability("admin.submissions.compare")) {
    byId("scanSummary").textContent = i18nMessage(
      "scan.evidence.compare_unavailable",
      "Compare evidence is available in reviewer/admin scope only.",
    )
    return
  }
  const submissionField = byId("decisionSubmissionId")
  const candidateSubmissionId =
    String(state.selectedSubmissionId || "").trim() ||
    String((submissionField && submissionField.value) || "").trim()
  if (!candidateSubmissionId) {
    byId("scanSummary").textContent = i18nMessage(
      "scan.evidence.jump_missing_submission",
      "No submission selected. Select a submission row first to open compare view.",
    )
    return
  }

  applyFieldPatches({ decisionSubmissionId: candidateSubmissionId })
  await loadSubmissionCompare({ submissionId: candidateSubmissionId, syncRoute: false })
  state.pendingCompareEvidenceFocus = normalized
  applyCompareEvidenceFocus()
}


function updateScanPanel(scanSummary, reviewLabels = [], warningFlags = []) {
  if (!scanSummary || Object.keys(scanSummary).length === 0) {
    byId("scanSummary").textContent = i18nMessage("scan.summary_idle", "No package scan loaded yet.")
    byId("scanLabels").innerHTML = ""
    clearScanEvidenceList()
    byId("scanDetails").textContent = state.developerMode
      ? i18nMessage("scan.evidence.empty", "No localized risk evidence found.")
      : i18nMessage(
          "scan.details.developer_hint",
          "Detailed file/path localization is hidden. Toggle Developer Mode to inspect evidence.",
        )
    return
  }

  const labels = Array.from(new Set([...(reviewLabels || []), ...(scanSummary.review_labels || [])]))
  const flags = Array.from(new Set([...(warningFlags || []), ...(scanSummary.warning_flags || [])]))
  const injection = scanSummary.prompt_injection || {}
  const evidence = Array.isArray(scanSummary.risk_evidence) ? scanSummary.risk_evidence : []

  byId("scanSummary").textContent =
    `risk=${scanSummary.risk_level || "unknown"} | compatibility=${scanSummary.compatibility || "unknown"} | levels=${(scanSummary.levels || []).join(", ") || "n/a"}`

  const labelsNode = byId("scanLabels")
  labelsNode.innerHTML = ""
  labels.forEach((label) => {
    appendPill(labelsNode, label, badgeTone(label))
  })
  flags.forEach((flag) => {
    appendPill(labelsNode, flag, badgeTone(flag))
  })
  renderScanEvidenceList(evidence)

  const detailsNode = byId("scanDetails")
  if (!state.developerMode) {
    detailsNode.textContent = i18nFormat(
      "scan.details.developer_hint_count",
      "Detailed file/path localization is hidden. Toggle Developer Mode to inspect {count} evidence item(s).",
      { count: evidence.length },
    )
    return
  }

  const lines = []
  if (!evidence.length) {
    lines.push(i18nMessage("scan.evidence.empty", "No localized risk evidence found."))
  } else {
    lines.push(
      i18nFormat(
        "scan.evidence.header",
        "Localized risk evidence ({count})",
        { count: evidence.length },
      ),
    )
    lines.push("")
    evidence.slice(0, 80).forEach((item, index) => {
      const category = String(item.category || "unknown")
      const rule = String(item.rule || "unknown")
      const severity = String(item.severity || "unknown")
      const file = String(item.file || "-")
      const path = String(item.path || "$")
      const line = Number(item.line || 0)
      const column = Number(item.column || 0)
      const phrase = String(item.phrase || "").trim() || "-"
      const location = `${i18nMessage("scan.evidence.file", "file")}=${file} | ${i18nMessage("scan.evidence.path", "path")}=${path} | ${i18nMessage("scan.evidence.line", "line")}=${line > 0 ? line : "-"} | ${i18nMessage("scan.evidence.column", "column")}=${column > 0 ? column : "-"}`
      lines.push(
        `${index + 1}. ${i18nMessage("scan.evidence.category", "category")}=${category} | ${i18nMessage("scan.evidence.rule", "rule")}=${rule} | ${i18nMessage("scan.evidence.severity", "severity")}=${severity}`,
      )
      lines.push(`   ${location}`)
      lines.push(`   ${i18nMessage("scan.evidence.phrase", "phrase")}=${phrase}`)
      lines.push(`   ${i18nMessage("scan.evidence.jump", "click item above to open compare view")}`)
      lines.push("")
    })
  }

  lines.push(i18nMessage("scan.evidence.raw_block", "Raw scan payload (developer mode)"))
  lines.push(
    JSON.stringify(
      {
        prompt_injection: {
          detected: Boolean(injection.detected),
          severity: injection.severity || "none",
          matched_rules: injection.matched_rules || [],
          matched_phrases: injection.matched_phrases || [],
        },
        warning_flags: flags,
        risk_evidence: evidence,
      },
      null,
      2,
    ),
  )
  detailsNode.textContent = lines.join("\n")
}

function extractScanSource(payload) {
  const data = workspacePayload(payload)
  if (data.scan_summary) {
    return {
      scanSummary: data.scan_summary,
      reviewLabels: data.review_labels || [],
      warningFlags: data.warning_flags || []
    }
  }
  const collections = [
    data.submissions,
    data.templates
  ]
  for (const items of collections) {
    if (!Array.isArray(items) || items.length === 0) continue
    const first = items[0]
    if (first && first.scan_summary) {
      return {
        scanSummary: first.scan_summary,
        reviewLabels: first.review_labels || [],
        warningFlags: first.warning_flags || []
      }
    }
  }
  return null
}

function updateScanPanelFromPayload(payload) {
  const source = extractScanSource(payload)
  if (!source) return
  setScanPanelSource(source.scanSummary, source.reviewLabels, source.warningFlags)
  updateScanPanel(source.scanSummary, source.reviewLabels, source.warningFlags)
}

function updateComparePanel(payload) {
  const data = workspacePayload(payload)
  if (!data.comparison || !data.details) {
    return
  }
  state.submissionCompare = data
  const submissionId = data.submission && (data.submission.submission_id || data.submission.id)
  if (submissionId) {
    setPanelStatus("compare", { status: "ready", id: submissionId, errorMessage: "" })
  }
  const helper = compareHelpers()
  const view = helper && helper.buildCompareViewModel
    ? helper.buildCompareViewModel(data)
    : null
  if (!view) {
    byId("compareSummary").textContent = `status=${data.comparison.status || "unknown"}`
    byId("compareDetails").textContent = JSON.stringify(data.details, null, 2)
    applyCompareEvidenceFocus()
    renderModerationWorkspace()
    return
  }

  byId("compareSummary").textContent =
    `status=${view.summary.status} | version_changed=${Boolean(view.summary.versionChanged)} | risk_changed=${Boolean(view.summary.riskChanged)} | package=${Boolean(view.summary.hasSubmissionPackage)}/${Boolean(view.summary.hasPublishedPackage)}`

  const highlightsNode = byId("compareHighlights")
  highlightsNode.innerHTML = ""
  view.highlights.forEach((item) => {
    appendPill(highlightsNode, item.label, item.tone || "neutral")
  })

  const sectionsNode = byId("compareSections")
  sectionsNode.innerHTML = ""
  view.sections.forEach((section) => {
    sectionsNode.appendChild(renderCompareSection(section))
  })

  byId("compareDetails").textContent = JSON.stringify(data.details, null, 2)
  applyCompareEvidenceFocus()
  renderModerationWorkspace()
}

function resetComparePanel(options = {}) {
  state.submissionCompare = null
  state.pendingCompareEvidenceFocus = null
  if (!options.preserveStatus) {
    resetPanelStatus("compare")
  }
  byId("compareSummary").textContent = i18nMessage("compare.summary_idle", "No comparison loaded yet.")
  byId("compareHighlights").innerHTML = ""
  byId("compareSections").innerHTML = ""
  byId("compareDetails").textContent = ""
  renderModerationWorkspace()
}

function updateDetailPanelsFromPayload(payload) {
  const data = workspacePayload(payload)
  if (data.template_id && data.published_at) {
    updateTemplateDetailPanel(data)
  }
  if (data.submission_id && data.created_at) {
    updateSubmissionDetailPanel(data)
  }
}

function renderDetailPanel(summaryId, badgesId, rowsId, view) {
  const summaryNode = byId(summaryId)
  if (view.empty) {
    if (summaryId === "templateDetailSummary") {
      summaryNode.textContent = i18nMessage(
        "detail.template.summary_idle",
        view.message || "No template detail loaded yet.",
      )
    } else if (summaryId === "submissionDetailSummary") {
      summaryNode.textContent = i18nMessage(
        "detail.submission.summary_idle",
        view.message || "No submission detail loaded yet.",
      )
    } else {
      summaryNode.textContent = view.message
    }
  } else {
    summaryNode.textContent = view.summary
  }

  const badgesNode = byId(badgesId)
  badgesNode.innerHTML = ""
  ;(view.badges || []).forEach((item) => {
    appendPill(badgesNode, item.label, badgeTone(item.label))
  })

  const rowsNode = byId(rowsId)
  rowsNode.innerHTML = ""
  ;(view.rows || []).forEach((item) => {
    const card = document.createElement("div")
    card.className = "detail-card"

    const label = document.createElement("div")
    label.className = "detail-card-label"
    label.textContent = localizeDetailLabel(item.label)
    card.appendChild(label)

    const value = document.createElement("div")
    value.className = "detail-card-value"
    value.textContent = item.value
    card.appendChild(value)

    rowsNode.appendChild(card)
  })
}

function updateTemplateDetailPanel(detail) {
  state.templateDetail = detail || {}
  if (detail && detail.template_id) {
    syncTemplateScopedFields(detail.template_id, detail.version || "")
    setPanelStatus("templateDetail", { status: "ready", id: detail.template_id, errorMessage: "" })
  }
  const helper = detailHelpers()
  if (!helper || !helper.buildTemplateDetailViewModel) return
  renderDetailPanel(
    "templateDetailSummary",
    "templateDetailBadges",
    "templateDetailRows",
    helper.buildTemplateDetailViewModel(detail),
  )
}

function updateSubmissionDetailPanel(detail) {
  state.submissionDetail = detail || {}
  if (detail && detail.submission_id) {
    applyFieldPatches({
      decisionSubmissionId: detail.submission_id,
      reviewLabels: Array.isArray(detail.review_labels) ? detail.review_labels.join(", ") : "",
      reviewNote: detail.review_note || "",
    })
    setPanelStatus("submissionDetail", { status: "ready", id: detail.submission_id, errorMessage: "" })
  }
  const helper = detailHelpers()
  if (!helper || !helper.buildSubmissionDetailViewModel) return
  renderDetailPanel(
    "submissionDetailSummary",
    "submissionDetailBadges",
    "submissionDetailRows",
    helper.buildSubmissionDetailViewModel(detail),
  )
  renderModerationWorkspace()
}

function syncTemplateScopedFields(templateId, version = "") {
  const nextTemplateId = String(templateId || "").trim()
  if (!nextTemplateId) return

  const templateNode = byId("dryrunTemplateId")
  const planNode = byId("dryrunPlanId")
  const currentTemplateId = templateNode ? String(templateNode.value || "").trim() : ""
  const currentPlanId = planNode ? String(planNode.value || "").trim() : ""
  const currentSuggestedPlanId = defaultPlanId(currentTemplateId)

  const patches = {
    submitTemplateId: nextTemplateId,
    submitVersion: String(version || byId("submitVersion").value || "1.0.0"),
    trialTemplateId: nextTemplateId,
    dryrunTemplateId: nextTemplateId,
    dryrunVersion: String(version || byId("submitVersion").value || byId("dryrunVersion").value || "1.0.0"),
  }
  if (!currentPlanId || currentPlanId === currentSuggestedPlanId) {
    patches.dryrunPlanId = defaultPlanId(nextTemplateId)
  }
  applyFieldPatches(patches)
}

function updateTrialStatusPanel(data = null) {
  state.trialStatus = data
  const summaryNode = byId("trialStatusSummary")
  const detailsNode = byId("trialStatusDetails")

  if (!data || !data.status) {
    summaryNode.textContent = i18nMessage("trial.summary_idle", "No trial status loaded yet.")
    detailsNode.textContent = ""
    return
  }

  const summaryBits = [
    `status=${data.status}`,
    `template=${data.template_id || "-"}`,
  ]
  if (data.status !== "not_started") {
    summaryBits.push(`ttl=${data.ttl_seconds || 0}s`)
    summaryBits.push(`remaining=${data.remaining_seconds || 0}s`)
  }
  summaryNode.textContent = summaryBits.join(" | ")
  detailsNode.textContent = JSON.stringify(data, null, 2)
}

function dryrunDraft() {
  const templateId =
    String(byId("dryrunTemplateId").value || byId("trialTemplateId").value || byId("submitTemplateId").value || "")
      .trim()
  const version =
    String(byId("dryrunVersion").value || byId("submitVersion").value || "1.0.0").trim() || "1.0.0"
  const planId = String(byId("dryrunPlanId").value || defaultPlanId(templateId)).trim()

  applyFieldPatches({
    dryrunPlanId: planId,
    dryrunTemplateId: templateId,
    dryrunVersion: version,
  })

  return {
    plan_id: planId,
    patch: {
      template_id: templateId,
      version,
    },
  }
}

function updateApplyWorkflowPanel(data = null) {
  state.applyPlanResult = data
  const summaryNode = byId("dryrunSummary")
  const detailsNode = byId("dryrunDetails")

  if (!data || (!data.plan_id && !data.status)) {
    summaryNode.textContent = i18nMessage("dryrun.summary_idle", "No apply plan prepared yet.")
    detailsNode.textContent = ""
    return
  }

  if (data.plan_id) {
    applyFieldPatches({ dryrunPlanId: data.plan_id })
  }
  summaryNode.textContent =
    `status=${data.status || "unknown"} | plan=${data.plan_id || "-"} | template=${data.patch && data.patch.template_id ? data.patch.template_id : byId("dryrunTemplateId").value || "-"}`
  detailsNode.textContent = JSON.stringify(data, null, 2)
}

function profilePackDefaultPlanId(packId) {
  const normalized = String(packId || "")
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
  return `profile-plan-${normalized || "default"}`
}

function readSelectedProfilePackRows() {
  const rows = []
  const checkboxes = document.querySelectorAll("input[data-profile-section]")
  checkboxes.forEach((node) => {
    rows.push({
      name: String(node.getAttribute("data-profile-section") || ""),
      checked: Boolean(node.checked),
    })
  })
  return rows
}

function renderProfilePackSections(rows) {
  const container = byId("profilePackSectionList")
  if (!container) return
  container.innerHTML = ""
  const items = Array.isArray(rows) ? rows : []
  const guidance = profilePackGuidanceHelpers()
  if (!items.length) {
    const empty = document.createElement("div")
    empty.className = "note"
    empty.textContent = i18nMessage(
      "profile_pack.sections_empty",
      "No imported sections yet. Import a profile pack first.",
    )
    container.appendChild(empty)
    return
  }
  items.forEach((item) => {
    const sectionName = String((item && item.name) || "").trim()
    if (!sectionName) return
    const sectionMeta = guidance && guidance.describeSection
      ? guidance.describeSection(sectionName)
      : null
    const label = document.createElement("label")
    label.className = "profile-pack-section-item"
    const input = document.createElement("input")
    input.type = "checkbox"
    input.checked = Boolean(item.checked)
    input.setAttribute("data-profile-section", sectionName)
    label.appendChild(input)

    const body = document.createElement("span")
    body.className = "profile-pack-section-body"
    const titleRow = document.createElement("span")
    titleRow.className = "profile-pack-section-title-row"

    const title = document.createElement("span")
    title.className = "profile-pack-section-title"
    title.textContent =
      sectionMeta && sectionMeta.known && sectionMeta.titleKey
        ? i18nMessage(sectionMeta.titleKey, sectionName)
        : sectionName
    titleRow.appendChild(title)

    if (sectionMeta && sectionMeta.stateful) {
      appendPill(
        titleRow,
        i18nMessage("profile_pack.section.badge.stateful", "Stateful"),
        "warning",
      )
    }
    if (sectionMeta && sectionMeta.localData) {
      appendPill(
        titleRow,
        i18nMessage("profile_pack.section.badge.local_data", "Local Data"),
        "neutral",
      )
    }
    body.appendChild(titleRow)

    if (sectionMeta && sectionMeta.known && sectionMeta.descriptionKey) {
      const description = document.createElement("span")
      description.className = "profile-pack-section-description"
      description.textContent = i18nMessage(
        sectionMeta.descriptionKey,
        sectionName,
      )
      body.appendChild(description)
    }

    label.appendChild(body)
    container.appendChild(label)
  })
}

function setProfilePackSections(sectionNames, selectedSections = []) {
  const helper = profilePackHelpers()
  const rows = helper && helper.buildSectionRows
    ? helper.buildSectionRows(sectionNames, selectedSections)
    : (Array.isArray(sectionNames) ? sectionNames : []).map((name) => ({ name, checked: true }))
  state.profilePack.sections = rows
  renderProfilePackSections(rows)
}

function clearProfilePackCompatibilityActionStatus() {
  const node = byId("profilePackCompatibilityActionStatus")
  if (!node) return
  node.classList.add("hidden")
  node.classList.remove("is-warning")
  node.classList.remove("is-success")
  node.textContent = ""
}

function setProfilePackCompatibilityActionStatus(message, tone = "success") {
  const node = byId("profilePackCompatibilityActionStatus")
  if (!node) return
  node.classList.remove("hidden")
  node.classList.remove("is-warning")
  node.classList.remove("is-success")
  if (tone === "warning") {
    node.classList.add("is-warning")
  } else {
    node.classList.add("is-success")
  }
  node.textContent = message
}

function highlightUiTarget(node) {
  if (!node || !node.classList) return
  node.classList.add("ui-focus-target")
  setTimeout(() => {
    if (node && node.classList) {
      node.classList.remove("ui-focus-target")
    }
  }, 1400)
}

function profilePackSectionCheckbox(sectionName) {
  const escaped = sectionName && String(sectionName || "").replace(/"/g, '\\"')
  if (!escaped) return null
  return document.querySelector(`input[data-profile-section="${escaped}"]`)
}

function normalizeProfilePackNameList(value) {
  const rows = Array.isArray(value)
    ? value
    : String(value || "")
        .split(",")
        .map((item) => item.trim())
  const out = []
  const seen = new Set()
  rows.forEach((item) => {
    const text = String(item || "").trim()
    if (!text || seen.has(text)) return
    seen.add(text)
    out.push(text)
  })
  return out
}

function mergeProfilePackNameList(baseValues, newValues) {
  return normalizeProfilePackNameList([...(baseValues || []), ...(newValues || [])])
}

function mergeProfilePackTextInputValues(inputId, incomingValues) {
  const node = byId(inputId)
  if (!node) return []
  const merged = mergeProfilePackNameList(
    normalizeProfilePackNameList(node.value),
    normalizeProfilePackNameList(incomingValues),
  )
  node.value = merged.join(",")
  return merged
}

function ensureProfilePackSectionsSelected(sectionNames) {
  const names = normalizeProfilePackNameList(sectionNames)
  if (!names.length) return []

  names.forEach((name) => {
    const checkbox = profilePackSectionCheckbox(name)
    if (checkbox) {
      checkbox.checked = true
    }
  })

  if (Array.isArray(state.profilePack.sections) && state.profilePack.sections.length > 0) {
    const sectionSet = new Set(names)
    state.profilePack.sections = state.profilePack.sections.map((row) => {
      if (!row || !row.name) return row
      if (!sectionSet.has(row.name)) return row
      return {
        ...row,
        checked: true,
      }
    })
  }

  mergeProfilePackTextInputValues("profilePackSections", names)
  return names
}

function collectProfilePackPluginPrefillCandidates() {
  const missing = []
  const required = []
  const missingSeen = new Set()
  const requiredSeen = new Set()

  const pushRows = (bucket, seen, rows) => {
    normalizeProfilePackNameList(rows).forEach((item) => {
      if (seen.has(item)) return
      seen.add(item)
      bucket.push(item)
    })
  }

  const appendSource = (source) => {
    if (!source || typeof source !== "object") return
    pushRows(missing, missingSeen, source.missing_plugins)
    pushRows(required, requiredSeen, source.required_plugins)
    if (source.plugin_install && typeof source.plugin_install === "object") {
      pushRows(missing, missingSeen, source.plugin_install.missing_plugins)
      pushRows(required, requiredSeen, source.plugin_install.required_plugins)
    }
  }

  appendSource(state.profilePack.lastOperation)
  appendSource(state.profilePack.dryrun)
  return missing.length > 0 ? missing : required
}

function prefillProfilePackPluginIds(pluginIds) {
  const normalized = normalizeProfilePackNameList(pluginIds)
  if (!normalized.length) return []
  mergeProfilePackTextInputValues("profilePackPluginIds", normalized)
  return normalized
}

function applyProfilePackActionPrefill(actionCode, target) {
  const guidance = profilePackGuidanceHelpers()
  const actionPrefill = guidance && guidance.resolveActionPrefill
    ? guidance.resolveActionPrefill(actionCode)
    : null

  const ensuredSections = ensureProfilePackSectionsSelected([
    target && target.sectionName ? target.sectionName : "",
    ...(actionPrefill && Array.isArray(actionPrefill.ensureSections) ? actionPrefill.ensureSections : []),
  ])

  let pluginIds = []
  if (actionPrefill && actionPrefill.prefillPluginIds) {
    pluginIds = prefillProfilePackPluginIds(collectProfilePackPluginPrefillCandidates())
  }

  return {
    sections: ensuredSections,
    pluginIds,
  }
}

function composeProfilePackShortcutStatus(baseMessage, prefill) {
  const details = []
  const sectionList = normalizeProfilePackNameList(prefill && prefill.sections)
  const pluginList = normalizeProfilePackNameList(prefill && prefill.pluginIds)
  if (sectionList.length > 0) {
    details.push(
      i18nFormat(
        "profile_pack.action.shortcut.prefill_sections",
        "sections={sections}",
        { sections: sectionList.join(",") },
      ),
    )
  }
  if (pluginList.length > 0) {
    details.push(
      i18nFormat(
        "profile_pack.action.shortcut.prefill_plugin_ids",
        "plugin_ids={plugin_ids}",
        { plugin_ids: pluginList.join(",") },
      ),
    )
  }
  if (details.length === 0) return baseMessage
  const prefillText = i18nFormat(
    "profile_pack.action.shortcut.prefill_applied",
    "Prefill applied: {details}",
    { details: details.join(" | ") },
  )
  return `${baseMessage} ${prefillText}`
}

function applyProfilePackActionShortcut(actionCode) {
  const guidance = profilePackGuidanceHelpers()
  const target = guidance && guidance.resolveActionTarget
    ? guidance.resolveActionTarget(actionCode)
    : null
  if (!target) {
    setProfilePackCompatibilityActionStatus(
      i18nMessage(
        "profile_pack.action.shortcut.unknown_action",
        "Shortcut target is unavailable for this action.",
      ),
      "warning",
    )
    return
  }

  if (target.developerModeRequired && !state.developerMode) {
    state.profilePack.pendingCompatibilityAction = actionCode
    const toggleNode = byId("btnToggleDeveloperMode")
    if (toggleNode && toggleNode.scrollIntoView) {
      toggleNode.scrollIntoView({ behavior: "smooth", block: "center" })
    }
    if (toggleNode && typeof toggleNode.focus === "function") {
      toggleNode.focus()
      highlightUiTarget(toggleNode)
    }
    setProfilePackCompatibilityActionStatus(
      i18nMessage(
        "profile_pack.action.shortcut.developer_mode_required_pending",
        "Enable Developer Mode first. This action will continue automatically.",
      ),
      "warning",
    )
    return
  }
  state.profilePack.pendingCompatibilityAction = ""

  const detailsNode = target.detailsId ? byId(target.detailsId) : null
  if (detailsNode && String(detailsNode.tagName || "").toUpperCase() === "DETAILS") {
    detailsNode.open = true
  }
  const prefill = applyProfilePackActionPrefill(actionCode, target)

  if (target.sectionName) {
    const sectionNode = profilePackSectionCheckbox(target.sectionName)
    if (sectionNode && sectionNode.scrollIntoView) {
      sectionNode.scrollIntoView({ behavior: "smooth", block: "center" })
    }
    if (sectionNode && typeof sectionNode.focus === "function") {
      sectionNode.focus()
      highlightUiTarget(sectionNode)
    }
    setProfilePackCompatibilityActionStatus(
      composeProfilePackShortcutStatus(
        i18nMessage(
          target.statusKey || "profile_pack.action.shortcut.highlighted_knowledge_base",
          "Focused knowledge-base section for follow-up checks.",
        ),
        prefill,
      ),
      "success",
    )
    return
  }

  const targetNode = target.targetId ? byId(target.targetId) : null
  if (targetNode && targetNode.scrollIntoView) {
    targetNode.scrollIntoView({ behavior: "smooth", block: "center" })
  }

  const focusNode = target.focusId ? byId(target.focusId) : null
  if (focusNode && typeof focusNode.focus === "function") {
    focusNode.focus()
    highlightUiTarget(focusNode)
  } else if (targetNode) {
    highlightUiTarget(targetNode)
  }

  setProfilePackCompatibilityActionStatus(
    composeProfilePackShortcutStatus(
      i18nMessage(
        target.statusKey || "profile_pack.action.shortcut.opened_target",
        "Opened related operation panel.",
      ),
      prefill,
    ),
    "success",
  )
}

function resetProfilePackCompatibilityPanel() {
  const summaryNode = byId("profilePackCompatibilitySummary")
  const issuesNode = byId("profilePackCompatibilityIssues")
  const actionsNode = byId("profilePackCompatibilityActions")
  const developerNode = byId("profilePackCompatibilityDeveloper")
  state.profilePack.pendingCompatibilityAction = ""
  if (summaryNode) {
    summaryNode.textContent = i18nMessage(
      "profile_pack.compatibility.idle",
      "No compatibility guidance yet.",
    )
  }
  if (issuesNode) {
    issuesNode.innerHTML = ""
    issuesNode.classList.add("hidden")
  }
  if (actionsNode) {
    actionsNode.innerHTML = ""
    actionsNode.classList.add("hidden")
  }
  if (developerNode) {
    developerNode.textContent = ""
    developerNode.classList.add("hidden")
  }
  clearProfilePackCompatibilityActionStatus()
}

function renderProfilePackCompatibilityPanel(data = null) {
  const summaryNode = byId("profilePackCompatibilitySummary")
  const issuesNode = byId("profilePackCompatibilityIssues")
  const actionsNode = byId("profilePackCompatibilityActions")
  const developerNode = byId("profilePackCompatibilityDeveloper")
  if (!summaryNode && !issuesNode && !actionsNode && !developerNode) return

  const guidance = profilePackGuidanceHelpers()
  if (!data || typeof data !== "object" || !guidance || !guidance.buildCompatibilityIssueView) {
    resetProfilePackCompatibilityPanel()
    return
  }

  const rawIssues = Array.isArray(data.compatibility_issues) ? data.compatibility_issues : []
  const hasCompatibilitySignal =
    String(data.compatibility || "").trim().length > 0 || rawIssues.length > 0
  if (!hasCompatibilitySignal) {
    resetProfilePackCompatibilityPanel()
    return
  }

  const view = guidance.buildCompatibilityIssueView({
    compatibility: data.compatibility || "unknown",
    compatibility_issues: rawIssues,
  })
  clearProfilePackCompatibilityActionStatus()

  const compatibilityValue = String(view.compatibility || "unknown")
  if (summaryNode) {
    if (view.blocked) {
      summaryNode.textContent = i18nFormat(
        "profile_pack.compatibility.blocked_summary",
        "Compatibility: {compatibility} (blocked)",
        { compatibility: compatibilityValue },
      )
    } else if (view.degraded) {
      summaryNode.textContent = i18nFormat(
        "profile_pack.compatibility.degraded_summary",
        "Compatibility: {compatibility} (degraded, manual actions required)",
        { compatibility: compatibilityValue },
      )
    } else if (view.issues.length > 0) {
      summaryNode.textContent = i18nFormat(
        "profile_pack.compatibility.status",
        "Compatibility: {compatibility}",
        { compatibility: compatibilityValue },
      )
    } else {
      summaryNode.textContent = i18nFormat(
        "profile_pack.compatibility.compatible_summary",
        "Compatibility: {compatibility} (no issues)",
        { compatibility: compatibilityValue },
      )
    }
  }

  if (issuesNode) {
    issuesNode.innerHTML = ""
    if (view.issues.length > 0) {
      issuesNode.classList.remove("hidden")
      view.issues.forEach((issue) => {
        const issueShortcut = guidance && guidance.resolveIssueActionCode
          ? guidance.resolveIssueActionCode(issue.code)
          : ""
        const row = issueShortcut ? document.createElement("button") : document.createElement("div")
        if (issueShortcut) {
          row.type = "button"
          row.className = issue.severity === "danger"
            ? "warning-item warning-item-danger warning-action-button warning-issue-button"
            : "warning-item warning-action-button warning-issue-button"
          row.setAttribute("data-issue-code", issue.code)
          row.setAttribute("data-action-code", issueShortcut)
          row.addEventListener("click", () => {
            applyProfilePackActionShortcut(issueShortcut)
          })
        } else {
          row.className = issue.severity === "danger" ? "warning-item warning-item-danger" : "warning-item"
        }
        let message = i18nMessage(issue.issueKey, issue.code)
        if (
          issue.baseCode === "section_hash_mismatch" &&
          String(issue.code || "").includes(":")
        ) {
          const sectionName = String(issue.code || "").split(":").slice(1).join(":").trim() || "unknown"
          message = i18nFormat(
            "profile_pack.issue.section_hash_mismatch_with_section",
            "Section hash mismatch: {section}",
            { section: sectionName },
          )
        }
        row.textContent = message
        issuesNode.appendChild(row)
      })
    } else {
      issuesNode.classList.add("hidden")
    }
  }

  if (actionsNode) {
    actionsNode.innerHTML = ""
    if (view.actionCodes.length > 0) {
      actionsNode.classList.remove("hidden")
      view.actionCodes.forEach((actionCode) => {
        const button = document.createElement("button")
        button.type = "button"
        button.className = "warning-item warning-action-button"
        button.setAttribute("data-action-code", actionCode)
        button.textContent = i18nMessage(
          `profile_pack.action.${actionCode}`,
          actionCode,
        )
        button.addEventListener("click", () => {
          applyProfilePackActionShortcut(actionCode)
        })
        actionsNode.appendChild(button)
      })
    } else {
      actionsNode.classList.add("hidden")
    }
  }

  if (developerNode) {
    if (!state.developerMode) {
      developerNode.textContent = ""
      developerNode.classList.add("hidden")
    } else {
      const developerPayload = {
        compatibility: view.compatibility,
        blocked: view.blocked,
        degraded: view.degraded,
        compatibility_issues: view.issues.map((item) => item.code),
        action_codes: view.actionCodes,
      }
      developerNode.textContent = [
        i18nMessage(
          "profile_pack.compatibility.developer_block",
          "Raw compatibility payload (developer mode)",
        ),
        JSON.stringify(developerPayload, null, 2),
      ].join("\n")
      developerNode.classList.remove("hidden")
    }
  }
}

function updateProfilePackPanel(data = null) {
  const summaryNode = byId("profilePackSummary")
  const detailsNode = byId("profilePackDetails")
  if (!summaryNode || !detailsNode) return
  if (!data || typeof data !== "object") {
    state.profilePack.lastOperation = null
    summaryNode.textContent = i18nMessage("profile_pack.summary_idle", "No profile pack operation yet.")
    detailsNode.textContent = ""
    resetProfilePackCompatibilityPanel()
    return
  }
  state.profilePack.lastOperation = data

  const status = data.status || (data.import_id ? "imported" : data.artifact_id ? "exported" : "updated")
  const summaryParts = [
    i18nFormat("market.summary.part.status", "status={value}", {
      value: enumLabelValue("status", status),
    }),
  ]
  if (data.pack_id) summaryParts.push(`pack=${data.pack_id}`)
  if (data.import_id) summaryParts.push(`import=${data.import_id}`)
  if (data.plan_id) summaryParts.push(`plan=${data.plan_id}`)
  if (data.compatibility) {
    summaryParts.push(
      i18nFormat("profile_pack.compatibility.status", "Compatibility: {compatibility}", {
        compatibility: enumLabelValue("compatibility", data.compatibility),
      }),
    )
  }
  summaryNode.textContent = summaryParts.join(" | ")
  detailsNode.textContent = JSON.stringify(data, null, 2)
  renderProfilePackCompatibilityPanel(data)
}

function updateProfilePackMarketPanel(data = null) {
  const summaryNode = byId("profilePackMarketSummary")
  const detailsNode = byId("profilePackMarketDetails")
  if (!summaryNode || !detailsNode) return
  if (!data || typeof data !== "object") {
    state.profilePack.market.lastOperation = null
    resetProfilePackMarketCompareView()
    renderProfilePackReviewEvidence(null)
    summaryNode.textContent = i18nMessage(
      "profile_pack.market.summary_idle",
      "No profile pack market operation yet.",
    )
    detailsNode.textContent = ""
    return
  }
  state.profilePack.market.lastOperation = data
  if (String(data.status || "").trim() === "compare_ready") {
    const view = renderProfilePackMarketCompareView(data)
    if (view) {
      summaryNode.textContent = view.summary
      renderProfilePackReviewEvidence(data)
      detailsNode.textContent = JSON.stringify(data, null, 2)
      return
    }
  } else {
    resetProfilePackMarketCompareView()
  }

  const status = data.status || "updated"
  const summary = [
    i18nFormat("market.summary.part.status", "status={value}", {
      value: enumLabelValue("status", status),
    }),
  ]
  if (data.submission_id || data.id) {
    summary.push(i18nFormat("market.summary.part.submission", "submission={value}", {
      value: data.submission_id || data.id,
    }))
  }
  if (data.pack_id) {
    summary.push(i18nFormat("market.summary.part.pack", "pack={value}", { value: data.pack_id }))
  }
  if (data.source_submission_id) {
    summary.push(i18nFormat("market.summary.part.source", "source={value}", { value: data.source_submission_id }))
  }
  if (typeof data.featured === "boolean") {
    summary.push(i18nFormat("market.summary.part.featured", "featured={value}", {
      value: data.featured
        ? i18nMessage("option.featured_toggle.true", "featured")
        : i18nMessage("option.featured_toggle.false", "normal"),
    }))
  }
  if (data.risk_level) {
    summary.push(i18nFormat("market.summary.part.risk", "risk={value}", {
      value: enumLabelValue("risk", data.risk_level),
    }))
  }
  if (Number.isFinite(Number(data.changed_sections_count))) {
    summary.push(i18nFormat("market.summary.part.changed", "changed={value}", {
      value: Number(data.changed_sections_count),
    }))
  }
  summaryNode.textContent = summary.join(" | ")
  renderProfilePackReviewEvidence(data)
  detailsNode.textContent = JSON.stringify(data, null, 2)
}

function renderProfilePackReviewEvidence(data = null) {
  const rowsNode = byId("profilePackReviewEvidenceRows")
  if (!rowsNode) return
  rowsNode.innerHTML = ""
  if (!data || typeof data !== "object") return

  const capabilitySummary = data.capability_summary || (data.review_evidence && data.review_evidence.capability_summary) || {}
  const compatibilityMatrix = data.compatibility_matrix || {}
  const reviewEvidence = data.review_evidence || {}
  const pluginInstall = data.plugin_install && typeof data.plugin_install === "object" ? data.plugin_install : {}
  const latestExecution = pluginInstall.latest_execution && typeof pluginInstall.latest_execution === "object"
    ? pluginInstall.latest_execution
    : (data.execution && typeof data.execution === "object" ? data.execution : null)
  const compareHelper = profilePackCompareViewHelpers()
  const executionSummary = latestExecution && compareHelper && typeof compareHelper.summarizePluginInstallExecution === "function"
    ? compareHelper.summarizePluginInstallExecution(latestExecution)
    : null
  const executionGroupParts = []
  if (executionSummary && executionSummary.groups) {
    if (Array.isArray(executionSummary.groups.policy_blocked) && executionSummary.groups.policy_blocked.length) {
      executionGroupParts.push(
        `${i18nMessage("profile_pack.review.group.policy_blocked", "policy")}:${executionSummary.groups.policy_blocked.join("|")}`,
      )
    }
    if (Array.isArray(executionSummary.groups.command_failed) && executionSummary.groups.command_failed.length) {
      executionGroupParts.push(
        `${i18nMessage("profile_pack.review.group.command_failed", "failed")}:${executionSummary.groups.command_failed.join("|")}`,
      )
    }
    if (Array.isArray(executionSummary.groups.timed_out) && executionSummary.groups.timed_out.length) {
      executionGroupParts.push(
        `${i18nMessage("profile_pack.review.group.timed_out", "timeout")}:${executionSummary.groups.timed_out.join("|")}`,
      )
    }
  }

  const rows = [
    {
      label: i18nMessage("profile_pack.review.field.featured", "featured"),
      value: typeof data.featured === "boolean" ? (data.featured ? "yes" : "no") : "-",
    },
    {
      label: i18nMessage("profile_pack.review.field.compatibility", "compatibility"),
      value: enumLabelValue("compatibility", String(data.compatibility || compatibilityMatrix.runtime_result || "unknown")),
    },
    {
      label: i18nMessage("profile_pack.review.field.declared_capabilities", "declared capabilities"),
      value: Array.isArray(capabilitySummary.declared) ? capabilitySummary.declared.join(", ") || "-" : "-",
    },
    {
      label: i18nMessage("profile_pack.review.field.missing_declared", "missing declared"),
      value: Array.isArray(capabilitySummary.missing_declared) ? capabilitySummary.missing_declared.join(", ") || "-" : "-",
    },
    {
      label: i18nMessage("profile_pack.review.field.review_labels", "review labels"),
      value: localizedCodeList("review_label", reviewEvidence.review_labels),
    },
    {
      label: i18nMessage("profile_pack.review.field.warning_flags", "warning flags"),
      value: localizedCodeList("warning_flag", reviewEvidence.warning_flags),
    },
    {
      label: i18nMessage("profile_pack.review.field.plugin_install_status", "plugin install status"),
      value: enumLabelValue("plugin_install_status", String(pluginInstall.status || "unknown")),
    },
    {
      label: i18nMessage("profile_pack.review.field.plugin_install_execution", "plugin install execution"),
      value: executionSummary
        ? `${enumLabelValue("plugin_install_status", executionSummary.status)} (installed=${executionSummary.installed_count}, failed=${executionSummary.failed_count}, blocked=${executionSummary.blocked_count})`
        : "-",
    },
    {
      label: i18nMessage("profile_pack.review.field.plugin_install_failure_groups", "plugin install failure groups"),
      value: executionGroupParts.length ? executionGroupParts.join(" ; ") : "-",
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
    rowsNode.appendChild(card)
  })
}

function resetProfilePackMarketCompareView() {
  const shell = byId("profilePackMarketCompareShell")
  if (!shell) return
  shell.classList.add("hidden")
  const highlights = byId("profilePackMarketCompareHighlights")
  const warnings = byId("profilePackMarketCompareWarnings")
  const cards = byId("profilePackMarketCompareCards")
  const table = byId("profilePackMarketCompareTable")
  const body = table ? table.querySelector("tbody") : null
  if (highlights) highlights.innerHTML = ""
  if (warnings) warnings.innerHTML = ""
  if (cards) cards.innerHTML = ""
  if (body) body.innerHTML = ""
  resetProfilePackMarketCompareDetailPane()
}

function renderProfilePackMarketCompareView(payload) {
  const shell = byId("profilePackMarketCompareShell")
  if (!shell) return null
  const helper = profilePackCompareViewHelpers()
  if (!helper || typeof helper.buildProfilePackCompareView !== "function") {
    resetProfilePackMarketCompareView()
    return null
  }

  const view = helper.buildProfilePackCompareView(payload, {
    t: i18nMessage,
    f: i18nFormat,
  })
  if (!view || view.empty) {
    resetProfilePackMarketCompareView()
    return null
  }
  shell.classList.remove("hidden")

  const highlights = byId("profilePackMarketCompareHighlights")
  if (highlights) {
    highlights.innerHTML = ""
    ;(view.highlights || []).forEach((item) => {
      appendPill(highlights, item.label, item.tone || badgeTone(item.label))
    })
  }

  const warnings = byId("profilePackMarketCompareWarnings")
  if (warnings) {
    warnings.innerHTML = ""
    ;(view.warnings || []).forEach((item) => {
      const node = document.createElement("div")
      node.className = "warning-item"
      if (item.tone === "danger") {
        node.classList.add("warning-item-danger")
      }
      node.textContent = String(item.message || "")
      warnings.appendChild(node)
    })
  }

  const cards = byId("profilePackMarketCompareCards")
  if (cards) {
    cards.innerHTML = ""
    ;(view.cards || []).forEach((item) => {
      const card = document.createElement("div")
      card.className = "detail-card"

      const label = document.createElement("div")
      label.className = "detail-card-label"
      label.textContent = String(item.label || "")
      card.appendChild(label)

      const value = document.createElement("div")
      value.className = "detail-card-value"
      value.textContent = String(item.value || "-")
      card.appendChild(value)

      if (item.tone && item.tone !== "neutral") {
        const toneRow = document.createElement("div")
        toneRow.className = "pill-row"
        appendPill(toneRow, item.tone, item.tone)
        card.appendChild(toneRow)
      }

      cards.appendChild(card)
    })
  }

  const table = byId("profilePackMarketCompareTable")
  const body = table ? table.querySelector("tbody") : null
  if (body) {
    body.innerHTML = ""
    ;(view.sections || []).forEach((item) => {
      const tr = document.createElement("tr")
      tr.appendChild(cell(item.section))
      tr.appendChild(profilePackMarketCompareChangedCell(item))
      tr.appendChild(profilePackMarketCompareSummaryCell(item))
      tr.appendChild(profilePackMarketCompareSizeCell(item))
      tr.appendChild(profilePackMarketCompareActionCell(item))
      body.appendChild(tr)
    })
  }

  return view
}

function profilePackMarketCompareChangedCell(row) {
  const td = document.createElement("td")
  const wrapper = document.createElement("div")
  wrapper.className = "pill-row"
  if (row && row.changed) {
    appendPill(wrapper, i18nMessage("market.compare.changed", "changed"), "danger")
  } else {
    appendPill(wrapper, i18nMessage("market.compare.same", "same"), "success")
  }
  td.appendChild(wrapper)
  return td
}

function profilePackMarketCompareSummaryCell(row) {
  const td = document.createElement("td")
  const wrapper = document.createElement("div")
  wrapper.className = "compare-row-value"
  wrapper.appendChild(
    profilePackMarketCompareValueLine(
      "change_overview",
      resolveProfilePackMarketChangeSummary(row),
    ),
  )
  if (row && row.file_path) {
    wrapper.appendChild(profilePackMarketCompareValueLine("file", row.file_path))
  }
  const preview = Array.isArray(row && row.changed_paths_preview) ? row.changed_paths_preview : []
  preview.slice(0, 2).forEach((path) => {
    wrapper.appendChild(profilePackMarketCompareValueLine("path", path))
  })
  td.appendChild(wrapper)
  return td
}

function resolveProfilePackMarketChangeSummary(row) {
  const summary = String((row && row.change_overview) || "").trim()
  if (summary) return summary
  const preview = Array.isArray(row && row.changed_paths_preview)
    ? row.changed_paths_preview.map((entry) => String(entry || "").trim()).filter(Boolean)
    : []
  if (preview.length) return preview.slice(0, 3).join(", ")
  if (row && row.changed) {
    if (row.file_path) {
      return i18nFormat(
        "market.compare.change_paths_fallback_with_file",
        "File updated: {file}",
        { file: String(row.file_path) },
      )
    }
    return i18nMessage("market.compare.change_paths_fallback", "Change detected")
  }
  return i18nMessage("market.compare.no_changes", "No change")
}

function profilePackMarketCompareActionCell(row) {
  const td = document.createElement("td")
  const button = document.createElement("button")
  button.type = "button"
  button.className = "btn-ghost"
  button.textContent = i18nMessage("market.compare.expand_detail", "Expand Detail")
  if (!row || !row.changed) {
    button.disabled = true
    button.setAttribute("aria-disabled", "true")
  } else {
    button.addEventListener("click", () => {
      renderProfilePackMarketCompareDetailPane(row)
    })
  }
  td.appendChild(button)
  return td
}

function profilePackMarketCompareSizeCell(row) {
  const td = document.createElement("td")
  const wrapper = document.createElement("div")
  wrapper.className = "compare-row-value"
  const beforeSize = Number((row && row.before_size) || 0)
  const afterSize = Number((row && row.after_size) || 0)
  const delta = Number((row && row.delta_size) || 0)
  const deltaLabel = delta >= 0 ? `+${delta}` : `${delta}`
  const bytesLabel = i18nMessage("market.compare.bytes", "bytes")
  wrapper.appendChild(profilePackMarketCompareValueLine("before", `${beforeSize} ${bytesLabel}`))
  wrapper.appendChild(profilePackMarketCompareValueLine("after", `${afterSize} ${bytesLabel}`))
  wrapper.appendChild(profilePackMarketCompareValueLine("delta", `${deltaLabel} ${bytesLabel}`))
  td.appendChild(wrapper)
  return td
}

function profilePackMarketCompareValueLine(side, value) {
  const line = document.createElement("div")
  const sideNode = document.createElement("span")
  sideNode.className = "compare-row-side"
  const sideKey = `market.compare.${String(side || "").toLowerCase()}`
  const sideLabel = i18nMessage(sideKey, String(side || ""))
  sideNode.textContent = `${sideLabel}: `
  line.appendChild(sideNode)

  const valueNode = document.createElement("span")
  valueNode.className = "compare-row-text"
  valueNode.textContent = String(value || "-")
  line.appendChild(valueNode)
  return line
}

function renderProfilePackMarketCompareDetailPane(row) {
  const pane = byId("profilePackMarketCompareDetailPane")
  const meta = byId("profilePackMarketCompareDetailMeta")
  const diff = byId("profilePackMarketCompareDetailDiff")
  const before = byId("profilePackMarketCompareDetailBefore")
  const after = byId("profilePackMarketCompareDetailAfter")
  if (!pane || !meta || !diff || !before || !after) return
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
  diff.textContent = diffRows.join("\n")
  before.textContent = beforeRows.join("\n")
  after.textContent = afterRows.join("\n")
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

function resetProfilePackMarketCompareDetailPane() {
  const pane = byId("profilePackMarketCompareDetailPane")
  const meta = byId("profilePackMarketCompareDetailMeta")
  const diff = byId("profilePackMarketCompareDetailDiff")
  const before = byId("profilePackMarketCompareDetailBefore")
  const after = byId("profilePackMarketCompareDetailAfter")
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

function updateProfilePackRecords(payload = null) {
  const helper = profilePackRecordHelpers()
  const patch = payload && typeof payload === "object" ? payload : {}
  if (helper && helper.mergeRecordCollections) {
    state.profilePack.records = helper.mergeRecordCollections(state.profilePack.records, patch)
  } else {
    state.profilePack.records = {
      exports: Array.isArray(patch.exports) ? patch.exports : state.profilePack.records.exports,
      imports: Array.isArray(patch.imports) ? patch.imports : state.profilePack.records.imports,
    }
  }
  renderProfilePackRecords()
}

function profilePackSubmissionTableFilters() {
  const helper = profilePackMarketHelpers()
  if (helper && helper.buildSubmissionFilterQuery) {
    return helper.buildSubmissionFilterQuery({
      status: byId("profilePackSubmissionStatusFilter").value,
      packQuery: byId("profilePackSubmissionPackFilter").value,
      packType: byId("profilePackSubmissionPackTypeFilter").value,
      riskLevel: byId("profilePackSubmissionRiskFilter").value,
      reviewLabel: byId("profilePackSubmissionReviewLabelFilter").value,
      warningFlag: byId("profilePackSubmissionWarningFlagFilter").value,
    })
  }
  return {
    status: byId("profilePackSubmissionStatusFilter").value,
    pack_id: byId("profilePackSubmissionPackFilter").value,
    pack_type: byId("profilePackSubmissionPackTypeFilter").value,
    risk_level: byId("profilePackSubmissionRiskFilter").value,
    review_label: byId("profilePackSubmissionReviewLabelFilter").value,
    warning_flag: byId("profilePackSubmissionWarningFlagFilter").value,
  }
}

function profilePackCatalogFilters() {
  const helper = profilePackMarketHelpers()
  if (helper && helper.buildCatalogFilterQuery) {
    return helper.buildCatalogFilterQuery({
      packQuery: byId("profilePackCatalogPackFilter").value,
      packType: byId("profilePackCatalogPackTypeFilter").value,
      riskLevel: byId("profilePackCatalogRiskFilter").value,
      featured: byId("profilePackCatalogFeaturedFilter").value,
      reviewLabel: byId("profilePackCatalogReviewLabelFilter").value,
      warningFlag: byId("profilePackCatalogWarningFlagFilter").value,
    })
  }
  return {
    pack_id: byId("profilePackCatalogPackFilter").value,
    pack_type: byId("profilePackCatalogPackTypeFilter").value,
    risk_level: byId("profilePackCatalogRiskFilter").value,
    featured: byId("profilePackCatalogFeaturedFilter").value,
    review_label: byId("profilePackCatalogReviewLabelFilter").value,
    warning_flag: byId("profilePackCatalogWarningFlagFilter").value,
  }
}

function profilePackCatalogCompareQuery() {
  const helper = profilePackMarketHelpers()
  const input = {
    packId: byId("profilePackCatalogPackId").value,
    selectedSections: byId("profilePackCatalogCompareSections").value,
  }
  if (helper && helper.buildCatalogCompareQuery) {
    return helper.buildCatalogCompareQuery(input)
  }
  const query = {
    pack_id: input.packId,
  }
  const normalizedSections = String(input.selectedSections || "")
    .split(",")
    .map((item) => String(item || "").trim())
    .filter(Boolean)
  if (normalizedSections.length > 0) {
    query.selected_sections = normalizedSections.join(",")
  }
  return query
}

function applyProfilePackMarketSubmissionSelection(row) {
  const helper = profilePackMarketHelpers()
  let patch = {}
  if (helper && helper.pickProfilePackSubmissionFields) {
    patch = helper.pickProfilePackSubmissionFields(row)
  } else {
    patch = {
      profilePackDecisionSubmissionId: String((row && (row.submission_id || row.id)) || ""),
      profilePackCatalogPackId: String((row && row.pack_id) || ""),
    }
  }
  applyFieldPatches(patch)
}

function applyProfilePackMarketCatalogSelection(row) {
  const helper = profilePackMarketHelpers()
  let patch = {}
  if (helper && helper.pickProfilePackCatalogFields) {
    patch = helper.pickProfilePackCatalogFields(row)
  } else {
    patch = {
      profilePackCatalogPackId: String((row && row.pack_id) || ""),
      profilePackDecisionSubmissionId: String((row && row.source_submission_id) || ""),
      profilePackFeaturedPackId: String((row && row.pack_id) || ""),
    }
  }
  applyFieldPatches(patch)
}

function recordDisplayText(value, fallback = "-") {
  const text = String(value || "").trim()
  return text || fallback
}

function buildProfilePackRecordPatch(group, row) {
  const helper = profilePackRecordHelpers()
  const packId = String((row && row.pack_id) || "").trim() || byId("profilePackId").value
  const defaultPlanId = profilePackDefaultPlanId(packId || "profile-pack")
  if (helper && helper.buildRecordPatch) {
    return helper.buildRecordPatch(group, row, defaultPlanId)
  }
  if (group === "exports") {
    return {
      profilePackImportArtifactId: recordDisplayText(row.artifact_id, ""),
      profilePackPlanId: defaultPlanId,
      profilePackId: recordDisplayText(row.pack_id, ""),
      profilePackVersion: recordDisplayText(row.version, ""),
    }
  }
  if (group === "imports") {
    const patch = {
      profilePackImportId: recordDisplayText(row.import_id, ""),
      profilePackPlanId: defaultPlanId,
      profilePackId: recordDisplayText(row.pack_id, ""),
      profilePackVersion: recordDisplayText(row.version, ""),
    }
    const sourceArtifactId = recordDisplayText(row.source_artifact_id, "")
    if (sourceArtifactId) {
      patch.profilePackImportArtifactId = sourceArtifactId
    }
    return patch
  }
  return {}
}

function applyProfilePackRecordSelection(group, row) {
  const patch = buildProfilePackRecordPatch(group, row)
  applyFieldPatches(patch)
  if (patch.profilePackImportArtifactId) {
    state.profilePack.exportArtifactId = patch.profilePackImportArtifactId
    applyFieldPatches({ profilePackSubmissionArtifactId: patch.profilePackImportArtifactId })
  }
  if (patch.profilePackImportId) {
    state.profilePack.importId = patch.profilePackImportId
  }
  if (patch.profilePackPlanId) {
    state.profilePack.planId = patch.profilePackPlanId
  }
}

function readProfilePackRecordPackFilter() {
  return String(byId("profilePackRecordPackFilter").value || "").trim()
}

function setProfilePackRecordPackFilter(value) {
  state.profilePack.recordPackFilter = String(value || "").trim()
  byId("profilePackRecordPackFilter").value = state.profilePack.recordPackFilter
}

function profilePackRecordQuickActionIds(group) {
  const helper = profilePackRecordHelpers()
  if (helper && helper.listQuickActions) {
    return helper.listQuickActions(group)
  }
  return ["use"]
}

function profilePackRecordQuickActionLabel(actionId) {
  if (actionId === "use_import") return i18nMessage("profile_pack.records.action.use_import", "Use + Import")
  if (actionId === "use_dryrun") return i18nMessage("profile_pack.records.action.use_dryrun", "Use + Dry-Run")
  return i18nMessage("profile_pack.records.action.use", "Use")
}

async function runProfilePackRecordQuickAction(group, row, actionId) {
  applyProfilePackRecordSelection(group, row)
  if (actionId === "use_import") {
    await importProfilePackFromExport()
    return
  }
  if (actionId === "use_dryrun") {
    if (group === "exports") {
      await importAndDryrunProfilePack()
      return
    }
    await dryrunProfilePack()
    return
  }
}

function renderProfilePackRecordGroup(group, rows) {
  const section = document.createElement("section")
  section.className = "profile-pack-record-group"
  section.dataset.group = group

  const heading = document.createElement("h4")
  heading.textContent = group === "exports"
    ? i18nMessage("profile_pack.records.group.exports", "Exports")
    : i18nMessage("profile_pack.records.group.imports", "Imports")
  section.appendChild(heading)

  const items = Array.isArray(rows) ? rows : []
  if (!items.length) {
    const note = document.createElement("div")
    note.className = "note"
    note.textContent = group === "exports"
      ? i18nMessage("profile_pack.records.empty_exports", "No export records loaded.")
      : i18nMessage("profile_pack.records.empty_imports", "No import records loaded.")
    section.appendChild(note)
    return section
  }

  items.forEach((row) => {
    const item = document.createElement("article")
    item.className = "profile-pack-record-item"

    const head = document.createElement("div")
    head.className = "profile-pack-record-head"
    if (group === "exports") {
      head.textContent = `${recordDisplayText(row.artifact_id)} | ${recordDisplayText(row.pack_id)}@${recordDisplayText(row.version)}`
    } else {
      head.textContent = `${recordDisplayText(row.import_id)} | ${recordDisplayText(row.pack_id)}@${recordDisplayText(row.version)}`
    }
    item.appendChild(head)

    const meta = document.createElement("div")
    meta.className = "profile-pack-record-meta"
    if (group === "exports") {
      meta.textContent = `file=${recordDisplayText(row.filename)} | exported_at=${recordDisplayText(row.exported_at)}`
    } else {
      meta.textContent = `file=${recordDisplayText(row.filename)} | imported_at=${recordDisplayText(row.imported_at)} | compatibility=${recordDisplayText(row.compatibility, "unknown")}`
    }
    item.appendChild(meta)

    const actionRow = document.createElement("div")
    actionRow.className = "profile-pack-record-actions"

    profilePackRecordQuickActionIds(group).forEach((actionId) => {
      const button = document.createElement("button")
      button.type = "button"
      button.className = "record-action-button"
      button.dataset.actionId = actionId
      button.textContent = profilePackRecordQuickActionLabel(actionId)
      button.addEventListener("click", () => {
        void runProfilePackRecordQuickAction(group, row, actionId)
      })
      actionRow.appendChild(button)
    })
    item.appendChild(actionRow)

    section.appendChild(item)
  })

  return section
}

function renderProfilePackRecords() {
  const node = byId("profilePackRecords")
  node.innerHTML = ""
  const records = state.profilePack.records || { exports: [], imports: [] }
  const packIdFilter = state.profilePack.recordPackFilter
  const helper = profilePackRecordHelpers()
  const filtered = helper && helper.filterRecordCollections
    ? helper.filterRecordCollections(records, packIdFilter)
    : records
  const exportRows = Array.isArray(filtered.exports) ? filtered.exports : []
  const importRows = Array.isArray(filtered.imports) ? filtered.imports : []
  const hasAnyStoredRows =
    Array.isArray(records.exports) && records.exports.length > 0 ||
    Array.isArray(records.imports) && records.imports.length > 0

  if (packIdFilter) {
    const filterNote = document.createElement("div")
    filterNote.className = "profile-pack-record-filter-note"
    filterNote.textContent = i18nFormat(
      "profile_pack.records.pack_filter",
      "pack_id filter: {pack_id}",
      { pack_id: packIdFilter },
    )
    node.appendChild(filterNote)
  }

  if (exportRows.length === 0 && importRows.length === 0) {
    if (packIdFilter && hasAnyStoredRows) {
      const note = document.createElement("div")
      note.className = "note"
      note.textContent = i18nMessage(
        "profile_pack.records_empty_filtered",
        "No profile pack records matched current pack_id filter.",
      )
      node.appendChild(note)
      return
    }
    node.textContent = i18nMessage("profile_pack.records_idle", "No profile pack records loaded yet.")
    return
  }

  node.appendChild(renderProfilePackRecordGroup("exports", exportRows))
  node.appendChild(renderProfilePackRecordGroup("imports", importRows))
}

function clearProfilePackPathErrors() {
  const maskInput = byId("profilePackMaskPaths")
  const dropInput = byId("profilePackDropPaths")
  const maskError = byId("profilePackMaskPathError")
  const dropError = byId("profilePackDropPathError")
  maskInput.classList.remove("input-invalid")
  dropInput.classList.remove("input-invalid")
  maskError.textContent = ""
  dropError.textContent = ""
}

function renderProfilePackPathErrors(validation) {
  clearProfilePackPathErrors()
  if (!validation || validation.valid || !Array.isArray(validation.errors)) return

  const grouped = {
    mask_paths: [],
    drop_paths: [],
  }
  validation.errors.forEach((entry) => {
    if (!entry || !entry.field || !grouped[entry.field]) return
    grouped[entry.field].push(String(entry.message || entry.value || "invalid path"))
  })

  if (grouped.mask_paths.length > 0) {
    byId("profilePackMaskPaths").classList.add("input-invalid")
    byId("profilePackMaskPathError").textContent = grouped.mask_paths.join(" | ")
  }
  if (grouped.drop_paths.length > 0) {
    byId("profilePackDropPaths").classList.add("input-invalid")
    byId("profilePackDropPathError").textContent = grouped.drop_paths.join(" | ")
  }
}

function profilePackExportPayload() {
  const helper = profilePackHelpers()
  if (helper && helper.buildExportPayload) {
    return helper.buildExportPayload({
      packId: byId("profilePackId").value,
      version: byId("profilePackVersion").value,
      packType: byId("profilePackType").value,
      redactionMode: byId("profilePackRedactionMode").value,
      sections: byId("profilePackSections").value,
      maskPaths: byId("profilePackMaskPaths").value,
      dropPaths: byId("profilePackDropPaths").value,
    })
  }
  return {
    pack_id: byId("profilePackId").value,
    version: byId("profilePackVersion").value || "1.0.0",
    pack_type: byId("profilePackType").value || "bot_profile_pack",
    redaction_mode: byId("profilePackRedactionMode").value || "exclude_secrets",
    sections: [],
    mask_paths: [],
    drop_paths: [],
  }
}

function profilePackDryrunPayload() {
  const helper = profilePackHelpers()
  const selectedRows = readSelectedProfilePackRows()
  if (helper && helper.buildDryrunPayload) {
    return helper.buildDryrunPayload({
      importId: byId("profilePackImportId").value,
      planId: byId("profilePackPlanId").value,
      sections: selectedRows,
    })
  }
  return {
    import_id: byId("profilePackImportId").value,
    plan_id: byId("profilePackPlanId").value,
    selected_sections: selectedRows.filter((row) => row.checked).map((row) => row.name),
  }
}

async function profilePackImportAndDryrunPayload() {
  const helper = profilePackHelpers()
  const planId = byId("profilePackPlanId").value || profilePackDefaultPlanId(byId("profilePackId").value)
  const selectedRows = readSelectedProfilePackRows()
  const artifactId = String(
    byId("profilePackImportArtifactId").value || state.profilePack.exportArtifactId || ""
  ).trim()

  if (artifactId && helper && helper.buildImportAndDryrunPayload) {
    return helper.buildImportAndDryrunPayload({
      artifactId,
      planId,
      sections: selectedRows,
    })
  }
  if (artifactId) {
    return {
      artifact_id: artifactId,
      plan_id: planId,
    }
  }

  const filePayload = await selectedProfilePackPayload()
  if (!filePayload) return null

  if (helper && helper.buildImportAndDryrunPayload) {
    return helper.buildImportAndDryrunPayload({
      filename: filePayload.filename,
      contentBase64: filePayload.content_base64,
      planId,
      sections: selectedRows,
    })
  }
  return {
    filename: filePayload.filename,
    content_base64: filePayload.content_base64,
    plan_id: planId,
  }
}

async function selectedProfilePackPayload() {
  const input = byId("profilePackFile")
  const file = input.files && input.files[0]
  if (!file) return null
  return {
    filename: file.name,
    content_base64: await readFileAsBase64(file),
  }
}

async function exportProfilePack() {
  const a = actor()
  const payload = profilePackExportPayload()
  const helper = profilePackHelpers()
  if (helper && helper.validateFieldPaths) {
    const validation = helper.validateFieldPaths(payload)
    renderProfilePackPathErrors(validation)
    if (!validation.valid) {
      const failed = {
        status: 400,
        data: {
          ok: false,
          message: "invalid_redaction_path",
          errors: validation.errors,
        },
      }
      render("admin_profile_pack_export_validation", failed)
      updateProfilePackPanel({
        status: "validation_error",
        errors: validation.errors,
      })
      return failed
    }
  }
  clearProfilePackPathErrors()
  const response = await api("/api/admin/profile-pack/export", {
    method: "POST",
    body: { ...a, ...payload },
  })
  render("admin_profile_pack_export", response)
  if (workspaceRequestFailed(response)) return response
  const data = apiData(response)
  state.profilePack.exportArtifactId = data.artifact_id || ""
  state.profilePack.planId = profilePackDefaultPlanId(data.pack_id || byId("profilePackId").value)
  applyFieldPatches({
    profilePackImportArtifactId: state.profilePack.exportArtifactId,
    profilePackSubmissionArtifactId: state.profilePack.exportArtifactId,
    profilePackPlanId: state.profilePack.planId,
  })
  updateProfilePackPanel(data)
  return response
}

async function downloadProfilePackExport() {
  const a = actor()
  const normalizedRole = String(a.role || "").trim().toLowerCase()
  const useAdminEndpoint = hasCapability("admin.profile_pack.manage") && normalizedRole !== "member"
  const useMemberEndpoint = !useAdminEndpoint && hasCapability("member.profile_pack.submissions.export.download")
  if (!useAdminEndpoint && !useMemberEndpoint) {
    render("profile_pack_download", buildClientErrorResponse("permission_denied", "permission denied", 403))
    updateProfilePackPanel({ status: "error", message: "permission denied" })
    return
  }

  const params = new URLSearchParams()
  let fallbackName = "profile-pack-export"
  if (useAdminEndpoint) {
    const artifactId = String(state.profilePack.exportArtifactId || "").trim()
    if (!artifactId) {
      updateProfilePackPanel({ status: "error", message: "No export artifact available yet." })
      return
    }
    params.set("artifact_id", artifactId)
    fallbackName = artifactId
  } else {
    const submissionId = String(byId("profilePackDecisionSubmissionId").value || "").trim()
    if (!submissionId) {
      updateProfilePackPanel({
        status: "error",
        message: i18nMessage("moderation.no_selection", "No submission selected."),
      })
      return
    }
    params.set("user_id", a.user_id)
    params.set("submission_id", submissionId)
    fallbackName = submissionId
  }

  const endpoint = useAdminEndpoint
    ? `/api/admin/profile-pack/export/download?${params.toString()}`
    : `/api/member/profile-pack/submissions/export/download?${params.toString()}`
  const response = await fetch(endpoint, {
    method: "GET",
    headers: state.token && state.token !== "no-auth" ? { Authorization: `Bearer ${state.token}` } : {},
  })
  if (!response.ok) {
    const data = await response.json().catch(() => ({ ok: false, message: "download_failed" }))
    render("profile_pack_download", { status: response.status, data })
    updateProfilePackPanel({ status: "download_failed", error: data })
    return
  }
  const blob = await response.blob()
  const disposition = response.headers.get("Content-Disposition") || ""
  const match = disposition.match(/filename=\"?([^"]+)\"?$/i)
  const filename = match ? match[1] : `${fallbackName}.zip`
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
    artifact_id: params.get("artifact_id") || "",
    submission_id: params.get("submission_id") || "",
    filename,
    size_bytes: blob.size,
  }
  render("profile_pack_download", { status: response.status, data: payload })
  updateProfilePackPanel(payload)
}

async function importProfilePack() {
  const a = actor()
  const payload = await selectedProfilePackPayload()
  if (!payload) {
    updateProfilePackPanel({ status: "error", message: "Select a profile pack .zip file first." })
    return
  }
  const response = await api("/api/admin/profile-pack/import", {
    method: "POST",
    body: {
      ...a,
      filename: payload.filename,
      content_base64: payload.content_base64,
    },
  })
  render("admin_profile_pack_import", response)
  if (workspaceRequestFailed(response)) return response
  applyImportedProfilePackState(apiData(response))
  return response
}

function applyImportedProfilePackState(data) {
  state.profilePack.importId = data.import_id || ""
  const suggestedPlanId = profilePackDefaultPlanId(data.pack_id || byId("profilePackId").value)
  state.profilePack.planId = suggestedPlanId
  const sourceArtifactId = String(data.source_artifact_id || "").trim()
  if (sourceArtifactId) {
    state.profilePack.exportArtifactId = sourceArtifactId
  }
  applyFieldPatches({
    profilePackImportId: state.profilePack.importId,
    profilePackPlanId: suggestedPlanId,
    profilePackImportArtifactId: state.profilePack.exportArtifactId,
    profilePackSubmissionArtifactId: state.profilePack.exportArtifactId,
  })
  setProfilePackSections(data.sections || [], data.sections || [])
  updateProfilePackPanel(data)
}

function applyProfilePackDryrunState(data, fallbackPlanId = "") {
  const dryrun = data && data.dryrun ? data.dryrun : data
  state.profilePack.dryrun = dryrun
  state.profilePack.planId = (dryrun && dryrun.plan_id) || fallbackPlanId || state.profilePack.planId
  if (dryrun && Array.isArray(dryrun.selected_sections) && dryrun.selected_sections.length > 0) {
    setProfilePackSections(dryrun.selected_sections, dryrun.selected_sections)
  }
  applyFieldPatches({ profilePackPlanId: state.profilePack.planId })
  updateProfilePackPanel(dryrun || data || {})
}

async function importProfilePackFromExport() {
  const a = actor()
  const artifactId = String(
    byId("profilePackImportArtifactId").value || state.profilePack.exportArtifactId || ""
  ).trim()
  if (!artifactId) {
    updateProfilePackPanel({ status: "error", message: "Provide artifact_id or export a profile pack first." })
    return
  }
  const response = await api("/api/admin/profile-pack/import/from-export", {
    method: "POST",
    body: {
      ...a,
      artifact_id: artifactId,
    },
  })
  render("admin_profile_pack_import_from_export", response)
  if (workspaceRequestFailed(response)) return response
  applyImportedProfilePackState(apiData(response))
  return response
}

async function importAndDryrunProfilePack() {
  const a = actor()
  const payload = await profilePackImportAndDryrunPayload()
  if (!payload) {
    updateProfilePackPanel({
      status: "error",
      message: "Provide artifact_id or select a profile pack .zip file first.",
    })
    return
  }
  const response = await api("/api/admin/profile-pack/import-and-dryrun", {
    method: "POST",
    body: { ...a, ...payload },
  })
  render("admin_profile_pack_import_and_dryrun", response)
  if (workspaceRequestFailed(response)) return response
  const data = apiData(response)
  applyImportedProfilePackState(data.import || data)
  applyProfilePackDryrunState(data.dryrun || data, payload.plan_id || "")
  return response
}

async function dryrunProfilePack() {
  const a = actor()
  const payload = profilePackDryrunPayload()
  const response = await api("/api/admin/profile-pack/dryrun", {
    method: "POST",
    body: { ...a, ...payload },
  })
  render("admin_profile_pack_dryrun", response)
  if (workspaceRequestFailed(response)) return response
  applyProfilePackDryrunState(apiData(response), payload.plan_id || "")
  return response
}

async function applyProfilePackPlan() {
  const a = actor()
  const planId = byId("profilePackPlanId").value
  const response = await api("/api/admin/profile-pack/apply", {
    method: "POST",
    body: { ...a, plan_id: planId },
  })
  render("admin_profile_pack_apply", response)
  if (workspaceRequestFailed(response)) return response
  const data = apiData(response)
  updateProfilePackPanel({
    ...(state.profilePack.dryrun || {}),
    ...data,
  })
  if (data && data.continuity) {
    setContinuityOutput("continuityDetailOutput", buildContinuityDetailText({ entry: data.continuity }), { entry: data.continuity })
    applyFieldPatches({ continuityPlanId: data.continuity.plan_id || planId })
  }
  return response
}

async function rollbackProfilePackPlan() {
  const a = actor()
  const planId = byId("profilePackPlanId").value
  const response = await api("/api/admin/profile-pack/rollback", {
    method: "POST",
    body: { ...a, plan_id: planId },
  })
  render("admin_profile_pack_rollback", response)
  if (workspaceRequestFailed(response)) return response
  const data = apiData(response)
  updateProfilePackPanel({
    ...(state.profilePack.dryrun || {}),
    ...data,
  })
  if (data && data.continuity) {
    setContinuityOutput("continuityDetailOutput", buildContinuityDetailText({ entry: data.continuity }), { entry: data.continuity })
    applyFieldPatches({ continuityPlanId: data.continuity.plan_id || planId })
  }
  return response
}

async function listProfilePackImports() {
  const a = actor()
  const response = await api(`/api/admin/profile-pack/imports${queryString({
    role: a.role,
    limit: 50,
  })}`)
  render("admin_profile_pack_list_imports", response)
  if (workspaceRequestFailed(response)) return response
  const data = apiData(response)
  updateProfilePackRecords({ imports: data.imports || [] })
  return response
}

async function listProfilePackExports() {
  const a = actor()
  const response = await api(`/api/admin/profile-pack/exports${queryString({
    role: a.role,
    limit: 50,
  })}`)
  render("admin_profile_pack_list_exports", response)
  if (workspaceRequestFailed(response)) return response
  const data = apiData(response)
  updateProfilePackRecords({ exports: data.exports || [] })
  return response
}

function profilePackPluginIds() {
  return String(byId("profilePackPluginIds").value || "")
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean)
}

async function loadProfilePackPluginInstallPlan() {
  const a = actor()
  const importId = String(byId("profilePackImportId").value || "").trim()
  if (!importId) {
    updateProfilePackPanel({ status: "error", message: "import_id is required" })
    return
  }
  const response = await api(`/api/admin/profile-pack/plugin-install-plan${queryString({
    role: a.role,
    import_id: importId,
  })}`)
  render("admin_profile_pack_plugin_install_plan", response)
  if (workspaceRequestFailed(response)) return response
  const data = apiData(response)
  const missing = Array.isArray(data.missing_plugins) ? data.missing_plugins : []
  if (missing.length > 0) {
    byId("profilePackPluginIds").value = missing.join(",")
  }
  updateProfilePackPanel(data)
  return response
}

async function confirmProfilePackPluginInstall() {
  const a = actor()
  const importId = String(byId("profilePackImportId").value || "").trim()
  if (!importId) {
    updateProfilePackPanel({ status: "error", message: "import_id is required" })
    return
  }
  const pluginIds = profilePackPluginIds()
  const payload = {
    ...a,
    import_id: importId,
  }
  if (pluginIds.length > 0) {
    payload.plugin_ids = pluginIds
  }
  const response = await api("/api/admin/profile-pack/plugin-install-confirm", {
    method: "POST",
    body: payload,
  })
  render("admin_profile_pack_plugin_install_confirm", response)
  if (workspaceRequestFailed(response)) return response
  const data = apiData(response)
  const missing = Array.isArray(data.missing_plugins) ? data.missing_plugins : []
  byId("profilePackPluginIds").value = missing.join(",")
  updateProfilePackPanel(data)
  return response
}

async function executeProfilePackPluginInstall() {
  const a = actor()
  const importId = String(byId("profilePackImportId").value || "").trim()
  if (!importId) {
    updateProfilePackPanel({ status: "error", message: "import_id is required" })
    return
  }
  const pluginIds = profilePackPluginIds()
  const payload = {
    ...a,
    import_id: importId,
    dry_run: Boolean(byId("profilePackPluginDryRun").checked),
  }
  if (pluginIds.length > 0) {
    payload.plugin_ids = pluginIds
  }
  const response = await api("/api/admin/profile-pack/plugin-install-execute", {
    method: "POST",
    body: payload,
  })
  render("admin_profile_pack_plugin_install_execute", response)
  if (workspaceRequestFailed(response)) return response
  const data = apiData(response)
  updateProfilePackPanel(data)
  return response
}

function profilePackCommunitySubmitPayload() {
  const a = actor()
  const helper = profilePackMarketHelpers()
  const artifactId = String(
    byId("profilePackSubmissionArtifactId").value || state.profilePack.exportArtifactId || ""
  ).trim()
  const submitOptions = readProfilePackSubmitOptionsFromForm()
  if (helper && helper.buildSubmitPayload) {
    return helper.buildSubmitPayload({
      userId: a.user_id,
      artifactId,
      fallbackArtifactId: state.profilePack.exportArtifactId,
      submitOptions,
    })
  }
  return {
    user_id: a.user_id,
    artifact_id: artifactId,
    submit_options: submitOptions,
  }
}

async function submitProfilePackToCommunity() {
  const payload = profilePackCommunitySubmitPayload()
  const artifactId = String(payload.artifact_id || "").trim()
  if (!artifactId) {
    updateProfilePackMarketPanel({ status: "error", message: "artifact_id is required for community submit" })
    return
  }
  const response = await api("/api/profile-pack/submit", {
    method: "POST",
    body: payload,
  })
  render("profile_pack_submit", response)
  if (workspaceRequestFailed(response)) return response
  const data = apiData(response)
  updateProfilePackMarketPanel(data)
  applyProfilePackMarketSubmissionSelection(data)
  return response
}

async function listProfilePackMarketSubmissions() {
  const a = actor()
  const filters = profilePackSubmissionTableFilters()
  const normalizedRole = String(a.role || "").trim().toLowerCase()
  const useAdminEndpoint = hasCapability("admin.profile_pack.market.review") && normalizedRole !== "member"
  const useMemberEndpoint = !useAdminEndpoint && hasCapability("member.profile_pack.submissions.read")
  setCollectionStatus("profilePackSubmissions", { status: "loading", errorMessage: "" })
  if (!useAdminEndpoint && !useMemberEndpoint) {
    const denied = buildClientErrorResponse("permission_denied", "permission denied", 403)
    render("list_profile_pack_submissions", denied)
    setCollectionStatus("profilePackSubmissions", {
      status: "error",
      count: state.profilePack.market.submissions.length,
      errorMessage: errorMessageForCollection("profilePackSubmissions", denied),
    })
    return denied
  }
  const endpoint = useAdminEndpoint
    ? `/api/admin/profile-pack/submissions${queryString({ role: a.role, ...filters })}`
    : `/api/member/profile-pack/submissions${queryString({ user_id: a.user_id, ...filters })}`
  const response = await api(endpoint)
  render(useAdminEndpoint ? "admin_list_profile_pack_submissions" : "member_list_profile_pack_submissions", response)
  if (workspaceRequestFailed(response)) {
    setCollectionStatus("profilePackSubmissions", {
      status: "error",
      count: state.profilePack.market.submissions.length,
      errorMessage: errorMessageForCollection("profilePackSubmissions", response),
    })
    return response
  }
  const data = apiData(response)
  const rows = data.submissions || []
  updateProfilePackSubmissionTable(rows)
  setCollectionStatus("profilePackSubmissions", {
    status: resolveCollectionStatus(Array.isArray(rows) ? rows.length : 0, filters),
    count: Array.isArray(rows) ? rows.length : 0,
    errorMessage: "",
  })
  updateProfilePackMarketPanel({
    status: "listed",
    count: Array.isArray(rows) ? rows.length : 0,
  })
  return response
}

function profilePackSubmissionDecisionPayload() {
  const a = actor()
  const helper = profilePackMarketHelpers()
  const input = {
    submissionId: byId("profilePackDecisionSubmissionId").value,
    decision: byId("profilePackDecisionValue").value,
    reviewNote: byId("profilePackDecisionReviewNote").value,
    reviewLabels: byId("profilePackDecisionReviewLabels").value,
  }
  let payload = {}
  if (helper && helper.buildSubmissionDecisionPayload) {
    payload = helper.buildSubmissionDecisionPayload(input)
  } else {
    payload = {
      submission_id: input.submissionId,
      decision: String(input.decision || "").toLowerCase(),
      review_note: input.reviewNote,
      review_labels: String(input.reviewLabels || "")
        .split(",")
        .map((item) => item.trim())
        .filter(Boolean),
    }
  }
  return { ...a, ...payload }
}

async function decideProfilePackSubmission() {
  const payload = profilePackSubmissionDecisionPayload()
  if (!String(payload.submission_id || "").trim()) {
    updateProfilePackMarketPanel({ status: "error", message: "submission_id is required" })
    return
  }
  const response = await api("/api/admin/profile-pack/submissions/decide", {
    method: "POST",
    body: payload,
  })
  render("admin_decide_profile_pack_submission", response)
  if (workspaceRequestFailed(response)) return response
  const data = apiData(response)
  updateProfilePackMarketPanel(data)
  applyProfilePackMarketSubmissionSelection(data)
  await listProfilePackMarketSubmissions()
  await listProfilePackCatalog()
  return response
}

async function listProfilePackCatalog() {
  const filters = profilePackCatalogFilters()
  setCollectionStatus("profilePackCatalog", { status: "loading", errorMessage: "" })
  const response = await api(`/api/profile-pack/catalog${queryString(filters)}`)
  render("profile_pack_catalog_list", response)
  if (workspaceRequestFailed(response)) {
    setCollectionStatus("profilePackCatalog", {
      status: "error",
      count: state.profilePack.market.catalog.length,
      errorMessage: errorMessageForCollection("profilePackCatalog", response),
    })
    return response
  }
  const data = apiData(response)
  const rows = data.packs || []
  updateProfilePackCatalogTable(rows)
  setCollectionStatus("profilePackCatalog", {
    status: resolveCollectionStatus(Array.isArray(rows) ? rows.length : 0, filters),
    count: Array.isArray(rows) ? rows.length : 0,
    errorMessage: "",
  })
  updateProfilePackMarketPanel({
    status: "listed",
    count: Array.isArray(rows) ? rows.length : 0,
  })
  return response
}

function profilePackFeaturedPayload() {
  const a = actor()
  return {
    ...a,
    pack_id: byId("profilePackFeaturedPackId").value,
    featured: String(byId("profilePackFeaturedToggle").value || "false").toLowerCase() === "true",
    note: byId("profilePackFeaturedNote").value,
  }
}

async function setProfilePackFeatured() {
  const payload = profilePackFeaturedPayload()
  if (!String(payload.pack_id || "").trim()) {
    updateProfilePackMarketPanel({ status: "error", message: "pack_id is required" })
    return
  }
  const response = await api("/api/admin/profile-pack/catalog/featured", {
    method: "POST",
    body: payload,
  })
  render("profile_pack_catalog_featured", response)
  if (workspaceRequestFailed(response)) return response
  const data = apiData(response)
  updateProfilePackMarketPanel(data)
  applyProfilePackMarketCatalogSelection(data)
  await listProfilePackCatalog()
  return response
}

async function loadProfilePackCatalogDetail() {
  const packId = String(byId("profilePackCatalogPackId").value || "").trim()
  if (!packId) {
    updateProfilePackMarketPanel({ status: "error", message: "pack_id is required" })
    return
  }
  const response = await api(`/api/profile-pack/catalog/detail${queryString({ pack_id: packId })}`)
  render("profile_pack_catalog_detail", response)
  if (workspaceRequestFailed(response)) return response
  const data = apiData(response)
  updateProfilePackMarketPanel(data)
  applyProfilePackMarketCatalogSelection(data)
  return response
}

async function compareProfilePackCatalog() {
  const query = profilePackCatalogCompareQuery()
  const packId = String(query.pack_id || "").trim()
  if (!packId) {
    updateProfilePackMarketPanel({ status: "error", message: "pack_id is required" })
    return
  }
  const response = await api(`/api/profile-pack/catalog/compare${queryString(query)}`)
  render("profile_pack_catalog_compare", response)
  if (workspaceRequestFailed(response)) return response
  const data = apiData(response)
  updateProfilePackMarketPanel(data)
  applyProfilePackMarketCatalogSelection(data)
  return response
}

function renderRiskGlossary() {
  const helper = detailHelpers()
  const rowsNode = byId("riskGlossary")
  rowsNode.innerHTML = ""
  if (!helper || !Array.isArray(helper.riskGlossaryItems)) return
  helper.riskGlossaryItems.forEach((item) => {
    const card = document.createElement("div")
    card.className = "detail-card"

    const group = document.createElement("div")
    group.className = "glossary-group"
    group.textContent = i18nMessage(item.groupKey || "", item.group)
    card.appendChild(group)

    const title = document.createElement("div")
    title.className = "glossary-title"
    title.textContent = i18nMessage(item.titleKey || "", item.title)
    card.appendChild(title)

    const key = document.createElement("div")
    key.className = "detail-card-label"
    key.textContent = item.key
    card.appendChild(key)

    const description = document.createElement("div")
    description.className = "detail-card-value"
    description.textContent = i18nMessage(item.descriptionKey || "", item.description)
    card.appendChild(description)

    rowsNode.appendChild(card)
  })
}

function panelConfig(panelKey) {
  return {
    templateDetail: {
      nodeId: "templateDetailState",
      resource: i18nMessage("panel.template_detail.resource", "Template detail"),
      emptyMessage: i18nMessage("panel.template_detail.empty", "Select a template row to load detail."),
    },
    submissionDetail: {
      nodeId: "submissionDetailState",
      resource: i18nMessage("panel.submission_detail.resource", "Submission detail"),
      emptyMessage: i18nMessage("panel.submission_detail.empty", "Select a submission row to load detail."),
    },
    compare: {
      nodeId: "compareState",
      resource: i18nMessage("panel.compare.resource", "Submission compare"),
      emptyMessage: i18nMessage("panel.compare.empty", "Select a submission row to load compare output."),
    },
  }[panelKey] || null
}

function detailLabelKey(label) {
  const map = {
    "Source submission": "detail.label.source_submission",
    Category: "detail.label.category",
    Tags: "detail.label.tags",
    Maintainer: "detail.label.maintainer",
    "Source channel": "detail.label.source_channel",
    "Trial requests": "detail.label.trial_requests",
    Installs: "detail.label.installs",
    "Prompt generations": "detail.label.prompt_generations",
    "Package generations": "detail.label.package_generations",
    "Community submissions": "detail.label.community_submissions",
    "Last activity": "detail.label.last_activity",
    "Published at": "detail.label.published_at",
    Package: "detail.label.package",
    "Prompt length": "detail.label.prompt_length",
    "Prompt preview": "detail.label.prompt_preview",
    "Review note": "detail.label.review_note",
    Template: "detail.label.template",
    Version: "detail.label.version",
    Source: "detail.label.source_channel",
    Risk: "detail.label.risk",
    User: "detail.label.user",
    "Created at": "detail.label.created_at",
    "Updated at": "detail.label.updated_at",
  }
  return map[String(label || "").trim()] || ""
}

function localizeDetailLabel(label) {
  const fallback = String(label || "")
  const key = detailLabelKey(fallback)
  if (!key) return fallback
  return i18nMessage(key, fallback)
}

function localizeModerationWarning(message) {
  const text = String(message || "")
  if (!text) return ""
  if (text === "High-risk submission. Confirm prompt diff, labels, and warning flags before approval.") {
    return i18nMessage("moderation.warning.high_risk", text)
  }
  if (text === "No published baseline exists yet. Approval will establish the first baseline.") {
    return i18nMessage("moderation.warning.baseline_missing", text)
  }
  if (text.startsWith("Warning flags: ")) {
    return i18nFormat("moderation.warning.flags", "Warning flags: {flags}", {
      flags: text.slice("Warning flags: ".length),
    })
  }
  return text
}

function collectionConfig(collectionKey) {
  return {
    templates: {
      nodeId: "templateListState",
      resource: i18nMessage("templates.resource", "Templates"),
      idleMessage: i18nMessage("templates.idle", "Load templates to browse published packages."),
      emptyUnfilteredMessage: i18nMessage(
        "templates.empty_unfiltered",
        "No templates have been published yet.",
      ),
      emptyFilteredMessage: i18nMessage(
        "templates.empty_filtered",
        "No templates matched the current filters.",
      ),
    },
    submissions: {
      nodeId: "submissionListState",
      resource: i18nMessage("submissions.resource", "Submissions"),
      idleMessage: i18nMessage(
        "submissions.idle",
        "Load submissions to review pending community packages.",
      ),
      emptyUnfilteredMessage: i18nMessage(
        "submissions.empty_unfiltered",
        "No submissions are available yet.",
      ),
      emptyFilteredMessage: i18nMessage(
        "submissions.empty_filtered",
        "No submissions matched the current filters.",
      ),
    },
    profilePackSubmissions: {
      nodeId: "profilePackSubmissionState",
      resource: i18nMessage("profile_pack.market.submissions_resource", "Profile pack submissions"),
      idleMessage: i18nMessage(
        "profile_pack.market.submissions_idle",
        "Load profile-pack submissions to review pending community packs.",
      ),
      emptyUnfilteredMessage: i18nMessage(
        "profile_pack.market.submissions_empty_unfiltered",
        "No profile-pack submissions are available yet.",
      ),
      emptyFilteredMessage: i18nMessage(
        "profile_pack.market.submissions_empty_filtered",
        "No profile-pack submissions matched the current filters.",
      ),
    },
    profilePackCatalog: {
      nodeId: "profilePackCatalogState",
      resource: i18nMessage("profile_pack.market.catalog_resource", "Profile pack catalog"),
      idleMessage: i18nMessage(
        "profile_pack.market.catalog_idle",
        "Load profile-pack catalog to browse published packs.",
      ),
      emptyUnfilteredMessage: i18nMessage(
        "profile_pack.market.catalog_empty_unfiltered",
        "No profile-pack packs are published yet.",
      ),
      emptyFilteredMessage: i18nMessage(
        "profile_pack.market.catalog_empty_filtered",
        "No profile-pack packs matched the current filters.",
      ),
    },
  }[collectionKey] || null
}

function workspaceRequestFailed(response) {
  return !response || response.status >= 400 || (response.data && response.data.ok === false)
}

function renderPanelState(panelKey) {
  const config = panelConfig(panelKey)
  const helper = feedbackHelpers()
  if (!config || !helper || !helper.buildPanelStateView) return
  const node = byId(config.nodeId)
  const view = helper.buildPanelStateView({
    ...config,
    ...(state.panelStatus[panelKey] || {}),
  })
  node.textContent = `${view.title}. ${view.message}`.trim()
  node.className = `workspace-state is-${view.tone}`
  node.classList.toggle("hidden", !view.visible)
}

function setPanelStatus(panelKey, patch) {
  state.panelStatus[panelKey] = {
    ...(state.panelStatus[panelKey] || { status: "idle", id: "", errorMessage: "" }),
    ...(patch || {}),
  }
  renderPanelState(panelKey)
}

function resetPanelStatus(panelKey) {
  setPanelStatus(panelKey, { status: "idle", id: "", errorMessage: "" })
}

function errorMessageForPanel(panelKey, response) {
  const config = panelConfig(panelKey)
  const helper = feedbackHelpers()
  if (!config || !helper || !helper.extractPanelErrorMessage) {
    return `Request failed: ${response && response.status ? response.status : "unknown"}`
  }
  return helper.extractPanelErrorMessage(response, config.resource)
}

function renderCollectionState(collectionKey) {
  const config = collectionConfig(collectionKey)
  const helper = collectionFeedbackHelpers()
  if (!config || !helper || !helper.buildCollectionStateView) return
  const node = byId(config.nodeId)
  const view = helper.buildCollectionStateView({
    ...config,
    ...(state.collectionStatus[collectionKey] || {}),
  })
  node.textContent = `${view.title}. ${view.message}`.trim()
  node.className = `collection-state is-${view.tone}`
  node.classList.toggle("hidden", !view.visible)
}

function setCollectionStatus(collectionKey, patch) {
  state.collectionStatus[collectionKey] = {
    ...(state.collectionStatus[collectionKey] || { status: "idle", count: 0, errorMessage: "" }),
    ...(patch || {}),
  }
  renderCollectionState(collectionKey)
}

function errorMessageForCollection(collectionKey, response) {
  const config = collectionConfig(collectionKey)
  const helper = collectionFeedbackHelpers()
  if (!config || !helper || !helper.extractCollectionErrorMessage) {
    return `Request failed: ${response && response.status ? response.status : "unknown"}`
  }
  return helper.extractCollectionErrorMessage(response, config.resource)
}

function hasActiveCollectionFilters(filters) {
  const helper = collectionStateHelpers()
  if (helper && helper.hasActiveCollectionFilters) {
    return helper.hasActiveCollectionFilters(filters)
  }
  return Object.values(filters || {}).some((value) => String(value || "").trim() !== "")
}

function resolveCollectionStatus(count, filters) {
  const helper = collectionStateHelpers()
  if (helper && helper.resolveCollectionStatus) {
    return helper.resolveCollectionStatus({
      count,
      hasActiveFilters: hasActiveCollectionFilters(filters),
    })
  }
  return count > 0 ? "ready" : "empty_unfiltered"
}

function templateListFilters() {
  const helper = tableInteractionHelpers()
  const sortQuery = helper && helper.buildTemplateSortQuery
    ? helper.buildTemplateSortQuery(byId("templateSortBy").value, byId("templateSortOrder").value)
    : { sort_by: "template_id", sort_order: "asc" }
  return {
    template_id: byId("templateFilterId").value,
    category: byId("templateCategoryFilter").value,
    tag: byId("templateTagFilter").value,
    source_channel: byId("templateSourceChannelFilter").value,
    risk_level: byId("templateRiskFilter").value,
    review_label: byId("templateReviewLabelFilter").value,
    warning_flag: byId("templateWarningFlagFilter").value,
    ...sortQuery,
  }
}

function submissionListFilters() {
  return {
    status: byId("submissionStatus").value,
    template_id: byId("submissionTemplateFilter").value,
    risk_level: byId("submissionRiskFilter").value,
    review_label: byId("submissionReviewLabelFilter").value,
    warning_flag: byId("submissionWarningFlagFilter").value,
  }
}

function activeWorkspaceRoute() {
  const helper = workspaceHelpers()
  if (!helper || !helper.parseWorkspaceHash) {
    return { scope: "", id: "" }
  }
  return helper.parseWorkspaceHash(window.location.hash)
}

function appendWarningItem(container, text) {
  const item = document.createElement("div")
  item.className = "warning-item"
  item.textContent = text
  container.appendChild(item)
}

function renderModerationWorkspace() {
  const helper = workspaceHelpers()
  const view = helper && helper.buildSubmissionModerationViewModel
    ? helper.buildSubmissionModerationViewModel(state.submissionDetail, state.submissionCompare)
    : {
        empty: true,
        title: i18nMessage("moderation.no_selection", "No submission selected."),
        summary: i18nMessage(
          "moderation.summary_idle",
          "Select a submission row to hydrate review fields and compare state.",
        ),
        highlights: [],
        warnings: [],
      }

  byId("moderationSummary").textContent = view.empty
    ? i18nMessage(
        "moderation.summary_idle",
        view.summary || "Select a submission row to hydrate review fields and compare state.",
      )
    : `${view.title} | ${view.summary}`

  const highlightsNode = byId("moderationHighlights")
  highlightsNode.innerHTML = ""
  ;(view.highlights || []).forEach((item) => {
    appendPill(highlightsNode, item.label, item.tone || badgeTone(item.label))
  })

  const warningsNode = byId("moderationWarnings")
  warningsNode.innerHTML = ""
  ;(view.warnings || []).forEach((item) => {
    appendWarningItem(warningsNode, localizeModerationWarning(item))
  })

  const hasManualSubmission = Boolean(String(byId("decisionSubmissionId").value || "").trim())
  byId("btnSaveSubmissionReview").disabled =
    !isControlCapabilityAllowed("btnSaveSubmissionReview") ||
    (!view.canReview && !hasManualSubmission)
  byId("btnApproveSubmission").disabled =
    !isControlCapabilityAllowed("btnApproveSubmission") ||
    (!view.canReview && !hasManualSubmission)
  byId("btnRejectSubmission").disabled =
    !isControlCapabilityAllowed("btnRejectSubmission") ||
    (!view.canReview && !hasManualSubmission)
  byId("btnDownloadSubmissionPackage").disabled =
    !isControlCapabilityAllowed("btnDownloadSubmissionPackage") ||
    (!view.canDownload && !hasManualSubmission)
}

function updateWorkspaceContext(route = activeWorkspaceRoute()) {
  const helper = workspaceHelpers()
  const rawView = helper && helper.buildWorkspaceSummary
    ? helper.buildWorkspaceSummary(route)
    : {
        empty: true,
        title: "No active workspace",
        routeLabel: i18nMessage("workspace.route_idle", "route: idle"),
        description: i18nMessage(
          "workspace.summary_idle",
          "Select a template or submission row to create a persistent workspace route.",
        ),
        scope: "",
        id: "",
      }
  const view = {
    ...rawView,
    routeLabel: rawView.empty ? i18nMessage("workspace.route_idle", "route: idle") : rawView.routeLabel,
    description: rawView.empty
      ? i18nMessage("workspace.summary_idle", "Select a template or submission row to create a persistent workspace route.")
      : rawView.scope === "template"
        ? i18nFormat(
            "workspace.template_pinned",
            "Pinned to template {id}. Refreshing the page restores this selection.",
            { id: rawView.id || route.id || "" },
          )
        : i18nFormat(
            "workspace.submission_pinned",
            "Pinned to submission {id}. Refreshing the page restores review context and compare state.",
            { id: rawView.id || route.id || "" },
          ),
  }

  byId("workspaceRoute").textContent = view.routeLabel
  byId("workspaceSummary").textContent = view.description
  byId("templateWorkspaceRoute").textContent =
    route.scope === "template"
      ? view.routeLabel
      : i18nMessage(
          "workspace.template_route_idle",
          "Template workspace idle. Select a template row or use Load Template Detail.",
        )
  byId("submissionWorkspaceRoute").textContent =
    route.scope === "submission"
      ? view.routeLabel
      : i18nMessage(
          "workspace.submission_route_idle",
          "Submission workspace idle. Select a submission row or use Load Submission Detail.",
        )
  byId("submissionWorkspaceSummary").textContent =
    route.scope === "submission"
      ? i18nMessage(
          "workspace.submission_summary_active",
          "Review context, compare output, and risk scan are pinned to this submission route.",
        )
      : i18nMessage(
          "workspace.submission_summary_idle",
          "Review context, compare output, and risk scan stay together in this workspace.",
        )
}

function setPendingWorkspaceScroll(targetId) {
  state.pendingWorkspaceScrollTarget = targetId || ""
}

function flushPendingWorkspaceScroll() {
  if (!state.pendingWorkspaceScrollTarget) return
  const node = byId(state.pendingWorkspaceScrollTarget)
  if (node && node.scrollIntoView) {
    node.scrollIntoView({ behavior: "smooth", block: "start" })
  }
  state.pendingWorkspaceScrollTarget = ""
}

function buildWorkspaceHash(route) {
  const helper = workspaceHelpers()
  if (!helper || !helper.buildWorkspaceHash) return ""
  return helper.buildWorkspaceHash(route)
}

function clearWorkspacePanels() {
  state.templateDetail = {}
  state.submissionDetail = {}
  state.submissionCompare = null
  clearScanPanelSource()
  resetPanelStatus("templateDetail")
  resetPanelStatus("submissionDetail")
  updateTemplateDetailPanel({})
  updateSubmissionDetailPanel({})
  resetComparePanel()
  rerenderScanPanelFromState()
}

function clearWorkspaceRouteState() {
  state.selectedTemplateId = ""
  state.selectedSubmissionId = ""
  state.marketHub.selectedTemplateId = ""
  updateTemplatesTable(state.templates)
  updateSubmissionsTable(state.submissions)
  closeTemplateDrawer()
  clearWorkspacePanels()
  updateWorkspaceContext({ scope: "", id: "" })
}

async function navigateToWorkspace(route, options = {}) {
  const hash = buildWorkspaceHash(route)
  if (!hash) return
  setPendingWorkspaceScroll(
    options.targetId || (route.scope === "submission" ? "submissionWorkspaceSection" : "templateWorkspaceSection"),
  )
  if (window.location.hash !== hash) {
    window.location.hash = hash
    return
  }
  await syncWorkspaceFromHash()
}

function clearWorkspaceRoute() {
  if (window.location.hash) {
    history.replaceState(null, "", `${window.location.pathname}${window.location.search}`)
  }
  clearWorkspaceRouteState()
}

async function syncWorkspaceFromHash() {
  const route = activeWorkspaceRoute()
  updateWorkspaceContext(route)

  if (!route.scope || !route.id) {
    clearWorkspaceRouteState()
    return
  }

  if (route.scope === "template") {
    state.selectedTemplateId = route.id
    state.selectedSubmissionId = ""
    state.submissionDetail = {}
    resetComparePanel()
    updateSubmissionDetailPanel({})
    clearScanPanelSource()
    rerenderScanPanelFromState()
    syncTemplateScopedFields(route.id)
    updateTemplatesTable(state.templates)
    updateSubmissionsTable(state.submissions)
    await loadTemplateDetail({ templateId: route.id, syncRoute: false })
    flushPendingWorkspaceScroll()
    return
  }

  state.selectedTemplateId = ""
  state.selectedSubmissionId = route.id
  state.templateDetail = {}
  updateTemplateDetailPanel({})
  clearScanPanelSource()
  rerenderScanPanelFromState()
  applyFieldPatches({
    decisionSubmissionId: route.id,
  })
  updateTemplatesTable(state.templates)
  updateSubmissionsTable(state.submissions)
  await loadSubmissionDetail({ submissionId: route.id, syncRoute: false })
  if (hasCapability("admin.submissions.compare")) {
    await loadSubmissionCompare({ submissionId: route.id, syncRoute: false })
  } else {
    resetComparePanel()
  }
  flushPendingWorkspaceScroll()
}

function renderCompareSection(section) {
  const wrapper = document.createElement("section")
  wrapper.className = "compare-section"

  const title = document.createElement("h3")
  title.textContent = section.title
  wrapper.appendChild(title)

  ;(section.rows || []).forEach((item) => {
    const rowNode = document.createElement("div")
    rowNode.className = "compare-row"

    const label = document.createElement("div")
    label.className = "compare-row-label"
    label.textContent = item.label
    rowNode.appendChild(label)

    const values = document.createElement("div")
    values.className = "compare-row-values"
    values.appendChild(renderCompareValue("Submission", item.submission))
    values.appendChild(renderCompareValue("Published", item.published))
    rowNode.appendChild(values)

    const meta = renderCompareMeta(item)
    if (meta) {
      rowNode.appendChild(meta)
    }

    wrapper.appendChild(rowNode)
  })

  return wrapper
}

function renderCompareValue(side, value) {
  const wrapper = document.createElement("div")
  wrapper.className = "compare-row-value"

  const sideNode = document.createElement("div")
  sideNode.className = "compare-row-side"
  sideNode.textContent = side
  wrapper.appendChild(sideNode)

  const valueNode = document.createElement("div")
  valueNode.className = "compare-row-text"
  valueNode.textContent = value
  wrapper.appendChild(valueNode)

  return wrapper
}

function renderCompareMeta(item) {
  const hasChangeSet = (Array.isArray(item.added) && item.added.length) || (Array.isArray(item.removed) && item.removed.length)
  if (!item.changed && !hasChangeSet) {
    return null
  }

  const meta = document.createElement("div")
  meta.className = "compare-row-meta"
  if (item.changed) {
    appendPill(meta, "changed", item.tone || "danger")
  }
  ;(item.added || []).forEach((entry) => {
    appendPill(meta, `added: ${entry}`, "warning")
  })
  ;(item.removed || []).forEach((entry) => {
    appendPill(meta, `removed: ${entry}`, "neutral")
  })
  return meta
}

function applyFieldPatches(patches) {
  Object.entries(patches || {}).forEach(([fieldId, value]) => {
    const node = byId(fieldId)
    if (!node) return
    node.value = value === undefined || value === null ? "" : String(value)
  })
}

function readTextField(fieldId, fallback = "") {
  const node = byId(fieldId)
  if (!node) return String(fallback)
  return String(node.value || "").trim()
}

function readIntegerField(fieldId, fallback = 0, minValue = null) {
  const node = byId(fieldId)
  const parsed = Number.parseInt(String(node && node.value !== undefined ? node.value : ""), 10)
  const base = Number.isFinite(parsed) ? parsed : Number.parseInt(String(fallback), 10)
  if (minValue === null || !Number.isFinite(Number(minValue))) {
    return Number.isFinite(base) ? base : 0
  }
  return Math.max(Number(minValue), Number.isFinite(base) ? base : 0)
}

function readCheckboxField(fieldId, fallback = false) {
  const node = byId(fieldId)
  if (!node || !("checked" in node)) return Boolean(fallback)
  return Boolean(node.checked)
}

function setCheckboxField(fieldId, value) {
  const node = byId(fieldId)
  if (!node || !("checked" in node)) return
  node.checked = Boolean(value)
}

function setJsonOutput(nodeId, payload) {
  const node = byId(nodeId)
  if (!node) return
  node.textContent = JSON.stringify(payload, null, 2)
}

function storageValueText(value, fallback = "-") {
  if (value === undefined || value === null) return fallback
  const text = String(value).trim()
  return text || fallback
}

function formatStorageBytes(value) {
  const bytes = Number(value)
  if (!Number.isFinite(bytes) || bytes <= 0) return "0 B"
  const units = ["B", "KB", "MB", "GB", "TB"]
  let amount = bytes
  let unit = units[0]
  for (let index = 0; index < units.length; index += 1) {
    unit = units[index]
    if (amount < 1024 || index === units.length - 1) break
    amount /= 1024
  }
  const precision = amount >= 100 ? 0 : amount >= 10 ? 1 : 2
  return `${amount.toFixed(precision)} ${unit}`
}

function buildStorageLocalSummaryText(data) {
  if (!data || typeof data !== "object") {
    return i18nMessage("storage.output.empty", "No storage response data.")
  }
  const lines = [
    i18nMessage("storage.output.local_summary.header", "Local Summary"),
    i18nFormat("storage.output.local_summary.root", "Storage root: {value}", {
      value: storageValueText(data.storage_root),
    }),
    i18nFormat("storage.output.local_summary.files", "Scanned files: {count}", {
      count: Number(data.scanned_file_count || 0),
    }),
    i18nFormat("storage.output.local_summary.size", "Estimated size: {value}", {
      value: formatStorageBytes(data.estimated_size_bytes || 0),
    }),
    i18nFormat("storage.output.local_summary.backup_jobs", "Backup jobs: total={total}, active={active}, succeeded={succeeded}", {
      total: Number(data.backup_jobs_total || 0),
      active: Number(data.backup_jobs_active || 0),
      succeeded: Number(data.backup_jobs_succeeded || 0),
    }),
    i18nFormat("storage.output.local_summary.restore_jobs", "Restore jobs: total={total}", {
      total: Number(data.restore_jobs_total || 0),
    }),
  ]
  if (data.last_backup_job && typeof data.last_backup_job === "object") {
    lines.push(
      i18nFormat("storage.output.local_summary.last_job", "Last backup: {job_id} ({status})", {
        job_id: storageValueText(data.last_backup_job.job_id),
        status: enumLabelValue("status", data.last_backup_job.status),
      }),
    )
  }
  if (data.scan_truncated) {
    lines.push(i18nMessage("storage.output.local_summary.scan_truncated", "Local scan hit file ceiling and was truncated."))
  }
  if (data.scan_error) {
    lines.push(
      i18nFormat("storage.output.error", "Error: {message}", {
        message: storageValueText(data.scan_error),
      }),
    )
  }
  return lines.join("\n")
}

function buildStoragePoliciesText(data) {
  const policies = data && typeof data === "object" && data.policies && typeof data.policies === "object"
    ? data.policies
    : null
  if (!policies) {
    return i18nMessage("storage.output.empty", "No storage response data.")
  }
  return [
    i18nMessage("storage.output.policies.header", "Backup Policies"),
    `rpo_hours=${storageValueText(policies.rpo_hours)}`,
    `local_retention_snapshots=${storageValueText(policies.local_retention_snapshots)}`,
    `remote_retention_days=${storageValueText(policies.remote_retention_days)}`,
    `daily_upload_budget_gb=${storageValueText(policies.daily_upload_budget_gb)}`,
    `upload_bandwidth_limit_mbps=${storageValueText(policies.upload_bandwidth_limit_mbps)}`,
    `command_timeout_seconds=${storageValueText(policies.command_timeout_seconds)}`,
    `pack_format=${storageValueText(policies.pack_format)}`,
    `sync_remote_enabled=${storageValueText(policies.sync_remote_enabled)}`,
    `rclone_remote_path=${storageValueText(policies.rclone_remote_path, "(empty)")}`,
    `last_updated_at=${storageValueText(policies.last_updated_at, "-")}`,
    `last_updated_by=${storageValueText(policies.last_updated_by, "-")}`,
  ].join("\n")
}

function buildStorageJobsText(data) {
  const rows = data && typeof data === "object" && Array.isArray(data.jobs)
    ? data.jobs
    : []
  if (!rows.length) {
    return i18nMessage("storage.output.jobs.empty", "No backup jobs matched current filter.")
  }
  const lines = [
    i18nFormat("storage.output.jobs.header", "Backup Jobs ({count})", { count: rows.length }),
  ]
  rows.slice(0, 20).forEach((row, index) => {
    const status = enumLabelValue("status", row.status)
    const artifact = storageValueText(row.artifact_id, "-")
    const size = formatStorageBytes(row.artifact_size_bytes || 0)
    lines.push(
      `${index + 1}. ${storageValueText(row.job_id)} | ${status} | artifact=${artifact} | size=${size}`,
    )
  })
  return lines.join("\n")
}

function buildStorageJobDetailText(data) {
  const job = data && typeof data === "object" && data.job && typeof data.job === "object"
    ? data.job
    : null
  if (!job) {
    return i18nMessage("storage.output.empty", "No storage response data.")
  }
  const lines = [
    i18nMessage("storage.output.job_detail.header", "Backup Job Detail"),
    `${storageValueText(job.job_id)} | ${enumLabelValue("status", job.status)}`,
    `artifact_id=${storageValueText(job.artifact_id)}`,
    `artifact_path=${storageValueText(job.artifact_path, "-")}`,
    `artifact_size=${formatStorageBytes(job.artifact_size_bytes || 0)}`,
  ]
  if (job.reason) {
    lines.push(
      i18nFormat("storage.output.reason", "Reason: {value}", {
        value: storageValueText(job.reason),
      }),
    )
  }
  return lines.join("\n")
}

function buildStorageRestoreText(data) {
  const restore = data && typeof data === "object" && data.restore && typeof data.restore === "object"
    ? data.restore
    : null
  if (!restore) {
    return i18nMessage("storage.output.empty", "No storage response data.")
  }
  const lines = [
    i18nMessage("storage.output.restore.header", "Restore Detail"),
    `${storageValueText(restore.restore_id)} | state=${storageValueText(restore.restore_state)}`,
    `artifact_ref=${storageValueText(restore.artifact_ref)}`,
    `artifact_sha256=${storageValueText(restore.artifact_sha256, "-")}`,
    `requested_by=${storageValueText(restore.requested_by, "-")}`,
  ]
  if (restore.commit_mode) {
    lines.push(`commit_mode=${storageValueText(restore.commit_mode)}`)
  }
  return lines.join("\n")
}

function buildStorageRestoreJobsText(data) {
  const rows = data && typeof data === "object" && Array.isArray(data.jobs)
    ? data.jobs
    : []
  if (!rows.length) {
    return i18nMessage("storage.output.restore_jobs.empty", "No restore jobs matched current filter.")
  }
  const lines = [
    i18nFormat("storage.output.restore_jobs.header", "Restore Jobs ({count})", { count: rows.length }),
  ]
  rows.slice(0, 20).forEach((row, index) => {
    lines.push(
      `${index + 1}. ${storageValueText(row.restore_id)} | state=${storageValueText(row.restore_state)} | artifact_ref=${storageValueText(row.artifact_ref)}`,
    )
  })
  return lines.join("\n")
}

function formatAuditActionCounts(rows, limit = 3) {
  const items = Array.isArray(rows) ? rows.filter(Boolean) : []
  if (!items.length) return "-"
  return items.slice(0, limit).map((item) => `${storageValueText(item.action)} x${Number(item.count || 0)}`).join(", ")
}

function buildAuditSummaryText(data) {
  const summary = data && typeof data === "object" && data.summary && typeof data.summary === "object"
    ? data.summary
    : null
  if (!summary || Number(summary.total || 0) <= 0) {
    return i18nMessage("audit.output.empty", "No audit events matched current window.")
  }

  const lines = [
    i18nMessage("audit.output.summary.header", "Audit Summary"),
    i18nFormat("audit.output.summary.window", "Window: total={total} | first={first} | last={last}", {
      total: Number(summary.total || 0),
      first: storageValueText(summary.first_event_at),
      last: storageValueText(summary.last_event_at),
    }),
  ]

  const groups = [
    ["audit.output.summary.actions", "Top Actions", Array.isArray(summary.actions) ? summary.actions : [], (item) => `${storageValueText(item.action)} | count=${Number(item.count || 0)} | last=${storageValueText(item.last_event_at)}`],
    ["audit.output.summary.actor_roles", "Actor Roles", Array.isArray(summary.actor_roles) ? summary.actor_roles : [], (item) => `${storageValueText(item.actor_role)} | count=${Number(item.count || 0)} | last=${storageValueText(item.last_event_at)}`],
    ["audit.output.summary.actors", "Actors", Array.isArray(summary.actors) ? summary.actors : [], (item) => `${storageValueText(item.actor_role)}/${storageValueText(item.actor_id)} | count=${Number(item.count || 0)} | last=${storageValueText(item.last_event_at)}`],
    ["audit.output.summary.reviewers", "Reviewer Activity", Array.isArray(summary.reviewers) ? summary.reviewers : [], (item) => `${storageValueText(item.reviewer_id)} | count=${Number(item.count || 0)} | roles=${storageValueText((item.actor_roles || []).join(","), "-")} | devices=${storageValueText((item.device_ids || []).join(","), "-")} | actions=${formatAuditActionCounts(item.actions, 4)}`],
    ["audit.output.summary.devices", "Device Activity", Array.isArray(summary.devices) ? summary.devices : [], (item) => `${storageValueText(item.reviewer_id, "-")} / ${storageValueText(item.device_id)} | count=${Number(item.count || 0)} | actions=${formatAuditActionCounts(item.actions, 4)}`],
  ]

  groups.forEach(([titleKey, fallback, rows, renderRow]) => {
    const items = Array.isArray(rows) ? rows : []
    if (!items.length) return
    lines.push("")
    lines.push(i18nMessage(titleKey, fallback))
    items.slice(0, 5).forEach((item, index) => {
      lines.push(`${index + 1}. ${renderRow(item)}`)
    })
  })

  return lines.join("\n")
}

function buildAuditEventsText(data) {
  const events = data && typeof data === "object" && Array.isArray(data.events) ? data.events : []
  if (!events.length) {
    return i18nMessage("audit.output.empty", "No audit events matched current window.")
  }
  const lines = [
    i18nFormat("audit.output.events.header", "Recent Events ({count})", {
      count: events.length,
    }),
  ]
  events.slice(-20).reverse().forEach((item, index) => {
    const detail = item && typeof item.detail === "object" ? item.detail : {}
    const reviewerId = storageValueText(detail.reviewer_id, "")
    const deviceId = storageValueText(detail.device_id, "")
    let suffix = ""
    if (reviewerId || deviceId) {
      suffix = ` | reviewer=${reviewerId || "-"} | device=${deviceId || "-"}`
    }
    lines.push(
      `${index + 1}. ${storageValueText(item.created_at)} | ${storageValueText(item.actor_role)}/${storageValueText(item.actor_id)} | ${storageValueText(item.action)} | status=${storageValueText(item.status)} | target=${storageValueText(item.target_id)}${suffix}`,
    )
  })
  return lines.join("\n")
}

function setAuditOutput(nodeId, summaryText, payload) {
  const node = byId(nodeId)
  if (!node) return
  const summary = String(summaryText || "").trim()
  if (state.developerMode) {
    const raw = JSON.stringify(payload, null, 2)
    node.textContent = summary ? `${summary}\n\n---\n${raw}` : raw
    return
  }
  node.textContent = summary || i18nMessage("audit.output.empty", "No audit events matched current window.")
}

function buildContinuityEntriesText(data) {
  const entries = data && typeof data === "object" && Array.isArray(data.entries)
    ? data.entries
    : []
  if (!entries.length) {
    return i18nMessage("continuity.output.entries.empty", "No continuity entries recorded yet.")
  }
  const lines = [
    i18nFormat("continuity.output.entries.header", "Continuity Entries ({count})", {
      count: entries.length,
    }),
  ]
  entries.slice(0, 20).forEach((item, index) => {
    const sections = Array.isArray(item.selected_sections) && item.selected_sections.length
      ? item.selected_sections.join(",")
      : "-"
    lines.push(
      `${index + 1}. ${storageValueText(item.plan_id)} | status=${storageValueText(item.status)} | source=${storageValueText(item.source_kind)}/${storageValueText(item.source_id)} | sections=${sections} | recovery=${storageValueText(item.recovery_class)} | verify=${storageValueText(item.restore_verification)} | active_snapshot=${item.active_snapshot_available ? "yes" : "no"}`,
    )
  })
  return lines.join("\n")
}

function buildContinuityDetailText(data) {
  const entry = data && typeof data === "object" && data.entry && typeof data.entry === "object"
    ? data.entry
    : null
  if (!entry) {
    return i18nMessage("continuity.output.empty", "No continuity response data.")
  }
  const sections = Array.isArray(entry.selected_sections) && entry.selected_sections.length
    ? entry.selected_sections.join(", ")
    : "-"
  const lines = [
    i18nMessage("continuity.output.detail.header", "Continuity Detail"),
    `plan_id=${storageValueText(entry.plan_id)}`,
    `status=${storageValueText(entry.status)}`,
    `source=${storageValueText(entry.source_kind)}/${storageValueText(entry.source_id)}`,
    `actor=${storageValueText(entry.actor_role)}/${storageValueText(entry.actor_id)}`,
    `sections=${sections}`,
    `recovery_class=${storageValueText(entry.recovery_class)}`,
    `pre_snapshot_id=${storageValueText(entry.pre_snapshot_id)}`,
    `post_snapshot_id=${storageValueText(entry.post_snapshot_id)}`,
    `restore_verification=${storageValueText(entry.restore_verification)}`,
    `active_snapshot_available=${entry.active_snapshot_available ? "yes" : "no"}`,
    `applied_at=${storageValueText(entry.applied_at)}`,
  ]
  if (entry.rolled_back_at) {
    lines.push(`rolled_back_at=${storageValueText(entry.rolled_back_at)}`)
  }
  return lines.join("\n")
}

function setContinuityOutput(nodeId, summaryText, payload) {
  const node = byId(nodeId)
  if (!node) return
  const summary = String(summaryText || "").trim()
  if (state.developerMode) {
    const raw = JSON.stringify(payload, null, 2)
    node.textContent = summary ? `${summary}\n\n---\n${raw}` : raw
    return
  }
  node.textContent = summary || i18nMessage("continuity.output.empty", "No continuity response data.")
}

function setStorageOutput(nodeId, summaryText, payload) {
  const node = byId(nodeId)
  if (!node) return
  const summary = String(summaryText || "").trim()
  if (state.developerMode) {
    const raw = JSON.stringify(payload, null, 2)
    node.textContent = summary ? `${summary}\n\n---\n${raw}` : raw
    return
  }
  node.textContent = summary || i18nMessage("storage.output.empty", "No storage response data.")
}

function applyStoragePolicyFields(policies) {
  if (!policies || typeof policies !== "object") return
  applyFieldPatches({
    storagePolicyRpoHours: policies.rpo_hours,
    storagePolicyLocalRetentionSnapshots: policies.local_retention_snapshots,
    storagePolicyRemoteRetentionDays: policies.remote_retention_days,
    storagePolicyDailyBudgetGb: policies.daily_upload_budget_gb,
    storagePolicyBandwidthLimitMpbs: policies.upload_bandwidth_limit_mbps,
    storagePolicyCommandTimeoutSeconds: policies.command_timeout_seconds,
    storagePolicyPackFormat: policies.pack_format,
    storagePolicyRcloneBinary: policies.rclone_binary,
    storagePolicyRcloneRemotePath: policies.rclone_remote_path,
    storagePolicyRcloneBwlimit: policies.rclone_bwlimit,
  })
  setCheckboxField("storagePolicySyncRemoteEnabled", policies.sync_remote_enabled)
  setCheckboxField("storagePolicyEncryptionRequired", policies.encryption_required)
  setCheckboxField("storagePolicyBackupEnabled", policies.backup_enabled)
  setCheckboxField("storagePolicySingleActiveLock", policies.single_active_backup_lock)
  setCheckboxField("storagePolicyIncludeProfilePacks", policies.include_profile_packs)
  setCheckboxField("storagePolicyIncludePackages", policies.include_packages)
}

async function listContinuityEntries() {
  const a = actor()
  const limit = readIntegerField("continuityLimit", 10, 1)
  const response = await api(`/api/admin/continuity${queryString({ role: a.role, limit })}`)
  render("admin_continuity_list", response)
  const data = apiData(response)
  setContinuityOutput("continuitySummaryOutput", buildContinuityEntriesText(data), data)
  return response
}

async function getContinuityDetail(options = {}) {
  const a = actor()
  const planId = String(
    options.planId || readTextField("continuityPlanId", "") || readTextField("dryrunPlanId", ""),
  ).trim()
  if (!planId) {
    setContinuityOutput(
      "continuityDetailOutput",
      i18nMessage("continuity.output.plan_id_required", "plan_id is required."),
      { error: "plan_id_required" },
    )
    return { status: 400, data: { ok: false, error: { code: "plan_id_required" } } }
  }
  applyFieldPatches({ continuityPlanId: planId })
  const response = await api(`/api/admin/continuity/detail${queryString({ role: a.role, plan_id: planId })}`)
  render("admin_continuity_detail", response)
  const data = apiData(response)
  setContinuityOutput("continuityDetailOutput", buildContinuityDetailText(data), data)
  return response
}

function readStoragePoliciesPatch() {
  return {
    rpo_hours: readIntegerField("storagePolicyRpoHours", 24, 1),
    local_retention_snapshots: readIntegerField("storagePolicyLocalRetentionSnapshots", 3, 1),
    remote_retention_days: readIntegerField("storagePolicyRemoteRetentionDays", 30, 1),
    daily_upload_budget_gb: readIntegerField("storagePolicyDailyBudgetGb", 700, 1),
    upload_bandwidth_limit_mbps: readIntegerField("storagePolicyBandwidthLimitMpbs", 10, 1),
    command_timeout_seconds: readIntegerField("storagePolicyCommandTimeoutSeconds", 900, 30),
    pack_format: readTextField("storagePolicyPackFormat", "tar.gz") || "tar.gz",
    rclone_binary: readTextField("storagePolicyRcloneBinary", "rclone") || "rclone",
    rclone_remote_path: readTextField("storagePolicyRcloneRemotePath", ""),
    rclone_bwlimit: readTextField("storagePolicyRcloneBwlimit", "10M") || "10M",
    sync_remote_enabled: readCheckboxField("storagePolicySyncRemoteEnabled", false),
    encryption_required: readCheckboxField("storagePolicyEncryptionRequired", true),
    backup_enabled: readCheckboxField("storagePolicyBackupEnabled", true),
    single_active_backup_lock: readCheckboxField("storagePolicySingleActiveLock", true),
    include_profile_packs: readCheckboxField("storagePolicyIncludeProfilePacks", true),
    include_packages: readCheckboxField("storagePolicyIncludePackages", false),
  }
}

function interactionSelection(scope, item) {
  const helper = tableInteractionHelpers()
  if (!helper) {
    return { selectedId: "", fieldPatches: {}, requests: [] }
  }
  if (scope === "template" && helper.buildTemplateSelection) {
    return helper.buildTemplateSelection(item)
  }
  if (scope === "submission" && helper.buildSubmissionSelection) {
    return helper.buildSubmissionSelection(item)
  }
  return { selectedId: "", fieldPatches: {}, requests: [] }
}

async function handleTemplateSelection(item) {
  const selection = interactionSelection("template", item)
  state.selectedTemplateId = selection.selectedId
  state.marketHub.selectedTemplateId = selection.selectedId
  applyFieldPatches(selection.fieldPatches)
  updateTemplatesTable(state.templates)
  openTemplateDrawer(selection.selectedId)
  if (selection.requests.includes("template_detail")) {
    await navigateToWorkspace({ scope: "template", id: selection.selectedId })
  }
}

async function handleSubmissionSelection(item) {
  const selection = interactionSelection("submission", item)
  state.selectedSubmissionId = selection.selectedId
  applyFieldPatches(selection.fieldPatches)
  updateSubmissionsTable(state.submissions)
  if (selection.requests.includes("submission_detail")) {
    await navigateToWorkspace({ scope: "submission", id: selection.selectedId })
  }
}

function clearNodeChildren(node) {
  if (!node) return
  node.innerHTML = ""
}

function numeric(value) {
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : 0
}

function templateEngagement(item) {
  const data = item && item.engagement && typeof item.engagement === "object" ? item.engagement : {}
  return {
    trials: numeric(data.trial_requests),
    installs: numeric(data.installs),
    prompts: numeric(data.prompt_generations),
    packages: numeric(data.package_generations),
    lastActivityAt: String(data.last_activity_at || item?.last_activity_at || ""),
  }
}

function templateHeatScore(item) {
  const stats = templateEngagement(item)
  return (stats.installs * 4) + (stats.trials * 3) + stats.prompts + (stats.packages * 2)
}

function templateLastActivityTs(item) {
  const raw = templateEngagement(item).lastActivityAt
  const parsed = Date.parse(raw)
  return Number.isFinite(parsed) ? parsed : 0
}

function templateLooksFeatured(item) {
  const tokens = [
    ...(Array.isArray(item?.tags) ? item.tags : []),
    ...(Array.isArray(item?.review_labels) ? item.review_labels : []),
    String(item?.source_channel || ""),
    String(item?.maintainer || ""),
  ]
    .map((entry) => String(entry || "").trim().toLowerCase())
    .filter(Boolean)

  return tokens.some(
    (entry) =>
      entry.includes("featured") ||
      entry.includes("official") ||
      entry.includes("curated") ||
      entry.includes("staff_pick") ||
      entry.includes("recommended"),
  )
}

function sortTemplatesByHeat(rows) {
  const items = Array.isArray(rows) ? rows.slice() : []
  return items.sort((left, right) => {
    const deltaScore = templateHeatScore(right) - templateHeatScore(left)
    if (deltaScore !== 0) return deltaScore
    return templateLastActivityTs(right) - templateLastActivityTs(left)
  })
}

function templateCardModel(item) {
  const helper = marketCardHelpers()
  if (helper && helper.buildTemplateCardModel) {
    return helper.buildTemplateCardModel(item)
  }
  return {
    id: String((item && item.template_id) || ""),
    title: String((item && item.template_id) || ""),
    subtitle: `${String((item && item.category) || "general")} · v${String((item && item.version) || "-")}`,
    risk: String((item && item.risk_level) || "unknown"),
    riskTone: badgeTone(item && item.risk_level),
    maintainer: String((item && item.maintainer) || "unknown"),
    sourceChannel: String((item && item.source_channel) || "community"),
    badges: [],
    signals: [],
    raw: item || {},
  }
}

function templateDrawerRows(item) {
  const helper = marketCardHelpers()
  if (helper && helper.buildTemplateDrawerRows) {
    return helper.buildTemplateDrawerRows(item)
  }
  return [
    { label: "Template", value: String((item && item.template_id) || "-") },
    { label: "Version", value: String((item && item.version) || "-") },
  ]
}

function localizeMarketSignalLabel(entry) {
  const key = String((entry && entry.key) || "").trim().toLowerCase()
  const fallbackLabel = String((entry && entry.label) || key || "")
  if (key) {
    return i18nMessage(`market.signal.${key}`, fallbackLabel)
  }
  const fallbackMap = {
    Trials: "market.signal.trials",
    Installs: "market.signal.installs",
    Prompts: "market.signal.prompts",
    Packages: "market.signal.packages",
  }
  const keyFromLabel = fallbackMap[fallbackLabel]
  if (!keyFromLabel) return fallbackLabel
  return i18nMessage(keyFromLabel, fallbackLabel)
}

function isNodeVisible(node) {
  if (!node) return false
  if (node.classList && node.classList.contains("hidden")) return false
  if (typeof node.getAttribute === "function") {
    const ariaHidden = String(node.getAttribute("aria-hidden") || "").toLowerCase()
    if (ariaHidden === "true") return false
  }
  if (typeof globalThis.getComputedStyle === "function") {
    const style = globalThis.getComputedStyle(node)
    if (style && (style.display === "none" || style.visibility === "hidden")) {
      return false
    }
  }
  return true
}

function focusableNodes(container) {
  if (!container || typeof container.querySelectorAll !== "function") return []
  return Array.from(container.querySelectorAll(FOCUSABLE_SELECTOR)).filter((node) => {
    if (!node || typeof node.focus !== "function") return false
    if (node.disabled) return false
    if (!isNodeVisible(node)) return false
    return true
  })
}

function focusFirstInteractiveNode(container) {
  const nodes = focusableNodes(container)
  if (!nodes.length) return false
  nodes[0].focus()
  return true
}

function focusFirstOutsideContainer(container) {
  if (!container || typeof document.querySelectorAll !== "function") return false
  const nodes = Array.from(document.querySelectorAll(FOCUSABLE_SELECTOR)).filter((node) => {
    if (!node || typeof node.focus !== "function") return false
    if (node.disabled) return false
    if (!isNodeVisible(node)) return false
    return !container.contains(node)
  })
  if (!nodes.length) return false
  nodes[0].focus()
  return true
}

function trapFocus(container, event) {
  if (event.key !== "Tab") return false
  const nodes = focusableNodes(container)
  if (!nodes.length) return false
  const first = nodes[0]
  const last = nodes[nodes.length - 1]
  const active = document.activeElement

  if (event.shiftKey) {
    if (active === first || !container.contains(active)) {
      event.preventDefault()
      last.focus()
      return true
    }
    return false
  }

  if (active === last || !container.contains(active)) {
    event.preventDefault()
    first.focus()
    return true
  }
  return false
}

function activateDialogFocus(scopeKey, container, options = {}) {
  if (!container) return
  const entry = dialogFocusState[scopeKey]
  if (!entry) return
  const scrollLock = dialogScrollLockHelpers()
  const activeElement = document.activeElement
  if (activeElement && typeof activeElement.focus === "function") {
    entry.restoreFocusTarget = activeElement
  } else {
    entry.restoreFocusTarget = null
  }
  entry.resolveFallbackFocus = typeof options.resolveFallbackFocus === "function"
    ? options.resolveFallbackFocus
    : null
  if (entry.keydownHandler) {
    document.removeEventListener("keydown", entry.keydownHandler, true)
  }
  const close = typeof options.close === "function" ? options.close : null
  entry.keydownHandler = (event) => {
    if (!isNodeVisible(container)) return
    const active = document.activeElement
    const inside = Boolean(active && container.contains(active))
    if (event.key === "Escape" && inside) {
      event.preventDefault()
      if (close) close()
      return
    }
    if (!inside) return
    trapFocus(container, event)
  }
  document.addEventListener("keydown", entry.keydownHandler, true)
  if (scrollLock && typeof scrollLock.nextOpenDialogScopes === "function") {
    openDialogScopes = scrollLock.nextOpenDialogScopes(openDialogScopes, scopeKey, true)
    if (typeof scrollLock.syncBodyScrollLock === "function") {
      scrollLock.syncBodyScrollLock(document.body, openDialogScopes)
    }
  }
  container.setAttribute("tabindex", "-1")
  if (!focusFirstInteractiveNode(container)) {
    container.focus()
  }
}

function deactivateDialogFocus(scopeKey, container) {
  if (!container) return
  const entry = dialogFocusState[scopeKey]
  if (!entry) return
  const scrollLock = dialogScrollLockHelpers()
  if (entry.keydownHandler) {
    document.removeEventListener("keydown", entry.keydownHandler, true)
    entry.keydownHandler = null
  }
  if (scrollLock && typeof scrollLock.nextOpenDialogScopes === "function") {
    openDialogScopes = scrollLock.nextOpenDialogScopes(openDialogScopes, scopeKey, false)
    if (typeof scrollLock.syncBodyScrollLock === "function") {
      scrollLock.syncBodyScrollLock(document.body, openDialogScopes)
    }
  }
  let restore = entry.restoreFocusTarget
  entry.restoreFocusTarget = null
  if ((!restore || !document.contains(restore)) && typeof entry.resolveFallbackFocus === "function") {
    restore = entry.resolveFallbackFocus()
  }
  entry.resolveFallbackFocus = null
  if (restore && typeof restore.focus === "function" && document.contains(restore)) {
    restore.focus()
  }
  if (container.contains(document.activeElement)) {
    focusFirstOutsideContainer(container)
  }
}

function setTemplateDrawerVisible(visible) {
  const node = byId("templateDrawer")
  if (!node) return
  state.marketHub.templateDrawerOpen = Boolean(visible)
  node.setAttribute("role", "dialog")
  node.setAttribute("aria-modal", "true")
  node.classList.toggle("hidden", !visible)
  node.setAttribute("aria-hidden", visible ? "false" : "true")
  if (visible) {
    activateDialogFocus("templateDrawer", node, {
      close: closeTemplateDrawer,
      resolveFallbackFocus: () => {
        const selected = document.querySelector("#templateCardGrid .template-card.is-selected")
        if (selected) return selected
        return document.querySelector("#templateCardGrid .template-card")
      },
    })
  } else {
    deactivateDialogFocus("templateDrawer", node)
  }
}

function renderTemplateDrawer(templateId) {
  const drawerTitle = byId("templateDrawerTitle")
  const drawerMeta = byId("templateDrawerMeta")
  const badgesNode = byId("templateDrawerBadges")
  const signalsNode = byId("templateDrawerSignals")
  if (!drawerTitle || !drawerMeta || !badgesNode || !signalsNode) return

  const item = state.templates.find((row) => String((row && row.template_id) || "") === String(templateId || ""))
  if (!item) {
    drawerTitle.textContent = i18nMessage("market.drawer.empty_title", "Select a template card")
    drawerMeta.textContent = i18nMessage(
      "market.drawer.empty_meta",
      "Template details and action shortcuts appear here.",
    )
    clearNodeChildren(badgesNode)
    clearNodeChildren(signalsNode)
    setTemplateDrawerVisible(false)
    return
  }

  const model = templateCardModel(item)
  drawerTitle.textContent = model.title || templateId
  drawerMeta.textContent = `${model.subtitle} · ${model.maintainer}`
  clearNodeChildren(badgesNode)
  ;(model.badges || []).forEach((badge) => {
    appendPill(badgesNode, badge.label, badge.tone || badgeTone(badge.label))
  })
  if (!model.badges || !model.badges.length) {
    appendPill(badgesNode, `risk:${model.risk || "unknown"}`, model.riskTone || "neutral")
  }

  clearNodeChildren(signalsNode)
  templateDrawerRows(item).forEach((entry) => {
    const card = document.createElement("div")
    card.className = "detail-card"
    const label = document.createElement("div")
    label.className = "detail-card-label"
    label.textContent = localizeDetailLabel(entry.label)
    card.appendChild(label)
    const value = document.createElement("div")
    value.className = "detail-card-value"
    value.textContent = String(entry.value || "-")
    card.appendChild(value)
    signalsNode.appendChild(card)
  })
  setTemplateDrawerVisible(true)
}

function openTemplateDrawer(templateId) {
  state.marketHub.selectedTemplateId = String(templateId || "")
  renderTemplateDrawer(templateId)
}

function closeTemplateDrawer() {
  setTemplateDrawerVisible(false)
}

function renderTemplateCards(rows) {
  const grid = byId("templateCardGrid")
  if (!grid) return
  clearNodeChildren(grid)
  const items = Array.isArray(rows) ? rows : []
  if (!items.length) {
    const empty = document.createElement("div")
    empty.className = "template-grid-empty"
    empty.textContent = i18nMessage(
      "market.templates.empty_cards",
      "No template cards to display. Load templates first.",
    )
    grid.appendChild(empty)
    return
  }

  items.forEach((item) => {
    const model = templateCardModel(item)
    const card = document.createElement("article")
    card.className = "template-card"
    card.tabIndex = 0
    if (model.id && model.id === state.selectedTemplateId) {
      card.classList.add("is-selected")
    }

    const top = document.createElement("div")
    top.className = "template-card-top"
    const risk = document.createElement("span")
    risk.className = `pill is-${model.riskTone || "neutral"}`
    risk.textContent = model.risk || "unknown"
    top.appendChild(risk)
    const version = document.createElement("span")
    version.className = "template-card-version"
    version.textContent = String((item && item.version) || "-")
    top.appendChild(version)
    card.appendChild(top)

    const title = document.createElement("h3")
    title.className = "template-card-title"
    title.textContent = model.title || "-"
    card.appendChild(title)

    const subtitle = document.createElement("p")
    subtitle.className = "template-card-subtitle"
    subtitle.textContent = model.subtitle || "-"
    card.appendChild(subtitle)

    const badges = document.createElement("div")
    badges.className = "pill-row"
    ;(model.badges || []).forEach((badge) => {
      appendPill(badges, badge.label, badge.tone || "neutral")
    })
    card.appendChild(badges)

    const signals = document.createElement("div")
    signals.className = "template-card-signals"
    ;(model.signals || []).forEach((entry) => {
      const signal = document.createElement("div")
      signal.className = "template-card-signal"
      const label = document.createElement("span")
      label.textContent = localizeMarketSignalLabel(entry)
      signal.appendChild(label)
      const value = document.createElement("strong")
      value.textContent = String(entry.value || "0")
      signal.appendChild(value)
      signals.appendChild(signal)
    })
    card.appendChild(signals)

    const selectCard = async () => {
      await handleTemplateSelection(item)
    }
    card.addEventListener("click", () => {
      void selectCard()
    })
    card.addEventListener("keydown", (event) => {
      if (event.key !== "Enter" && event.key !== " ") return
      event.preventDefault()
      void selectCard()
    })
    grid.appendChild(card)
  })
}

function renderFeaturedTemplateCard(item) {
  const container = byId("featuredTemplateCard")
  if (!container) return
  clearNodeChildren(container)
  if (!item) return

  const model = templateCardModel(item)
  const stats = templateEngagement(item)
  const button = document.createElement("button")
  button.type = "button"
  button.className = "featured-template-entry"
  if (model.id && model.id === state.selectedTemplateId) {
    button.classList.add("is-selected")
  }

  const title = document.createElement("div")
  title.className = "featured-template-title"
  title.textContent = model.title || "-"
  button.appendChild(title)

  const subtitle = document.createElement("div")
  subtitle.className = "featured-template-subtitle"
  subtitle.textContent = model.subtitle || "-"
  button.appendChild(subtitle)

  const metrics = document.createElement("div")
  metrics.className = "featured-template-metrics"
  metrics.textContent = i18nFormat("market.insight.activity", "installs {installs} · trials {trials}", {
    installs: stats.installs,
    trials: stats.trials,
  })
  button.appendChild(metrics)

  const score = document.createElement("div")
  score.className = "featured-template-score"
  score.textContent = i18nFormat("market.insight.score", "heat {score}", {
    score: templateHeatScore(item),
  })
  button.appendChild(score)

  const action = document.createElement("div")
  action.className = "featured-template-action"
  action.textContent = i18nMessage("market.featured.select", "Use + Open Drawer")
  button.appendChild(action)

  button.addEventListener("click", () => {
    void handleTemplateSelection(item)
  })
  container.appendChild(button)
}

function renderTrendingTemplateList(items) {
  const listNode = byId("trendingTemplateList")
  if (!listNode) return
  clearNodeChildren(listNode)
  ;(items || []).forEach((item, index) => {
    const row = document.createElement("button")
    row.type = "button"
    row.className = "trending-template-item"
    if (String(item?.template_id || "") === state.selectedTemplateId) {
      row.classList.add("is-selected")
    }

    const rank = document.createElement("span")
    rank.className = "trending-template-rank"
    rank.textContent = i18nFormat("market.trending.rank", "#{rank}", { rank: index + 1 })
    row.appendChild(rank)

    const name = document.createElement("span")
    name.className = "trending-template-name"
    name.textContent = String(item?.template_id || "-")
    row.appendChild(name)

    const score = document.createElement("span")
    score.className = "trending-template-score"
    score.textContent = i18nFormat("market.insight.score", "heat {score}", {
      score: templateHeatScore(item),
    })
    row.appendChild(score)

    row.addEventListener("click", () => {
      void handleTemplateSelection(item)
    })
    listNode.appendChild(row)
  })
}

function renderMarketInsights(rows) {
  const featuredState = byId("featuredTemplateState")
  const trendingState = byId("trendingTemplateState")
  const featuredCard = byId("featuredTemplateCard")
  const trendingList = byId("trendingTemplateList")
  if (!featuredState || !trendingState || !featuredCard || !trendingList) return

  const items = Array.isArray(rows) ? rows : []
  if (!items.length) {
    featuredState.classList.remove("hidden")
    trendingState.classList.remove("hidden")
    featuredState.textContent = i18nMessage(
      "market.featured.empty",
      "No templates available for featured view.",
    )
    trendingState.textContent = i18nMessage(
      "market.trending.empty",
      "No templates available for trending ranking.",
    )
    clearNodeChildren(featuredCard)
    clearNodeChildren(trendingList)
    return
  }

  const sorted = sortTemplatesByHeat(items)
  const featuredPool = items.filter((item) => templateLooksFeatured(item))
  const featuredCandidate = (featuredPool.length ? sortTemplatesByHeat(featuredPool) : sorted)[0]

  featuredState.classList.add("hidden")
  trendingState.classList.add("hidden")
  renderFeaturedTemplateCard(featuredCandidate)
  renderTrendingTemplateList(sorted.slice(0, 5))
}

async function applyBadgeFilter(scope, category, value) {
  const helper = tableInteractionHelpers()
  if (!helper || !helper.buildBadgeFilterPatch) return
  const patch = helper.buildBadgeFilterPatch(scope, category, value)
  applyFieldPatches(patch)
  if (scope === "template") {
    await listTemplates()
    return
  }
  if (scope === "profile_pack_submission") {
    await listProfilePackMarketSubmissions()
    return
  }
  if (scope === "profile_pack_catalog") {
    await listProfilePackCatalog()
    return
  }
  await listSubmissions()
}

function cell(text) {
  const td = document.createElement("td")
  td.textContent = text
  return td
}

function joinLabels(items) {
  return Array.isArray(items) && items.length ? items.join(", ") : "-"
}

function pillCell(scope, category, items) {
  const td = document.createElement("td")
  const values = Array.isArray(items) ? items.filter(Boolean) : []
  if (!values.length) {
    td.textContent = "-"
    return td
  }

  const row = document.createElement("div")
  row.className = "pill-row table-pill-row"
  values.forEach((item) => {
    const rawValue = String(item)
    appendInteractivePill(
      row,
      scope,
      category,
      rawValue,
      badgeTone(rawValue),
      enumLabelValue(category, rawValue),
    )
  })
  td.appendChild(row)
  return td
}

function bindInteractiveRow(tr, onSelect) {
  tr.classList.add("interactive-row")
  tr.tabIndex = 0
  tr.addEventListener("click", () => {
    void onSelect()
  })
  tr.addEventListener("keydown", (event) => {
    if (event.key !== "Enter" && event.key !== " ") return
    event.preventDefault()
    void onSelect()
  })
}

function reviewerLifecycleNode(nodeId) {
  return byId(nodeId)
}

function setReviewerLifecycleState(nodeId, tone, key, fallback, tokens = {}) {
  const node = reviewerLifecycleNode(nodeId)
  if (!node) return
  node.textContent = i18nFormat(key, fallback, tokens)
  node.className = `collection-state is-${tone}`
}

function formatEpochTimestamp(value) {
  const numeric = Number(value)
  if (!Number.isFinite(numeric) || numeric <= 0) return "-"
  const milliseconds = numeric > 1e12 ? numeric : numeric * 1000
  const timestamp = new Date(milliseconds)
  if (Number.isNaN(timestamp.getTime())) return "-"
  try {
    return timestamp.toLocaleString(state.uiLocale || "en-US", {
      dateStyle: "medium",
      timeStyle: "short",
    })
  } catch (_error) {
    return timestamp.toISOString()
  }
}

function reviewerLifecycleCopyLabel() {
  return i18nMessage("button.copy_code", "Copy code")
}

function reviewerLifecycleRevokeLabel() {
  return i18nMessage("button.revoke", "Revoke")
}

function reviewerLifecycleSelectedReviewerId() {
  const node = byId("reviewerDeviceTargetId")
  const value = String(node && node.value ? node.value : "").trim()
  if (value) {
    state.reviewerLifecycle.selectedReviewerId = value
  }
  return state.reviewerLifecycle.selectedReviewerId || ""
}

function setReviewerLifecycleSelectedReviewer(reviewerId) {
  const normalized = String(reviewerId || "").trim()
  state.reviewerLifecycle.selectedReviewerId = normalized
  const node = byId("reviewerDeviceTargetId")
  if (node && node.value !== normalized) {
    node.value = normalized
  }
}

function renderReviewerLifecycleAuthState() {
  const maxDevices = Number(state.reviewerLifecycle.maxDevices || 0) || 0
  if (!state.authRequired) {
    setReviewerLifecycleState(
      "reviewerLifecycleAuthState",
      "warning",
      "reviewer.lifecycle.auth_state.local_mode",
      "Auth disabled. Reviewer lifecycle runs in local admin mode only.",
    )
    return
  }
  if (state.availableRoles.includes("reviewer")) {
    setReviewerLifecycleState(
      "reviewerLifecycleAuthState",
      "success",
      "reviewer.lifecycle.auth_state.enabled",
      "Reviewer auth enabled. Max devices per reviewer: {count}.",
      { count: maxDevices || 3 },
    )
    return
  }
  setReviewerLifecycleState(
    "reviewerLifecycleAuthState",
    "danger",
    "reviewer.lifecycle.auth_state.unavailable",
    "Reviewer auth is unavailable. Configure reviewer credentials before handing out invites.",
  )
}

async function copyTextToClipboard(value) {
  const text = String(value || "").trim()
  if (!text) return false
  if (!globalThis.navigator || !navigator.clipboard || typeof navigator.clipboard.writeText !== "function") {
    return false
  }
  try {
    await navigator.clipboard.writeText(text)
    return true
  } catch (_error) {
    return false
  }
}

async function copyReviewerInviteCode(inviteCode) {
  const success = await copyTextToClipboard(inviteCode)
  setReviewerLifecycleState(
    "reviewerInviteState",
    success ? "success" : "warning",
    success ? "reviewer.lifecycle.invites.copied" : "reviewer.lifecycle.invites.copy_failed",
    success ? "Invite code copied: {invite_code}" : "Clipboard unavailable. Copy invite code manually: {invite_code}",
    { invite_code: String(inviteCode || "").trim() },
  )
}

function reviewerLifecycleActionButton(label, tone = "ghost") {
  const button = document.createElement("button")
  button.type = "button"
  button.className = tone === "primary" ? "btn-primary compare-inline-action" : "btn-ghost compare-inline-action"
  button.textContent = label
  return button
}

function updateReviewerInviteTable(rows) {
  state.reviewerLifecycle.invites = Array.isArray(rows) ? rows : []
  const table = byId("reviewerInviteTable")
  if (!table) return
  const tbody = table.querySelector("tbody")
  if (!tbody) return
  tbody.innerHTML = ""
  state.reviewerLifecycle.invites.forEach((item) => {
    const tr = document.createElement("tr")
    const inviteCode = String(item.code || item.invite_code || "").trim()
    const status = String(item.status || "unknown").trim().toLowerCase()
    tr.appendChild(cell(inviteCode || "-"))
    tr.appendChild(cell(enumLabelValue("status", status || "unknown")))
    tr.appendChild(cell(String(item.issued_by || "").trim() || "-"))
    tr.appendChild(cell(String(item.redeemed_by || "").trim() || "-"))
    tr.appendChild(cell(formatEpochTimestamp(item.expires_at)))

    const actions = document.createElement("td")
    const actionRow = document.createElement("div")
    actionRow.className = "inline-form wrap"

    const copyButton = reviewerLifecycleActionButton(reviewerLifecycleCopyLabel())
    copyButton.disabled = !hasCapability("admin.reviewer.lifecycle.manage")
    copyButton.addEventListener("click", (event) => {
      event.stopPropagation()
      void copyReviewerInviteCode(inviteCode)
    })
    actionRow.appendChild(copyButton)

    if (status !== "redeemed" && status !== "revoked") {
      const revokeButton = reviewerLifecycleActionButton(reviewerLifecycleRevokeLabel())
      revokeButton.disabled = !hasCapability("admin.reviewer.lifecycle.manage")
      revokeButton.addEventListener("click", (event) => {
        event.stopPropagation()
        void revokeReviewerInvite(inviteCode)
      })
      actionRow.appendChild(revokeButton)
    }

    actions.appendChild(actionRow)
    tr.appendChild(actions)
    bindInteractiveRow(tr, async () => {
      const redeemedBy = String(item.redeemed_by || "").trim()
      if (redeemedBy) {
        setReviewerLifecycleSelectedReviewer(redeemedBy)
        await listReviewerDevices({ reviewerId: redeemedBy })
        await listReviewerSessions({ reviewerId: redeemedBy })
      }
    })
    tbody.appendChild(tr)
  })
}

function updateReviewerAccountTable(rows) {
  state.reviewerLifecycle.accounts = Array.isArray(rows) ? rows : []
  const table = byId("reviewerAccountTable")
  if (!table) return
  const tbody = table.querySelector("tbody")
  if (!tbody) return
  tbody.innerHTML = ""
  state.reviewerLifecycle.accounts.forEach((item) => {
    const tr = document.createElement("tr")
    const reviewerId = String(item.reviewer_id || "").trim()
    tr.appendChild(cell(reviewerId || "-"))
    tr.appendChild(cell(String(item.created_by || "").trim() || "-"))
    tr.appendChild(cell(String(item.source_invite || "").trim() || "-"))
    tr.appendChild(cell(String(Number(item.device_count || 0))))
    tr.appendChild(cell(formatEpochTimestamp(item.created_at)))
    bindInteractiveRow(tr, async () => {
      setReviewerLifecycleSelectedReviewer(reviewerId)
      await listReviewerDevices({ reviewerId })
      await listReviewerSessions({ reviewerId })
    })
    tbody.appendChild(tr)
  })
}

function updateReviewerDeviceTable(rows) {
  state.reviewerLifecycle.devices = Array.isArray(rows) ? rows : []
  const table = byId("reviewerDeviceTable")
  if (!table) return
  const tbody = table.querySelector("tbody")
  if (!tbody) return
  tbody.innerHTML = ""
  state.reviewerLifecycle.devices.forEach((item) => {
    const tr = document.createElement("tr")
    const deviceId = String(item.device_id || "").trim()
    tr.appendChild(cell(deviceId || "-"))
    tr.appendChild(cell(String(item.label || "").trim() || "-"))
    tr.appendChild(cell(formatEpochTimestamp(item.registered_at)))
    tr.appendChild(cell(formatEpochTimestamp(item.last_used_at)))

    const actions = document.createElement("td")
    const actionRow = document.createElement("div")
    actionRow.className = "inline-form wrap"
    const revokeButton = reviewerLifecycleActionButton(reviewerLifecycleRevokeLabel())
    revokeButton.disabled = !hasCapability("admin.reviewer.lifecycle.manage")
    revokeButton.addEventListener("click", (event) => {
      event.stopPropagation()
      void revokeReviewerDevice(deviceId)
    })
    actionRow.appendChild(revokeButton)
    actions.appendChild(actionRow)
    tr.appendChild(actions)
    tbody.appendChild(tr)
  })
}

function updateReviewerSessionTable(rows) {
  state.reviewerLifecycle.sessions = Array.isArray(rows) ? rows : []
  const table = byId("reviewerSessionTable")
  if (!table) return
  const tbody = table.querySelector("tbody")
  if (!tbody) return
  tbody.innerHTML = ""
  state.reviewerLifecycle.sessions.forEach((item) => {
    const tr = document.createElement("tr")
    const sessionId = String(item.session_id || "").trim()
    const reviewerId = String(item.reviewer_id || "").trim()
    const deviceId = String(item.device_id || "").trim()
    tr.appendChild(cell(sessionId || "-"))
    tr.appendChild(cell(deviceId || "-"))
    tr.appendChild(cell(formatEpochTimestamp(item.issued_at)))
    tr.appendChild(cell(formatEpochTimestamp(item.expires_at)))

    const actions = document.createElement("td")
    const actionRow = document.createElement("div")
    actionRow.className = "inline-form wrap"
    const revokeButton = reviewerLifecycleActionButton(reviewerLifecycleRevokeLabel())
    revokeButton.disabled = !hasCapability("admin.reviewer.lifecycle.manage")
    revokeButton.addEventListener("click", (event) => {
      event.stopPropagation()
      void revokeReviewerSessions({ reviewerId, sessionId, deviceId })
    })
    actionRow.appendChild(revokeButton)
    actions.appendChild(actionRow)
    tr.appendChild(actions)
    bindInteractiveRow(tr, () => {
      const sessionNode = byId("reviewerSessionId")
      if (sessionNode) {
        sessionNode.value = sessionId
      }
      const deviceNode = byId("reviewerSessionDeviceId")
      if (deviceNode && deviceId) {
        deviceNode.value = deviceId
      }
    })
    tbody.appendChild(tr)
  })
}

async function createReviewerInvite() {
  const a = actor()
  const ttlSeconds = readIntegerField("reviewerInviteTtlSeconds", 3600, 60)
  setReviewerLifecycleState(
    "reviewerInviteState",
    "warning",
    "reviewer.lifecycle.invites.loading",
    "Creating reviewer invite...",
  )
  const response = await api("/api/reviewer/invites", {
    method: "POST",
    body: {
      role: a.role,
      admin_id: a.admin_id,
      expires_in_seconds: ttlSeconds,
    },
  })
  render("reviewer_invite_create", response)
  if (!response.data || !response.data.ok) {
    setReviewerLifecycleState(
      "reviewerInviteState",
      "danger",
      "reviewer.lifecycle.invites.error",
      "Failed to create reviewer invite.",
    )
    return response
  }
  await listReviewerInvites()
  const payload = apiData(response)
  setReviewerLifecycleState(
    "reviewerInviteState",
    "success",
    "reviewer.lifecycle.invites.created",
    "Invite created. Code: {invite_code}",
    { invite_code: String(payload.invite_code || "").trim() },
  )
  return response
}

async function listReviewerInvites() {
  const a = actor()
  const status = readTextField("reviewerInviteStatusFilter")
  setReviewerLifecycleState(
    "reviewerInviteState",
    "warning",
    "reviewer.lifecycle.invites.loading",
    "Loading reviewer invites...",
  )
  const response = await api(`/api/reviewer/invites${queryString({ role: a.role, status })}`)
  render("reviewer_invite_list", response)
  if (!response.data || !response.data.ok) {
    updateReviewerInviteTable([])
    setReviewerLifecycleState(
      "reviewerInviteState",
      "danger",
      "reviewer.lifecycle.invites.error",
      "Failed to load reviewer invites.",
    )
    return response
  }
  const invites = Array.isArray(apiData(response).invites) ? apiData(response).invites : []
  updateReviewerInviteTable(invites)
  setReviewerLifecycleState(
    "reviewerInviteState",
    invites.length ? "success" : "neutral",
    invites.length ? "reviewer.lifecycle.invites.loaded" : "reviewer.lifecycle.invites.empty",
    invites.length ? "Loaded {count} reviewer invites." : "No reviewer invites matched the current filter.",
    { count: invites.length },
  )
  return response
}

async function revokeReviewerInvite(inviteCode) {
  const a = actor()
  setReviewerLifecycleState(
    "reviewerInviteState",
    "warning",
    "reviewer.lifecycle.invites.revoking",
    "Revoking reviewer invite...",
  )
  const response = await api("/api/reviewer/invites/revoke", {
    method: "POST",
    body: {
      role: a.role,
      admin_id: a.admin_id,
      invite_code: String(inviteCode || "").trim(),
    },
  })
  render("reviewer_invite_revoke", response)
  if (!response.data || !response.data.ok) {
    setReviewerLifecycleState(
      "reviewerInviteState",
      "danger",
      "reviewer.lifecycle.invites.revoke_failed",
      "Failed to revoke reviewer invite.",
    )
    return response
  }
  await listReviewerInvites()
  setReviewerLifecycleState(
    "reviewerInviteState",
    "success",
    "reviewer.lifecycle.invites.revoked",
    "Invite revoked: {invite_code}",
    { invite_code: String(inviteCode || "").trim() },
  )
  return response
}

async function listReviewerAccounts() {
  const a = actor()
  setReviewerLifecycleState(
    "reviewerAccountState",
    "warning",
    "reviewer.lifecycle.accounts.loading",
    "Loading reviewer accounts...",
  )
  const response = await api(`/api/reviewer/accounts${queryString({ role: a.role })}`)
  render("reviewer_account_list", response)
  if (!response.data || !response.data.ok) {
    updateReviewerAccountTable([])
    setReviewerLifecycleState(
      "reviewerAccountState",
      "danger",
      "reviewer.lifecycle.accounts.error",
      "Failed to load reviewer accounts.",
    )
    return response
  }
  const data = apiData(response)
  const reviewers = Array.isArray(data.reviewers) ? data.reviewers : []
  state.reviewerLifecycle.maxDevices = Number(data.max_devices || 0) || state.reviewerLifecycle.maxDevices
  updateReviewerAccountTable(reviewers)
  renderReviewerLifecycleAuthState()
  setReviewerLifecycleState(
    "reviewerAccountState",
    reviewers.length ? "success" : "neutral",
    reviewers.length ? "reviewer.lifecycle.accounts.loaded" : "reviewer.lifecycle.accounts.empty",
    reviewers.length ? "Loaded {count} reviewer accounts." : "No reviewer accounts have redeemed invites yet.",
    { count: reviewers.length },
  )
  return response
}

async function listReviewerDevices(options = {}) {
  const a = actor()
  const reviewerId = String(options.reviewerId || reviewerLifecycleSelectedReviewerId()).trim()
  if (!reviewerId) {
    setReviewerLifecycleState(
      "reviewerDeviceState",
      "danger",
      "reviewer.lifecycle.devices.target_required",
      "Reviewer ID is required before loading devices.",
    )
    return buildClientErrorResponse("reviewer_id_required", "reviewer_id is required", 400)
  }
  setReviewerLifecycleSelectedReviewer(reviewerId)
  setReviewerLifecycleState(
    "reviewerDeviceState",
    "warning",
    "reviewer.lifecycle.devices.loading",
    "Loading reviewer devices...",
  )
  const response = await api(`/api/reviewer/devices${queryString({ role: a.role, reviewer_id: reviewerId })}`)
  render("reviewer_device_list", response)
  if (!response.data || !response.data.ok) {
    updateReviewerDeviceTable([])
    setReviewerLifecycleState(
      "reviewerDeviceState",
      "danger",
      "reviewer.lifecycle.devices.error",
      "Failed to load reviewer devices.",
    )
    return response
  }
  const data = apiData(response)
  const devices = Array.isArray(data.devices) ? data.devices : []
  state.reviewerLifecycle.maxDevices = Number(data.max_devices || 0) || state.reviewerLifecycle.maxDevices
  updateReviewerDeviceTable(devices)
  renderReviewerLifecycleAuthState()
  setReviewerLifecycleState(
    "reviewerDeviceState",
    devices.length ? "success" : "neutral",
    devices.length ? "reviewer.lifecycle.devices.loaded" : "reviewer.lifecycle.devices.empty",
    devices.length ? "Loaded {count} devices for {reviewer_id}." : "No active devices for {reviewer_id}.",
    { count: devices.length, reviewer_id: reviewerId },
  )
  return response
}

async function listReviewerSessions(options = {}) {
  const a = actor()
  const reviewerId = String(options.reviewerId || reviewerLifecycleSelectedReviewerId()).trim()
  const deviceId = String(options.deviceId !== undefined ? options.deviceId : readTextField("reviewerSessionDeviceId")).trim()
  if (!reviewerId) {
    setReviewerLifecycleState(
      "reviewerSessionState",
      "danger",
      "reviewer.lifecycle.sessions.target_required",
      "Reviewer ID is required before listing sessions.",
    )
    return buildClientErrorResponse("reviewer_id_required", "reviewer_id is required", 400)
  }
  setReviewerLifecycleSelectedReviewer(reviewerId)
  setReviewerLifecycleState(
    "reviewerSessionState",
    "warning",
    "reviewer.lifecycle.sessions.loading",
    "Loading reviewer sessions...",
  )
  const response = await api(
    `/api/admin/reviewer/sessions${queryString({ role: a.role, reviewer_id: reviewerId, device_id: deviceId })}`,
  )
  render("reviewer_session_list", response)
  if (!response.data || !response.data.ok) {
    updateReviewerSessionTable([])
    setReviewerLifecycleState(
      "reviewerSessionState",
      "danger",
      "reviewer.lifecycle.sessions.load_failed",
      "Failed to load reviewer sessions.",
    )
    return response
  }
  const sessions = Array.isArray(apiData(response).sessions) ? apiData(response).sessions : []
  updateReviewerSessionTable(sessions)
  setReviewerLifecycleState(
    "reviewerSessionState",
    sessions.length ? "success" : "neutral",
    sessions.length ? "reviewer.lifecycle.sessions.loaded" : "reviewer.lifecycle.sessions.empty",
    sessions.length
      ? "Loaded {count} sessions for {reviewer_id}."
      : "No active reviewer sessions matched the current filter.",
    {
      count: sessions.length,
      reviewer_id: reviewerId,
    },
  )
  return response
}

async function revokeReviewerDevice(deviceId) {
  const a = actor()
  const reviewerId = reviewerLifecycleSelectedReviewerId()
  if (!reviewerId) {
    setReviewerLifecycleState(
      "reviewerDeviceState",
      "danger",
      "reviewer.lifecycle.devices.target_required",
      "Reviewer ID is required before revoking devices.",
    )
    return buildClientErrorResponse("reviewer_id_required", "reviewer_id is required", 400)
  }
  setReviewerLifecycleState(
    "reviewerDeviceState",
    "warning",
    "reviewer.lifecycle.devices.revoking",
    "Revoking reviewer device...",
  )
  const response = await api(
    `/api/reviewer/devices/${encodeURIComponent(String(deviceId || "").trim())}${queryString({ role: a.role, reviewer_id: reviewerId })}`,
    {
      method: "DELETE",
    },
  )
  render("reviewer_device_revoke", response)
  if (!response.data || !response.data.ok) {
    setReviewerLifecycleState(
      "reviewerDeviceState",
      "danger",
      "reviewer.lifecycle.devices.revoke_failed",
      "Failed to revoke reviewer device.",
    )
    return response
  }
  await listReviewerDevices({ reviewerId })
  setReviewerLifecycleState(
    "reviewerDeviceState",
    "success",
    "reviewer.lifecycle.devices.revoked",
    "Revoked device {device_id} for {reviewer_id}.",
    { device_id: String(deviceId || "").trim(), reviewer_id: reviewerId },
  )
  return response
}

async function resetReviewerDevices() {
  const a = actor()
  const reviewerId = reviewerLifecycleSelectedReviewerId()
  if (!reviewerId) {
    setReviewerLifecycleState(
      "reviewerDeviceState",
      "danger",
      "reviewer.lifecycle.devices.target_required",
      "Reviewer ID is required before resetting devices.",
    )
    return buildClientErrorResponse("reviewer_id_required", "reviewer_id is required", 400)
  }
  setReviewerLifecycleState(
    "reviewerDeviceState",
    "warning",
    "reviewer.lifecycle.devices.resetting",
    "Resetting reviewer devices...",
  )
  const response = await api("/api/reviewer/accounts/reset-devices", {
    method: "POST",
    body: {
      role: a.role,
      admin_id: a.admin_id,
      reviewer_id: reviewerId,
    },
  })
  render("reviewer_device_reset", response)
  if (!response.data || !response.data.ok) {
    setReviewerLifecycleState(
      "reviewerDeviceState",
      "danger",
      "reviewer.lifecycle.devices.reset_failed",
      "Failed to reset reviewer devices.",
    )
    return response
  }
  await listReviewerAccounts()
  await listReviewerDevices({ reviewerId })
  const payload = apiData(response)
  setReviewerLifecycleState(
    "reviewerDeviceState",
    "success",
    "reviewer.lifecycle.devices.reset",
    "Reset {count} devices for {reviewer_id}.",
    {
      count: Number(payload.revoked_devices || 0),
      reviewer_id: reviewerId,
    },
  )
  return response
}

async function revokeReviewerSessions(options = {}) {
  const a = actor()
  const reviewerId = String(options.reviewerId || reviewerLifecycleSelectedReviewerId()).trim()
  const deviceId = String(options.deviceId !== undefined ? options.deviceId : readTextField("reviewerSessionDeviceId")).trim()
  const sessionId = String(options.sessionId !== undefined ? options.sessionId : readTextField("reviewerSessionId")).trim()
  if (!reviewerId) {
    setReviewerLifecycleState(
      "reviewerSessionState",
      "danger",
      "reviewer.lifecycle.sessions.target_required",
      "Reviewer ID is required before revoking sessions.",
    )
    return buildClientErrorResponse("reviewer_id_required", "reviewer_id is required", 400)
  }
  setReviewerLifecycleSelectedReviewer(reviewerId)
  setReviewerLifecycleState(
    "reviewerSessionState",
    "warning",
    "reviewer.lifecycle.sessions.revoking",
    "Revoking reviewer sessions...",
  )
  const response = await api("/api/admin/reviewer/sessions/revoke", {
    method: "POST",
    body: {
      role: a.role,
      admin_id: a.admin_id,
      reviewer_id: reviewerId,
      device_id: deviceId,
      session_id: sessionId,
    },
  })
  render("reviewer_session_revoke", response)
  if (!response.data || !response.data.ok) {
    setReviewerLifecycleState(
      "reviewerSessionState",
      "danger",
      "reviewer.lifecycle.sessions.revoke_failed",
      "Failed to revoke reviewer sessions.",
    )
    return response
  }
  const data = apiData(response)
  const count = Number(data.revoked_sessions || 0)
  await listReviewerSessions({ reviewerId, deviceId })
  if (count > 0) {
    setReviewerLifecycleState(
      "reviewerSessionState",
      "success",
      sessionId
        ? "reviewer.lifecycle.sessions.revoked_session"
        : deviceId
          ? "reviewer.lifecycle.sessions.revoked_device"
          : "reviewer.lifecycle.sessions.revoked",
      sessionId
        ? "Revoked session {session_id} for {reviewer_id}."
        : deviceId
          ? "Revoked {count} sessions for {reviewer_id} on device {device_id}."
          : "Revoked {count} sessions for {reviewer_id}.",
      {
        count,
        reviewer_id: reviewerId,
        device_id: deviceId,
        session_id: sessionId,
      },
    )
  } else {
    setReviewerLifecycleState(
      "reviewerSessionState",
      "neutral",
      "reviewer.lifecycle.sessions.noop",
      "No active reviewer sessions matched the current filter.",
    )
  }
  return response
}

function updateTemplatesTable(rows) {
  state.templates = Array.isArray(rows) ? rows : []
  const tbody = byId("templatesTable").querySelector("tbody")
  tbody.innerHTML = ""
  state.templates.forEach((item) => {
    const tr = document.createElement("tr")
    const templateId = item.template_id || ""
    tr.dataset.templateId = templateId
    tr.classList.toggle("is-selected", templateId === state.selectedTemplateId)
    tr.appendChild(cell(item.template_id || ""))
    tr.appendChild(cell(item.version || ""))
    tr.appendChild(cell(item.category || "-"))
    tr.appendChild(pillCell("template", "tag", item.tags))
    tr.appendChild(pillCell("template", "risk_level", item.risk_level ? [item.risk_level] : []))
    tr.appendChild(pillCell("template", "review_label", item.review_labels))
    tr.appendChild(pillCell("template", "warning_flag", item.warning_flags))
    tr.appendChild(pillCell("template", "source_channel", item.source_channel ? [item.source_channel] : []))
    tr.appendChild(cell(item.maintainer || "-"))
    tr.appendChild(cell(templateSignalsSummary(item)))
    bindInteractiveRow(tr, async () => {
      await handleTemplateSelection(item)
    })
    tbody.appendChild(tr)
  })
  renderTemplateCards(state.templates)
  renderMarketInsights(state.templates)
  if (state.marketHub.selectedTemplateId && state.marketHub.templateDrawerOpen) {
    renderTemplateDrawer(state.marketHub.selectedTemplateId)
  }
}

function templateSignalsSummary(item) {
  const helper = detailHelpers()
  if (helper && helper.buildTemplateSignalsSummary) {
    return helper.buildTemplateSignalsSummary(item)
  }
  const engagement = item && item.engagement ? item.engagement : {}
  return [
    `trial ${Number(engagement.trial_requests || 0)}`,
    `install ${Number(engagement.installs || 0)}`,
    `prompt ${Number(engagement.prompt_generations || 0)}`,
    `pkg ${Number(engagement.package_generations || 0)}`,
  ].join(" | ")
}

function updateSubmissionsTable(rows) {
  state.submissions = Array.isArray(rows) ? rows : []
  const tbody = byId("submissionsTable").querySelector("tbody")
  tbody.innerHTML = ""
  state.submissions.forEach((item) => {
    const tr = document.createElement("tr")
    const submissionId = item.submission_id || item.id || ""
    tr.dataset.submissionId = submissionId
    tr.classList.toggle("is-selected", submissionId === state.selectedSubmissionId)
    tr.appendChild(cell(item.submission_id || item.id || ""))
    tr.appendChild(cell(item.template_id || ""))
    tr.appendChild(cell(item.status || ""))
    tr.appendChild(pillCell("submission", "risk_level", item.risk_level ? [item.risk_level] : []))
    tr.appendChild(pillCell("submission", "review_label", item.review_labels))
    tr.appendChild(pillCell("submission", "warning_flag", item.warning_flags))
    tr.appendChild(cell(item.review_note || "-"))
    bindInteractiveRow(tr, async () => {
      await handleSubmissionSelection(item)
    })
    tbody.appendChild(tr)
  })
}

function updateProfilePackSubmissionTable(rows) {
  state.profilePack.market.submissions = Array.isArray(rows) ? rows : []
  const tbody = byId("profilePackSubmissionTable").querySelector("tbody")
  tbody.innerHTML = ""
  state.profilePack.market.submissions.forEach((item) => {
    const tr = document.createElement("tr")
    const packLabel = item.pack_type
      ? `${item.pack_id || ""} (${enumLabelValue("pack_type", item.pack_type)})`
      : item.pack_id || ""
    tr.appendChild(cell(item.submission_id || item.id || ""))
    tr.appendChild(cell(packLabel))
    tr.appendChild(cell(enumLabelValue("status", item.status || "unknown")))
    tr.appendChild(pillCell("profile_pack_submission", "risk_level", item.risk_level ? [item.risk_level] : []))
    tr.appendChild(pillCell("profile_pack_submission", "review_label", item.review_labels))
    tr.appendChild(pillCell("profile_pack_submission", "warning_flag", item.warning_flags))
    tr.appendChild(cell(item.review_note || "-"))
    tr.appendChild(profilePackSubmissionActionCell(item))
    bindInteractiveRow(tr, async () => {
      applyProfilePackMarketSubmissionSelection(item)
    })
    tbody.appendChild(tr)
  })
}

function canWithdrawProfilePackSubmission(item) {
  const a = actor()
  return (
    hasCapability("member.profile_pack.submissions.withdraw") &&
    String(a.role || "").trim().toLowerCase() === "member" &&
    String(a.user_id || "").trim() !== "" &&
    String(item && item.user_id || "").trim() === String(a.user_id || "").trim() &&
    String(item && item.status || "").trim().toLowerCase() === "pending"
  )
}

function profilePackSubmissionActionCell(item) {
  const td = document.createElement("td")
  if (!canWithdrawProfilePackSubmission(item)) {
    td.textContent = "-"
    return td
  }
  const button = document.createElement("button")
  button.type = "button"
  button.className = "btn-ghost"
  button.textContent = i18nMessage("button.withdraw_submission", "Withdraw Submission")
  button.addEventListener("click", (event) => {
    event.preventDefault()
    event.stopPropagation()
    void withdrawMemberProfilePackSubmission(item, button)
  })
  td.appendChild(button)
  return td
}

async function withdrawMemberProfilePackSubmission(item, button) {
  const submissionId = String(item && (item.submission_id || item.id) || "").trim()
  if (!submissionId) {
    return buildClientErrorResponse("submission_id_required", "submission_id is required", 400)
  }
  const a = actor()
  if (button) {
    button.disabled = true
    button.setAttribute("aria-busy", "true")
  }
  try {
    const response = await api("/api/member/profile-pack/submissions/withdraw", {
      method: "POST",
      body: {
        user_id: a.user_id,
        submission_id: submissionId,
      },
    })
    render("member_withdraw_profile_pack_submission", response)
    if (workspaceRequestFailed(response)) {
      return response
    }
    const data = apiData(response)
    await listProfilePackMarketSubmissions()
    updateProfilePackMarketPanel(data)
    applyProfilePackMarketSubmissionSelection(data)
    return response
  } finally {
    if (button) {
      button.disabled = false
      button.setAttribute("aria-busy", "false")
    }
  }
}

function updateProfilePackCatalogTable(rows) {
  state.profilePack.market.catalog = Array.isArray(rows) ? rows : []
  const tbody = byId("profilePackCatalogTable").querySelector("tbody")
  tbody.innerHTML = ""
  state.profilePack.market.catalog.forEach((item) => {
    const tr = document.createElement("tr")
    const packLabel = item.pack_type
      ? `${item.pack_id || ""} (${enumLabelValue("pack_type", item.pack_type)})`
      : item.pack_id || ""
    tr.appendChild(cell(packLabel))
    tr.appendChild(cell(item.version || ""))
    tr.appendChild(cell(item.source_submission_id || "-"))
    tr.appendChild(
      cell(
        item.featured
          ? i18nMessage("option.featured_toggle.true", "featured")
          : i18nMessage("option.featured_toggle.false", "normal"),
      ),
    )
    tr.appendChild(pillCell("profile_pack_catalog", "risk_level", item.risk_level ? [item.risk_level] : []))
    tr.appendChild(pillCell("profile_pack_catalog", "review_label", item.review_labels))
    tr.appendChild(pillCell("profile_pack_catalog", "warning_flag", item.warning_flags))
    bindInteractiveRow(tr, async () => {
      applyProfilePackMarketCatalogSelection(item)
    })
    tbody.appendChild(tr)
  })
}

async function listTemplates() {
  const filters = templateListFilters()
  setCollectionStatus("templates", { status: "loading", errorMessage: "" })
  const response = await api(`/api/templates${queryString(filters)}`)
  if (workspaceRequestFailed(response)) {
    setCollectionStatus("templates", {
      status: "error",
      count: state.templates.length,
      errorMessage: errorMessageForCollection("templates", response),
    })
    render("list_templates", response)
    return response
  }
  const rows = response.data && response.data.data ? response.data.data.templates : []
  updateTemplatesTable(rows)
  setCollectionStatus("templates", {
    status: resolveCollectionStatus(rows.length, filters),
    count: rows.length,
    errorMessage: "",
  })
  render("list_templates", response)
  return response
}

async function listSubmissions() {
  const a = actor()
  const filters = submissionListFilters()
  const normalizedRole = String(a.role || "").trim().toLowerCase()
  const useAdminEndpoint = hasCapability("admin.submissions.read") && normalizedRole !== "member"
  const useMemberEndpoint = !useAdminEndpoint && hasCapability("member.submissions.read")
  setCollectionStatus("submissions", { status: "loading", errorMessage: "" })
  if (!useAdminEndpoint && !useMemberEndpoint) {
    const denied = buildClientErrorResponse("permission_denied", "permission denied", 403)
    render("list_submissions", denied)
    setCollectionStatus("submissions", {
      status: "error",
      count: state.submissions.length,
      errorMessage: errorMessageForCollection("submissions", denied),
    })
    return denied
  }
  const endpoint = useAdminEndpoint
    ? `/api/admin/submissions${queryString({ role: a.role, ...filters })}`
    : `/api/member/submissions${queryString({ user_id: a.user_id, ...filters })}`
  const response = await api(endpoint)
  if (workspaceRequestFailed(response)) {
    setCollectionStatus("submissions", {
      status: "error",
      count: state.submissions.length,
      errorMessage: errorMessageForCollection("submissions", response),
    })
    render(useAdminEndpoint ? "admin_list_submissions" : "member_list_submissions", response)
    return response
  }
  const rows = response.data && response.data.data ? response.data.data.submissions : []
  updateSubmissionsTable(rows)
  setCollectionStatus("submissions", {
    status: resolveCollectionStatus(rows.length, filters),
    count: rows.length,
    errorMessage: "",
  })
  render(useAdminEndpoint ? "admin_list_submissions" : "member_list_submissions", response)
  return response
}

async function refreshHealth() {
  const health = await api("/api/health")
  byId("healthLine").textContent = i18nFormat(
    "health.line",
    "health: {status} {url}",
    {
      status: String(health.status || ""),
      url: String((health.data && health.data.webui_url) || ""),
    },
  ).trim()
}

async function initAuth() {
  const auth = await api("/api/auth-info")
  state.authRequired = Boolean(auth.data.auth_required)
  state.allowAnonymousMember = Boolean(auth.data.allow_anonymous_member)
  state.authPromptRequested = false
  state.runtimeFeatures.supportsLocalAstrbotImport = auth.data.supports_local_astrbot_import !== false
  state.runtimeFeatures.allowAnonymousLocalAstrbotImport = Boolean(
    auth.data.allow_anonymous_local_astrbot_import,
  )
  state.availableRoles = Array.isArray(auth.data.available_roles) ? auth.data.available_roles : []
  restoreAdminAuthSession()
  applyAuthOptions(state.availableRoles)
  updateAuthUi()
  await refreshCapabilities({ updateScope: false })
  persistAdminAuthSession()
}

async function login() {
  if (state.pageMode === "reviewer") {
    render("login", {
      status: 403,
      data: {
        ok: false,
        message: "reviewer_route_login_disabled",
        error: {
          code: "reviewer_route_login_disabled",
          message: "Reviewer direct login is disabled on this route.",
        },
      },
    })
    return
  }
  const password = byId("authPassword").value
  const role = byId("authRole").value || "member"
  const reviewerIdNode = byId("authReviewerId")
  const reviewerDeviceKeyNode = byId("authReviewerDeviceKey")
  const body = { role, password }
  if (String(role).toLowerCase() === "reviewer") {
    body.reviewer_id = reviewerIdNode ? String(reviewerIdNode.value || "").trim() : ""
    body.reviewer_device_key = reviewerDeviceKeyNode ? String(reviewerDeviceKeyNode.value || "").trim() : ""
  }
  const res = await api("/api/login", {
    method: "POST",
    body
  })
  if (res.data.ok && res.data.token) {
    state.token = res.data.token
    state.authRole = res.data.role || role
    state.authPromptRequested = true
    state.availableRoles = Array.isArray(res.data.available_roles) ? res.data.available_roles : state.availableRoles
    persistAdminAuthSession()
    applyAuthOptions(state.availableRoles)
    updateAuthUi()
    await refreshCapabilities({ updateScope: false })
    if (byId("memberInstallationsList")) {
      await loadMemberInstallations()
    }
    if (byId("memberImportDraftList")) {
      await loadMemberProfilePackImports()
    }
    if (byId("memberTaskQueueList")) {
      await loadMemberTasks()
    }
  } else {
    persistAdminAuthSession()
  }
  render("login", res)
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

function buildClientErrorResponse(code, message, status = 400, data = {}) {
  return {
    status,
    data: {
      ok: false,
      message,
      data,
      error: {
        code,
        message,
      },
    },
  }
}

function assertUploadFileAllowed(file) {
  if (!file) return
  const size = Number(file.size || 0)
  if (size <= UPLOAD_LIMIT_BYTES) return
  throw new Error("package_too_large")
}

function uploadTooLargeResponse() {
  return buildClientErrorResponse(
    "package_too_large",
    i18nFormat(
      "upload.error.package_too_large",
      "Package exceeds the {limit} limit.",
      { limit: uploadLimitLabel() },
    ),
    413,
    { max_size_bytes: UPLOAD_LIMIT_BYTES },
  )
}

async function selectedPackagePayload() {
  const input = byId("submitPackageFile")
  if (!input || !input.files) {
    return {}
  }
  const file = input.files[0]
  if (!file) {
    return {}
  }
  assertUploadFileAllowed(file)
  return {
    package_name: file.name,
    package_base64: await readFileAsBase64(file)
  }
}

function readInstallOptionsFromForm() {
  const sourcePreferenceNode = byId("installSourcePreference")
  const sourcePreference = sourcePreferenceNode
    ? String(sourcePreferenceNode.value || "auto").trim()
    : "auto"
  return {
    preflight: Boolean(byId("installPreflight") && byId("installPreflight").checked),
    force_reinstall: Boolean(byId("installForceReinstall") && byId("installForceReinstall").checked),
    source_preference: sourcePreference || "auto",
  }
}

function readUploadOptionsFromForm() {
  const helper = profilePackMarketHelpers()
  const input = {
    scanMode: String(byId("uploadScanMode")?.value || "balanced").trim() || "balanced",
    visibility: String(byId("uploadVisibility")?.value || "community").trim() || "community",
    replaceExisting: Boolean(byId("uploadReplaceExisting") && byId("uploadReplaceExisting").checked),
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

function readProfilePackSubmitOptionsFromForm() {
  const helper = profilePackMarketHelpers()
  const input = {
    packType: String(byId("submitPackType")?.value || "bot_profile_pack").trim() || "bot_profile_pack",
    redactionMode: String(byId("submitRedactionMode")?.value || "exclude_secrets").trim() || "exclude_secrets",
    selectedSections: String(byId("submitSelectedSections")?.value || ""),
    replaceExisting: Boolean(byId("submitReplaceExisting") && byId("submitReplaceExisting").checked),
  }
  if (helper && typeof helper.buildSubmitOptions === "function") {
    return helper.buildSubmitOptions(input)
  }
  return {
    pack_type: input.packType,
    redaction_mode: input.redactionMode,
    selected_sections: input.selectedSections
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean),
    replace_existing: Boolean(input.replaceExisting),
  }
}

function memberSearchQuery() {
  return String(state.memberPanel.searchQuery || "").trim().toLowerCase()
}

function filteredMemberInstallations(rows) {
  const items = Array.isArray(rows) ? rows : []
  const query = memberSearchQuery()
  if (!query) return items
  return items.filter((item) => {
    const templateId = String(item.template_id || "").toLowerCase()
    const version = String(item.version || "").toLowerCase()
    const risk = String(item.risk_level || "").toLowerCase()
    const installedAt = String(item.installed_at || "").toLowerCase()
    return (
      templateId.includes(query) ||
      version.includes(query) ||
      risk.includes(query) ||
      installedAt.includes(query)
    )
  })
}

function setMemberInstallationsState(status, message) {
  const node = byId("memberInstallationsState")
  if (!node) return
  node.classList.remove("is-neutral", "is-warning", "is-danger", "is-success")
  if (status === "loading" || status === "warning") node.classList.add("is-warning")
  else if (status === "error") node.classList.add("is-danger")
  else if (status === "success") node.classList.add("is-success")
  else node.classList.add("is-neutral")
  node.textContent = message
}

function appendMemberCollectionLabel(container, key, fallback) {
  if (!container) return
  const label = document.createElement("div")
  label.className = "member-install-group-label note"
  label.textContent = i18nMessage(key, fallback)
  container.appendChild(label)
}

function buildMemberImportDraftCard(item, options = {}) {
  const importId = String(item.import_id || "").trim()
  const packId = String(item.pack_id || "").trim() || String(item.filename || "").trim() || "-"
  const version = String(item.version || "").trim() || "-"
  const packType = enumLabelValue("pack_type", String(item.pack_type || "unknown").trim() || "unknown")
  const compatibility = enumLabelValue("compatibility", String(item.compatibility || "unknown").trim() || "unknown")
  const row = document.createElement("article")
  row.className = "member-install-item member-import-item"
  if (Boolean(options.selected) && importId && importId === String(state.memberPanel.selectedImportDraftId || "").trim()) {
    row.classList.add("is-selected")
  }
  row.tabIndex = 0
  row.setAttribute("role", "button")
  row.addEventListener("click", () => {
    openMemberProfilePackUploadModalById(importId)
  })
  row.addEventListener("keydown", (event) => {
    if (event.key !== "Enter" && event.key !== " ") return
    event.preventDefault()
    openMemberProfilePackUploadModalById(importId)
  })

  const body = document.createElement("div")
  body.className = "member-install-item-body"
  const title = document.createElement("strong")
  title.textContent = packId
  body.appendChild(title)
  const meta = document.createElement("span")
  meta.textContent = i18nFormat(
    "member.imports.meta",
    "v{version} · {pack_type} · {compatibility}",
    {
      version,
      pack_type: packType,
      compatibility,
    },
  )
  body.appendChild(meta)
  const note = document.createElement("span")
  note.className = "member-import-item-note"
  note.textContent = String(item.filename || "").trim() || "-"
  body.appendChild(note)
  const summaryText = memberImportSummaryText(item)
  if (summaryText) {
    const summaryNote = document.createElement("span")
    summaryNote.className = "member-import-item-note"
    summaryNote.textContent = summaryText
    body.appendChild(summaryNote)
  }
  const issueSummary = memberImportIssueSummary(item.compatibility_issues, 2)
  if (issueSummary) {
    const issueNote = document.createElement("span")
    issueNote.className = "member-import-item-note member-import-item-note-warning"
    issueNote.textContent = i18nFormat(
      "member.imports.issue_summary",
      "Review notes: {summary}",
      { summary: issueSummary },
    )
    body.appendChild(issueNote)
  }
  row.appendChild(body)

  const actions = document.createElement("div")
  actions.className = "member-install-actions"
  const submitButton = document.createElement("button")
  submitButton.type = "button"
  submitButton.className = "btn-ghost member-install-action"
  submitButton.textContent = i18nMessage("member.imports.open_upload_detail", "Open Upload Details")
  submitButton.disabled = false
  submitButton.addEventListener("click", (event) => {
    event.stopPropagation()
    openMemberProfilePackUploadModalById(importId)
  })
  actions.appendChild(submitButton)
  const deleteButton = document.createElement("button")
  deleteButton.type = "button"
  deleteButton.className = "btn-ghost member-install-action"
  deleteButton.textContent = i18nMessage("button.delete_import_draft", "Delete Draft")
  deleteButton.disabled = item.delete_allowed === false
  if (deleteButton.disabled) {
    deleteButton.title = i18nMessage(
      "member.imports.delete_blocked",
      "This draft is already referenced by a submission and cannot be deleted.",
    )
  }
  deleteButton.addEventListener("click", (event) => {
    event.stopPropagation()
    void deleteMemberImportDraft(importId)
  })
  actions.appendChild(deleteButton)
  row.appendChild(actions)
  return row
}

function openMemberInstallation(item) {
  const templateId = String(item && item.template_id || "").trim()
  if (templateId) {
    applyFieldPatches({
      trialTemplateId: templateId,
      submitTemplateId: templateId,
      templateFilterId: templateId,
    })
  }
  void loadTemplateDetail({ templateId, syncRoute: false })
}

function setMemberInstallationActionBusy(button, busy) {
  if (!button) return
  button.disabled = Boolean(busy)
  button.setAttribute("aria-busy", busy ? "true" : "false")
}

async function reinstallMemberInstallation(item, button) {
  const templateId = String(item && item.template_id || "").trim()
  if (!templateId) return
  const a = actor()
  setMemberInstallationActionBusy(button, true)
  const installOptions = item && typeof item.install_options === "object"
    ? { ...item.install_options, force_reinstall: true }
    : { force_reinstall: true }
  const response = await api("/api/templates/install", {
    method: "POST",
    body: {
      ...a,
      template_id: templateId,
      install_options: installOptions,
    },
  })
  render("install", response)
  await loadMemberInstallations()
  setMemberInstallationActionBusy(button, false)
}

async function uninstallMemberInstallation(item, button) {
  const templateId = String(item && item.template_id || "").trim()
  if (!templateId) return
  const a = actor()
  setMemberInstallationActionBusy(button, true)
  const response = await api("/api/member/installations/uninstall", {
    method: "POST",
    body: {
      user_id: a.user_id,
      template_id: templateId,
    },
  })
  render("member_installations_uninstall", response)
  await loadMemberInstallations()
  setMemberInstallationActionBusy(button, false)
}

function renderMemberInstallations(rows) {
  const container = byId("memberInstallationsList")
  if (!container) return
  container.innerHTML = ""
  const importItems = filteredMemberImportDrafts(state.memberPanel.importDrafts)
  const items = filteredMemberInstallations(rows)
  if (!importItems.length && !items.length) {
    container.textContent = memberSearchQuery()
      ? i18nMessage("member.installations.empty_filtered", "No local installations or imported config packs matched the current search.")
      : i18nMessage("member.installations.empty", "No local installations or imported config packs yet.")
    return
  }
  if (importItems.length) {
    appendMemberCollectionLabel(
      container,
      "member.installations.imported_heading",
      "Imported Config Drafts",
    )
    importItems.forEach((item) => {
      container.appendChild(buildMemberImportDraftCard(item, { selected: true }))
    })
  }
  if (importItems.length && items.length) {
    appendMemberCollectionLabel(
      container,
      "member.installations.current_heading",
      "Installed Configs",
    )
  }
  items.forEach((item) => {
    const templateId = String(item.template_id || "").trim()
    const version = String(item.version || "").trim()
    const risk = String(item.risk_level || "unknown").trim()
    const installedAt = String(item.installed_at || "").trim()
    const row = document.createElement("article")
    row.className = "member-install-item"
    row.tabIndex = 0
    row.setAttribute("role", "button")
    row.addEventListener("click", () => {
      openMemberInstallation(item)
    })
    row.addEventListener("keydown", (event) => {
      if (event.key !== "Enter" && event.key !== " ") return
      event.preventDefault()
      openMemberInstallation(item)
    })

    const body = document.createElement("div")
    body.className = "member-install-item-body"
    const title = document.createElement("strong")
    title.textContent = templateId || "-"
    body.appendChild(title)
    const meta = document.createElement("span")
    meta.textContent = i18nFormat(
      "member.installations.meta",
      "v{version} · {risk} · {installed_at}",
      {
        version: version || "-",
        risk: enumLabelValue("risk", risk || "unknown"),
        installed_at: installedAt || "-",
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
      void reinstallMemberInstallation(item, reinstallButton)
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
      void uninstallMemberInstallation(item, uninstallButton)
    })
    actions.appendChild(uninstallButton)

    row.appendChild(actions)
    container.appendChild(row)
  })
}

function filteredMemberImportDrafts(rows) {
  const items = Array.isArray(rows) ? rows : []
  const query = memberSearchQuery()
  if (!query) return items
  return items.filter((item) => {
    const packId = String(item.pack_id || "").toLowerCase()
    const version = String(item.version || "").toLowerCase()
    const filename = String(item.filename || "").toLowerCase()
    const compatibility = String(item.compatibility || "").toLowerCase()
    const packType = String(item.pack_type || "").toLowerCase()
    return (
      packId.includes(query) ||
      version.includes(query) ||
      filename.includes(query) ||
      compatibility.includes(query) ||
      packType.includes(query)
    )
  })
}

function setMemberImportDraftState(status, message) {
  const node = byId("memberImportDraftState")
  if (!node) return
  node.classList.remove("is-neutral", "is-warning", "is-danger", "is-success")
  if (status === "loading" || status === "warning") node.classList.add("is-warning")
  else if (status === "error") node.classList.add("is-danger")
  else if (status === "success") node.classList.add("is-success")
  else node.classList.add("is-neutral")
  node.textContent = message
}

function syncMemberImportReviewTrigger() {
  const button = byId("btnOpenMemberImportReview")
  if (!button) return
  const count = Array.isArray(state.memberPanel.importDrafts) ? state.memberPanel.importDrafts.length : 0
  const visible = count > 0 && hasCapability("member.profile_pack.imports.read")
  button.classList.toggle("hidden", !visible)
  button.disabled = !visible
  button.textContent = visible
    ? i18nFormat(
        "button.review_imported_configs_with_count",
        "Review Imported Config Packs ({count})",
        { count },
      )
    : i18nMessage("button.review_imported_configs", "Review Imported Config Packs")
}

function syncMemberLocalImportEntrySurface() {
  const importButton = byId("btnImportAstrbotConfig")
  const hintNode = byId("memberLocalImportFeatureHint")
  if (!importButton) return
  const supported = state.runtimeFeatures.supportsLocalAstrbotImport !== false
  importButton.classList.toggle("hidden", !supported)
  if (!supported) {
    importButton.disabled = true
    importButton.setAttribute("aria-disabled", "true")
    if (hintNode) {
      hintNode.hidden = false
      hintNode.classList.remove("hidden")
      hintNode.textContent = i18nMessage(
        "member.imports.local_feature_disabled",
        "Local AstrBot import is disabled by deployment policy.",
      )
    }
    return
  }
  importButton.disabled = false
  importButton.removeAttribute("aria-disabled")
  if (hintNode) {
    hintNode.hidden = true
    hintNode.classList.add("hidden")
  }
}

function selectedMemberImportDraft() {
  const selectedId = String(state.memberPanel.selectedImportDraftId || "").trim()
  if (!selectedId) return null
  return state.memberPanel.importDrafts.find(
    (item) => String(item && item.import_id || "").trim() === selectedId,
  ) || null
}

function memberProfilePackUploadModalNode() {
  return byId("memberProfilePackUploadModal")
}

function setMemberProfilePackUploadState(status, message) {
  const node = byId("memberProfilePackUploadState")
  if (!node) return
  node.classList.remove("is-neutral", "is-warning", "is-danger", "is-success")
  if (status === "loading" || status === "warning") node.classList.add("is-warning")
  else if (status === "error") node.classList.add("is-danger")
  else if (status === "success") node.classList.add("is-success")
  else node.classList.add("is-neutral")
  node.textContent = message
}

function appendMemberImportDetailCard(container, label, value) {
  if (!container) return
  const card = document.createElement("div")
  card.className = "detail-card"
  const labelNode = document.createElement("div")
  labelNode.className = "detail-card-label"
  labelNode.textContent = String(label || "")
  card.appendChild(labelNode)
  const valueNode = document.createElement("div")
  valueNode.className = "detail-card-value"
  valueNode.textContent = String(value || "-")
  card.appendChild(valueNode)
  container.appendChild(card)
}

function fallbackMemberUploadSelectionTree(item) {
  const sections = Array.isArray(item && item.sections) ? item.sections : []
  return sections.map((sectionName) => ({
    name: String(sectionName || "").trim(),
    path: String(sectionName || "").trim(),
    items: [],
  }))
}

function normalizeMemberUploadSelectionNode(rawNode, fallbackSectionName = "") {
  const node = rawNode && typeof rawNode === "object" ? rawNode : {}
  const sectionName = String(node.name || fallbackSectionName || "").trim()
  const path = String(node.path || sectionName || "").trim()
  if (!path) return null
  const childRows = Array.isArray(node.items) ? node.items : Array.isArray(node.children) ? node.children : []
  const children = childRows
    .map((child) => normalizeMemberUploadSelectionNode(child, sectionName))
    .filter(Boolean)
  return {
    name: sectionName || String(path.split(".", 1)[0] || "").trim(),
    path,
    label: String(node.label || node.title || sectionName || path).trim() || path,
    kind: String(node.kind || "").trim() || (children.length ? "object" : "scalar"),
    previewLines: Array.isArray(node.preview_lines)
      ? node.preview_lines.map((item) => String(item || "")).filter((item) => item.trim())
      : [],
    previewTruncated: Boolean(node.preview_truncated),
    children,
    checked: true,
    indeterminate: false,
    expanded: false,
  }
}

function buildMemberUploadSelectionState(item) {
  const rawTree = Array.isArray(item && item.selection_tree) && item.selection_tree.length
    ? item.selection_tree
    : fallbackMemberUploadSelectionTree(item)
  return rawTree
    .map((node) => normalizeMemberUploadSelectionNode(node))
    .filter(Boolean)
}

function setMemberUploadSelectionNodeChecked(node, checked) {
  if (!node || typeof node !== "object") return
  node.checked = Boolean(checked)
  node.indeterminate = false
  const children = Array.isArray(node.children) ? node.children : []
  children.forEach((child) => setMemberUploadSelectionNodeChecked(child, checked))
}

function syncMemberUploadSelectionNodeState(node) {
  if (!node || typeof node !== "object") return
  const children = Array.isArray(node.children) ? node.children : []
  if (!children.length) return
  children.forEach((child) => syncMemberUploadSelectionNodeState(child))
  const allChecked = children.every((child) => Boolean(child.checked) && !child.indeterminate)
  const anyChecked = children.some((child) => Boolean(child.checked) || child.indeterminate)
  node.checked = anyChecked
  node.indeterminate = anyChecked && !allChecked
}

function updateMemberUploadSelectionNode(nodes, path, checked) {
  const rows = Array.isArray(nodes) ? nodes : []
  for (const node of rows) {
    if (!node || typeof node !== "object") continue
    if (node.path === path) {
      setMemberUploadSelectionNodeChecked(node, checked)
      return true
    }
    if (updateMemberUploadSelectionNode(node.children, path, checked)) {
      syncMemberUploadSelectionNodeState(node)
      return true
    }
  }
  return false
}

function memberUploadPathCovers(parentPath, targetPath) {
  const parent = String(parentPath || "").trim()
  const target = String(targetPath || "").trim()
  if (!parent || !target) return false
  return (
    target === parent ||
    target.startsWith(`${parent}.`) ||
    target.startsWith(`${parent}[`)
  )
}

function findMemberUploadSelectionNode(nodes, path) {
  const rows = Array.isArray(nodes) ? nodes : []
  const target = String(path || "").trim()
  if (!target) return null
  for (const node of rows) {
    if (!node || typeof node !== "object") continue
    if (node.path === target) return node
    const nested = findMemberUploadSelectionNode(node.children, target)
    if (nested) return nested
  }
  return null
}

function expandMemberUploadSelectionAncestors(nodes, path) {
  const rows = Array.isArray(nodes) ? nodes : []
  const target = String(path || "").trim()
  if (!target) return
  rows.forEach((node) => {
    if (!node || typeof node !== "object") return
    if (!memberUploadPathCovers(node.path, target)) return
    if (Array.isArray(node.children) && node.children.length) {
      node.expanded = true
      expandMemberUploadSelectionAncestors(node.children, target)
    }
  })
}

function selectedMemberUploadSelectionNode() {
  const tree = Array.isArray(state.memberPanel.uploadSelectionTree) ? state.memberPanel.uploadSelectionTree : []
  const current = findMemberUploadSelectionNode(tree, state.memberPanel.uploadSelectedNodePath)
  if (current) return current
  const fallback = tree[0] || null
  state.memberPanel.uploadSelectedNodePath = fallback ? fallback.path : ""
  return fallback
}

function selectMemberUploadSelectionNode(path) {
  const tree = Array.isArray(state.memberPanel.uploadSelectionTree) ? state.memberPanel.uploadSelectionTree : []
  const target = findMemberUploadSelectionNode(tree, path)
  if (!target) return
  state.memberPanel.uploadSelectedNodePath = target.path
  expandMemberUploadSelectionAncestors(tree, target.path)
}

function toggleMemberUploadSelectionNodeExpanded(path) {
  const tree = Array.isArray(state.memberPanel.uploadSelectionTree) ? state.memberPanel.uploadSelectionTree : []
  const target = findMemberUploadSelectionNode(tree, path)
  if (!target || !Array.isArray(target.children) || !target.children.length) return
  target.expanded = !target.expanded
}

function memberUploadSelectionSectionMeta(sectionName) {
  const guidance = profilePackGuidanceHelpers()
  const normalized = String(sectionName || "").trim()
  if (!guidance || !guidance.describeSection) return null
  return guidance.describeSection(normalized)
}

function memberUploadSelectionNodeLabel(node) {
  const path = String(node && node.path || "").trim()
  const fallback = String(node && node.label || path || "Item").trim() || "Item"
  if (path === "personas.runtime") {
    return i18nMessage("member.upload_detail.node.personas_runtime", fallback)
  }
  if (path === "personas.entries") {
    return i18nMessage("member.upload_detail.node.personas_entries", fallback)
  }
  if (path === "environment_manifest.subagent_orchestrator") {
    return i18nMessage("member.upload_detail.node.subagent_orchestrator", fallback)
  }
  if (path === "environment_manifest.platform") {
    return i18nMessage("member.upload_detail.node.platforms", fallback)
  }
  if (path === "environment_manifest.provider_sources") {
    return i18nMessage("member.upload_detail.node.provider_sources", fallback)
  }
  if (path === "astrbot_core.provider_settings") {
    return i18nMessage("member.upload_detail.node.provider_settings", fallback)
  }
  return fallback
}

function memberUploadSelectionStateLabel(node) {
  if (!node || typeof node !== "object") {
    return i18nMessage("member.upload_detail.selection_state_unchecked", "Not selected")
  }
  if (node.indeterminate) {
    return i18nMessage("member.upload_detail.selection_state_partial", "Partially selected")
  }
  if (node.checked) {
    return i18nMessage("member.upload_detail.selection_state_checked", "Selected")
  }
  return i18nMessage("member.upload_detail.selection_state_unchecked", "Not selected")
}

function memberUploadSelectionKindLabel(node) {
  const kind = String(node && node.kind || "scalar").trim() || "scalar"
  return i18nMessage(`member.upload_detail.kind.${kind}`, kind)
}

function memberUploadSelectionPreviewText(node) {
  const lines = Array.isArray(node && node.previewLines) ? node.previewLines : []
  if (!lines.length) {
    return i18nMessage(
      "member.upload_detail.preview_empty",
      "No preview content is available for the current node.",
    )
  }
  let text = lines.join("\n")
  if (node && node.previewTruncated) {
    text += `\n\n${i18nMessage("member.upload_detail.preview_truncated", "Preview truncated.")}`
  }
  return text
}

function memberUploadSelectionPreviewSnippet(node) {
  const lines = Array.isArray(node && node.previewLines) ? node.previewLines : []
  const normalized = lines
    .map((line) => String(line || "").trim())
    .filter(Boolean)
    .filter((line) => !["{", "}", "[", "]"].includes(line))
  const source = normalized[0] || String(lines[0] || "").trim()
  if (!source) return ""
  const cleaned = source.replace(/^"(.*)"[,]?$/, "$1")
  if (cleaned.length <= 120) return cleaned
  return `${cleaned.slice(0, 117)}...`
}

function renderMemberUploadSelectionNode(node, level, isSectionRoot) {
  const wrapper = document.createElement("div")
  wrapper.className = `member-upload-tree-node member-upload-tree-level-${Math.min(level, 4)}`
  const row = document.createElement("div")
  row.className = "member-upload-tree-row"
  if (String(state.memberPanel.uploadSelectedNodePath || "").trim() === node.path) {
    row.classList.add("is-selected")
  }

  const children = Array.isArray(node.children) ? node.children : []
  if (children.length) {
    const toggle = document.createElement("button")
    toggle.type = "button"
    toggle.className = "member-upload-tree-toggle"
    toggle.setAttribute("aria-label", node.expanded ? "Collapse node" : "Expand node")
    toggle.textContent = node.expanded ? "▾" : "▸"
    toggle.addEventListener("click", () => {
      toggleMemberUploadSelectionNodeExpanded(node.path)
      renderMemberUploadDetailSections()
    })
    row.appendChild(toggle)
  } else {
    const spacer = document.createElement("span")
    spacer.className = "member-upload-tree-spacer"
    spacer.setAttribute("aria-hidden", "true")
    row.appendChild(spacer)
  }

  const input = document.createElement("input")
  input.type = "checkbox"
  input.checked = Boolean(node.checked)
  input.indeterminate = Boolean(node.indeterminate)
  input.setAttribute("data-member-upload-path", node.path)
  if (isSectionRoot) {
    input.setAttribute("data-member-upload-section", node.name)
  }
  input.addEventListener("change", () => {
    updateMemberUploadSelectionNode(state.memberPanel.uploadSelectionTree, node.path, input.checked)
    state.memberPanel.uploadSelectionTree.forEach((sectionNode) => syncMemberUploadSelectionNodeState(sectionNode))
    renderMemberUploadDetailSections()
  })
  row.appendChild(input)

  const button = document.createElement("button")
  button.type = "button"
  button.className = "member-upload-tree-select"
  button.addEventListener("click", () => {
    selectMemberUploadSelectionNode(node.path)
    renderMemberUploadDetailSections()
  })

  const body = document.createElement("span")
  body.className = "profile-pack-section-body"
  const titleRow = document.createElement("span")
  titleRow.className = "profile-pack-section-title-row"

  const title = document.createElement("span")
  title.className = "profile-pack-section-title"
  if (isSectionRoot) {
    const sectionMeta = memberUploadSelectionSectionMeta(node.name)
    title.textContent =
      sectionMeta && sectionMeta.known && sectionMeta.titleKey
        ? i18nMessage(sectionMeta.titleKey, node.label)
        : node.label
    if (sectionMeta && sectionMeta.stateful) {
      appendPill(
        titleRow,
        i18nMessage("profile_pack.section.badge.stateful", "Stateful"),
        "warning",
      )
    }
    if (sectionMeta && sectionMeta.localData) {
      appendPill(
        titleRow,
        i18nMessage("profile_pack.section.badge.local_data", "Local Data"),
        "neutral",
      )
    }
  } else {
    title.textContent = memberUploadSelectionNodeLabel(node)
  }
  titleRow.appendChild(title)
  body.appendChild(titleRow)

  if (isSectionRoot) {
    const sectionMeta = memberUploadSelectionSectionMeta(node.name)
    if (sectionMeta && sectionMeta.known && sectionMeta.descriptionKey) {
      const description = document.createElement("span")
      description.className = "profile-pack-section-description"
      description.textContent = i18nMessage(sectionMeta.descriptionKey, node.name)
      body.appendChild(description)
    }
  } else {
    const pathMeta = document.createElement("span")
    pathMeta.className = "profile-pack-section-description"
    pathMeta.textContent = node.path
    body.appendChild(pathMeta)
  }
  button.appendChild(body)
  row.appendChild(button)
  wrapper.appendChild(row)

  if (children.length && node.expanded) {
    const childContainer = document.createElement("div")
    childContainer.className = "member-upload-tree-children"
    children.forEach((child) => {
      childContainer.appendChild(renderMemberUploadSelectionNode(child, level + 1, false))
    })
    wrapper.appendChild(childContainer)
  }
  return wrapper
}

function renderMemberUploadDetailInspector() {
  const headingNode = byId("memberUploadDetailInspectorHeading")
  const pathNode = byId("memberUploadDetailInspectorPath")
  const summaryNode = byId("memberUploadDetailInspectorSummary")
  const previewNode = byId("memberUploadDetailInspectorPreview")
  const childrenNode = byId("memberUploadDetailInspectorChildren")
  if (!headingNode || !pathNode || !summaryNode || !previewNode || !childrenNode) return
  clearNodeChildren(summaryNode)
  clearNodeChildren(childrenNode)
  const node = selectedMemberUploadSelectionNode()
  if (!node) {
    headingNode.textContent = i18nMessage("member.upload_detail.inspector_title", "Section Inspector")
    pathNode.textContent = i18nMessage(
      "member.upload_detail.inspector_empty",
      "Select a section or item from the left to inspect it here.",
    )
    previewNode.textContent = i18nMessage(
      "member.upload_detail.preview_empty",
      "No preview content is available for the current node.",
    )
    return
  }

  const label = memberUploadSelectionNodeLabel(node)
  headingNode.textContent = label
  pathNode.textContent = i18nFormat(
    "member.upload_detail.path_value",
    "{label}: {path}",
    {
      label: i18nMessage("member.upload_detail.path_label", "Path"),
      path: node.path,
    },
  )
  appendMemberImportDetailCard(
    summaryNode,
    i18nMessage("member.upload_detail.kind_label", "Node Type"),
    memberUploadSelectionKindLabel(node),
  )
  appendMemberImportDetailCard(
    summaryNode,
    i18nMessage("member.upload_detail.child_count_label", "Child Items"),
    String(Array.isArray(node.children) ? node.children.length : 0),
  )
  appendMemberImportDetailCard(
    summaryNode,
    i18nMessage("member.upload_detail.selection_state_label", "Selection"),
    memberUploadSelectionStateLabel(node),
  )
  previewNode.textContent = memberUploadSelectionPreviewText(node)

  const children = Array.isArray(node.children) ? node.children : []
  if (!children.length) {
    const empty = document.createElement("div")
    empty.className = "note"
    empty.textContent = i18nMessage(
      "member.upload_detail.children_empty",
      "This item is already at the finest upload granularity.",
    )
    childrenNode.appendChild(empty)
    return
  }

  children.forEach((child) => {
    const card = document.createElement("article")
    card.className = "member-upload-child-card"
    if (String(state.memberPanel.uploadSelectedNodePath || "").trim() === child.path) {
      card.classList.add("is-selected")
    }

    const head = document.createElement("div")
    head.className = "member-upload-child-head"

    const input = document.createElement("input")
    input.type = "checkbox"
    input.checked = Boolean(child.checked)
    input.indeterminate = Boolean(child.indeterminate)
    input.addEventListener("change", () => {
      updateMemberUploadSelectionNode(state.memberPanel.uploadSelectionTree, child.path, input.checked)
      state.memberPanel.uploadSelectionTree.forEach((sectionNode) => syncMemberUploadSelectionNodeState(sectionNode))
      renderMemberUploadDetailSections()
    })
    head.appendChild(input)

    const open = document.createElement("button")
    open.type = "button"
    open.className = "member-upload-child-open"
    open.addEventListener("click", () => {
      selectMemberUploadSelectionNode(child.path)
      renderMemberUploadDetailSections()
    })

    const title = document.createElement("span")
    title.className = "member-upload-child-title"
    title.textContent = memberUploadSelectionNodeLabel(child)
    open.appendChild(title)

    const meta = document.createElement("span")
    meta.className = "member-upload-child-meta"
    meta.textContent = `${child.path} · ${memberUploadSelectionKindLabel(child)}`
    open.appendChild(meta)
    head.appendChild(open)

    card.appendChild(head)
    const preview = memberUploadSelectionPreviewSnippet(child)
    if (preview) {
      const previewNode = document.createElement("div")
      previewNode.className = "member-upload-child-preview"
      previewNode.textContent = preview
      card.appendChild(previewNode)
    }
    childrenNode.appendChild(card)
  })
}

function renderMemberUploadDetailSections() {
  const container = byId("memberUploadDetailSectionList")
  if (!container) return
  clearNodeChildren(container)
  const tree = Array.isArray(state.memberPanel.uploadSelectionTree) ? state.memberPanel.uploadSelectionTree : []
  if (!tree.length) {
    const empty = document.createElement("div")
    empty.className = "note"
    empty.textContent = i18nMessage(
      "member.upload_detail.sections_empty",
      "No selectable sections are available for this draft.",
    )
    container.appendChild(empty)
    renderMemberUploadDetailInspector()
    return
  }
  selectedMemberUploadSelectionNode()
  tree.forEach((sectionNode) => {
    container.appendChild(renderMemberUploadSelectionNode(sectionNode, 0, true))
  })
  renderMemberUploadDetailInspector()
}

function collectMemberUploadSelectionPaths(node, isSectionRoot) {
  if (!node || !node.checked) return []
  const children = Array.isArray(node.children) ? node.children : []
  if (isSectionRoot) {
    if (!node.indeterminate) return []
    return children.flatMap((child) => collectMemberUploadSelectionPaths(child, false))
  }
  if (!children.length) {
    return [node.path]
  }
  return children.flatMap((child) => collectMemberUploadSelectionPaths(child, false))
}

function readMemberUploadDetailSelection(item) {
  const tree = Array.isArray(state.memberPanel.uploadSelectionTree) ? state.memberPanel.uploadSelectionTree : []
  if (!tree.length) {
    const fallbackSections = Array.isArray(item && item.sections) ? item.sections : []
    return {
      selectedSections: fallbackSections,
      selectedItemPaths: [],
    }
  }
  const selectedSections = []
  const selectedItemPaths = []
  tree.forEach((sectionNode) => {
    if (!sectionNode || !sectionNode.checked) return
    const sectionName = String(sectionNode.name || sectionNode.path || "").trim()
    if (!sectionName) return
    selectedSections.push(sectionName)
    selectedItemPaths.push(...collectMemberUploadSelectionPaths(sectionNode, true))
  })
  return {
    selectedSections,
    selectedItemPaths,
  }
}

function readMemberUploadDetailSections(item) {
  return readMemberUploadDetailSelection(item).selectedSections
}

function syncMemberProfilePackUploadModal() {
  const item = selectedMemberImportDraft()
  const metaNode = byId("memberProfilePackUploadMeta")
  const detailGrid = byId("memberProfilePackUploadDetailGrid")
  const replaceExistingNode = byId("memberUploadDetailReplaceExisting")
  const deleteButton = byId("btnMemberProfilePackUploadDelete")
  const submitButton = byId("btnMemberProfilePackUploadSubmit")
  if (!metaNode || !detailGrid || !replaceExistingNode || !submitButton || !deleteButton) return
  clearNodeChildren(detailGrid)
  if (!item) {
    state.memberPanel.uploadSelectionTree = []
    state.memberPanel.uploadSelectedNodePath = ""
    metaNode.textContent = i18nMessage(
      "member.upload_detail.meta_idle",
      "Select an imported config pack to continue.",
    )
    renderMemberUploadDetailSections()
    replaceExistingNode.checked = false
    deleteButton.disabled = true
    deleteButton.title = ""
    submitButton.disabled = true
    submitButton.title = ""
    setMemberProfilePackUploadState(
      "neutral",
      i18nMessage("member.upload_detail.idle", "Select an imported config pack to continue."),
    )
    return
  }
  const packId = String(item.pack_id || "").trim() || String(item.filename || "").trim() || "-"
  const version = String(item.version || "").trim() || "-"
  const packType = enumLabelValue("pack_type", String(item.pack_type || "unknown").trim() || "unknown")
  const compatibility = enumLabelValue("compatibility", String(item.compatibility || "unknown").trim() || "unknown")
  const sections = Array.isArray(item.sections) ? item.sections : []
  const issues = Array.isArray(item.compatibility_issues) ? item.compatibility_issues : []
  const summary = item && typeof item.import_summary === "object" && item.import_summary
    ? item.import_summary
    : {}
  const issueSummary = memberImportIssueSummary(issues, 3)
  metaNode.textContent = i18nFormat(
    "member.upload_detail.meta",
    "{pack_id} · {pack_type} · {version}",
    {
      pack_id: packId,
      pack_type: packType,
      version,
    },
  )
  appendMemberImportDetailCard(detailGrid, i18nMessage("field.profile_pack_id", "Profile Pack ID"), packId)
  appendMemberImportDetailCard(detailGrid, i18nMessage("field.pack_type", "Pack Type"), packType)
  appendMemberImportDetailCard(detailGrid, i18nMessage("field.version", "Version"), version)
  appendMemberImportDetailCard(detailGrid, i18nMessage("detail.label.import_source", "Import source"), memberImportSourceLabel(item))
  appendMemberImportDetailCard(detailGrid, i18nMessage("detail.label.compatibility", "Compatibility"), compatibility)
  appendMemberImportDetailCard(
    detailGrid,
    i18nMessage("detail.label.compatibility_notes", "Compatibility notes"),
    issueSummary || "-",
  )
  if (String(summary.default_personality || "").trim()) {
    appendMemberImportDetailCard(
      detailGrid,
      i18nMessage("detail.label.default_personality", "Default Persona"),
      String(summary.default_personality || "").trim(),
    )
  }
  if (Number(summary.persona_count || 0) > 0) {
    appendMemberImportDetailCard(
      detailGrid,
      i18nMessage("detail.label.persona_entries", "Persona entries"),
      String(summary.persona_count || 0),
    )
  }
  if (Number(summary.subagent_count || 0) > 0) {
    appendMemberImportDetailCard(
      detailGrid,
      i18nMessage("detail.label.enabled_subagents", "Enabled subagents"),
      String(summary.subagent_count || 0),
    )
  }
  if (Number(summary.platform_count || 0) > 0) {
    appendMemberImportDetailCard(
      detailGrid,
      i18nMessage("detail.label.platforms", "Platforms"),
      String(summary.platform_count || 0),
    )
  }
  appendMemberImportDetailCard(detailGrid, i18nMessage("detail.label.sections", "Sections"), sections.length ? sections.join(", ") : "-")
  appendMemberImportDetailCard(detailGrid, i18nMessage("detail.label.filename", "Filename"), String(item.filename || "").trim() || "-")
  state.memberPanel.uploadSelectionTree = buildMemberUploadSelectionState(item)
  state.memberPanel.uploadSelectedNodePath = String(
    state.memberPanel.uploadSelectionTree[0] && state.memberPanel.uploadSelectionTree[0].path || "",
  ).trim()
  renderMemberUploadDetailSections()
  replaceExistingNode.checked = false
  deleteButton.disabled = item.delete_allowed === false
  deleteButton.title = deleteButton.disabled
    ? i18nMessage(
        "member.imports.delete_blocked",
        "This draft is already referenced by a submission and cannot be deleted.",
      )
    : ""
  setMemberProfilePackUploadState(
    issues.length ? "warning" : "success",
    issues.length
      ? i18nFormat(
          "member.upload_detail.warning_with_issue",
          "Compatibility issues: {count}. First issue: {issue}",
          {
            count: issues.length,
            issue: memberImportIssueSummary(issues, 1),
          },
        )
      : i18nMessage(
          "member.upload_detail.ready",
          "Import is ready for submission.",
        ),
  )
  const allowed = hasCapability("profile_pack.community.submit")
  submitButton.disabled = !allowed
  submitButton.title = allowed ? "" : capabilityLockedHint("profile_pack.community.submit")
}

function openMemberProfilePackUploadModalById(importId) {
  const normalized = String(importId || "").trim()
  const fallbackImportId = normalized || String(state.memberPanel.selectedImportDraftId || "").trim()
  const nextImportId = fallbackImportId || String(state.memberPanel.importDrafts[0] && state.memberPanel.importDrafts[0].import_id || "").trim()
  if (!nextImportId) return
  state.memberPanel.selectedImportDraftId = nextImportId
  renderMemberImportDrafts(state.memberPanel.importDrafts)
  const modal = memberProfilePackUploadModalNode()
  if (!modal) return
  syncMemberProfilePackUploadModal()
  modal.setAttribute("role", "dialog")
  modal.setAttribute("aria-modal", "true")
  modal.classList.remove("hidden")
  modal.setAttribute("aria-hidden", "false")
  activateDialogFocus("memberProfilePackUpload", modal, {
    close: closeMemberProfilePackUploadModal,
    resolveFallbackFocus: () => byId("btnOpenMemberImportReview") || byId("btnImportAstrbotConfig"),
  })
}

function closeMemberProfilePackUploadModal() {
  const modal = memberProfilePackUploadModalNode()
  if (!modal) return
  modal.classList.add("hidden")
  modal.setAttribute("aria-hidden", "true")
  deactivateDialogFocus("memberProfilePackUpload", modal)
}

function renderMemberImportDrafts(rows) {
  const container = byId("memberImportDraftList")
  if (!container) return
  container.innerHTML = ""
  const items = filteredMemberImportDrafts(rows)
  if (!items.length) {
    container.textContent = memberSearchQuery()
      ? i18nMessage("member.imports.empty_filtered", "No imported config packs matched the current search.")
      : i18nMessage("member.imports.empty", "No imported config packs yet.")
    syncMemberImportReviewTrigger()
    return
  }
  items.forEach((item) => {
    container.appendChild(buildMemberImportDraftCard(item, { selected: true }))
  })
  syncMemberImportReviewTrigger()
}

async function loadMemberProfilePackImports(options = {}) {
  const container = byId("memberImportDraftList")
  if (!container) return null
  if (!hasCapability("member.profile_pack.imports.read")) {
    state.memberPanel.importDrafts = []
    state.memberPanel.selectedImportDraftId = ""
    renderMemberImportDrafts([])
    renderMemberInstallations(state.memberPanel.installations)
    setMemberImportDraftState(
      "warning",
      i18nMessage(
        "member.imports.locked",
        "Login is required before importing or managing AstrBot config packs.",
      ),
    )
    syncMemberImportReviewTrigger()
    syncMemberProfilePackUploadModal()
    return buildClientErrorResponse("permission_denied", "permission denied", 403)
  }
  const selectedImportId = String(options.selectedImportId || "").trim()
  setMemberImportDraftState(
    "loading",
    i18nMessage("member.imports.loading", "Loading imported config packs..."),
  )
  const a = actor()
  const response = await api(`/api/member/profile-pack/imports${queryString({
    user_id: a.user_id,
    limit: 50,
  })}`)
  const data = apiData(response)
  const rows = Array.isArray(data.imports) ? data.imports : []
  state.memberPanel.importDrafts = rows
  if (selectedImportId && rows.some((item) => String(item && item.import_id || "").trim() === selectedImportId)) {
    state.memberPanel.selectedImportDraftId = selectedImportId
  } else if (!rows.some((item) => String(item && item.import_id || "").trim() === String(state.memberPanel.selectedImportDraftId || "").trim())) {
    state.memberPanel.selectedImportDraftId = String(rows[0] && rows[0].import_id || "").trim()
  }
  renderMemberImportDrafts(rows)
  renderMemberInstallations(state.memberPanel.installations)
  if (workspaceRequestFailed(response)) {
    setMemberImportDraftState(
      "error",
      i18nFormat("member.imports.error", "Failed to load imported config packs: {message}", {
        message: errorMessageForCollection("profilePackSubmissions", response),
      }),
    )
  } else {
    setMemberImportDraftState(
      rows.length ? "success" : "neutral",
      i18nFormat("member.imports.ready", "Imported config packs: {count}", { count: rows.length }),
    )
  }
  syncMemberImportReviewTrigger()
  syncMemberProfilePackUploadModal()
  return response
}

function promptMemberProfilePackImport() {
  if (!hasCapability("member.profile_pack.imports.package_upload")) return
  const input = byId("memberImportAstrbotConfigFile")
  if (!input) return
  input.value = ""
  input.click()
}

async function importMemberLocalAstrbotConfig() {
  if (!hasCapability("member.profile_pack.imports.local_astrbot")) return null
  const trigger = byId("btnImportAstrbotConfig")
  if (trigger) {
    trigger.disabled = true
    trigger.setAttribute("aria-busy", "true")
  }
  let response = null
  try {
    const a = actor()
    response = await api("/api/member/profile-pack/imports/local-astrbot", {
      method: "POST",
      body: {
        user_id: a.user_id,
      },
    })
    render("member_profile_pack_import_local_astrbot", response)
    if (!workspaceRequestFailed(response)) {
      const data = apiData(response)
      const importId = String(data.import_id || "").trim()
      await loadMemberProfilePackImports({ selectedImportId: importId })
      if (importId) {
        openMemberProfilePackUploadModalById(importId)
      }
      setMemberImportDraftState(
        "success",
        i18nMessage(
          "member.imports.local_import_ready",
          "Local AstrBot config imported. Review upload details before submission.",
        ),
      )
    } else {
      const errorCode = responseErrorCode(response)
      const errorMessage = errorMessageForCollection("profilePackSubmissions", response)
      setMemberImportDraftState(
        "error",
        errorCode === "astrbot_local_config_not_found"
          ? i18nMessage(
              "member.imports.local_import_not_found",
              "No local AstrBot config was detected on this host.",
            )
          : i18nFormat(
              "member.imports.local_import_failed",
              "Failed to import the local AstrBot config: {message}",
              { message: errorMessage },
            ),
      )
    }
  } finally {
    if (trigger) {
      trigger.disabled = false
      trigger.setAttribute("aria-busy", "false")
    }
  }
  return response
}

async function importMemberProfilePackFromSelection() {
  const input = byId("memberImportAstrbotConfigFile")
  const trigger = byId("btnImportConfigPackFile")
  if (!input || !input.files || !input.files[0]) return
  const file = input.files[0]
  if (trigger) {
    trigger.disabled = true
    trigger.setAttribute("aria-busy", "true")
  }
  try {
    assertUploadFileAllowed(file)
  } catch (_error) {
    render("member_profile_pack_import", uploadTooLargeResponse())
    setMemberImportDraftState(
      "error",
      i18nFormat(
        "upload.error.package_too_large",
        "Package exceeds the {limit} limit.",
        { limit: uploadLimitLabel() },
      ),
    )
    if (trigger) {
      trigger.disabled = false
      trigger.setAttribute("aria-busy", "false")
    }
    input.value = ""
    return
  }

  let response = null
  try {
    const a = actor()
    response = await api("/api/member/profile-pack/imports", {
      method: "POST",
      body: {
        user_id: a.user_id,
        filename: String(file.name || "profile-pack.zip"),
        content_base64: await readFileAsBase64(file),
      },
    })
    render("member_profile_pack_import", response)
    if (!workspaceRequestFailed(response)) {
      const data = apiData(response)
      const importId = String(data.import_id || "").trim()
      await loadMemberProfilePackImports({ selectedImportId: importId })
      if (importId) {
        openMemberProfilePackUploadModalById(importId)
      }
    } else if (responseErrorCode(response) === "invalid_profile_pack_payload") {
      setMemberImportDraftState(
        "error",
        i18nMessage(
          "member.imports.invalid_format",
          "Import failed. Accepted inputs are Sharelife standard zip, AstrBot backup zip, cmd_config.json, or abconf_*.json.",
        ),
      )
    } else {
      setMemberImportDraftState(
        "error",
        i18nFormat("member.imports.error", "Failed to load imported config packs: {message}", {
          message: String(
            response && response.data && response.data.error && response.data.error.message || response.status || "request failed",
          ),
        }),
      )
    }
  } finally {
    if (trigger) {
      trigger.disabled = false
      trigger.setAttribute("aria-busy", "false")
    }
    input.value = ""
    updateSelectedFileName(
      "memberImportAstrbotConfigFile",
      "memberUploadFileName",
      "member.upload.file_idle",
      "No file selected. Max 20 MiB. Sharelife standard zip, AstrBot backup zip, cmd_config.json, and abconf_*.json are supported.",
    )
  }
  return response
}

function memberProfilePackSubmitOptionsFromModal(item) {
  const selection = readMemberUploadDetailSelection(item)
  return {
    pack_type: String(item && item.pack_type || "bot_profile_pack").trim() || "bot_profile_pack",
    selected_sections: selection.selectedSections,
    selected_item_paths: selection.selectedItemPaths,
    replace_existing: Boolean(byId("memberUploadDetailReplaceExisting") && byId("memberUploadDetailReplaceExisting").checked),
    source: "member_import",
  }
}

async function submitSelectedMemberImportDraft() {
  const item = selectedMemberImportDraft()
  const button = byId("btnMemberProfilePackUploadSubmit")
  if (!item || !button) return null
  if (!hasCapability("profile_pack.community.submit")) {
    setMemberProfilePackUploadState(
      "warning",
      capabilityLockedHint("profile_pack.community.submit"),
    )
    return buildClientErrorResponse("permission_denied", "permission denied", 403)
  }
  const artifactId = String(item.source_artifact_id || "").trim()
  if (!artifactId) {
    setMemberProfilePackUploadState(
      "error",
      i18nMessage(
        "member.upload_detail.error_missing_artifact",
        "Imported config pack is missing its source artifact.",
      ),
    )
    return buildClientErrorResponse("artifact_id_required", "artifact_id is required", 400)
  }
  const submitOptions = memberProfilePackSubmitOptionsFromModal(item)
  if (!Array.isArray(submitOptions.selected_sections) || !submitOptions.selected_sections.length) {
    setMemberProfilePackUploadState(
      "warning",
      i18nMessage(
        "member.upload_detail.sections_empty",
        "No selectable sections are available for this draft.",
      ),
    )
    return buildClientErrorResponse("invalid_profile_section", "invalid profile section", 400)
  }
  button.disabled = true
  button.setAttribute("aria-busy", "true")
  const a = actor()
  const response = await api("/api/profile-pack/submit", {
    method: "POST",
    body: {
      user_id: a.user_id,
      artifact_id: artifactId,
      submit_options: submitOptions,
    },
  })
  render("member_profile_pack_submit", response)
  if (!workspaceRequestFailed(response)) {
    setMemberProfilePackUploadState(
      "success",
      i18nMessage("member.upload_detail.submitted", "Config pack submitted successfully."),
    )
    closeMemberProfilePackUploadModal()
    if (byId("btnProfilePackListPackSubmissions")) {
      await listProfilePackMarketSubmissions()
    }
  } else {
    setMemberProfilePackUploadState(
      "error",
      i18nFormat("member.upload_detail.error", "Submission failed: {message}", {
        message: errorMessageForCollection("profilePackSubmissions", response),
      }),
    )
  }
  button.disabled = !hasCapability("profile_pack.community.submit")
  button.setAttribute("aria-busy", "false")
  return response
}

async function deleteMemberImportDraft(importId = "") {
  const normalizedImportId = String(importId || "").trim()
  const item = normalizedImportId
    ? state.memberPanel.importDrafts.find((entry) => String(entry && entry.import_id || "").trim() === normalizedImportId) || null
    : selectedMemberImportDraft()
  const button = byId("btnMemberProfilePackUploadDelete")
  if (!item || !button) return null
  if (item.delete_allowed === false) {
    setMemberProfilePackUploadState(
      "warning",
      i18nMessage(
        "member.imports.delete_blocked",
        "This draft is already referenced by a submission and cannot be deleted.",
      ),
    )
    return buildClientErrorResponse("profile_import_in_use", "profile import in use", 409)
  }
  button.disabled = true
  button.setAttribute("aria-busy", "true")
  try {
    const a = actor()
    const response = await api(
      `/api/member/profile-pack/imports/${encodeURIComponent(String(item.import_id || "").trim())}${queryString({ user_id: a.user_id })}`,
      { method: "DELETE" },
    )
    render("member_profile_pack_import_delete", response)
    if (!workspaceRequestFailed(response)) {
      await loadMemberProfilePackImports()
      if (!state.memberPanel.importDrafts.length) {
        closeMemberProfilePackUploadModal()
      } else {
        syncMemberProfilePackUploadModal()
      }
      setMemberImportDraftState(
        "success",
        i18nMessage("member.imports.deleted", "Imported config draft deleted."),
      )
    } else {
      setMemberProfilePackUploadState(
        "error",
        i18nFormat("member.upload_detail.error", "Submission failed: {message}", {
          message: errorMessageForCollection("profilePackSubmissions", response),
        }),
      )
    }
    return response
  } finally {
    button.setAttribute("aria-busy", "false")
    const currentItem = selectedMemberImportDraft()
    button.disabled = !currentItem || currentItem.delete_allowed === false
  }
}

function memberTaskQueueNodes() {
  const queueNode = byId("memberTaskQueueList")
  const stateNode = byId("memberTaskQueueState")
  return { queueNode, stateNode }
}

function memberTaskSortValue(value) {
  const parsed = Date.parse(String(value || ""))
  return Number.isFinite(parsed) ? parsed : 0
}

function memberTaskKey(item) {
  if (!item || typeof item !== "object") return ""
  const taskId = String(item.task_id || item.id || "").trim()
  if (taskId) return `id:${taskId}`
  return [
    String(item.name || "operation").trim(),
    String(item.at || "").trim(),
    String(item.status || "").trim(),
    String(item.message || "").trim(),
  ].join("|")
}

function normalizeMemberTaskEntry(raw) {
  if (!raw || typeof raw !== "object") return null
  const at = String(raw.at || raw.created_at || new Date().toISOString()).trim() || new Date().toISOString()
  const statusText = String(raw.status || "").trim()
  const okRaw = raw.ok
  const ok = typeof okRaw === "boolean"
    ? okRaw
    : !["failed", "error", "conflict", "denied", "rejected"].includes(statusText.toLowerCase())
  return {
    task_id: String(raw.task_id || raw.id || "").trim(),
    name: String(raw.name || raw.action || "operation").trim() || "operation",
    action: String(raw.action || "").trim(),
    ok,
    status: statusText,
    message: String(raw.message || "").trim(),
    at,
  }
}

function mergeMemberTasks(entries, limit = 24) {
  const rows = Array.isArray(entries) ? entries : []
  const out = []
  const seen = new Set()
  rows
    .map((item) => normalizeMemberTaskEntry(item))
    .filter(Boolean)
    .sort((left, right) => memberTaskSortValue(right.at) - memberTaskSortValue(left.at))
    .forEach((item) => {
      const key = memberTaskKey(item)
      if (!key || seen.has(key)) return
      seen.add(key)
      out.push(item)
    })
  return out.slice(0, Math.max(1, Number(limit || 24)))
}

function renderMemberTaskQueue() {
  const { queueNode, stateNode } = memberTaskQueueNodes()
  if (!queueNode || !stateNode) return
  queueNode.innerHTML = ""
  if (!state.memberPanel.tasks.length) {
    stateNode.textContent = i18nMessage("member.tasks.idle", "Task queue is idle.")
    return
  }
  state.memberPanel.tasks.forEach((item) => {
    const line = document.createElement("div")
    line.className = `member-task-item ${item.ok ? "is-success" : "is-warning"}`
    line.textContent = `${item.at} | ${item.name} | ${item.status} | ${item.message || (item.ok ? "ok" : "failed")}`
    queueNode.appendChild(line)
  })
  stateNode.textContent = i18nFormat(
    "member.tasks.summary",
    "Task queue updated: {count}",
    { count: state.memberPanel.tasks.length },
  )
}

async function loadMemberTasks(options = {}) {
  const { queueNode, stateNode } = memberTaskQueueNodes()
  if (!queueNode || !stateNode) return null
  if (!hasCapability("member.tasks.read")) return null
  const shouldRefresh = Boolean(options.refresh)
  const a = actor()
  const response = shouldRefresh
    ? await api("/api/member/tasks/refresh", {
      method: "POST",
      body: { user_id: a.user_id, limit: 50 },
    })
    : await api(`/api/member/tasks${queryString({ user_id: a.user_id, limit: 50 })}`)
  if (workspaceRequestFailed(response)) {
    return response
  }
  const data = apiData(response)
  const serverRows = Array.isArray(data.tasks) ? data.tasks : []
  state.memberPanel.tasks = mergeMemberTasks([...serverRows, ...state.memberPanel.tasks], 24)
  renderMemberTaskQueue()
  return response
}

function pushMemberTask(name, payload) {
  const { queueNode, stateNode } = memberTaskQueueNodes()
  if (!queueNode || !stateNode) return
  const response = payload && typeof payload === "object" ? payload : {}
  const ok = Boolean(response.data && response.data.ok)
  const status = Number(response.status || 0)
  const message = String((response.data && response.data.message) || "")
  const entry = {
    name: String(name || "operation"),
    ok,
    status,
    message,
    at: new Date().toISOString(),
  }
  state.memberPanel.tasks = mergeMemberTasks([entry, ...state.memberPanel.tasks], 24)
  renderMemberTaskQueue()
  void loadMemberTasks()
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
      input.dispatchEvent(new Event("change", { bubbles: true }))
    } catch (_error) {
      syncFileName()
    }
  })
  syncFileName()
}

async function loadMemberInstallations(options = {}) {
  if (!hasCapability("member.installations.read")) {
    state.memberPanel.installations = []
    renderMemberInstallations([])
    setMemberInstallationsState(
      "warning",
      i18nFormat(
        "capability.locked_hint",
        "Requires capability: {capability}",
        { capability: "member.installations.read" },
      ),
    )
    return buildClientErrorResponse("permission_denied", "permission denied", 403)
  }
  const shouldRefresh = Boolean(options.refresh)
  const a = actor()
  setMemberInstallationsState(
    "loading",
    i18nMessage("member.installations.loading", "Loading local installations..."),
  )
  const response = shouldRefresh
    ? await api("/api/member/installations/refresh", {
      method: "POST",
      body: { user_id: a.user_id, limit: 50 },
    })
    : await api(`/api/member/installations${queryString({ user_id: a.user_id, limit: 50 })}`)
  const data = apiData(response)
  const rows = Array.isArray(data.installations) ? data.installations : []
  state.memberPanel.installations = rows
  renderMemberInstallations(rows)
  if (workspaceRequestFailed(response)) {
    setMemberInstallationsState(
      "error",
      i18nFormat("member.installations.error", "Failed to load installations: {message}", {
        message: errorMessageForCollection("templates", response),
      }),
    )
  } else {
    setMemberInstallationsState(
      rows.length ? "success" : "neutral",
      i18nFormat("member.installations.ready", "Local installations: {count}", { count: rows.length }),
    )
  }
  render(shouldRefresh ? "member_installations_refresh" : "member_installations", response)
  return response
}

function marketChipButtons() {
  return Array.from(document.querySelectorAll("[data-market-chip]"))
}

function isInlineMemberMarketVisible() {
  const section = byId("section-market")
  if (!section) return false
  return !section.classList.contains("hidden")
}

function revealInlineMemberMarket() {
  const section = byId("section-market")
  if (!section) return null
  section.classList.remove("hidden")
  return section
}

function memberSpotlightProfilePackQuery(value) {
  const raw = String(value || "").trim()
  const normalized = raw.toLowerCase()
  if (!raw) return ""
  if (normalized.startsWith("profile/")) return raw
  if (normalized.includes("official-starter")) return "profile/official-starter"
  if (normalized.includes("official-safe-reference")) return "profile/official-safe-reference"
  return ""
}

function syncMemberSpotlightMarketJump(query) {
  const button = byId("memberSpotlightMarketJump")
  if (!button) return
  const nextQuery = String(query || "").trim()
  button.dataset.marketQuery = nextQuery
  button.classList.toggle("hidden", !nextQuery)
}

function openMemberSpotlightMarketQuery(query) {
  const nextQuery = String(query || "").trim()
  if (!nextQuery || !window.location) return
  window.location.assign(`/market?q=${encodeURIComponent(nextQuery)}`)
}

function setActiveMarketChip(chipValue = "") {
  const value = String(chipValue || "").trim()
  marketChipButtons().forEach((node) => {
    const chip = String(node.getAttribute("data-market-chip") || "")
    const active = chip === value
    node.classList.toggle("is-active", active)
    node.setAttribute("aria-pressed", active ? "true" : "false")
  })
}

function wizardStepNodes() {
  return Array.from(document.querySelectorAll("#submitWizardModal .wizard-step"))
}

function setWizardStep(step) {
  const totalSteps = 3
  const normalizedStep = Math.min(totalSteps, Math.max(1, Number(step || 1)))
  state.marketHub.wizardStep = normalizedStep
  wizardStepNodes().forEach((node) => {
    const nodeStep = Number(node.getAttribute("data-step") || "0")
    node.classList.toggle("hidden", nodeStep !== normalizedStep)
  })
  const statusNode = byId("submitWizardStepState")
  if (statusNode) {
    statusNode.textContent = i18nFormat(
      "market.wizard.step_format",
      "Step {step} / {total}",
      { step: normalizedStep, total: totalSteps },
    )
  }
  const prevButton = byId("btnSubmitWizardPrev")
  const nextButton = byId("btnSubmitWizardNext")
  const publishButton = byId("btnSubmitWizardPublish")
  if (prevButton) prevButton.disabled = normalizedStep <= 1
  if (nextButton) nextButton.classList.toggle("hidden", normalizedStep >= totalSteps)
  if (publishButton) publishButton.classList.toggle("hidden", normalizedStep < totalSteps)
  if (normalizedStep === totalSteps) {
    const review = byId("submitWizardReview")
    if (review) {
      review.textContent = i18nFormat(
        "market.wizard.review_format",
        "template={template} | version={version}",
        {
          template: String(byId("wizardTemplateId").value || "").trim() || "-",
          version: String(byId("wizardTemplateVersion").value || "").trim() || "-",
        },
      )
    }
  }
}

function submitWizardContainer() {
  return byId("submitWizardModal")
}

function openSubmitWizard() {
  const modal = submitWizardContainer()
  if (!modal) return
  byId("wizardTemplateId").value = String(byId("submitTemplateId").value || "").trim() || "community/basic"
  byId("wizardTemplateVersion").value = String(byId("submitVersion").value || "").trim() || "1.0.0"
  modal.setAttribute("role", "dialog")
  modal.setAttribute("aria-modal", "true")
  modal.classList.remove("hidden")
  modal.setAttribute("aria-hidden", "false")
  setWizardStep(1)
  activateDialogFocus("submitWizard", modal, {
    close: closeSubmitWizard,
    resolveFallbackFocus: () => byId("btnOpenSubmitWizard"),
  })
  const templateInput = byId("wizardTemplateId")
  if (templateInput && typeof templateInput.focus === "function") {
    templateInput.focus()
  }
}

function closeSubmitWizard() {
  const modal = submitWizardContainer()
  if (!modal) return
  modal.classList.add("hidden")
  modal.setAttribute("aria-hidden", "true")
  deactivateDialogFocus("submitWizard", modal)
}

async function submitTemplateFromWizard() {
  const templateId = String(byId("wizardTemplateId").value || "").trim()
  const version = String(byId("wizardTemplateVersion").value || "").trim() || "1.0.0"
  if (!templateId) {
    setWizardStep(1)
    byId("wizardTemplateId").focus()
    return
  }
  const a = actor()
  const fileInput = byId("wizardPackageFile")
  const file = fileInput && fileInput.files ? fileInput.files[0] : null
  let packagePayload = {}
  if (file) {
    try {
      assertUploadFileAllowed(file)
    } catch (error) {
      render("submit_template_wizard", uploadTooLargeResponse())
      return
    }
    packagePayload = {
      package_name: file.name,
      package_base64: await readFileAsBase64(file),
    }
  }
  applyFieldPatches({
    submitTemplateId: templateId,
    submitVersion: version,
    trialTemplateId: templateId,
  })
  const response = await api("/api/templates/submit", {
    method: "POST",
    body: {
      ...a,
      template_id: templateId,
      version,
      upload_options: readUploadOptionsFromForm(),
      ...packagePayload,
    },
  })
  render("submit_template_wizard", response)
  if (!workspaceRequestFailed(response)) {
    state.selectedTemplateId = templateId
    state.marketHub.selectedTemplateId = templateId
    closeSubmitWizard()
    await listTemplates()
    applyFieldPatches({
      submitTemplateId: templateId,
      submitVersion: version,
      trialTemplateId: templateId,
    })
  }
}

async function downloadPackage() {
  const templateId = byId("trialTemplateId").value
  const params = new URLSearchParams({ template_id: templateId })
  const response = await fetch(`/api/templates/package/download?${params.toString()}`, {
    method: "GET",
    headers: state.token && state.token !== "no-auth" ? { Authorization: `Bearer ${state.token}` } : {}
  })
  if (!response.ok) {
    const data = await response.json().catch(() => ({ ok: false, message: "download_failed" }))
    render("package_download", { status: response.status, data })
    return
  }
  const blob = await response.blob()
  const disposition = response.headers.get("Content-Disposition") || ""
  const match = disposition.match(/filename=\"?([^"]+)\"?$/i)
  const filename = match ? match[1] : `${templateId.replace(/\//g, "__")}.zip`
  const url = URL.createObjectURL(blob)
  const link = document.createElement("a")
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
  render("package_download", {
    status: response.status,
    data: { ok: true, filename, size_bytes: blob.size }
  })
}

async function downloadSubmissionPackage() {
  const submissionId = byId("decisionSubmissionId").value
  const a = actor()
  const normalizedRole = String(a.role || "").trim().toLowerCase()
  const useAdminEndpoint = hasCapability("admin.submissions.package.download") && normalizedRole !== "member"
  const useMemberEndpoint = !useAdminEndpoint && hasCapability("member.submissions.package.download")
  if (!useAdminEndpoint && !useMemberEndpoint) {
    render("submission_package_download", buildClientErrorResponse("permission_denied", "permission denied", 403))
    return
  }
  const params = new URLSearchParams({ submission_id: submissionId })
  if (useMemberEndpoint) {
    params.set("user_id", a.user_id)
  }
  const endpoint = useAdminEndpoint
    ? `/api/admin/submissions/package/download?${params.toString()}`
    : `/api/member/submissions/package/download?${params.toString()}`
  const response = await fetch(endpoint, {
    method: "GET",
    headers: state.token && state.token !== "no-auth" ? { Authorization: `Bearer ${state.token}` } : {}
  })
  if (!response.ok) {
    const data = await response.json().catch(() => ({ ok: false, message: "download_failed" }))
    render("submission_package_download", { status: response.status, data })
    return
  }
  const blob = await response.blob()
  const disposition = response.headers.get("Content-Disposition") || ""
  const match = disposition.match(/filename=\"?([^"]+)\"?$/i)
  const filename = match ? match[1] : `${submissionId || "submission"}.zip`
  const url = URL.createObjectURL(blob)
  const link = document.createElement("a")
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
  render("submission_package_download", {
    status: response.status,
    data: { ok: true, filename, size_bytes: blob.size }
  })
}

async function loadTrialStatus() {
  const a = actor()
  const response = await api(`/api/trial/status${queryString({
    user_id: a.user_id,
    session_id: a.session_id,
    template_id: byId("trialTemplateId").value
  })}`)
  render("trial_status", response)
  if (!workspaceRequestFailed(response)) {
    updateTrialStatusPanel(apiData(response))
  }
  return response
}

async function prepareDryrunPlan() {
  const a = actor()
  const draft = dryrunDraft()
  const response = await api("/api/admin/dryrun", {
    method: "POST",
    body: {
      ...a,
      plan_id: draft.plan_id,
      patch: draft.patch,
    }
  })
  render("admin_dryrun", response)
  if (!workspaceRequestFailed(response)) {
    updateApplyWorkflowPanel(apiData(response))
  }
  return response
}

async function applyPlan() {
  const a = actor()
  const draft = dryrunDraft()
  const response = await api("/api/admin/apply", {
    method: "POST",
    body: {
      ...a,
      plan_id: draft.plan_id,
    }
  })
  render("admin_apply", response)
  if (!workspaceRequestFailed(response)) {
    const data = apiData(response)
    updateApplyWorkflowPanel({
      ...state.applyPlanResult,
      ...data,
      patch: (state.applyPlanResult && state.applyPlanResult.patch) || draft.patch,
    })
    if (data && data.continuity) {
      setContinuityOutput("continuityDetailOutput", buildContinuityDetailText({ entry: data.continuity }), { entry: data.continuity })
      applyFieldPatches({ continuityPlanId: data.continuity.plan_id || draft.plan_id })
    }
  }
  return response
}

async function rollbackPlan() {
  const a = actor()
  const draft = dryrunDraft()
  const response = await api("/api/admin/rollback", {
    method: "POST",
    body: {
      ...a,
      plan_id: draft.plan_id,
    }
  })
  render("admin_rollback", response)
  if (!workspaceRequestFailed(response)) {
    const data = apiData(response)
    updateApplyWorkflowPanel({
      ...state.applyPlanResult,
      ...data,
      patch: (state.applyPlanResult && state.applyPlanResult.patch) || draft.patch,
    })
    if (data && data.continuity) {
      setContinuityOutput("continuityDetailOutput", buildContinuityDetailText({ entry: data.continuity }), { entry: data.continuity })
      applyFieldPatches({ continuityPlanId: data.continuity.plan_id || draft.plan_id })
    }
  }
  return response
}

async function loadTemplateDetail(options = {}) {
  const templateId = options.templateId || byId("trialTemplateId").value || byId("submitTemplateId").value
  if (!templateId) return
  if (options.syncRoute !== false) {
    await navigateToWorkspace({ scope: "template", id: templateId }, { targetId: "templateWorkspaceSection" })
    return
  }
  setPanelStatus("templateDetail", { status: "loading", id: templateId, errorMessage: "" })
  updateTemplateDetailPanel({})
  clearScanPanelSource()
  rerenderScanPanelFromState()
  const response = await api(`/api/templates/detail${queryString({ template_id: templateId })}`)
  render("template_detail", response)
  if (workspaceRequestFailed(response)) {
    setPanelStatus("templateDetail", {
      status: "error",
      id: templateId,
      errorMessage: errorMessageForPanel("templateDetail", response),
    })
    updateTemplateDetailPanel({})
  }
}

async function loadSubmissionDetail(options = {}) {
  const submissionId = options.submissionId || byId("decisionSubmissionId").value
  if (!submissionId) return
  if (options.syncRoute !== false) {
    await navigateToWorkspace({ scope: "submission", id: submissionId }, { targetId: "submissionWorkspaceSection" })
    return
  }
  setPanelStatus("submissionDetail", { status: "loading", id: submissionId, errorMessage: "" })
  updateSubmissionDetailPanel({})
  clearScanPanelSource()
  rerenderScanPanelFromState()
  const a = actor()
  const normalizedRole = String(a.role || "").trim().toLowerCase()
  const useAdminEndpoint = hasCapability("admin.submissions.read") && normalizedRole !== "member"
  const useMemberEndpoint = !useAdminEndpoint && hasCapability("member.submissions.detail.read")
  if (!useAdminEndpoint && !useMemberEndpoint) {
    const denied = buildClientErrorResponse("permission_denied", "permission denied", 403)
    render("submission_detail", denied)
    setPanelStatus("submissionDetail", {
      status: "error",
      id: submissionId,
      errorMessage: errorMessageForPanel("submissionDetail", denied),
    })
    updateSubmissionDetailPanel({})
    return denied
  }
  const endpoint = useAdminEndpoint
    ? `/api/admin/submissions/detail${queryString({
      role: a.role,
      submission_id: submissionId,
    })}`
    : `/api/member/submissions/detail${queryString({
      user_id: a.user_id,
      submission_id: submissionId,
    })}`
  const response = await api(endpoint)
  render(useAdminEndpoint ? "admin_submission_detail" : "member_submission_detail", response)
  if (workspaceRequestFailed(response)) {
    setPanelStatus("submissionDetail", {
      status: "error",
      id: submissionId,
      errorMessage: errorMessageForPanel("submissionDetail", response),
    })
    updateSubmissionDetailPanel({})
  }
}

async function loadSubmissionCompare(options = {}) {
  const submissionId = options.submissionId || byId("decisionSubmissionId").value
  if (!submissionId) return
  if (!hasCapability("admin.submissions.compare")) {
    resetComparePanel()
    setPanelStatus("compare", { status: "idle", id: submissionId, errorMessage: "" })
    return buildClientErrorResponse("permission_denied", "permission denied", 403)
  }
  if (options.syncRoute !== false) {
    await navigateToWorkspace({ scope: "submission", id: submissionId }, { targetId: "submissionWorkspaceSection" })
    return
  }
  setPanelStatus("compare", { status: "loading", id: submissionId, errorMessage: "" })
  resetComparePanel({ preserveStatus: true })
  const a = actor()
  const response = await api(`/api/admin/submissions/compare${queryString({
    role: a.role,
    submission_id: submissionId
  })}`)
  render("admin_compare_submission", response)
  if (workspaceRequestFailed(response)) {
    resetComparePanel({ preserveStatus: true })
    setPanelStatus("compare", {
      status: "error",
      id: submissionId,
      errorMessage: errorMessageForPanel("compare", response),
    })
  }
}

async function saveSubmissionReview() {
  const a = actor()
  const submissionId = byId("decisionSubmissionId").value
  if (!submissionId) return
  render("admin_save_submission_review", await api("/api/admin/submissions/review", {
    method: "POST",
    body: {
      ...a,
      submission_id: submissionId,
      review_note: byId("reviewNote").value,
      review_labels: reviewLabelsArray()
    }
  }))
  await loadSubmissionDetail({ submissionId, syncRoute: false })
  await loadSubmissionCompare({ submissionId, syncRoute: false })
}

async function decideSubmission(decision) {
  const a = actor()
  const submissionId = byId("decisionSubmissionId").value
  if (!submissionId) return
  const finalDecision = decision || byId("submissionDecision").value
  byId("submissionDecision").value = finalDecision
  render("admin_decide_submission", await api("/api/admin/submissions/decide", {
    method: "POST",
    body: {
      ...a,
      submission_id: submissionId,
      decision: finalDecision,
      review_note: byId("reviewNote").value,
      review_labels: reviewLabelsArray()
    }
  }))
  await loadSubmissionDetail({ submissionId, syncRoute: false })
  await loadSubmissionCompare({ submissionId, syncRoute: false })
}

function handleUiStorageSync(event) {
  if (!event || !event.key) return
  const key = String(event.key || "")
  if (key === UI_LOCALE_STORAGE_KEY) {
    const incoming = String(event.newValue || "").trim()
    const nextLocale = normalizeUiLocale(incoming || browserUiLocale() || "en-US")
    if (nextLocale !== state.uiLocale) {
      applyUiLocale(nextLocale, {
        persist: false,
        refreshCollections: true,
        source: "storage",
        sourceId: "storage",
      })
    }
    return
  }
  if (key === DEVELOPER_MODE_STORAGE_KEY) {
    const nextValue = parseDeveloperModeValue(event.newValue)
    if (nextValue !== state.developerMode) {
      setDeveloperMode(nextValue, {
        persist: false,
        source: "storage",
        sourceId: "storage",
      })
    }
  }
}

function bindStorageSync() {
  if (storageSyncBound) return
  if (!globalThis || typeof globalThis.addEventListener !== "function") return
  globalThis.addEventListener("storage", handleUiStorageSync)
  storageSyncBound = true
}

function bindUiEventBusSync() {
  if (uiEventBusBound) return
  const bus = uiEventBusHelpers()
  if (!bus || typeof bus.on !== "function") return
  const localeTopic = uiEventTopic("UI_LOCALE_CHANGED", "ui.locale.changed")
  const developerTopic = uiEventTopic("DEVELOPER_MODE_CHANGED", "ui.developer_mode.changed")

  const offLocale = bus.on(localeTopic, (payload) => {
    if (!payload || payload.sourceId === APP_PAGE_INSTANCE_ID) return
    const locale = normalizeUiLocale(payload.locale || "")
    if (locale === state.uiLocale) return
    applyUiLocale(locale, {
      persist: false,
      refreshCollections: true,
      emit: false,
      source: payload.source || "event_bus",
      sourceId: payload.sourceId || "event_bus",
    })
  })
  const offDeveloper = bus.on(developerTopic, (payload) => {
    if (!payload || payload.sourceId === APP_PAGE_INSTANCE_ID) return
    const enabled = Boolean(payload.enabled)
    if (enabled === state.developerMode) return
    setDeveloperMode(enabled, {
      persist: false,
      emit: false,
      source: payload.source || "event_bus",
      sourceId: payload.sourceId || "event_bus",
    })
  })
  uiEventBusUnsubscribe.push(offLocale, offDeveloper)
  uiEventBusBound = true
}

function triggerControl(id) {
  const node = byId(id)
  if (!node) return
  node.click()
}

function bindButtons() {
  Array.from(document.querySelectorAll(".sidebar-link")).forEach((node) => {
    node.addEventListener("click", () => {
      Array.from(document.querySelectorAll(".sidebar-link")).forEach((link) => {
        link.classList.remove("is-active")
      })
      node.classList.add("is-active")
    })
  })
  byId("loginBtn").addEventListener("click", login)
  byId("authRole").addEventListener("change", syncReviewerAuthFields)
  const openLoginButton = byId("btnAuthOpenLoginPanel")
  if (openLoginButton) {
    openLoginButton.addEventListener("click", () => {
      state.authPromptRequested = true
      updateAuthUi()
      const passwordNode = byId("authPassword")
      if (passwordNode && typeof passwordNode.focus === "function") {
        passwordNode.focus()
      }
    })
  }
  byId("role").addEventListener("change", () => {
    applyConsoleScope()
    void refreshCapabilities({ updateScope: false })
  })
  byId("uiLocale").addEventListener("change", () => {
    applyUiLocale(byId("uiLocale").value, { persist: true, refreshCollections: true })
  })
  localeQuickButtons().forEach((node) => {
    node.addEventListener("click", () => {
      const locale = String(node.getAttribute("data-locale-option") || "").trim()
      if (!locale) return
      applyUiLocale(locale, { persist: true, refreshCollections: true })
    })
  })
  const developerToggle = byId("btnToggleDeveloperMode")
  if (developerToggle) {
    developerToggle.addEventListener("click", () => {
      setDeveloperMode(!state.developerMode, { persist: true })
    })
  }
  byId("btnReloadWorkspace").addEventListener("click", () => {
    void syncWorkspaceFromHash()
  })
  byId("btnClearWorkspace").addEventListener("click", clearWorkspaceRoute)

  const reviewerInviteCreateButton = byId("btnReviewerInviteCreate")
  if (reviewerInviteCreateButton) {
    reviewerInviteCreateButton.addEventListener("click", () => {
      void createReviewerInvite()
    })
  }
  const reviewerInviteListButton = byId("btnReviewerInviteList")
  if (reviewerInviteListButton) {
    reviewerInviteListButton.addEventListener("click", () => {
      void listReviewerInvites()
    })
  }
  const reviewerAccountListButton = byId("btnReviewerAccountList")
  if (reviewerAccountListButton) {
    reviewerAccountListButton.addEventListener("click", () => {
      void listReviewerAccounts()
    })
  }
  const reviewerDeviceListButton = byId("btnReviewerDeviceList")
  if (reviewerDeviceListButton) {
    reviewerDeviceListButton.addEventListener("click", () => {
      void listReviewerDevices()
    })
  }
  const reviewerDeviceResetButton = byId("btnReviewerDeviceReset")
  if (reviewerDeviceResetButton) {
    reviewerDeviceResetButton.addEventListener("click", () => {
      void resetReviewerDevices()
    })
  }
  const reviewerSessionListButton = byId("btnReviewerSessionList")
  if (reviewerSessionListButton) {
    reviewerSessionListButton.addEventListener("click", () => {
      void listReviewerSessions()
    })
  }
  const reviewerSessionRevokeButton = byId("btnReviewerSessionRevoke")
  if (reviewerSessionRevokeButton) {
    reviewerSessionRevokeButton.addEventListener("click", () => {
      void revokeReviewerSessions()
    })
  }
  const reviewerDeviceTargetNode = byId("reviewerDeviceTargetId")
  if (reviewerDeviceTargetNode) {
    reviewerDeviceTargetNode.addEventListener("change", () => {
      setReviewerLifecycleSelectedReviewer(String(reviewerDeviceTargetNode.value || "").trim())
    })
  }

  byId("btnPrefGet").addEventListener("click", async () => {
    const a = actor()
    render("get_preferences", await api(`/api/preferences${queryString({ user_id: a.user_id })}`))
  })

  byId("btnModeSet").addEventListener("click", async () => {
    const a = actor()
    render("set_mode", await api("/api/preferences/mode", {
      method: "POST",
      body: { ...a, mode: byId("modeValue").value }
    }))
  })

  byId("btnObserveSet").addEventListener("click", async () => {
    const a = actor()
    render("set_observe", await api("/api/preferences/observe", {
      method: "POST",
      body: { ...a, enabled: byId("observeValue").value === "true" }
    }))
  })

  const listTemplatesButton = byId("btnTemplates")
  if (listTemplatesButton) {
    listTemplatesButton.addEventListener("click", listTemplates)
  }
  const memberSearchNode = byId("memberGlobalSearch")
  if (memberSearchNode) {
    memberSearchNode.addEventListener("input", () => {
      const value = String(memberSearchNode.value || "").trim()
      const packQuery = memberSpotlightProfilePackQuery(value)
      state.memberPanel.searchQuery = value
      renderMemberInstallations(state.memberPanel.installations)
      renderMemberImportDrafts(state.memberPanel.importDrafts)
      const templateFilter = byId("templateFilterId")
      const categoryFilter = byId("templateCategoryFilter")
      if (templateFilter) {
        templateFilter.value = packQuery ? "" : value
      }
      if (value && byId("trialTemplateId")) {
        byId("trialTemplateId").value = value
      }
      if (value && categoryFilter) {
        categoryFilter.value = ""
        setActiveMarketChip("")
      }
      syncMemberSpotlightMarketJump(packQuery)
      if (packQuery) return
      revealInlineMemberMarket()
      if (templateFilter && categoryFilter) {
        void listTemplates()
      }
    })
    memberSearchNode.addEventListener("keydown", (event) => {
      if (event.key !== "Enter") return
      event.preventDefault()
      const value = String(memberSearchNode.value || "").trim()
      const packQuery = memberSpotlightProfilePackQuery(value)
      if (packQuery) {
        openMemberSpotlightMarketQuery(packQuery)
        return
      }
      revealInlineMemberMarket()
      if (byId("templateFilterId") && byId("templateCategoryFilter")) {
        void listTemplates()
      }
    })
  }
  const memberSpotlightMarketJump = byId("memberSpotlightMarketJump")
  if (memberSpotlightMarketJump) {
    memberSpotlightMarketJump.addEventListener("click", () => {
      openMemberSpotlightMarketQuery(
        String(memberSpotlightMarketJump.dataset.marketQuery || "").trim(),
      )
    })
  }
  const importAstrbotButton = byId("btnImportAstrbotConfig")
  if (importAstrbotButton) {
    importAstrbotButton.addEventListener("click", () => {
      void importMemberLocalAstrbotConfig()
    })
  }
  const importConfigPackButton = byId("btnImportConfigPackFile")
  if (importConfigPackButton) {
    importConfigPackButton.addEventListener("click", () => {
      promptMemberProfilePackImport()
    })
  }
  const openMemberImportReviewButton = byId("btnOpenMemberImportReview")
  if (openMemberImportReviewButton) {
    openMemberImportReviewButton.addEventListener("click", () => {
      openMemberProfilePackUploadModalById("")
    })
  }
  const importAstrbotInput = byId("memberImportAstrbotConfigFile")
  if (importAstrbotInput) {
    importAstrbotInput.addEventListener("change", () => {
      void importMemberProfilePackFromSelection()
    })
  }
  const refreshMemberInstallationsButton = byId("btnRefreshMemberInstallationsInline")
  if (refreshMemberInstallationsButton) {
    refreshMemberInstallationsButton.addEventListener("click", () => {
      void loadMemberInstallations({ refresh: true })
    })
  }
  const memberProfilePackUploadClose = byId("btnCloseMemberProfilePackUploadModal")
  if (memberProfilePackUploadClose) {
    memberProfilePackUploadClose.addEventListener("click", closeMemberProfilePackUploadModal)
  }
  const memberProfilePackUploadCancel = byId("btnMemberProfilePackUploadCancel")
  if (memberProfilePackUploadCancel) {
    memberProfilePackUploadCancel.addEventListener("click", closeMemberProfilePackUploadModal)
  }
  const memberProfilePackUploadBackdrop = byId("memberProfilePackUploadBackdrop")
  if (memberProfilePackUploadBackdrop) {
    memberProfilePackUploadBackdrop.addEventListener("click", closeMemberProfilePackUploadModal)
  }
  const memberProfilePackUploadSubmit = byId("btnMemberProfilePackUploadSubmit")
  if (memberProfilePackUploadSubmit) {
    memberProfilePackUploadSubmit.addEventListener("click", () => {
      void submitSelectedMemberImportDraft()
    })
  }
  const memberProfilePackUploadDelete = byId("btnMemberProfilePackUploadDelete")
  if (memberProfilePackUploadDelete) {
    memberProfilePackUploadDelete.addEventListener("click", () => {
      void deleteMemberImportDraft()
    })
  }
  bindUploadDropZone({
    zoneId: "memberUploadDropzone",
    inputId: "memberImportAstrbotConfigFile",
    outputId: "memberUploadFileName",
    emptyKey: "member.upload.file_idle",
    emptyFallback: "No file selected. Max 20 MiB. Sharelife standard zip, AstrBot backup zip, cmd_config.json, and abconf_*.json are supported.",
  })
  marketChipButtons().forEach((node) => {
    node.addEventListener("click", () => {
      revealInlineMemberMarket()
      const value = String(node.getAttribute("data-market-chip") || "").trim()
      const categoryFilter = byId("templateCategoryFilter")
      if (categoryFilter) {
        categoryFilter.value = value
      }
      const memberSearch = byId("memberGlobalSearch")
      if (memberSearch) {
        memberSearch.value = ""
      }
      setActiveMarketChip(value)
      void listTemplates()
    })
  })
  byId("btnTemplateDrawerClose").addEventListener("click", closeTemplateDrawer)
  byId("btnDrawerTrial").addEventListener("click", () => {
    if (state.marketHub.selectedTemplateId) {
      byId("trialTemplateId").value = state.marketHub.selectedTemplateId
    }
    triggerControl("btnTrial")
  })
  byId("btnDrawerInstall").addEventListener("click", () => {
    if (state.marketHub.selectedTemplateId) {
      byId("trialTemplateId").value = state.marketHub.selectedTemplateId
    }
    triggerControl("btnInstall")
  })
  byId("btnDrawerPrompt").addEventListener("click", () => {
    if (state.marketHub.selectedTemplateId) {
      byId("trialTemplateId").value = state.marketHub.selectedTemplateId
    }
    triggerControl("btnPrompt")
  })
  byId("btnDrawerPackage").addEventListener("click", () => {
    if (state.marketHub.selectedTemplateId) {
      byId("trialTemplateId").value = state.marketHub.selectedTemplateId
    }
    triggerControl("btnPackage")
  })
  byId("btnDrawerDetail").addEventListener("click", () => {
    if (state.marketHub.selectedTemplateId) {
      byId("trialTemplateId").value = state.marketHub.selectedTemplateId
    }
    triggerControl("btnTemplateDetail")
  })
  byId("btnOpenSubmitWizard").addEventListener("click", openSubmitWizard)
  byId("btnCloseSubmitWizard").addEventListener("click", closeSubmitWizard)
  byId("submitWizardBackdrop").addEventListener("click", closeSubmitWizard)
  byId("btnSubmitWizardPrev").addEventListener("click", () => {
    setWizardStep(state.marketHub.wizardStep - 1)
  })
  byId("btnSubmitWizardNext").addEventListener("click", () => {
    if (state.marketHub.wizardStep === 1 && !String(byId("wizardTemplateId").value || "").trim()) {
      byId("wizardTemplateId").focus()
      return
    }
    setWizardStep(state.marketHub.wizardStep + 1)
  })
  byId("btnSubmitWizardPublish").addEventListener("click", () => {
    void submitTemplateFromWizard()
  })

  byId("btnSubmitTemplate").addEventListener("click", async () => {
    const a = actor()
    let packagePayload = {}
    try {
      packagePayload = await selectedPackagePayload()
    } catch (error) {
      render("submit_template", uploadTooLargeResponse())
      return
    }
    render("submit_template", await api("/api/templates/submit", {
      method: "POST",
      body: {
        ...a,
        template_id: byId("submitTemplateId").value,
        version: byId("submitVersion").value || "1.0.0",
        upload_options: readUploadOptionsFromForm(),
        ...packagePayload
      }
    }))
  })

  byId("btnTrial").addEventListener("click", async () => {
    const a = actor()
    const response = await api("/api/trial", {
      method: "POST",
      body: {
        ...a,
        template_id: byId("trialTemplateId").value
      }
    })
    render("trial", response)
    if (!workspaceRequestFailed(response)) {
      await loadTrialStatus()
    }
  })

  byId("btnTrialStatus").addEventListener("click", () => {
    void loadTrialStatus()
  })

  byId("btnInstall").addEventListener("click", async () => {
    const a = actor()
    render("install", await api("/api/templates/install", {
      method: "POST",
      body: {
        ...a,
        template_id: byId("trialTemplateId").value,
        install_options: readInstallOptionsFromForm(),
      }
    }))
  })

  byId("btnPrompt").addEventListener("click", async () => {
    render("prompt", await api("/api/templates/prompt", {
      method: "POST",
      body: { template_id: byId("trialTemplateId").value }
    }))
  })

  byId("btnPackage").addEventListener("click", async () => {
    render("package", await api("/api/templates/package", {
      method: "POST",
      body: { template_id: byId("trialTemplateId").value }
    }))
  })

  byId("btnTemplateDetail").addEventListener("click", loadTemplateDetail)
  byId("btnPackageDownload").addEventListener("click", downloadPackage)
  byId("btnDryrunPlan").addEventListener("click", () => {
    void prepareDryrunPlan()
  })
  byId("btnApplyPlan").addEventListener("click", () => {
    void applyPlan()
  })
  byId("btnRollbackPlan").addEventListener("click", () => {
    void rollbackPlan()
  })
  byId("btnProfilePackExport").addEventListener("click", () => {
    void exportProfilePack()
  })
  byId("btnProfilePackDownloadExport").addEventListener("click", () => {
    void downloadProfilePackExport()
  })
  byId("btnProfilePackListExports").addEventListener("click", () => {
    void listProfilePackExports()
  })
  byId("btnProfilePackImport").addEventListener("click", () => {
    void importProfilePack()
  })
  byId("btnProfilePackImportFromExport").addEventListener("click", () => {
    void importProfilePackFromExport()
  })
  byId("btnProfilePackImportDryrun").addEventListener("click", () => {
    void importAndDryrunProfilePack()
  })
  byId("btnProfilePackListImports").addEventListener("click", () => {
    void listProfilePackImports()
  })
  byId("btnProfilePackDryrun").addEventListener("click", () => {
    void dryrunProfilePack()
  })
  byId("btnProfilePackApply").addEventListener("click", () => {
    void applyProfilePackPlan()
  })
  byId("btnProfilePackRollback").addEventListener("click", () => {
    void rollbackProfilePackPlan()
  })
  byId("btnProfilePackPluginPlan").addEventListener("click", () => {
    void loadProfilePackPluginInstallPlan()
  })
  byId("btnProfilePackPluginConfirm").addEventListener("click", () => {
    void confirmProfilePackPluginInstall()
  })
  byId("btnProfilePackPluginExecute").addEventListener("click", () => {
    void executeProfilePackPluginInstall()
  })
  byId("profilePackRecordPackFilter").addEventListener("input", () => {
    setProfilePackRecordPackFilter(readProfilePackRecordPackFilter())
    renderProfilePackRecords()
  })
  byId("btnProfilePackClearRecordFilter").addEventListener("click", () => {
    setProfilePackRecordPackFilter("")
    renderProfilePackRecords()
  })
  byId("btnProfilePackSubmitCommunity").addEventListener("click", () => {
    void submitProfilePackToCommunity()
  })
  byId("btnProfilePackListPackSubmissions").addEventListener("click", () => {
    void listProfilePackMarketSubmissions()
  })
  byId("btnProfilePackDecideSubmission").addEventListener("click", () => {
    void decideProfilePackSubmission()
  })
  byId("btnProfilePackListCatalog").addEventListener("click", () => {
    void listProfilePackCatalog()
  })
  byId("btnProfilePackCatalogDetail").addEventListener("click", () => {
    void loadProfilePackCatalogDetail()
  })
  byId("btnProfilePackCatalogCompare").addEventListener("click", () => {
    void compareProfilePackCatalog()
  })
  byId("btnProfilePackSetFeatured").addEventListener("click", () => {
    void setProfilePackFeatured()
  })

  byId("btnListSubmissions").addEventListener("click", listSubmissions)

  byId("btnSaveSubmissionReview").addEventListener("click", saveSubmissionReview)
  byId("btnApproveSubmission").addEventListener("click", async () => {
    await decideSubmission("approve")
  })
  byId("btnRejectSubmission").addEventListener("click", async () => {
    await decideSubmission("reject")
  })

  byId("btnSubmissionDetail").addEventListener("click", loadSubmissionDetail)
  byId("btnCompareSubmission").addEventListener("click", loadSubmissionCompare)

  byId("btnDownloadSubmissionPackage").addEventListener("click", downloadSubmissionPackage)

  byId("btnListRetry").addEventListener("click", async () => {
    const a = actor()
    render("admin_list_retry", await api(`/api/admin/retry-requests${queryString({ role: a.role })}`))
  })

  byId("btnLockRetry").addEventListener("click", async () => {
    const a = actor()
    render("admin_retry_lock", await api("/api/admin/retry-requests/lock", {
      method: "POST",
      body: {
        ...a,
        request_id: byId("lockRequestId").value,
        force: byId("lockForce").checked,
        reason: byId("lockReason").value
      }
    }))
  })

  byId("btnRetryDecide").addEventListener("click", async () => {
    const a = actor()
    render("admin_retry_decide", await api("/api/admin/retry-requests/decide", {
      method: "POST",
      body: {
        ...a,
        request_id: byId("retryRequestId").value,
        decision: byId("retryDecision").value,
        request_version: Number(byId("retryRequestVersion").value || 0),
        lock_version: Number(byId("retryLockVersion").value || 0)
      }
    }))
  })

  byId("btnAudit").addEventListener("click", async () => {
    const a = actor()
    const response = await api(`/api/admin/audit${queryString({
      role: a.role,
      limit: Number(byId("auditLimit").value || 20)
    })}`)
    render("admin_audit", response)
    const data = apiData(response)
    setAuditOutput("auditSummaryOutput", buildAuditSummaryText(data), data && data.summary ? data.summary : data)
    setAuditOutput("auditEventsOutput", buildAuditEventsText(data), data && data.events ? data.events : data)
  })

  byId("btnNotice").addEventListener("click", async () => {
    render("notifications", await api(`/api/notifications${queryString({
      limit: Number(byId("noticeLimit").value || 50)
    })}`))
  })

  byId("btnStorageSummary").addEventListener("click", async () => {
    const a = actor()
    const response = await api(`/api/admin/storage/local-summary${queryString({ role: a.role })}`)
    render("admin_storage_local_summary", response)
    const data = apiData(response)
    setStorageOutput("storageSummaryOutput", buildStorageLocalSummaryText(data), data)
  })

  byId("btnContinuityList").addEventListener("click", () => {
    void listContinuityEntries()
  })

  byId("btnContinuityGet").addEventListener("click", () => {
    void getContinuityDetail()
  })

  byId("btnStoragePoliciesGet").addEventListener("click", async () => {
    const a = actor()
    const response = await api(`/api/admin/storage/policies${queryString({ role: a.role })}`)
    render("admin_storage_get_policies", response)
    const data = apiData(response)
    if (data && typeof data === "object" && data.policies && typeof data.policies === "object") {
      applyStoragePolicyFields(data.policies)
    }
    setStorageOutput("storagePoliciesOutput", buildStoragePoliciesText(data), data)
  })

  byId("btnStoragePoliciesSet").addEventListener("click", async () => {
    const a = actor()
    const response = await api("/api/admin/storage/policies", {
      method: "POST",
      body: {
        ...a,
        policy_patch: readStoragePoliciesPatch(),
      },
    })
    render("admin_storage_set_policies", response)
    const data = apiData(response)
    if (data && typeof data === "object" && data.policies && typeof data.policies === "object") {
      applyStoragePolicyFields(data.policies)
    }
    setStorageOutput("storagePoliciesOutput", buildStoragePoliciesText(data), data)
  })

  byId("btnStorageRunBackup").addEventListener("click", async () => {
    const a = actor()
    const response = await api("/api/admin/storage/jobs/run", {
      method: "POST",
      body: {
        ...a,
        trigger: readTextField("storageJobTrigger", "manual") || "manual",
        note: readTextField("storageJobNote", ""),
      },
    })
    render("admin_storage_run_job", response)
    const data = apiData(response)
    const job = data && typeof data === "object" && data.job && typeof data.job === "object"
      ? data.job
      : null
    if (job) {
      applyFieldPatches({
        storageJobId: job.job_id,
        storageRestoreArtifactRef: job.artifact_id || job.job_id || "",
      })
    }
    setStorageOutput("storageJobsOutput", buildStorageJobDetailText(data), data)
  })

  byId("btnStorageJobsList").addEventListener("click", async () => {
    const a = actor()
    const status = readTextField("storageJobsStatus", "")
    const limit = readIntegerField("storageJobsLimit", 20, 1)
    const response = await api(`/api/admin/storage/jobs${queryString({ role: a.role, status, limit })}`)
    render("admin_storage_list_jobs", response)
    const data = apiData(response)
    setStorageOutput("storageJobsOutput", buildStorageJobsText(data), data)
  })

  byId("btnStorageJobGet").addEventListener("click", async () => {
    const a = actor()
    const jobId = readTextField("storageJobId", "")
    if (!jobId) {
      setStorageOutput(
        "storageJobsOutput",
        i18nMessage("storage.output.job_id_required", "job_id is required."),
        { error: "job_id_required" },
      )
      return
    }
    const response = await api(`/api/admin/storage/jobs/${encodeURIComponent(jobId)}${queryString({ role: a.role })}`)
    render("admin_storage_get_job", response)
    const data = apiData(response)
    const job = data && typeof data === "object" && data.job && typeof data.job === "object"
      ? data.job
      : null
    if (job) {
      applyFieldPatches({
        storageRestoreArtifactRef: job.artifact_id || job.job_id || "",
      })
    }
    setStorageOutput("storageJobsOutput", buildStorageJobDetailText(data), data)
  })

  byId("btnStorageRestorePrepare").addEventListener("click", async () => {
    const a = actor()
    const artifactRef = readTextField("storageRestoreArtifactRef", "")
    if (!artifactRef) {
      setStorageOutput(
        "storageRestoreOutput",
        i18nMessage("storage.output.artifact_ref_required", "artifact_ref is required."),
        { error: "artifact_ref_required" },
      )
      return
    }
    const response = await api("/api/admin/storage/restore/prepare", {
      method: "POST",
      body: {
        ...a,
        artifact_ref: artifactRef,
        note: readTextField("storageRestoreNote", ""),
      },
    })
    render("admin_storage_restore_prepare", response)
    const data = apiData(response)
    const restore = data && typeof data === "object" && data.restore && typeof data.restore === "object"
      ? data.restore
      : null
    if (restore) {
      applyFieldPatches({
        storageRestoreId: restore.restore_id,
        storageRestoreJobId: restore.restore_id,
      })
    }
    setStorageOutput("storageRestoreOutput", buildStorageRestoreText(data), data)
  })

  byId("btnStorageRestoreCommit").addEventListener("click", async () => {
    const a = actor()
    const restoreId = readTextField("storageRestoreId", "")
    if (!restoreId) {
      setStorageOutput(
        "storageRestoreOutput",
        i18nMessage("storage.output.restore_id_required", "restore_id is required."),
        { error: "restore_id_required" },
      )
      return
    }
    const response = await api("/api/admin/storage/restore/commit", {
      method: "POST",
      body: {
        ...a,
        restore_id: restoreId,
      },
    })
    render("admin_storage_restore_commit", response)
    const data = apiData(response)
    setStorageOutput("storageRestoreOutput", buildStorageRestoreText(data), data)
  })

  byId("btnStorageRestoreCancel").addEventListener("click", async () => {
    const a = actor()
    const restoreId = readTextField("storageRestoreId", "")
    if (!restoreId) {
      setStorageOutput(
        "storageRestoreOutput",
        i18nMessage("storage.output.restore_id_required", "restore_id is required."),
        { error: "restore_id_required" },
      )
      return
    }
    const response = await api("/api/admin/storage/restore/cancel", {
      method: "POST",
      body: {
        ...a,
        restore_id: restoreId,
      },
    })
    render("admin_storage_restore_cancel", response)
    const data = apiData(response)
    setStorageOutput("storageRestoreOutput", buildStorageRestoreText(data), data)
  })

  byId("btnStorageRestoreJobsList").addEventListener("click", async () => {
    const a = actor()
    const stateFilter = readTextField("storageRestoreJobsState", "")
    const limit = readIntegerField("storageRestoreJobsLimit", 20, 1)
    const response = await api(`/api/admin/storage/restore/jobs${queryString({ role: a.role, state: stateFilter, limit })}`)
    render("admin_storage_list_restore_jobs", response)
    const data = apiData(response)
    setStorageOutput("storageRestoreJobsOutput", buildStorageRestoreJobsText(data), data)
  })

  byId("btnStorageRestoreJobGet").addEventListener("click", async () => {
    const a = actor()
    const restoreId = readTextField("storageRestoreJobId", "")
    if (!restoreId) {
      setStorageOutput(
        "storageRestoreJobsOutput",
        i18nMessage("storage.output.restore_id_required", "restore_id is required."),
        { error: "restore_id_required" },
      )
      return
    }
    const response = await api(`/api/admin/storage/restore/jobs/${encodeURIComponent(restoreId)}${queryString({ role: a.role })}`)
    render("admin_storage_get_restore_job", response)
    const data = apiData(response)
    const restore = data && typeof data === "object" && data.restore && typeof data.restore === "object"
      ? data.restore
      : null
    if (restore) {
      applyFieldPatches({ storageRestoreId: restore.restore_id })
    }
    setStorageOutput("storageRestoreJobsOutput", buildStorageRestoreText(data), data)
  })
}

async function bootstrap() {
  state.pageMode = pageModeFromLocation()
  bindUiEventBusSync()
  bindStorageSync()
  bindButtons()
  applyConsoleScope()
  initializeUiLocale()
  initializeDeveloperMode()
  renderRiskGlossary()
  updateTrialStatusPanel()
  updateApplyWorkflowPanel()
  syncTemplateScopedFields(byId("trialTemplateId").value, byId("submitVersion").value)
  renderCollectionState("templates")
  renderCollectionState("submissions")
  renderCollectionState("profilePackSubmissions")
  renderCollectionState("profilePackCatalog")
  renderPanelState("templateDetail")
  renderPanelState("submissionDetail")
  renderPanelState("compare")
  renderModerationWorkspace()
  setProfilePackSections([])
  setProfilePackRecordPackFilter(readProfilePackRecordPackFilter())
  updateProfilePackPanel()
  updateProfilePackRecords()
  updateProfilePackMarketPanel()
  renderTemplateCards([])
  renderTemplateDrawer("")
  setActiveMarketChip(String(byId("templateCategoryFilter").value || "").trim())
  closeSubmitWizard()
  setWizardStep(1)
  updateProfilePackSubmissionTable([])
  updateProfilePackCatalogTable([])
  applyFieldPatches({
    profilePackPlanId: profilePackDefaultPlanId(byId("profilePackId").value),
    profilePackSubmissionArtifactId: state.profilePack.exportArtifactId,
  })
  updateWorkspaceContext({ scope: "", id: "" })
  window.addEventListener("hashchange", () => {
    void syncWorkspaceFromHash()
  })
  await initAuth()
  await refreshHealth()
  if (byId("memberInstallationsList")) {
    await loadMemberInstallations()
  }
  if (byId("memberImportDraftList")) {
    await loadMemberProfilePackImports()
  }
  if (byId("memberTaskQueueList")) {
    await loadMemberTasks()
  }
  if (state.pageMode === "member" && byId("btnTemplates") && isInlineMemberMarketVisible()) {
    if (hasCapability("templates.list")) {
      await listTemplates()
    }
    if (byId("btnListSubmissions")) {
      if (hasCapability("member.submissions.read") || hasCapability("admin.submissions.read")) {
        await listSubmissions()
      }
    }
    if (byId("btnProfilePackListPackSubmissions")) {
      if (hasCapability("member.profile_pack.submissions.read") || hasCapability("admin.profile_pack.market.review")) {
        await listProfilePackMarketSubmissions()
      }
    }
  }
  await syncWorkspaceFromHash()
}

bootstrap()
