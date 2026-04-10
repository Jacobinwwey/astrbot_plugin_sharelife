const test = require("node:test")
const assert = require("node:assert/strict")

const {
  fallbackCapabilityOperations,
  hasCapability,
  requiredCapabilityForControl,
  isControlCapabilityAllowed,
} = require("../../sharelife/webui/capability_guard_runtime.js")

test("fallbackCapabilityOperations resolves role-specific operation bundles", () => {
  const adminOps = fallbackCapabilityOperations("admin", { authenticated: true })
  assert.ok(adminOps.includes("admin.reviewer.lifecycle.manage"))
  assert.ok(adminOps.includes("member.installations.read"))
  assert.ok(adminOps.includes("profile_pack.community.submit"))

  const reviewerOps = fallbackCapabilityOperations("reviewer", { authenticated: true })
  assert.ok(reviewerOps.includes("admin.submissions.review"))
  assert.ok(reviewerOps.includes("member.installations.read"))
  assert.ok(!reviewerOps.includes("admin.reviewer.lifecycle.manage"))
})

test("fallbackCapabilityOperations respects anonymous member fallback policy", () => {
  const anonymousMemberOps = fallbackCapabilityOperations("member", {
    authenticated: false,
    allowAnonymousMember: true,
  })
  assert.ok(anonymousMemberOps.includes("member.installations.read"))
  assert.ok(anonymousMemberOps.includes("templates.install"))
  assert.ok(!anonymousMemberOps.includes("profile_pack.community.submit"))

  const authenticatedMemberOps = fallbackCapabilityOperations("member", {
    authenticated: true,
    allowAnonymousMember: true,
  })
  assert.ok(authenticatedMemberOps.includes("profile_pack.community.submit"))
})

test("fallbackCapabilityOperations accepts custom role bundles for per-surface policy", () => {
  const ops = fallbackCapabilityOperations("member", {
    authenticated: true,
    allowAnonymousMember: false,
    baseOperations: ["auth.login", "health.read"],
    memberOperations: ["profile_pack.catalog.read", "templates.install"],
    reviewerOperations: [],
    adminOperations: [],
  })
  assert.ok(ops.includes("auth.login"))
  assert.ok(ops.includes("profile_pack.catalog.read"))
  assert.ok(!ops.includes("admin.submissions.read"))

  const anonymousOps = fallbackCapabilityOperations("member", {
    authenticated: false,
    allowAnonymousMember: true,
    anonymousMemberFallbackOperations: ["auth.login", "profile_pack.catalog.read"],
  })
  assert.deepEqual(anonymousOps, ["auth.login", "profile_pack.catalog.read"])
})

test("hasCapability enforces reviewer-readonly lock and capability lookup", () => {
  assert.equal(
    hasCapability("templates.list", {
      pageMode: "reviewer",
      reviewerAdminBridgeActive: false,
      operations: ["templates.list"],
    }),
    false,
  )
  assert.equal(
    hasCapability("templates.list", {
      pageMode: "reviewer",
      reviewerAdminBridgeActive: true,
      operations: ["templates.list"],
    }),
    true,
  )
  assert.equal(hasCapability("", { operations: [] }), true)
})

test("requiredCapabilityForControl and isControlCapabilityAllowed resolve control map", () => {
  const controlMap = {
    btnApproveSubmission: "admin.submissions.decide",
  }
  assert.equal(
    requiredCapabilityForControl("btnApproveSubmission", controlMap),
    "admin.submissions.decide",
  )
  assert.equal(
    requiredCapabilityForControl("unknownControl", controlMap),
    "",
  )
  assert.equal(
    isControlCapabilityAllowed("btnApproveSubmission", {
      controlCapabilityMap: controlMap,
      operations: ["admin.submissions.decide"],
      pageMode: "admin",
    }),
    true,
  )
  assert.equal(
    isControlCapabilityAllowed("btnApproveSubmission", {
      controlCapabilityMap: controlMap,
      operations: ["admin.submissions.read"],
      pageMode: "admin",
    }),
    false,
  )
})
