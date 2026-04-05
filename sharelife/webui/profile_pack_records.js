(function bootstrapProfilePackRecords(globalScope) {
  function textValue(value, fallback = "") {
    if (value === undefined || value === null) {
      return fallback
    }
    const text = String(value).trim()
    return text || fallback
  }

  function normalizeRows(rows) {
    if (!Array.isArray(rows)) {
      return []
    }
    const out = []
    rows.forEach((item) => {
      if (!item || typeof item !== "object") return
      out.push({ ...item })
    })
    return out
  }

  function mergeRecordCollections(current, patch) {
    const base = current && typeof current === "object" ? current : {}
    const next = patch && typeof patch === "object" ? patch : {}
    return {
      exports: Object.prototype.hasOwnProperty.call(next, "exports")
        ? normalizeRows(next.exports)
        : normalizeRows(base.exports),
      imports: Object.prototype.hasOwnProperty.call(next, "imports")
        ? normalizeRows(next.imports)
        : normalizeRows(base.imports),
    }
  }

  function buildRecordPatch(group, row, defaultPlanId = "") {
    const data = row && typeof row === "object" ? row : {}
    const patch = {}
    const packId = textValue(data.pack_id)
    const version = textValue(data.version)
    const planId = textValue(defaultPlanId)

    if (packId) patch.profilePackId = packId
    if (version) patch.profilePackVersion = version
    if (planId) patch.profilePackPlanId = planId

    if (group === "exports") {
      const artifactId = textValue(data.artifact_id)
      if (artifactId) patch.profilePackImportArtifactId = artifactId
      return patch
    }

    if (group === "imports") {
      const importId = textValue(data.import_id)
      const sourceArtifactId = textValue(data.source_artifact_id)
      if (importId) patch.profilePackImportId = importId
      if (sourceArtifactId) patch.profilePackImportArtifactId = sourceArtifactId
      return patch
    }

    return patch
  }

  function normalizePackIdFilter(value) {
    return textValue(value).toLowerCase()
  }

  function rowPackId(row) {
    if (!row || typeof row !== "object") return ""
    return textValue(row.pack_id).toLowerCase()
  }

  function filterRowsByPackId(rows, packIdFilter) {
    const normalizedRows = normalizeRows(rows)
    const matcher = normalizePackIdFilter(packIdFilter)
    if (!matcher) {
      return normalizedRows
    }
    return normalizedRows.filter((row) => rowPackId(row).includes(matcher))
  }

  function filterRecordCollections(records, packIdFilter) {
    const base = records && typeof records === "object" ? records : {}
    return {
      exports: filterRowsByPackId(base.exports, packIdFilter),
      imports: filterRowsByPackId(base.imports, packIdFilter),
    }
  }

  function listQuickActions(group) {
    if (group === "exports") {
      return ["use", "use_import", "use_dryrun"]
    }
    if (group === "imports") {
      return ["use", "use_dryrun"]
    }
    return ["use"]
  }

  const api = {
    mergeRecordCollections,
    buildRecordPatch,
    filterRecordCollections,
    listQuickActions,
  }

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api
  }
  globalScope.SharelifeProfilePackRecords = api
})(typeof globalThis !== "undefined" ? globalThis : this)
