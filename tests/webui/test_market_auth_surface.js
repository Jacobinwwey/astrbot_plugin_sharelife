const test = require("node:test")
const assert = require("node:assert/strict")

const {
  describeMarketAuthSurface,
} = require("../../sharelife/webui/market_auth_surface.js")

test("describeMarketAuthSurface keeps auth panel hidden for anonymous-member browsing", () => {
  const view = describeMarketAuthSurface({
    authRequired: true,
    allowAnonymousMember: true,
    authenticated: false,
    availableRoles: ["member", "reviewer", "admin"],
    promptRequested: false,
  })

  assert.equal(view.mode, "optional")
  assert.equal(view.showAuthPanel, false)
  assert.equal(view.canBrowseAnonymously, true)
  assert.equal(view.rolesText, "member, reviewer, admin")
})

test("describeMarketAuthSurface opens auth panel once a protected action requests login", () => {
  const view = describeMarketAuthSurface({
    authRequired: true,
    allowAnonymousMember: true,
    authenticated: false,
    availableRoles: ["member", "reviewer", "admin"],
    promptRequested: true,
  })

  assert.equal(view.mode, "optional")
  assert.equal(view.showAuthPanel, true)
  assert.equal(view.canBrowseAnonymously, true)
})

test("describeMarketAuthSurface keeps strict-auth deployments gated", () => {
  const view = describeMarketAuthSurface({
    authRequired: true,
    allowAnonymousMember: false,
    authenticated: false,
    availableRoles: ["member"],
    promptRequested: false,
  })

  assert.equal(view.mode, "required")
  assert.equal(view.showAuthPanel, true)
  assert.equal(view.canBrowseAnonymously, false)
})

test("describeMarketAuthSurface hides auth panel when auth is fully disabled", () => {
  const view = describeMarketAuthSurface({
    authRequired: false,
    allowAnonymousMember: false,
    authenticated: false,
    availableRoles: [],
    promptRequested: false,
  })

  assert.equal(view.mode, "disabled")
  assert.equal(view.showAuthPanel, false)
  assert.equal(view.canBrowseAnonymously, false)
  assert.equal(view.rolesText, "none")
})
