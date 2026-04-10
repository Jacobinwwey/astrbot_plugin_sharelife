const test = require("node:test")
const assert = require("node:assert/strict")

const {
  normalizeScope,
  normalizePageMode,
  resolveConsoleHint,
  visibilityForPageMode,
} = require("../../sharelife/webui/console_surface_controls.js")

test("normalizeScope keeps only member/reviewer/admin", () => {
  assert.equal(normalizeScope("admin"), "admin")
  assert.equal(normalizeScope("reviewer"), "reviewer")
  assert.equal(normalizeScope("MEMBER"), "member")
  assert.equal(normalizeScope("other"), "member")
})

test("normalizePageMode resolves known modes and falls back to auto", () => {
  assert.equal(normalizePageMode("member"), "member")
  assert.equal(normalizePageMode("reviewer"), "reviewer")
  assert.equal(normalizePageMode("admin"), "admin")
  assert.equal(normalizePageMode("market"), "auto")
})

test("resolveConsoleHint returns member/reviewer/admin hint descriptors", () => {
  const memberHint = resolveConsoleHint("member", { bridgeActive: false })
  assert.equal(memberHint.hintKey, "console.switch.hint.member")

  const reviewerReadonlyHint = resolveConsoleHint("reviewer", { bridgeActive: false })
  assert.equal(reviewerReadonlyHint.hintKey, "console.switch.hint.reviewer_readonly")

  const reviewerBridgeHint = resolveConsoleHint("reviewer", { bridgeActive: true })
  assert.equal(reviewerBridgeHint.hintKey, "console.switch.hint.reviewer")

  const adminHint = resolveConsoleHint("admin", { bridgeActive: false })
  assert.equal(adminHint.hintKey, "console.switch.hint.admin")
})

test("visibilityForPageMode keeps member page minimal and admin/reviewer variants stable", () => {
  assert.deepEqual(
    visibilityForPageMode("member"),
    { member: true, market: true, reviewer: false, admin: false, full: false },
  )
  assert.deepEqual(
    visibilityForPageMode("reviewer"),
    { member: true, market: true, reviewer: false, admin: true, full: true },
  )
  assert.deepEqual(
    visibilityForPageMode("admin"),
    { member: true, market: true, reviewer: true, admin: false, full: true },
  )
  assert.deepEqual(
    visibilityForPageMode("auto"),
    { member: true, market: true, reviewer: true, admin: true, full: true },
  )
})
