const test = require("node:test")
const assert = require("node:assert/strict")

const {
  textValue,
  isManualVisibility,
  buildScopeLineText,
  resolveScopeNodeVisibility,
} = require("../../sharelife/webui/console_scope_dom_runtime.js")

test("textValue trims values and falls back for empty inputs", () => {
  assert.equal(textValue(" member "), "member")
  assert.equal(textValue(""), "")
  assert.equal(textValue("", "fallback"), "fallback")
  assert.equal(textValue(null, "fallback"), "fallback")
})

test("isManualVisibility detects manual marker only", () => {
  assert.equal(isManualVisibility("manual"), true)
  assert.equal(isManualVisibility(" manual "), true)
  assert.equal(isManualVisibility("auto"), false)
  assert.equal(isManualVisibility(""), false)
})

test("buildScopeLineText uses injected formatter", () => {
  const line = buildScopeLineText("reviewer", {
    formatMessage: (_key, _fallback, tokens) => `scope=${tokens.scope}`,
  })
  assert.equal(line, "scope=reviewer")
})

test("resolveScopeNodeVisibility computes hide/remove decisions", () => {
  const node = {
    getAttribute(name) {
      if (name === "data-console-scope") return "admin"
      if (name === "data-scope-visibility") return ""
      return ""
    },
  }
  const hidden = resolveScopeNodeVisibility(node, "member", {
    scopeVisible: (targetScope, activeScope) => targetScope === activeScope,
  })
  assert.equal(hidden.hide, true)
  assert.equal(hidden.removeHidden, false)

  const visibleNode = {
    getAttribute(name) {
      if (name === "data-console-scope") return "member"
      if (name === "data-scope-visibility") return ""
      return ""
    },
  }
  const visible = resolveScopeNodeVisibility(visibleNode, "member", {
    scopeVisible: (targetScope, activeScope) => targetScope === activeScope,
  })
  assert.equal(visible.hide, false)
  assert.equal(visible.removeHidden, true)

  const manualNode = {
    getAttribute(name) {
      if (name === "data-console-scope") return "member"
      if (name === "data-scope-visibility") return "manual"
      return ""
    },
  }
  const manual = resolveScopeNodeVisibility(manualNode, "member", {
    scopeVisible: (targetScope, activeScope) => targetScope === activeScope,
  })
  assert.equal(manual.hide, false)
  assert.equal(manual.removeHidden, false)
})
