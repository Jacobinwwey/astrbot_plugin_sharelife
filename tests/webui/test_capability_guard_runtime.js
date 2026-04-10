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
