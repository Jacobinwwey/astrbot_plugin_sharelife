const test = require("node:test")
const assert = require("node:assert/strict")

const {
  anonymousMemberFallbackOperations,
} = require("../../sharelife/webui/capability_policy_runtime.js")

test("anonymousMemberFallbackOperations exposes stable anonymous member capability bundle", () => {
  const operations = anonymousMemberFallbackOperations()
  assert.ok(Array.isArray(operations))
  assert.ok(operations.includes("member.installations.read"))
  assert.ok(operations.includes("templates.install"))
  assert.ok(operations.includes("profile_pack.catalog.read"))
  assert.ok(!operations.includes("profile_pack.community.submit"))
})

test("anonymousMemberFallbackOperations returns a defensive copy", () => {
  const first = anonymousMemberFallbackOperations()
  first.push("temporary.fake.capability")
  const second = anonymousMemberFallbackOperations()
  assert.equal(second.includes("temporary.fake.capability"), false)
})
