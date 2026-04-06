const test = require("node:test")
const assert = require("node:assert/strict")

const {
  normalizeRole,
  isReviewerRole,
  buildAuthRoleOptions,
  resolveConsoleVisibility,
  applyConsoleVisibility,
} = require("../../sharelife/webui/market_auth_view.js")

test("market auth view normalizes roles and reviewer predicate", () => {
  assert.equal(normalizeRole("  Admin "), "admin")
  assert.equal(isReviewerRole("Reviewer"), true)
  assert.equal(isReviewerRole("member"), false)
})

test("market auth view builds role options constrained to preferred role", () => {
  const options = buildAuthRoleOptions(["member", "reviewer"], "member", {
    i18nMessage(key, fallback) {
      return `${key}:${fallback}`
    },
  })
  assert.equal(options.length, 1)
  assert.equal(options[0].value, "member")
  assert.equal(options[0].i18nKey, "option.member")
  assert.match(options[0].label, /option\.member/)
})

test("market auth view resolves console visibility by auth state and role", () => {
  assert.deepEqual(resolveConsoleVisibility(false, "member"), {
    memberHidden: false,
    reviewerHidden: true,
    adminHidden: true,
    fullHidden: true,
  })
  assert.deepEqual(resolveConsoleVisibility(true, "reviewer"), {
    memberHidden: false,
    reviewerHidden: false,
    adminHidden: true,
    fullHidden: true,
  })
  assert.deepEqual(resolveConsoleVisibility(true, "admin"), {
    memberHidden: false,
    reviewerHidden: false,
    adminHidden: false,
    fullHidden: false,
  })
})

test("market auth view applies visibility toggles to links", () => {
  function node() {
    return {
      hidden: false,
      classList: {
        toggle(_name, value) {
          this._owner.hidden = Boolean(value)
        },
        _owner: null,
      },
    }
  }
  const member = node()
  const reviewer = node()
  const admin = node()
  const full = node()
  member.classList._owner = member
  reviewer.classList._owner = reviewer
  admin.classList._owner = admin
  full.classList._owner = full

  applyConsoleVisibility(
    { member, reviewer, admin, full },
    resolveConsoleVisibility(true, "reviewer"),
  )
  assert.equal(member.hidden, false)
  assert.equal(reviewer.hidden, false)
  assert.equal(admin.hidden, true)
  assert.equal(full.hidden, true)
})
