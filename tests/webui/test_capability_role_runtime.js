const test = require("node:test")
const assert = require("node:assert/strict")

const {
  normalizeRole,
  fixedRoleByPageMode,
  fallbackCapabilityRole,
} = require("../../sharelife/webui/capability_role_runtime.js")

test("normalizeRole keeps supported roles and falls back otherwise", () => {
  assert.equal(normalizeRole("member"), "member")
  assert.equal(normalizeRole("ADMIN"), "admin")
  assert.equal(normalizeRole("unknown"), "")
  assert.equal(normalizeRole("unknown", "member"), "member")
})

test("fixedRoleByPageMode resolves reviewer bridge semantics", () => {
  assert.equal(fixedRoleByPageMode("member"), "member")
  assert.equal(fixedRoleByPageMode("admin"), "admin")
  assert.equal(
    fixedRoleByPageMode("reviewer", { reviewerAdminBridgeActive: false }),
    "member",
  )
  assert.equal(
    fixedRoleByPageMode("reviewer", { reviewerAdminBridgeActive: true }),
    "admin",
  )
  assert.equal(fixedRoleByPageMode("auto"), "")
})

test("fallbackCapabilityRole keeps reviewer readonly public and defaults safely", () => {
  assert.equal(
    fallbackCapabilityRole({
      pageMode: "reviewer",
      reviewerAdminBridgeActive: false,
      roleFieldValue: "admin",
    }),
    "public",
  )
  assert.equal(
    fallbackCapabilityRole({
      pageMode: "reviewer",
      reviewerAdminBridgeActive: true,
      roleFieldValue: "member",
    }),
    "admin",
  )
  assert.equal(
    fallbackCapabilityRole({
      pageMode: "auto",
      reviewerAdminBridgeActive: false,
      roleFieldValue: "reviewer",
    }),
    "reviewer",
  )
  assert.equal(
    fallbackCapabilityRole({
      pageMode: "auto",
      reviewerAdminBridgeActive: false,
      roleFieldValue: "",
    }),
    "member",
  )
})
