(function bootstrapProfilePackPanel(globalScope) {
  function textValue(value, fallback = "") {
    if (value === undefined || value === null) {
      return fallback
    }
    const text = String(value).trim()
    return text || fallback
  }

  function normalizeSectionList(value) {
    const rawItems = Array.isArray(value)
      ? value
      : textValue(value)
          .split(",")
          .map((item) => item.trim())
    const out = []
    const seen = new Set()
    rawItems.forEach((item) => {
      const text = textValue(item)
      if (!text || seen.has(text)) return
      seen.add(text)
      out.push(text)
    })
    return out
  }

  function buildExportPayload(input) {
    const data = input || {}
    return {
      pack_id: textValue(data.packId),
      version: textValue(data.version, "1.0.0"),
      pack_type: textValue(data.packType, "bot_profile_pack"),
      redaction_mode: textValue(data.redactionMode, "exclude_secrets"),
      sections: normalizeSectionList(data.sections),
      mask_paths: normalizeSectionList(data.maskPaths),
      drop_paths: normalizeSectionList(data.dropPaths),
    }
  }

  function buildSelectedSections(sectionRows) {
    const rows = Array.isArray(sectionRows) ? sectionRows : []
    const out = []
    rows.forEach((item) => {
      const name = textValue(item && item.name)
      if (!name || !(item && item.checked)) return
      out.push(name)
    })
    return out
  }

  function buildDryrunPayload(input) {
    const data = input || {}
    return {
      import_id: textValue(data.importId),
      plan_id: textValue(data.planId),
      selected_sections: buildSelectedSections(data.sections),
    }
  }

  function buildSectionRows(sectionNames, selectedSections) {
    const available = normalizeSectionList(sectionNames)
    const selected = new Set(normalizeSectionList(selectedSections))
    return available.map((name) => ({
      name,
      checked: selected.size ? selected.has(name) : true,
    }))
  }

  function buildImportAndDryrunPayload(input) {
    const data = input || {}
    const payload = {
      plan_id: textValue(data.planId),
    }
    const selectedSections = buildSelectedSections(data.sections)
    if (selectedSections.length > 0) {
      payload.selected_sections = selectedSections
    }
    const artifactId = textValue(data.artifactId)
    if (artifactId) {
      payload.artifact_id = artifactId
      return payload
    }
    payload.filename = textValue(data.filename)
    payload.content_base64 = textValue(data.contentBase64)
    return payload
  }

  function validateFieldPaths(payload) {
    const data = payload || {}
    const allowedSections = new Set([
      "astrbot_core",
      "providers",
      "plugins",
      "skills",
      "personas",
      "mcp_servers",
      "sharelife_meta",
      "memory_store",
      "conversation_history",
      "knowledge_base",
      "environment_manifest",
    ])
    const fieldEntries = {
      mask_paths: normalizeSectionList(data.mask_paths),
      drop_paths: normalizeSectionList(data.drop_paths),
    }
    const errors = []
    Object.entries(fieldEntries).forEach(([field, entries]) => {
      entries.forEach((item) => {
        if (!item.includes(".")) {
          errors.push({
            field,
            value: item,
            code: "invalid_path_format",
            message: `Path must include section prefix: ${item}`,
          })
          return
        }
        const section = item.split(".", 1)[0]
        if (!allowedSections.has(section)) {
          errors.push({
            field,
            value: item,
            code: "invalid_section",
            message: `Unknown section: ${section}`,
          })
        }
      })
    })
    return {
      valid: errors.length === 0,
      errors,
    }
  }

  const api = {
    normalizeSectionList,
    buildExportPayload,
    buildSelectedSections,
    buildDryrunPayload,
    buildSectionRows,
    buildImportAndDryrunPayload,
    validateFieldPaths,
  }

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api
  }
  globalScope.SharelifeProfilePackPanel = api
})(typeof globalThis !== "undefined" ? globalThis : this)
