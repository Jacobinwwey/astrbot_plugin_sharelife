const test = require("node:test")
const assert = require("node:assert/strict")

const {
  mergeRecordCollections,
  buildRecordPatch,
  filterRecordCollections,
  listQuickActions,
} = require("../../sharelife/webui/profile_pack_records.js")

test("mergeRecordCollections keeps existing groups when patch omits them", () => {
  const current = {
    exports: [{ artifact_id: "exp-1" }],
    imports: [{ import_id: "imp-1" }],
  }
  const merged = mergeRecordCollections(current, {
    imports: [{ import_id: "imp-2" }],
  })
  assert.deepEqual(merged.exports, [{ artifact_id: "exp-1" }])
  assert.deepEqual(merged.imports, [{ import_id: "imp-2" }])
})

test("buildRecordPatch maps export row to artifact and plan fields", () => {
  const patch = buildRecordPatch("exports", {
    artifact_id: "exp-2",
    pack_id: "profile/basic",
    version: "1.0.0",
  }, "profile-plan-basic")

  assert.deepEqual(patch, {
    profilePackImportArtifactId: "exp-2",
    profilePackPlanId: "profile-plan-basic",
    profilePackId: "profile/basic",
    profilePackVersion: "1.0.0",
  })
})

test("buildRecordPatch maps import row to import and optional source artifact fields", () => {
  const patch = buildRecordPatch("imports", {
    import_id: "imp-9",
    source_artifact_id: "exp-9",
    pack_id: "profile/new",
    version: "2.0.0",
  }, "profile-plan-new")

  assert.deepEqual(patch, {
    profilePackImportId: "imp-9",
    profilePackImportArtifactId: "exp-9",
    profilePackPlanId: "profile-plan-new",
    profilePackId: "profile/new",
    profilePackVersion: "2.0.0",
  })
})

test("filterRecordCollections matches pack_id across exports and imports", () => {
  const records = {
    exports: [
      { artifact_id: "exp-1", pack_id: "profile/basic" },
      { artifact_id: "exp-2", pack_id: "profile/research" },
    ],
    imports: [
      { import_id: "imp-1", pack_id: "profile/basic" },
      { import_id: "imp-2", pack_id: "profile/new" },
    ],
  }

  const filtered = filterRecordCollections(records, "basic")
  assert.equal(filtered.exports.length, 1)
  assert.equal(filtered.exports[0].artifact_id, "exp-1")
  assert.equal(filtered.imports.length, 1)
  assert.equal(filtered.imports[0].import_id, "imp-1")
})

test("listQuickActions returns supported action ids by group", () => {
  assert.deepEqual(listQuickActions("exports"), ["use", "use_import", "use_dryrun"])
  assert.deepEqual(listQuickActions("imports"), ["use", "use_dryrun"])
  assert.deepEqual(listQuickActions("unknown"), ["use"])
})
