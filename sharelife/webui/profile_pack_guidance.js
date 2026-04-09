(function bootstrapProfilePackGuidance(globalScope) {
  const SECTION_META = Object.freeze({
    astrbot_core: {
      titleKey: "profile_pack.section.astrbot_core.title",
      descriptionKey: "profile_pack.section.astrbot_core.description",
      stateful: false,
      localData: false,
    },
    providers: {
      titleKey: "profile_pack.section.providers.title",
      descriptionKey: "profile_pack.section.providers.description",
      stateful: false,
      localData: false,
    },
    plugins: {
      titleKey: "profile_pack.section.plugins.title",
      descriptionKey: "profile_pack.section.plugins.description",
      stateful: false,
      localData: false,
    },
    skills: {
      titleKey: "profile_pack.section.skills.title",
      descriptionKey: "profile_pack.section.skills.description",
      stateful: false,
      localData: false,
    },
    personas: {
      titleKey: "profile_pack.section.personas.title",
      descriptionKey: "profile_pack.section.personas.description",
      stateful: false,
      localData: false,
    },
    mcp_servers: {
      titleKey: "profile_pack.section.mcp_servers.title",
      descriptionKey: "profile_pack.section.mcp_servers.description",
      stateful: false,
      localData: false,
    },
    sharelife_meta: {
      titleKey: "profile_pack.section.sharelife_meta.title",
      descriptionKey: "profile_pack.section.sharelife_meta.description",
      stateful: false,
      localData: false,
    },
    memory_store: {
      titleKey: "profile_pack.section.memory_store.title",
      descriptionKey: "profile_pack.section.memory_store.description",
      stateful: true,
      localData: true,
    },
    conversation_history: {
      titleKey: "profile_pack.section.conversation_history.title",
      descriptionKey: "profile_pack.section.conversation_history.description",
      stateful: true,
      localData: true,
    },
    knowledge_base: {
      titleKey: "profile_pack.section.knowledge_base.title",
      descriptionKey: "profile_pack.section.knowledge_base.description",
      stateful: true,
      localData: true,
    },
    environment_manifest: {
      titleKey: "profile_pack.section.environment_manifest.title",
      descriptionKey: "profile_pack.section.environment_manifest.description",
      stateful: false,
      localData: true,
    },
  })

  const ISSUE_META = Object.freeze({
    astrbot_version_mismatch: {
      issueKey: "profile_pack.issue.astrbot_version_mismatch",
      severity: "danger",
    },
    plugin_compat_mismatch: {
      issueKey: "profile_pack.issue.plugin_compat_mismatch",
      severity: "danger",
    },
    signature_algorithm_unsupported: {
      issueKey: "profile_pack.issue.signature_algorithm_unsupported",
      severity: "danger",
    },
    signature_untrusted_key: {
      issueKey: "profile_pack.issue.signature_untrusted_key",
      severity: "danger",
    },
    signature_invalid: {
      issueKey: "profile_pack.issue.signature_invalid",
      severity: "danger",
    },
    encrypted_secrets_key_unavailable: {
      issueKey: "profile_pack.issue.encrypted_secrets_key_unavailable",
      severity: "danger",
    },
    encrypted_secret_payload_invalid: {
      issueKey: "profile_pack.issue.encrypted_secret_payload_invalid",
      severity: "danger",
    },
    environment_container_reconfigure_required: {
      issueKey: "profile_pack.issue.environment_container_reconfigure_required",
      severity: "warning",
      actionCode: "reconfigure_container",
    },
    environment_system_dependencies_reconfigure_required: {
      issueKey: "profile_pack.issue.environment_system_dependencies_reconfigure_required",
      severity: "warning",
      actionCode: "reconfigure_system_dependencies",
    },
    environment_plugin_binary_reconfigure_required: {
      issueKey: "profile_pack.issue.environment_plugin_binary_reconfigure_required",
      severity: "warning",
      actionCode: "reconfigure_plugin_binary",
    },
    knowledge_base_storage_sync_required: {
      issueKey: "profile_pack.issue.knowledge_base_storage_sync_required",
      severity: "warning",
      actionCode: "sync_knowledge_base_storage",
    },
    section_hash_mismatch: {
      issueKey: "profile_pack.issue.section_hash_mismatch",
      severity: "warning",
    },
    astrbot_raw_import_converted: {
      issueKey: "profile_pack.issue.astrbot_raw_import_converted",
      severity: "warning",
    },
    astrbot_backup_runtime_payload_omitted: {
      issueKey: "profile_pack.issue.astrbot_backup_runtime_payload_omitted",
      severity: "warning",
    },
    astrbot_operator_fields_omitted: {
      issueKey: "profile_pack.issue.astrbot_operator_fields_omitted",
      severity: "warning",
    },
    astrbot_plugin_wildcard_unresolved: {
      issueKey: "profile_pack.issue.astrbot_plugin_wildcard_unresolved",
      severity: "warning",
    },
  })

  const ACTION_TARGETS = Object.freeze({
    reconfigure_container: {
      actionCode: "reconfigure_container",
      targetId: "profilePackPluginInstallAdvanced",
      detailsId: "profilePackPluginInstallAdvanced",
      focusId: "btnProfilePackPluginPlan",
      statusKey: "profile_pack.action.shortcut.opened_plugin_install",
    },
    reconfigure_system_dependencies: {
      actionCode: "reconfigure_system_dependencies",
      targetId: "profilePackPluginInstallAdvanced",
      detailsId: "profilePackPluginInstallAdvanced",
      focusId: "btnProfilePackPluginPlan",
      statusKey: "profile_pack.action.shortcut.opened_plugin_install",
    },
    reconfigure_plugin_binary: {
      actionCode: "reconfigure_plugin_binary",
      targetId: "profilePackPluginInstallAdvanced",
      detailsId: "profilePackPluginInstallAdvanced",
      focusId: "btnProfilePackPluginExecute",
      statusKey: "profile_pack.action.shortcut.opened_plugin_install",
    },
    sync_knowledge_base_storage: {
      actionCode: "sync_knowledge_base_storage",
      targetId: "profilePackSectionList",
      sectionName: "knowledge_base",
      statusKey: "profile_pack.action.shortcut.highlighted_knowledge_base",
    },
    tell_ai_reconfigure_environment: {
      actionCode: "tell_ai_reconfigure_environment",
      targetId: "profilePackCompatibilityDeveloper",
      focusId: "profilePackCompatibilityDeveloper",
      developerModeRequired: true,
      statusKey: "profile_pack.action.shortcut.opened_developer_payload",
    },
  })

  const ACTION_PREFILLS = Object.freeze({
    reconfigure_container: {
      prefillPluginIds: true,
    },
    reconfigure_system_dependencies: {
      prefillPluginIds: true,
    },
    reconfigure_plugin_binary: {
      prefillPluginIds: true,
    },
    sync_knowledge_base_storage: {
      ensureSections: ["knowledge_base"],
    },
    tell_ai_reconfigure_environment: {
      prefillPluginIds: true,
      ensureSections: ["environment_manifest"],
    },
  })

  function textValue(value, fallback = "") {
    if (value === undefined || value === null) return fallback
    const text = String(value).trim()
    return text || fallback
  }

  function issueBaseCode(code) {
    const value = textValue(code).toLowerCase()
    if (!value) return ""
    if (value.startsWith("section_hash_mismatch:")) {
      return "section_hash_mismatch"
    }
    return value
  }

  function normalizeIssueList(values) {
    const rows = Array.isArray(values) ? values : []
    const out = []
    const seen = new Set()
    rows.forEach((item) => {
      const code = textValue(item)
      if (!code || seen.has(code)) return
      seen.add(code)
      out.push(code)
    })
    return out
  }

  function buildI18n(options = {}) {
    const t = typeof options.t === "function"
      ? options.t
      : (_key, fallback = "") => String(fallback || "")
    const f = typeof options.f === "function"
      ? options.f
      : (key, fallback = "", tokens = {}) => {
        const template = t(key, fallback)
        return String(template).replace(/\{([a-zA-Z0-9_]+)\}/g, (match, token) => {
          if (!Object.prototype.hasOwnProperty.call(tokens, token)) return match
          return String(tokens[token] ?? "")
        })
      }
    return { t, f }
  }

  function normalizeNameList(values) {
    const rows = Array.isArray(values) ? values : [values]
    const out = []
    const seen = new Set()
    rows.forEach((item) => {
      const text = textValue(item)
      if (!text || seen.has(text)) return
      seen.add(text)
      out.push(text)
    })
    return out
  }

  function describeSection(name) {
    const key = textValue(name)
    const meta = SECTION_META[key]
    if (!meta) {
      return {
        name: key,
        known: false,
        titleKey: "",
        descriptionKey: "",
        stateful: false,
        localData: false,
      }
    }
    return {
      name: key,
      known: true,
      titleKey: meta.titleKey,
      descriptionKey: meta.descriptionKey,
      stateful: Boolean(meta.stateful),
      localData: Boolean(meta.localData),
    }
  }

  function resolveActionTarget(actionCode) {
    const key = textValue(actionCode).toLowerCase()
    const item = ACTION_TARGETS[key]
    if (!item) return null
    return {
      actionCode: item.actionCode,
      targetId: item.targetId || "",
      detailsId: item.detailsId || "",
      focusId: item.focusId || "",
      sectionName: item.sectionName || "",
      developerModeRequired: Boolean(item.developerModeRequired),
      statusKey: item.statusKey || "",
    }
  }

  function resolveActionPrefill(actionCode) {
    const key = textValue(actionCode).toLowerCase()
    const item = ACTION_PREFILLS[key]
    if (!item) return null
    return {
      actionCode: key,
      ensureSections: normalizeNameList(item.ensureSections),
      prefillPluginIds: Boolean(item.prefillPluginIds),
    }
  }

  function resolveIssueActionCode(issueCode) {
    const baseCode = issueBaseCode(issueCode)
    const meta = ISSUE_META[baseCode] || null
    if (meta && meta.actionCode) {
      return meta.actionCode
    }
    if (baseCode === "section_hash_mismatch") {
      const raw = textValue(issueCode)
      const parts = raw.split(":")
      const sectionName = parts.length > 1 ? textValue(parts.slice(1).join(":")).toLowerCase() : ""
      if (sectionName === "knowledge_base") {
        return "sync_knowledge_base_storage"
      }
    }
    return ""
  }

  function buildCompatibilityIssueView(payload) {
    const data = payload && typeof payload === "object" ? payload : {}
    const compatibility = textValue(data.compatibility, "unknown")
    const issues = normalizeIssueList(data.compatibility_issues)
    const actionCodes = []
    const issueRows = issues.map((code) => {
      const baseCode = issueBaseCode(code)
      const meta = ISSUE_META[baseCode] || null
      const severity = meta ? meta.severity : compatibility === "blocked" ? "danger" : "warning"
      if (meta && meta.actionCode && !actionCodes.includes(meta.actionCode)) {
        actionCodes.push(meta.actionCode)
      }
      return {
        code,
        baseCode,
        issueKey: meta ? meta.issueKey : "profile_pack.issue.unknown",
        severity,
      }
    })

    if (actionCodes.length && !actionCodes.includes("tell_ai_reconfigure_environment")) {
      actionCodes.push("tell_ai_reconfigure_environment")
    }

    return {
      compatibility,
      blocked: compatibility === "blocked",
      degraded: compatibility === "degraded",
      issues: issueRows,
      actionCodes,
    }
  }

  function formatIssueLabel(code, options = {}) {
    const raw = textValue(code)
    if (!raw) return "-"
    const i18n = buildI18n(options)
    if (raw.toLowerCase().startsWith("section_hash_mismatch:")) {
      const section = raw.split(":", 2)[1] || ""
      return i18n.f(
        "profile_pack.issue.section_hash_mismatch_with_section",
        "Section hash mismatch: {section}",
        { section: section || "-" },
      )
    }
    const view = buildCompatibilityIssueView({
      compatibility: "unknown",
      compatibility_issues: [raw],
    })
    const issue = view.issues[0]
    if (!issue) return raw
    return i18n.t(issue.issueKey, raw)
  }

  function formatIssueLabels(values, options = {}) {
    return normalizeIssueList(values).map((code) => formatIssueLabel(code, options))
  }

  const api = {
    describeSection,
    normalizeIssueList,
    issueBaseCode,
    resolveActionTarget,
    resolveActionPrefill,
    resolveIssueActionCode,
    buildCompatibilityIssueView,
    formatIssueLabel,
    formatIssueLabels,
  }

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api
  }
  globalScope.SharelifeProfilePackGuidance = api
})(typeof globalThis !== "undefined" ? globalThis : this)
