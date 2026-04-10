const test = require("node:test")
const assert = require("node:assert/strict")

const {
  BODY_SCROLL_LOCK_CLASS,
  nextOpenDialogScopes,
  shouldLockBodyScroll,
  syncBodyScrollLock,
} = require("../../sharelife/webui/dialog_scroll_lock.js")

test("nextOpenDialogScopes tracks multiple open dialogs without duplicates", () => {
  let openScopes = nextOpenDialogScopes([], "memberProfilePackUpload", true)
  openScopes = nextOpenDialogScopes(openScopes, "submitWizard", true)
  openScopes = nextOpenDialogScopes(openScopes, "memberProfilePackUpload", true)

  assert.deepEqual(openScopes, ["memberProfilePackUpload", "submitWizard"])

  openScopes = nextOpenDialogScopes(openScopes, "memberProfilePackUpload", false)
  assert.deepEqual(openScopes, ["submitWizard"])
})

test("shouldLockBodyScroll returns true while any dialog is open", () => {
  assert.equal(shouldLockBodyScroll([]), false)
  assert.equal(shouldLockBodyScroll(["memberProfilePackUpload"]), true)
})

test("syncBodyScrollLock toggles body class in place", () => {
  const classState = new Set()
  const body = {
    classList: {
      toggle(name, enabled) {
        if (enabled) classState.add(name)
        else classState.delete(name)
      },
    },
  }

  assert.equal(syncBodyScrollLock(body, ["memberProfilePackUpload"]), true)
  assert.equal(classState.has(BODY_SCROLL_LOCK_CLASS), true)

  assert.equal(syncBodyScrollLock(body, []), false)
  assert.equal(classState.has(BODY_SCROLL_LOCK_CLASS), false)
})
